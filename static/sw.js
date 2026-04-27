// Service Worker for School Copilot PWA
// Caches the app shell for offline launch; network-first for API calls.

const CACHE = "school-copilot-v1";
const SHELL = ["/", "/static/manifest.json", "/static/icon-192.png", "/static/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);

  // Always network-first for API routes
  if (url.pathname.startsWith("/chat") ||
      url.pathname.startsWith("/sms") ||
      url.pathname.startsWith("/email") ||
      url.pathname.startsWith("/auth") ||
      url.pathname.startsWith("/onboarding")) {
    return; // Let browser handle — no caching
  }

  // Cache-first for static assets and app shell
  e.respondWith(
    caches.match(e.request).then((cached) => {
      if (cached) return cached;
      return fetch(e.request).then((response) => {
        if (response.ok && e.request.method === "GET") {
          const clone = response.clone();
          caches.open(CACHE).then((c) => c.put(e.request, clone));
        }
        return response;
      });
    }).catch(() => {
      // Offline fallback: return cached root if available
      if (e.request.destination === "document") {
        return caches.match("/");
      }
    })
  );
});
