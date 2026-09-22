# Ocena czytelności dziennika — trasy renderów dla panelu krytyków (agent `krytyk-ux`).
#
# KIEDY: Artur zgłasza „nieczytelne / szum / za dużo przycisków / nie wiem, gdzie kliknąć”.
# To jest wyzwalacz (decyzja 22.09) — NIE pre-push i NIE każdy render: panel to trzy modele,
# niedeterministyczny i płatny, a 2 z 7 findingów 22.09 były fałszywe.
#
# Procedura (pełna: README, sekcja „Ocena czytelności”):
#   1. py -3.14 ocena_czytelnosci.py <trasa>     -> _zrzuty/czytelnosc/<trasa>/*.png + brief.md
#      (brak trasy dla zgłoszonego ekranu = dopisz wpis do TRASY, nie nowy skrypt)
#   2. trzy agenty `krytyk-ux` równolegle, różne role (K1/K2/K4; K3 gdy chodzi o kontrast/dotyk)
#   3. py -3.14 D:/Projects/tools/contracts/ux_panel.py --weryfikuj <K*.json> --kod dziennik_wf.html
#   4. werdykt przy kodzie (NIE po liczbie głosów); uznany finding -> reguła w test_audyt_ux.py
#
# Stan PEŁNY z fixture_stan.zasiej (23 uczniów, 10 dni) — render ze stanu pustego nad-raportuje
# (19.09: 2 z 4 findingów fałszywe). Bramka test_ocena_czytelnosci.py pilnuje tylko, że każda
# trasa wciąż przechodzi (selektory żyją) — między zgłoszeniami skrypt inaczej by zgnił.
#
#     py -3.14 ocena_czytelnosci.py              -> lista tras
#     py -3.14 ocena_czytelnosci.py droga_kopii

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from fixture_stan import otworz, serwer, zasiej

ROOT = Path(__file__).resolve().parent
KATALOG = ROOT / "_zrzuty" / "czytelnosc"


@dataclass
class Krok:
    nazwa: str
    opis: str  # co użytkownik właśnie zrobił — trafia do briefu dla K4
    akcja: Callable | None = None
    pelna: bool = True  # False = kadr od góry (wysokosc)
    wysokosc: dict = field(default_factory=dict)  # szerokosc -> px dla kadru


@dataclass
class Trasa:
    opis: str
    cele: list  # cele zadaniowe dla K4 (cognitive walkthrough)
    kroki: list
    szerokosci: tuple = (1400, 390)
    uwagi: list = field(default_factory=list)  # artefakty trasy, które krytyk ma znać


# --- atrapy tego, czego headless nie kliknie --------------------------------------------

# Lista kopii w folderze wymaga uchwytu File System Access — podstawiam atrapę (ta sama
# technika co test_kopie_z_folderu). UWAGA dla krytyka: atrapa zmienia nazwę folderu między
# krokami 2 i 3 — to artefakt trasy, nie apki (22.09 dwóch krytyków wzięło to za błąd).
ATRAPA_FOLDERU = """() => {
  const plik = (name, mtime, tresc) => ({
    kind: 'file', name,
    getFile: async () => ({ lastModified: mtime, size: tresc.length, text: async () => tresc })
  });
  _folderKopii = {
    name: 'Dziennik WF kopie',
    queryPermission: async () => 'granted',
    requestPermission: async () => 'granted',
    values: async function* () {
      yield plik('dziennik-wf_AUTO-codzienna_SZYFROWANA_2026-09-22_07-12.enc.json', Date.parse('2026-09-22T07:12:00'), 'x'.repeat(41000));
      yield plik('dziennik-wf_WYSLANA_SZYFROWANA_2026-09-21_19-30.enc.json', Date.parse('2026-09-21T19:30:00'), 'x'.repeat(40200));
      yield plik('dziennik-wf_AUTO-codzienna_SZYFROWANA_2026-09-21_07-40.enc.json', Date.parse('2026-09-21T07:40:00'), 'x'.repeat(39800));
    }
  };
  _folderKopiiNazwa = 'Dziennik WF kopie';
  odswiezFolderKopii();
}"""


def _klik(selektor, czekaj=400):
    def akcja(page):
        page.click(selektor)
        page.wait_for_timeout(czekaj)

    return akcja


def _wczytaj_z_folderu(page):
    page.evaluate(ATRAPA_FOLDERU)
    page.click("#pasekWczytaj")
    page.wait_for_timeout(700)


def _rozwin_ustawienia(page):
    page.evaluate("() => zamknijKopieModal()")
    page.click("#kopiaStan a")
    page.wait_for_timeout(300)


# --- trasy -------------------------------------------------------------------------------

