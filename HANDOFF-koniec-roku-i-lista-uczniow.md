# HANDOFF — koniec roku szkolnego i praca na liście uczniów (2026-09-22)

> **Po polsku:** co ma się stać z dziennikiem po zakończeniu roku szkolnego, żeby nie przepisywać klas
> od zera, oraz jak zmieniać skład i kolejność listy uczniów w trakcie roku. **Handoff zapisuje problem,
> stan kodu i pytania — bez gotowych rozwiązań** (zasada Artura z 22.09: pomysł agenta zapisany jako
> ustalenie każe następnej sesji bronić go jak decyzji Artura). Nic tu nie jest zatwierdzone.

## Co zgłosił Artur (22.09, słowa)
> „co z dziennikiem po zakończeniu roku szkolnego, wykorzystanie danych z klas, żeby nie przepisywać,
> tylko podmienić klasę, czy dodawanie czy odejmowanie uczniów w klasach, czy przesuwanie ich na liście
> góra dół"

Cztery sprawy pod jednym zgłoszeniem:
1. **Nowy rok z tych samych klas** — nie przepisywać listy, „podmienić klasę" (np. 6b → 7b).
2. **Dodanie ucznia** do istniejącej klasy (w trakcie roku albo na starcie nowego).
3. **Odjęcie ucznia** (odchodzi ze szkoły / zmienia klasę).
4. **Przesuwanie na liście góra/dół** — kolejność wierszy.

## Stan kodu (zmierzony 22.09 w `dziennik_wf.html`, nie decyzja)
| Sprawa | Co jest dziś | Gdzie |
|---|---|---|
| Nowy rok | **Brak.** Jest tylko „+ klasa" (pusta, 10 pustych wierszy) i „zmień nazwę" (zmienia nazwę, ale cała frekwencja/oceny/pomiary starego roku zostają w tej samej klasie). Nie ma kopiowania listy do nowej klasy ani pojęcia „rok szkolny" w klasie. | `uiAddClass` ~3177, `uiRenameClass` ~3191, `makeClass` ~2085 |
| Granica czasu w klasie | Jest `semesterBreak` (granica półrocza) — statystyki liczą okna I / II / cały rok od **całej historii** klasy. Rok szkolny istnieje tylko w planie lekcji (`rokSzkolnyStart`, od 1.09). | ~2095, ~2615, ~5703 |
| Dodanie ucznia | Jest: „+ Dodaj ucznia" i szybkie dopisywanie nazwiskiem z Enterem. | `addStudent` ~4210, quick-add |
| Odjęcie ucznia | Jest „×" w wierszu = **usunięcie razem z całą historią** obecności i pomiarów (potwierdzenie, ale bez kopii bezpieczeństwa — w odróżnieniu od usuwania klasy). Nie ma „odszedł od daty X" z zachowaniem historii. | `deleteStudent` ~4227 |
| Kolejność | **Brak** sortowania i przesuwania. Lista = kolejność dopisania (`state.students`). | `renderStudents` |
| Identyfikatory | Nowy uczeń `'u' + Date.now()`, ale startowe puste wiersze nowej klasy mają `u1…u10` — **te same id w każdej klasie**. Scalanie kopii i historia chodzą po id. Ważne przy każdym pomyśle „przenieś ucznia między klasami". | `uiAddClass`, `addStudent` |
| Mostek do VULCANa | Paruje po **nazwisku i imieniu**, nie po kolejności — przesunięcie na liście go nie psuje (do sprawdzenia przy każdej zmianie: `test_vulcan_pary.py`). | README §VULCAN |

## Pytania do Artura (jego domena: szkoła, rytm roku, prawo) — bez odpowiedzi nie projektować
- **P1.** Co ma zostać ze starego roku po „podmianie"? Historia do wglądu (np. do końca września, do
  odwołań od oceny), czy zeszłoroczne dane mogą zniknąć z dziennika i żyć tylko w kopii?
- **P2.** Jak zmieniają się Twoje klasy między latami w ZSS? Ta sama klasa idzie w górę (6b → 7b) z
  prawie tym samym składem? Technikum i LO tak samo? Ile klas co roku jest zupełnie nowych?
- **P3.** Uczeń, który odchodzi w trakcie roku — ma zniknąć z listy, czy zostać wyszarzony z historią
  (frekwencja do dnia odejścia liczy się do klasyfikacji)?
