"""Repack restored repository assets after intentionally editing them."""
from pathlib import Path
import json,struct,hashlib,zlib
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'asset-bundles/manifest.json').read_text())
# The checked-in list is the complete set of packed asset paths.
paths=json.loads((root/'asset-bundles/paths.json').read_text())
out=bytearray()
for path in paths:
 b=(root/path).read_bytes();h=json.dumps({'path':path,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()},separators=(',',':')).encode();out+=struct.pack('>I',len(h))+h+b
co=zlib.compressobj(9,zlib.DEFLATED,31);data=co.compress(out)+co.flush();parts=[]
for old in (root/'asset-bundles').glob('assets-*.gzpart'):old.unlink()
for i,start in enumerate(range(0,len(data),4*1024*1024)):
 b=data[start:start+4*1024*1024];name=f'assets-{i:03}.gzpart';(root/'asset-bundles'/name).write_bytes(b);parts.append({'name':name,'sha256':hashlib.sha256(b).hexdigest(),'size':len(b)})
(root/'asset-bundles/manifest.json').write_text(json.dumps({'format':1,'files':len(paths),'parts':parts},indent=2)+'\n')
print(f'Packed {len(paths)} assets in {len(parts)} parts.')
