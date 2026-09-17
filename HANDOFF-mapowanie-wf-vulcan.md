# HANDOFF — projekcja statusów Dziennik WF → VULCAN

> **STAN 2026-09-17 noc (po 4. sesji, v19): Szczebel 5 (zamek) DOMKNIĘTY** — decyzje usera: hasło kopii
> + PIN 4 cyfry, 10 min od ostatniego klawisza, „Zmień hasło” zamiast podglądu. Magazyn (localStorage +
> IndexedDB) trzyma wyłącznie szyfrogram; migracja jawne→szyfrowane przejmuje stare hasło kopii i kasuje
> je z localStorage. `test_zamek.py` 35/35, pozostałe 10 testów przerobione (odblokowanie przez API).
> Sekcja „Zamek na apce” w README. **U usera po aktualizacji:** ekran „Zamknij dziennik hasłem” z
> podstawionym hasłem kopii → klik → propozycja PIN-u. Następny: Szczebel 3 (zrzuty DOM 1–3 od usera).
>
> **STAN 2026-09-17 wieczór (po 3. sesji, v18):** Szczebel 2 DOMKNIĘTY w kodzie: A (usprawiedliwienia
> `u`/`ns`/`z` z VULCAN nie nadpisywane przez NB, lista do poprawki w apce; `test_vulcan_usprawiedliwienia.py`),
> C (panel bez DEBUG/DIAG/ZNAKI), B (`build_bookmarklet.py` → `vulcan-frekwencja.bookmarklet.txt`).
> Snippet i bookmarklet na pulpicie. Pełny bookmarklet urywał się w zakładce (~12 tys. zn.) → **zakładka-loader** z jsDelivr
> (`vulcan-frekwencja.loader.txt`), DZIAŁA na żywo (user 09-17); aktualizacja skryptu = `git push`
> (+ purge jsDelivr przy pilnej zmianie), zakładki nie ruszać. **Do zrobienia przez usera:** żywy test A:
> kratka z `u` + apka `NB` → po Wypełnij kratka nadal `u`, log wymienia nazwisko.
> Następny szczebel: 3 (wiadomości do rodziców, czeka na zrzuty 1–3 od usera) lub 4 (apka: Pomiary).
> Szczegóły: `VULCAN-INTEGRACJA-USTALENIA.md` §„Szczebel 2 domknięty".

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
| ZW | `nc` | decyzja 09-17: `z` w VULCAN = nieobecny z powodu zwolnienia, u nas martwy; nc niewidoczne dla rodzica, ale Artur ma prawdę w dzienniku WF |
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

