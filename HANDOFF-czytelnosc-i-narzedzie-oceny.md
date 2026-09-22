# HANDOFF — „Czytelność i narzędzie do oceny" (2026-09-22 wieczór)

> **Po polsku:** Trzy sprawy pod jedną nazwą: (1) nierozstrzygnięte pytania o czytelność drogi
> kopii, (2) recenzja panelu krytyków — co znaleziono, co wdrożono, co skasowano jako fałszywe,
> (3) pytanie o narzędzie do oceny funkcjonalności, które by się przydało na stałe. Gdy Artur mówi
> „robimy handoff czytelność i narzędzie oceny", chodzi o całość.
>
> **Ten handoff celowo NIE zawiera gotowych rozwiązań.** Powód jest wprost od Artura (2026-09-22):
> poprzedni handoff zapisał pomysły agenta jako ustalenia, przez co następna sesja odziedziczyła je
> jako zastane i broniła ich, myśląc, że broni decyzji Artura. Tu są problem, pomiar i pytania.
> Warianty, które w sesji padły, są opisane jawnie jako **rozważane, nie zatwierdzone**.

## Co zgłosił Artur (to jest problem, reszta to praca wokół niego)

> „za dużo przycisków, które wprowadzają szum, czy to się da odchudzić"

oraz, po przebudowie: **„nie do końca czytelne"**.

Zgłoszona wielkość to **SZUM**, nie liczba kliknięć. W sesji 2026-09-22 rekomendowałem wariant
(dwa przyciski w pasku) na podstawie liczby kliknięć — czyli metryki, której Artur nie zgłaszał.
Trzej niezależni krytycy wskazali potem dokładnie ten element jako źródło wahania.

## 1. Pytania otwarte — nierozstrzygnięte, decyzja Artura po użyciu apki

**P1. Dwa przyciski kopii w pasku („📤 Wyślij kopię" + „📦 Kopia zapasowa") — zostają czy jeden?**
Trzej krytycy z trzech różnych korpusów, niezależnie: nie da się przewidzieć różnicy bez kliknięcia.
Cytat z przejścia zadaniowego, w roli nauczyciela: *„Boję się kliknąć nie to i coś nadpisać."*
Warianty rozważane w sesji (**żaden nie jest zatwierdzony**): jeden przycisk prowadzący do okna ·
dwa przyciski z podpisem różnicującym pod spodem · zostawić i zmierzyć po tygodniu używania.
Czego NIE wiemy: ile razy dziennie Artur realnie wysyła kopię. Bez tego „klik więcej" to spekulacja.

