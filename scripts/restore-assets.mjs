import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve,dirname,sep} from 'node:path';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..');
const hash=b=>createHash('sha256').update(b).digest('hex');
const m=JSON.parse(readFileSync(resolve(root,'asset-bundles/manifest.json')));
const compressed=m.parts.map(p=>{if(!/^assets-[0-9]+[.]gzpart$/.test(p.name))throw Error('Unsafe asset part');const b=readFileSync(resolve(root,'asset-bundles',p.name));if(hash(b)!==p.sha256)throw Error('Asset bundle checksum mismatch');return b});
const bytes=gunzipSync(Buffer.concat(compressed));let pos=0,count=0;
while(pos<bytes.length){const len=bytes.readUInt32BE(pos);pos+=4;const f=JSON.parse(bytes.subarray(pos,pos+len));pos+=len;const dest=resolve(root,f.path);if(!dest.startsWith(root+sep)||f.path.split('/').some(p=>p.startsWith('.'))||!Number.isSafeInteger(f.size)||f.size<0)throw Error('Unsafe asset entry');const data=bytes.subarray(pos,pos+f.size);pos+=f.size;if(data.length!==f.size||hash(data)!==f.sha256)throw Error('Asset checksum mismatch');if(existsSync(dest)&&hash(readFileSync(dest))!==f.sha256)throw Error('Local asset modified: '+f.path+'; preserve it before restoring');mkdirSync(dirname(dest),{recursive:true});if(!existsSync(dest))writeFileSync(dest,data);count++;}
if(count!==m.files)throw Error('Asset count mismatch');console.log(`Verified ${count} repository-owned assets.`);
