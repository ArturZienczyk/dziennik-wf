# Integracja Dziennik WF → VULCAN (frekwencja) — ustalenia

**Cel:** userscript (Tampermonkey) w przeglądarce nauczyciela, który wypełnia frekwencję WF
w Dzienniku VULCAN na podstawie danych z tej appki. Fill-only — nigdy nie zapisuje sam,
nauczyciel klika „Zapisz". Dopasowanie po nazwisku. Per dzień.

**Data ustaleń:** 2026-09-16. Sesja: rozpoznanie DOM przez DevTools (zrzuty od usera).

> **Dane uczniów — zasada repo (2026-09-22):** repozytorium jest PUBLICZNE (zakładka-loader
> ciągnie skrypt z raw.githubusercontent bez tokena), więc w plikach, testach i komunikatach
> commitów nie ma prawdziwych nazwisk — tylko fikcyjne albo „uczeń testowy”. Notatka z 17.09
> zawierała jedno prawdziwe nazwisko wraz ze statusem frekwencji; usunięte z bieżącego stanu
> ORAZ z całej historii (git filter-repo, 97 commitów przepisanych). Kopia sprzed operacji:
> `D:\Projects\nauczyciel\wf\dziennik-wf-BACKUP-przed-czyszczeniem-2026-09-22.bundle`

## ▶ RESUME — MECHANIZM DZIAŁA E2E (2026-09-17, wersja v10)

**Stan:** dopasowanie + zapis potwierdzone na żywym VULCAN. `wpisano 1` na zielono, uczeń testowy
dostał `z` (zwolniony). Plik: `D:\Projects\nauczyciel\wf\dziennik-wf\vulcan-frekwencja.user.js`
(kopia na pulpicie `D:\Users\Desktop\vulcan-frekwencja.txt`). Dostawa w debugu: **DevTools
Snippet** (nie Notatnik — bufor edytora mylił wersje). Panel ma widoczny **znacznik wersji** w
nagłówku (v10) — potwierdza, którą wersję załadowano.

**DWIE niezależne przyczyny rozwiązane dziś (nie jedna!):**
1. **Dopasowanie dawało `do wpisania: 0`.** Przyczyna ZMIERZONA (nie zgadnięta): VULCAN
   **dubluje węzły kratek w DOM** — 46 `td[data-value-field=Wpis].f-editable` to 23 uczniów × 2,
   ta sama `data-key`, oba `vis=T`. Kod miał warunek „dopasuj tylko gdy nazwisko jednoznaczne";
   każdy był 2× → blokada CAŁEJ klasy. **Fix:** `buildPairs` dedupuje po `data-key` (zostaw
   widoczną kopię, zachowaj kolejność) → 46→23, nazwiska znów jednoznaczne.
   - Ślepe tropy (odrzucone dowodem): niewidzialny znak w nazwisku — `ZNAKI SPECJALNE: brak`,
     kody bajtów czyste `67|122|97…`. Normalizacja `norm()` została wzmocniona (strip nie-liter),
     ale to NIE była przyczyna.
2. **Zapis — klik nie wpisywał symbolu.** Przyczyna: **legenda to PĘDZEL, nie „zastosuj do
   zaznaczonej".** Model = klik symbolu **ARMuje** (`tr.x-grid-row-selected`, symbol w
   `span.clickableText`), potem klik w kratkę **maluje**. Nasza stara kolejność (kratka→symbol)
   tylko zaznaczała oba (`#0 SEL`, `legZ=SEL`), kratka zostawała `•`. **Fix:** odwrócona kolejność
   **arm→paint** + dorzucone `PointerEvent` (Sencha słucha pointer, nie tylko mouse).

**Gest usera (źródło prawdy, potwierdzone 09-17):** klik kratki → klik symbolu z listy. Plus
ułatwienie VULCAN: zaznacz tylko nieobecnych/zwolnionych, potem „Zapisz" → **reszta dostaje
obecność automatycznie**. → skrypt musi wpisywać tylko WYJĄTKI (mało uczniów/dzień).

