# „Odszedł od” w kopii telefon ↔ laptop (2026-11-04): dwa urządzenia = dwa konteksty przeglądarki.
# Data wpisana na jednym przechodzi na drugie, zdjęta daty też przechodzi, starsza kopia jej nie
# wskrzesza, a wpisy innych uczniów z drugiego urządzenia nie giną przy scalaniu.
import sys
import json
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
PORT = 8807

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


ST = [{"id": "u1", "name": "Adam K."}, {"id": "u3", "name": "Cezary M."}]
with sync_playwright() as pw:
    browser = pw.chromium.launch()

    def urzadzenie():
        p = browser.new_context(service_workers="block").new_page()
        err = []
        p.on("pageerror", lambda e: err.append(str(e)))
        p.goto("http://127.0.0.1:%d/%s" % (PORT, PLIK))
        p.wait_for_timeout(400)
        p.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
        p.wait_for_timeout(600)
        return p, err

    A, ea = urzadzenie()  # telefon
    B, eb = urzadzenie()  # laptop
    snap = lambda p: json.loads(p.evaluate("() => JSON.stringify(snapshotData())"))
    scal = lambda p, d: p.evaluate(
        "(d) => { const w = scalKopie(d); save(); return w; }", d
    )
    odszedl = lambda p: p.evaluate(
        "() => { const c = state.classes.find(c => c.name === '7b'); const s = c && c.students.find(s => s.id === 'u3'); return s ? (s.odszedl || '') : 'brak'; }"
    )
    A.evaluate(
        "(st) => { const c = makeClass('SP','7b',st); state.classes.push(c); activateClass(c.id); save(); refreshAll(); }",
        ST,
    )
    A.wait_for_timeout(30)
    scal(B, snap(A))
    B.evaluate(
        "() => { activateClass(state.classes.find(c => c.name === '7b').id); refreshAll(); }"
    )
    check("start: klasa na obu, bez daty", odszedl(B) == "", odszedl(B))

    # 1. data na telefonie -> laptop; w międzyczasie laptop wpisał lekcję Adamowi
    A.evaluate("() => ustawOdszedl('u3', '2026-10-15')")
    stara = snap(A)  # kopia z datą — posłuży w kroku 3
    B.evaluate(
        "() => { const c = getCurrentClass(); c.attendance['2026-10-20#3'] = { u1: 'NB' }; save(); }"
    )
    A.wait_for_timeout(30)
    scal(B, snap(A))
    check("data przeszła telefon -> laptop", odszedl(B) == "2026-10-15", odszedl(B))
    check(
        "wpis laptopa dla Adama nie zginął",
        B.evaluate("() => (getCurrentClass().attendance['2026-10-20#3'] || {}).u1")
        == "NB",
    )
    scal(A, snap(B))
    check(
        "w drugą stronę: telefon ma wpis laptopa i nadal datę",
        A.evaluate("() => (getCurrentClass().attendance['2026-10-20#3'] || {}).u1")
        == "NB"
        and odszedl(A) == "2026-10-15",
        odszedl(A),
    )

    # 2. zdjęcie daty na laptopie -> telefon
    B.wait_for_timeout(30)
    B.evaluate("() => ustawOdszedl('u3', '')")
    B.wait_for_timeout(30)
    scal(A, snap(B))
    check("zdjęta data przeszła laptop -> telefon", odszedl(A) == "", odszedl(A))

    # 3. starsza kopia z datą nie wskrzesza jej
    scal(A, stara)
    check("stara kopia nie przywraca daty", odszedl(A) == "", odszedl(A))

    check("bez błędów strony", not ea and not eb, (ea + eb)[:3])
    browser.close()

httpd.shutdown()
print("WYNIK: %s" % ("PASS" if not FAILS else "FAIL %d" % len(FAILS)))
sys.exit(1 if FAILS else 0)
