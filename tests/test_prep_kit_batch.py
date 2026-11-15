"""`generate_prep_kit.py --all` must survive a catalog-flagged race.

load_race_data refuses catalog-flagged races (duplicate / discipline
mismatch) with SystemExit. The batch loop only caught Exception, so the first
flagged race ended the whole run: on 2026-11-14 rift-valley-odyssey stopped
it and the 82 races after it alphabetically got no kit, which the race-page
deploy gate then refused. The flagged race is skipped and named; every other
race still gets its kit, and the index never links the flagged one.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wordpress"))

import generate_prep_kit  # noqa: E402

SOURCE = ROOT / "race-data" / "maratona-dles-dolomites.json"


def _stage(data_dir: Path) -> None:
    for slug in ("aaa-clean-race", "zzz-clean-race"):
        shutil.copy(SOURCE, data_dir / f"{slug}.json")
    flagged = json.loads(SOURCE.read_text(encoding="utf-8"))
    flagged.setdefault("race", {})["catalog_flags"] = {"discipline_mismatch": True}
    (data_dir / "mmm-flagged-race.json").write_text(json.dumps(flagged), encoding="utf-8")


def test_all_skips_flagged_race_and_finishes(tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    out_dir = tmp_path / "out"
    data_dir.mkdir()
    _stage(data_dir)
    monkeypatch.setattr(
        sys, "argv",
        ["generate_prep_kit.py", "--all", "--data-dir", str(data_dir), "--output-dir", str(out_dir)],
    )

    assert generate_prep_kit.main() == 0

    assert (out_dir / "aaa-clean-race.html").exists()
    assert (out_dir / "zzz-clean-race.html").exists()  # after the flagged one
    assert not (out_dir / "mmm-flagged-race.html").exists()
    printed = capsys.readouterr().out
    assert "1 catalog-flagged races skipped" in printed
    assert "mmm-flagged-race" in printed
    index_files = [p for p in out_dir.rglob("*.html") if "flagged" not in p.name and "clean" not in p.name]
    for index in index_files:
        assert "mmm-flagged-race" not in index.read_text(encoding="utf-8")
