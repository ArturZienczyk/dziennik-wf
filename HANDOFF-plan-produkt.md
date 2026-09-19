# HANDOFF — zakładka Plan jako produkt dla kolegów + kafelek „nie było” + neutralizacja pod firmę

**Data:** 2026-09-19 (po sesji: checkbox „Zastąp wszystko” usunięty, statystyki po roku, „nie było” na kafelku).
Dla: czysta sesja w `D:\Projects\nauczyciel\wf\dziennik-wf` (osobne repo, `git push origin main`, GitHub Pages,
**`sw.js` CACHE_VERSION v20 — podbij przy każdej zmianie html**). Commity dziś: `8889bd5`, `f7b7beb`, `e3d5dbd`.

**Słowa usera (19.09, zamówienie tego handoffu):**

> czy kafelek nie było gdy lekcja się nie odbyła może delikatnie wyróżnić, plan zrobić bardziej pasujący do
> pozostałych zakładek jest trochę surowy, nie wiem czy nie brakuje mu tej intuicyjnego flow, opis klasa bierze
> się z zakładki uczniowie? jeżeli tak to warto byłoby na otwartym planie jeszcze bez wpisów w uczniowie, by był
> zapis w planie, żeby uzupełnić tam dane, to automatycznie klasy pojawia się w planie i można wtedy wpisać plan
> po wybraniu szkoły, klasy i wpisaniu listy

**Kontekst produktu (decyzja 19.09):** dziennik był „pod Artura”, teraz idzie do kolegów z ZSS **i** jako dodatek
do firmy od konkursu naukowego. **Jeden produkt, nie dwie kopie:** wszystko szkolne (PZO ZSS, nazwy, ścieżki) ma
przejść z kodu do danych per szkoła; VULCAN / Librus zostają do wyboru per szkoła (nauczyciele pracują w kilku
szkołach z różnymi dziennikami — to jest istotne, nie upraszczać).

## Stan wyjściowy (zweryfikowany 19.09)
- **Plan** (`#tab-plan`, HTML ~1451; `renderPlanUstawienia` ~2478): siatka klasa × Pn–Pt (klik komórki → numery
  lekcji), „Inne zajęcia”, „Dni wolne”, `<details class="plan-zaaw">` z wczytaniem `plan-wf.json`. Kolumna
  „klasa w planie” tylko gdy `zPliku` (plan ma `wygenerowano` / `zrodlo` ≠ 'ręcznie'). Kolumny „nie było” już nie ma.
  Wiersze siatki = `state.classes` — **tak, klasy biorą się z zakładki Uczniowie** (`+ klasa` w belce, szkoła +
  nazwa + lista). Przy zerze klas Plan pokazuje pustą tabelę bez żadnej wskazówki — to jest luka z zamówienia.
- **Kafelek „nie było”** (podgląd `.kol.podglad.niebylo`, otwarta: `head.parentElement.classList('niebylo')`):
  CSS `.kol.niebylo .kol-head { opacity:.6; text-decoration: line-through }` + `.sum` z „nie było: powód” i
  przyciskiem `.niebylo-cofnij` („jednak była”). Na zrzucie `_zrzuty/`/pulpit `niebylo_dzien.png`: otwarta lekcja
  z „nie było” wygląda jak zwykła otwarta (biała ramka), tylko linijka tekstu — user chce **delikatne wyróżnienie**.
  Pasek tygodnia `.plan-lekcja.niebylo` ma już przekreślenie + „–”.
- `nieByloZdejmij()` — wpis statusu / „Zapisz lekcję” zdejmuje flagę bieżącej lekcji. `zalegleCofnijNieBylo`
  odświeża dzień, chip, Plan.
