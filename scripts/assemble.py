"""Build a standalone offline HTML viewer from the cached Blender export.
No network is needed. Requires Python 3, and the pinned free esbuild binary in vendor.
"""
import base64,json,re,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
# Runtime assets are already embedded in the tracked standalone document.
# Extract the cache on a fresh checkout, avoiding duplicate binary assets in Git.
(R/'data').mkdir(exist_ok=True)
prior=(R/'dist/index.html').read_text()
for tag,filename in [('world-data','world.json'),('geometry-data','city.bin.gz'),('aerial-data','aerial.jpg'),('realism-data','realism.json')]:
 path=R/'data'/filename
 if not path.exists():
  value=re.search(r'<script id="'+tag+r'"[^>]*>(.*?)</script>',prior,re.S).group(1)
  if value.strip():path.write_bytes(value.encode() if filename.endswith('.json') else base64.b64decode(value.strip()))
  else:
   tagtext=re.search(r'<script id="'+tag+r'"[^>]*>',prior).group(0)
   files=json.loads(re.search(r"data-files='([^']+)'",tagtext).group(1))
   path.write_bytes(b''.join((R/'dist'/x).read_bytes() for x in files))
if not (R/'vendor/esbuild').exists():
 import urllib.request,tarfile,io,os,hashlib
 url='https://registry.npmjs.org/@esbuild/linux-x64/-/linux-x64-0.25.10.tgz'
 with urllib.request.urlopen(url,timeout=60) as response: archive=response.read()
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf: binary=tf.extractfile('package/bin/esbuild').read()
 assert hashlib.sha256(binary).hexdigest()=='b26b7502819ba76774dfd0b61f8c7d1ab8ee99482fca7b5970df746ce6042974'
 (R/'vendor/esbuild').write_bytes(binary);os.chmod(R/'vendor/esbuild',0o755)

subprocess.run([str(R/'vendor/esbuild'),str(R/'src/viewer.js'),'--bundle','--minify','--format=iife','--outfile='+str(R/'data/viewer.bundle.js')],check=True)
s=(R/'src/shell.html').read_text()
world=json.loads((R/'data/world.json').read_text())
s=s.replace('__LAYERS__',(R/'src/layers-data.json').read_text().replace('<','\\u003c'))
s=s.replace('__WORLD__',json.dumps(world,separators=(',',':')).replace('<','\\u003c'))
s=s.replace('__GEOMETRY__',base64.b64encode((R/'data/city.bin.gz').read_bytes()).decode())
s=s.replace('__REALISM__',(R/'data/realism.json').read_text())
s=s.replace('__AERIAL__',base64.b64encode((R/'data/aerial.jpg').read_bytes()).decode())
licenses=(R/'vendor/THREE-LICENSE.txt').read_text()+'\n\n'+(R/'vendor/ESBUILD-LICENSE.txt').read_text()
s=s.replace('__LICENSES__',licenses)
s=s.replace('__BUNDLE__',(R/'data/viewer.bundle.js').read_text().replace('</script','<\\/script'))
assert not re.search(r'__(WORLD|GEOMETRY|AERIAL|REALISM|BUNDLE)__',s)
(R/'exports').mkdir(exist_ok=True)
(R/'exports/Denver_Explorer_Offline.html').write_text(s)
# Serve large public assets as modest local chunks, without any external tile service.
assets=R/'dist/assets';assets.mkdir(exist_ok=True)
for old in assets.glob('*.bin'):old.unlink()
for tag,name in [('geometry-data','city.bin.gz'),('aerial-data','aerial.jpg'),('realism-data','realism.json'),('layers-data','layers.json')]:
 data=(R/'src/layers-data.json').read_bytes() if name=='layers.json' else (R/'data'/name).read_bytes();files=[]
 for i in range(0,len(data),1500000):
  filename=name.split('.')[0]+'.'+str(i//1500000).zfill(2)+'.bin';(assets/filename).write_bytes(data[i:i+1500000]);files.append('assets/'+filename)
 pattern=r'<script id="'+tag+r'"[^>]*>.*?</script>'
 replacement=f"""<script id="{tag}" type="application/octet-stream" data-files='{json.dumps(files,separators=(',',':'))}'></script>"""
 s=re.sub(pattern,lambda _:replacement,s,flags=re.S)
(R/'dist/index.html').write_text(s)
print('Built hosted entry:',len(s.encode()),'bytes; standalone export:',(R/'exports/Denver_Explorer_Offline.html').stat().st_size,'bytes')
