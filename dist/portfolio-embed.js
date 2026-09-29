(() => {
 if (window.parent === window) return;
 let origin;
 try { origin = new URL(document.referrer).origin; } catch { return; }
 if (!['https://mattvildibill.com','https://www.mattvildibill.com','http://localhost:3000'].includes(origin)) return;
 document.documentElement.dataset.portfolioProject = 'denver';
 const style = document.createElement('link'); style.rel='stylesheet'; style.href='/portfolio-embed.css'; document.head.appendChild(style);
 const send = (type, hint) => parent.postMessage({type, hint}, origin);
 send('portfolio:ready');
 document.addEventListener('keydown', event => { if(event.key==='Escape' && !event.defaultPrevented && !document.pointerLockElement && !document.querySelector('dialog[open], [role="dialog"], [role="menu"], [role="listbox"]')) send('portfolio:close'); });
 const check = () => {
   if(document.querySelector('#fallback:not([hidden])')) send('portfolio:hint','Map edition: the 3D view requires WebGL.');
   else if(document.querySelector('.art-only')) send('portfolio:hint','Original-art edition: the walkable worlds require WebGL.');
   else if(document.querySelector('.aerial-fallback')) send('portfolio:hint','Aerial edition: the 3D view requires WebGL.');
 };
 const observer=new MutationObserver(check); observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class','hidden']}); check();
 addEventListener('pagehide',()=>observer.disconnect(),{once:true});
})();
