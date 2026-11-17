/*
 * MLBB Tracker â€” service worker.
 *
 * Makes the web app installable and usable offline:
 *   - the app shell (HTML, bootstrap, main.dart.js, icons) is precached;
 *   - CanvasKit (the Flutter renderer) is precached best-effort, so the first
 *     offline launch still paints;
 *   - navigations are network-first with a cached shell fallback;
 *   - static assets are stale-while-revalidate (fast, self-updating);
 *   - /canvaskit/ is cache-first (large, immutable per build).
 *
 * API calls are NEVER cached: stale numbers presented as live would be
 * fabricated data. Offline, the app shows its own honest error states.
 *
 * Bump CACHE_VERSION on every release â€” the activate handler deletes caches
 * from previous versions.
 */

'use strict';

const CACHE_VERSION = 'v2';
const SHELL_CACHE = `mlbb-shell-${CACHE_VERSION}`;
const STATIC_CACHE = `mlbb-static-${CACHE_VERSION}`;

const SHELL_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/flutter_bootstrap.js',
  '/main.dart.js',
  '/favicon.png',
  '/apple-touch-icon.png',
  '/icons/Icon-192.png',
  '/icons/Icon-512.png',
  '/icons/Icon-maskable-192.png',
  '/icons/Icon-maskable-512.png',
  // Font manifest + the icon fonts Flutter renders with. Without these the
  // first offline launch would show fallback glyphs.
  '/assets/AssetManifest.bin.json',
  '/assets/FontManifest.json',
  '/assets/fonts/MaterialIcons-Regular.otf',
  '/assets/packages/cupertino_icons/assets/CupertinoIcons.ttf',
];

// CanvasKit: both the default and the Chromium variant (Chrome picks the
// latter). The skwasm files are only used by `--wasm` builds and are
// deliberately not precached - they would add ~8 MB nobody downloads here.
// A miss must not fail the install, so each entry is added on its own.
const OPTIONAL_URLS = [
  '/canvaskit/canvaskit.js',
  '/canvaskit/canvaskit.wasm',
  '/canvaskit/chromium/canvaskit.js',
  '/canvaskit/chromium/canvaskit.wasm',
];

// Always live: the API and anything that must reflect the current state.
const NETWORK_ONLY = [
  /^\/api(\/|$)/,
  /^\/download(\/|$)/,
  /^\/docs(\/|$)/,
  /^\/redoc(\/|$)/,
  /^\/openapi\.json$/,
  /^\/health(\/|$)/,
];

async function addAll(cache, urls) {
  await Promise.all(
    urls.map(async (url) => {
      try {
        await cache.add(new Request(url, { cache: 'reload' }));
      } catch (error) {
        // Optional assets may not exist for this build; never fail the install.
        console.debug('[sw] skipped', url, error);
      }
    })
  );
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const shell = await caches.open(SHELL_CACHE);
      await addAll(shell, SHELL_URLS);
      const statics = await caches.open(STATIC_CACHE);
      await addAll(statics, OPTIONAL_URLS);
      await self.skipWaiting();
    })()
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keep = new Set([SHELL_CACHE, STATIC_CACHE]);
      const names = await caches.keys();
      await Promise.all(names.filter((name) => !keep.has(name)).map((name) => caches.delete(name)));
      await self.clients.claim();
    })()
  );
});

async function cached(cacheName, request) {
  const cache = await caches.open(cacheName);
  // ignoreVary: responses carry `Vary: Origin` (CORS middleware), and module
  // script requests differ from the precache request in that header.
  return (await cache.match(request, { ignoreSearch: true, ignoreVary: true })) || null;
}

async function networkFirstNavigation(request) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      // Keep the shell current for the next offline launch.
      const cache = await caches.open(SHELL_CACHE);
      cache.put('/index.html', response.clone());
    }
    return response;
  } catch (error) {
    const shell = await cached(SHELL_CACHE, '/index.html');
    if (shell) return shell;
    return new Response('MLBB Tracker is offline and its app shell has not been cached yet.', {
      status: 503,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}

async function cacheFirst(request, cacheName) {
  const hit = await cached(cacheName, request);
  if (hit) return hit;
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return new Response('Offline: this asset is not cached.', {
      status: 503,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
    });
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const hit = await cached(cacheName, request);
  const network = fetch(request)
    .then(async (response) => {
      if (response && response.ok) {
        const cache = await caches.open(cacheName);
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);

  if (hit) return hit;
  const fresh = await network;
  if (fresh) return fresh;
  return new Response('Offline: this asset is not cached.', {
    status: 503,
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return; // let the browser handle it
  if (NETWORK_ONLY.some((pattern) => pattern.test(url.pathname))) return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(request));
    return;
  }
  if (url.pathname.startsWith('/canvaskit/')) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }
  event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
});
