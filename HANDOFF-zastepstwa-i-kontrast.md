# HANDOFF — kafelek „nie było” mocniej, „klasa w planie” do Zaawansowane, zastępstwa (prosty → z listą)

**Data:** 2026-09-19 (po commicie `261c31a`: kafelek szary kreskowany, Plan jako trzy karty, pusty stan → Uczniowie; sw v21).
Dla: czysta sesja w `D:\Projects\nauczyciel\wf\dziennik-wf` (osobne repo, `git push origin main`, **`sw.js` CACHE_VERSION v21 — podbij**).
Poprzedni handoff `HANDOFF-plan-produkt.md`: punkty 1–3 zrobione, **punkt 4 (PZO do danych, stopka z wersją, `start.html`) nadal otwarty**.

## STAN 19.09 po południu (commit `3187fa4`, sw v24) — p.1–3 WDROŻONE
- p.1 kafelek: mockup A/A2/B (`_zrzuty/mockup-niebylo-v2/porownanie.html`), klik usera = **A** (kreskowanie na białym, ramka #9A9184). Otwarte z p.1: klik w „nie było: inne" = zmiana powodu bez „jednak była" — NIE zrobione.
- p.2 „klasa w planie" → lista dopasowania w `details.plan-zaaw` (`.plan-dopasowanie`), details `open` przy dublu. Testy przepisane.
- p.3 poziom 1 wdrożony: `cls.zastepstwa[klucz]` (liść `z|klucz`) + `state.zastepstwaOkienka` (snapshot/load/scal). Wejścia: panel Zaległe (przycisk „zastępstwo"), kafelek „+ zastępstwo" na pasku dnia (modal: moja lekcja bez wpisu / okienko + nr), klik w kafelek zastępstwa = zmień/zdejmij. `test_zastepstwa.py` 30/30.
  **Poziom 2 (klasa doraźna z listą) — nadal tylko propozycja; zwiad EduPage zastępstwa nieruszony (hipoteza).**
- Pułapki z tej sesji: modal otwierany z listy Zaległych (też modal) potrzebuje `z-index` wyżej (`#zastModal{z-index:110}`); test scalania „kopia przywraca" musi symulować świeże urządzenie (`delete c._t[p]; stemplujBaza()`), bo lokalne skasowanie = nagrobek nowszy od kopii i kopia słusznie przegrywa; 5. karta w `#summaryGrid` łamie druk 1 str. A4 → `.summary-zast` schowana w `body.stats-print`.
- Następne: p.4 (audyt heurystyczny, 4 findingi) + `HANDOFF-plan-produkt.md` p.4 (PZO do danych, stopka z wersją, start.html).

## Słowa usera (19.09, po obejrzeniu wdrożenia na prawdziwych danych)

> czy tutaj jest to kreskowane mimo że nie było, ma kolor kremowy, nie wiem czy nie jest zbyt mało wyróżniające,
> plus wycieczka, zamiast inne, […] czy klasa w planie to coś co jest potrzebne, może niech to będzie ewentualnie
> miejsce, gdzie mogę zapisać zastępstwo, […] jak zastępstwa wprowadzac na moich lekcjach z innymi klasami, lub
> zastępstwa na moich okienkach, czy byłaby mozliwość jakiegoś programu, który by mógł zczytywać zastępstwa
> łącznie z listą uczniów?

> zastępstwa oba przypadki, […] wpiszę tylko jaka klasa i koniec albo zaczytuje liste, ja wybieram czy wystarczy
> mi ten prosty czy chcę więcej, może na początek ten prosty a ten drugi jako propozycja

## 1. Kafelek „nie było” — za mało kontrastu (mockup → oko → patch)
Zrzut usera: dzień wycieczki całej szkoły = 6 kafelków `--line-soft` na kremowym tle strony — zlewają się.
Propozycja do mockupu (nakładka CSS, fixture z `test_niebylo_kafelek.py`, zestaw 4–6 kafelków obok siebie):
- tło: ukośne kreskowanie `repeating-linear-gradient(135deg, transparent 0 6px, rgba(0,0,0,.05) 6px 7px)` na `var(--paper)`
  (sygnał „nie odbyło się”, nie „inne zajęcia”), ramka `1px dashed #9A9184` (ciemniejsza niż teraz `#B9B1A2`);
- wariant B do porównania: tylko ciemniejsza ramka + tło `--paper`, bez kreskowania.
CSS dziś: `dziennik_wf.html` sekcja `.kol.niebylo …` (~linia 203) + `.plan-lekcja.niebylo` (~165).
**„inne” przy 3c to powód** wybrany z listy przy odwoływaniu (`zalegleNieBylo`: select `zaleglePowod_*`, wartości
wycieczka/zawody/inne), nie klasa. Rozważyć: klik w „nie było: inne” na kafelku = zmiana powodu bez „jednak była”.

## 2. „Klasa w planie” → do „Zaawansowane: plan z pliku”
Kolumna = mapowanie klasy dziennika („4d”) na nazwę z EduPage („4dLO”); potrzebna tylko przy planie z pliku,
ustawienie jednorazowe. Przenieść z siatki do `<details class="plan-zaaw">` w stopce karty Siatki (tam jest już
wczytywanie pliku) jako listę „klasa dziennika → klasa w pliku” z ostrzeżeniem `.plan-dubel`. User nie odpowiedział
wprost — to rekomendacja; pokazać w mockupie razem z p.1. Testy dotknięte: `test_niebylo_kafelek.py` (nagłówek
„klasa w planie” — `tr:first-child`), `test_zalegle.py` (`.plan-dubel` count == 2/0). Zastępstwa NIE tam.

## 3. Zastępstwa — dwa poziomy, na start prosty
**Poziom 1 (wdrożyć najpierw):** na kafelku lekcji (pasek dnia, obok „nie było”) akcja „zastępstwo”: pole „jaka
klasa” (tekst, np. „6a”) + opcjonalnie „za kogo”. Lekcja liczy się jako odbyta dla nauczyciela (nie zaległa,
nie „nie było”), **bez frekwencji w dzienniku WF** (frekwencję tej klasy wpisuje w VULCANie). Dwa przypadki tym
samym mechanizmem: (a) moja lekcja, inna klasa zamiast planowej — kafelek planowej klasy dostaje „zastępstwo: 8b”
(planowa klasa: nie zaległa, bez wpisu); (b) okienko — w dniu „+ zastępstwo” na wolnym numerze lekcji.
Model danych: `cls.zastepstwa[klucz] = {klasa, zaKogo}` dla (a); dla (b) osobno `state.zastepstwaOkienka[data#nr]`
(nie należy do żadnej klasy). Kopia/snapshot MUSI to nieść (memory `feedback_kopia_zapasowa_pelny_stan`:
dopisz do snapshotu + test szyfruj→odszyfruj). Statystyki nauczyciela: „zastępstw: N” w Statystykach.
**Poziom 2 (propozycja, nie budować bez „tak”):** zastępstwo z listą uczniów = klasa doraźna (nazwa + wklejona lista,
frekwencja wpisywana jak zwykle, oznaczona „doraźna”, bez statystyk rocznych). Zwiad przed propozycją: czy
publiczny viewer EduPage ZSS daje zastępstwa (jak plan — memory `reference_edupage_plan_lekcji_zss`); to
**hipoteza, niesprawdzona**. Listy uczniów z VULCANa automatycznie NIE (login) — lista zawsze wklejona ręcznie.
Mockup obu poziomów na jednym pasku dnia (klik = user), zanim kod.

## Zasady sesji (bez zmian)
- Klik = user. Render zestawu (pasek dnia 4–6 kafelków), obejrzeć samemu, dopiero pokazać.
- Edycja punktowa (plik ~5950 linii); heredoc w Bash blokuje hook — skrypt z pliku (scratchpad).
- Zamek w testach: `zamekPierwszeHaslo('test-haslo-123')`.
- `git push origin main > push.log 2>&1; echo EXIT=$?` + `git ls-remote origin main` = HEAD (hook blokuje push z pipe).
- Stare FAIL-e nie z tej pracy: `test_zalegle.py` 2 (dryf daty), `test_uklad.py` 1 (nagłówek przyklejony po przewinięciu).

## 4. Audyt heurystyczny frontendu (user 19.09, cztery findingi; każdy = mały osobny ruch, po p.1–3)
Zweryfikowane w kodzie 19.09 (linie orientacyjne):
1. **Pierwsze uruchomienie — czasownik walczy z intencją** (`~5756` `<h2>Zamknij dziennik hasłem</h2>`, `~5763` guzik
   „Zamknij dziennik tym hasłem”, nad tym czerwone „dane nie do odzyskania”). Nowy user przyszedł ZACZĄĆ. Gulf of
   execution + Nielsen #2. Fix: h2 „Ustaw hasło, żeby zacząć”, guzik „Ustaw hasło i otwórz dziennik”; ostrzeżenie
   o nieodzyskiwalności jako druga linia (zostaje, nie dominuje). Testy zamka: `test_zamek.py` (grep tekstów guzika).
2. **Oceny — dwa selektory klasy obok siebie** („ZSS · 7b ▾” i „ZSS · klasa ▾”). Nielsen #4. Sprawdzić, co robi
   drugi (grep w `#tab-oceny` / `renderOceny*`); jeśli to filtr szkoły — etykieta „Szkoła ▾” / „Klasa ▾”, nie dwa razy
   „ZSS · …”; jeśli duplikat — jeden selektor.
3. **Oceny — kolumna „Syst.” wygląda jak edytowalna, a jest liczona** (klik → toast „kolumna liczona automatycznie”,
   `~5234/5332/6100`). Norman: signifier PRZED akcją. Fix: nagłówek z 🔒 / „auto” + komórki bez ramki/hover pola
   (klasa `.kol-auto`), toast zostaje jako siatka.
4. **Obecność — ikonowy guzik bez etykiety przy „◀ dziś ▶”** = `🗑` `.dzien-usun` `deleteLesson()` (`~1221`,
   title „usuń wpisy tej lekcji”). Nielsen #6. Fix: tekst „usuń wpisy” obok ikony (albo ikona + etykieta na hover
   widoczna bez najechania na telefonie); rozważyć przesunięcie na koniec paska, z dala od nawigacji dnia.
Zasada: mockup nakładką tylko dla p.1 (ekran startowy) — reszta to zmiany tekstu/klasy, render zestawu i patch.
