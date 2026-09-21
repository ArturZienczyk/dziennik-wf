# Dziennik WF

Single-file aplikacja (HTML+JS, bez instalacji, offline) do prowadzenia frekwencji,
pomiarów sprawności i ocen na WF. Dyktowanie głosem na sali (mikrofon / Win+H).

## Uruchomienie

Otwórz `dziennik_wf.html` w przeglądarce (dwuklik). Działa lokalnie, nic nie wychodzi
na żaden serwer.

## Dane i backup

- Dane żyją w `localStorage` **i** w IndexedDB tej przeglądarki — per przeglądarka,
  per komputer — **wyłącznie jako szyfrogram** (hasło dziennika; patrz „Zamek”). Drugi magazyn jest po to, by wpisy nie ginęły, gdy wspólny limit
  plików otwieranych z dysku się zapełni (patrz „Pełna pamięć przeglądarki").
- Kopia zapasowa: **zawsze zaszyfrowana hasłem** — auto raz dziennie przy zapisie
  lekcji, przed każdą operacją kasującą i ręcznie przyciskiem „Zapisz kopię".
  Szczegóły: „Kopie zapasowe — zawsze zaszyfrowane" niżej.
- Backupy trzymaj w `backups/` — folder jest w `.gitignore` (imiona/oceny dzieci
  NIGDY nie idą do git ani na Drive bez szyfrowania — zakaz CLAUDE.md projektu).

## Wprowadzanie danych z klawiatury (Faza 5, laptop)

Założenie: dane wpisujesz **przy biurku, serią po lekcji**. Mysz nie jest potrzebna
w żadnej z trzech ścieżek; wszędzie obowiązuje ta sama zasada — **Enter zapisuje
i schodzi w dół**.

**Frekwencja** (zakładka Obecność, kursor = podświetlony wiersz):

| klawisz | co robi |
|---|---|
| `↑` `↓` | wybór ucznia |
| `c` | ćwiczył (C) |
| `n` | nie ćwiczył (NĆ) |
| `b` | brak stroju (BS) |
| `w` | wagary / nieobecny nieusprawiedliwiony (NB) |
| `u` | nieobecny usprawiedliwiony (NU) |
| `z` | zwolnienie jednorazowe (ZW) |
| `r` | nieobecność z przyczyn szkolnych (NS) — „r” jak *reprezentuje szkołę* |
| `1`–`7` | to samo, w kolejności legendy |
| `s` | dokleja spóźnienie do statusu, który już jest |
| `0` | czyści status |
| `Enter` | zapisuje lekcję (drugi `Enter` potwierdza okno) |

### Procent ćwiczył — jedno źródło prawdy

Cały procent liczy **jedna funkcja**: `wagaLekcji(status, spóźniony)`. Każdej lekcji przypisuje
dwie wagi — ile wnosi do **bazy** (mianownik) i ile do **ćwiczył** (licznik). Pytają ją wszyscy:
tabela Statystyk, wydruk i PDF, CSV, „% dotąd” w Obecności, oceny z Systematyczności, kafelki
i krzywa na karcie ucznia, a także **wzór rysowany w zakładce Reguły** (więc wzór nie może
skłamać — pokazuje dokładnie to, co apka liczy).

Po co: do 2026-09-21 karta ucznia miała **własny wzór** i nie patrzyła na przełączniki z Reguł.
Przy domyślnych ustawieniach oba wzory dawały to samo, więc nic nie było widać — ale wystarczyło
przestawić jedną regułę (np. wyłączyć „Brak stroju liczy się jak nieobecność”), żeby ten sam
uczeń miał w tabeli inny procent niż na swojej karcie. Po cichu, bez błędu.

**Dokładasz nowy status albo nową regułę? Dopisz jeden warunek w `wagaLekcji()`** — reszta apki
pójdzie za tym sama. Bramka: `py -3.14 test_jedno_zrodlo_procentu.py` przechodzi po wszystkich
pięciu przełącznikach w obie strony i za każdym razem porównuje tabelę z kartą ucznia; pilnuje
też, że warunki reguł występują w kodzie **dokładnie raz**.

**NS — nieobecność z przyczyn szkolnych** (2026-09-21). Uczeń jest na zawodach, konkursie,
wycieczce albo w poczcie sztandarowym. **Liczy się jak ćwiczył**: wchodzi do bazy procentu
i do licznika, więc nie tylko nic nie zabiera, ale rozcieńcza cenę pojedynczego niećwiczenia
(C, C, NĆ, NS → 3/4 = **75%**).

To **świadome odstępstwo od litery PZO** (decyzja Artura 2026-09-21, na korzyść ucznia).
PZO mówi: *„nieobecności […] związane z działalnością na rzecz szkoły nie są wliczane do ogólnej
liczby zajęć”* — czyli literalnie takie lekcje powinny z bazy **wypadać** (ten sam uczeń miałby
wtedy 2/3 = 67%). Uzasadnienie odstępstwa: uczeń reprezentujący szkołę formalnie **jest**
na zajęciach szkolnych, więc traktujemy to jak obecność z ćwiczeniem.

W zakładce **Reguły** stoi piąty przełącznik — *Zajęcia szkolne (NS) liczą się jak ćwiczył* —
**domyślnie włączony**. Wyłączenie wraca do litery PZO: NS wypada z bazy jak NU i ZW.
Przełącznik zmienia liczenie wstecz (Statystyki, % dotąd, Systematyczność, karta ucznia,
wzór w Regułach) — wpisy zostają nietknięte. Jest po to, żeby dyrekcja albo kontrola PZO
mogła zobaczyć obie wersje bez grzebania w kodzie, nie do codziennego klikania.

W VULCANie odpowiada temu symbol **ns** („nieob. uspr. szkolne”) — skrypt
`vulcan-frekwencja.user.js` wstawia go sam. Klawisz to `r`, nie `ns`: `n` i `s` są już
zajęte (NĆ i spóźnienie). Bramka: `py -3.14 test_status_ns.py`.

Po nadaniu statusu kursor **sam schodzi niżej** — zaznaczasz tylko wyjątki i kończysz
`Enter`em. Okienko statusów (klik myszą) nadal działa i też przyjmuje te litery;
w nim siedzą zaległe usprawiedliwienia NB.

**Oceny i pomiary** — edycja wprost w komórce, bez okna:
`Enter` zapis + następny uczeń · `Shift+Enter` w górę · `Tab` następna kolumna ·
`Esc` anuluj · puste pole + `Enter` kasuje ocenę · dwuklik otwiera stare okno z suwakiem.

**Lista klasy** (zakładka Uczniowie): pole „Dopisz uczniów" — nazwisko + `Enter`,
pole zostaje aktywne, lecisz całą kartką. Wklejenie kilku linii naraz dodaje wszystkich.
Puste wiersze, które już są na liście, zapełniają się pierwsze. W tabeli `Enter`
przechodzi do pola niżej, a na ostatnim wierszu dopisuje kolejnego ucznia.

Wszystkie okna (potwierdzenia, hasła, nowa kolumna) zamyka `Esc`, a zatwierdza `Enter`.

### Bramka regresji

```
py -3.14 test_klawiatura.py
```

22 sprawdzenia end-to-end w prawdziwej przeglądarce (Playwright): steruje wyłącznie
klawiaturą i czyta stan z `localStorage`. Zrzuty ekranu lądują w `_zrzuty/` (poza git).
**Po każdej zmianie w `dziennik_wf.html` odpal ten test** — ścieżka klawiaturowa jest
niewidoczna gołym okiem i łatwo ją zepsuć przy okazji innej poprawki.

## Kopie zapasowe — zawsze zaszyfrowane (Faza 6)

Do września 2026 kopie wychodziły **jawnie**: auto-kopia raz dziennie przy zapisie
lekcji, kopia przed każdą operacją kasującą i ręczny „Zapis JSON" lądowały
w Pobranych jako czytelny plik z imionami i ocenami. Taki plik wysłany mailem albo
przeniesiony na pendrive to wyciek danych dzieci. Od Fazy 6 **każda** kopia jest
szyfrowana (AES-GCM 256 + PBKDF2-SHA256, 150 000 iteracji).

- Hasło ustawiasz **raz** — apka poprosi o nie przy pierwszym zapisie lekcji.
  Potem żadna kopia już nie pyta; wpisywanie danych idzie bez przerw.
- **Auto-kopia ma dwa wyzwalacze** (drugi od 2026-09-21): pierwsze „Zapisz lekcję"
  w danym dniu **oraz** odblokowanie dziennika hasłem. Powód: dzień bez zapisanej
  lekcji nie zostawiał żadnej kopii, choć stan się zmieniał (import kopii z telefonu,
  same oceny, pomiary). Licznik dnia jest wspólny, więc kopia jest najwyżej jedna na
  dobę i na urządzenie. Odblokowanie PIN-em po bezczynności kopii nie robi — to ten
  sam, już otwarty dzień pracy. Bramka: `py -3.14 test_kopie.py`.
- Hasło pamięta ta przeglądarka. To świadomy kompromis: kto ma odblokowany laptop,
  widzi dane i tak w samym dzienniku — więc hasło obok nich niczego nie osłabia.
  Chroniony jest **plik, który wychodzi z laptopa**.
- Zapomniane hasło podejrzysz przyciskiem **🔑 Hasło kopii** (tam też się je zmienia;
  starsze kopie otwiera nadal stare hasło).
- Operacja kasująca dane (wyczyść wszystko / import / usuń klasę) **nie wykona się**,
  jeśli kopia bezpieczeństwa nie powstała. Anulowanie hasła = dane nietknięte.
- Jawny przycisk „Zapis JSON" zniknął. Wczytywanie **starych**, nieszyfrowanych
  kopii zostaje („📂 Wczytaj stary JSON") — te sprzed września nadal się otwierają.
- Przeglądarka bez Web Crypto: kopia powstaje jawna, ale z głośnym ostrzeżeniem
  (utrata danych jest gorsza niż jawny plik na własnym dysku). Zmierzone 2026-09-14:
  w Chromium szyfrowanie działa **także z pliku otwartego z dysku** (`file://`) —
  zaszyfrowanie i odszyfrowanie przechodzą.

**Folder kopii (2026-09-17).** Przycisk **📁 Kopie: Pobrane** w zakładce Uczniowie — raz wskazujesz
folder (np. `Dziennik WF kopie` na pulpicie) i od tej pory każda kopia, automatyczna i ręczna, zapisuje
się prosto tam, bez okienka. Przeglądarka pamięta folder między uruchomieniami (uchwyt w IndexedDB);
Chrome może raz na sesję zapytać o zgodę na zapis. Gdy folder jest niedostępny (brak zgody, folder
usunięty, przeglądarka bez tej funkcji) kopia idzie do Pobranych, a dymek o tym mówi — kopia nigdy
nie przepada. Shift+klik na przycisku = powrót do Pobranych. Bramka: `py -3.14 test_folder_kopii.py`
(atrapa folderu; prawdziwy wybór folderu sprawdza użytkownik w Chrome).

Bramka: `py -3.14 test_kopie.py` — 13 sprawdzeń, kluczowe: **pobrany plik nie zawiera
nazwiska dziecka**, zła fraza go nie otwiera, własne hasło odtwarza dane w całości.

### Czego to NIE załatwia

- ~~**Mikrofon** (dyktowanie) wysyła nagranie z imionami do Google~~ — załatwione 2026-09-17 („Mikrofon lokalny” niżej).
- ~~Brak zamka na apce~~ — załatwione w Szczeblu 5 („Zamek na apce” niżej).

## Nic nie wychodzi z laptopa (Faza 7)

Pytanie, od którego to się zaczęło: skoro dziennik chodzi w przeglądarce, czy dane
nie trafiają do Google? **Nie trafiają** — ale sama aplikacja łączyła się z Google
przy każdym otwarciu, po kroje pisma. Zmierzone 2026-09-14: 7 zapytań przy typowej
pracy, z czego **6 do `fonts.googleapis.com` / `fonts.gstatic.com`**. Żadne nie
niosło danych dzieci, ale Google widział IP i porę.

Kroje są teraz wklejone do pliku jako `data:` URI. Po zmianie: **0 zapytań poza
laptop**, a dziennik wygląda tak samo bez internetu (wcześniej bez sieci tracił
typografię). Koszt: plik urósł ze 126 KB do ~403 KB.

Dobór krojów zmierzony, nie zgadnięty — cztery warianty zapytania do Google:

| wariant | plików | w pliku |
|---|---|---|
| wagi wypisane pojedynczo (jak było) | 16 | 1251 KB |
| zakresy wag, Serif z osią `opsz` | 4 | 392 KB (**gubi IBM Plex Mono** — nie ma wersji variable) |
| **zakresy wag, Serif bez osi `opsz`** ← wybrane | 6 | **259 KB** |
| Serif tylko w wadze 600 | 6 | 189 KB (ryzyko: pozostałe wagi nagłówków syntetyzowane) |

Wzięte subsety: `latin` + `latin-ext` (polskie znaki). Cyrylica, greka i wietnamski
pominięte. Odświeżenie krojów (gdyby kiedyś trzeba): `py -3.14 narzedzia_osadz_fonty.py`.

Bramka: `py -3.14 test_siec.py` — przechwytuje **każde** zapytanie podczas typowej
pracy i wywala się, gdy którekolwiek wyjdzie poza `file://`. Odpalaj po każdej
zmianie, która dokłada bibliotekę, ikonę albo czcionkę.

### Co nadal wychodzi na zewnątrz — i kiedy

- **Mikrofon** (dyktowanie): od 2026-09-17 rozpoznawanie jest **lokalne** (Chrome 139+,
  pakiet pl-PL pobierany raz); gdy pakietu nie ma, mikrofon nie rusza. Sekcja „Mikrofon lokalny”.
- **Nic poza tym.** `localStorage` nie jest objęty synchronizacją konta Google
  (Chrome Sync obejmuje zakładki, historię, hasła, ustawienia, rozszerzenia — nie dane
  zapisane przez strony). Kopie lądują w `D:\Users\Downloads` — zwykłym folderze
  lokalnym, poza OneDrive i bez Google Drive for Desktop — i są zaszyfrowane.

## Pełna pamięć przeglądarki (Faza 8) — przyczyna „nie mogę dopisać klasy"

**Objaw zgłoszony 2026-09-14:** klikasz „+ klasa", wpisujesz nazwę, zatwierdzasz —
i nic. Klasy nie ma w pasku, nie ma komunikatu, po ponownym otwarciu nie ma jej też
w danych.

**Przyczyna:** pliki HTML otwierane **z dysku** (`file://`) dzielą w Chrome
**jeden wspólny magazyn** — wszystkie naraz, limit 10 MB łącznie, nie każdy osobno.
Zapełniły go inne projekty na tym komputerze (klucze `deckimg_PROMPTY_*`,
`ilumkom-v1:*` — patrz `strusie-kniewo/docs/KANON-dziennik-partii.md`, gdzie ten sam
mechanizm rozbroił dziennik partii 2026-09-04). Gdy magazyn jest pełny,
`localStorage.setItem` rzuca `QuotaExceededError` — a `save()` nie miał żadnej
obsługi błędu, więc wyjątek **przerywał operację w połowie**: klasa siadała w pamięci
strony, pasek się nie odświeżał, na dysk nie szło nic i nie było żadnego komunikatu.

To nie dotyczyło samych klas. **Tak samo cicho przepadał każdy status frekwencji,
każda ocena i każde nazwisko** — aplikacja wyglądała na sprawną.

**Lek — dwa magazyny zamiast jednego:**

- Zapis idzie do `localStorage` **i** do IndexedDB, który ma własny limit liczony
  z miejsca na dysku. Gdy pierwszy jest pełny, drugi pracuje dalej.
- Przy starcie wygrywa **nowszy** zapis (pole `savedAt`) — również wtedy, gdy
  w `localStorage` nie ma nic, bo ostatnie lekcje trafiły tylko do zapasowego.
- Do IndexedDB piszemy z sekundowym opóźnieniem (`save()` leci przy każdym znaku
  w nazwisku), ale `pagehide` domyka ostatni zapis przy zamykaniu karty.
- **Awaria jest głośna:** czerwony baner na górze mówi, co się dzieje. Gdy padną oba
  magazyny, baner żąda zrobienia kopii, zanim zamkniesz kartę.
- Próbny zapis **przy starcie** — dowiadujesz się o pełnej pamięci, zanim wpiszesz
  lekcję, a nie po tym, jak wpisy przepadną.
- Przycisk **„🔍 Co zajmuje pamięć?"** pokazuje wszystkie wpisy z rozmiarami
  i pozwala skasować cudze. Wpisów dziennika nie da się tam odznaczyć. Dziennik
  **nie kasuje cudzych danych sam** — decyzja należy do użytkownika.

Bramka: `py -3.14 test_pamiec.py` — 9 sprawdzeń. Zapycha magazyn do limitu
i sprawdza, że przy pełnej pamięci klasa się dodaje, jest widoczna, użytkownik
dostaje komunikat, a **klasa i wpis frekwencji przeżywają ponowne otwarcie**.
Na koniec zwalnia miejsce i sprawdza, że zapis wraca do `localStorage`, a baner znika.

## Zamek na apce (Szczebel 5, 2026-09-17) — hasło + PIN, magazyn szyfrowany

Skąd: research regulaminów (`research-notes/2026-09-17_regulamin-vulcan-automatyzacja.md`)
— realne ryzyko to nie skrypty do VULCAN, tylko **dane dzieci na laptopie**: kto miał
odblokowany komputer, otwierał dziennik i widział nazwiska.

Trzy warstwy, z których pierwsza jest tylko zasłoną, a sednem jest druga:

1. **Ekran blokady.** Przy otwarciu dziennika — hasło (klucz nie przeżywa
   przeładowania strony). Po 10 min bez klawisza/dotknięcia albo gdy karta zejdzie
   w tło — PIN (4 cyfry; klucz siedzi w pamięci strony). 5 złych PIN-ów → hasło.
   Przycisk „🔒 Zablokuj” w pasku zakładek zasłania od ręki. Klawisze i kliknięcia
   nie docierają do zasłoniętej apki (`inert` + przechwycenie `keydown`).
2. **Magazyn szyfrowany.** `localStorage` i IndexedDB trzymają WYŁĄCZNIE szyfrogram
   (AES-GCM 256, klucz z hasła PBKDF2 150 000 — te same prymitywy co kopie
   `.enc.json`). DevTools → Application → localStorage pokazuje `ct: "…"`, nie
   nazwiska. PBKDF2 liczy się raz przy odblokowaniu, AES przy każdym `save()`.
3. **Jedno hasło.** Hasło dziennika = hasło kopii. Nie leży już jawnie w
   `localStorage` (do 09-2026 leżało — świadomy kompromis z Fazy 6, który zamek
   unieważnił). Przycisk „🔑 Hasło kopii” (pokazywał hasło) → „🔑 Zmień hasło”
   (wymaga obecnego; magazyn przepisany nowym od razu; stare kopie otwiera stare
   hasło). **Zapomniane hasło = dane nie do odzyskania** poza kopiami — apka mówi to
   wprost na ekranie ustawiania.

Migracja: pierwsze uruchomienie po aktualizacji pokazuje ekran „Zamknij dziennik
hasłem” z podstawionym dotychczasowym hasłem kopii (ostatni raz, gdy apka je
pokazuje); klik szyfruje magazyn, kasuje jawne dane i jawne hasło. PIN — propozycja
raz po odblokowaniu, opcjonalny („🔢 PIN” w Uczniowie zmienia/usuwa). Hash PIN-u
leży W ŚRODKU szyfrogramu — na dysku nie przybywa nic jawnego.

Bramka: `py -3.14 test_zamek.py` — 35 sprawdzeń, kluczowe: **localStorage ani
IndexedDB nie zawierają nazwiska**, skróty klawiszowe nie przechodzą przez
zasłonę, migracja zachowuje wszystko i kasuje jawne hasło kopii, po przeładowaniu
PIN nie wystarcza. Pozostałe testy odblokowują apkę przez API
(`zamekPierwszeHaslo` / `zamekOdblokuj`) i czytają magazyn przez `zamekStanZapisany()`.

Czego zamek NIE robi: nie chroni przed kimś, kto zna hasło; nie chroni danych
w pamięci strony przy odblokowanej apce (DevTools) — chroni dysk i oko przypadkowego
przechodnia; mikrofon od 2026-09-17 rozpoznaje lokalnie („Mikrofon lokalny”).

## Układ: praca wysoko, ściągi na żądanie (2026-09-18)

Objaw (zrzut 1366×768 z klasą 20 uczniów): lista uczniów w Obecności zaczynała się na
~710 px, czyli po otwarciu apki nie było widać ani jednego nazwiska. Nad tabelą stały
tytuł, pasek klasy, „Szybki workflow” (na każdej zakładce, także w Ocenach i Pomiarach),
zakładki, data, baner zapisu, mikrofon, legenda, ściąga klawiszy — pomoc na pierwszy
tydzień wyświetlana przy każdej lekcji do końca roku (progressive disclosure: instrukcja
na żądanie, nie stale).

Zmiana: (1) tytuł + wybór klasy + zakładki w jednym **przyklejonym** pasku (`.topbar`,
zostaje przy przewijaniu, na telefonie bez podtytułu); (2) wszystkie ściągi per zakładka
zwinięte do jednej linii `❔ …` (`<details class="pomoc" data-pomoc=…>`): pierwsze
otwarcie rozwinięte, potem tak, jak zostawisz — stan w `localStorage` pod
`dziennik_wf_pomoc` (tylko 0/1 per zakładka, zero danych uczniów; test zamka dalej
zielony); (3) w Ocenach granica półrocza została jako akcja poza ściągą; (4) „Wyczyść
wszystko” zjechało z codziennego paska Uczniów do osobnego pola na dole zakładki;
(5) stempel „— zwolniony —” bez zawijania (na telefonie nachodził na kółko statusu).

Efekt: Obecność ze ściągą zwiniętą — tabela od ~350 px (9 uczniów widocznych od razu),
z rozwiniętą ~600 px. Bramka: `test_uklad.py` (progi 400/450 px, pamięć stanu, sticky,
miejsce „Wyczyść wszystko”). Ryzyko: przez pierwsze dni sięgasz do `❔` po klawisze.

## Nagłówek tabeli przyklejony (2026-09-18)

Objaw: przy 20+ uczniach po przewinięciu znikał wiersz z opisami kolumn i nie było
wiadomo, co oznacza liczba. Lek: `thead th { position: sticky; top: var(--topbar-h) }`
we wszystkich tabelach (Obecność, Uczniowie, Pomiary, Oceny, Statystyki); `--topbar-h`
ustawia JS z wysokości paska górnego (ResizeObserver), więc nagłówek klei się tuż pod
paskiem także po zawinięciu paska klasy.

Pułapka: element-opakowanie z `overflow` innym niż `visible` staje się kontenerem sticky
i nagłówek „klei się" do niego, nie do strony. Na laptopie (≥701 px) `.table-wrap` i
`.oceny-wrap` mają `overflow: visible` (tabele mieszczą się w 100%). Reguła musi mieć
wyższą specyficzność (`.container .oceny-wrap`), bo `.oceny-wrap { overflow-x: auto }`
stoi później w pliku i wygrywało — diagnoza: `getComputedStyle` + spacer po przodkach
z overflow ≠ visible. Na telefonie opakowanie przewija samo (`max-height: 100vh −
pasek`, `overflow: auto`) i nagłówek klei się do jego góry; przyklejone kolumny # i
Uczeń dostają wyższy z-index w nagłówku. Bramka: `test_uklad.py` (nagłówek Obecności po
przewinięciu ≤ 2 px pod paskiem, przy 40 wierszach).

## Zarys kolumn — gdzie wiersze wystarczą, a gdzie nie (2026-09-18)

Pytanie Artura: w których tabelach same linie poziome wystarczą, a gdzie trzeba zarysu
kolumn, żeby oko nie gubiło wartości. Diagnoza ze zrzutów 1366 px z klasą 20 uczniów:

- **Wystarczą wiersze** tam, gdzie komórka sama ma obrys: **Uczniowie** (pola dat,
  kratki, pola wzrost/waga) i **Oceny** (kolumny mają tło, ocena stoi w kafelku).
  Także małe tabele w karcie ucznia (2–4 kolumny).
- **Potrzebny zarys kolumn** tam, gdzie liczba stoi luzem w rzadkiej kolumnie:
  **Obecność** (8 kolumn liczników, większość komórek pusta — „1” w NĆ czy BS?),
  **Statystyki** (11 kolumn, obie tabele) i **Pomiary** (wynik bez obrysu, 150–200 px
  między kolumnami).

Rozwiązanie: klasa `kolumny` na tabeli → cienka pionowa linia (`var(--line-soft)`) po
lewej każdej kolumny liczb, w nagłówku ciemniejsza. Bez zebry: na telefonie przyklejone
kolumny # i Uczeń mają własne tło i pasy by się łamały. Hover wiersza zostaje.

## Mikrofon lokalny (2026-09-17)

Do tej pory rozpoznawanie mowy w Chrome było serwerowe: nagranie z nazwiskami dzieci
leciało do Google. Od Chrome 139 Web Speech API umie rozpoznawać na urządzeniu
(`processLocally = true`, pakiet językowy SODA jak w Live Caption). Sprawdzone u Artura
w konsoli: `available({langs:['pl-PL'], processLocally:true})` → `'downloadable'`,
`install()` → `true`, potem `'available'`.

Jak działa w dzienniku: przed startem mikrofonu `micLokalnieGotowy()` pyta Chrome o pakiet
pl-PL. Jest → start z `processLocally`. Do pobrania → pobiera (raz, kilkadziesiąt MB, toast)
i startuje. Nie ma / pobranie padło / stary Chrome bez `available()` → mikrofon **nie rusza**
i mówi dlaczego (fail-closed). Chrome bez tej bramki domyślnie spada do chmury po cichu
(udokumentowana pułapka: issues.chromium.org/521896368), dlatego bramka jest w kodzie,
nie w ustawieniu. Status przy nagrywaniu: „słucham (lokalnie, bez internetu)”.

Czego to NIE załatwia: Win+H (Windows) nadal wysyła do Microsoftu (Azure); Voice Access
działa lokalnie, ale nie ma polskiego. Dyktuj mikrofonikiem w dzienniku. Jakość
rozpoznawania lokalnego może być inna niż serwerowego — ocena po tygodniu na sali.
Bramka: `test_mikrofon_lokalny.py`, 5/5 PASS (atrapa Chrome w 5 stanach pakietu).

## Puste wiersze-widma (2026-09-17)

Objaw: usunięty pusty uczeń w 4b wracał. Przyczyna: Enter w ostatnim wierszu tabeli Uczniowie
dopisuje pustego ucznia (celowo, do wpisywania ciągiem), a porzucony wiersz zostawał na stałe.
Lek: wiersz bez nazwiska i bez żadnych danych (obecność, pomiar, ocena) znika przy wyjściu
z zakładki Uczniowie i przy otwarciu dziennika. Klasa bez żadnego nazwiska (świeży start)
zostaje nietknięta. Bramka: `test_puste_wiersze.py`.

## Zaległe lekcje — plan (siatka) + dni wolne vs wpisy (2026-09-18)

Chip w pasku górnym: **„⚠ Zaległe: N"** albo **„✓ Frekwencja na bieżąco"**. Zaległość =
lekcja z planu (dzień tygodnia + numer lekcji) przed dziś, dzień nie jest wolny, a klasa
nie ma wpisu frekwencji ani „nie było" pod tą lekcją. Klik chipu otwiera listę:
**wpisz** (przełącza klasę, datę i numer lekcji, wchodzisz w Obecność) albo **nie było**
z powodem (wycieczka / zawody / zastępstwo / odwołana) — pozycja znika na stałe, do
cofnięcia w Ustawieniach okna.

**Skąd plan — zakładka 🗓 Plan, siatka jest pierwsza.** Tabela klasa × Pn–Pt: klik
komórki otwiera numery lekcji 0–11, klik numeru wpisuje lekcję do planu (drugi klik
zdejmuje). Pierwszy klik zakłada plan „od 1 września" — daty ważności od/do są do zmiany
obok. **Inne zajęcia** (edukacja zdrowotna, wychowawcza, dyżur) dopisujesz w tej samej
zakładce: nazwa + „dodaj zajęcia" + numery w dniach; w pasku tygodnia są szare,
przerywane, bez kliku, bez frekwencji i bez Zaległych. Dni wolne: zakres od–do + „dodaj"
albo wklejony tekst kalendarium (łapie `RRRR-MM-DD` i `DD.MM.RRRR`, „od – do" w jednej
linii). Każdy nauczyciel wpisuje plan sam — to jest produkt, plik z EduPage to dodatek.
Okno „Zaległe" jest tylko listą braków; planu się w nim nie edytuje (feedback usera:
ustawienia schowane w alarmie były nieczytelne).

**Dyżury na przerwach — słupek, nie kafelek (2026-09-21).** Karta „Dyżury na przerwach"
w zakładce Plan: miejsce (`parter`, `szatnie`) × dzień → numery lekcji, po których masz
dyżur. Stały grafik tygodniowy, jak siatka lekcji. W Obecności dyżur wchodzi jako wąski
(26 px) kreskowany **słupek między kafelkami lekcji, z napisem pionowym** — miejscem
dyżuru; bez frekwencji, bez kliku. Dlaczego nie kafelek jak lekcja: przerwa nie ma numeru
lekcji, ona jest **pomiędzy** numerami — kafelek „L3" kłamałby o tym, czym jest, a numer
w danych oznacza lekcję, PO której przerwa wypada. W widoku Tydzień kafelki stoją jedna
pod drugą, więc tam ta sama rzecz jest cienką **belką poziomą** (pionowy napis miałby sens
tylko przy kafelkach obok siebie). Przy zawijaniu paska słupek jest sklejony z kafelkiem
po lewej (`.kol-para`), żeby nigdy nie został sam na początku wiersza i nie stracił sensu
„pomiędzy". Dzień wolny dyżuru nie pokazuje. Bramka: `py -3.14 test_dyzury.py`
(kolejność w pasku, szerokość i `writing-mode`, brak kliku w lekcję, sklejenie na 430 px,
widok Tydzień, dzień wolny, klikanie grafiku w zakładce Plan; zrzuty `_zrzuty/dyzury_*.png`).

Dodatek: `plan-roczny/plan-lekcji-RRRR-MM/zbuduj_plan_wf.py` → `plan-wf.json` (EduPage +
`technikum-recznie.json` + kalendarium ICS + święta ustawowe; format v2: klasa → dzień →
numery lekcji; `inne` = pozostałe moje lekcje jako EZ/GW). „Wczytaj plan" (zakładka Plan) o tym
samym `od` **dokłada do siatki**: klasy i inne zajęcia z pliku
nadpisują swoje wiersze, ręcznie wpisane inne klasy zostają, dni wolne się sumują. Inny
`od` (np. od 1.10) = nowy plan obok, stare miesiące liczą się po starym. Stary format pliku
(lista dni bez numerów) czyta się dalej: siatka pokazuje „?", zaległość liczy się per dzień.

Dopasowanie klasy dziennika do klasy w planie idzie po nazwie (`7 b` → `7b`,
`4d LO dz.` → `4dLO`); gdy nazwa nie pasuje (technikum), wybierz ręcznie w tabeli
zakładki Plan albo „— nie licz —"; dwie klasy na tej samej klasie planu dostają
czerwone ostrzeżenie (empiria: 5TS przypięte do 2 technikum). Klasa bez klucza dostaje przy pierwszym kliku w siatce
klucz = własna nazwa.

Dlaczego „nie było" jest obowiązkowe: plan nie wie o wycieczkach, zawodach i
zastępstwach, więc bez tej siatki chip mówiłby „zaległe" częściej niż jest
naprawdę i stałby się szumem. Dziś nie liczy się jako zaległe (trwająca praca).

### Pasek tygodnia — klikasz lekcję, nie wybierasz numeru

Pod datą w Obecności stoi tydzień z planu (Pn–Pt, wszystkie klasy): kafelek = lekcja
(`L3 · 2 inf`). Kolor: zielony ✓ wpis jest, czerwony ! dzień miniony bez wpisu, szary
przekreślony „nie było", ramka = lekcja otwarta teraz. **Klik kafelka przełącza klasę,
datę i lekcję** — dalej wpisujesz klawiaturą/myszą/głosem jak zawsze. Pasek widać tylko
z planem (siatka albo plik); bez planu obok daty jest zapasowy selektor „lekcja nr".

Pod spodem: wpis ma klucz `RRRR-MM-DD` (jedyna albo pierwsza lekcja dnia — wszystkie
stare wpisy, zero migracji) **albo** `RRRR-MM-DD#nr` (druga godzina tego dnia z tą samą
klasą). Numer nadaje kafelek, nie użytkownik. Wpis pod samą datą pokrywa pierwszą lekcję
dnia, wpis `#nr` dokładnie tę lekcję — dlatego dwie godziny z rzędu = dwa wpisy i dwie
pozycje w Zaległych. Statystyki, karta ucznia, CSV (kolumna `2026-09-18 L4`) i „Kopiuj
dla VULCAN" (dwa wklejenia, w VULCAN kolumny mają numer lekcji) liczą każdy klucz
osobno; półrocze, zwolnienia OD–DO i zakres karty patrzą na samą datę z klucza.

Bramka: `py -3.14 test_zalegle.py` (54 sprawdzeń: liczenie v1 i v2, pasek tygodnia, zakładka Plan, inne zajęcia, dwie lekcje jednego
dnia, klawiatura pod `#nr`, siatka, dni wolne, „nie było", „wpisz", magazyn, prawdziwy
`plan-wf.json`).

## Bramki: jedna komenda i zapadka przed pushem (2026-09-21)

`py -3.14 sprawdz_wszystko.py` uruchamia **wszystkie** bramki dziennika i drukuje tabelkę
plik → wynik → czas. 32 testy, **~75 s**, bo lecą równolegle. Fragment nazwy zawęża:
`py -3.14 sprawdz_wszystko.py -k dyzur`.

Dlaczego grupowanie, a nie zwykła równoległość: każdy test stawia własny serwer HTTP na
stałym porcie wpisanym w pliku, a kilka testów dzieli ten sam numer (8771 mają cztery,
8769 trzy). Na Windows `SO_REUSEADDR` pozwala drugiemu procesowi przejąć zajęty port — dwa
testy na tym samym porcie uruchomione naraz zaczęłyby sobie podawać cudze strony i sypać
losowo. Runner grupuje więc testy po porcie: w grupie po kolei, grupy równolegle. Alternatywą
było przenumerowanie portów w 33 plikach. `test_mikrofon_lokalny.py` jest jawnie **pomijany**
(wymaga mikrofonu i ręcznego kliku) — widać go w tabelce jako pominięty, nie jako zielony.

**Zapadka `pre-push`** (plik `pre-push` w korzeniu repo; instalacja raz po klonie:
`cp pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push`). Przed każdym pushem,
który rusza kod (`.html` / `.js` / `.py`), odpala cały zestaw; czerwona bramka = push
wstrzymany. Push samych `.md` idzie bez czekania. Cały zestaw, a nie wybrane testy, bo
dziennik to **jeden plik** `dziennik_wf.html` — każda zmiana dotyka go w całości, więc
mapowanie „zmieniony plik → te testy" nie istnieje. Sprawdzone w obie strony: przy zielonym
zestawie hook przepuszcza (exit 0), przy rozbitym CSS słupka dyżuru blokuje (exit 1).
Cofnięcie bramki = świadoma edycja testu z „dlaczego" w commicie, nie kasowanie hooka.

## Synchronizacja laptop ↔ telefon — scalanie kopii (2026-09-18)

Dane żyją osobno w każdej przeglądarce. Do teraz „Wczytaj szyfrowaną" **podmieniało** wszystko
plikiem — wpisy zrobione na drugim urządzeniu ginęły. Od dziś wczytanie kopii **scala**:

- brakujące wpisy dochodzą; ten sam wpis w obu miejscach różny → **wygrywa nowszy**; skasowany
  na jednym urządzeniu nie wraca ze starej kopii (nagrobek). Nic nie pyta — po scaleniu okno
  informacyjne „dołożono N, nadpisano K" z listą nadpisanych (klasa, lekcja, uczeń, było → jest).
- klasy parowane po `id` (nieznana z pliku dochodzi cała), uczniowie po `id`, plan przez upsert
  (jak wczytanie `plan-wf.json`). Stary tryb = checkbox **„Zastąp wszystko"** w tym samym oknie
  (przenosiny na czysto). Kopia obecnych danych zapisuje się przed operacją, jak dawniej.
- kopie sprzed dziś nie mają znaczników czasu → nic nie nadpisują, tylko dokładają brakujące
  („laptop jest prawdą" przy pierwszym scaleniu).

Pod spodem: `cls._t[ścieżka] = ms` obok danych (format komórek nietknięty). Znaczniki liczy
`save()` przez diff z poprzednim zapisem — jedno miejsce, nie 40 miejsc zapisu. Ścieżki:
`a|klucz|uczeń` frekwencja · `o|klucz` nie było · `g|kol|uczeń` ocena · `gc|kol` kolumna ·
`m|uczeń` pomiary · `s|uczeń` uczeń · `k` meta klasy.

**Rytm dnia (jedno kliknięcie na urządzenie):** laptop zapisuje kopię sam (auto raz dziennie
+ „Zapisz kopię"); na telefonie: Dysk Google → plik `.enc.json` → otwórz w dzienniku →
„Wczytaj szyfrowaną" → hasło → OK. Kierunek telefon → laptop: „Zapisz kopię" (plik w
Pobranych) → Udostępnij → Dysk (Android nie synchronizuje Pobranych sam — **nie testowane
u użytkownika**), na laptopie „Wczytaj szyfrowaną" z folderu Dysku.

**Dwa foldery kopii:** „📁 Kopie" (główny, dotychczasowy) i **„📁 Kopia 2"** — każda kopia
idzie do obu; drugi to np. folder Dysku Google na komputerze (wymaga aplikacji *Dysk Google na
komputer*; na tym laptopie 18.09 jej **nie było** — bez niej „Kopia 2" może wskazać dowolny
folder, ale do chmury nic samo nie pójdzie). Błąd drugiego folderu nie blokuje kopii (dymek).

**Czego nie ma:** automatu (Drive API w apce) — decyzja: dopiero gdy ręczny transfer po
tygodniu okaże się uciążliwy; Wi-Fi/serwer lokalny (szkolna sieć izoluje urządzenia).

Bramka: `py -3.14 test_scalanie.py` (30 sprawdzeń: znaczniki z diffu, nowszy wygrywa, remis =
lokalne, nagrobek, plan upsert, klasa nieznana, kopia bez znaczników, magazyn, „zastąp
wszystko", okno importu, dwa foldery). Regresja: `test_kopie`, `test_zamek`, `test_klawiatura`,
`test_zalegle`, `test_folder_kopii`.

## Widok dnia + belki C v2 + Reguły (2026-09-18/19)

Słowa usera: „plan chciałbym jako widok dzienny — godzina obok godziny, żeby lepiej było widać
uczniów i lekcje z obecnościami; belki tak pokazać, żeby było jasne, że tam się klika". Najpierw
mockup (`_zrzuty/mockup-widok-dzienny.html`, oko usera wybrało C, uwagi → C v2), potem żywa apka.

**Obecność = widok dnia (domyślny).** Lekcje dnia z planu stoją **obok siebie**: otwarta lekcja
to dotychczasowa tabela (jedyne miejsce wpisu — klawiatura, picker, dyktowanie bez zmian; `attRead/attWrite`
nietknięte), pozostałe to **podglądy** (nazwisko + status; klik nagłówka = `wybierzLekcje`, czyli otwiera
lekcję w tabeli — podgląd nie edytuje). Zajęcia bez frekwencji (`inne` z planu: EZ, GW) = wąska kreskowana
kolumna na swoim miejscu w dniu. Bez planu otwarta kolumna stoi sama (zero zmian dla klasy bez planu).
Przełącznik **Dzień / Tydzień** (`ustawWidok`, preferencja w `localStorage`, nie w danych); Tydzień =
dotychczasowy pasek Pn–Pt. W widoku dnia kolumny liczników (C/NĆ/BS/…) są schowane (są w Statystykach),
zostaje status + „% dotąd". Telefon: kolumny przewijane poziomo, otwarta przewinięta na ekran od razu;
`◀ dziś ▶` to jedna grupa `nowrap`.

**Belki.** Zakładki = karty zrośnięte z białym panelem treści (aktywna zlewa się z panelem). **W Obecności
nie ma paska klasy** — klasa wynika z otwartej lekcji; wybór szkoły/klasy, „+ klasa", zmiana nazwy, usuń,
forma (chł./dz.) mieszkają w **Uczniowie** (`#classBar`). Pomiary/Oceny/Statystyki mają tytuł klasy z ▾
(`.klasa-tytul`, ten sam `onClassChange`).

**Stopka otwartej kolumny** (`#saveBar`): „✓ Zapisz lekcję" (reszta bez statusu → ćwiczył/ćwiczyła; Enter
jak dotąd) + „📋 do VULCANa / do Librusa" (`copyForVulcan(clsId?, klucz?)` — bez argumentów bieżąca lekcja,
z argumentami lekcja z podglądu; tekst schowka ten sam dla obu e-dzienników). Po zapisie: „Zapisano HH:MM"
(pamięć sesji `_zapisanoO`, nie dane). Etykieta z ustawienia szkoły: `edziennikSzkoly(szkoła)` —
ręczne (`state.ustawienia.szkoly[szkoła].edziennik`, pytanie w modalu „+ klasa" i w Reguły) albo domyślne
po nazwie (zawiera „tech" → Librus, reszta VULCAN). Skrypt wklejania istnieje tylko dla VULCANa.

**Forma ćwiczył/ćwiczyła** — `cls.plec` (`''|'chl'|'dz'`), klasy ZSS jednorodne płciowo → ustawienie per
klasa, tylko etykiety (`cwLabel`), nie liczenie. Nagłówek kolumny pokazuje „dz."/„chł.".

**Zakładka Reguły** cytuje PZO (`D:/Projects/nauczyciel/wf/pzo/README.md` — źródło reguły, która siedziała
w kodzie od maja) i daje manipulatory `state.ustawienia.reguly` (`bsBaza`, `ncBaza`, `spPol`, `nuBaza`,
`progZielony`, `progCzerwony`); **domyślne = dotychczasowe liczenie** (`REGULY_DOMYSLNE`). Jedno miejsce
liczenia: `getStudentStatsZ` (progi: `pctKlasa`). Ustawienia jedzą do magazynu, migawki i kopii obok `planWf`;
scalanie kopii: szkoły dopisują się, gdy lokalnie brak, reguły z kopii tylko gdy lokalnie nic nie ustawiono.

**Systematyczność = 4 okna** (decyzja 18.09, dwie oceny na półrocze): `oknaSystematycznosci(cls)` →
`Syst. I.1 / I.2 / II.1 / II.2` (`auto_sys11…22`). Granica półrocza jak dotąd (`semesterBreak`), środki
półroczy liczone same (`oknaGranice`: połowa 1.09→granica i granica→30.06) albo ręcznie `cls.polI` / `cls.polII`
(Reguły). Bez granicy: jedno okno (`auto_sys0`), jak dotąd. Meta klasy w listkach scalania (`k`) niesie
`polI`, `polII`, `plec`.

Test: `test_widok_dzienny.py` (kolumny, klik nagłówka, przełącznik, inne, stopka, forma, reguły, okna,
390 px; zrzuty `_zrzuty/cv2_*.png`). Regresja dopasowana: `test_zalegle` (pasek tygodnia = widok Tydzień),
`test_pamiec` (pasek klasy w Uczniowie), `test_vulcan_kopiuj` / `test_zwolnienie_od_do` (`#saveBarKopiuj`).
Otwarte: SLO punkty (max 20/okno) vs procent — decyzja usera; bookmarklet Librus — osobny szczebel.

**Kafelek „nie było” przy 9 lekcjach (2026-09-19, sw v30).** Przy pełnym dniu kafelek ma ~124 px; „nie było:
wycieczka · Kraków, 3 dni” + „jednak była” łamały się na 3–4 linie (145 px obok 83 px sąsiadów — zestaw
tracił rytm). Teraz kafelek zamknięty pokazuje **sam powód** (segment przed ` · `) w jednej linii z
wielokropkiem i kreską w przycisku, „jednak była” zawsze w drugiej — wysokość stała (104 px), niezależna
od komentarza; pełna treść w dymku i w kafelku otwartym. Test: `test_niebylo_9lekcji.py`
(wsad 9 lekcji, 5 × „nie było”, wszystkie kafelki równe i ≤ 110 px; zrzut `_zrzuty/niebylo_9lekcji_po.png`).

**Dryf daty w testach (2026-09-19).** `test_zalegle.py` (lista modalu liczy „dziś” z `new Date()`) i
`test_uklad.py` (widok Dzień w weekend bez lekcji chowa tabelę → `rect 0`) padały zależnie od dnia
uruchomienia. Fix: `page.clock.set_fixed_time('2026-09-18T10:00:00')` przed `goto` — nowy test z datą
w fixture ma mrozić zegar tak samo.

## Uwaga operacyjna: jedno miejsce uruchamiania

Dane siedzą w `localStorage`, który jest **osobny dla pliku na dysku i dla adresu
https://**. Otwierany raz stąd, raz stamtąd dziennik pokaże dwa różne komplety danych.
Wybierz jedno miejsce i trzymaj się go przez cały rok; przenosiny = eksport JSON
z jednego, import w drugim.

## Status

Adoptowany do projektu `nauczyciel` 2026-05-18 (był prototypem w Downloads).

- Faza 1 (gotowe, zweryfikowane): kompletny backup z ocenami + auto-backup raz
  dziennie przy zapisie lekcji + backup przed operacją niszczącą.
- Faza 2 (gotowe): model szkoła→klasa (zespół szkół, wiele klas), migracja
  starych danych bez utraty, pasek wyboru szkoły/klasy.
- Faza 3 (wdrożone): hosting HTTPS na GitHub Pages
  (https://arturzienczyk.github.io/dziennik-wf/dziennik_wf.html) + PWA
  (manifest + service worker, działa offline, instalacja na Androidzie) +
  szyfrowana kopia (AES-GCM + hasło) — dane dzieci mailem dopiero zaszyfrowane,
  zgodnie z zakazem CLAUDE.md. Repo publiczne, ale `backups/` i kopie danych
  poza git (dwie warstwy `.gitignore`).
  Niezweryfikowane na żywo: instalacja PWA na fizycznym Androidzie + szyfrowana
  kopia w UI przeglądarki (rdzeń krypto przetestowany, integracja UI nie).
- Faza 4 (wdrożone): runda zmian dydaktycznych —
  - Widełki %→ocena 1-6 MEN (96-100→6, 90-95→5, 75-89→4, 53-74→3, 41-52→2,
    20-40→1; <20% liczone jak 20%; 0 = niezaliczony, waga 0). W tabeli ocen,
    średniej, CSV.
  - Responsywność: sticky kolumny #/Uczeń na telefonie (koniec poziomego
    scrolla treści), desktop bez zmian.
  - Spóźnienie: znacznik ⏱ doklejany do dowolnego statusu (attRead/attWrite,
    stare backupy czytane bez migracji). Nie wpływa na %.
  - Systematyczność: 2 auto-kolumny (Syst. I/II) liczone z % ćwiczenia w
    oknie półrocza wg widełek; pole „Granica półrocza" per klasa; reset
    licznika na dacie granicznej; auto-kolumny read-only.
  Niezweryfikowane na żywo: render/klikanie w przeglądarce (logika
  przetestowana w Node — progi, okna półrocza, round-trip spóźnienia).
  → **Domknięte przy Fazie 5**: `test_klawiatura.py` przeszedł w prawdziwym
  Chromium — auto-kolumna Syst. renderuje się i jest chroniona przed ręcznym
  wpisem, widełki %→ocena pokazują się w tabeli, spóźnienie robi round-trip
  przez UI. Otwarte zostają tylko założenia (waga=1, kolumny na początku).
  Założenia do ew. korekty: waga systematyczności=1, kolumny na początku.
- Faza 5 (wdrożona, przetestowana e2e): wprowadzanie danych z klawiatury —
  litery/cyfry nadają status frekwencji z auto-zejściem kursora, oceny i pomiary
  edytowane wprost w komórce (`Enter` w dół), dopisywanie uczniów ciągiem,
  `Enter`/`Esc` w oknach dialogowych, panele dyktowania zwinięte (tabela wyżej
  na ekranie). Bramka: `test_klawiatura.py`, 22/22 PASS, render obejrzany.
  Szczegóły niżej: „Wprowadzanie danych z klawiatury".
- Faza 6 (wdrożona, przetestowana e2e): wymuszone szyfrowanie kopii — auto-kopia
  dzienna, kopia przed operacją niszczącą i kopia ręczna idą jedną drogą przez
  AES-GCM z hasłem ustawianym raz; operacja kasująca nie rusza danych, gdy kopia
  nie powstała. Bramka: `test_kopie.py`. Zostaje otwarte: mikrofon
  (nagranie do Google); zamek na aplikacji → Szczebel 5.
- Faza 7 (wdrożona, zmierzona): kroje pisma wklejone do pliku — dziennik nie wykonuje
  żadnego zapytania poza laptop (było 6 do Google po czcionki przy każdym otwarciu)
  i wygląda tak samo bez internetu. Bramka: `test_siec.py`. Otwarte zostaje: mikrofon
  (rozpoznawanie mowy po stronie Google); zamek na aplikacji → Szczebel 5.
- Faza 8 (wdrożona, odtworzona kontrolą): drugi magazyn (IndexedDB) + głośny baner
  + podgląd zajętości pamięci. Powód: wspólny limit `file://` był pełny, `save()`
  nie miał obsługi błędu i każdy zapis cicho przepadał — objaw „nie mogę dopisać
  klasy". Bramka: `test_pamiec.py`, 9/9 PASS.
- Szczebel 5 (wdrożony 2026-09-17): zamek — ekran blokady (hasło / PIN 4 cyfry / 10 min
  bezczynności / karta w tle) + magazyn przeglądarki wyłącznie jako szyfrogram + jedno
  hasło dla dziennika i kopii (bez podglądu, ze zmianą). Bramka: `test_zamek.py`, 35/35.
