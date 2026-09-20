# Dowód, że piaskownica NIE dotyka prawdziwego dziennika.
#
# Warunek ostrzejszy niż rzeczywisty: oba pliki otwierane w TYM SAMYM profilu
# przeglądarki i z tego samego originu (http://127.0.0.1:PORT). W realnym użyciu
# piaskownica jest odcięta już samym plikiem; tutaj sprawdzamy, czy jest odcięta
# nawet wtedy, gdy wszystko inne jest wspólne. Jeśli przechodzi tu — przejdzie
# wszędzie.
#
# Co orzeka:
#   1. piaskownica nie widzi danych prawdziwego dziennika,
#   2. zapis w piaskownicy NIE zmienia klucza prawdziwego dziennika,
#   3. prawdziwy dziennik po wizycie w piaskownicy ma swoje dane nietknięte.

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from fixture_stan import HASLO, serwer, zasiej

ROOT = Path(__file__).resolve().parent
PORT = 8783
PRAWDZIWY = "dziennik_wf.html"
PIASKOWNICA = "dziennik_wf_piaskownica.html"

KLUCZ_PRAWDZIWY = "dziennik_wf_v1"
KLUCZ_PIASKOWNICA = "dziennik_wf_PIASKOWNICA"

FAILS = []


def check(nazwa, warunek, detal=""):
    if not warunek:
        FAILS.append("%s :: %s" % (nazwa, detal))


def ls_klucze(page):
    """Surowa zawartość localStorage — patrzymy na magazyn, nie na to, co apka mówi."""
    return page.evaluate(
        """() => {
        const out = {};
        for (let i = 0; i < localStorage.length; i++) {
            const k = localStorage.key(i);
            out[k] = (localStorage.getItem(k) || '').length;
        }
        return out;
    }"""
    )


if not (ROOT / PIASKOWNICA).exists():
    print("BLAD: brak %s — odpal najpierw: python zrob_piaskownice.py" % PIASKOWNICA)
    sys.exit(1)

with serwer(PORT) as port, sync_playwright() as pw:
    browser = pw.chromium.launch()
    # JEDEN kontekst dla obu plików — celowo. Osobne konteksty niczego by nie dowiodły.
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
    )
    page = ctx.new_page()

    # --- 1. prawdziwy dziennik dostaje dane ----------------------------------
    page.goto("http://127.0.0.1:%d/%s" % (port, PRAWDZIWY))
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('%s')" % HASLO)
    page.wait_for_timeout(200)
    opis = zasiej(page, uczniow=5, dni=2)
    klucze_po_zasianiu = ls_klucze(page)
    rozmiar_prawdziwego = klucze_po_zasianiu.get(KLUCZ_PRAWDZIWY, 0)
    # Surowy szyfrogram przed wizytą w piaskownicy — porównanie bajt w bajt jest
    # mocniejszym dowodem niż odszyfrowanie i oglądanie klasy (i nie wymaga hasła
    # po przeładowaniu strony).
    szyfrogram_przed = page.evaluate(
        "() => localStorage.getItem('%s')" % KLUCZ_PRAWDZIWY
    )

    check(
        "prawdziwy dziennik zapisal sie pod swoim kluczem",
        rozmiar_prawdziwego > 0,
        klucze_po_zasianiu,
    )

    # --- 2. piaskownica: czy widzi cudze dane? -------------------------------
    page.goto("http://127.0.0.1:%d/%s" % (port, PIASKOWNICA))
    page.wait_for_timeout(500)

    widzi = page.evaluate(
        "() => ({ klucz: STORAGE_KEY, idb: IDB_NAME,"
        " maStan: !!localStorage.getItem(STORAGE_KEY) })"
    )
    check(
        "piaskownica uzywa wlasnego klucza LS",
        widzi["klucz"] == KLUCZ_PIASKOWNICA,
        widzi,
    )
    check(
        "piaskownica uzywa wlasnej bazy IDB", widzi["idb"] == KLUCZ_PIASKOWNICA, widzi
    )
    check(
        "piaskownica startuje PUSTA (nie widzi cudzych danych)",
        not widzi["maStan"],
        widzi,
    )

    # zamek piaskownicy to osobny zamek — gdyby dzielił magazyn,
    # zapytałby o odblokowanie zamiast o pierwsze hasło
    page.evaluate("() => zamekPierwszeHaslo('inne-haslo-piaskownicy')")
    page.wait_for_timeout(200)
    zasiej(page, uczniow=3, dni=1, klasa="TESTOWA")
    po_zapisie = ls_klucze(page)

    check(
        "piaskownica zapisala sie pod SWOIM kluczem",
        po_zapisie.get(KLUCZ_PIASKOWNICA, 0) > 0,
        po_zapisie,
    )
    check(
        "zapis w piaskownicy NIE ruszyl klucza prawdziwego dziennika",
        po_zapisie.get(KLUCZ_PRAWDZIWY, 0) == rozmiar_prawdziwego,
        "przed=%d po=%d" % (rozmiar_prawdziwego, po_zapisie.get(KLUCZ_PRAWDZIWY, 0)),
    )

    # --- 3. powrót: prawdziwy dziennik nietknięty ----------------------------
    page.goto("http://127.0.0.1:%d/%s" % (port, PRAWDZIWY))
    page.wait_for_timeout(500)
    szyfrogram_po = page.evaluate("() => localStorage.getItem('%s')" % KLUCZ_PRAWDZIWY)
    check(
        "szyfrogram prawdziwego dziennika identyczny bajt w bajt",
        szyfrogram_po == szyfrogram_przed,
        "przed=%d znakow, po=%d"
        % (len(szyfrogram_przed or ""), len(szyfrogram_po or "")),
    )
    # Zamek prawdziwego dziennika nadal zna SWOJE hasło — gdyby piaskownica
    # nadpisała magazyn, odszyfrowanie hasłem z prawdziwego dziennika by padło.
    stan = page.evaluate(
        """async (haslo) => {
        const ok = await zamekOdblokuj(haslo);
        if (!ok) return { odblokowany: false };
        const s = await zamekStanZapisany();
        const c = s && s.classes && s.classes[0];
        return {
            odblokowany: true,
            klasa: c ? c.name : null,
            uczniow: c ? (c.students || []).filter(u => u.name).length : 0,
        };
    }""",
        HASLO,
    )
    check(
        "prawdziwy dziennik otwiera sie SWOIM haslem",
        stan.get("odblokowany"),
        stan,
    )
    if stan.get("odblokowany"):
        check(
            "prawdziwy dziennik ma swoja klase (6A, 5 uczniow)",
            stan["klasa"] == "6A" and stan["uczniow"] == 5,
            stan,
        )
        check(
            "prawdziwy dziennik NIE dostal klasy z piaskownicy",
            stan["klasa"] != "TESTOWA",
            stan,
        )

    browser.close()

print()
if FAILS:
    print("FAIL (%d) — IZOLACJA NIESZCZELNA, nie uzywaj piaskownicy:" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)

print("PASS — piaskownica jest odcieta nawet w tym samym profilu i originie.")
print("       Klikanie w niej nie moze tknac Twoich wpisow.")
