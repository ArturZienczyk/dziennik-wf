# HANDOFF — scalanie kopii (laptop ↔ telefon) w dzienniku WF

**Data:** 2026-09-18 wieczór. Dla: czysta sesja w `D:\Projects\nauczyciel\wf\dziennik-wf`.
**Decyzja usera (2026-09-18):** „pasuje" dla wariantu: **scalanie przy wczytaniu kopii + folder kopii
na Dysku Google**. Pełny automat (Drive API w apce) NIE teraz — dopiero gdy po tygodniu ręczny transfer
okaże się uciążliwy. Konflikty **z automatu** (nowszy wygrywa), lista tylko informacyjna po scaleniu,
user nic nie klika.

## Stan wyjściowy (zweryfikowany w kodzie)
- Dane per przeglądarka (localStorage + IndexedDB, szyfrogram). Mobile = GitHub Pages
  `https://arturzienczyk.github.io/dziennik-wf/dziennik_wf.html` (PWA, `sw.js` CACHE_VERSION v9 —
  **podbij przy każdej zmianie html**). Push = `git push origin main` (bez pipe; hook wymusza log).
- Kopia szyfrowana: „Zapisz kopię" → folder kopii (`_folderKopii`, File System Access, u usera
  `D:\Users\Desktop\Dziennik WF kopie`), auto raz dziennie `autoBackupDaily()` (~l. 3656).
- Import: `importEncrypted(event)` (~l. 3821) → `decryptBackup` → `showConfirm` → **ZASTĘPUJE**
  `state.classes` i `state.planWf` w całości (`backupBeforeDestruction('IMPORT-ENC')` przed).
  Dwa wejścia: `#fileImportEnc` (szyfrowana) i `#fileImport` (stary jawny JSON).
- Struktura klasy: `makeClass()` (~l. 1630): `id, school, name, students[], attendance{klucz→{sid→cell}},
  measurements{sid→{}}, gradeColumns[], grades{colId→{sid→v}}, semesterBreak, odwolane{klucz→powód},
  planKlasa, releases per uczeń`. Klucz frekwencji `'RRRR-MM-DD'` lub `'RRRR-MM-DD#nr'`
  (README §„Pasek tygodnia"). Cell = `'C'` albo `{s, sp}` (`attRead/attWrite`).
- Plan: `state.planWf.plany[] = {od, do, klasy, inne, wolne, zrodlo}`; `zaleglePlanZastosuj` już
  robi upsert po `od` (wzór scalania dla planu — użyć, nie pisać drugi raz).

## Zadanie
1. **Znaczniki czasu.** Każdy zapis wpisu frekwencji / oceny / pomiaru / „nie było" / ucznia dostaje
   `t` (ms). Miejsce: jedna funkcja `stempluj(obj)` wołana w `save()` na diff? Prościej: `cls._t = {klucz: ms}`
   per klasa dla frekwencji (klucz lekcji), `gradeColumns[i].t`, `measurements[sid]._t`, `odwolane` → obiekt
   `{powod, t}`? **Uwaga migracja:** stare wpisy bez `t` → traktuj jak `t = 0` („laptop jest prawdą" przy
   pierwszym scaleniu: importowany plik bez `t` przegrywa z lokalnym bez `t` — zachowaj lokalne).
   Nie przepisuj formatu cell (attRead/attWrite w ~40 miejscach) — znaczniki trzymaj OBOK, w `cls._t`.
2. **Scalanie** `scalKopie(dataZPliku)` zamiast podmiany w `importEncrypted` (i w imporcie jawnym):
   - klasy parowane po `id`; brak lokalnie → dodaj całą; nowa lokalnie → zostaje.
   - uczniowie po `id` (dodaj brakujących; nazwisko: nowszy `t`).
   - frekwencja: per (klucz lekcji, sid): brak → dodaj; oba są, różne → nowszy `t`; równe `t` (0 i 0) → lokalny.
   - oceny: kolumny po `id`, wartości per sid jak wyżej; pomiary jak wyżej; `odwolane` i `releases` jak wyżej.
   - plan: `zaleglePlanZastosuj` per plan z pliku (już scala).
   - wynik: `{dodane: n, nadpisane: [{klasa, klucz, uczeń, było, jest}], pominięte: n}` → toast + modal
     „Scalono N wpisów, K nadpisanych" z listą (informacja, bez przycisków decyzji).
   - `showConfirm` w imporcie: tekst zmienić z „WSZYSTKIE klasy zostaną zastąpione" na „dołoży brakujące,
     nowszy wpis wygrywa"; kopia przed operacją zostaje (`backupBeforeDestruction`).
   - Stary tryb „zastąp wszystko" zostaw jako checkbox w tym samym oknie (przenosiny na czysto).
3. **Test** `test_scalanie.py` (wzór: `test_zalegle.py`, Playwright, `zamekPierwszeHaslo`, `zamekStanZapisany`):
   laptop A ma lekcje 1,2; telefon B ma lekcje 2 (inny status jednego ucznia, nowszy t), 3 → po scaleniu
   A ma 1,2,3, uczeń z 2 = wersja B, lista nadpisanych = 1; import pliku bez `t` nic nie nadpisuje;
   plan scala się przez upsert; klasa nieznana z pliku dochodzi; „zastąp wszystko" działa jak dawniej.
   Regresja: `test_kopie.py`, `test_zamek.py`, `test_klawiatura.py`, `test_zalegle.py` (54).
4. **Folder kopii na Dysku Google** — bez kodu: instrukcja w README §„Kopie" + zdanie dla usera
   (Ustawienia → „Folder kopii" → wskazać folder w `G:\Mój dysk\...` albo folder Dysku Google na
   komputerze). Telefon: Drive → plik → „Wczytaj szyfrowaną". Kierunek telefon → laptop: Udostępnij → Drive
   (Android nie synchronizuje Pobranych; nie testowane u usera — powiedzieć wprost).
5. README: sekcja „Synchronizacja laptop ↔ telefon" (scalanie, nowszy wygrywa, jedno kliknięcie na
   urządzenie, czego nie ma: automat) + `sw.js` v10 + push + memory (`project_dziennik_wf_scalanie_kopii`).

## Nie robić
- Drive API / OAuth w apce (osobna decyzja usera o danych dzieci, „nic nie wychodzi z laptopa").
- Zmiany formatu cell frekwencji ani klucza (`data#nr`) — świeże, przetestowane, 40+ miejsc.
- Serwer lokalny / Wi-Fi sync (szkolne Wi-Fi izoluje urządzenia).

## Otwarte u usera (z tej sesji, nie z handoffu)
- 5TS w zakładce Plan → „klasa w planie" = 5 technikum (informatyka) (było przypięte do 2 technikum).
- Wczytać nowy `D:\Users\Desktop\Sesja-Claude\2026-09-18\plan-wf.json` (ma `inne`: EZ/GW).
- Librus (technikum) — osobny wątek, nie ruszony.
