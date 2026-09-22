# HANDOFF — „Jedna droga kopii" (2026-09-22)

> **Po polsku:** Zadanie na następną sesję: schować cały transfer kopii do wnętrza aplikacji
> i zostawić JEDNĄ zrozumiałą drogę zamiast ośmiu przycisków. Po co: dziś zakładka Uczniowie
> wygląda jak Librus — pasek enigmatycznych kafelków, przy których nauczyciel nie wie, w który
> kliknąć. Artur (2026-09-22): „gdy otwierasz a tam kafelki, które są dla ciebie enigmą, to
> bardzo odpycha — ma to aplikacja Librusa, która nazywa rzeczy tak, że nie rozumiem po co".
>
> Ten handoff ma jedną nazwę i cztery punkty. Gdy Artur mówi „zrób handoff jedna droga kopii",
> chodzi o całość; punkty są kolejnością, nie osobnymi zadaniami.

## Stan zastany (zmierzony 2026-09-22, nie z pamięci)

Pasek `.toolbar` w `#tab-uczniowie` (`dziennik_wf.html` ~1424): **11 przycisków**, z tego
**8 wokół kopii i haseł**:

| przycisk | co robi | problem nazwy |
|---|---|---|
| 🔒 Zapisz kopię (szyfrowana) | `exportEncrypted()` | „(szyfrowana)” — a jest jakaś inna? |
| 🔓 Wczytaj szyfrowaną | okno wyboru pliku | para do powyższego, ale inna droga niż niżej |
| 📂 Kopie w folderze | `pokazKopieZFolderu()` | **druga droga do tego samego** co „Wczytaj szyfrowaną” |
| 📁 Kopie: Pobrane | wybór folderu | nauczyciel nie wie, po co ma wybierać folder |
| 📁 Kopia 2: brak | drugi folder | „Kopia 2” nie znaczy nic bez historii projektu |
| 📂 Wczytaj stary JSON | import sprzed IX.2026 | **„JSON” to słowo z innego świata** |
| 🔑 Zmień hasło | hasło dziennika i kopii | OK |
| 🔢 PIN | szybkie odblokowanie | OK |

Do tego `🔒 Zapisz kopię teraz` w banerze awaryjnym (~1288) — dziewiąte wejście w to samo.

**Sedno:** do wczytania kopii prowadzą DWIE drogi (plik z okna systemowego / lista z folderu),
do zapisania DWIE (toolbar / baner), a dwa przyciski folderów są konfiguracją, nie czynnością.

## 1. Przycisk „Wyślij kopię” — zmierzone, że da się

`navigator.share({files})` **działa w Chrome na tym laptopie** — sprawdzone 2026-09-22:
`canShare({files}) === true` w kanale `chrome` (headless Chromium go nie ma, więc probe
uruchamiać z `channel="chrome"`). Na Androidzie to standardowa ścieżka PWA.

Dzięki temu wysyłka kopii wchodzi DO aplikacji: jeden przycisk → systemowe okno udostępniania
(Gmail, Dysk, WhatsApp) → koniec. Znika najgorszy krok dla kogoś z zewnątrz: „zapisz plik,
znajdź go w Pobranych, załącz do maila”.

Fallback obowiązkowy: brak `navigator.canShare` → zachowanie dzisiejsze (zapis do folderu kopii)
+ dymek mówiący, co się stało. Bez fallbacku przycisk milczy na starszej przeglądarce.

## 2. Redukcja do jednej drogi — propozycja do oceny Artura (nie wdrażać bez „pasuje”)

Zamiast ośmiu przycisków **jeden**: `📦 Kopia zapasowa` — otwiera okno z trzema czynnościami
nazwanymi czasownikiem i po ludzku:

- **„Wyślij kopię na telefon”** (punkt 1; na telefonie ten sam przycisk mówi „Wyślij kopię na laptop”)
- **„Wczytaj kopię”** — JEDNA lista: kopie z folderu + `📂 Wybierz plik ręcznie` jako link na dole.
  Dwie dzisiejsze drogi łączą się w jedną z furtką, nie znikają.
- **„Ustawienia kopii”** — zwinięte: folder, drugi folder, hasło, PIN, stary import.
  Konfiguracja przestaje udawać czynność.

Zasada nazewnicza (to jest właściwy produkt tej sesji, nie sam przycisk): **nazwa mówi, co się
stanie dla użytkownika, nie jak to działa w środku.** „Wczytaj stary JSON” → „Wczytaj kopię
sprzed września 2026”. „Kopia 2” → „Zapasowy folder”. Żadnego słowa, którego nauczyciel nie
użyłby sam.

## 3. Czego NIE ruszać

- **Szyfrowania i hasła** — AES-GCM + PBKDF2 zostaje bez zmian; to jest powód, dla którego kopie
  wolno wysyłać mailem. Upraszczamy nazwy i drogi, nie bezpieczeństwo.
- **Scalania przy wczytaniu** — „Zastąp wszystko” został usunięty 2026-09-19 świadomie.
- **Skryptów `kopia` / `kopia --na-telefon`** — zostają dla Artura jako automat codzienny. Dla
  kogoś z zewnątrz aplikacja ma wystarczać BEZ nich (patrz punkt 4).

## 4. Komunikat dla kogoś z zewnątrz (ustalone 2026-09-22)

Aplikacja **nie wymaga Pythona ani niczego poza przeglądarką** — to jeden plik HTML. Python jest
potrzebny wyłącznie do skrótów Artura na pulpicie, a realną barierą w nich nie jest Python, tylko
**hasło aplikacji Gmaila w zmiennej środowiskowej** (każdy musiałby wygenerować własne). Dlatego
kolegi nie trzeba o niczym uprzedzać — dostaje plik, otwiera, działa. Po punkcie 1 wysyłka kopii
też przestaje wymagać czegokolwiek spoza apki.

## Bramki przed „zrobione”

- `py -3.14 sprawdz_wszystko.py` — 35 bramek zielonych (pre-push i tak je odpali).
- `test_audyt_ux.py` — po przebudowie paska przejrzeć jego findingi, to jest bramka od tego.
- **Render + oko**: zrzut zakładki Uczniowie na 1400 px i 390 px, obejrzany przed pokazaniem.
- **`CACHE_VERSION` w `sw.js`** — podbić (teraz v41), inaczej telefon serwuje starą wersję.
- Klik zapadki należy do Artura: „jedna droga” uznajemy za zrobioną, gdy on otworzy apkę i nie
  zawaha się, w co kliknąć.

## Resume

„Robimy handoff »jedna droga kopii« z `D:\Projects\nauczyciel\wf\dziennik-wf\HANDOFF-jedna-droga-kopii.md`.
Zacznij od punktu 1 (przycisk Wyślij kopię), potem pokaż propozycję z punktu 2 do oceny, zanim
cokolwiek przebudujesz.”
