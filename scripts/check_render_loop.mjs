// Execute the actual frame loop against real Three.js camera math and a mock renderer.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import * as THREE from '../vendor/three.module.js';
const source=fs.readFileSync('src/viewer.js','utf8');
const loopSource=source.slice(source.indexOf('const previousPosition='),source.indexOf('// Test graphics'));
const harness=Function('THREE',`
 let ready=true,last=0,transition=null,quality='balanced',frameNo=0,dirty=true,autoQuality=true,slowFrames=0,mode='fly',yaw=0,pitch=0;
 let walking=false,animated=false,renders=0,treeUpdates=0;
 const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera();camera.position.set(0,200,300);
 const document={hidden:false},requestAnimationFrame=()=>{},$=()=>({value:0});
 const renderer={shadowMap:{needsUpdate:false},render(){renders++;}};
 const euler=new THREE.Euler(0,0,0,'YXZ');
 const sun=new THREE.DirectionalLight();
 const treesLOD={update(){treeUpdates++;}},features={update(){},animating:()=>animated};
 const move=dt=>{if(walking)camera.position.x+=dt*30},drawMap=()=>{},updateExternal=()=>{},updateLabels=()=>{},toast=()=>{};
 const applyQuality=q=>{quality=q;dirty=true;};
 ${loopSource}
 return {loop,stats:()=>({renders,treeUpdates,last,quality}),walking:v=>walking=v,animated:v=>animated=v,dirty:()=>dirty=true,hidden:v=>document.hidden=v};
`)(THREE);
harness.loop(16);assert.equal(harness.stats().renders,1);
for(let i=2;i<100;i++)harness.loop(i*16);
assert.equal(harness.stats().renders,1,'An idle scene must not submit GPU frames');
harness.dirty();harness.loop(1600);assert.equal(harness.stats().renders,2,'UI change redraws');
harness.walking(true);for(let i=101;i<111;i++)harness.loop(i*16);assert.equal(harness.stats().renders,12,'Movement remains animated');
harness.walking(false);harness.hidden(true);harness.loop(2000);assert.equal(harness.stats().renders,12);assert.equal(harness.stats().last,0);
harness.hidden(false);harness.animated(true);harness.loop(2100);assert.equal(harness.stats().renders,13,'Tour/lighting animation wakes drawing');
harness.animated(false);harness.loop(2116);assert.equal(harness.stats().renders,13);
assert(harness.stats().treeUpdates<12,'Tree LOD does not rebuild every moving frame');
console.log('Actual render loop: idle, UI redraw, motion, hidden/resumed tab, animated features and throttled tree LOD pass.');
