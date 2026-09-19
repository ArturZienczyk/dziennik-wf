# Test „Statystyki i karta ucznia po całym roku” (2026-09-19): zakres rok | I | II półrocze w zakładce
# Statystyki (granica z Reguł), lista lekcji zwinięta domyślnie, druk statystyk = 1 strona A4 bez
# nagłówka/zakładek/listy; karta ucznia: druk bez listy lekcji (sekcja 4 schowana) chyba że checkbox
# „z listą lekcji”, kafle bilansu 8 w rzędzie. Roczny wsad: 19 uczniów × 77 lekcji.
import sys
import datetime
import random
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8775

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright

FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


def pdf_pages(path):
    try:
        import fitz

        return len(fitz.open(str(path)))
    except ImportError:
        from pypdf import PdfReader

        return len(PdfReader(str(path)).pages)


random.seed(1)
IM = [
    "Adam",
    "Bartek",
    "Cezary",
    "Damian",
    "Emil",
    "Filip",
    "Gracjan",
    "Hubert",
    "Igor",
    "Jakub",
    "Kacper",
    "Leon",
    "Marcel",
    "Nikodem",
    "Oskar",
    "Patryk",
    "Robert",
    "Szymon",
    "Tymon",
    "Wiktor",
]
STUDENTS = [
    {"id": f"u{i}", "name": f"{n} K.", "longTermReleased": i == 19}
    for i, n in enumerate(IM)
]
ATT = {}
d = datetime.date(2026, 9, 1)
while d <= datetime.date(2027, 6, 20):
    ferie = datetime.date(2026, 12, 23) <= d <= datetime.date(
        2027, 1, 3
    ) or datetime.date(2027, 1, 18) <= d <= datetime.date(2027, 1, 31)
    if d.weekday() in (1, 3) and not ferie:
        key = f"{d.isoformat()}#{3 if d.weekday() == 1 else 5}"
        ATT[key] = {}
        for s in STUDENTS[:19]:
            r = random.random()
            ATT[key][s["id"]] = (
                "C"
                if r < 0.82
                else "BS"
                if r < 0.88
                else "NU"
                if r < 0.94
                else "NB"
                if r < 0.97
                else "NC"
            )
    d += datetime.timedelta(days=1)