TRASY = {
    "droga_kopii": Trasa(
        opis="Droga kopii dziennika: blok kopii w zakładce Uczniowie -> wczytanie z listy w folderze -> ustawienia (⚙)",
        cele=[
            "Jesteś nauczycielem po lekcji na telefonie. Chcesz, żeby dzisiejsze wpisy trafiły na laptopa.",
            "Jesteś przy laptopie. Chcesz wczytać najnowszą kopię, którą przysłałeś sobie z telefonu.",
        ],
        kroki=[
            Krok(
                "pasek",
                "Otworzył zakładkę Uczniowie.",
                _klik('button.tab:has-text("Uczniowie")', 500),
                pelna=False,
                wysokosc={1400: 420, 390: 560},
            ),
            Krok(
                "okno",
                "Kliknął „Wczytaj kopię dziennika z telefonu” (folder kopii już wybrany wcześniej).",
                _wczytaj_z_folderu,
            ),
            Krok("ustawienia", "Zamknął okno i kliknął „⚙ hasło, PIN, foldery kopii”.", _rozwin_ustawienia),
        ],
        uwagi=[
            "Folder kopii w kroku 2 to atrapa podstawiona przez skrypt (headless nie wybierze folderu). "
            "Nazwa folderu w kroku 2 to artefakt trasy, nie zachowanie apki.",
        ],
    ),
}


def renderuj(nazwa, katalog=None, port=8813):
    """Przechodzi trasę w każdej szerokości. Zwraca (lista PNG, błędy JS). Wyjątek = trasa zgniła."""
    from playwright.sync_api import sync_playwright

    trasa = TRASY[nazwa]
    katalog = Path(katalog or KATALOG / nazwa)
    katalog.mkdir(parents=True, exist_ok=True)
    pliki, bledy = [], []
    with serwer(port) as p, sync_playwright() as pw:
        for szer in trasa.szerokosci:
            # szerokość < 600 = telefon: dotyk + mobile, bo apka czyta pointer, nie szerokość
            browser, ctx, page, errors = otworz(
                pw, p, viewport={"width": szer, "height": 1000}, telefon=szer < 600
            )
            zasiej(page)
            for i, k in enumerate(trasa.kroki, 1):
                if k.akcja:
                    k.akcja(page)
                sciezka = katalog / ("%02d_%s_%d.png" % (i, k.nazwa, szer))
                if k.pelna:
                    page.screenshot(path=str(sciezka))
                else:
                    h = k.wysokosc.get(szer, 520)
                    page.screenshot(
                        path=str(sciezka),
                        clip={"x": 0, "y": 0, "width": szer, "height": h},
                    )
                pliki.append(sciezka)
            bledy += errors
            browser.close()
    return pliki, bledy


def zapisz_brief(nazwa, pliki, katalog=None):
    trasa = TRASY[nazwa]
    katalog = Path(katalog or KATALOG / nazwa)
    linie = [
        "# Brief dla panelu krytyków — trasa `%s`" % nazwa,
        "",
        trasa.opis,
        "",
        "Stan: dziennik wypełniony (23 uczniów, 10 dni frekwencji) — nie pusty.",
        "Szerokości: %s px (ostatnia = telefon)."
        % ", ".join(map(str, trasa.szerokosci)),
        "",
        "## Cele zadaniowe (K4)",
        *["- " + c for c in trasa.cele],
        "",
        *(["## Artefakty trasy (NIE zgłaszaj jako błąd apki)", *["- " + u for u in trasa.uwagi], ""] if trasa.uwagi else []),
        "## Kroki i zrzuty",
    ]
    for i, k in enumerate(trasa.kroki, 1):
        zrzuty = ", ".join("%02d_%s_%d.png" % (i, k.nazwa, s) for s in trasa.szerokosci)
        linie.append("%d. **%s** — %s  \n   %s" % (i, k.nazwa, k.opis, zrzuty))
    linie += [
        "",
        "Zrzuty leżą w tym samym katalogu co ten plik. Raport zapisz jako `<ROLA>.json` obok.",
    ]
    (katalog / "brief.md").write_text("\n".join(linie) + "\n", encoding="utf-8")
    return katalog / "brief.md"


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in TRASY:
        print("Trasy:")
        for n, t in TRASY.items():
            print("  %-14s %s" % (n, t.opis))
        sys.exit(0 if len(sys.argv) < 2 else 1)
    nazwa = sys.argv[1]
    pliki, bledy = renderuj(nazwa)
    brief = zapisz_brief(nazwa, pliki)
    for p in pliki:
        print("  ->", p.relative_to(ROOT))
    if bledy:
        print("  BLEDY JS:", bledy[:3])
    print("brief:", brief)
