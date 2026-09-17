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
| `1`–`6` | to samo, w kolejności legendy |
| `s` | dokleja spóźnienie do statusu, który już jest |
| `0` | czyści status |
| `Enter` | zapisuje lekcję (drugi `Enter` potwierdza okno) |

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

- **Mikrofon** (dyktowanie) wysyła nagranie z imionami do Google — to osobna decyzja.
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

- **Mikrofon** (dyktowanie): rozpoznawanie mowy w Chrome jest **serwerowe** — nagranie
  z imionami dzieci trafia na serwery Google. Dopóki nie klikniesz mikrofonu, nic się
  nie dzieje; ale to nie jest funkcja lokalna, mimo że tak wygląda.
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
przechodnia; mikrofon nadal wysyła nagranie do Google (osobna decyzja).

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
