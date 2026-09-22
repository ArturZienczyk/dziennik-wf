# -*- coding: utf-8 -*-
# Bramka dla przycisku „Wyslij kopie" (handoff „jedna droga kopii", punkt 1).
# Pilnuje dwoch rzeczy, ktore lamia sie po cichu:
#   1. to, co wychodzi z apki do systemowego okna udostepniania, JEST ZASZYFROWANE
#      (wysylka mailem jest bezpieczna wylacznie dlatego),
#   2. przegladarka bez navigator.share nie zostawia userowi milczacego przycisku —
#      kopia i tak powstaje zwykla droga.
import json
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8799
HASLO = "tajne-haslo-2026"
NAZWISKO = "Brzeczyszczykiewicz Grzegorz"

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright

FAILS = []


def check(name, cond, detail=""):
    print("[%s] %s %s" % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name + " :: " + str(detail))


STUB = """
() => {
  window.__udostepnione = null;
  navigator.canShare = (d) => !!(d && d.files && d.files.length);
  navigator.share = async (d) => {
    const f = d.files[0];
    window.__udostepnione = { name: f.name, type: f.type, text: await f.text(), title: d.title };
  };
}
"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(service_workers="block", accept_downloads=True,
                              viewport={"width": 1500, "height": 1000})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('%s')" % HASLO)
    page.evaluate("() => { state.students.length = 0; save(); renderStudents(); renderAttendance(); }")

    page.click('button:has-text("Uczniowie")')
    page.click("#quickAddStudent")
    page.keyboard.type(NAZWISKO)
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)

    check("przycisk Wyslij kopie jest w pasku Uczniowie",
          page.query_selector('#tab-uczniowie button:has-text("Wyślij kopię")') is not None)

    # ---------- 0. ZAPADKA „jedna droga kopii" (22.09) ----------
    # Inwariant, nie gust: pasek Uczniowie mial 12 przyciskow, z tego 8 wokol kopii i hasel —
    # nauczyciel nie wiedzial, w ktory kliknac. Czynnosci zostaja dwie (wyslij / kopia zapasowa),
    # reszta mieszka w oknie. Ta bramka pilnuje, zeby pasek nie zarosl z powrotem.
    pasek = page.eval_on_selector_all(
        "#tab-uczniowie .toolbar button",
        "bs => bs.filter(b => b.offsetParent !== null).map(b => b.textContent.trim())")
    check("pasek Uczniowie ma najwyzej 5 przyciskow", len(pasek) <= 5, pasek)
    wejscia = [t for t in pasek if "kopi" in t.lower()]
    check("do kopii prowadza dokladnie dwa wejscia: Wyslij + Kopia zapasowa",
          sorted(wejscia) == sorted(["📤 Wyślij kopię", "📦 Kopia zapasowa"]), wejscia)
    zargon = [t for t in pasek if "JSON" in t or "szyfrowan" in t.lower() or "Kopia 2" in t]
    check("w pasku nie ma slowa z innego swiata (JSON / szyfrowana / Kopia 2)", not zargon, zargon)

    page.click('#tab-uczniowie button:has-text("Kopia zapasowa")')
    page.wait_for_timeout(300)
    check("okno kopii otwiera sie ciche: lista zwinieta, Chrome o nic nie pyta",
          page.eval_on_selector("#kopiaListaBox", "e => e.style.display === 'none'"))
    check("Ustawienia kopii sa zwiniete — konfiguracja nie udaje czynnosci",
          page.eval_on_selector("#kopiaModal details", "e => !e.open"))
    czynnosci = page.eval_on_selector_all(
        "#kopiaModal > .modal > div:nth-of-type(2) button",
        "bs => bs.map(b => b.textContent.trim())")
    check("okno oferuje trzy czynnosci nazwane czasownikiem", len(czynnosci) == 3, czynnosci)
    check("kazda czynnosc zaczyna sie od tego, co sie stanie",
          all(any(w in t for w in ("Wyślij", "Zapisz", "Wczytaj")) for t in czynnosci), czynnosci)
    page.click('#kopiaModal button:has-text("Zamknij")')
    page.wait_for_timeout(200)

    # ---------- 1. Droga glowna: navigator.share dostaje ZASZYFROWANY plik ----------
    page.evaluate(STUB)
    page.click('#tab-uczniowie button:has-text("Wyślij kopię")')
    page.wait_for_timeout(1500)
    wys = page.evaluate("() => window.__udostepnione")
    check("wysylka oddaje plik do systemowego okna udostepniania", wys is not None)
    if wys:
        check("nazwa wyslanego pliku mowi, ze jest szyfrowany",
              "SZYFROWANA" in wys["name"] and wys["name"].endswith(".enc.json"), wys["name"])
        check("wyslany plik NIE ZAWIERA nazwiska dziecka",
              NAZWISKO not in wys["text"] and "Brzeczy" not in wys["text"])
        obj = json.loads(wys["text"])
        check("wyslany plik ma format AES-GCM + PBKDF2",
              obj.get("app") == "dziennik-wf-enc" and obj.get("cipher") == "AES-GCM-256"
              and len(obj.get("ct", "")) > 40,
              {k: obj.get(k) for k in ("app", "cipher", "kdf")})
        wrocilo = page.evaluate(
            """async ([txt, pwd]) => {
                 const d = await decryptBackup(txt, pwd);
                 return d.classes[0].students.map(s => s.name);
               }""", [wys["text"], HASLO])
        check("wyslana kopia da sie odszyfrowac haslem dziennika (dane sa w srodku)",
              NAZWISKO in wrocilo, wrocilo)

    check("wysylka nie pyta o haslo drugi raz",
          page.query_selector("#pwdPromptModal.modal-bg.active") is None)

    # ---------- 2. Anulowanie okna udostepniania to nie blad ----------
    page.evaluate("""() => {
        navigator.share = async () => { const e = new Error('cancel'); e.name = 'AbortError'; throw e; };
    }""")
    anulowane = "BRAK"
    try:
        with page.expect_download(timeout=2500):
            page.click('#tab-uczniowie button:has-text("Wyślij kopię")')
        anulowane = "POWSTAL PLIK"
    except Exception:
        pass
    check("zamkniecie okna udostepniania nie zapisuje kopii awaryjnie", anulowane == "BRAK", anulowane)

    # ---------- 3. Fallback: przegladarka bez share zapisuje kopie jak dotad ----------
    page.evaluate("() => { delete navigator.canShare; delete navigator.share; }")
    with page.expect_download(timeout=15000) as dl_info:
        page.click('#tab-uczniowie button:has-text("Wyślij kopię")')
    dl = dl_info.value
    check("bez navigator.share kopia i tak powstaje (przycisk nie milczy)",
          "SZYFROWANA" in dl.suggested_filename, dl.suggested_filename)
    fb = SHOTS / "wyslij_fallback.enc.json"
    dl.save_as(str(fb))
    check("kopia z fallbacku tez NIE ZAWIERA nazwiska dziecka",
          NAZWISKO not in fb.read_text(encoding="utf-8"))

    check("brak bledow JS w konsoli", not errors, errors[:3])
    browser.close()

httpd.shutdown()
print()
if FAILS:
    print("FAIL: %d" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("WYNIK: OK — wszystkie bramki wysylki kopii zielone")
