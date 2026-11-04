# Test „uczeń odszedł” (2026-11-04, P3 handoffu „koniec roku": wyszarzony z historią): data w kolumnie
# „Odszedł od” na liście uczniów; od tego dnia uczeń poza lekcją (Zapisz lekcję nie daje mu C, nie liczy
# się do „wpisanych”, klawiatura i kopia do VULCANa go pomijają, nie wchodzi do % klasy), a wpisy sprzed
# odejścia zostają i liczą się do jego własnego procentu; pusta data = wraca. Render laptop + telefon 369×608.
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
PORT = 8804

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright

FAILS = []
TABY = {"uczniowie": "Uczniowie", "statystyki": "Statystyki", "obecnosc": "Obecność"}


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


ST = [
    {"id": "u1", "name": "Adam K."},
    {"id": "u2", "name": "Bartek L."},
    {"id": "u3", "name": "Cezary M."},
]
# u3 odchodzi 15.10: przed odejściem 1×C i 1×NĆ (50%), reszta 100%
ATT = {
    "2026-10-08#3": {"u1": "C", "u2": "C", "u3": "C"},
    "2026-10-13#3": {"u1": "C", "u2": "C", "u3": "NC"},
}
ODSZEDL = "2026-10-15"

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

        # 1. Lista uczniów: data w kolumnie „Odszedł od”
        page.locator("button.tab").filter(has_text=TABY["uczniowie"]).click()
        page.wait_for_timeout(200)
        page.fill("#studentsBody tr:nth-child(3) input.odszedl-data", ODSZEDL)
        page.dispatch_event(
            "#studentsBody tr:nth-child(3) input.odszedl-data", "change"
        )
        page.wait_for_timeout(200)
        check(
            nazwa + ": data zapisana w uczniu",
            page.evaluate("() => state.students[2].odszedl") == ODSZEDL,
        )
        check(
            nazwa + ": wiersz na liście wyszarzony",
            page.evaluate(
                "() => document.querySelector('#studentsBody tr:nth-child(3)').classList.contains('odszedl')"
            ),
        )
        check(
            nazwa + ": historia została",
            page.evaluate("() => state.attendance['2026-10-13#3'].u3") == "NC",
        )
        page.screenshot(
            path=str(SHOTS / ("odszedl_lista_%s.png" % nazwa)), full_page=True
        )

        # 2. Lekcja PO odejściu: Zapisz lekcję nie daje mu C
        page.locator("button.tab").filter(has_text=TABY["obecnosc"]).click()
        page.evaluate(
            "() => { state.currentDate = '2026-10-20'; state.currentNr = 3; renderAttendance(); }"
        )
        page.wait_for_timeout(200)
        check(
            nazwa + ": w Obecności wiersz wyszarzony z napisem",
            "odszedł 15.10" in page.inner_text("#attendanceBody tr:nth-child(3)"),
            page.inner_text("#attendanceBody tr:nth-child(3)")[:80],
        )
        check(
            nazwa + ": klawiatura go pomija",
            page.evaluate("() => kbdActiveStudents().map(s => s.id).join(',')")
            == "u1,u2",
        )
        page.screenshot(
            path=str(SHOTS / ("odszedl_obecnosc_%s.png" % nazwa)), full_page=True
        )
        page.evaluate("() => { finalizeLesson(); confirmOk(); }")
        page.wait_for_timeout(200)
        dzien = page.evaluate("() => state.attendance['2026-10-20#3']")
        check(
            nazwa + ": Zapisz lekcję — C dla obecnych, nic dla odszedłego",
            dzien == {"u1": "C", "u2": "C"},
            dzien,
        )

        # 3. Lekcja PRZED odejściem: normalny uczeń
        check(
            nazwa + ": 13.10 liczy się do lekcji",
            page.evaluate(
                "() => state.students.filter(s => naLekcji(s, '2026-10-13')).length"
            )
            == 3,
        )

        # 4. % klasy bez niego, jego własny % z historii
        check(
            nazwa + ": % klasy bez odszedłego (100, nie 88)",
            page.evaluate("() => procentKlasy(getCurrentClass())") == 100,
            page.evaluate("() => procentKlasy(getCurrentClass())"),
        )
        page.locator("button.tab").filter(has_text=TABY["statystyki"]).click()
        page.wait_for_timeout(300)
        wiersz = page.inner_text("#statsBody tr:nth-child(3)")
        check(
            nazwa + ": w Statystykach zostaje z dopiskiem",
            "odszedł 15.10" in wiersz,
            wiersz[:80],
        )
        check(
            nazwa + ": jego własny procent z historii (50%)",
            "50%" in wiersz,
            wiersz[:120],
        )
        karta = page.evaluate(
            "() => [...document.querySelectorAll('.summary-card')].find(k => k.textContent.includes('Zwolnionych')).querySelector('.summary-value').textContent"
        )
        check(nazwa + ": odszedły nie liczy się jako zwolniony", karta == "0", karta)
        page.screenshot(
            path=str(SHOTS / ("odszedl_statystyki_%s.png" % nazwa)), full_page=True
        )

        # 5. Kopia do VULCANa po odejściu go pomija (wpisu nie ma); przed odejściem NĆ jest
        page.evaluate(
            """() => { window._schowek = null;
          navigator.clipboard.writeText = t => { window._schowek = t; return Promise.resolve(); }; }"""
        )
        page.evaluate(
            "() => { const c = getCurrentClass(); c.attendance['2026-10-22#3'] = { u1: 'NB' }; copyForVulcan(c.id, '2026-10-22#3'); }"
        )
        page.wait_for_timeout(100)
        check(
            nazwa + ": VULCAN po odejściu — bez niego",
            "Cezary" not in (page.evaluate("() => window._schowek") or ""),
            page.evaluate("() => window._schowek"),
        )
        page.evaluate("() => copyForVulcan(getCurrentClass().id, '2026-10-13#3')")
        page.wait_for_timeout(100)
        check(
            nazwa + ": VULCAN przed odejściem — jest",
            "Cezary M.\tNC" in (page.evaluate("() => window._schowek") or ""),
        )

        # 6. Pusta data = wraca
        page.locator("button.tab").filter(has_text=TABY["uczniowie"]).click()
        page.wait_for_timeout(200)
        page.fill("#studentsBody tr:nth-child(3) input.odszedl-data", "")
        page.dispatch_event(
            "#studentsBody tr:nth-child(3) input.odszedl-data", "change"
        )
        page.wait_for_timeout(200)
        check(
            nazwa + ": pusta data — wraca",
            page.evaluate("() => 'odszedl' in state.students[2]") is False,
        )

        # 7. Przeżywa przeładowanie (zapis)
        page.fill("#studentsBody tr:nth-child(3) input.odszedl-data", ODSZEDL)
        page.dispatch_event(
            "#studentsBody tr:nth-child(3) input.odszedl-data", "change"
        )
        page.wait_for_timeout(300)
        page.reload()
        page.wait_for_timeout(500)
        page.evaluate(
            "() => { if (typeof zamekOdblokuj === 'function') zamekOdblokuj('test-haslo-123'); }"
        )
        page.wait_for_timeout(600)
        po = page.evaluate(
            "() => { const c = state.classes.find(c => c.name === '7b'); return c ? (c.students[2] || {}).odszedl : 'brak klasy'; }"
        )
        check(nazwa + ": data przeżywa przeładowanie", po == ODSZEDL, po)

        check(nazwa + ": bez błędów strony", not errors, errors[:3])
        ctx.close()
    browser.close()

httpd.shutdown()
print("WYNIK: %s" % ("PASS" if not FAILS else "FAIL %d" % len(FAILS)))
sys.exit(1 if FAILS else 0)