BRK = "2027-02-01"
N_I = sum(1 for k in ATT if k[:10] < BRK)
N_II = len(ATT) - N_I

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
    page.wait_for_timeout(600)
    page.evaluate(
        """([st, att, brk]) => {
      const c = makeClass('SP','7b',st); c.attendance = att; c.semesterBreak = brk;
      state.classes.push(c); activateClass(c.id); save(); refreshAll(); }""",
        [STUDENTS, ATT, BRK],
    )
    page.wait_for_timeout(400)
    page.click("button.tab:has-text('Statystyki')")
    page.wait_for_timeout(300)

    # ---------- 1. Zakres statystyk klasy ----------
    kafel = lambda: page.inner_text("#summaryGrid")
    check(
        "domyślnie cały rok: %d lekcji" % len(ATT),
        str(len(ATT)) in kafel()
        and page.evaluate(
            "() => document.querySelector('#statsZakres button.on').dataset.z"
        )
        == "rok",
    )
    page.click("#statsZakres button[data-z=I]")
    page.wait_for_timeout(200)
    check(
        "I półrocze: %d lekcji w kaflu" % N_I,
        str(N_I) in kafel() and "i półr" in kafel().lower(),
        kafel(),
    )
    check(
        "I półrocze: tabela ucznia liczy tylko I",
        page.inner_text("#statsBody tr:first-child td:nth-child(3)") == str(N_I),
    )
    page.click("#statsZakres button[data-z=II]")
    page.wait_for_timeout(200)
    check(
        "II półrocze: %d lekcji" % N_II,
        page.inner_text("#statsBody tr:first-child td:nth-child(3)") == str(N_II),
    )
    check(
        "zakres zapamiętany w localStorage (preferencja, nie dane)",
        page.evaluate("() => localStorage.getItem('dziennik_stats_zakres')") == "II",
    )
    check(
        "lista lekcji zwinięta domyślnie, z licznikiem",
        not page.evaluate("() => document.querySelector('details.stats-lekcje').open")
        and "(%d)" % len(ATT) in page.inner_text("details.stats-lekcje > summary"),
    )
    page.click("#statsZakres button[data-z=rok]")
    page.wait_for_timeout(200)
    page.screenshot(path=str(SHOTS / "druk_stats_ekran.png"))

    # bez granicy półrocza: przyciski I/II wyłączone
    page.evaluate("() => { getCurrentClass().semesterBreak = ''; renderStats(); }")
    check(
        "bez granicy: I/II wyłączone, opis mówi gdzie ustawić",
        page.evaluate(
            "() => document.querySelector('#statsZakres button[data-z=I]').disabled"
        )
        and "Regułach" in page.inner_text("#statsZakresOpis"),
    )
    page.evaluate("(b) => { getCurrentClass().semesterBreak = b; renderStats(); }", BRK)

    # ---------- 2. Druk statystyk = 1 strona ----------
    page.evaluate("() => document.body.classList.add('stats-print')")
    page.emulate_media(media="print")
    pdf1 = SHOTS / "druk_stats.pdf"
    page.pdf(path=str(pdf1), format="A4", print_background=True)
    check(
        "druk statystyk: 1 strona A4 (19 uczniów, 77 lekcji)",
        pdf_pages(pdf1) == 1,
        pdf_pages(pdf1),
    )
    check(
        "druk statystyk: nagłówek i zakładki schowane",
        not page.locator(".topbar").is_visible()
        and not page.locator("details.stats-lekcje").is_visible(),
    )
    check(
        "druk statystyk: tabela i opis zakresu widoczne",
        page.locator("#statsBody").is_visible()
        and page.locator("#statsZakresOpis").is_visible(),
    )
    page.emulate_media(media="screen")
    page.evaluate("() => document.body.classList.remove('stats-print')")

    # ---------- 3. Karta ucznia: druk bez listy / z listą ----------
    page.evaluate("() => openKarta('u0')")
    page.wait_for_timeout(500)
    check(
        "karta: checkbox „z listą lekcji” obok Drukuj, domyślnie odznaczony",
        page.locator("#kartaDrukLista").is_visible()
        and not page.is_checked("#kartaDrukLista"),
    )
    check(
        "karta na ekranie: sekcja 4 widoczna",
        page.locator(".karta-lista-sekcja").is_visible(),
    )
    page.evaluate(
        "() => { document.body.classList.add('karta-print'); document.body.classList.toggle('karta-print-lista', !!state.kartaDrukLista); }"
    )
    page.emulate_media(media="print")
    pdf2 = SHOTS / "druk_karta_bez_listy.pdf"
    page.pdf(path=str(pdf2), format="A4", print_background=True)
    check("karta bez listy: ≤2 strony (było 4)", pdf_pages(pdf2) <= 2, pdf_pages(pdf2))
    check(
        "karta bez listy: sekcja 4 schowana",
        not page.locator(".karta-lista-sekcja").is_visible(),
    )
    check(
        "karta w druku: kafle 8 w rzędzie",
        page.evaluate(
            "() => getComputedStyle(document.querySelector('.karta-kafle')).gridTemplateColumns.split(' ').length"
        )
        == 8,
    )
    page.emulate_media(media="screen")
    page.evaluate(
        "() => document.body.classList.remove('karta-print', 'karta-print-lista')"
    )
    page.check("#kartaDrukLista")
    page.evaluate(
        "() => { document.body.classList.add('karta-print'); document.body.classList.toggle('karta-print-lista', !!state.kartaDrukLista); }"
    )
    page.emulate_media(media="print")
    pdf3 = SHOTS / "druk_karta_z_lista.pdf"
    page.pdf(path=str(pdf3), format="A4", print_background=True)
    check(
        "karta z listą: sekcja 4 widoczna, więcej stron",
        page.locator(".karta-lista-sekcja").is_visible()
        and pdf_pages(pdf3) > pdf_pages(pdf2),
        (pdf_pages(pdf2), pdf_pages(pdf3)),
    )
    page.emulate_media(media="screen")
    page.evaluate(
        "() => document.body.classList.remove('karta-print', 'karta-print-lista')"
    )

    check("brak błędów JS", not errors, errors)
    browser.close()

httpd.shutdown()
print("\n%d FAIL" % len(FAILS) if FAILS else "\nALL PASS")
sys.exit(1 if FAILS else 0)
