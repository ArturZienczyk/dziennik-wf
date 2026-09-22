# Rendery drogi kopii dla panelu grounded-krytyki (K1/K2/K4).
#
# Po co osobny skrypt, a nie zrzut z palca: krytyk ocenia ŚWIEŻY render, a render
# ze stanu PUSTEGO nad-raportuje (empiria 19.09: 2 z 4 findingów fałszywe). Stan
# seeduje `fixture_stan.zasiej` — 23 uczniów, 10 dni frekwencji, klasa 6A.
#
# Lista kopii w folderze wymaga uchwytu File System Access, którego w headless nie
# da się kliknąć — podstawiam atrapę folderu (ta sama technika co test_kopie_z_folderu).
#
#     py -3.14 zrzut_droga_kopii.py        -> _zrzuty/wt2_*.png

from pathlib import Path

from playwright.sync_api import sync_playwright

from fixture_stan import otworz, serwer, zasiej

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)

ATRAPA = """() => {
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


def zrzut(page, nazwa, szer, pelna=False, wysokosc=520):
    sciezka = SHOTS / ("wt2_%s_%d.png" % (nazwa, szer))
    if pelna:
        page.screenshot(path=str(sciezka))
    else:
        page.screenshot(
            path=str(sciezka), clip={"x": 0, "y": 0, "width": szer, "height": wysokosc}
        )
    print("  ->", sciezka.name)


with serwer(8813) as port, sync_playwright() as pw:
    for szer in (1400, 390):
        browser, ctx, page, errors = otworz(
            pw, port, viewport={"width": szer, "height": 1000}
        )
        zasiej(page)
        page.click('button.tab:has-text("Uczniowie")')
        page.wait_for_timeout(500)
        zrzut(page, "1_pasek", szer, wysokosc=420 if szer == 1400 else 560)

        page.click('#tab-uczniowie button:has-text("Kopia zapasowa")')
        page.wait_for_timeout(400)
        zrzut(page, "2_okno", szer, pelna=True)

        page.evaluate(ATRAPA)
        page.click('#kopiaModal button:has-text("Wczytaj kopię")')
        page.wait_for_timeout(700)
        zrzut(page, "3_lista", szer, pelna=True)

        page.evaluate(
            "() => { document.querySelector('#kopiaModal details').open = true; }"
        )
        page.wait_for_timeout(300)
        zrzut(page, "4_ustawienia", szer, pelna=True)

        if errors:
            print("  BLEDY JS:", errors[:3])
        browser.close()
print("gotowe")