**P2. Hasło i PIN siedzą w „Ustawieniach kopii" — czy to właściwe miejsce?**
To pomysł z handoffu „jedna droga kopii", nie decyzja Artura. Zarzut krytyka: kto szuka zmiany hasła
do dziennika, nigdy nie zajrzy pod przycisk od kopii zapasowych. Pytanie otwarte, bo dotyczy też
tego, czy dziennik ma w ogóle osobne miejsce na sprawy dostępu (obok „Zablokuj").

**P3. Poza drogą kopii — dwa teksty, w które trafili wszyscy trzej krytycy:**
- plakietka **„Zaległe: brak planu"** — nie mówi, czego zaległość dotyczy ani czy to problem;
- pole **„Forma: ćwiczył (domyślnie)"** — w kontekście WF „forma" czyta się jako kondycja, nie jako
  domyślny status obecności.
Nie ruszane, bo poza zakresem tej sesji. Do rozstrzygnięcia, czy w ogóle są problemem dla Artura.

## 2. Recenzja — panel krytyków na drodze kopii (2026-09-22)

Metoda: panel grounded-krytyki, trzech agentów, każdy inny nazwany korpus, **żaden nie znał
projektu ani powodu, dla którego cokolwiek nazwano tak, jak nazwano**. Wejście: 8 renderów
(4 kroki × 1400 i 390 px) na stanie **zaseedowanym** (`fixture_stan.py` — 23 uczniów, 10 dni),
nie pustym. Trasa renderów: `zrzut_droga_kopii.py`.
- **K1** — 10 heurystyk Nielsena
- **K2** — information scent (Pirolli & Card), findability (Morville), wayfinding (Lynch), Miller
- **K4** — cognitive walkthrough (Wharton), 4 pytania per krok, dwa cele zadaniowe

### Wdrożone (≥2 krytyków niezależnie **i** weryfikacja w kodzie) — commit `51bd0f2`
| Finding | Kto |
|---|---|
| Lista kopii miała jako grubą etykietę surową nazwę pliku, a datę — jedyne, po czym się wybiera — drobnym drukiem | K1 (H2) + K2 (scent) + własne oko |
| Pochodzenie kopii dało się poznać tylko **przez negację** z nagłówka („nieoznaczona to ta z telefonu") | K4 |
| Droga telefon → laptop nie była opisana **nigdzie w apce** | K4 |
| „Folder kopii" i „Zapasowy folder" — ten sam rdzeń słowny, zero zdania o różnicy | K2 + K4 |
| Brak „×" przy tytule; z rozwiniętą listą okno dłuższe niż ekran telefonu, Escape na telefonie nie istnieje | K1 (H3) |

### Skasowane jako nad-raport — i to jest ważniejsze niż findingi
| Fałszywy finding | Kto | Dlaczego fałszywy |
|---|---|---|
| „Folder zmienia się z Pobranych na Dziennik WF kopie bez akcji użytkownika" — zgłoszony jako **krytyczny** | K1 **i** K4 | artefakt skryptu renderującego (atrapa folderu podstawiana po otwarciu okna), nie apki |
| „Brak ostrzeżenia o zapomnianym haśle" | K1 | okno zmiany hasła mówi to wprost (`dziennik_wf.html:6509`); krytyk zgadł zachowanie spoza zrzutu, wbrew instrukcji |

**Lekcja, która ma trafić do następnej sesji:** *zbieżność dwóch krytyków nie dowodzi prawdy* —
dowodzi zgodności co do **obrazu**. K1 i K4 zgodziły się co do błędu, którego w aplikacji nie ma,
bo oba patrzyły na ten sam zepsuty render. Filtrem jest weryfikacja w kodzie, nie liczba głosów.
To domyka wcześniejszą, błędną heurystykę z tej samej sesji („trzy trafienia = sygnał").

Znany wcześniej tryb porażki (nad-raport ze stanu pustego, empiria 19.09) **nie wystąpił** — bo
render szedł z `fixture_stan.py`. Zadziałało.

### Ryzyko wprowadzone przy naprawie i złapane na renderze
Wiersz listy potrafił sobie zaprzeczyć: „Kopia wysłana **stąd**" + „przyniesiona **z zewnątrz**",
gdy rejestr własnych nazw jest pusty (wyczyszczony `localStorage`). Etykieta mówi teraz o **rejestrze**
(„nie zapisywana tutaj"), nie o pochodzeniu — bo z braku wpisu pochodzenie nie wynika.

## 3. Pytanie o narzędzie — to jest sedno tego handoffu

Artur (2026-09-22): *„nie wiem czy nie mamy jakiegoś klasyfikatora, agenta czy umiejętności,
która chodzi po aplikacji, klika i ocenia, jak to się czyta"*.

**Stan zastany:** metoda **istnieje i jest zwalidowana dwa razy** (19.09 na dzienniku WF — 4 findingi;
22.09 na drodze kopii — 5 wdrożonych, 2 skasowane). **Nie istnieje jako narzędzie.** W ledgerze
`D:/Projects/docs/proposals-ledger.md` wisi jako **PROPOSED** od 19.09, z otwartym pytaniem
„spakować jako skill/agent czy zostaje metodą". Dlatego dziś jej nie znalazłem od razu — szukałem
narzędzia, a nie metody, i **najpierw odpowiedziałem Arturowi błędnie, że czegoś takiego nie mamy**.

**Czego brakuje, żeby to było narzędziem (opis luki, nie projekt rozwiązania):**
- trasa renderów jest pisana **od nowa per ekran** (`zrzut_droga_kopii.py` powstał dziś ad hoc);
- role krytyków K1/K2/K3/K4 żyją w pamięci jako opis, nie jako uruchamialni agenci;
- filtr anty-nad-raport (weryfikacja findingu w kodzie) robię **ręcznie**, za każdym razem;
- nie ma miejsca, w którym uznany finding staje się regułą — dziś przepisuję go ręcznie do
  `test_audyt_ux.py`.

**Pytanie do rozstrzygnięcia w nowej sesji:** czy pakujemy to w narzędzie, a jeśli tak — na jakim
**istniejącym** stanie Artura się to piggybackuje. Kandydaci do sprawdzenia, nie rekomendacje:
moment, gdy i tak robię render przed „zrobione"; moment pre-push; moment handoffu.
Bez odpowiedzi na to pytanie narzędzie umrze — będzie żyło z dobrej woli, a nie z rytmu pracy.

## Stan kodu na teraz (żeby nowa sesja nie zgadywała)

- `51bd0f2` na `origin/main`, **36/36 bramek zielonych**, `CACHE_VERSION` **v43**.
- Nowe w repo: `zrzut_droga_kopii.py` (trasa renderów), `test_wyslij_kopie.py` (18 sprawdzeń —
  w tym zapadka „pasek nie może zarosnąć" i 3 klasy wejścia parsera: typowy/brzegowy/wrogi).
- Zrzuty po poprawkach: `_zrzuty/wt2_*.png` (gitignore).
- Kieszeń pamięci: `~/.claude/projects/D--Projects-nauczyciel-wf-dziennik-wf/memory/_staging/2026-09-22.md`
  — 3 wpisy do przeglądu przy `/zakoncz`.

**Niezweryfikowane u użytkownika:** `navigator.share({files})` na Androidzie Artura — zmierzone tylko
w Chrome na laptopie i na atrapie w bramce. Nikt tego jeszcze nie kliknął na telefonie.

## Resume

„Robimy handoff »czytelność i narzędzie oceny« z
`D:\Projects\nauczyciel\wf\dziennik-wf\HANDOFF-czytelnosc-i-narzedzie-oceny.md`.
Zacznij od punktu 3 (narzędzie) — najpierw powiedz, na jakim moim istniejącym nawyku ma się to
piggybackować, zanim cokolwiek zbudujesz. Pytania z punktu 1 zostają otwarte do mojej decyzji."
