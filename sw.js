const CACHE='starfill-shell-v16';
const FILES=['./','./index.html','./styles.css?v=20261003-7','./main.js?v=20261003-15','./questions.json?v=reviewed2','./manifest.webmanifest','./star.svg'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(FILES)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{if(event.request.method!=='GET')return;event.respondWith((async()=>{const cache=await caches.open(CACHE);try{const response=await fetch(event.request);if(response.ok&&new URL(event.request.url).origin===location.origin)cache.put(event.request,response.clone());return response;}catch(error){return await caches.match(event.request)||await cache.match('./index.html')}})())});
