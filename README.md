# Dziennik WF

Single-file aplikacja (HTML+JS, bez instalacji, offline) do prowadzenia frekwencji,
pomiarów sprawności i ocen na WF. Dyktowanie głosem na sali (mikrofon / Win+H).

## Uruchomienie

Otwórz `dziennik_wf.html` w przeglądarce (dwuklik). Działa lokalnie, nic nie wychodzi
na żaden serwer.

## Dane i backup

- Dane żyją w `localStorage` przeglądarki — **per przeglądarka, per komputer**.
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

Bramka: `py -3.14 test_kopie.py` — 13 sprawdzeń, kluczowe: **pobrany plik nie zawiera
nazwiska dziecka**, zła fraza go nie otwiera, własne hasło odtwarza dane w całości.

### Czego to NIE załatwia

- **Mikrofon** (dyktowanie) wysyła nagranie z imionami do Google — to osobna decyzja.
- **Brak zamka na apce**: kto ma odblokowany laptop, otwiera dziennik i widzi dane.

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
  nie powstała. Bramka: `test_kopie.py`, 13/13 PASS. Zostaje otwarte: mikrofon
  (nagranie do Google) i brak zamka na samej aplikacji.
