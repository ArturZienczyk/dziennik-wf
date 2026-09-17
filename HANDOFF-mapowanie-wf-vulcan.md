# HANDOFF — projekcja statusów Dziennik WF → VULCAN

> **STAN 2026-09-17 (po sesji):** decyzje 1–4 ROZSTRZYGNIĘTE i wdrożone (tabela kanoniczna w
> `VULCAN-INTEGRACJA-USTALENIA.md`), przycisk „Kopiuj dla VULCAN" w apce przy dacie lekcji,
> test `py -3.14 test_vulcan_kopiuj.py` OK. Zostało: weryfikacja na żywym VULCAN z realnym dniem;
> sprzątnięcie bloków DEBUG w skrypcie + bookmarklet.

**Data:** 2026-09-17. Dla: czysta sesja, która ma zaprojektować i wdrożyć mapowanie.
**Powiązane:** `VULCAN-INTEGRACJA-USTALENIA.md` (mechanizm zapisu — DZIAŁA e2e, v11).

## Zadanie (słowami usera)
Zgrać zapisy dziennika WF z VULCANem tak, żeby **treść frekwencji w obu systemach była taka
sama**. Ale zaznaczenia charakterystyczne dla workflow usera, których **nie da się przełożyć
1:1** na symbolikę VULCANa — **zostają w dzienniku WF w swojej natywnej formie**, a mapowanie
**umiejętnie je koryguje** do symboli dostępnych w VULCAN. Cel: kompatybilność dwóch systemów
bez zubażania bogatszego dziennika WF.

## Zasada projektowa (do utrzymania)
1. **Dziennik WF = źródło prawdy** dla bogatego zapisu nauczyciela (BS, spóźnienie jako doklejka,
   C+sp itd.). NIE zubażać appki pod VULCAN.
2. **VULCAN = zapis oficjalny**, słownik grubszy (8 wykluczających symboli).
3. **Mapowanie = świadoma PROJEKCJA:** każdy status appki (łącznie z kombinacjami +sp) → dokładnie
   jeden symbol VULCANa. Stratne tam, gdzie inaczej się nie da, ale **udokumentowane i nigdy błędne**.
4. Projekcja odpala się **tylko przy eksporcie do VULCANa** — natywne marki appki zostają nietknięte.

## Fakty — model appki WF (`dziennik_wf.html`)
- Komórka frekwencji: string statusu ALBO obiekt `{s, sp}`. `attRead`→`{s, sp:bool}`,
  `attWrite(status, sp)` zapisuje string bez sp / obiekt gdy sp. (linie ~1849–1859)
- **Statusy bazowe (`s`):** `C` (ćwiczył), `NĆ` (nie ćwiczył bez zwolnienia), `BS` (brak stroju),
  `NB` (nieobecny nieuspr.), `NU` (nieobecny uspr.), `ZW` (zwolnienie jednorazowe).
