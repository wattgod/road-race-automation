"""Public guide and multi-race handoff regressions."""
import re
import json
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'wordpress'))
from generate_guide import generate
from generate_season_plan_form import generate_season_plan_page
from guide_reference import table
@pytest.fixture(scope='module')
def guide(tmp_path_factory):
 return generate(tmp_path_factory.mktemp('public-guide'))
@pytest.mark.parametrize('chapter',json.loads((ROOT/'guide/road-guide-content.json').read_text())['chapters'],ids=lambda c:c['id'])
def test_public_chapter_links_and_sources(guide,chapter):
 text=(guide/chapter['id']/'index.html').read_text()
 assert 'noindex' not in text and 'EMAIL TO UNLOCK' not in text
 assert '<figure' in text and '<h1>'+chapter['title'].replace('&','&amp;')+'</h1>' in text
 for source in chapter['sources']:
  assert 'href="#source-'+source['id']+'"' in text
  assert source['url'] in text
 assert not re.search(r'\[\^[a-z][a-z0-9-]+\]', text) and 'Not an AI' not in text
 assert 'https://roadielabs.com/guide/'+chapter['id']+'/' in text

def test_table_preserves_zero_escapes_and_row_headers():
 text=table({'title':'<script>','headers':['Item','Value'],'rows':[['<img>',0]]})
 assert '<script>' not in text and '<img>' not in text
 assert 'data-label="Value">0</td>' in text
 assert 'scope="col"' in text and 'scope="row"' in text

def test_season_checkout_retains_multi_race_contract():
 text=generate_season_plan_page()
 assert 'rl-season-form' in text and 'product: \'season_plan\'' in text
 assert 'second_race_date' in text and 'second_race_name' in text
 assert 'races:' in text and '$499' in text
 assert '--gg-' not in text and 'gravelgodcycling.com' not in text
