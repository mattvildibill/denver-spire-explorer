import * as THREE from '../vendor/three.module.js';
import { HDRLoader } from '../vendor/HDRLoader.js';
let textures={},environment;
export async function loadRealism(renderer){
 const payload=JSON.parse(document.getElementById('realism-data').textContent);
 await Promise.all(Object.entries(payload.images).map(async([key,data])=>{const t=await new THREE.TextureLoader().loadAsync('data:image/jpeg;base64,'+data);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());if(key.endsWith('color'))t.colorSpace=THREE.SRGBColorSpace;textures[key]=t;}));
 const raw=Uint8Array.from(atob(payload.hdr),c=>c.charCodeAt(0));const parsed=new HDRLoader().parse(raw.buffer);const t=new THREE.DataTexture(parsed.data,parsed.width,parsed.height,THREE.RGBAFormat,parsed.type);t.flipY=true;t.minFilter=THREE.LinearFilter;t.magFilter=THREE.LinearFilter;t.mapping=THREE.EquirectangularReflectionMapping;t.colorSpace=THREE.LinearSRGBColorSpace;t.needsUpdate=true;
 const pmrem=new THREE.PMREMGenerator(renderer);environment=pmrem.fromEquirectangular(t).texture;pmrem.dispose();t.dispose();return environment;
}
export function finishMaterial(mat,g,photos=textures){
 const type=/neutral asphalt/.test(g.name)?'asphalt_02':/concrete with mapped|Realism curb/.test(g.name)?'concrete_pavement_02':g.name==='Realism wall brick'?'brick_wall_001':null;
 const prior=mat.onBeforeCompile;const oldkey=mat.customProgramCacheKey();
 // Baked, geometric ambient visibility affects indirect light, preserving direct sun.
 mat.onBeforeCompile=shader=>{
  prior(shader);
  shader.vertexShader='attribute float ambientVisibility; varying float vVisibility; varying vec3 vRealPosition; varying vec3 vRealNormal;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvVisibility=ambientVisibility; vRealPosition=(modelMatrix*vec4(position,1.)).xyz;vRealNormal=normalize(mat3(modelMatrix)*normal);');
  shader.fragmentShader='varying float vVisibility; varying vec3 vRealPosition; varying vec3 vRealNormal;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <aomap_fragment>','#include <aomap_fragment>\nreflectedLight.indirectDiffuse*=mix(.4,1.,vVisibility);');
  if(type&&['color','roughness','normal_opengl'].every(k=>photos[type+'_'+k])){
   const tile=type==='concrete_pavement_02'?1.8:3.;
   shader.uniforms.photoColor={value:photos[type+'_color']};shader.uniforms.photoRough={value:photos[type+'_roughness']};shader.uniforms.photoNormal={value:photos[type+'_normal_opengl']};
   shader.fragmentShader=`uniform sampler2D photoColor;uniform sampler2D photoRough;uniform sampler2D photoNormal;\n`+shader.fragmentShader;
   const projection=`vec3 rw=abs(normalize(vRealNormal));vec2 puv=rw.y>.6?vRealPosition.xz:rw.x>rw.z?vec2(vRealPosition.z,vRealPosition.y):vRealPosition.xy;puv/=${tile.toFixed(2)};`;
   shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>\n${projection}\nvec3 photo=texture2D(photoColor,puv).rgb;diffuseColor.rgb=mix(diffuseColor.rgb,photo,${g.aerial?'.86':'1.'});`);
   shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nroughnessFactor=clamp(texture2D(photoRough,puv).g,.5,1.);');
   // Derivative tangent frame accommodates the world-space pavement and wall projections.
   shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>\nvec3 q0=dFdx(-vViewPosition),q1=dFdy(-vViewPosition);vec2 st0=dFdx(puv),st1=dFdy(puv);vec3 T=q0*st1.y-q1*st0.y;vec3 B=-q0*st1.x+q1*st0.x;float inv=inversesqrt(max(max(dot(T,T),dot(B,B)),1.e-10));vec3 nm=texture2D(photoNormal,puv).xyz*2.-1.;nm.xy*=.35;normal=normalize(mat3(T*inv,B*inv,normal)*nm);`);
  }
 };
 mat.customProgramCacheKey=()=>oldkey+'realism-v2-'+(type||'plain');
 if(/glazing|curtain wall|mullions/.test(g.name)){mat.roughness=.23;mat.metalness=.18;mat.envMapIntensity=.85;}
 return mat;
}
// Reflections use the actual modeled neighborhood. One static capture avoids six renders per frame.
export function captureDistrictReflection(scene,renderer,meshes){
 const target=new THREE.WebGLCubeRenderTarget(256,{type:THREE.HalfFloatType,generateMipmaps:true,minFilter:THREE.LinearMipmapLinearFilter});
 const probe=new THREE.CubeCamera(.5,2800,target);probe.position.set(-75,65,75);scene.add(probe);probe.update(renderer,scene);
 const pmrem=new THREE.PMREMGenerator(renderer);const reflected=pmrem.fromCubemap(target.texture).texture;
 for(const m of meshes)if(/SPIRE|Spire|recessed glazing|curtain wall/.test(m.name)){m.material.envMap=reflected;m.material.envMapIntensity=.8;m.material.needsUpdate=true;}
 pmrem.dispose();target.dispose();scene.remove(probe);
}
