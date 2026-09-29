import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {localToLonLat} from '../src/navigation.mjs';
const world=JSON.parse(fs.readFileSync('data/world.json'));
function xy(lon,lat){let x=(lon-world.origin[0])*85000,y=(lat-world.origin[1])*111000;for(let i=0;i<8;i++){const ll=localToLonLat(x,y,world.origin);x+=(lon-ll[0])*85000;y+=(lat-ll[1])*111000;}return [Number(x.toFixed(3)),Number(y.toFixed(3))];}
const osm=JSON.parse(gunzipSync(fs.readFileSync('data/routes_osm.json.gz')));
const roads=osm.elements.filter(e=>e.geometry&&e.nodes).map(e=>({id:e.id,name:e.tags.name||'',type:e.tags.highway,access:e.tags.access||'',foot:e.tags.foot||'',nodes:e.nodes,points:e.geometry.map(p=>xy(p.lon,p.lat))}));
const neighborhoods=fs.existsSync('data/neighborhoods.geojson')?JSON.parse(fs.readFileSync('data/neighborhoods.geojson')).features.map(f=>({name:f.properties.NBHD_NAME||f.properties.NEIGHBORHOOD||Object.values(f.properties).find(v=>typeof v==='string'),rings:(f.geometry.type==='MultiPolygon'?f.geometry.coordinates.flat():f.geometry.coordinates).map(r=>r.map(p=>xy(...p)))})):[];
const ccc=world.buildings.filter(b=>b.name==='Colorado Convention Center');const all=ccc.flatMap(b=>b.rings[0]);const center=[(Math.min(...all.map(p=>p[0]))+Math.max(...all.map(p=>p[0])))/2,(Math.min(...all.map(p=>p[1]))+Math.max(...all.map(p=>p[1])))/2];
const data={roads,neighborhoods,ccc:center,roadTimestamp:osm.osm3s.timestamp_osm_base,neighborhoodSource:'https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_ADMN_NEIGHBORHOOD_A/FeatureServer',downloaded:'2026-09-09'};
fs.writeFileSync('src/layers-data.json',JSON.stringify(data));console.log({roads:roads.length,neighborhoods:neighborhoods.map(n=>n.name),ccc:center});
