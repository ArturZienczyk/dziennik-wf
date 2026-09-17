# Test end-to-end trybu klawiatury w dzienniku WF.
# Steruje WYLACZNIE klawiatura, stan sprawdza w localStorage.
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8765

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


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1500, "height": 1000}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on(
        "console",
        lambda m: errors.append("console.error: " + m.text)
        if m.type == "error"
        else None,
    )

    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")  # zamek (Szczebel 5): pusty magazyn -> pierwsze haslo
    # czysta klasa: kasuje 10 pustych wierszy startowych
    # + haslo kopii ustawione z gory, zeby auto-kopia nie przerywala testu
    #   (sama mechanika kopii ma wlasny test: test_kopie.py)
    page.evaluate(
        "() => { state.students.length = 0; save(); renderStudents(); renderAttendance();"
        " }"
    )

    def state():
        return page.evaluate('() => zamekStanZapisany()')

    def cls():
        return state()["classes"][0]

    # ---------- 1. UCZNIOWIE: przepisywanie z kartki ciagiem ----------
    page.click('button:has-text("Uczniowie")')
    page.click("#quickAddStudent")
    for name in ["Kowalski Jan", "Nowak Piotr", "Wisniewski Adam", "Zielinski Marek"]:
        page.keyboard.type(name)
        page.keyboard.press("Enter")

    names = [s["name"] for s in cls()["students"]]
    check(
        "quickAdd: 4 nazwiska wpisane ciagiem, bez myszy",
        names == ["Kowalski Jan", "Nowak Piotr", "Wisniewski Adam", "Zielinski Marek"],
        names,
    )
    check(
        "quickAdd: pole czysci sie po Enter", page.input_value("#quickAddStudent") == ""
    )
    check(
        "quickAdd: fokus zostaje w polu",
        page.evaluate("() => document.activeElement.id") == "quickAddStudent",
    )

    # Enter na ostatnim wierszu tabeli dopisuje kolejnego ucznia
    rows = page.query_selector_all("#studentsBody tr")
    rows[-1].query_selector_all("input")[0].click()
    page.keyboard.press("Enter")
    page.wait_for_timeout(150)
    check(
        "tabela: Enter na ostatnim wierszu dodaje nowy wiersz",
        len(page.query_selector_all("#studentsBody tr")) == 5,
    )
    page.keyboard.type("Dabrowski Igor")
    page.wait_for_timeout(200)
    check(
        "tabela: nowy wiersz przyjal nazwisko",
        [s["name"] for s in cls()["students"]][-1] == "Dabrowski Igor",
    )

    # Enter w srodku tabeli schodzi wiersz nizej
    page.query_selector_all("#studentsBody tr")[0].query_selector_all("input")[
        0
    ].click()
    page.keyboard.press("Enter")
    val = page.evaluate("() => document.activeElement.value")
    check(
        "tabela: Enter schodzi wiersz nizej (ta sama kolumna)",
        val == "Nowak Piotr",
        val,
    )

    ids = [s["id"] for s in cls()["students"]]

    # ---------- 2. OBECNOSC: tylko klawiatura ----------
    page.click('button:has-text("Obecność")')
    page.wait_for_timeout(200)
    page.click("h1")  # fokus poza polem tekstowym
    check(
        "obecnosc: kursor startuje na 1. uczniu",
        page.evaluate(
            '() => document.querySelector("#attendanceBody tr.kbd-active").dataset.sid'
        )
        == ids[0],
    )

    page.keyboard.press("n")  # 1. uczen NC, kursor schodzi
    page.keyboard.press("b")  # 2. uczen BS
    page.keyboard.press("w")  # 3. uczen NB
    page.keyboard.press("ArrowDown")  # 4. pomijamy
    page.keyboard.press("5")  # 5. uczen NU
    page.wait_for_timeout(250)

    c = cls()
    date = list(c["attendance"].keys())[0]
    got = [c["attendance"][date].get(i) for i in ids]
    check(
        "obecnosc: litery nadaja status i kursor schodzi sam",
        got == ["NC", "BS", "NB", None, "NU"],
        got,
    )

    # spoznienie na 3. uczniu (NB)
    page.keyboard.press("ArrowUp")
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(100)
    check(
        "obecnosc: strzalki wracaja na wlasciwy wiersz",
        page.evaluate(
            '() => document.querySelector("#attendanceBody tr.kbd-active").dataset.sid'
        )
        == ids[2],
    )
    page.keyboard.press("s")
    page.wait_for_timeout(200)
    cell = page.evaluate(
        "(id) => attRead(state.attendance[state.currentDate][id])", ids[2]
    )
    check(
        "obecnosc: klawisz s dokleja spoznienie, status zostaje",
        cell.get("s") == "NB" and cell.get("sp") is True,
        cell,
    )

    page.keyboard.press("0")
    page.wait_for_timeout(200)
    check(
        "obecnosc: 0 czysci status biezacego ucznia",
        ids[2] not in cls()["attendance"][date],
    )

    page.screenshot(path=str(SHOTS / "shot_obecnosc.png"), full_page=True)

    # Enter zapisuje lekcje, drugi Enter potwierdza okno
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    check(
        "obecnosc: Enter otwiera potwierdzenie",
        page.query_selector("#confirmModal.modal-bg.active") is not None,
    )
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)
    check(
        "modal: Enter zatwierdza bez myszy",
        page.query_selector("#confirmModal.modal-bg.active") is None,
    )
    check(
        "obecnosc: gotowe haslo kopii nie przerywa codziennego zapisu",
        page.query_selector("#pwdPromptModal.modal-bg.active") is None,
    )
    day = cls()["attendance"][date]
    check(
        "obecnosc: reszta klasy dostaje C",
        len(day) == 5 and day[ids[2]] == "C" and day[ids[3]] == "C",
        day,
    )

    # ---------- 3. OCENY: Enter schodzi w dol kolumny ----------
    page.click('button:has-text("Oceny")')
    page.wait_for_timeout(200)
    page.click('button[onclick="openGradeColumnModal()"]')
    page.fill("#colFullName", "Test sprawnosciowy")
    page.fill("#colShortName", "T.spr")
    page.click("#columnModal button.btn-save")
    page.wait_for_timeout(300)

    colid = [x["id"] for x in cls()["gradeColumns"] if not x.get("auto")][0]
    CELL = '#ocenyBody td[data-col="%s"]' % colid
    autos = [x for x in cls()["gradeColumns"] if x.get("auto")]
    check(
        "oceny: kolumny automatyczne (Syst.) istniej i sa odrozniane",
        len(autos) >= 1,
        [x["shortName"] for x in autos],
    )

    page.click(CELL)
    page.wait_for_timeout(150)
    check(
        "oceny: klik otwiera pole wprost w komorce (bez okna)",
        page.query_selector("#ocenyBody input.grade-inline") is not None,
    )
    for v in ["80", "55", "30", "96"]:
        page.keyboard.type(v)
        page.keyboard.press("Enter")
        page.wait_for_timeout(120)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    c = cls()
    vals = [c["grades"][colid].get(i) for i in ids]
    check(
        "oceny: Enter zapisuje i schodzi do nastepnego ucznia",
        vals[:4] == [80, 55, 30, 96],
        vals,
    )

    page.click(CELL)
    page.wait_for_timeout(150)
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    check(
        "oceny: puste pole + Enter kasuje ocene", ids[0] not in cls()["grades"][colid]
    )

    # Esc nie zapisuje
    page.click(CELL)
    page.wait_for_timeout(150)
    page.keyboard.type("77")
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    check(
        "oceny: Esc porzuca wpisana wartosc",
        ids[0] not in cls()["grades"][colid],
        cls()["grades"][colid],
    )

    page.screenshot(path=str(SHOTS / "shot_oceny.png"), full_page=True)

    # ---------- 4. POMIARY: Enter w dol kolumny ----------
    page.click('button:has-text("Pomiary")')
    page.wait_for_timeout(200)
    page.query_selector_all("#pomiaryBody tr")[0].query_selector_all("input")[0].click()
    page.keyboard.type("165")
    page.keyboard.press("Enter")
    page.wait_for_timeout(150)
    page.keyboard.type("172")
    page.wait_for_timeout(250)
    m = cls()["measurements"]
    check(
        "pomiary: Enter schodzi w dol tej samej kolumny",
        m.get(ids[0], {}).get("jump") == "165"
        and m.get(ids[1], {}).get("jump") == "172",
        m,
    )

    page.screenshot(path=str(SHOTS / "shot_pomiary.png"), full_page=True)
    page.click('button:has-text("Uczniowie")')
    page.wait_for_timeout(200)
    page.screenshot(path=str(SHOTS / "shot_uczniowie.png"), full_page=True)

    check("brak bledow JS w konsoli", not errors, errors[:5])
    browser.close()

httpd.shutdown()
print()
print("WYNIK: %s" % ("WSZYSTKO PASS" if not FAILS else ("%d FAIL" % len(FAILS))))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
