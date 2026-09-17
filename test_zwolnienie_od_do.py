# Test Szczebel 4.3: zwolnienie lekarskie OD–DO per uczeń. W dniu z okresu: Obecność podpowiada „ZW?",
# „Zapisz lekcję" nadaje ZW zamiast C (ręczny status wygrywa), „Kopiuj dla VULCAN" eksportuje ZW;
# po dacie DO uczeń wraca sam; stare dane bez pola releases czytają się bez migracji.
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8773

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
  state.students.push({id:'u1', name:'Jan Kowalski', longTermReleased:false});            // bez pola releases (stare dane)
  state.students.push({id:'u2', name:'Piotr Nowak', longTermReleased:false, releases:[{od:'2026-09-10', do:'2026-09-20'}]});
  state.students.push({id:'u3', name:'Adam Lis', longTermReleased:false, releases:[{od:'2026-09-10', do:'2026-09-20'}]});
  state.students.push({id:'u4', name:'Karol Bąk', longTermReleased:true});
  state.currentDate = '2026-09-15';
  state.attendance['2026-09-15'] = { u3: 'NB' };   // ręczny status u3 wygrywa nad zwolnieniem
  save(); renderAttendance();
}"""

STATUS_BTN = "#attendanceBody tr[data-sid='%s'] .status-btn"

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1300, "height": 800}
    )
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate(SEED)
    page.wait_for_timeout(200)

    check(
        "isReleasedOn w okresie",
        page.evaluate("() => isReleasedOn(state.students[1], '2026-09-15')") is True,
    )
    check(
        "isReleasedOn granice OD i DO włącznie",
        page.evaluate(
            "() => isReleasedOn(state.students[1], '2026-09-10') && isReleasedOn(state.students[1], '2026-09-20')"
        )
        is True,
    )
    check(
        "isReleasedOn po DO = false",
        page.evaluate("() => isReleasedOn(state.students[1], '2026-09-21')") is False,
    )
    check(
        "brak pola releases = false, bez błędu",
        page.evaluate("() => isReleasedOn(state.students[0], '2026-09-15')") is False,
    )

    check(
        "Obecność: u2 pokazuje ZW?",
        page.text_content(STATUS_BTN % "u2").strip() == "ZW?",
    )
    check("Obecność: u1 pusty —", page.text_content(STATUS_BTN % "u1").strip() == "—")
    check(
        "Obecność: u3 ręczne NB zostaje",
        page.text_content(STATUS_BTN % "u3").strip() == "NB",
    )
    check(
        "wiersz u2 ma klasę released-period",
        "released-period"
        in (page.get_attribute("#attendanceBody tr[data-sid='u2']", "class") or ""),
    )
    bar = page.text_content("#saveBarStatus")
    check("pasek zapisu wspomina ZW", "ZW" in bar and "1 ze zwolnieniem" in bar, bar)
    page.screenshot(path=str(SHOTS / "zwolnienie_obecnosc.png"))

    # Zapisz lekcję -> u1 C, u2 ZW, u3 NB, u4 (długoterminowy) bez wpisu
    page.evaluate("() => finalizeLesson()")
    page.wait_for_timeout(200)
    msg = page.text_content("#confirmModal, .modal, body")
    check(
        "okno potwierdzenia wymienia ZW dla Piotr Nowak",
        "ZW" in msg and "Piotr Nowak" in msg,
    )
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    day = page.evaluate("() => state.attendance['2026-09-15']")
    check(
        "po zapisie: u1=C, u2=ZW, u3=NB, u4 brak",
        day == {"u1": "C", "u2": "ZW", "u3": "NB"},
        day,
    )

    # Kopiuj dla VULCAN w dniu z okresu, uczeń bez statusu -> ZW
    page.evaluate(
        "() => { state.currentDate = '2026-09-12'; state.attendance['2026-09-12'] = { u1: 'C' }; save(); renderAttendance(); }"
    )
    page.click('button:has-text("Kopiuj dla VULCAN")')
    page.wait_for_timeout(300)
    clip = (
        page.evaluate("() => navigator.clipboard.readText()")
        .replace("\r", "")
        .split("\n")
    )
    check(
        "VULCAN: u2 i u3 bez statusu -> ZW, u4 ZW, u1 C pominięty",
        sorted(clip) == sorted(["Piotr Nowak\tZW", "Adam Lis\tZW", "Karol Bąk\tZW"]),
        clip,
    )

    # Po dacie DO uczeń wraca sam: 2026-09-25 -> u2 pusty '—', Zapisz daje C
    page.evaluate(
        "() => { state.currentDate = '2026-09-25'; save(); renderAttendance(); }"
    )
    page.wait_for_timeout(100)
    check(
        "po DO: u2 pokazuje — (nie ZW?)",
        page.text_content(STATUS_BTN % "u2").strip() == "—",
    )
    page.evaluate("() => finalizeLesson()")
    page.wait_for_timeout(200)
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    check(
        "po DO: Zapisz daje u2 = C",
        page.evaluate("() => state.attendance['2026-09-25'].u2") == "C",
    )

    # Zakładka Uczniowie: chip + dodawanie / usuwanie okresu
    page.click('button.tab:has-text("Uczniowie")')
    page.wait_for_timeout(200)
    chips = page.evaluate(
        "() => [...document.querySelectorAll('#studentsBody tr:nth-child(2) .rel-chip')].map(c => c.textContent.replace('×','').trim())"
    )
    check("chip 10.09–20.09 u Piotra", chips == ["10.09–20.09"], chips)
    page.fill("#relOd_u1", "2026-10-01")
    page.fill("#relDo_u1", "2026-10-14")
    page.click("#studentsBody tr:nth-child(1) .rel-form button")
    page.wait_for_timeout(200)
    check(
        "dodany okres u Jana",
        page.evaluate("() => JSON.stringify(state.students[0].releases)")
        == '[{"od":"2026-10-01","do":"2026-10-14"}]',
    )
    page.fill("#relOd_u1", "2026-11-10")
    page.fill("#relDo_u1", "2026-11-01")
    page.click("#studentsBody tr:nth-child(1) .rel-form button")
    page.wait_for_timeout(200)
    check(
        "OD > DO odrzucone",
        page.evaluate("() => state.students[0].releases.length") == 1,
    )
    page.click("#studentsBody tr:nth-child(1) .rel-chip button")
    page.wait_for_timeout(200)
    check(
        "usunięcie okresu",
        page.evaluate("() => state.students[0].releases.length") == 0,
    )
    page.screenshot(path=str(SHOTS / "zwolnienie_uczniowie.png"))

    # trwałość po reload
    page.reload()
    page.wait_for_timeout(400)
    check(
        "po reload releases u2 zachowane",
        page.evaluate("() => state.students[1].releases[0].do") == "2026-09-20",
    )

    # karta ucznia pokazuje okresy
    page.click('button.tab:has-text("Statystyki")')
    page.evaluate("() => openKarta('u2')")
    page.wait_for_timeout(300)
    karta = page.evaluate("() => document.getElementById('kartaBody').innerText")
    check(
        "karta: zwolnienia OD–DO w nagłówku", "zwolnienia OD–DO: 10.09–20.09" in karta
    )

    check("brak błędów JS", errors == [], errors)
    browser.close()
httpd.shutdown()
print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