- **Spóźnienie (`sp`) = MODYFIKATOR**, nie osobny status. Dokleja się do DOWOLNEGO statusu
  („NĆ + spóźniony" itd., linia 1184).
- Eksport (`exportCSV`, linia 2745): token = `s + (sp ? '+sp' : '')` → np. `C`, `NĆ`, `C+sp`.
  To format RAPORTOWY (wszystkie daty w kolumnach) — NIE do importu; „Kopiuj dla VULCAN"
  (jeden dzień, `Nazwisko Imię <TAB> STATUS`) jeszcze NIE istnieje.
- `%ćwiczył` liczy się `C / (C+NĆ+BS+NB)`; NU i ZW wypadają z bazy (linia 849).

## Fakty — VULCAN (8 symboli WYKLUCZAJĄCYCH)
`•` obecność · `—` nieobecność · `u` nieob. uspraw. · `s` spóźnienie · `ns` nieob. uspr.
szkolne · `z` zwolniony · `#` obecność zdalna · `nc` nie ćwiczy na zajęciach WF.
- Nie ma „brak stroju". Nie ma „status + modyfikator" — jeden symbol na kratkę.
- Ułatwienie: nauczyciel zaznacza tylko WYJĄTKI, po „Zapisz" reszta dostaje `•` (obecność) AUTO.

## Obecne mapowanie (`symbolFor` w `vulcan-frekwencja.user.js`) — punkt wyjścia
| App | VULCAN | uwaga |
|---|---|---|
| C | `•` obecność | (patrz decyzja 1 — może pomijać) |
| NĆ | `nc` | |
| BS | `nc` | VULCAN nie ma BS → scala z NĆ (decyzja 3) |
| NB | `—` | |
| NU | `u` | |
| ZW | `z` | |
| *cokolwiek*+sp | `s` | obecnie spóźnienie WYGRYWA nad bazą (decyzja 2) |
Prześledzone 2026-09-17: wszystkie kody bazowe appki `symbolFor` już rozumie (Ć→C w środku).

## OTWARTE DECYZJE (do rozstrzygnięcia z userem — jego domena: rytm/pedagogika/prawo)
1. **Status C (ćwiczył, bez sp):** pomijać (zdać się na auto-fill VULCANa `•`, mniej klików,
   zgodne z „zaznaczam tylko wyjątki") vs wpisywać `•` jawnie każdemu. *Rekomendacja modelu:
   pomijać; C+sp i tak dostaje `s`.* — user PRZERWAŁ tę rozmowę bugiem obwódki, wraca tu.
2. **sp doklejone do bazy innej niż C** (NĆ+sp, NB+sp…): baza wygrywa (nc/—/u) czy `s` wygrywa?
   VULCAN nie pomieści obu. Rzadkie; dziś default = `s`. Do potwierdzenia, co legalnie/pedagogicznie
   poprawne dla WF.
3. **BS→nc:** potwierdzić (brak alternatywy w VULCAN).
4. **Gdzie żyje projekcja (jedno źródło prawdy):** appka eksportuje SUROWE kody WF (`C+sp`, `BS`…)
   a `symbolFor` skryptu jest kanoniczną projekcją? *Rekomendacja: tak — jedno miejsce mapy,
   dziennik zostaje natywny, skrypt tłumaczy.* Alternatywa: appka projektuje w eksporcie.

## Do zbudowania po decyzjach
- Kanoniczna tabela projekcji (wszystkie bazy × {bez sp, +sp}) → symbol VULCANa — spisana,
  jedno źródło.
- Przycisk „Kopiuj dla VULCAN" w `dziennik_wf.html`: eksport WYBRANEGO dnia jako
  `Nazwisko Imię <TAB> STATUS` (surowe kody WF), do wklejenia w panel skryptu.
- (Osobno, nie mapowanie:) sprzątnięcie bloków DEBUG/ZNAKI SPECJALNE/DIAG ze skryptu + pakowanie
  do bookmarkletu.
- Weryfikacja zgodności: dla dnia — projekcja statusów appki == symbole w VULCAN po Zapisz.

## Pliki
- Skrypt: `D:\Projects\nauczyciel\wf\dziennik-wf\vulcan-frekwencja.user.js` (v11, działa e2e)
- Appka: `D:\Projects\nauczyciel\wf\dziennik-wf\dziennik_wf.html`
- Ustalenia mechanizmu: `D:\Projects\nauczyciel\wf\dziennik-wf\VULCAN-INTEGRACJA-USTALENIA.md`
- Kopia skryptu na pulpicie (do snippetu): `D:\Users\Desktop\vulcan-frekwencja.txt`

## Stan userscriptu na dziś (żeby nie ruszać tego, co działa)
v11: dopasowanie (dedup po `data-key`, 46 fantomów DOM → 23 realnych), zapis (model PĘDZLA
arm→paint + `PointerEvent`), sprzątanie obwódek (`clearMarks`). Potwierdzone na żywym VULCAN:
`wpisano 3`, trzy różne symbole przełączone, obwódki znikają. **Mechanizmu NIE ruszać** —
następna sesja pracuje wyłącznie nad PROJEKCJĄ STATUSÓW i eksportem z appki.
