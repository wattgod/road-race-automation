from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wordpress"))

from generate_questionnaire import generate_questionnaire_page


def test_road_questionnaire_collects_license_category_without_wkg_claim():
    html = generate_questionnaire_page()
    assert 'name="roadCategory"' in html
    assert "Novice / Cat 5" in html
    assert "License category is based on racing experience and results, not W/kg." in html
    assert "<strong>Power band:</strong>" in html
    assert "<strong>Category:</strong>" not in html


def test_road_brand_enables_format_fields_in_shared_javascript():
    html = generate_questionnaire_page()
    script = (ROOT / "web" / "training-plans-form.js").read_text(encoding="utf-8")

    assert "showRoadFields: true" in html
    assert "SHOW_ROAD_FIELDS" in script
    assert '<option value="criterium">Criterium</option>' in script
    assert '<option value="hill_climb">Hill climb</option>' in script
    assert '<option value="time_trial">Time trial</option>' in script
    assert '<option value="stage_race">Stage race</option>' in script
    assert '<option value="fondo">Gran fondo / sportive</option>' in script
    assert "mapped.race_format = aRace.race_format" in script
    assert "roadCategory: 'road_category'" in script


def test_power_band_is_not_serialized_as_license_category():
    script = (ROOT / "web" / "training-plans-form.js").read_text(encoding="utf-8")
    assert "data.powerBand =" in script
    assert "data.estimatedCategory" not in script
    assert "Cat 1-2" not in script
