# Test „Daty” w Statystykach (2026-10-21, Artur: raport z dowolnego okresu): czwarty przycisk zakresu
# z polami od–do (oba dni włącznie), tabela klasy i raport całego dziennika liczą tylko ten zakres,
# działa też w klasie bez granicy półrocza, daty przeżywają przeładowanie; render laptop + telefon 369×608.
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
PORT = 8803

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


ST = [{"id": "u1", "name": "Adam K."}, {"id": "u2", "name": "Bartek L."}]
# 6 lekcji: 1.10, 6.10, 8.10, 13.10, 15.10, 20.10 — u1 ćwiczy tylko 6–15.10
DNI = [
    "2026-10-01",
    "2026-10-06",
    "2026-10-08",
    "2026-10-13",
    "2026-10-15",
    "2026-10-20",
]
ATT = {d + "#3": {"u1": "C" if "06" <= d[8:] <= "15" else "NC", "u2": "C"} for d in DNI}

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for nazwa, vp in (
        ("lap", {"width": 1400, "height": 900}),
        ("tel", {"width": 369, "height": 608}),
    ):
        ctx = browser.new_context(service_workers="block", viewport=vp)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("http://127.0.0.1:%d/%s" % (PORT, PLIK))
        page.wait_for_timeout(400)
        page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
        page.wait_for_timeout(600)
        page.evaluate(
            """([st, att]) => {
          const c = makeClass('SP','7b',st); c.attendance = att;
          state.classes.push(c); activateClass(c.id); save(); refreshAll(); }""",
            [ST, ATT],
        )
        page.wait_for_timeout(300)
        page.click("button.tab:has-text('Statystyki')")
        page.wait_for_timeout(300)
        lekcje_u1 = lambda: page.inner_text("#statsBody tr:first-child td:nth-child(3)")
        pct_u1 = lambda: page.inner_text("#statsBody tr:first-child td:nth-child(6)")

        check(
            nazwa + ": klasa bez granicy — 'Daty' aktywny",
            page.is_enabled("#statsZakres button[data-z=daty]"),
        )
        check(
            nazwa + ": pola dat schowane przy 'Cały rok'",
            not page.is_visible("#statsOd"),
        )
        page.click("#statsZakres button[data-z=daty]")
        page.wait_for_timeout(200)
        check(
            nazwa + ": pola dat widoczne po 'Daty'",
            page.is_visible("#statsOd") and page.is_visible("#statsDo"),
        )
        check(
            nazwa + ": puste daty = cała historia (6)", lekcje_u1() == "6", lekcje_u1()
        )
        page.fill("#statsOd", "2026-10-06")
        page.fill("#statsDo", "2026-10-15")
        page.wait_for_timeout(200)
        check(
            nazwa + ": 6–15.10 = 4 lekcje (oba dni włącznie)",
            lekcje_u1() == "4",
            lekcje_u1(),
        )
        check(nazwa + ": u1 w zakresie 100%", pct_u1() == "100%", pct_u1())
        opis = page.inner_text("#statsZakresOpis")
        check(nazwa + ": opis zakresu", "06.10" in opis and "15.10" in opis, opis)
        page.screenshot(
            path=str(SHOTS / ("statystyki_daty_%s.png" % nazwa)), full_page=False
        )

        # raport całego dziennika liczy ten sam zakres
        page.evaluate("() => { window.print = () => {}; drukujRaportCaly(); }")
        r = page.inner_text("#raportCaly")
        check(
            nazwa + ": raport — nagłówek z datami",
            "od 06.10" in r and "do 15.10" in r,
            r[:160],
        )
        check(nazwa + ": raport — 4 lekcje w klasie", "4 lekcji" in r, r[:300])
        u1 = page.evaluate(
            "() => document.querySelector('#raportCaly tbody tr td.ost').textContent"
        )
        check(nazwa + ": raport — u1 100%", u1 == "100%", u1)
        page.evaluate("() => document.body.classList.remove('raport-print')")

        # przeładowanie: zakres i daty zostają
        page.reload()
        page.wait_for_timeout(400)
        page.evaluate("() => zamekOdblokuj('test-haslo-123')")
        page.wait_for_timeout(700)
        page.click("button.tab:has-text('Statystyki')")
        page.wait_for_timeout(300)
        check(
            nazwa + ": po przeładowaniu daty zostały",
            page.input_value("#statsOd") == "2026-10-06"
            and page.input_value("#statsDo") == "2026-10-15"
            and lekcje_u1() == "4",
            [page.input_value("#statsOd"), page.input_value("#statsDo"), lekcje_u1()],
        )
        szer = page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
        )
        check(nazwa + ": bez poziomego przewijania strony", szer)
        check(nazwa + ": bez błędów JS", not errors, errors)
        ctx.close()
    browser.close()

httpd.shutdown()
print("\nWYNIK:", "OK" if not FAILS else "BŁĘDY (%d FAIL)" % len(FAILS))
sys.exit(1 if FAILS else 0)