**NASTĘPNE KROKI:**
1. Test wielu uczniów naraz + różne symbole (np. `Nowak NB`, `Kowalski NU`, `X ZW`) — sprawdzić,
   czy arm→paint przełącza symbole per uczeń (kod ARMuje w każdym `apply` od nowa — powinno grać).
2. **Sprzątanie:** wyrzucić debug (DEBUG / ZNAKI SPECJALNE / DIAG siatka widzi); zostawić „SPRAWDŹ
   dopasowania" (bramka human-verify) + raport wpisano/do-sprawdzenia.
3. **Bookmarklet** (koniec z wklejaniem) — `@match .../lodz/016197/*`.
4. **Appka WF:** przycisk „Kopiuj dla VULCAN" — `Nazwisko Imię <TAB> STATUS` (NIE zrobiony).

**Uwagi operacyjne:**
- Guard `if(window.__wfvulcan)return;` — po zmianie skryptu **✕ na panelu** (albo F5) przed
  ponownym odpaleniem, inaczej nowa wersja nie wejdzie.
- Okno EDYCJI frekwencji (z listą symboli) MUSI być otwarte — legenda znika po zamknięciu.
- Ile uczniów: 23 realnych (46 to fantomy DOM). Dedup to potwierdza w linii „Uczniów w kolumnie".

## Kontekst decyzji

- **Oficjalnego importu ocen/frekwencji dla nauczyciela w VULCAN NIE MA** (potwierdzone,
  5 instrukcji UONET+). Wszystkie zewnętrzne „haki" (wtyczki Chrome, `vulcan-api` Python,
  bot Telegram) są **read-only** — czytają, nie wpisują. Oficjalne API tylko administracyjne
  (OneRoster/Office365, zakładanie kont). Raport:
  `D:\Projects\research-notes\tools\2026-09-16_research_vulcan_uonet_data_management_analysis.md`
- Wniosek: jedyna droga automatyzacji zapisu = udawanie człowieka w przeglądarce
  (symulowane kliknięcia). User wybrał: userscript na własnej sesji (nie headless bot, nie Pi).
- Frekwencja to **najtrudniejszy** cel (klikana siatka ExtJS, per dzień, ruchome id), ale
  to codzienny grind usera → warto.

## VULCAN — fakty techniczne (z DevTools)

- Aplikacja **ExtJS (Sencha)**. Host/URL: `dziennik-dziennik.vulcan.net.pl/lodz/016197/App...`
- **UWAGA: id są generowane** (`ext-gen4040`, `panel-1253`, `gridview-1405`, `column-1403`) —
  zmieniają się przy każdym otwarciu. Skrypt MUSI celować w klasy i `data-*`, nie w id.
- **Panel frekwencji:** `[uitestid="Frekwencja"]` (stabilny znacznik). Widok = jeden dzień,
  kolumny 0–11 = godziny lekcyjne. Przyciski „Zapisz" / „Anuluj" na dole.

### Kratka frekwencji (cel zapisu)
- Selektor: `td[data-value-field="Wpis"]` (wewnątrz panelu Frekwencja).
- Klasy: `v-grid-cell v-grid-body-cell d-body-cell x-unselectable-other f-current-day`
  (dla dnia bieżącego; też `f-editable`, `f-normal`).
- `data-key="<dataMs>-<lekcja?>-<idUcznia>"` — np. `1789509600000-102-53678`
  (1789509600000 ms = 2026-09-16; 53678 = ID ucznia w VULCAN).
- Symbol jest **treścią tekstową** komórki (`•`, `—`, `u`, `s`, ...).
- Nazwiska uczniów: osobna zablokowana kolumna (locked grid), dopasowanie name→wiersz
  po kolejności/pozycji — DO POTWIERDZENIA.

### Legenda symboli (przycisk wyboru)
- To druga siatka ExtJS: wiersze `tr.x-grid-row` (id `gridview-NNNN-record-NNN`,
  `data-recordindex`, `data-recordid`). Wybrany wiersz: `x-grid-row-selected x-grid-row-focused`.