**v16 (2026-09-17 wieczór, żywy test PRZESZEDŁ — „wszystko zagrało"):** żywy test v11 wykrył
przesunięcie o jednego ucznia (klik legendy uzbraja pędzel ORAZ wpisuje do zaznaczonej kratki).
Fix: kratka → legenda → kratka + `armedName` + wzorzec glifu z legendy + kontrola końcowa
wszystkich kratek. ZW → `nc` (decyzja usera). Szczegóły: `VULCAN-INTEGRACJA-USTALENIA.md`
§„Poprawki 2026-09-17". Snippet usera = `D:/Users/Desktop/vulcan-frekwencja.txt` — każda zmiana
skryptu MUSI tam trafić (`pulpit ... --name vulcan-frekwencja.txt`) + `vNN` w nagłówku panelu.
Kolejność Szczebla 2: punkt 1 (test) DOMKNIĘTY → następne A, potem B+C.

---

## SZCZEBEL 2 (zapisany 2026-09-17, do zrobienia PO teście przycisku na żywym VULCAN)

### A. Usprawiedliwienia wchodzą do VULCANa SAME (problem zgłoszony przez usera)
Rodzic wysyła usprawiedliwienie przez e-dziennik → VULCAN wstawia `u` w kratce ZANIM nauczyciel
otworzy lekcję. Apka WF ma wtedy jeszcze `NB` (nieobecny nieuspr.). Skrypt v11 porównuje kratkę
tylko z tym, co CHCE wpisać (`beforeAll.some(t===want)`) → dla NB chce `—` i **nadpisze `u`
nieobecnością nieusprawiedliwioną**. Błąd, bo `u` z e-dziennika jest nowszą prawdą.

**Reguła (do wdrożenia w `apply`):** zanim skrypt zamaluje kratkę, czyta jej obecny symbol.
Jeśli w VULCAN stoi już `u` / `ns` / `z`, a apka chce `—` (NB) → **NIE nadpisuj**, kratka złota,
osobna lista w logu: „już usprawiedliwieni w VULCAN (popraw w apce na NU): Nowak, Lis". Kierunek
prawdy: VULCAN wygrywa dla usprawiedliwień, apka wygrywa dla ćwiczenia/stroju/spóźnienia.
Powrót do apki: apka ma komendę „usprawiedliw Nazwisko" (NB→NU, linia ~2255) — user przepisuje
z listy w logu. Krok dalszy (opcjonalny, jeśli lista bywa długa): przycisk w panelu „Kopiuj
usprawiedliwionych" → apka dostaje pole „wklej z VULCAN" i sama zamienia NB→NU.
Test: kratka z `u` + apka `NB` → po Wypełnij kratka nadal `u`, log wymienia nazwisko.

### B. Dostawa skryptu — jak to wygląda od strony użytkowania
Dziś (działa): skrypt zapisany jako **DevTools Snippet** (F12 → Sources → Snippets → Ctrl+Enter),
NIE wkleja się za każdym razem; wklejanie tylko przy aktualizacji (treść z pulpitu
`D:/Users/Desktop/vulcan-frekwencja.txt`). Rytm dnia: apka „Kopiuj dla VULCAN" → VULCAN okno
frekwencji → snippet → Ctrl+V w panel → Podgląd → Wypełnij → Zapisz w VULCAN.
Cel: **bookmarklet** = ten sam kod pod zakładką w pasku, jeden klik zamiast F12; aktualizacja =
edycja adresu zakładki. Plan B: Tampermonkey (panel sam się pokazuje), ale rozszerzenie może być
zablokowane na szkolnym laptopie. Budowa bookmarkletu: `javascript:(function(){...})()` z kodu
zminifikowanego, URL-encoded; sprawdzić limit długości adresu zakładki w Chrome/Edge.

### C. Sprzątnięcie panelu (co to znaczy)
Po „Podgląd" panel drukuje 3 bloki serwisowe z czasu walki z siatką: `DEBUG` (pary, duplikaty,
data-key per uczeń, linie 143–150), `DIAG` (lista nazwisk siatki, 156), `ZNAKI SPECJALNE`
(157–158). Problemy, do których służyły (46 fantomów DOM, znaki niewidzialne w nazwiskach) są
naprawione w kodzie (dedup po `data-key`, `norm`). Wyciąć te 3 bloki; ZOSTAWIĆ diagnostykę przy
nieudanym kliknięciu (`nie zareagowało (arm→paint) [...]`, linia ~188) — przyda się, gdy VULCAN
zmieni interfejs. Po sprzątnięciu panel = liczba uczniów, lista dopasowań, ostrzeżenia.

### Kolejność
1. User testuje przycisk + snippet v11 na żywym VULCAN z realnym dniem.
2. A (usprawiedliwienia) — zmiana w mechanizmie, więc osobny commit + test.
3. C + B razem (sprzątnięcie i bookmarklet) — jeden commit, podbić wersję w nagłówku panelu.

## SZCZEBEL 3 (zapisany 2026-09-17 wieczór) — powiadomienia rodziców o NĆ przez Wiadomości VULCAN

### Zadanie (słowami usera)
„Czy jest możliwość skryptu, aby po tym jak uczeń jest niećwiczący, to automatycznie szła
informacja do rodziców przez wiadomości w dzienniku?" Próg: **po jednym NĆ bez
usprawiedliwienia** — wiadomość ma informować o NĆ i jednocześnie przypominać zasady (strój,
usprawiedliwienia). Uwaga usera: „rodzice mogą przysłać info o usprawiedliwieniu przed lekcją
i trzeba mieć to na uwadze".

