# Przesuwanie ucznia na liście (2026-11-04, P4 handoffu „koniec roku": poprawka pomyłki w kolejności bez
# kasowania listy): ▲▼ w kolumnie numeru, skrajne strzałki ukryte, kolejność przeżywa przeładowanie, Obecność
# numeruje tak samo, historia jedzie z uczniem; kopia telefon ↔ laptop przenosi kolejność, nie gubi ucznia
# dopisanego na drugim urządzeniu, stara kopia nie cofa kolejności. Render laptop + telefon 369×608.
import sys
import json
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
PORT = 8808

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


ST = [
    {"id": "u1", "name": "Adam K."},
    {"id": "u2", "name": "Cezary M."},
    {"id": "u3", "name": "Bartek L."},
    {"id": "u4", "name": "Darek N."},
]
ATT = {"2026-10-13#3": {"u3": "NC"}}
NOWA = "(st, att) => { const c = makeClass('SP','7b',st); c.attendance = att; state.classes.push(c); activateClass(c.id); save(); refreshAll(); }"
KOL = "() => { const c = state.classes.find(c => c.name === '7b'); return c.students.map(s => s.id).join(','); }"


def otworz(browser, vp=None):
    ctx = browser.new_context(
        service_workers="block", viewport=vp or {"width": 1400, "height": 900}
    )
    p = ctx.new_page()
    err = []
    p.on("pageerror", lambda e: err.append(str(e)))
    p.goto("http://127.0.0.1:%d/%s" % (PORT, PLIK))
    p.wait_for_timeout(400)
    p.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
    p.wait_for_timeout(600)
    return p, err


def wiersz(p, n, krok):
    return p.locator(
        "#studentsBody tr:nth-child(%d) .przes button[data-krok='%d']" % (n, krok)
    )


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for nazwa, vp in (
        ("lap", {"width": 1400, "height": 900}),
        ("tel", {"width": 369, "height": 608}),
    ):
        p, err = otworz(browser, vp)
        p.evaluate("([st, att]) => (" + NOWA + ")(st, att)", [ST, ATT])
        p.wait_for_timeout(200)
        p.locator("button.tab").filter(has_text="Uczniowie").click()
        p.wait_for_timeout(200)
        check(
            nazwa + ": ▲ ukryta w pierwszym wierszu", not wiersz(p, 1, -1).is_visible()
        )
        check(nazwa + ": ▼ ukryta w ostatnim wierszu", not wiersz(p, 4, 1).is_visible())
        p.screenshot(path=str(SHOTS / ("przesuwanie_przed_%s.png" % nazwa)))
        # pomyłka: Cezary (2.) powinien być za Bartkiem (3.)
        wiersz(p, 2, 1).click()
        p.wait_for_timeout(200)
        check(
            nazwa + ": ▼ przesuwa niżej",
            p.evaluate(KOL) == "u1,u3,u2,u4",
            p.evaluate(KOL),
        )
        check(
            nazwa + ": numer i nazwisko po przesunięciu",
            p.inner_text("#studentsBody tr:nth-child(2) .przes span") == "2"
            and p.input_value("#studentsBody tr:nth-child(2) input.student-name")
            == "Bartek L.",
        )
        check(
            nazwa + ": fokus jedzie z uczniem",
            p.evaluate(
                "() => document.activeElement.closest('tr') === document.querySelector('#studentsBody tr:nth-child(3)')"
            ),
        )
        wiersz(p, 4, -1).click()
        p.wait_for_timeout(200)
        check(
            nazwa + ": ▲ przesuwa wyżej",
            p.evaluate(KOL) == "u1,u3,u4,u2",
            p.evaluate(KOL),
        )
        wiersz(p, 3, 1).click()
        p.wait_for_timeout(200)
        p.screenshot(path=str(SHOTS / ("przesuwanie_po_%s.png" % nazwa)))
        check(
            nazwa + ": historia jedzie z uczniem",
            p.evaluate("() => state.attendance['2026-10-13#3'].u3") == "NC",
        )
        # Obecność numeruje tak samo
        p.locator("button.tab").filter(has_text="Obecność").click()
        p.wait_for_timeout(200)
        p.evaluate(
            "() => { state.currentDate = '2026-10-13'; state.currentNr = 3; renderAttendance(); }"
        )
        p.wait_for_timeout(200)
        imiona = p.evaluate(
            "() => [...document.querySelectorAll('#attendanceBody input.student-name')].map(i => i.value).join(',')"
        )
        check(
            nazwa + ": Obecność w nowej kolejności",
            imiona == "Adam K.,Bartek L.,Cezary M.,Darek N.",
            imiona,
        )
        # przeładowanie
        p.reload()
        p.wait_for_timeout(500)
        p.evaluate(
            "() => { if (typeof zamekOdblokuj === 'function') zamekOdblokuj('test-haslo-123'); }"
        )
        p.wait_for_timeout(600)
        check(
            nazwa + ": kolejność przeżywa przeładowanie",
            p.evaluate(KOL) == "u1,u3,u2,u4",
            p.evaluate(KOL),
        )
        check(nazwa + ": bez błędów strony", not err, err[:3])
        p.context.close()

    # Kopia telefon (A) ↔ laptop (B)
    A, ea = otworz(browser)
    B, eb = otworz(browser)
    snap = lambda p: json.loads(p.evaluate("() => JSON.stringify(snapshotData())"))
    scal = lambda p, d: p.evaluate(
        "(d) => { const w = scalKopie(d); save(); return w; }", d
    )
    A.evaluate("([st, att]) => (" + NOWA + ")(st, att)", [ST, ATT])
    A.wait_for_timeout(30)
    scal(B, snap(A))
    B.evaluate(
        "() => { activateClass(state.classes.find(c => c.name === '7b').id); refreshAll(); }"
    )
    stara = snap(A)  # kolejność sprzed poprawki
    A.wait_for_timeout(30)
    A.evaluate("() => przesunUcznia('u2', 1)")  # telefon: Cezary za Bartka
    B.evaluate(
        "() => { state.students.push({ id: 'u9', name: 'Emil O.', longTermReleased: false, height: '', weight: '' }); save(); }"
    )  # laptop w międzyczasie dopisał ucznia
    A.wait_for_timeout(30)
    scal(B, snap(A))
    check(
        "kopia: kolejność z telefonu na laptopie",
        B.evaluate(KOL) == "u1,u3,u2,u4,u9",
        B.evaluate(KOL),
    )
    scal(A, snap(B))
    check(
        "kopia: telefon dostał ucznia z laptopa na końcu",
        A.evaluate(KOL) == "u1,u3,u2,u4,u9",
        A.evaluate(KOL),
    )
    scal(B, stara)
    check(
        "kopia: stara kopia nie cofa kolejności",
        B.evaluate(KOL) == "u1,u3,u2,u4,u9",
        B.evaluate(KOL),
    )
    check("kopia: bez błędów strony", not ea and not eb, (ea + eb)[:3])
    browser.close()

httpd.shutdown()
print("WYNIK: %s" % ("PASS" if not FAILS else "FAIL %d" % len(FAILS)))
sys.exit(1 if FAILS else 0)
