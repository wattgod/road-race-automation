"""Roadie adapter for the canonical Gravel God guide app snapshot."""
import re, json
from pathlib import Path
import shared_guide_blocks as blocks
from shared_guide_infographics import INFOGRAPHIC_RENDERERS
from brand_tokens import get_tokens_css
DIR=Path(__file__).resolve().parent
ALIASES={'dark-brown':'dark-navy','primary-brown':'primary-navy','secondary-brown':'secondary-blue','warm-brown':'steel','tan':'silver','sand':'silver','warm-paper':'cool-white','gold':'signal-red','light-gold':'steel','teal':'signal-red','light-teal':'silver','near-black':'near-black','white':'white','error':'error','tier-1':'tier-1','tier-2':'tier-2','tier-3':'tier-3','tier-4':'tier-4'}
SHARED_IMAGES={'ch3-supercompensation','ch3-zone-spectrum','ch3-pmc-chart','ch3-training-phases','ch3-power-duration','ch3-gantt-season','ch3-before-after','ch4-traffic-light','ch4-recovery-dash','ch4-sleep-debt'}
def brand(text):
 for old,new in ALIASES.items():text=text.replace('--gg-color-'+old,'--rl-color-'+new)
 return text.replace('gg-','rl-').replace('--gg-','--rl-')
def app_css():
 source=(DIR/'shared_guide_app.css').read_text()
 root=re.search(r':root\s*\{([^}]+)\}',source)
 palette={}
 if root:
  for name,value in re.findall(r'--gg-color-([\w-]+):\s*(#[0-9a-fA-F]+)',root[1]):palette[value.lower()]='var(--rl-color-'+ALIASES.get(name,'near-black')+')'
  source=source[:root.start()]+source[root.end():]
 # Convert the inherited app's literal colors into native Roadie tokens.
 source=re.sub(r'#[0-9a-fA-F]{3,8}\b',lambda m:palette.get(m[0].lower(),'var(--rl-color-white)' if m[0].lower() in ('#fff','#ffffff') else 'var(--rl-color-near-black)'),source)
 return brand(source)+'.rl-guide-callout{border-left:0;border-block:2px solid var(--rl-color-near-black)}.rl-guide-section{margin:40px 0}.rl-guide-section-title{font:700 28px/1.3 var(--rl-font-editorial)}'
def app_js():return brand((DIR/'shared_guide_app.js').read_text())
def render(block,chapter_id):
 blocks.set_lesson_context(chapter_id)
 blocks._GLOSSARY=json.loads((DIR.parent/"guide/road-guide-content.json").read_text()).get("glossary",{})
 if block['type']=='image':
  aid=block.get('asset_id','')
  if aid not in SHARED_IMAGES:raise ValueError('Roadie guide cannot use a gravel-specific diagram: '+aid)
  return brand(INFOGRAPHIC_RENDERERS[aid](block))
 if block['type'] not in blocks.BLOCK_RENDERERS:raise ValueError('Unsupported shared guide block: '+block['type'])
 return brand(blocks.render_block(block))