### Fakty ustalone (ze zrzutów usera, 2 obrazy w sesji)
- Wiadomości żyją na OSOBNEJ domenie: `dziennik-wiadomoscip.vulcan.net.pl/lodz/App/odebrane`
  → osobny userscript / bookmarklet, inny `@match` niż frekwencja.
- Panel: Nowa wiadomość / Odebrane (licznik) / Wysłane / Kopie robocze / Archiwum / Ustawienia /
  Grupy adresatów. Lista Odebrane ma kolumny: Nadawca (format `Nazwisko Imię - R - Nazwisko Imię
  dziecka - (016197)`, czyli **rodzic jest opisany przez dziecko**), Temat, Załącznik, Otrzymano,
  Odpowiedziano, Przekazano, Skrzynka, Przeczytano. Filtr tekstowy nad tabelą.
- Formularz „Nowa wiadomość": Wyślij jako (select) · **Adresaci** (pole tekstowe z podpowiedziami
  + 2 przyciski: książka adresowa, grupy) · Temat · edytor treści (toolbar Domyślny/Sans Serif/
  B/I/U/listy — wygląda na Quill; zgaduję, nie sprawdzone) · Rodzaj kont · Wyślij / Anuluj.
- Zwolnienia od rodziców przychodzą właśnie tu (na zrzucie 2 wiadomości „zwolnienie z ćwiczeń WF").

### Zasada (ta sama co frekwencja + zakaz z CLAUDE.md nauczyciel)
**Fill-only.** Skrypt wypełnia adresata/temat/treść, klik „Wyślij" ZAWSZE u nauczyciela.
Zakaz „NIE wysyłaj wiadomości do rodziców automatycznie" dotyczy także tej drogi.

### Kształt narzędzia (uzgodniony)
1. Dziennik WF: przycisk „Powiadom rodziców" — lista uczniów z NĆ bez usprawiedliwienia z dnia
   → schowek (nazwisko + dane do szablonu). Analog „Kopiuj dla VULCAN".
2. Panel wiadomości (skrypt): Ctrl+V listy → **krok 0: skan „Odebrane"** z ostatnich N dni po
   nadawcy (nazwisko dziecka w opisie rodzica) i temacie (`zwolnien|usprawiedliw|nie będzie
   ćwicz`) → flaga „jest wiadomość od rodzica, sprawdź" przy uczniu; skrypt czyta tylko listę
   (nadawca+temat), nie otwiera treści. → dla każdego ucznia bez flagi (lub po odklinięciu):
   Nowa wiadomość → wpisz nazwisko w Adresaci (wybór rodzica z podpowiedzi = user, dopóki nie
   znamy struktury podpowiedzi) → Temat → Treść z szablonu → user: Wyślij.
3. Szablon treści: `szablony/rodzice/nc-informacja-przypomnienie.md` (do napisania; jeden dla
   wszystkich, pola: data, imię dziecka, klasa; ton informacyjny, nie karcący).

### Ryzyka nazwane
- Fałszywy alarm: NĆ ze zwolnieniem, którego jeszcze nie ma w apce → krok 0 + decyzja usera.
- Skala: kilkanaście „Wyślij" tygodniowo — akceptowalne przy gotowym formularzu; jeśli boli,
  rozważyć „Grupy adresatów" (jedna zbiorcza wiadomość dzienna do kilku rodziców? — do sprawdzenia,
  czy VULCAN pozwala na wielu adresatów i czy to nie ujawnia listy rodzicom nawzajem).
- Edytor treści: jeśli Quill, to wpis przez `innerHTML` może nie odpalić modelu — sprawdzić
  `quill.clipboard.dangerouslyPasteHTML` lub `execCommand('insertText')` na zrzucie DOM.