- Każdy wiersz = 2 komórki: `td` kolumny symbolu (span `.clickab...` z symbolem, np. `u`)
  + `td` kolumny nazwy (`div.x-grid-cell-inner` z tekstem, np. „nieob. uspraw.").
- Interakcja (potwierdzone przez usera): **zaznacz kratkę → kliknij wiersz legendy** → ExtJS wpisuje.

## Mapowanie: nasza appka → symbole VULCAN

| Nasz status | VULCAN symbol | nazwa w legendzie |
|---|---|---|
| C (ćwiczył) | `•` | obecność |
| NĆ (nie ćwiczył) | `nc` | nie ćwiczy na zajęciach WF |
| BS (brak stroju) | `nc` | (brak osobnego symbolu — „brak stroju" znika) |
| NB (nieob. nieuspr.) | `—` | nieobecność |
| NU (nieob. uspr.) | `u` | nieob. uspraw. |
| ZW (jednorazowe, OD–DO i długoterminowe) | `nc` | nie ćwiczy na zajęciach WF (decyzja 09-17, potwierdzona 09-19: `nc` dla rodzica = obecny na lekcji, uwaga tylko dla nauczyciela; `z` „zwolniony" w VULCAN = nieobecny — NIE używać dla zwolnień lekarskich, uczeń jest na sali z papierem) |
| +sp (spóźnienie) | `s` | spóźnienie |
| — | `ns` | nieob. uspr. szkolne |
| — | `#` | obecność zdalna |

## Status mechanizmu — UDOWODNIONE 2026-09-16

- ✅ **Symulowany klik WCHODZI w ExtJS.** Test: `fire(cell,'mousedown/mouseup/click')` →
  `fire(legendaRow,...)` zmienił kratkę „u" → „s". Droga „zaznacz kratkę → kliknij wiersz
  legendy" odtwarza się syntetycznymi MouseEvent (`bubbles:true`). To był największy ryzyk — zdjęty.
- ✅ Kratka: `td.v-grid-cell.v-grid-body-cell` z `data-value-field="Wpis"`, `data-key`, `data-qtip`.
  Selektor działa DOKUMENT-WIDE (zawężenie do `[uitestid=Frekwencja]` dawało 0 — panel to inny
  fragment; kratki i legenda żyją w oknie EDYCJI, które MUSI być OTWARTE).
- ✅ `data-key = "<dataMs>-<idLekcji>-<idUcznia>"`, np. `1789509600000-107-35343`
  (2026-09-16, lekcja 107, uczeń 35343). Precyzyjne celowanie w ucznia+lekcję.
- ✅ Legenda 8/8. Wiersz = `tr.x-grid-row`, nazwa w 2. komórce; klik wiersza wybiera symbol.
- ⚠️ Okno EDYCJI frekwencji (z listą symboli) musi być OTWARTE — legenda znika po zamknięciu.

## Selektory KOMPLETNE (potwierdzone empirycznie)

1. ✅ **Kolumna WF:** `td[data-value-field="Wpis"].f-editable` = edytowalna kolumna (Twoja lekcja),
   46 kratek = 46 uczniów (552 Wpis / 12 godzin). `f-other` = cudze lekcje, read-only.
2. ✅ **Nazwisko per uczeń:** PO POZYCJI (geometria). Nazwiska w `td.v-grid-body-cell` (bez
   `data-value-field=Wpis`, tekst ze spacją, zaczyna wielką literą). Kratka i nazwisko na tej
   samej wysokości (`getBoundingClientRect().top`, tolerancja ~8px). Test parowania: **15/15**.
   Wiersze NIE mają stabilnego recordindex → dlatego geometria. `data-key` daje ID ucznia (stały).
3. ✅ **Legenda:** `tr.x-grid-row` gdzie 2. komórka == znormalizowana nazwa symbolu; `click` wiersza wybiera.
4. ✅ **Zapis (UDOWODNIONY):** dla ucznia `click(kratka)` (mousedown+mouseup+click) → `click(wiersz legendy)`.
   Sekwencyjnie z odstępem ~120–180 ms. Fill-only; ANULUJ/Zapisz u nauczyciela.

## Do zbudowania

- **Skrypt VULCAN** (`vulcan-frekwencja.user.js`): panel z textarea (wklej statusy dnia),
  „Podgląd" (dry-run, bez zapisu) + „Wypełnij". Match po znormalizowanym nazwisku.
  Działa TYLKO przy OTWARTYM oknie edycji frekwencji.
- **Appka WF:** przycisk „Kopiuj dla VULCAN" — kopiuje statusy dnia jako `Nazwisko Imię <TAB> STATUS`.
- **Dostawa:** najpierw test przez konsolę (okno otwarte), potem **bookmarklet** (bez instalacji
  rozszerzenia) do codziennego użytku. `@match https://dziennik-dziennik.vulcan.net.pl/lodz/016197/*`
  gdyby jednak Tampermonkey.

## Mapowanie statusu (nasz→symbol VULCAN, znormalizowany klucz)
C/•→obecność · NĆ/NC/BS→nie ćwiczy na zajęciach WF · NB/—→nieobecność · NU→nieob. uspraw. ·
ZW→nie ćwiczy na zajęciach WF (nie „zwolniony") · SP (lub sufiks +sp)→spóźnienie

- Eksporty CSV w appce (`exportCSV`, `exportOcenyCSV`) to format RAPORTOWY, nie do importu —
  pod VULCAN osobna ścieżka danych.

## Zasady bezpieczeństwa skryptu (do wdrożenia)
1. Fill-only, nigdy auto-„Zapisz".
2. Dopasowanie po nazwisku, nie po numerze wiersza (brak dopasowania → puste + lista).
3. Podświetlenie wypełnionych + raport (X wpisanych / Y do sprawdzenia).
4. Dane dzieci nie wychodzą na zewnątrz (zakaz z CLAUDE.md projektu).

## Projekcja statusów WF → VULCAN (KANONICZNA, decyzje usera 2026-09-17)

Jedno źródło mapy: `symbolFor` w `vulcan-frekwencja.user.js`. Apka eksportuje SUROWE kody
(przycisk „Kopiuj dla VULCAN" przy dacie lekcji, jeden dzień, `Imię Nazwisko <TAB> kod`).

| kod apki | VULCAN | dlaczego |
|---|---|---|
| C (ćwiczył) | pomijany | VULCAN sam wstawia „•" po Zapisz; zaznaczamy tylko wyjątki |
| C+sp | s | |
| NC / NC+sp | nc / **s** | spóźnienie ZAWSZE wygrywa (decyzja usera: „jeśli spóźniony, zapisujemy spóźniony; reszta zostaje w dzienniku WF") |
| BS / BS+sp | nc / s | VULCAN nie ma „brak stroju" |
| NB / NB+sp | — / s | |
| NU / NU+sp | u / s | |
| ZW / ZW+sp | nc / s | „zwolniony" nieużywany (09-17) |
| zwolniony długoterminowo | nc | apka eksportuje jako ZW |
| bez statusu | pomijany | toast podaje liczbę |

Dopasowanie nazwisk: skrypt szuka nazwiska jako 1. LUB ostatniego tokenu (apka trzyma
„Imię Nazwisko", VULCAN „Nazwisko Imię"). Test e2e: `py -3.14 test_vulcan_kopiuj.py`.

## Poprawki 2026-09-17 (v12-v16, żywy test 3 uczniów: wpisano 3/3, kontrola końcowa zgodna)

1. **Przesunięcie o jednego ucznia** (objaw: „NB daje z, ZW daje —"). Przyczyna: VULCAN obsługuje OBA
   gesty naraz — klik legendy uzbraja pędzel ORAZ wpisuje symbol do aktualnie zaznaczonej kratki.
   Skrypt zostawiał kratkę ucznia i zaznaczoną, więc klik legendy dla ucznia i+1 nadpisywał ucznia i;
   kontrola per uczeń przechodziła (czytała kratkę PRZED nadpisaniem). **Fix:** przed klikiem legendy
   zaznacz kratkę właściwego ucznia (kratka → legenda → kratka działa w obu modelach) + kontrola
   końcowa wszystkich kratek po serii.
2. **Weryfikacja kreski.** VULCAN wpisuje inny znak myślnika niż `—` w `SHORT`; porównanie padało i
   skrypt malował 3×. **Fix:** wzorcem jest glif z 1. komórki wiersza legendy, `SHORT` awaryjnie.
3. **Uzbrojenie sprawdzane** (`armedName`): po kliku legendy skrypt czyta zaznaczony wiersz i ponawia do 3×.
4. **Snippet usera żyje w `D:/Users/Desktop/vulcan-frekwencja.txt`** — każdą zmianę kopiuj tam
   (`pulpit vulcan-frekwencja.user.js --name vulcan-frekwencja.txt`) i podbij `vNN` w nagłówku panelu,
   inaczej user uruchamia starą wersję (kosztowało 2 rundy).
5. **ZW → nc** (decyzja usera): „zwolniony" w VULCAN = nieobecny z powodu zwolnienia; w ZSS zapis martwy.

## Szczebel 2 domknięty (2026-09-17 wieczór, v17→v18)

**A. Usprawiedliwienia z e-dziennika (v17).** Rodzic usprawiedliwia przez VULCAN zanim nauczyciel
otworzy lekcję → w kratce stoi już `u` (lub `ns`/`z`), a apka ma jeszcze `NB`. Skrypt czyta kratkę
PRZED malowaniem: jeśli apka chce `—` (nieobecność), a kratka ma `u`/`ns`/`z` → **nie nadpisuje**,
kratka złota, w logu osobna lista „✋ już usprawiedliwieni w VULCAN (popraw w apce na NU): …".
Kierunek prawdy: VULCAN wygrywa dla usprawiedliwień, apka dla ćwiczenia/stroju/spóźnienia (`nc`,
`s` nadpisują `u` — świadomie). Czysta funkcja `keepExcused(symbolName, cellTexts)`, test
`py -3.14 test_vulcan_usprawiedliwienia.py` (12 przypadków + 3 kontrole strukturalne).
Kontrola końcowa pomija zachowane kratki. Powrót do apki: komenda „usprawiedliw Nazwisko" (NB→NU).

**C. Panel sprzątnięty (v18).** Wycięte bloki DEBUG (pary/duplikaty/data-key), DIAG (lista siatki)
i ZNAKI SPECJALNE — problemy, którym służyły, są naprawione w kodzie (dedup po `data-key`, `norm`).
Zostaje: liczba uczniów, „SPRAWDŹ dopasowania", ostrzeżenia, diagnostyka przy nieudanym kliku.

**B. Bookmarklet.** `py -3.14 build_bookmarklet.py` → `vulcan-frekwencja.bookmarklet.txt`
(`javascript:` + kod bez nagłówka UserScript, URL-encoded; skrypt sprawdza, że adres dekoduje się do
identycznego kodu). ~26 tys. znaków. Instalacja: nowa zakładka w pasku Chrome/Edge, w pole adresu
wkleić CAŁĄ treść pliku. Użycie: otwórz okno edycji frekwencji → klik zakładki → panel. Aktualizacja
= edycja adresu zakładki. **NIE sprawdzone na żywo** (limit długości adresu zakładki w Chrome/Edge
— zgaduję, że 26 tys. mieści się; jeśli zakładka się ucina, wracamy do snippetu, który działa).
Kopie na pulpicie: `vulcan-frekwencja.txt` (snippet) + `vulcan-frekwencja-bookmarklet.txt`.

**B′ (2026-09-17, po teście usera): pełny bookmarklet się URYWA.** Zakładka Chrome/Edge przyjęła
ok. 11–12 tys. znaków z 26 tys. — kod obcięty w połowie, klik nic nie robi. Rozwiązanie:
`vulcan-frekwencja.loader.txt` (747 znaków) — zakładka dociąga aktualny skrypt z publicznego repo
(`<script>` z jsDelivr `@main`, awaryjnie `fetch` z raw.githubusercontent + `Function`).
Aktualizacja = `git push` (zakładki nie ruszać); jsDelivr cache'uje do ~12 h — pilna zmiana:
otwórz w przeglądarce `https://purge.jsdelivr.net/gh/ArturZienczyk/dziennik-wf@main/vulcan-frekwencja.user.js`.
**Potwierdzone na żywo 2026-09-17 (user): zakładka-loader działa na stronie VULCAN** — CSP nie
blokuje skryptu z jsDelivr. Dostawa domyślna = zakładka; snippet DevTools zostaje jako plan B.
