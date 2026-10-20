# Scalanie zastępstw na okienkach (2026-10-21): dwa urządzenia = dwa konteksty przeglądarki.
# Poprawka i usunięcie przechodzą, usunięte nie wraca, stara kopia nie wskrzesza, kopia bez znaczników
# (ze starej wersji dziennika) nadal dokłada nowe, nagrobek przeżywa magazyn.
import sys
import json
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
PORT = 8779

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


K = "2026-09-04#8"
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

    A, ea = urzadzenie()
    B, eb = urzadzenie()
    snap = lambda p: json.loads(p.evaluate("() => JSON.stringify(snapshotData())"))
    scal = lambda p, d: p.evaluate(
        "(d) => { const w = scalKopie(d); save(); return w; }", d
    )
    okienko = lambda p: p.evaluate("(k) => state.zastepstwaOkienka[k] || null", K)

    # 1. nowe na A -> B
    A.evaluate("(k) => zastepstwoZapisz(null, k, '5b', 'Nowak')", K)
    A.wait_for_timeout(30)
    scal(B, snap(A))
    check("nowe dochodzi", okienko(B) == {"klasa": "5b", "zaKogo": "Nowak"}, okienko(B))
    # 2. poprawka na B -> A
    B.wait_for_timeout(30)
    B.evaluate("(k) => zastepstwoZapisz(null, k, '5c', 'Nowak')", K)
    w = scal(A, snap(B))
    check(
        "poprawka przechodzi",
        bool(okienko(A)) and okienko(A)["klasa"] == "5c",
        okienko(A),
    )
    check(
        "poprawka w liście nadpisanych",
        any(
            n["klasa"] == "okienko"
            and n["bylo"].startswith("5b")
            and n["jest"].startswith("5c")
            for n in w["nadpisane"]
        ),
        w["nadpisane"],
    )
    # 3. usunięcie na A -> B i nie wraca w drugą stronę
    A.wait_for_timeout(30)
    A.evaluate("(k) => zastepstwoZapisz(null, k, '', '')", K)
    scal(B, snap(A))
    check("usunięcie przechodzi", okienko(B) is None, okienko(B))
    scal(A, snap(B))
    check("usunięte nie wraca", okienko(A) is None, okienko(A))
    # 4. starsza kopia (sprzed usunięcia) nie wskrzesza
    stara = snap(A)
    stara["zastepstwaOkienka"] = {K: {"klasa": "5b", "zaKogo": "Nowak"}}
    stara["zastepstwaOkienkaT"] = {K: 1000}
    scal(A, stara)
    check("stara kopia nie wskrzesza", okienko(A) is None, okienko(A))
    # 5. kopia ze starej wersji dziennika (bez znaczników) — nowe okienko i tak dochodzi
    K2 = "2026-09-05#7"
    s2 = snap(A)
    s2.pop("zastepstwaOkienkaT", None)
    s2["zastepstwaOkienka"] = {K2: {"klasa": "4a", "zaKogo": ""}}
    scal(B, s2)
    check(
        "kopia bez znaczników: nowe dochodzi",
        B.evaluate("(k) => !!state.zastepstwaOkienka[k]", K2),
    )
    # 6. nagrobek przeżywa przeładowanie (magazyn)
    B.evaluate("() => save(true)")
    B.wait_for_timeout(500)
    B.reload()
    B.wait_for_timeout(500)
    B.evaluate("() => zamekOdblokuj('test-haslo-123')")
    B.wait_for_timeout(700)
    tk = B.evaluate("(k) => (state.zastepstwaOkienkaT || {})[k] || 0", K)
    check("nagrobek przeżył przeładowanie", tk > 0, tk)
    check("brak błędów JS", not ea and not eb, ea + eb)
    browser.close()

httpd.shutdown()
print("\nWYNIK:", "OK" if not FAILS else "BŁĘDY (%d FAIL)" % len(FAILS))
sys.exit(1 if FAILS else 0)