### Do zebrania od usera PRZED kodem (DevTools, jak przy frekwencji; pliki na pulpit → `_zrzuty/`, NIE do gita — nazwiska rodziców)
1. Zrzut pola „Adresaci" po wpisaniu kilku liter nazwiska — jak nazwany jest rodzic przy uczniu.
2. outerHTML okna „Nowa wiadomość" → `D:/Users/Desktop/vulcan-wiadomosc.txt`.
3. outerHTML jednego wiersza listy „Odebrane" → `D:/Users/Desktop/vulcan-odebrane.txt`.

### Kolejność względem Szczebla 2
Szczebel 2 (test przycisku, A, B+C) NADAL pierwszy — ten sam skrypt frekwencji. Szczebel 3 to
nowy plik `vulcan-wiadomosci.user.js`; można równolegle, gdy przyjdą zrzuty 1–3.

## Kandydaci do dalszej automatyzacji (burza 2026-09-17, NIE decyzje — do oceny przez usera)
Kryterium goal.md: pain-driven, nie search-driven. Każdy punkt = ból, który ma ciągnąć.
1. **Usprawiedliwienia z Odebranych → apka WF** (odwrotny kierunek niż Szczebel 2A): skan
   Odebranych po temacie/nadawcy → propozycja „ustaw ZW/U dla X na daty…" w apce. Ból: ręczne
   przepisywanie zwolnień z 2 miejsc. Ryzyko: daty w temacie wolnym tekstem (`16-18.09`).
2. **Oceny WF → VULCAN** (fill-only jak frekwencja): apka ma oceny per uczeń, VULCAN ma siatkę
   ocen. Ból: podwójne wpisywanie po każdym sprawdzianie. Wymaga rozpoznania DOM okna ocen.
3. **Pomiary/testy sprawnościowe → wiadomość do rodzica** (karta ucznia z apki jako treść lub
   PDF-załącznik OneDrive). Ból: rodzic pyta „jak idzie", nauczyciel klika ręcznie. Skala mała
   (semestr), więc może zostać ręczne.
4. **Przypomnienie o stroju dzień przed** dla klasy (Grupy adresatów) — cykliczne, jedna
   wiadomość. Ból wątpliwy; łatwo przejść w spam. Raczej NIE.
5. **Zebranie NĆ tygodniowe → wychowawca** (nie rodzic): jedna wiadomość do wychowawcy klasy z
   listą uczniów z ≥2 NĆ. Ból: wychowawca dowiaduje się na radzie. Możliwe piggyback na tym samym
   skrypcie wiadomości (adresat = nauczyciel).
6. **Wykrywanie sprzeczności apka↔VULCAN** po „Zapisz" (odczyt siatki i porównanie ze statusem w
   apce, raport różnic). Ból: rozjazd po ręcznych poprawkach w VULCAN. Read-only, bezpieczne.
Najwięcej sensu na dziś (moja ocena): 1 i 5 — oba jadą na skrypcie wiadomości, który i tak
powstaje w Szczeblu 3; 2 to osobne rozpoznanie DOM; 6 tanie, ale bez zgłoszonego bólu.

## SZCZEBEL 4 — DOMKNIĘTY 2026-09-17 (3 commity, GitHub Pages = wdrożone; testy `test_pomiary_kolumny.py`, `test_pomiary_status.py`, `test_zwolnienie_od_do.py`)

- **4.1 Przypinanie kolumny.** Przycisk `⇤` w nagłówku testu; przypięta kolumna stoi tuż za nazwiskiem
  (przed Wzrost/Waga), podświetlona, fokus wskakuje w 1. kratkę; `⇥` odpina. Pole `cls.pinnedTest` (id),
  kolejność `testFields` i dane pomiarów nietknięte.
- **4.2 Status w kratce wyniku.** Pole tekstowe zamiast number: liczba ALBO `NB`/`NĆ` (w danych `NB`/`NC`
  jak we frekwencji; `nc`, `nć`, `n.c.` → `NC`; `12,5` → `12.5`). Karta ucznia pokazuje status z opisem.
  Średnich z pomiarów apka nie liczy — nie było czego omijać.
