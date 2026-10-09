import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createAssetLoader,chooseQuality} from '../src/assets.mjs';
assert.equal(chooseQuality({coarse:true}), 'low');
assert.equal(chooseQuality({memory:4}), 'low');
assert.equal(chooseQuality({saveData:true}), 'low');
assert.equal(chooseQuality({}), 'balanced');
assert.equal(chooseQuality({requested:'high',coarse:true}), 'high');
assert.equal(chooseQuality({requested:'garbage'}), 'balanced');
let active=0,maximum=0;const attempts=new Map();
const load=createAssetLoader(async path=>{
 active++;maximum=Math.max(maximum,active);
 try{await new Promise(resolve=>setTimeout(resolve,2));const n=(attempts.get(path)||0)+1;attempts.set(path,n);if(path==='retry'&&n===1)throw Error('Temporary failure');return {ok:true,arrayBuffer:async()=>Uint8Array.of(path==='retry'?99:Number(path)).buffer};}finally{active--;}
},3);
const [a,b]=await Promise.all([load(['1','2','3','4']),load(['5','retry','6'])]);
assert.deepEqual([...a],[1,2,3,4]);assert.deepEqual([...b],[5,99,6]);assert(maximum<=3);assert.equal(attempts.get('retry'),2);
let failures=0;await assert.rejects(createAssetLoader(async()=>{failures++;return {ok:false,status:404}})(['missing']));assert.equal(failures,2);
await assert.rejects(load([]));
const viewer=fs.readFileSync('src/viewer.js','utf8');
assert(!viewer.includes('__OFFLINE_SOURCE__'));
assert(!viewer.includes('AbortSignal.timeout'));
assert(viewer.indexOf('prepareRenderer();await loadHostedAssets()')>0);
assert.match(viewer,/if\(!dirty\)return/);
assert.match(viewer,/if\(quality==='high'\)captureDistrictReflection/);
assert.match(viewer,/assetBuffers.delete\('geometry-data'\)/);
const html=fs.readFileSync('dist/index.html','utf8');assert(html.length<850000,'Hosted HTML budget');
assert.match(html,/data-light-files=/);assert.match(html,/assets\/viewer-[a-f0-9]+\.js/);
assert(!html.includes('window.__OFFLINE_SOURCE__'));
console.log('Adaptive profiles, three-request limit, retries/failure, binary buffer lifecycle, early graphics check, on-demand rendering and hosted size budget pass.');
