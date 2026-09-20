# Bramka ukladu (2026-09-18): praca (tabela) ma zaczynac sie wysoko na ekranie laptopa,
# sciagi maja byc zwijane i pamietane, pasek gorny przyklejony, "Wyczysc wszystko" poza
# codziennym paskiem. Powod: przed ta runda lista uczniow w Obecnosci zaczynala sie na
# ~710 px z 768 - po otwarciu apki nie bylo widac ani jednego nazwiska.
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

FILE = (Path(__file__).resolve().parent / "dziennik_wf.html").as_uri()
FAILS = []
LAPTOP = {"width": 1366, "height": 768}


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name)


TOP = "(sel) => Math.round(document.querySelector(sel).getBoundingClientRect().top)"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_context(viewport=LAPTOP).new_page()
    # Piatek: widok Dzien w weekend bez lekcji chowa tabele (rect 0) — bez zamrozenia test dryfowal z data
    page.clock.set_fixed_time("2026-09-18T10:00:00")
    page.goto(FILE)
    page.wait_for_timeout(1200)
    page.evaluate("() => zamekPierwszeHaslo('x-haslo-123')")
    page.wait_for_timeout(400)

    otwarte = page.evaluate(
        "() => [...document.querySelectorAll('details.pomoc')].every(d => d.open)"
    )
    check("pierwsze otwarcie: wszystkie sciagi rozwiniete", otwarte)
    y_otw = page.evaluate(TOP, "#tab-obecnosc table")
    check(
        "Obecnosc ze sciaga rozwinieta: tabela widoczna na ekranie (< 700 px)",
        y_otw < 700,
        y_otw,
    )

    page.click("details.pomoc[data-pomoc=obecnosc] > summary")
    page.wait_for_timeout(200)
    y_zw = page.evaluate(TOP, "#tab-obecnosc table")
    check("Obecnosc ze sciaga zwinieta: tabela od < 400 px", y_zw < 400, y_zw)

    page.reload()
    page.wait_for_timeout(1200)
    page.evaluate("async () => { await zamekOdblokuj('x-haslo-123'); }")
    page.wait_for_timeout(400)
    st = page.evaluate(
        "() => Object.fromEntries([...document.querySelectorAll('details.pomoc')].map(d => [d.dataset.pomoc, d.open]))"
    )
    check(
        "po przeladowaniu: Obecnosc zwinieta, reszta rozwinieta",
        st.get("obecnosc") is False
        and all(v for k, v in st.items() if k != "obecnosc"),
        st,
    )

    for tab, sel in [
        ("Pomiary", "#tab-pomiary table"),
        ("Oceny", "#tab-oceny table"),
        ("Uczniowie", "#tab-uczniowie table"),
    ]:
        page.click('button.tab:has-text("%s")' % tab)
        page.wait_for_timeout(300)
        page.click("details.pomoc > summary >> visible=true")
        page.wait_for_timeout(200)
        y = page.evaluate(TOP, sel)
        check("%s ze sciaga zwinieta: tabela od < 450 px" % tab, y < 450, y)

    page.evaluate("() => window.scrollTo(0, 2000)")
    page.wait_for_timeout(200)
    y_tabs = page.evaluate(TOP, ".topbar .tabs")
    check(
        "pasek gorny przyklejony: zakladki widoczne po przewinieciu",
        0 <= y_tabs < 120,
        y_tabs,
    )
    page.click('button.tab:has-text("Obecno")')
    page.wait_for_timeout(300)
    # tabela musi byc dluzsza niz ekran, inaczej nie ma czego przewijac
    page.evaluate(
        "() => { for (let i = 0; i < 30; i++) state.students.push({ id: 't' + i, name: 'Uczen ' + i, longTermReleased: false, height: '', weight: '' }); renderAttendance(); }"
    )
    page.evaluate("() => window.scrollTo(0, 600)")
    page.wait_for_timeout(200)
    h_top = page.evaluate(
        "() => Math.round(document.querySelector('.topbar').getBoundingClientRect().bottom)"
    )
    # Od 2026-09-20 pod paskiem gornym stoi jeszcze przyklejona belka dnia (data, numer
    # lekcji) — naglowek tabeli klei sie pod NIA, nie pod samym paskiem gornym.
    # Pelny inwariant obu belek na trzech szerokosciach: test_belka_przyklejona.py
    y_belka = page.evaluate(
        "() => Math.round(document.querySelector('#tab-obecnosc .date-row.dzien-row').getBoundingClientRect().bottom)"
    )
    check("belka dnia przyklejona tuz pod paskiem gornym", y_belka >= h_top, (y_belka, h_top))
    y_th = page.evaluate(TOP, "#attendanceTable thead th")
    check(
        "naglowek tabeli przyklejony tuz pod belka dnia po przewinieciu",
        abs(y_th - y_belka) <= 2,
        (y_th, y_belka),
    )

    w_toolbar = page.evaluate(
        "() => !!document.querySelector('#tab-uczniowie .toolbar:not(.toolbar-niebezpieczne) button.danger')"
    )
    check(
        "Wyczysc wszystko NIE w codziennym pasku, tylko w osobnym na dole",
        not w_toolbar,
    )

    b.close()

if FAILS:
    print("\nWYNIK: FAIL - %d: %s" % (len(FAILS), FAILS))
    sys.exit(1)
print("\nWYNIK: PASS - uklad: praca wysoko, sciagi zwijane i pamietane.")
