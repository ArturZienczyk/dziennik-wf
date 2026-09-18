# HANDOFF — plan: widok dzienny (godziny obok siebie) + belki, które zapraszają do kliknięcia

**Data:** 2026-09-18 wieczór. Dla: czysta sesja w `D:\Projects\nauczyciel\wf\dziennik-wf` (osobne repo,
`git push origin main`, GitHub Pages, **`sw.js` CACHE_VERSION v11 — podbij przy każdej zmianie html**).
**Słowa usera (18.09, po wdrożeniu scalania kopii + Drive):**

> plan chciałbym jako widok tygodniowy i dzienny, ale pierwszy wybór to ten dzienny — ale nie żeby był
> godzina za godziną, ale raczej godzina obok godziny, żeby lepiej było widać uczniów i lekcje z obecnościami.
> Ta belka z uczniami, planem, statystyką tak pokazać, żeby było jasne, że tam się klika. Belka ze szkołą,
> klasą też tak zrobić, żeby bardziej rzucało się w oczy. Zbadać, jak to zrobić w sposób smaczny, nie krzykliwy.

## Stan wyjściowy (zweryfikowany 18.09)
- Zakładka **Obecność**: pod datą **pasek tygodnia** `#planTydzien` (Pn–Pt, kafelki `L3 · 2 inf`, klik =
  klasa+data+lekcja; README §„Pasek tygodnia"). Renderuje `renderAttendance` → część planu; kafelki
  `.plan-lekcja` (zielony ✓ wpis / czerwony ! brak / szary inne / ramka = otwarta).
- Zakładka **Plan** (`#planUstawienia`, `renderZalegle`): siatka per klasa Pn–Pt × nr lekcji, dni wolne, inne.
- Belka zakładek: `.tab` (Obecność, Uczniowie, Pomiary, Oceny, Statystyki, Plan, Zablokuj) — dziś tekst
  z ikoną, podkreślenie aktywnej; belka nagłówka: `Szkoła: <select>` `Klasa: <select>` + `+ klasa`,
  `zmień nazwę`, przyciski zamka — dziś jak zwykłe kontrolki formularza.
- Klucz wpisu `data` / `data#nr` (nie ruszać); plan v2 `klasy[k][dzień] = [nry]`.
- Testy: `test_zalegle.py` (54, pasek tygodnia i siatka), `test_klawiatura.py` (22, klawiatura — **widok
  dzienny nie może jej zepsuć**), `test_uklad.py`, `test_scalanie.py` (31).

## Co zbudować
1. **Widok dzienny jako domyślny** w Obecności: lekcje dnia **obok siebie** (kolumny), nie jedna pod drugą.
   Każda kolumna = lekcja (`L3 · 2 inf`) z listą uczniów i ich statusami — user chce z jednego ekranu widzieć
   uczniów i obecności kilku lekcji tego dnia. Przełącznik **Dzień / Tydzień** (tydzień = obecny pasek).
   Do rozstrzygnięcia z userem (jedno pytanie, nie widżet — decyzja z jego rytmu, opis przepływu):
   czy kolumna jest **edytowalna** (klik statusu w kolumnie zapisuje) czy **podgląd** + klik nagłówka
   otwiera lekcję w dotychczasowej tabeli. Propozycja: podgląd + klik nagłówka (klawiatura i tabela
   zostają jedynym miejscem wpisu — 40+ miejsc `attRead/attWrite` bez zmian).
   Telefon: kolumny przewijane poziomo (`overflow-x:auto`), min. szerokość kolumny ~220px.
2. **Belka zakładek** i **belka szkoła/klasa**: afordancja „tu się klika" — smaczna, nie krzykliwa.
   Kierunki do zbadania (render + oko usera, nie deklaracja): zakładki jako segmented control /
   pigułki z lekkim tłem i cieniem; aktywna z wypełnieniem, nie tylko podkreśleniem; selecty szkoła/klasa
   jako wyraźne „chipy" z chevronem, nazwa klasy większa (to główny kontekst pracy). Paleta obecna
   (`--ink`, `--paper`, `--line`, zieleń #1D9E75) — nie wprowadzać nowych kolorów.
3. **Zanim narysujesz:** `kanon "afordancja klikalności belka zakładek"` + `design/canon/` (visual
   render-invariant-ratchet, mechanizm-przed-pozorem). Render headless (`shot.py` z `design/tools`) na
   1400 i 390 px, **obejrzeć PNG**, zrzuty do `_zrzuty/`; ocena = oko usera.
4. Test `test_widok_dzienny.py` (wzór `test_zalegle.py`): dzień z 2 lekcjami → 2 kolumny, klik nagłówka
   przełącza lekcję, przełącznik Dzień/Tydzień, wąski viewport = przewijanie poziome; regresja pełna.
5. README sekcja + sw v12 + push + memory.

## Nie robić
- Nie zmieniać formatu wpisów ani klucza `data#nr`; nie dublować logiki statusów (jedno `attRead/attWrite`).
- Nie robić nowej palety / nowych fontów. Nie „upiększać" reszty ekranu przy okazji.

## Otwarte u usera (przeniesione)
- Telefon: wczytać najnowszą kopię z Drive (od 18.09 kopia niesie plan) — sprawdzić, czy plan doszedł.
- 5TS → „5 technikum" w zakładce Plan; nowy `plan-wf.json` (z `inne`) wczytany?
- Po tygodniu: czy ręczny transfer telefon → laptop męczy (wtedy Drive API, osobna decyzja).