- Testy: `test_niebylo_kafelek.py` (12), `test_druk_statystyki.py` (17), `test_widok_dzienny.py` (71),
  `test_karta_ucznia.py` (31), `test_scalanie.py` (30), `test_kopie.py` (18). **`test_zalegle.py`: 2 FAIL od
  dawna** („lista ma 8 pozycji”, „po nie było = 7”) — liczy zaległości względem prawdziwego „dziś”; padały przed
  zmianami 19.09 (sprawdzone na `git stash`). Naprawa = zamrozić „dziś” w fixturze (nie ruszać logiki).

## Zamówienie (trzy rzeczy + reszta produktu)

### 1. Kafelek „nie było” — delikatne wyróżnienie
Cel: lekcja, która się nie odbyła, ma być widoczna na pierwszy rzut oka, ale nie krzyczeć (to nie błąd, to fakt).
Propozycja do mockupu: tło kafelka jak „inne zajęcia” (szare, `--line-soft`), ramka kreskowana, nagłówek bez
przekreślenia (przekreślenie czyta się jak „skasowane”), etykieta „nie było · wycieczka” w miejscu procentu,
przycisk „jednak była” bez zmian. Otwarta lekcja z flagą: ta sama ramka kreskowana zamiast czarnej „otwarta”.
Sprawdzić w **zestawie** (pasek dnia = 4-5 kafelków obok siebie; memory `feedback_render_zestaw_nie_element`):
brak wpisu (czerwone), jest (zielone), nie było (szare kreskowane), inne (szare bez ramki) mają się różnić jednym
ruchem oka. Mockup jako nakładka CSS na żywej apce (memory `feedback_mockup_nakladka_css_na_zywej_apce`):
fixture z `test_niebylo_kafelek.py`, `add_style_tag`, zrzut teraz/propozycja, wybór usera, potem CSS = patch.

### 2. Plan — wygląd jak reszta zakładek + flow
Dziś: gołe `<table>` z inline-stylami, `<b>` jako nagłówki sekcji, wszystko w jednej bryle. Reszta zakładek ma
karty (`.oceny-intro`, `.reg-box`, `.summary-card`, nagłówki `h2`/`h3`, `.uwaga`). Zrobić Plan w tym języku:
- trzy karty w kolejności czytania: **Siatka tygodnia** (kto, kiedy) → **Inne zajęcia** → **Dni wolne**;
  „Plan od–do” i „Zaawansowane: plan z pliku” jako stopka karty siatki;
- komórka siatki z numerem lekcji jako chip (jak `.rel-chip` zwolnień), pusta jako kropka; otwarte numery
  (0–11) jako wiersz pod klasą — zostaje, ale w stylu chipów;
- flow = kolejność kroków widoczna bez czytania instrukcji. Jeśli instrukcja jest potrzebna, to jedno zdanie
  na karcie, nie akapit na górze.
Mockup najpierw (memory `feedback_mockup_przed_zywa_apka`): warianty A/B w osobnym HTML albo nakładka CSS,
wybór okiem usera, potem kod. Nie zmieniać modelu danych (`planWf.plany[].klasy[k][dzień]=[nry]`).

### 3. Plan bez klas — poprowadź do Uczniowie
Gdy `state.classes.length === 0` (albo klasa bez uczniów): zamiast pustej tabeli **karta pusta** z krokami:
„1. Szkoła i klasa — belka na górze `+ klasa` · 2. Lista uczniów — zakładka Uczniowie · 3. Wróć tu: klasa
pojawi się w siatce, klik komórki wpisuje lekcje”. Krok zrobiony = odhaczony (klasy są → krok 1 ✓). Przycisk
„Dodaj klasę” w tej karcie woła to samo, co `+ klasa` w belce (sprawdzić nazwę funkcji — grep `+ klasa`).
To samo dla nowego nauczyciela na Obecności (pusty dziennik) — jeśli już jest jakiś pusty stan, ujednolicić,
nie dublować. Test: świeża apka (0 klas) → Plan → karta z krokami; po `+ klasa` siatka.

