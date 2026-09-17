/* Dziennik WF — service worker.
 * Po co: aplikacja ma działać offline na sali gimnastycznej (brak wifi).
 * Strategia:
 *  - dokument (nawigacja): network-first → fallback cache  (świeże gdy online,
 *    działa gdy offline; aktualizacje wchodzą same przy następnym wejściu online)
 *  - shell (manifest, ikony): stale-while-revalidate
 * Od 2026-09-14 (Faza 7) kroje pisma siedza w samym pliku HTML, wiec regula
 * dla fonts.googleapis.com/gstatic zostala usunieta - nie ma juz czego cache'owac.
 * UWAGA: przy każdej zmianie dziennik_wf.html PODBIJ CACHE_VERSION — inaczej
 * stary klient może serwować starą wersję z cache zanim sieć odpowie.
 */
// v2: Fazy 5-7 (klawiatura, szyfrowane kopie, kroje w pliku). Podbicie wersji
// jest tu KONIECZNE - bez niego klient z cache serwowalby dziennik sprzed
// wymuszonego szyfrowania kopii, czyli cofnalby poprawke bezpieczenstwa.
const CACHE_VERSION = 'dziennik-wf-v4';
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

  // Shell same-origin: stale-while-revalidate. Zadnych obcych hostow - dziennik
  // nie ma sie z czym laczyc poza wlasnym katalogiem (bramka: test_siec.py).
  if (url.origin === self.location.origin) {
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
