/* Dziennik WF — service worker.
 * Po co: aplikacja ma działać offline na sali gimnastycznej (brak wifi).
 * Strategia:
 *  - dokument (nawigacja): network-first → fallback cache  (świeże gdy online,
 *    działa gdy offline; aktualizacje wchodzą same przy następnym wejściu online)
 *  - shell (manifest, ikony) i Google Fonts: stale-while-revalidate
 * UWAGA: przy każdej zmianie dziennik_wf.html PODBIJ CACHE_VERSION — inaczej
 * stary klient może serwować starą wersję z cache zanim sieć odpowie.
 */
const CACHE_VERSION = 'dziennik-wf-v1';
const SHELL = [
  './dziennik_wf.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isFontHost(url) {
  return url.host === 'fonts.googleapis.com' || url.host === 'fonts.gstatic.com';
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Dokument: network-first (świeże gdy online), cache fallback (offline na sali).
  if (req.mode === 'navigate' || req.destination === 'document') {
    e.respondWith(
      fetch(req)
        .then(resp => {
          const copy = resp.clone();
          caches.open(CACHE_VERSION).then(c => c.put('./dziennik_wf.html', copy));
          return resp;
        })
        .catch(() => caches.match('./dziennik_wf.html').then(r => r || caches.match(req)))
    );
    return;
  }

  // Shell same-origin + fonty Google: stale-while-revalidate.
  if (url.origin === self.location.origin || isFontHost(url)) {
    e.respondWith(
      caches.match(req).then(cached => {
        const net = fetch(req).then(resp => {
          if (resp && (resp.ok || resp.type === 'opaque')) {
            const copy = resp.clone();
            caches.open(CACHE_VERSION).then(c => c.put(req, copy));
          }
          return resp;
        }).catch(() => cached);
        return cached || net;
      })
    );
  }
});
