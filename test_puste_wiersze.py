# Test widm (2026-09-17, "nadmiarowy uczen w 4b wraca"): Enter w ostatnim wierszu
# Uczniow dopisuje pusty wiersz; porzucony ma zniknac przy wyjsciu z zakladki i po
# otwarciu dziennika. Wiersz pusty, ale z danymi (obecnosc/pomiar/ocena) ZOSTAJE.
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8771
URL = "http://127.0.0.1:%d/dziennik_wf.html" % PORT
HASLO = "haslo-test-1"

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


NAZWY = "() => state.students.map(s => s.name)"

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_timeout(500)
    page.evaluate("() => zamekPierwszeHaslo('%s')" % HASLO)
    page.wait_for_timeout(300)

    # swiezy start: 10 pustych wierszy zostaja (klasa bez zadnego nazwiska)
    check(
        "swiezy dziennik: 10 pustych wierszy do wpisania nietkniete",
        page.evaluate("() => state.students.length") == 10,
    )

    page.click('button.tab:has-text("Uczniowie")')
    page.click("#quickAddStudent")
    page.keyboard.type("Kowalski Jan")
    page.keyboard.press("Enter")
    page.keyboard.type("Nowak Piotr")
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    page.click('button.tab:has-text("Obecność")')
    page.wait_for_timeout(300)
    check(
        "po wpisaniu 2 nazwisk i wyjsciu: 8 pustych startowych sprzatniete",
        page.evaluate(NAZWY) == ["Kowalski Jan", "Nowak Piotr"],
        page.evaluate(NAZWY),
    )

    # objaw: Enter w polu ostatniego ucznia -> pusty wiersz-widmo
    page.click('button.tab:has-text("Uczniowie")')
    page.wait_for_timeout(200)
    ost = page.locator("#studentsBody tr").last.locator("input[type=text]").first
    ost.click()
    page.keyboard.press("End")
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    check(
        "Enter w ostatnim wierszu dopisuje pusty wiersz (jak dotad)",
        page.evaluate("() => state.students.length") == 3,
    )

    page.click('button.tab:has-text("Obecność")')
    page.wait_for_timeout(300)
    check(
        "wyjscie z zakladki: widmo znika",
        page.evaluate(NAZWY) == ["Kowalski Jan", "Nowak Piotr"],
        page.evaluate(NAZWY),
    )

    # pusty wiersz Z DANYMI zostaje (obecnosc wpisana bez nazwiska)
    page.evaluate(
        "() => { state.students.push({id:'u_bez', name:'', longTermReleased:false, height:'', weight:''});"
        " state.attendance[state.currentDate] = Object.assign(state.attendance[state.currentDate] || {}, {u_bez: 'NC'});"
        " state.students.push({id:'u_widmo', name:'', longTermReleased:false, height:'', weight:''}); save(); }"
    )
    page.wait_for_timeout(300)
    page.click('button.tab:has-text("Uczniowie")')
    page.wait_for_timeout(200)
    page.click('button.tab:has-text("Pomiary")')
    page.wait_for_timeout(300)
    ids = page.evaluate("() => state.students.map(s => s.id)")
    check(
        "pusty wiersz z obecnoscia ZOSTAJE, widmo bez danych znika",
        "u_bez" in ids and "u_widmo" not in ids,
        ids,
    )

    # widmo zapisane w magazynie (np. zamknieta karta przed sprzataniem) znika przy otwarciu
    page.evaluate(
        "() => { state.students.push({id:'u_widmo2', name:'', longTermReleased:false, height:'', weight:''}); return save(true); }"
    )
    page.reload()
    page.wait_for_timeout(500)
    page.evaluate("() => zamekOdblokuj('%s')" % HASLO)
    page.wait_for_timeout(500)
    ids = page.evaluate("() => state.students.map(s => s.id)")
    check(
        "po otwarciu dziennika widmo z magazynu znika",
        "u_widmo2" not in ids and "u_bez" in ids and len(ids) == 3,
        ids,
    )
    check("brak bledow JS", not errors, errors[:3])
    browser.close()

httpd.shutdown()
print()
print("WYNIK: %s" % ("WSZYSTKO PASS" if not FAILS else ("%d FAIL" % len(FAILS))))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
