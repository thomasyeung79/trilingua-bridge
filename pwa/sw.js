/* TriLingua Bridge — Service Worker */

const CACHE_NAME = "trilingua-bridge-v1";
const STATIC_ASSETS = [
  "/",
  "/manifest.json",
  "/icon.svg",
  "/icon-192.png",
  "/icon-512.png",
];

/* ── Install: pre-cache static assets ── */
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        /* Non-critical assets; skip if offline at install time */
      });
    })
  );
  /* Activate immediately without waiting for reload */
  self.skipWaiting();
});

/* ── Activate: clean old caches ── */
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  /* Take control of all clients immediately */
  self.clients.claim();
});

/* ── Fetch: cache-first for assets, network-first for API/Streamlit ── */
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  /* Skip non-GET requests and browser extensions */
  if (request.method !== "GET" || !url.protocol.startsWith("http")) return;

  /* === Cache-first for static PWA assets === */
  if (STATIC_ASSETS.includes(url.pathname)) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request))
    );
    return;
  }

  /* === Network-first for everything else (Streamlit pages, API) === */
  event.respondWith(
    fetch(request)
      .then((response) => {
        /* Cache successful responses for offline fallback */
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        /* Offline: try cache, then show offline page */
        return caches.match(request).then(
          (cached) =>
            cached ||
            new Response(
              `<html><body style="font-family:system-ui;padding:2rem;text-align:center">
                <h2>🌐 TriLingua Bridge</h2>
                <p>You're offline. Connect to the internet and try again.</p>
                <button onclick="location.reload()">Retry</button>
              </body></html>`,
              {
                status: 503,
                statusText: "Service Unavailable",
                headers: { "Content-Type": "text/html;charset=UTF-8" },
              }
            )
        );
      })
  );
});
