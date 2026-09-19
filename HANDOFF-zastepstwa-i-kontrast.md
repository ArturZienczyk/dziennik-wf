# HANDOFF — kafelek „nie było” mocniej, „klasa w planie” do Zaawansowane, zastępstwa (prosty → z listą)

**Data:** 2026-09-19 (po commicie `261c31a`: kafelek szary kreskowany, Plan jako trzy karty, pusty stan → Uczniowie; sw v21).
Dla: czysta sesja w `D:\Projects\nauczyciel\wf\dziennik-wf` (osobne repo, `git push origin main`, **`sw.js` CACHE_VERSION v21 — podbij**).
Poprzedni handoff `HANDOFF-plan-produkt.md`: punkty 1–3 zrobione, **punkt 4 (PZO do danych, stopka z wersją, `start.html`) nadal otwarty**.

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
