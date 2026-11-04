"""Main plan landing page must use the real public contract, not a mock week."""
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'wordpress'))
from generate_training_plans import build_plan_preview, generate_training_page
from plan_simulator import _race_date


def test_main_landing_projects_road_race_demands_and_format():
    markup = build_plan_preview()
    match = re.search(r'<script type="application/json"[^>]*>(.*?)</script>', markup, re.S)
    config = json.loads(match.group(1).replace('<\\/', '</'))
    assert config['brand'] == 'roadie_labs'
    assert config['schema_version'] == 'training-plan-preview-request/v2'
    assert config['race']['discipline'] == 'road'
    assert config['race']['event_format'] == 'fondo'
    assert config['race_date'] == '2027-04-24'
    assert len(config['race_options']) > 100
    assert all(race['discipline'] == 'road' for race in config['race_options'])


def test_main_landing_places_engine_preview_before_deliverables():
    page = generate_training_page()
    assert page.index('id="custom-plan-preview"') < page.index('id="what-you-get"')
    assert '<div class="rl-tp-sample-grid"' not in page
    assert '<section class="rl-tp-pullquote"' not in page
    assert '$2/day' not in page
    assert 'two plan adjustments' in page
    assert 'Personally reviewed and delivered in TrainingPeaks within 24 hours' in page


def test_explicit_date_formats_and_unknown_dates():
    assert _race_date({'vitals': {'date_specific': '2027: Saturday, April 24'}}) == '2027-04-24'
    assert _race_date({'vitals': {'date_specific': '2027: date not announced'}}) == ''
    assert _race_date({'vitals': {'date_specific': '2027-02-30'}}) == ''