- **4.3 Zwolnienie OD–DO.** `s.releases = [{od, do}]` (opcjonalne, stare kopie bez migracji). Uczniowie:
  kolumna z chipami + od/do/`+`. W dniu z okresu: Obecność pokazuje `ZW?` (klik = inny status), pasek
  i okno „Zapisz lekcję" wymieniają, kto dostanie ZW; zapis nadaje ZW zamiast C; „Kopiuj dla VULCAN"
  eksportuje ZW; karta ucznia listuje okresy. Po DO uczeń wraca sam. **Nie zrobione:** oznaczanie
  pomiarów w okresie — pomiar nie ma daty, nie ma czego porównać (użyj NĆ w kratce, 4.2).

Oryginalny zapis szczebla (dla kontekstu):

## SZCZEBEL 4 (zapisany 2026-09-17 wieczór, słowa usera po udanym teście VULCAN) — apka WF, zakładka Pomiary

Trzy bóle zgłoszone przez usera, wszystkie po stronie `dziennik_wf.html` (NIE userscriptu):

1. **Ruchome kolumny w Pomiarach.** Przy wpisywaniu wyników danego testu kolumna jest daleko od
   nazwisk i łatwo zgubić wiersz. Cel: przesunąć wybraną kolumnę testu na początek (tuż za
   nazwisko) na czas wpisywania — przycisk „na początek" w nagłówku kolumny albo drag nagłówka.
   Kolejność nazwisk niezmienna. Gdzie: tabela `.pomiary-table` (HTML ~1095), kolumny dopisuje
   `renderPomiary()` z `getTestFields()`. Propozycja: pole `pomiaryColOrder` w stanie (lista id
   testów), render czyta kolejność z niego; zero zmian w danych pomiarów.
2. **Status na teście: nieobecny / niećwiczący.** Dziś kratka wyniku jest tylko liczbą; brak
   rozróżnienia „nie było go" od „był, nie ćwiczył" od „nie wpisano jeszcze". Cel: w kratce
   wyniku obok liczby dopuszczalne `NB` / `NĆ` (klawiaturą, jak statusy frekwencji), render
   pokazuje etykietę zamiast liczby, karta ucznia i średnie pomijają takie wpisy. Sprawdzić
   kolizję z rubrykami/karta ucznia (`test_karta_ucznia.py`).
3. **Zwolnienie lekarskie w określonym terminie.** Dziś jest tylko `longTermReleased` (flaga
   bez dat, uczeń znika z listy) i ZW per lekcja. Cel: zwolnienie z datą OD–DO per uczeń
   (lista okresów); w dniach z okresu apka podpowiada/wymusza ZW przy frekwencji i oznacza
   pomiary; po dacie DO uczeń wraca sam. Projekcja do VULCAN bez zmian (ZW → `nc`). Gdzie:
   model `students[]` (`longTermReleased` linie ~1688/1793/1879/1961), setStatus dla ZW (~1249).
   Uwaga na zgodność ze starymi kopiami (szyfrowane JSON) — pole nowe, opcjonalne, migracja
   przy wczytaniu.

Kolejność (propozycja): 1 (najmniejsze, czysty UI) → 2 (model kratki wyniku) → 3 (model ucznia +
migracja kopii). Każdy punkt: próba na jednej klasie przed skalą, test w stylu istniejących
`test_*.py` (Playwright, `py -3.14`).

## SZCZEBEL 5 — DOMKNIĘTY 2026-09-17 noc (v19; `test_zamek.py` 35/35; sekcja „Zamek na apce” w README)

Zrealizowane wg kształtu niżej z decyzjami usera: (1) hasło kopii + PIN 4 cyfry, (2) 10 min od
ostatniego klawisza + `visibilitychange`, (3) „Zmień hasło” po podaniu starego, bez podglądu.
Odstępstwa od planu: hash PIN-u w środku szyfrogramu (nie osobno); 5 złych PIN-ów → hasło;
przycisk „🔒 Zablokuj” w pasku zakładek; testy odblokowują przez API zamiast bypassu.
Ryzyko „PIN co 10 min na lekcji” — user ocenia po tygodniu; `zamekCfg.minuty` to jedna liczba.

### Kształt pierwotny (dla historii)