### 4. Reszta produktu (z listy 19.09, każde osobny mały ruch, po 1–3)
- **Reguły:** cytat PZO i nazwa szkoły z kodu do danych — pole „Zasady frekwencji (PZO)” per szkoła w sekcji
  „Szkoły i e-dziennik” (`ustawienia().szkoly[s]`, snapshot/kopia już niosą `ustawienia`); domyślnie puste
  z podpowiedzią; Artur wpisuje cytat ZSS raz. Wyciąć notatki robocze z UI („decyzja 18.09.2026”, „rozjazd z PZO
  — decyzja jeszcze nie zapadła”, ścieżki `wf/pzo/*.docx`, „skrypt wklejania istnieje dziś tylko dla VULCANa”).
  Wzór liczenia i przykład zostają (to matematyka, nie szkoła).
- **Stopka** (`Wygenerowane w rozmowie z Claude · maj 2026`, ~linia 1574): „Dziennik WF · wersja <CACHE_VERSION>
  · Artur Zienczyk” + zdanie o danych lokalnych, które już jest. Wersję brać z jednej stałej, nie wpisywać ręcznie.
- **Instrukcja „Start w 5 minut”** — osobny `start.html` w repo (hasło i PIN → + klasa → uczniowie → siatka planu
  → pierwsza lekcja → kopia szyfrowana). Bez niej kolega utknie na zamku. Link ze stopki.
- **Follow-upy poza zakresem** (nie ruszać bez pytania): `test_zalegle.py` 2 FAIL (data); karta ucznia pokazuje
  „×undefined” / „Średnia ważona: NaN” przy kolumnie ocen bez wagi (wyszło na sztucznym wsadzie).

## STAN 19.09 wieczór (sw v27) — p.4 WDROŻONE (p.1–3 wdrożone wcześniej, commit `3187fa4`)
- **PZO → dane per szkoła:** `ustawienia().szkoly[s].pzo` (textarea `.reg-pzo` w karcie „Szkoły i e-dziennik”,
  `pzoUstaw`/`pzoSzkoly`); karta „Jak liczona jest frekwencja” pokazuje cytat szkoły aktywnej klasy (`#regPzo`)
  albo wskazówkę, gdzie wpisać. `pzoSeedZSS()` zasiewa cytat ZSS raz (klucz `pzo` obecny = nie nadpisuj).
  Notatki robocze z UI wycięte (docx, „decyzja…”, „rozjazd”). Snapshot/kopia niosą `ustawienia` → pzo jedzie.
- **Błąd produktu złapany po drodze:** nazwa szkoły ze spacją („SP 99”) rozrywała atrybut `onchange`
  (`JSON.stringify(s)` = cudzysłowy w cudzysłowie) — select e-dziennika też nie działał. Fix: `&quot;`.
- **Stopka:** „Dziennik WF · wersja N · Artur Zienczyk · Start w 5 minut”; N z `fetch('sw.js')` (jedna stała
  CACHE_VERSION; z file:// zostaje „wersja lokalna”). `start.html` w SHELL sw.js.
- **`start.html`:** 6 kroków (hasło+PIN → +klasa → lista → Plan → pierwsza lekcja → kopia) + Reguły + telefon.
- Test: `test_produkt_p4.py` 17/17, zrzuty `_zrzuty/p4_reguly_1400.png`, `p4_start_1400.png`.
- Zostaje z tej listy: nic. Follow-upy bez zmian (test_zalegle 2 FAIL, karta ucznia ×undefined/NaN).

## Zasady sesji
- Klik = user. Każdy obiekt wizualny: headless render **zestawu**, obejrzeć samemu, dopiero pokazać.
- Edycja punktowa (plik ma ~5900 linii; `Edit`/patch, nie `Write`). Heredoc w Bash blokuje hook — skrypt z pliku.
- Zamek w testach: `zamekPierwszeHaslo('test-haslo-123')` (krótkie hasło nie przechodzi).
- Po pushu: `git ls-remote origin main` = HEAD; telefon dostaje nową wersję po podbiciu `sw.js`.
