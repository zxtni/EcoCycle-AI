const CACHE="ecocycle-shell-v1";
self.addEventListener("install",event=>{
 event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(["/offline.html","/icon-192.png","/icon-512.png"])));
 self.skipWaiting();
});
self.addEventListener("activate",event=>{
 event.waitUntil(caches.keys().then(names=>Promise.all(names.filter(name=>name.startsWith("ecocycle-shell-")&&name!==CACHE).map(name=>caches.delete(name)))).then(()=>self.clients.claim()));
});
self.addEventListener("fetch",event=>{
 const request=event.request;
 if(request.method!=="GET" || new URL(request.url).origin!==self.location.origin)return;
 if(request.mode==="navigate" && !new URL(request.url).pathname.startsWith("/api/")){
   event.respondWith(fetch(request).catch(()=>caches.match("/offline.html")));
 }
});
