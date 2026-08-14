import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wordpress"))

import generate_neo_brutalist as generator


def test_configure_plans_db_resolves_path_and_invalidates_cache(tmp_path, monkeypatch):
    source = tmp_path / "plans.json"
    source.write_text('{"plans": []}\n', encoding="utf-8")
    monkeypatch.setattr(generator, "_PLANS_BY_SLUG_CACHE", {"stale": []})

    generator.configure_plans_db(source)

    assert generator.PLANS_DB_PATH == source.resolve()
    assert generator._PLANS_BY_SLUG_CACHE is None
