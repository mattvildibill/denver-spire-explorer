// DOM-adapter regression checks. Browser layout and GPU behavior are tested separately.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {fallback,extendPlaces} from '../src/exploration.js';
const src=fs.readFileSync('src/viewer.js','utf8'),shell=fs.readFileSync('src/shell.html','utf8');
const nodes=new Map();
function node(id){if(!nodes.has(id)){const classes=new Set();nodes.set(id,{id,hidden:false,children:[],attrs:{},classList:{add:k=>classes.add(k),toggle(k,on){on?classes.add(k):classes.delete(k)},contains:k=>classes.has(k)},appendChild(child){this.children.push(child)},replaceChildren(){this.children=[]},setAttribute(k,v){this.attrs[k]=String(v)},focus(){this.focused=true},close(){this.open=false}})}return nodes.get(id)}
const canvas=node('fallback-map');canvas.width=700;canvas.height=800;const coordinates=[];canvas.getContext=()=>new Proxy({},{get:(_target,key)=>key==='moveTo'||key==='lineTo'?((x,y)=>coordinates.push([x,y])):()=>{},set:()=>true});
const body=node('body');body.children=[node('view'),node('header'),node('loading'),node('fallback')];
globalThis.document={body,getElementById:node,querySelectorAll:()=>[],createElement:tag=>({tag,children:[],appendChild(child){this.children.push(child)}}),createTextNode:text=>({textContent:text})};
globalThis.location={reload(){}};
const world=JSON.parse(fs.readFileSync('data/world.json')),data=JSON.parse(fs.readFileSync('src/layers-data.json')),places=Function('return '+src.match(/const places=(\[[\s\S]*?\n\]);/)[1])();extendPlaces(places,world,data);
fallback(world,places,'3D is unavailable.');
assert(!node('fallback').hidden);assert(node('fallback').focused);assert(body.children.filter(n=>n.id!=='fallback').every(n=>n.inert));assert(!node('fallback').inert);assert.equal(node('fallback-list').children.length,6);assert.equal(node('fallback-list').children[0].children[0].textContent,'Spire');assert(coordinates.every(p=>p.every(Number.isFinite)));
fallback(world,places,'Retry still needs graphics support.');assert.equal(node('fallback-list').children.length,6,'Repeated fallback should not duplicate destinations');
const helper=src.slice(src.indexOf('function setSceneOnly('),src.indexOf('function setup('));const setSceneOnly=Function('$','document',helper+';return setSceneOnly;')(node,document);
for(const on of [true,false,true,false]){setSceneOnly(on);assert.equal(body.classList.contains('scene-only'),on);assert.equal(node('scene-toggle').attrs['aria-pressed'],String(on));assert.equal(node('scene-toggle').attrs['aria-label'],on?'Show panels':'Hide panels')}
assert.equal((shell.match(/name="description"/g)||[]).length,1);assert.match(shell,/aria-labelledby="welcome-title"/);assert.match(shell,/aria-label="Close introduction"/);assert.match(shell,/\.scene-only, \.immersive/);
console.log('Scene-only controls, repeated toggles, accessible fallback focus/inert state, six nonduplicated destinations, canvas coordinates and metadata pass.');
