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

## Czego NIE wiemy / ryzyka do sprawdzenia przed projektem
- Czy PZO/statystyki ZSS wymagają zachowania frekwencji ucznia, który zmienił klasę.
- Jak scalanie kopii telefon ↔ laptop zachowa się, gdy na jednym urządzeniu klasa zostanie
  „podmieniona", a na drugim jeszcze nie (dwie wersje tej samej klasy w obiegu).
- Produkt dla kolegów (HANDOFF-plan-produkt): nowy nauczyciel nie ma historii — ścieżka „nowy rok"
  nie może zakładać, że poprzedni rok istnieje.

## Resume
„Robimy handoff »koniec roku i lista uczniów« z
`D:\Projects\nauczyciel\wf\dziennik-wf\HANDOFF-koniec-roku-i-lista-uczniow.md`.
Zacznij od pytań P1–P5 — najpierw moje odpowiedzi, potem propozycja."
