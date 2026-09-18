# HANDOFF — plan: widok dzienny (godziny obok siebie) + belki, które zapraszają do kliknięcia

**Data:** 2026-09-18 wieczór. Dla: czysta sesja w `D:\Projects\nauczyciel\wf\dziennik-wf` (osobne repo,
`git push origin main`, GitHub Pages, **`sw.js` CACHE_VERSION v11 — podbij przy każdej zmianie html**).
**Słowa usera (18.09, po wdrożeniu scalania kopii + Drive):**

> plan chciałbym jako widok tygodniowy i dzienny, ale pierwszy wybór to ten dzienny — ale nie żeby był
> godzina za godziną, ale raczej godzina obok godziny, żeby lepiej było widać uczniów i lekcje z obecnościami.
> Ta belka z uczniami, planem, statystyką tak pokazać, żeby było jasne, że tam się klika. Belka ze szkołą,
> klasą też tak zrobić, żeby bardziej rzucało się w oczy. Zbadać, jak to zrobić w sposób smaczny, nie krzykliwy.

## Stan wyjściowy (zweryfikowany 18.09)
- Zakładka **Obecność**: pod datą **pasek tygodnia** `#planTydzien` (Pn–Pt, kafelki `L3 · 2 inf`, klik =
  klasa+data+lekcja; README §„Pasek tygodnia"). Renderuje `renderAttendance` → część planu; kafelki
  `.plan-lekcja` (zielony ✓ wpis / czerwony ! brak / szary inne / ramka = otwarta).
- Zakładka **Plan** (`#planUstawienia`, `renderZalegle`): siatka per klasa Pn–Pt × nr lekcji, dni wolne, inne.
- Belka zakładek: `.tab` (Obecność, Uczniowie, Pomiary, Oceny, Statystyki, Plan, Zablokuj) — dziś tekst
  z ikoną, podkreślenie aktywnej; belka nagłówka: `Szkoła: <select>` `Klasa: <select>` + `+ klasa`,
  `zmień nazwę`, przyciski zamka — dziś jak zwykłe kontrolki formularza.
- Klucz wpisu `data` / `data#nr` (nie ruszać); plan v2 `klasy[k][dzień] = [nry]`.
- Testy: `test_zalegle.py` (54, pasek tygodnia i siatka), `test_klawiatura.py` (22, klawiatura — **widok
  dzienny nie może jej zepsuć**), `test_uklad.py`, `test_scalanie.py` (31).

## KOLEJNOŚĆ (decyzja usera 18.09): NAJPIERW MOCKUP, NIE ŻYWA APKA
User: „może nie rób od razu na żywej aplikacji, ale mockup, bo nie jestem pewien, jak to będzie wyglądać".
- Krok 0: **osobny plik** `mockup-widok-dzienny.html` (statyczny HTML z danymi na sztywno: 1 dzień, 2–3
  lekcje obok siebie, kilkunastu uczniów fikcyjnych, oba warianty belek) — CSS skopiowany z `dziennik_wf.html`
  (ta sama paleta, fonty), żeby wyglądał jak apka. **2–3 warianty** belek i układu kolumn obok siebie
  na jednej stronie (A/B/C), z podpisem, co się różni. Render 1400 + 390 px → PNG → `pulpit --sesja`
  (albo SendUserFile) → **oko usera wybiera**. Dopiero po „pasuje" punkty 1–5 na żywej apce.
- Mockup nie jest produktem: po wdrożeniu do usunięcia albo `_zrzuty/` jako ślad decyzji.

## Co zbudować (po zatwierdzeniu mockupu)
1. **Widok dzienny jako domyślny** w Obecności: lekcje dnia **obok siebie** (kolumny), nie jedna pod drugą.
   Każda kolumna = lekcja (`L3 · 2 inf`) z listą uczniów i ich statusami — user chce z jednego ekranu widzieć
   uczniów i obecności kilku lekcji tego dnia. Przełącznik **Dzień / Tydzień** (tydzień = obecny pasek).
   Do rozstrzygnięcia z userem (jedno pytanie, nie widżet — decyzja z jego rytmu, opis przepływu):
   czy kolumna jest **edytowalna** (klik statusu w kolumnie zapisuje) czy **podgląd** + klik nagłówka
   otwiera lekcję w dotychczasowej tabeli. Propozycja: podgląd + klik nagłówka (klawiatura i tabela
   zostają jedynym miejscem wpisu — 40+ miejsc `attRead/attWrite` bez zmian).
   Telefon: kolumny przewijane poziomo (`overflow-x:auto`), min. szerokość kolumny ~220px.
2. **Belka zakładek** i **belka szkoła/klasa**: afordancja „tu się klika" — smaczna, nie krzykliwa.
   Kierunki do zbadania (render + oko usera, nie deklaracja): zakładki jako segmented control /
   pigułki z lekkim tłem i cieniem; aktywna z wypełnieniem, nie tylko podkreśleniem; selecty szkoła/klasa
   jako wyraźne „chipy" z chevronem, nazwa klasy większa (to główny kontekst pracy). Paleta obecna
   (`--ink`, `--paper`, `--line`, zieleń #1D9E75) — nie wprowadzać nowych kolorów.
3. **Zanim narysujesz:** `kanon "afordancja klikalności belka zakładek"` + `design/canon/` (visual
   render-invariant-ratchet, mechanizm-przed-pozorem). Render headless (`shot.py` z `design/tools`) na
   1400 i 390 px, **obejrzeć PNG**, zrzuty do `_zrzuty/`; ocena = oko usera.
4. Test `test_widok_dzienny.py` (wzór `test_zalegle.py`): dzień z 2 lekcjami → 2 kolumny, klik nagłówka
   przełącza lekcję, przełącznik Dzień/Tydzień, wąski viewport = przewijanie poziome; regresja pełna.
5. README sekcja + sw v12 + push + memory.

## Nie robić
- Nie zmieniać formatu wpisów ani klucza `data#nr`; nie dublować logiki statusów (jedno `attRead/attWrite`).
- Nie robić nowej palety / nowych fontów. Nie „upiększać" reszty ekranu przy okazji.

## Otwarte u usera (przeniesione)
- Telefon: wczytać najnowszą kopię z Drive (od 18.09 kopia niesie plan) — sprawdzić, czy plan doszedł.
- 5TS → „5 technikum" w zakładce Plan; nowy `plan-wf.json` (z `inne`) wczytany?
- Po tygodniu: czy ręczny transfer telefon → laptop męczy (wtedy Drive API, osobna decyzja).

## Decyzja oka usera (18.09, 22:30) — baza = wariant C, mockup C v2
User wybrał **C** („od razu pokazuje, co należy kliknąć"). Uwagi wniesione do `mockup-widok-dzienny.html` sekcja „C v2"
(zrzuty `_zrzuty/mockup_c2_1400.png`, `_zrzuty/mockup_c2_390.png`):
1. Widok dnia → belka szkoła/klasa staje się ozdobnikiem: klasa wynika z otwartej lekcji. Tytuł klasy bez „zmień";
   w Obecności tylko pokazuje, w pozostałych zakładkach (Uczniowie/Oceny/…) ten sam tytuł z ▾ wybiera klasę.
2. „Zapisz lekcję — pozostali bez statusu jako ćwiczył" w stopce otwartej kolumny (zielony pasek jak save-bar).
3. Forma żeńska „ćwiczyła" — klasy ZSS są jednorodne płciowo → ustawienie per klasa (dz./chł.), nie per uczeń;
   dzienniki elektroniczne tego nie mają, u nas tylko etykiety (stopka, podsumowanie, legenda).
4. Lekcje bez frekwencji (EZ/GW, `inne` z planu): wąska szara kolumna z kreskowanym obrysem na swoim miejscu w dniu.
Otwarte: klik nagłówka kolumny = otwiera lekcję w tabeli (podgląd, nie edycja w kolumnie) — user nie zaprzeczył.
Doprecyzowanie (22:45): w Obecności NIE ma belki klasy w ogóle (także na telefonie) — wybór klasy/szkoły, „+ klasa",
zmiana nazwy przenoszą się do zakładki Uczniowie. Na telefonie ◀ dziś ▶ = jedna grupa `nowrap`, nic nie przeskakuje
do drugiego wiersza (data w osobnym wierszu jest OK).
Uwaga 5 (22:55) — „Kopiuj dla VULCAN" jest bardzo ważne, nie może być schowane w date-row. Decyzja: w stopce KAŻDEJ
kolumny dnia obok „Zapisz lekcję" — jeden przycisk `copyForVulcan()` (tekst Nazwisko Imię + status jest agnostyczny),
etykieta ze szkoły klasy: technikum → „📋 do Librusa", SP/LO (ZSS) → „📋 do VULCANa". Po zapisie stopka zostaje
(„zapisano 9:52 · do VULCANa"). Mapowanie szkoła → e-dziennik = ustawienie per szkoła (domyślnie: nazwa zawiera
„tech" → Librus, reszta VULCAN). Skrypt po stronie Librusa NIE istnieje — osobny szczebel (bookmarklet jak VULCAN);
sam schowek działa już dziś dla obu.
Uwagi 6-8 (23:10): (6) e-dziennik = pytanie przy dodawaniu szkoły (VULCAN/Librus), widoczne też w Reguły → „Szkoły
i e-dziennik". (7) Frekwencja dotychczasowa: szary % przy uczniu w otwartej kolumnie (+ % klasy w nagłówku), liczony
jak getStudentStats. (8) Zakładka „Reguły": opis liczenia + manipulatory (bs/nć w bazie, spóźnienie, nu w bazie,
progi 90/75, granica półrocza) — domyślne = dzisiejsze zachowanie. USER: „one [reguły] są opisane w e-dzienniku" —
treść Reguł ma odzwierciedlać zasady VULCAN/Librus, nie własną formułę; manipulatory służą do ZRÓWNANIA liczenia
z e-dziennikiem. Potrzebny od usera: tekst/zrzut reguł z VULCANa i Librusa (albo link do pomocy).
ROZSTRZYGNIĘTE (23:20): reguła liczenia w kodzie (getStudentStats: NU i ZW poza bazą) = PZO ZSS obszar
„Systematyczność". Dokumenty leżały w Downloads, teraz D:/Projects/nauczyciel/wf/pzo/ (SSP + SLO + README z
wyciągiem i 3 rozjazdami: okno 2 mies. vs półrocze, SLO punkty vs %, nć/bs jako interpretacja). Zakładka Reguły
cytuje PZO, nie własną formułę.
DECYZJA (23:30): Systematyczność = 2 oceny na półrocze (4 okna w roku: I.1 I.2 II.1 II.2), okno = połowa
półrocza; szczegóły w wf/pzo/README.md. Zakładka Reguły pokazuje 4 daty granic zamiast jednej. Wdrożenie razem
z żywą apką (osobny punkt listy, po widoku dziennym).

## ZATWIERDZONE (user „dobra pasuje", 18.09 23:35) — mockup C v2 = baza robocza. Start żywej apki:
1. Belka zakładek C (karty zrośnięte z treścią) + zakładka Reguły (cytat PZO z wf/pzo/README.md, manipulatory,
   szkoły→e-dziennik). 2. Obecność: widok dnia (kolumny z planu v2, otwarta = tabela, podgląd = klik nagłówka),
   przełącznik Dzień/Tydzień, bez belki klasy; ◀ dziś ▶ nowrap. 3. Wybór/dodawanie klasy i szkoły → Uczniowie;
   pytanie o e-dziennik przy szkole. 4. Stopka kolumny: Zapisz (reszta = ćwiczył) + Kopiuj do VULCANa/Librusa;
   po zapisie „zapisano HH:MM". 5. Ustawienie klasy dz./chł. → etykiety ćwiczył/ćwiczyła. 6. % dotychczasowy przy
   uczniu + % klasy w nagłówku (getStudentStats). 7. Kolumna „inne" (EZ/GW) w dniu. 8. Systematyczność: 4 okna
   (I.1 I.2 II.1 II.2). 9. test_widok_dzienny.py + regresja (zalegle 54, klawiatura 22, uklad, scalanie 31),
   README, sw v12, push + purge jsDelivr. Mockup po wdrożeniu → _zrzuty/ (ślad decyzji).
