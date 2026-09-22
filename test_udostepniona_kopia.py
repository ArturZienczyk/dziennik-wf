# -*- coding: utf-8 -*-
# Bramka dla „Udostepnij -> Dziennik WF" (Web Share Target, 23.09).
# Artur: kopia z laptopa przychodzi WhatsAppem, a Android nie pokazuje plikow WhatsAppa w wyborze
# pliku - trzeba bylo zapisywac do Pobranych i szukac. Teraz WhatsApp udostepnia plik prosto do
# dziennika: sw.js odklada go do cache, dziennik po odblokowaniu pyta o haslo i scala.
# Pilnuje: manifest zglasza cel udostepniania dla .txt, sw.js przyjmuje POST i przekierowuje,
# dziennik odbiera kopie RAZ (po odblokowaniu), scala ja i czysci adres.
# Czego NIE sprawdza: samego menu Androida / WhatsAppa - to tylko na telefonie.
import json
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8831
HASLO = "tajne-haslo-2026"
UCZEN = "Kopiowy Z Laptopa"
NAZWA = "dziennik-wf_WYSLANA_SZYFROWANA_2026-09-23_01-10.enc.txt"
PAGE = "http://127.0.0.1:%d/dziennik_wf.html" % PORT

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


# 1. Manifest: cel udostepniania w zakresie aplikacji, przyjmuje .txt (Chrome nie udostepnia .json)
m = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
st = m.get("share_target") or {}
pliki = (st.get("params") or {}).get("files") or [{}]
check(
    "manifest: share_target POST multipart",
    st.get("method") == "POST" and st.get("enctype") == "multipart/form-data",
    st,
)
check(
    "manifest: akcja z parametrem udostepniona-kopia",
    "udostepniona-kopia" in st.get("action", ""),
    st.get("action"),
)
check(
    "manifest: pole pliku 'kopia' przyjmuje text/plain",
    pliki[0].get("name") == "kopia" and "text/plain" in pliki[0].get("accept", []),
    pliki,
)

with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # 2. Laptop: kopia z uczniem, ktorego telefon nie ma
    lap = browser.new_context().new_page()
    lap.goto(PAGE)
    lap.wait_for_timeout(400)
    lap.evaluate("(h) => zamekPierwszeHaslo(h)", HASLO)
    lap.evaluate("() => { state.students.length = 0; save(); renderStudents(); }")
    lap.click('button:has-text("Uczniowie")')
    lap.click("#quickAddStudent")
    lap.keyboard.type(UCZEN)
    lap.keyboard.press("Enter")
    lap.wait_for_timeout(200)
    tekst = lap.evaluate("(h) => encryptSnapshot(h)", HASLO)

    # 3. Telefon: swiezy dziennik z service workerem
    ctx = browser.new_context()
    tel = ctx.new_page()
    errors = []
    tel.on("pageerror", lambda e: errors.append(str(e)))
    tel.goto(PAGE)
    tel.wait_for_timeout(400)
    tel.evaluate("(h) => zamekPierwszeHaslo(h)", HASLO)
    tel.evaluate("() => navigator.serviceWorker.ready")
    tel.wait_for_function("() => !!navigator.serviceWorker.controller", timeout=10000)

    # 4. „Udostepnij -> Dziennik WF": tak samo jak Android - POST multipart na akcje z manifestu
    odp = tel.evaluate(
        """async (a) => { const fd = new FormData(); fd.append('title', 'Kopia dziennika WF');
             fd.append('kopia', new File([a.t], a.n, { type: 'text/plain' }));
             const r = await fetch('./dziennik_wf.html?udostepniona-kopia', { method: 'POST', body: fd });
             return { redirected: r.redirected, url: r.url }; }""",
        {"t": tekst, "n": NAZWA},
    )
    check(
        "sw.js przyjmuje plik i przekierowuje do dziennika",
        "udostepniona-kopia=1" in odp["url"],
        odp,
    )

    # 5. Otwarcie po udostepnieniu: zamek -> haslo -> pytanie o haslo KOPII z nazwa pliku
    tel.goto(PAGE + "?udostepniona-kopia=1")
    tel.wait_for_timeout(500)
    check(
        "przed odblokowaniem nie pyta o haslo kopii (dane jeszcze zamkniete)",
        not tel.locator("#pwdPromptModal").evaluate(
            "e => e.classList.contains('active')"
        ),
    )
    tel.evaluate("(h) => zamekOdblokuj(h)", HASLO)
    tel.wait_for_timeout(600)
    aktywne = tel.locator("#pwdPromptModal").evaluate(
        "e => e.classList.contains('active')"
    )
    check("po odblokowaniu pyta o haslo kopii", aktywne)
    check(
        "pytanie pokazuje nazwe udostepnionego pliku",
        NAZWA in tel.inner_text("#pwdPromptHint"),
        tel.inner_text("#pwdPromptHint"),
    )
    check(
        "adres wyczyszczony z ?udostepniona-kopia",
        "udostepniona-kopia" not in tel.url,
        tel.url,
    )
    tel.fill("#pwdPromptInput", HASLO)
    tel.click("#pwdPromptOk")
    tel.wait_for_timeout(1500)
    # ta sama droga co „Wczytaj": najpierw okno „Wczytaj dane — zostanie SCALONA", potem wynik
    check(
        "przed scaleniem pyta jak przy zwyklym wczytaniu",
        "SCALONA" in tel.inner_text("#confirmMessage"),
        tel.inner_text("#confirmTitle"),
    )
    tel.evaluate("() => confirmOk()")
    tel.wait_for_timeout(800)
    check(
        "scalenie: okno „Scalono kopie”",
        "Scalono" in tel.inner_text("#confirmTitle"),
        tel.inner_text("#confirmTitle"),
    )
    check(
        "scalenie: uczen z laptopa jest na telefonie",
        tel.evaluate(
            "(n) => state.classes.some(c => (c.students || []).some(s => s.name === n))",
            UCZEN,
        ),
    )
    tel.evaluate("() => confirmOk()")

    # 6. Odebrana RAZ: kolejne otwarcie nie pyta znowu
    tel.goto(PAGE)
    tel.wait_for_timeout(500)
    tel.evaluate("(h) => zamekOdblokuj(h)", HASLO)
    tel.wait_for_timeout(600)
    check(
        "kopia odebrana raz - drugie otwarcie nie pyta o nia",
        not tel.locator("#pwdPromptModal").evaluate(
            "e => e.classList.contains('active')"
        ),
    )
    check("bez bledow JS", not errors, errors[:3])
    browser.close()

httpd.shutdown()
if FAILS:
    print(
        "\nWYNIK: FAIL - %d: %s" % (len(FAILS), json.dumps(FAILS, ensure_ascii=False))
    )
    sys.exit(1)
print("\nWYNIK: PASS - kopia z WhatsAppa wchodzi prosto do dziennika")
