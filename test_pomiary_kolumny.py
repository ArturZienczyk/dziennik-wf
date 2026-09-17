# Test Szczebel 4.1: przypinanie kolumny testu w Pomiarach (tuż za nazwiskiem na czas wpisywania).
# Kolejność nazwisk niezmienna, dane pomiarów nietknięte, przypięcie przeżywa przeładowanie strony.
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8771

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
  localStorage.setItem('dziennik_wf_backup_pwd', 'x-1');
  state.students.push({id:'u1', name:'Jan Kowalski', longTermReleased:false, height:'152', weight:'44'});
  state.students.push({id:'u2', name:'Piotr Nowak', longTermReleased:false});
  state.students.push({id:'u3', name:'Adam Lis', longTermReleased:false});
  state.measurements.u1 = {jump:'165', beep:'6.5'};
  getTestFields().push({id:'pompki', name:'Pompki', unit:'x'});
  save();
}"""

HEADERS = "() => [...document.querySelectorAll('.pomiary-table thead th')].map(th => th.firstChild.textContent.trim())"
NAMES = "() => [...document.querySelectorAll('#pomiaryBody tr td:nth-child(2)')].map(td => td.textContent.trim())"
ROW1_FIELDS = "() => [...document.querySelectorAll('#pomiaryBody tr:first-child td')].map(td => td.dataset.field || td.textContent.trim())"

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
    page.evaluate(SEED)
    page.click('button.tab:has-text("Pomiary")')
    page.wait_for_timeout(200)

    h0 = page.evaluate(HEADERS)
    check(
        "start: testy za Wzrost/Waga",
        h0[:4] == ["#", "Uczeń", "Wzrost [cm]", "Waga [kg]"]
        and "Beep test [stage]" in h0[4:],
        h0,
    )
    check("5 kolumn testów (4 domyślne + Pompki)", len(h0) == 9, h0)
    check("brak przypiętej na starcie", page.evaluate("() => getPinnedTest()") is None)

    # przypnij Beep test
    page.click('th[data-field="beep"] .test-pin')
    page.wait_for_timeout(200)
    h1 = page.evaluate(HEADERS)
    check(
        "po przypięciu: Beep tuż za Uczeń",
        h1[:3] == ["#", "Uczeń", "Beep test [stage]"],
        h1,
    )
    check("Wzrost/Waga za przypiętą", h1[3:5] == ["Wzrost [cm]", "Waga [kg]"], h1)
    check(
        "reszta testów bez Beep, w starej kolejności",
        h1[5:] == ["Skok w dal [cm]", "Bieg 10×5 [s]", "Deska [s]", "Pompki [x]"],
        h1,
    )
    check(
        "nazwiska w tej samej kolejności",
        page.evaluate(NAMES) == ["Jan Kowalski", "Piotr Nowak", "Adam Lis"],
    )
    r1 = page.evaluate(ROW1_FIELDS)
    check(
        "wiersz 1: komórka beep na 3. pozycji", r1[2] == "beep" and r1[3] == "152", r1
    )
    check(
        "wiersz: komórka beep ma klasę pinned",
        page.evaluate(
            "() => document.querySelector('#pomiaryBody tr td.pinned').dataset.field"
        )
        == "beep",
    )
    check(
        "wartość beep u1 widoczna w przypiętej",
        page.evaluate(
            "() => document.querySelector('#pomiaryBody tr td.pinned input').value"
        )
        == "6.5",
    )
    check(
        "fokus wskoczył w 1. przypiętą kratkę",
        page.evaluate(
            "() => document.activeElement === document.querySelector('#pomiaryBody tr td.pinned input')"
        ),
    )

    # wpis w przypiętej kolumnie trafia do właściwego pola u właściwego ucznia
    page.fill("#pomiaryBody tr:nth-child(2) td.pinned input", "7.1")
    page.wait_for_timeout(100)
    check(
        "wpis w przypiętej → measurements.u2.beep",
        page.evaluate("() => state.measurements.u2 && state.measurements.u2.beep")
        == "7.1",
    )
    check(
        "dane innych pól nietknięte",
        page.evaluate("() => state.measurements.u1.jump") == "165",
    )
    check(
        "testFields kolejność nietknięta",
        page.evaluate("() => getTestFields().map(f=>f.id)")
        == ["jump", "shuttle", "beep", "plank", "pompki"],
    )
    page.screenshot(path=str(SHOTS / "pomiary_przypieta.png"))

    # przeładowanie: przypięcie przeżywa (per klasa, w save)
    page.reload()
    page.wait_for_timeout(400)
    page.click('button.tab:has-text("Pomiary")')
    page.wait_for_timeout(200)
    check(
        "po reload nadal przypięta",
        page.evaluate(HEADERS)[2] == "Beep test [stage]",
        page.evaluate(HEADERS),
    )

    # odepnij
    page.click('th[data-field="beep"] .test-pin')
    page.wait_for_timeout(200)
    h2 = page.evaluate(HEADERS)
    check("po odpięciu: wraca stara kolejność", h2 == h0, h2)
    check(
        "brak td.pinned",
        page.evaluate(
            "() => document.querySelectorAll('#pomiaryBody td.pinned').length"
        )
        == 0,
    )

    # usunięcie przypiętego testu nie psuje renderu
    page.click('th[data-field="pompki"] .test-pin')
    page.wait_for_timeout(150)
    page.evaluate(
        "() => { const f = getTestFields(); f.splice(f.findIndex(x => x.id === 'pompki'), 1); save(); renderPomiary(); }"
    )
    page.wait_for_timeout(150)
    check(
        "usunięty przypięty test → brak przypięcia, render OK",
        page.evaluate("() => getPinnedTest()") is None
        and len(page.evaluate(HEADERS)) == 8,
        page.evaluate(HEADERS),
    )

    check("brak błędów JS", errors == [], errors)
    browser.close()
httpd.shutdown()
print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