### Skąd
Research `research-notes/2026-09-17_regulamin-vulcan-automatyzacja.md`: skrypty do VULCAN literalnie
nie podpadają pod jedyny znaleziony zapis dostawcy o automatyzacji (eduVULCAN pkt 15: auto-logowanie,
scraping, inne oprogramowanie niż przeglądarka). Realne ryzyko regulaminowe leży w DANYCH DZIECI NA
LAPTOPIE (wzorcowy regulamin szkolny §84: nośniki z danymi w sejfie; §13.1 nie udostępniać zasobów).
Dziś: kto ma odblokowany laptop, otwiera dziennik i widzi wszystko (README „Brak zamka na apce").

### Kształt (propozycja — do „pasuje / nie pasuje" na starcie sesji)
1. **Ekran blokady przy otwarciu i po bezczynności.** Apka startuje zasłonięta; odblokowanie = hasło
   (to samo co hasło kopii `dziennik_wf_backup_pwd`, żeby user pamiętał JEDNO; do rozstrzygnięcia:
   osobny PIN 4–6 cyfr na szybkie odblokowanie na lekcji?). Po N minutach bez ruchu (domyślnie 10)
   ekran wraca; `visibilitychange` (karta w tle) też blokuje.
2. **Dane w pamięci przeglądarki ZASZYFROWANE tym hasłem** (localStorage + IndexedDB trzymają
   ciphertext; jest już `encryptSnapshot` AES-GCM + PBKDF2 — reużyć). Bez tego zamek jest tylko
   zasłoną: DevTools → Application → localStorage pokazuje nazwiska. To jest sedno, nie ekran.
   Koszt: `save()` szyfruje przy każdym zapisie (PBKDF2 raz przy odblokowaniu, klucz w pamięci
   strony; AES per zapis jest tani). Migracja: przy pierwszym uruchomieniu po aktualizacji apka
   czyta jawne dane, prosi o hasło, zapisuje szyfrowane, kasuje jawne. Stare kopie `.enc.json`
   działają bez zmian.
3. **Zapomniane hasło = dane nie do odzyskania** (poza kopiami, które mają to samo hasło). Powiedzieć
   to userowi wprost na ekranie ustawiania. Alternatywa: przycisk „🔑 Hasło kopii" dziś POKAZUJE
   hasło — po zamku nie może (bo pokazałby je każdemu przy odblokowanym laptopie) → zamiast tego
   „zmień hasło" po podaniu starego.
4. **Nie ruszać:** kolejność zakładek, klawiatura, testy `test_*.py` (dopisać `test_zamek.py`:
   start zasłonięty, złe hasło nie odsłania, po odblokowaniu dane są, localStorage nie zawiera
   nazwiska, po bezczynności ekran wraca, migracja jawne→szyfrowane zachowuje wszystko).

### Ryzyka nazwane
- Blokada na lekcji = tarcie (hasło co 10 min przy wpisywaniu). Stąd PIN + timer liczony od
  ostatniego klawisza, nie od otwarcia. User oceni po tygodniu.
- Szyfrowanie storage podnosi koszt `test_pamiec.py` (pełna pamięć) — rozmiar ciphertextu ≈ jawny
  +33% (base64). Sprawdzić limit 10 MB dla największej klasy.
- Dyktowanie głosem i VULCAN „Kopiuj" — bez zmian (działają po odblokowaniu).

### Kolejność względem 3
Zamek (5) PRZED wiadomościami do rodziców (3): najpierw zabezpieczyć dane, które już są, potem
dokładać kanał komunikacji. Szczebel 3 nadal czeka na 3 zrzuty DOM od usera.

### Otwarte u usera (bez tego można zaczynać, ale warto wiedzieć)
- Po zalogowaniu do UONET+: Pomoc → Regulamin → skopiować akapit o „oprogramowaniu/automatyzacji"
  (regulaminu nauczyciela nie widać z zewnątrz).
- Czy ZSS ma własny regulamin e-dziennika (na stronie szkoły go nie ma) — pytanie do administratora.
