# Dziennik WF

Single-file aplikacja (HTML+JS, bez instalacji, offline) do prowadzenia frekwencji,
pomiarów sprawności i ocen na WF. Dyktowanie głosem na sali (mikrofon / Win+H).

## Uruchomienie

Otwórz `dziennik_wf.html` w przeglądarce (dwuklik). Działa lokalnie, nic nie wychodzi
na żaden serwer.

## Dane i backup

- Dane żyją w `localStorage` przeglądarki — **per przeglądarka, per komputer**.
- Backup JSON: auto-pobierany przy zapisie lekcji + ręczny eksport w pasku narzędzi.
- Backupy trzymaj w `backups/` — folder jest w `.gitignore` (imiona/oceny dzieci
  NIGDY nie idą do git ani na Drive bez szyfrowania — zakaz CLAUDE.md projektu).

## Status

Adoptowany do projektu `nauczyciel` 2026-05-18 (był prototypem w Downloads).

- Faza 1 (gotowe, zweryfikowane): kompletny backup z ocenami + auto-backup raz
  dziennie przy zapisie lekcji + backup przed operacją niszczącą.
- Faza 2 (gotowe): model szkoła→klasa (zespół szkół, wiele klas), migracja
  starych danych bez utraty, pasek wyboru szkoły/klasy.
- Faza 3 (wdrożone): hosting HTTPS na GitHub Pages
  (https://arturzienczyk.github.io/dziennik-wf/dziennik_wf.html) + PWA
  (manifest + service worker, działa offline, instalacja na Androidzie) +
  szyfrowana kopia (AES-GCM + hasło) — dane dzieci mailem dopiero zaszyfrowane,
  zgodnie z zakazem CLAUDE.md. Repo publiczne, ale `backups/` i kopie danych
  poza git (dwie warstwy `.gitignore`).
  Niezweryfikowane na żywo: instalacja PWA na fizycznym Androidzie + szyfrowana
  kopia w UI przeglądarki (rdzeń krypto przetestowany, integracja UI nie).
- Widełki punkty→ocena 1-6 (szkolne, zatwierdzone przez MEN) — czeka na tabelę od Artura.
