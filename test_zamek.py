# Test zamka (Szczebel 5): apka startuje zaslonieta, magazyn przegladarki trzyma
# WYLACZNIE szyfrogram, PIN odslania po bezczynnosci, haslo po przeladowaniu,
# migracja jawne -> szyfrowane niczego nie gubi. Kluczowa asercja: w localStorage
# i IndexedDB NIE MA nazwiska dziecka.
import functools
import http.server
import json
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8769
HASLO = "haslo-test-1"
NAZWISKO = "Brzeczyszczykiewicz Grzegorz"
URL = "http://127.0.0.1:%d/dziennik_wf.html" % PORT

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
handler.log_message = lambda *a, **k: None  # type: ignore[attr-defined]
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


ZAMEK_STAN = (
    "() => ({ widoczny: document.getElementById('zamek').style.display !== 'none',"
    " tryb: zamek.tryb, otwarty: zamek.otwarty,"
    " inert: !!document.querySelector('.tabs').closest('[inert]') })"
)
MAGAZYN = (
    "async () => { const ls = localStorage.getItem('dziennik_wf_v1') || '';"
    " const idb = JSON.stringify(await idbCzytaj());"
    " return { ls, idb, wszystkie: Object.keys(localStorage).map(k => k + '=' + localStorage.getItem(k)).join('|') }; }"
)


def bez_nazwiska(m):
    return (
        NAZWISKO not in m["ls"]
        and "Brzeczy" not in m["idb"]
        and "Brzeczy" not in m["wszystkie"]
    )


