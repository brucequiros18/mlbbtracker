/*
 * The app shell cache.
 *
 * Rules:
 * - the shell (HTML, JS, CSS, icons) is cached, so the app opens offline;
 * - API responses are NEVER cached - live data must stay live, and a stale
 *   ranking would be a lie;
 * - navigations fall back to the cached shell when the network is gone.
 */

const SHELL_CACHE = 'mlbb-shell-v1'
const APP_SHELL = ['/app/index.html', '/manifest.webmanifest']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .catch(() => undefined)
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== SHELL_CACHE).map((key) => caches.delete(key))),
      )
      .then(() => self.clients.claim()),
  )
})

function isApiRequest(url) {
  return url.pathname.startsWith('/api/')
}

function isShellAsset(url) {
  return url.pathname.startsWith('/app/') || url.pathname === '/manifest.webmanifest'
}

self.addEventListener('fetch', (event) => {
  const request = event.request
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return

  // Live data: always go to the network, never cache.
  if (isApiRequest(url)) return

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone()
          caches.open(SHELL_CACHE).then((cache) => cache.put('/app/index.html', copy))
          return response
        })
        .catch(() =>
          caches.match('/app/index.html').then((cached) => cached ?? Response.error()),
        ),
    )
    return
  }

  if (isShellAsset(url)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached
        return fetch(request).then((response) => {
          if (response.ok) {
            const copy = response.clone()
            caches.open(SHELL_CACHE).then((cache) => cache.put(request, copy))
          }
          return response
        })
      }),
    )
  }
})
