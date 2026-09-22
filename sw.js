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
// v5: mikrofon tylko lokalnie (processLocally) - poprawka prywatnosci, stary klient nie moze zostac.
// v6: uklad - pasek gorny przyklejony, sciagi zwijane, tabela wysoko.
// v7: zarys kolumn w Obecnosci/Statystykach/Pomiarach.
// v8: naglowek tabeli przyklejony pod paskiem gornym.
const CACHE_VERSION = 'dziennik-wf-v49';
const SHELL = [
  './dziennik_wf.html',
  './start.html',
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
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_VERSION && k !== UDOSTEPNIONA).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Kopia udostępniona z WhatsAppa (Web Share Target, 23.09): „Udostępnij → Dziennik WF" wysyła tu
// POST z plikiem. Odkładamy go do osobnego cache (przeżywa podbicie CACHE_VERSION) i otwieramy
// dziennik — ten po odblokowaniu odbiera plik tą samą drogą co „Wczytaj" (hasło → scal).
// Wcześniej: WhatsApp → zapisz do Pobranych → znajdź w wyborze pliku (Android nie widzi WhatsAppa).
const UDOSTEPNIONA = 'dziennik-wf-udostepniona';
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'POST' || !url.searchParams.has('udostepniona-kopia')) return;
  e.respondWith((async () => {
    try {
      const fd = await e.request.formData();
      const f = fd.getAll('kopia').find(x => x && typeof x.text === 'function');
      if (f) {
        const c = await caches.open(UDOSTEPNIONA);
        await c.put('./udostepniona-kopia', new Response(await f.text(),
          { headers: { 'X-Nazwa': encodeURIComponent(f.name || '') } }));
      }
    } catch (err) { /* uszkodzony formularz: dziennik i tak się otworzy, tylko bez kopii */ }
    return Response.redirect(new URL('./dziennik_wf.html?udostepniona-kopia=1', self.registration.scope).href, 303);
  })());
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
