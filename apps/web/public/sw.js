const CACHE_NAME = 'task-dashboard-v1';
const APP_SHELL = [
  '/dashboard',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// Install: pre-cache app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)),
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)),
        ),
      ),
  );
  self.clients.claim();
});

// Push: show notification + set app badge when a Claude run finishes.
self.addEventListener('push', (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { /* noop */ }
  const title = data.title || 'Claude';
  const options = {
    body: data.body || '',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png',
    tag: data.conversationId || 'claude',
    data: { conversationId: data.conversationId },
  };
  event.waitUntil((async () => {
    await self.registration.showNotification(title, options);
    if (self.navigator && self.navigator.setAppBadge) {
      try { await self.navigator.setAppBadge(data.badge || 1); } catch (e) { /* noop */ }
    }
  })());
});

// Tap a notification: focus the chat (and clear the badge).
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil((async () => {
    if (self.navigator && self.navigator.clearAppBadge) {
      try { await self.navigator.clearAppBadge(); } catch (e) { /* noop */ }
    }
    const wins = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of wins) { if (c.url.includes('/chat')) return c.focus(); }
    return self.clients.openWindow('/chat');
  })());
});

// Fetch: network-first for API, stale-while-revalidate for assets
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // API calls: network only (we need fresh data)
  if (request.url.includes('/api/')) {
    return;
  }

  // Everything else: stale-while-revalidate
  event.respondWith(
    caches.match(request).then((cached) => {
      const fetchPromise = fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() => cached);

      return cached || fetchPromise;
    }),
  );
});
