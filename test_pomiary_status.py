# Test Szczebel 4.2: kratka wyniku przyjmuje liczbę ALBO status NB / NĆ (kody 'NB'/'NC' w danych),
# etykieta po wyjściu z kratki, karta ucznia pokazuje status zamiast liczby, Enter nadal schodzi w dół.
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8772

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


SEED = """() => {
  state.students.length = 0;
  state.students.push({id:'u1', name:'Jan Kowalski', longTermReleased:false, height:'152', weight:'44'});
  state.students.push({id:'u2', name:'Piotr Nowak', longTermReleased:false});
  state.students.push({id:'u3', name:'Adam Lis', longTermReleased:false});
  state.measurements.u1 = {jump:'165', beep:'6.5'};
  state.measurements.u3 = {jump:'NC'};
  state.attendance['2026-09-10'] = {u1:'C', u2:'C', u3:'BS'};
  save();
}"""

INP = "#pomiaryBody tr:nth-child(%d) td[data-field='%s'] input"

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1300, "height": 700}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('haslo-x1')")  # zamek (Szczebel 5): pusty magazyn -> pierwsze haslo
    page.evaluate(SEED)
    page.click('button.tab:has-text("Pomiary")')
    page.wait_for_timeout(200)

    check(
        "stara liczba renderuje się bez zmian",
        page.input_value(INP % (1, "jump")) == "165",
    )
    check(
        "zapisany kod NC renderuje się jako NĆ",
        page.input_value(INP % (3, "jump")) == "NĆ",
    )
    check(
        "kratka NĆ ma klasę wynik-nc",
        "wynik-nc" in page.get_attribute(INP % (3, "jump"), "class"),
    )

    # wpis 'nb' małymi
    page.click(INP % (2, "jump"))
    page.keyboard.type("nb")
    check(
        "w trakcie pisania: dane = 'NB'",
        page.evaluate("() => state.measurements.u2.jump") == "NB",
    )
    page.keyboard.press("Tab")
    page.wait_for_timeout(100)
    check("po wyjściu etykieta NB", page.input_value(INP % (2, "jump")) == "NB")
    check(
        "klasa wynik-nb", "wynik-nb" in page.get_attribute(INP % (2, "jump"), "class")
    )

    # 'nć' z ogonkiem i spacją -> NC
    page.fill(INP % (2, "shuttle"), " nć ")
    page.keyboard.press("Tab")
    page.wait_for_timeout(100)
    check(
        "'nć' -> dane 'NC'",
        page.evaluate("() => state.measurements.u2.shuttle") == "NC",
    )
    check("'nć' -> etykieta NĆ", page.input_value(INP % (2, "shuttle")) == "NĆ")

    # 'n.c.' też
    page.fill(INP % (2, "beep"), "n.c.")
    page.keyboard.press("Tab")
    check("'n.c.' -> 'NC'", page.evaluate("() => state.measurements.u2.beep") == "NC")

    # liczba z przecinkiem -> kropka, klasa pusta
    page.fill(INP % (2, "plank"), "12,5")
    page.keyboard.press("Tab")
    page.wait_for_timeout(100)
    check(
        "'12,5' -> '12.5'", page.evaluate("() => state.measurements.u2.plank") == "12.5"
    )
    check(
        "liczba bez klasy statusu",
        (page.get_attribute(INP % (2, "plank"), "class") or "") == "",
    )
    check("etykieta liczby = 12.5", page.input_value(INP % (2, "plank")) == "12.5")

    # nadpisanie statusu liczbą
    page.fill(INP % (2, "jump"), "150")
    page.keyboard.press("Tab")
    page.wait_for_timeout(100)
    check(
        "NB -> 150 (klasa znika)",
        page.evaluate("() => state.measurements.u2.jump") == "150"
        and (page.get_attribute(INP % (2, "jump"), "class") or "") == "",
    )

    # wyczyszczenie
    page.fill(INP % (2, "jump"), "")
    page.keyboard.press("Tab")
    check("puste = ''", page.evaluate("() => state.measurements.u2.jump") == "")

    # Enter nadal schodzi w dół tej samej kolumny (pole tekstowe zamiast number)
    page.click(INP % (1, "beep"))
    page.keyboard.press("Enter")
    check(
        "Enter -> ta sama kolumna, wiersz 2",
        page.evaluate(
            '() => document.activeElement === document.querySelector("%s")'
            % (INP % (2, "beep"))
        ),
    )

    # trwałość po reload
    page.reload()
    page.wait_for_timeout(400)
    page.evaluate("() => zamekOdblokuj('haslo-x1')")  # zamek: po przeladowaniu klucz nie zyje
    page.wait_for_timeout(300)
    page.click('button.tab:has-text("Pomiary")')
    page.wait_for_timeout(200)
    check("po reload NĆ w shuttle u2", page.input_value(INP % (2, "shuttle")) == "NĆ")
    page.screenshot(path=str(SHOTS / "pomiary_status.png"))

    # karta ucznia: status zamiast liczby
    page.click('button.tab:has-text("Statystyki")')
    page.wait_for_timeout(200)
    page.evaluate("() => openKarta('u2')")
    page.wait_for_timeout(300)
    karta = page.evaluate("() => document.getElementById('kartaBody').innerText")
    check(
        "karta: NĆ z opisem",
        "NĆ" in karta and "był, nie ćwiczył" in karta,
        karta[-400:],
    )
    check("karta: liczba 12.5 nadal", "12.5" in karta)

    check("brak błędów JS", errors == [], errors)
    browser.close()
httpd.shutdown()
print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
