# Test NEGATYWNY obchodu — czy detektory z test_obchod.py w ogóle coś widzą.
#
# Po co osobny plik: bramka, która nigdy nie zapaliła się na czerwono, nie jest
# zmierzona — jest ozdobą. Tu psujemy apkę celowo, na trzy sposoby, i żądamy,
# żeby każdy detektor złapał swoją wadę. Jeśli któryś przepuści — to detektor
# jest do naprawy, nie apka.
#
# Uruchamiaj razem z test_obchod.py: pozytywny mówi "czysto", negatywny mówi
# "i umiem powiedzieć, kiedy nie jest".

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from fixture_stan import otworz, serwer, zasiej

ROOT = Path(__file__).resolve().parent
PORT = 8782
TAB_BTN = "button.tab[onclick=\"switchTab('%s')\"]"

FAILS = []


def check(nazwa, warunek, detal=""):
    if not warunek:
        FAILS.append("%s :: %s" % (nazwa, detal))


def szerokosci(page):
    return page.evaluate(
        "() => ({ doc: document.documentElement.scrollWidth,"
        " win: document.documentElement.clientWidth })"
    )


def wystajace(page, win):
    return page.evaluate(
        """(win) => {
        const out = [];
        document.querySelectorAll('.tab-content.active *').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width > 0 && r.right > win + 2) out.push(el.tagName);
        });
        return out.slice(0, 3);
    }""",
        win,
    )


with serwer(PORT) as port, sync_playwright() as pw:
    browser, ctx, page, errors = otworz(pw, port)
    zasiej(page)
    page.click(TAB_BTN % "uczniowie")
    page.wait_for_timeout(300)

    # --- kontrola dodatnia: w stanie zdrowym detektory MILCZĄ ------------------
    # (bez tego nie wiemy, czy poniższe alarmy to zasługa wady, czy szum detektora)
    s = szerokosci(page)
    check("zdrowa apka: brak poziomego scrolla", s["doc"] <= s["win"] + 2, s)
    check("zdrowa apka: nic nie wystaje", not wystajace(page, s["win"]))
    check(
        "zdrowa apka: tabela ma wiersze", page.locator("#studentsBody tr").count() > 0
    )
    check("zdrowa apka: brak bledow JS", not errors, str(errors[:2]))

    # --- wada 1: element szerszy niż okno ------------------------------------
    page.evaluate(
        """() => {
        const d = document.createElement('div');
        d.id = 'wada-szerokosc';
        d.style.cssText = 'width:4000px;height:20px;background:red';
        document.querySelector('#tab-uczniowie').appendChild(d);
    }"""
    )
    page.wait_for_timeout(200)
    s = szerokosci(page)
    zlapane_scroll = s["doc"] > s["win"] + 2
    zlapane_wystaje = bool(wystajace(page, s["win"]))
    check("detektor layoutu lapie element 4000px", zlapane_scroll or zlapane_wystaje, s)
    page.evaluate("() => document.getElementById('wada-szerokosc').remove()")

    # --- wada 2: pusta tabela (regresja renderu) ------------------------------
    page.evaluate("() => { document.querySelector('#studentsBody').innerHTML = ''; }")
    page.wait_for_timeout(150)
    check(
        "detektor danych lapie pusta tabele",
        page.locator("#studentsBody tr").count() == 0,
        "wierszy=%d" % page.locator("#studentsBody tr").count(),
    )
    page.click(TAB_BTN % "obecnosc")
    page.click(TAB_BTN % "uczniowie")  # przerysowanie wraca do stanu zdrowego
    page.wait_for_timeout(250)

    # --- wada 3: błąd JS ------------------------------------------------------
    errors.clear()
    page.evaluate("() => { setTimeout(() => { null.boom; }, 0); }")
    page.wait_for_timeout(300)
    check("detektor bledow lapie wyjatek JS", bool(errors), "errors=%s" % errors[:2])

    browser.close()

print()
if FAILS:
    print("FAIL (%d) — detektor NIE widzi wady, ktora powinien:" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)

print("PASS — wszystkie 3 detektory zapalaja sie na wstrzyknietej wadzie,")
print("       i milcza na zdrowej apce. Zielony wynik test_obchod.py cos znaczy.")
