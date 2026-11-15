"""RL-04: every og:image a generator emits must exist and ship to /og/.

The live site 404'd /og/homepage.jpg and every /og/<slug>.jpg: the generator
made race cards only (no homepage.jpg, which home, plans, vs pages and other
non-race pages reference) and nothing stopped a partial --sync-og.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import push_wordpress  # noqa: E402
import validate_deploy  # noqa: E402
from scripts import generate_og_images as og  # noqa: E402

GENERATORS = sorted((REPO_ROOT / "wordpress").glob("generate_*.py"))
OG_REF = re.compile(r"/og/([^\"'\s]+?)\.jpg")


def test_every_generator_og_reference_is_homepage_or_race_slug():
    """Each /og/<x>.jpg in a generator is the site card or a per-slug card,
    so expected_og_filenames covers all of them."""
    refs = set()
    for path in GENERATORS:
        refs.update(OG_REF.findall(path.read_text(encoding="utf-8")))
    assert refs, "no /og/ references found; pattern drifted"
    for ref in refs:
        assert ref == "homepage" or "slug" in ref, (
            f"/og/{ref}.jpg is neither homepage.jpg nor a race-slug card; "
            "teach generate_og_images.py to produce it")


def test_expected_og_filenames_cover_homepage_and_every_race():
    names = push_wordpress.expected_og_filenames()
    slugs = [p.stem for p in (REPO_ROOT / "race-data").glob("*.json")]
    assert names[0] == "homepage.jpg"
    assert set(names[1:]) == {f"{s}.jpg" for s in slugs}


def test_race_profile_slug_matches_filename():
    """Race pages build /og/{rd['slug']}.jpg; the generator writes by filename."""
    for path in (REPO_ROOT / "race-data").glob("*.json"):
        race = json.loads(path.read_text(encoding="utf-8")).get("race", {})
        assert race.get("slug", path.stem) == path.stem, path.name


def test_missing_og_images_reports_gaps(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "alpha.json").write_text("{}")
    (data / "beta.json").write_text("{}")
    ogdir = tmp_path / "og"
    ogdir.mkdir()
    (ogdir / "alpha.jpg").write_bytes(b"x")
    assert push_wordpress.missing_og_images(ogdir, data) == ["homepage.jpg", "beta.jpg"]
    (ogdir / "homepage.jpg").write_bytes(b"x")
    (ogdir / "beta.jpg").write_bytes(b"x")
    assert push_wordpress.missing_og_images(ogdir, data) == []


def test_sync_og_refuses_partial_set(tmp_path, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(push_wordpress, "get_ssh_credentials",
                        lambda: ("host.example", "deploy", "18765"))
    monkeypatch.setattr(push_wordpress.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd))
    monkeypatch.setattr(push_wordpress.subprocess, "Popen",
                        lambda *a, **kw: calls.append(a))
    (tmp_path / "paris-brest-paris.jpg").write_bytes(b"x")
    assert push_wordpress.sync_og(str(tmp_path)) is None
    assert calls == []
    assert "homepage.jpg" in capsys.readouterr().out


def test_missing_brand_font_is_an_error_not_a_substitute(tmp_path):
    with pytest.raises(og.FontMissingError):
        og.set_font_dir(tmp_path)


_FONT_DIRS = [d for d in (og.DEFAULT_FONT_DIR,
                          Path.home() / "gravel-race-automation" / "guide" / "fonts")
              if d.is_dir()]


@pytest.mark.skipif(not _FONT_DIRS,
                    reason="brand TTFs live in the sibling gravel-race-automation checkout")
def test_site_and_race_cards_render(tmp_path):
    from PIL import Image
    og.set_font_dir(_FONT_DIRS[0])
    site = og.generate_site_og_image(tmp_path / "homepage.jpg")
    race = json.loads((REPO_ROOT / "race-data" / "paris-brest-paris.json").read_text())["race"]
    card = og.generate_og_image(race, tmp_path / "paris-brest-paris.jpg")
    for path in (site, card):
        with Image.open(path) as im:
            assert im.size == (1200, 630)
            assert im.format == "JPEG"


def test_race_card_requires_stored_score_and_tier(tmp_path):
    race = {"slug": "x", "name": "X", "fondo_rating": {"overall_score": 70}}
    with pytest.raises(ValueError):
        og.generate_og_image(race, tmp_path / "x.jpg")


def test_extract_og_image_urls_reads_meta_and_jsonld():
    base = validate_deploy.BASE_URL
    html = f'''
      <meta property="og:image" content="{base}/og/homepage.jpg">
      <meta name="twitter:image" content="{base}/og/homepage.jpg">
      <meta property="og:image:width" content="1200">
      <script type="application/ld+json">{{"image":["{base}/og/pbp.jpg"]}}</script>
      <meta property="og:image" content="https://elsewhere.example/x.jpg">'''
    assert validate_deploy.extract_og_image_urls(html) == [
        f"{base}/og/homepage.jpg", f"{base}/og/pbp.jpg"]


def test_og_sample_covers_home_plans_vs_and_each_tier():
    index = [{"slug": "a", "tier": 1}, {"slug": "b", "tier": 1}, {"slug": "c", "tier": 2}]
    paths = validate_deploy.og_sample_paths(index)
    assert paths[:2] == ["/", "/training-plans/"]
    assert any("-vs-" in p for p in paths)
    assert "/race/a/" in paths and "/race/c/" in paths and "/race/b/" not in paths


def _parse(argv):
    return push_wordpress.build_parser().parse_args(argv)


@pytest.mark.parametrize("flag", [
    a.option_strings[0] for a in push_wordpress.build_parser()._actions
    if a.option_strings and a.option_strings[0].startswith("--sync-")
    and a.const is True
])
def test_every_sync_flag_alone_counts_as_an_action(flag):
    assert push_wordpress.has_sync_action(_parse([flag]))


def test_sync_legal_alone_is_accepted():
    assert push_wordpress.has_sync_action(_parse(["--sync-legal"]))


def test_no_flags_is_not_an_action():
    assert not push_wordpress.has_sync_action(_parse([]))
    assert push_wordpress.has_sync_action(_parse(["--purge-cache"]))
