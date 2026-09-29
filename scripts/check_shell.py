import json,re
from html.parser import HTMLParser
from pathlib import Path
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.ids={};self.labels=[];self.scripts=[];self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:
   assert a['id'] not in self.ids,'Duplicate ID '+a['id'];self.ids[a['id']]=(tag,a)
  if tag=='label' and 'for' in a:self.labels.append(a['for'])
  if tag=='script' and 'src' in a:self.scripts.append(a['src'])
  if tag=='a' and 'href' in a:self.links.append(a['href'])
p=Parser();p.feed(Path('exports/Denver_Explorer_Offline.html').read_text())
for label in p.labels:assert label in p.ids,label
for source in Path('src').glob('*.js'):
 for ref in re.findall(r"\$\('([^']+)'\)",source.read_text()):assert ref in p.ids,(source,ref)
assert not p.scripts
for id in ['tour-pause','tour-prev','tour-next','tour-exit','begin-tour','free-start','roof-view','layers-button','retry-3d']:assert p.ids[id][0]=='button'
for k in ['layer-labels','layer-routes','layer-rings','layer-boundaries','layer-heights','layer-history']:assert p.ids[k][1]['type']=='checkbox'
assert 'prefers-reduced-motion' in Path('src/shell.html').read_text()
hosted=Path('dist/index.html').read_text()
for raw in re.findall(r"data-files='([^']+)'",hosted):
 for f in json.loads(raw):assert (Path('dist')/f).is_file(),f
print(f'{len(p.ids)} unique UI IDs, label associations, control types, reduced-motion rules, offline embedding and hosted chunk references pass.')