- **P4.** Przesuwanie góra/dół — po co? Żeby lista szła **jak w VULCANie / w dzienniku papierowym**
  (numer z dziennika), czy alfabetycznie, czy w innym porządku (np. grupy na lekcji)? To rozstrzyga,
  czy wystarczy „sortuj", czy potrzebne jest ręczne przesuwanie.
- **P5.** Kiedy to jest potrzebne pierwszy raz? Koniec roku to czerwiec 2027 — czy wcześniej
  (np. uczeń przeniesiony w październiku)?

### Odpowiedzi Artura (2026-10-02, słowa w skrócie)
- **P1.** „ale kopię będzie można odtworzyć?" — odpowiedź zależna od tego, czy stary rok da się odtworzyć
  z kopii. Stan dziś: wczytanie kopii **scala** albo, z checkboxem „Zastąp wszystko", podmienia całość
  (README §Synchronizacja). Jak to zagra z kopią sprzed zmiany roku — niesprawdzone, bo zmiany roku
  jeszcze nie ma. **Otwarte.**
- **P2.** Tak — ta sama klasa idzie w górę z prawie tym samym składem.
- **P3.** Wyszarzony (z historią).
- **P4.** Przesuwanie na wypadek pomyłki w kolejności — żeby nie kasować listy do miejsca pomyłki,
  tylko przesunąć wiersz. (Czyli ręczne przesuwanie, nie sortowanie.)
- **P5.** Teraz tylko w piaskownicy; naprawdę potrzebne w czerwcu 2027.
- **P6.** Wszystkie trzy zakresy: pojedyncza lekcja, cały dzień, kilka dni.
- **P7.** Kafelek lekcji w przyszłym dniu (Obecność → strzałka na przyszły dzień → klik w kafelek).

## Czego NIE wiemy / ryzyka do sprawdzenia przed projektem
- Czy PZO/statystyki ZSS wymagają zachowania frekwencji ucznia, który zmienił klasę.
- Jak scalanie kopii telefon ↔ laptop zachowa się, gdy na jednym urządzeniu klasa zostanie
  „podmieniona", a na drugim jeszcze nie (dwie wersje tej samej klasy w obiegu).
- Produkt dla kolegów (HANDOFF-plan-produkt): nowy nauczyciel nie ma historii — ścieżka „nowy rok"
  nie może zakładać, że poprzedni rok istnieje.

## Dopisek 1 — „nie było" wpisane z wyprzedzeniem (Artur 22.09, słowa)
> „możliwość dopisania do lekcji wcześniej niż teraz, że lekcja nie odbyła się lub nie odbędzie się,
> bo teraz muszę specjalnie czekać, a czasem jest czas, by wpisać do planu dużo szybciej, że jej nie będzie"

**Stan kodu (zmierzony, nie decyzja):** jedyne wejście, które znalazłem, żeby **ustawić** „nie było",
to przycisk w liście **Zaległe** (`zalegleNieBylo`, `dziennik_wf.html` ~2774/~2906). A Zaległe to
lekcje z przeszłości bez wpisu. Stąd czekanie: lekcja przyszła albo dzisiejsza jeszcze nie jest zaległa,
więc nie ma gdzie kliknąć. Kafelek lekcji (`kolumnaPodgladu` ~3520) pokazuje „nie było" dopiero,
gdy flaga już jest (klik = zmiana powodu), a nie pozwala jej postawić. Model danych przyszłości nie
blokuje: `cls.odwolane[klucz]`, gdzie klucz to data + numer lekcji (tak samo dla dnia przyszłego).
Nie sprawdzałem, czy ◀ ▶ w widoku dnia pozwala wejść w przyszły tydzień i czy kafelki przyszłych lekcji
się tam rysują — **do weryfikacji przed projektem**.

**Pytania:**
- **P6.** Skąd zwykle wiesz z wyprzedzeniem: wycieczka, rekolekcje, apel, egzaminy, Twoje szkolenie?
  Czy to zwykle **pojedyncza lekcja**, **cały dzień**, czy **kilka dni** (np. wyjazd klasy na 3 dni)?
- **P7.** Gdzie byś tego szukał odruchowo: w **Planie** (siatka tygodnia), w **Obecności** na kafelku
  lekcji w przyszłym dniu, czy obok „Dni wolne"?

## Dopisek 2 — „Start w 5 minut" (link w stopce) do uaktualnienia
> „uaktualnić, jeżeli będzie taka potrzeba, dziennik w 5 minut, który jest w stopce"