with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # =================== A. Pierwsze uruchomienie (pusty magazyn) ===================
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_timeout(500)

    st = page.evaluate(ZAMEK_STAN)
    check(
        "start: apka zaslonieta, tryb ustawiania hasla",
        st["widoczny"] and st["tryb"] == "ustaw",
        st,
    )
    check("start: reszta strony nieaktywna (inert)", st["inert"], st)
    page.screenshot(path=str(SHOTS / "zamek_ustaw.png"))

    page.fill("#zamekInput", "abc")
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    check(
        "za krotkie haslo nie otwiera",
        page.evaluate(ZAMEK_STAN)["widoczny"],
        page.text_content("#zamekBlad"),
    )

    page.fill("#zamekInput", HASLO)
    page.click('#zamek button:has-text("Zamknij dziennik tym hasłem")')
    page.wait_for_timeout(800)
    st = page.evaluate(ZAMEK_STAN)
    check(
        "po ustawieniu hasla: apka otwarta, propozycja PIN-u",
        st["otwarty"] and st["tryb"] == "pin-ustaw" and not st["inert"],
        st,
    )
    page.screenshot(path=str(SHOTS / "zamek_pin_ustaw.png"))
    page.fill("#zamekInput", "12")
    page.click('#zamek button:has-text("Zapisz PIN")')
    page.wait_for_timeout(200)
    check(
        "PIN 2 cyfry odrzucony",
        page.evaluate("() => !zamek.pin") and page.evaluate(ZAMEK_STAN)["widoczny"],
    )
    page.fill("#zamekInput", "1234")
    page.click('#zamek button:has-text("Zapisz PIN")')
    page.wait_for_timeout(500)
    check(
        "PIN 1234 zapisany, zaslona zdjeta",
        page.evaluate("() => !!zamek.pin")
        and not page.evaluate(ZAMEK_STAN)["widoczny"],
    )

    # dane dziecka
    page.click('button.tab:has-text("Uczniowie")')
    page.click("#quickAddStudent")
    page.keyboard.type(NAZWISKO)
    page.keyboard.press("Enter")
    page.wait_for_timeout(600)
    check(
        "nazwisko jest w state",
        NAZWISKO in page.evaluate("() => state.students.map(s => s.name)"),
    )

    m = page.evaluate(MAGAZYN)
    check(
        "localStorage: szyfrogram (app=dziennik-wf-magazyn), NIE nazwisko",
        json.loads(m["ls"]).get("app") == "dziennik-wf-magazyn" and bez_nazwiska(m),
    )
    check(
        "IndexedDB: tez szyfrogram, bez nazwiska",
        "dziennik-wf-magazyn" in m["idb"] and "Brzeczy" not in m["idb"],
    )
    check(
        "hasla kopii nie ma jawnie w localStorage",
        "backup_pwd" not in m["wszystkie"] and HASLO not in m["wszystkie"],
    )
    check("PIN nie lezy jawnie w localStorage", "1234" not in m["wszystkie"])

    # -------- bezczynnosc -> PIN; klawisze nie docieraja do apki --------
    page.click('button.tab:has-text("Obecność")')
    page.evaluate("() => { zamekCfg.minuty = 0.015; }")  # 0.9 s
    page.click("h1")  # aktywnosc -> nowy timer z krotkim czasem
    page.wait_for_timeout(1600)
    st = page.evaluate(ZAMEK_STAN)
    check(
        "po bezczynnosci: zaslona wraca, tryb PIN",
        st["widoczny"] and st["tryb"] == "pin" and not st["otwarty"],
        st,
    )
    page.screenshot(path=str(SHOTS / "zamek_pin.png"))
    przed = page.evaluate(
        "() => JSON.stringify(state.attendance[state.currentDate] || {})"
    )
    page.keyboard.press("n")  # skrot statusu obecnosci
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    po = page.evaluate(
        "() => JSON.stringify(state.attendance[state.currentDate] || {})"
    )
    check(
        "skroty klawiszowe nie przechodza przez zaslone",
        przed == po and page.evaluate(ZAMEK_STAN)["widoczny"],
    )

    for i in range(5):
        page.fill("#zamekInput", "0000")
        page.wait_for_timeout(150)
    page.wait_for_timeout(300)
    st = page.evaluate(ZAMEK_STAN)
    check(
        "5 zlych PIN-ow -> wymagane haslo", st["tryb"] == "haslo" and st["widoczny"], st
    )

    page.fill("#zamekInput", HASLO)
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)
    check(
        "haslo po bezczynnosci otwiera (bez ponownego PBKDF2)",
        page.evaluate(ZAMEK_STAN)["otwarty"],
    )
    page.evaluate("() => { zamekCfg.minuty = 10; }")
    page.click("h1")

    # -------- PIN dziala --------
    page.click("button.tab-zamek")
    page.wait_for_timeout(200)
    check(
        "przycisk Zablokuj zaslania w trybie PIN",
        page.evaluate(ZAMEK_STAN)["tryb"] == "pin",
    )
    page.fill("#zamekInput", "1234")  # 4. cyfra odblokowuje sama
    page.wait_for_timeout(400)
    check("dobry PIN odslania", page.evaluate(ZAMEK_STAN)["otwarty"])

    # -------- karta w tle -> zaslona --------
    page.evaluate(
        "() => { Object.defineProperty(document, 'hidden', { get: () => true, configurable: true });"
        " document.dispatchEvent(new Event('visibilitychange')); }"
    )
    page.wait_for_timeout(200)
    check("karta w tle zaslania", page.evaluate(ZAMEK_STAN)["widoczny"])
    page.evaluate(
        "() => { Object.defineProperty(document, 'hidden', { get: () => false, configurable: true }); }"
    )
    page.fill("#zamekInput", "1234")
    page.wait_for_timeout(300)

    # -------- przeladowanie -> haslo, PIN nie wystarcza --------
    page.reload()
    page.wait_for_timeout(600)
    st = page.evaluate(ZAMEK_STAN)
    check(
        "po przeladowaniu: tryb HASLO (klucz nie przezyl)",
        st["widoczny"] and st["tryb"] == "haslo",
        st,
    )
    check(
        "po przeladowaniu state pusty do czasu odblokowania",
        page.evaluate("() => state.classes.length") == 0,
    )
    page.fill("#zamekInput", "zle-haslo-xx")
    page.keyboard.press("Enter")
    page.wait_for_timeout(600)
    check(
        "zle haslo nie otwiera",
        page.evaluate(ZAMEK_STAN)["widoczny"],
        page.text_content("#zamekBlad"),
    )
    page.fill("#zamekInput", HASLO)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)
    st = page.evaluate(ZAMEK_STAN)
    check(
        "dobre haslo otwiera, bez propozycji PIN-u (PIN jest)",
        st["otwarty"] and not st["widoczny"],
        st,
    )
    check(
        "dane po przeladowaniu w calosci",
        NAZWISKO in page.evaluate("() => state.students.map(s => s.name)"),
    )
    page.click("button.tab-zamek")
    page.fill("#zamekInput", "1234")
    page.wait_for_timeout(300)
    check(
        "PIN przezyl przeladowanie (lezy w szyfrogramie)",
        page.evaluate(ZAMEK_STAN)["otwarty"],
    )
    check("A: brak bledow JS", not errors, errors[:3])
    ctx.close()

    # =================== B. Migracja: jawne dane + stare haslo kopii ===================
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    jawne = {
        "classes": [
            {
                "id": "c1",
                "name": "3c",
                "school": "",
                "students": [
                    {"id": "u1", "name": NAZWISKO, "longTermReleased": False},
                    {"id": "u2", "name": "Nowak Piotr", "longTermReleased": False},
                ],
                "attendance": {"2026-09-10": {"u1": "NC"}},
                "measurements": {},
                "grades": {},
                "testFields": [],
            }
        ],
        "currentClassId": "c1",
        "savedAt": 1700000000000,
    }
    page.add_init_script(
        "localStorage.setItem('dziennik_wf_v1', %s); localStorage.setItem('dziennik_wf_backup_pwd', 'stare-haslo-9');"
        % json.dumps(json.dumps(jawne))
    )
    page.goto(URL)
    page.wait_for_timeout(600)
    st = page.evaluate(ZAMEK_STAN)
    check(
        "migracja: ekran ustawiania hasla", st["widoczny"] and st["tryb"] == "ustaw", st
    )
    check(
        "migracja: stare haslo kopii podstawione (ostatni pokaz)",
        page.input_value("#zamekInput") == "stare-haslo-9",
    )
    check(
        "migracja: nazwisko jeszcze NIE w state (zaslona przed danymi)",
        page.evaluate("() => state.classes.length") == 0,
    )
    page.screenshot(path=str(SHOTS / "zamek_migracja.png"))
    page.click('#zamek button:has-text("Zamknij dziennik tym hasłem")')
    page.wait_for_timeout(1000)
    st = page.evaluate(ZAMEK_STAN)
    check("migracja: otwarte", st["otwarty"], st)
    check(
        "migracja: dane w calosci",
        page.evaluate("() => state.students.map(s => s.name)")
        == [NAZWISKO, "Nowak Piotr"]
        and page.evaluate("() => (state.attendance['2026-09-10'] || {}).u1") == "NC",
    )
    m = page.evaluate(MAGAZYN)
    check(
        "migracja: jawne dane ZNIKNELY z localStorage i IndexedDB",
        bez_nazwiska(m) and json.loads(m["ls"]).get("app") == "dziennik-wf-magazyn",
    )
    check("migracja: jawne haslo kopii skasowane", "backup_pwd" not in m["wszystkie"])
    check(
        "migracja: haslo dziennika = stare haslo kopii",
        page.evaluate("() => zamek.haslo") == "stare-haslo-9",
    )
    page.reload()
    page.wait_for_timeout(500)
    page.fill("#zamekInput", "stare-haslo-9")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1000)
    check(
        "migracja: po przeladowaniu stare haslo kopii otwiera",
        page.evaluate(ZAMEK_STAN)["otwarty"]
        and NAZWISKO in page.evaluate("() => state.students.map(s => s.name)"),
    )
    check("B: brak bledow JS", not errors, errors[:3])
    ctx.close()
    browser.close()

httpd.shutdown()
print()
print("WYNIK: %s" % ("WSZYSTKO PASS" if not FAILS else ("%d FAIL" % len(FAILS))))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
