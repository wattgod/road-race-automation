"""The Roadie Stop hook fires only for turns that changed road-race-automation files."""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "roadie_stop_review.py"


def _iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat().replace("+00:00", "Z")


def _user(text, ts):
    return {"type": "user", "timestamp": _iso(ts), "message": {"role": "user", "content": text}}


def _tool(name, args, cwd, ts):
    return {"type": "assistant", "timestamp": _iso(ts), "cwd": str(cwd),
            "message": {"content": [{"type": "tool_use", "name": name, "input": args}]}}


def _repo(path):
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    (path / "a.py").write_text("x = 1\n")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run(["git", "-C", str(path), "add", "."], check=True, env=env)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "init"], check=True, env=env)
    return path


def _run(tmp_path, entries, cwd, active=False):
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    payload = {"transcript_path": str(transcript), "cwd": str(cwd), "stop_hook_active": active}
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout) if out.stdout.strip() else None


@pytest.fixture
def repos(tmp_path):
    roadie = _repo(tmp_path / "road-race-automation")
    gravel = _repo(tmp_path / "gravel-race-automation")
    time.sleep(1.1)  # reflog and mtimes are whole seconds; the turn starts after setup
    return roadie, gravel


def test_edits_in_another_repo_do_not_fire(tmp_path, repos):
    roadie, gravel = repos
    now = time.time()
    (gravel / "a.py").write_text("x = 2\n")
    entries = [_user("verify the collector", now),
               _tool("Edit", {"file_path": str(gravel / "a.py")}, roadie, now + 1),
               _tool("Bash", {"command": f"cd {gravel} && git commit -qam x"}, roadie, now + 2)]
    assert _run(tmp_path, entries, roadie) is None


def test_edit_tool_on_a_roadie_file_fires(tmp_path, repos):
    roadie, _ = repos
    now = time.time()
    entries = [_user("fix the page", now),
               _tool("Edit", {"file_path": str(roadie / "a.py")}, roadie, now + 1)]
    result = _run(tmp_path, entries, roadie)
    assert result["decision"] == "block"
    assert str(roadie / "a.py") in result["reason"]
    assert "fondo_rating" in result["reason"]


def test_bash_change_in_the_roadie_checkout_fires(tmp_path, repos):
    roadie, _ = repos
    now = time.time()
    (roadie / "generated.html").write_text("<p>new</p>")
    entries = [_user("regenerate", now), _tool("Bash", {"command": "python3 gen.py"}, roadie, now + 1)]
    result = _run(tmp_path, entries, roadie)
    assert result["decision"] == "block"
    assert "generated.html" in result["reason"]


def test_roadie_edit_in_an_earlier_turn_does_not_fire_again(tmp_path, repos):
    roadie, _ = repos
    now = time.time()
    entries = [_user("fix the page", now - 600),
               _tool("Edit", {"file_path": str(roadie / "a.py")}, roadie, now - 590),
               _user("what's the status?", now)]
    assert _run(tmp_path, entries, roadie) is None


def test_already_answering_the_checklist_lets_claude_stop(tmp_path, repos):
    roadie, _ = repos
    now = time.time()
    entries = [_user("fix the page", now),
               _tool("Edit", {"file_path": str(roadie / "a.py")}, roadie, now + 1)]
    assert _run(tmp_path, entries, roadie, active=True) is None


def test_stop_hook_feedback_is_not_a_new_turn(tmp_path, repos):
    roadie, _ = repos
    now = time.time()
    feedback = {**_user("Stop hook feedback: ...", now + 2), "isMeta": True}
    entries = [_user("fix the page", now),
               _tool("Edit", {"file_path": str(roadie / "a.py")}, roadie, now + 1), feedback]
    assert _run(tmp_path, entries, roadie)["decision"] == "block"


def test_a_broken_transcript_blocks_once_with_the_error(tmp_path):
    payload = {"transcript_path": str(tmp_path / "missing.jsonl"), "cwd": str(tmp_path)}
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                         capture_output=True, text=True, timeout=60)
    assert "Roadie stop hook failed" in json.loads(out.stdout)["reason"]
    payload["stop_hook_active"] = True
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                         capture_output=True, text=True, timeout=60)
    assert out.stdout.strip() == ""


def test_old_uncommitted_deletion_does_not_fire_on_later_turns(tmp_path):
    roadie = _repo(tmp_path / "road-race-automation")
    (roadie / "a.py").unlink()  # deleted in an earlier turn, never committed
    time.sleep(1.1)
    now = time.time()
    assert _run(tmp_path, [_user("what's the status?", now)], roadie) is None


def test_deletion_in_this_turn_fires(tmp_path, repos):
    roadie, _ = repos
    now = time.time()
    (roadie / "a.py").unlink()
    result = _run(tmp_path, [_user("remove a.py", now)], roadie)
    assert str(roadie / "a.py") in result["reason"]


def test_commit_in_the_same_second_as_the_message_fires(tmp_path, repos):
    roadie, gravel = repos
    now = time.time()
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    subprocess.run(["git", "-C", str(roadie), "commit", "-q", "--allow-empty", "-m", "x"], check=True, env=env)
    # The message timestamp carries a fraction of a second; the reflog does not.
    entries = [_user("commit it", int(now) + 0.9),
               _tool("Bash", {"command": f"cd {roadie} && git commit"}, gravel, int(now) + 1)]
    assert _run(tmp_path, entries, gravel)["decision"] == "block"


@pytest.mark.parametrize("template", [
    "set -e; cd {roadie} && python3 gen.py",
    "export X=1 && cd '{roadie}' && python3 gen.py",
    "python3 {roadie}/gen.py --out {roadie}/out",
])
def test_roadie_folder_named_later_in_a_bash_command_fires(tmp_path, repos, template):
    roadie, gravel = repos
    now = time.time()
    (roadie / "out.html").write_text("<p>new</p>")
    entries = [_user("regenerate", now),
               _tool("Bash", {"command": template.format(roadie=roadie)}, gravel, now + 1)]
    result = _run(tmp_path, entries, gravel)
    assert "out.html" in result["reason"]
