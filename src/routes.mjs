// Routes follow connected OSM ways; endpoints are nearest mapped nodes.
// Street centerlines can be included: this is orientation, not turn-by-turn guidance.
export function makeRoutes(roads,stops){
 const graph=new Map(),points=new Map();
 for(const r of roads){if(['motorway','motorway_link','trunk','trunk_link','construction','proposed','raceway'].includes(r.type)||['private','no'].includes(r.access)||r.foot==='no')continue;
 r.nodes.forEach((id,i)=>{points.set(id,r.points[i]);if(!graph.has(id))graph.set(id,[]);if(i){const a=r.nodes[i-1],d=Math.hypot(r.points[i][0]-r.points[i-1][0],r.points[i][1]-r.points[i-1][1]);graph.get(id).push([a,d]);graph.get(a).push([id,d]);}});}
 const nearest=p=>[...points.keys()].reduce((a,b)=>!a||Math.hypot(...points.get(b).map((v,i)=>v-p[i]))<Math.hypot(...points.get(a).map((v,i)=>v-p[i]))?b:a,null);
 return stops.slice(1).map((p,i)=>{const start=nearest(stops[i]),end=nearest(p),distance=new Map([[start,0]]),previous=new Map(),queue=new Set([start]),visited=new Set();
 while(queue.size){let u=null;for(const k of queue)if(u===null||distance.get(k)<distance.get(u))u=k;queue.delete(u);if(u===end)break;visited.add(u);for(const [v,cost] of graph.get(u)||[]){const d=distance.get(u)+cost;if(!visited.has(v)&&d<(distance.get(v)??Infinity)){distance.set(v,d);previous.set(v,u);queue.add(v);}}}
 if(!distance.has(end))return {points:[],length:0,available:false};const ids=[end];while(ids.at(-1)!==start){const prior=previous.get(ids.at(-1));if(prior===undefined)return {points:[],length:0,available:false};ids.push(prior);}return {points:ids.reverse().map(id=>points.get(id)),length:distance.get(end),available:true};});
}
