# HANDOFF — blok „Kopia dziennika" w dwóch krokach (2026-09-22 noc)

> **Po polsku:** zgłoszenie Artura o enigmatycznych przyciskach kopii i JEGO decyzje (widżet 22.09),
> żeby następna sesja nie zgadywała. Poniżej rozdzielone: co powiedział/wybrał Artur, co jest stanem kodu.

## Zgłoszenie Artura (22.09, słowa)
> „wyślij kopię, to do końca nie wiadomo, jaką kopię i czego i gdzie się tworzy, kopia zapasowa, czym jest
> kopia zapasowa, po co mi kopia zapasowa, uproszczenie spowodowało, że się to stało enigmatyczne"

> „ręczna kopia jest potrzebna, bo wtedy robię kopię kiedy mi jest wygodnie" · „na lekcję idę z telefonem"
> · „pierwszym krokiem jest [kopia — automat lub ręczna, najświeższa, i to widać], drugi wyślij na telefon"

Fakty od Artura: kopię robi **codziennie**; wysyłka i wczytanie **Android ↔ laptop działa** (sprawdzone
przez niego 21–22.09, pocztą) — to już NIE jest „niezweryfikowane".

## Decyzje Artura (widżet 22.09) — to są JEGO wybory
1. **Układ bloku = „Pasuje":**
   ```
   KOPIA DZIENNIKA
    Najnowsza: dziś 14:32 · automatyczna
    [💾 Zrób kopię dziennika teraz]
    [📤 Wyślij kopię dziennika na telefon]   ← robi świeżą kopię w chwili kliknięcia
      zrobi się świeża, ze wszystkim co jest teraz
    [📂 Wczytaj kopię dziennika z telefonu]
    Kopia robi się też sama raz dziennie · ⚙ hasło, PIN, foldery kopii
   ```
   Na telefonie kierunek odwrócony („na laptop" / „z laptopa").
2. **Skróty z pulpitu:** „Kopia dziennika na telefon.cmd" **znika** (wysyłka jest w apce);
   „Kopie dziennika z maila.cmd" **zostaje** (pobranie z Gmaila w apce = OAuth Google, poza zakresem).
   Kasować skrót dopiero PO wdrożeniu bloku do dziennika.
3. Makieta w **piaskownicy** (`zrob_piaskownice.py` z `dziennik_wf_roboczy.html`), nie w osobnym pliku.

## Stan kodu (nie decyzja — do sprawdzenia)
- `dziennik_wf_roboczy.html` odświeżony z prod 22.09 (stary z 20.09 w `_wersje-poprzednie/`); ma już
  pośrednią makietę: `pasekKopii()`, `pasekWczytaj()`, `otworzKopieModal(tryb)` ('wczytaj'|'ustawienia'),
  `#kopiaStan`. Do przerobienia na blok z pkt 1 — brakuje zapisu czasu i rodzaju najnowszej kopii.
- Przy wdrożeniu świadomie zmienić zapadkę `test_wyslij_kopie.py:79-97` (dziś wymaga nazw „📤 Wyślij kopię"
  / „📦 Kopia zapasowa") + README §„Jedna droga kopii". `CACHE_VERSION` teraz v44.

## Stan 22.09 ~22:00
- Blok z pkt 1 zbudowany w roboczym (`#kopiaBlok`, `ostatniaKopiaZapisz/Opis`, klucz `dziennik_wf_ostatnia_kopia`), piaskownica odświeżona, render 1400/390 obejrzany, zero błędów JS. **Czeka na klik Artura w piaskownicy**, potem: `wdroz_roboczy.py --wdroz`, zapadka testu + README, v45, push, skasować skrót „Kopia dziennika na telefon.cmd".
