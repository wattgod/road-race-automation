#!/usr/bin/env python3
"""Generate the free Roadie Labs public chapter guide."""
from pathlib import Path
import argparse
import html
import json
import re
from brand_tokens import get_tokens_css,get_font_face_css,get_ga4_head_snippet
from shared_header import get_site_header_html,get_site_header_css,get_site_header_js
from shared_footer import get_mega_footer_html,get_mega_footer_css
from cookie_consent import get_consent_banner_html
from guide_reference import table,css,figure,bars,sequence
from shared_guide_runtime import app_css,app_js,render as render_shared
ROOT=Path(__file__).resolve().parents[1]
BASE='https://roadielabs.com'
def inline(value,sources):
 text=html.escape(str(value),quote=True)
 return re.sub(r'\[\^([\w.-]+)\]',lambda m:f'<sup><a href="#source-{m[1]}" aria-label="Source {sources[m[1]]}">[{sources[m[1]]}]</a></sup>',text)
def build_css():
 return app_css()+get_tokens_css()+get_font_face_css()+get_site_header_css()+get_mega_footer_css()+css('var(--rl-color-near-black)','var(--rl-color-cool-white)','var(--rl-color-silver)','var(--rl-color-steel)','var(--rl-color-near-black)','var(--rl-font-data)','var(--rl-font-editorial)')+'''
*{box-sizing:border-box}body{margin:0;background:var(--rl-color-cool-white);color:var(--rl-color-near-black);font:18px/1.7 var(--rl-font-editorial)}main{max-width:900px;margin:auto;padding:48px 24px}h1{font:700 clamp(32px,6vw,64px)/1.1 var(--rl-font-editorial);margin:18px 0}h2{font:700 28px/1.2 var(--rl-font-editorial)}a{color:inherit;text-underline-offset:4px}.kicker,nav{font:700 13px/1.5 var(--rl-font-data)}.chapters{padding:0;list-style:none}.chapters li{border-top:1px solid var(--rl-color-steel);padding:22px 0}.chapters a{display:block;min-height:44px;font-size:24px;font-weight:700}.chapters p{margin:6px 0}.guide-pagination{display:flex;flex-wrap:wrap;gap:24px;border-block:2px solid var(--rl-color-near-black);padding:24px 0;margin-top:40px}.guide-pagination a{min-height:44px}a:focus-visible{outline:3px solid var(--rl-color-near-black);outline-offset:4px}.sources{font-size:16px;overflow-wrap:anywhere}.sources li{margin:16px 0}sup a{font:700 12px var(--rl-font-data)}
'''
def page(title,description,path,body):
 canonical=BASE+path
 schema={'@context':'https://schema.org','@type':'Article','headline':title,'description':description,'url':canonical,'publisher':{'@type':'Organization','name':'Roadie Labs','url':BASE}}
 return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+' | Roadie Labs</title><meta name="description" content="'+html.escape(description,quote=True)+'"><link rel="canonical" href="'+canonical+'"><style>'+build_css()+'</style>'+get_ga4_head_snippet()+'<script type="application/ld+json">'+json.dumps(schema).replace('<','\\u003c')+'</script></head><body>'+get_site_header_html('products')+'<main id="rl-guide-page">'+body+'</main>'+get_mega_footer_html()+get_consent_banner_html()+'<script>'+get_site_header_js()+app_js()+'</script></body></html>'
def generate(output_dir):
 d=json.loads((ROOT/'guide/road-guide-content.json').read_text()); chapters=d['chapters']; output_dir.mkdir(parents=True,exist_ok=True)
 index='<p class="kicker">ROADIE LABS / FREE FIELD GUIDE</p><h1>'+html.escape(d['title'])+'</h1><p>'+html.escape(d['subtitle'])+'</p><ol class="chapters">'+''.join('<li><a href="/guide/'+c['id']+'/">'+str(c['number']).zfill(2)+' / '+html.escape(c['title'])+'</a><p>'+html.escape(c['subtitle'])+'</p></li>' for c in chapters)+'</ol><p><a href="/training-plans/#custom-plan-preview">Preview a plan for your race →</a></p>'
 (output_dir/'index.html').write_text(page(d['title'],d['meta_description'],'/guide/',index))
 for i,c in enumerate(chapters):
  sources={s['id']:j+1 for j,s in enumerate(c.get('sources',[]))}
  body='<nav><a href="/guide/">All eight chapters</a></nav><p class="kicker">CHAPTER '+str(c['number']).zfill(2)+'</p><h1>'+html.escape(c['title'])+'</h1><p>'+html.escape(c['subtitle'])+'</p>'
  for section in c['sections']:
   body+='<section class="rl-guide-section"><h2 class="rl-guide-section-title">'+html.escape(section['title'])+'</h2>'
   for b in section['blocks']:
    if b['type']!='reference_table':
     rendered=render_shared(b,c['id'])
     body+=re.sub(r'\[\^([\w.-]+)\]',lambda m:f'<sup><a href="#source-{m[1]}">[{sources[m[1]]}]</a></sup>',rendered)
    elif b['type']=='reference_table':body+=figure(b['title'],sequence([(str(row[0]),str(row[1])) for row in b['rows']]),'Keep this reference beside your race and training notes.')
   body+='</section>'
  if c['number']==2:
   race=json.loads((ROOT/'race-data/letape-du-tour.json').read_text())['race']
   ratings=race['fondo_rating']
   measures=[('Distance',ratings['distance']),('Climbing',ratings['climbing']),('Descent technicality',ratings['descent_technicality']),('Climate risk',ratings['climate_risk']),('Logistics',ratings['logistics'])]
   body+=figure("L’Etape du Tour / course demands",bars(measures,5,'/5'),'Roadie Labs catalogue ratings, not physical measurements. Check the linked profile for the recorded edition and provisional route details.')+'<p><a href="/race/letape-du-tour/">Read the race profile and sources →</a></p>'
  if c['number']==5:body+=table({'caption':'Fueling rehearsal log','headers':['Record','What to write down'],'rows':[['Ride duration','Time from start to finish'],['Intake','Products and total carbohydrate consumed'],['Refills','Where and how much you refilled'],['Tolerance','Any stomach trouble and when it began']]})
  if sources:body+='<section class="sources" id="sources"><h2>Sources</h2><ol>'+''.join('<li id="source-'+s['id']+'"><a href="'+html.escape(s['url'],quote=True)+'">'+html.escape(s['title'])+'</a></li>' for s in c['sources'])+'</ol></section>'
  body+='<nav class="guide-pagination" aria-label="Chapter navigation">'+(f'<a href="/guide/{chapters[i-1]["id"]}/">← Previous chapter</a>' if i else '')+(f'<a href="/guide/{chapters[i+1]["id"]}/">Next chapter →</a>' if i+1<len(chapters) else '')+'<a href="/training-plans/#custom-plan-preview">Preview your plan →</a></nav>'
  dest=output_dir/c['id'];dest.mkdir(exist_ok=True);(dest/'index.html').write_text(page(c['title'],c['subtitle'],'/guide/'+c['id']+'/',body))
 return output_dir
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'wordpress/output/guide');args=parser.parse_args();print(generate(args.output_dir))