**Stan (zmierzony): potrzeba już JEST.** `start.html` krok 6 „Kopia zapasowa" podaje przyciski, których
w apce nie ma od 22.09: „🔒 Zapisz kopię" i „🔓 Wczytaj szyfrowaną". Teraz jest blok **„Kopia dziennika"**:
💾 Zrób kopię dziennika teraz · 📤 Wyślij kopię dziennika na telefon · 📂 Wczytaj kopię dziennika z
telefonu (README §„Blok »Kopia dziennika« w dwóch krokach"). Pozostałe kroki (hasło, + klasa, lista,
Plan, pierwsza lekcja, Reguły) nie były sprawdzane pod kątem dzisiejszych zmian nazw — **przejść cały
plik z apką obok**, nie tylko krok 6. Kandydat na strażnika: test, że każda nazwa przycisku cytowana
w `start.html` istnieje w `dziennik_wf.html` (dziś takiej bramki nie ma, stąd rozjazd) — **rozważany,
nie zatwierdzony**.

## Stan 2026-10-02 (koniec sesji)
Kolejność ułożona wg „kiedy potrzebne", Artur: „tak" na start od punktu 1.
1. **„Nie będzie" z wyprzedzeniem (P6/P7) — ZROBIONE W ROBOCZYM, czeka na oko Artura.**
   - Kod: `dziennik_wf_roboczy.html` (**gitignored — zmiana żyje tylko na dysku**; prod `dziennik_wf.html`
     nietknięty; kopia bezpieczeństwa `_wersje-poprzednie/dziennik_wf_roboczy_2026-10-02_nie-bedzie.html`). Funkcje: `nieByloZakres`, `nieByloZakresWidok`, zakres w `nieByloOk`/`nieByloOkno`,
     przycisk `.niebylo-postaw` w `kolumnaPodgladu` i w nagłówku otwartej lekcji; „jednak będzie" dla dnia ≥ dziś.
   - Piaskownica zbudowana (`zrob_piaskownice.py`), skrót na pulpicie.
   - Test: `test_niebylo_wyprzedzenie.py` (28/28 na roboczym; nie wpięty w `sprawdz_wszystko.py`/pre-push —
     wpiąć przy wdrożeniu, uruchamiać z arg `dziennik_wf.html`).
   - **Plansza uwag ze zrzutami (6 szt.):** `D:\Users\Desktop\Plansze\nauczyciel\2026-10-02_nie-bedzie-z-wyprzedzeniem`.
     Otwarcie: `python D:\Projects\design\tools\plansza_uwag.py otworz "<folder>" --port 8780`
     (własny port — patrz pułapka niżej). Artur jeszcze nic nie zaznaczył.
   - Dalej: uwagi z planszy → poprawki w roboczym → „pasuje" → `python wdroz_roboczy.py --wdroz` → bramki
     (`sprawdz_wszystko.py` przed push, bieg ~4 min) → commit. **Przed wdrożeniem sprawdź, czy prod nie dostał
     zmian od 30.09** (roboczy był równy prod 02.10) — inaczej `wdroz_roboczy` je cofnie.
2. Uczeń „odszedł" — wyszarzony z historią (P3). Nie zaczęte.
3. Przesuwanie wiersza góra/dół (P4). Nie zaczęte.
4. Nowy rok (P1/P2) — najpierw piaskownica; warunek projektu: co robi wczytanie kopii z poprzedniego roku
   (ryzyko: scalanie po tych samych id wrzuca stare wpisy do nowej klasy). Nie zaczęte.

**Pułapka (osobny projekt `design`, nie naprawiona):** `plansza_uwag.py` `serwuj()` — `ThreadingHTTPServer`
ma `allow_reuse_address`, na Windowsie dwa serwery wiążą ten sam port (8765), pętla „następny port" nigdy
nie rusza; przeglądarka trafia do cudzej planszy. Obejście: `--port`. Poprawka do zrobienia w tamtym projekcie.

## Resume
„Robimy handoff »koniec roku i lista uczniów« z
`D:\Projects\nauczyciel\wf\dziennik-wf\HANDOFF-koniec-roku-i-lista-uczniow.md`, sekcja »Stan 2026-10-02«.
Najpierw otwórz planszę (port 8780) i przeczytaj moje uwagi albo „pasuje" — potem wdrożenie punktu 1.
Potem punkty 2–4."
