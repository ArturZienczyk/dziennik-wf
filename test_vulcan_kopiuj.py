# Test end-to-end: "Kopiuj dla VULCAN" (appka) -> parseInput/match/symbolFor (userscript).
# Sprawdza, ze surowe kody appki przechodza przez projekcje skryptu na wlasciwe symbole VULCANa.
import re
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8766

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


# funkcje projekcji ze skryptu (bez UI) - wycinam z pliku, zeby test uzywal TEJ SAMEJ mapy
src = (ROOT / "vulcan-frekwencja.user.js").read_text(encoding="utf-8")


def fn(name):
    m = re.search(r"^function %s\(.*?^}" % name, src, re.S | re.M)
    assert m, name
    return m.group(0)


SCRIPT_FNS = "\n".join(fn(n) for n in ["symbolFor", "norm", "parseInput", "match"])
SHORT = re.search(r"^var SHORT=.*?;$", src, re.M).group(0)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1500, "height": 1000}
    )
    ctx.grant_permissions(["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate(
        "() => zamekPierwszeHaslo('haslo-x1')"
    )  # zamek (Szczebel 5): pusty magazyn -> pierwsze haslo
    page.evaluate(
        "() => { state.students.length = 0; "
        "state.students.push("
        " {id:'u1', name:'Jan Kowalski', longTermReleased:false},"
        " {id:'u2', name:'Nowak Piotr', longTermReleased:false},"
        " {id:'u3', name:'Adam Wiśniewski', longTermReleased:false},"
        " {id:'u4', name:'Zieliński Marek', longTermReleased:false},"
        " {id:'u5', name:'Lis Tomasz', longTermReleased:false},"
        " {id:'u6', name:'Bąk Karol', longTermReleased:true},"
        " {id:'u7', name:'Mazur Filip', longTermReleased:false},"
        " {id:'u8', name:'', longTermReleased:false},"
        " {id:'u9', name:'Sowa Igor', longTermReleased:false},"
        " {id:'u10', name:'Dudek Ewa', longTermReleased:false},"
        " {id:'u11', name:'Kruk Oliwia', longTermReleased:false},"
        # para imiennikow zapisana w appce odwrotnie niz w VULCANie (Imie Nazwisko / Nazwisko Imie)
        " {id:'u12', name:'Anna Wilk', longTermReleased:false},"
        " {id:'u13', name:'Marcin Wilk', longTermReleased:false});"
        " state.currentDate='2026-09-17';"
        " state.attendance['2026-09-17']={u1:'C', u2:attWrite('C',true), u3:'BS', u4:attWrite('NC',true), u5:'NB', u7:'NU',"
        "   u9:'NS', u10:attWrite('NS',true), u11:attWrite('NU',true), u12:'NS', u13:'NU'};"
        " save(); renderStudents(); renderAttendance(); }"
    )
    page.click("#saveBarKopiuj")  # C v2: „📋 do VULCANa” w stopce kolumny
    page.wait_for_timeout(300)
    clip = page.evaluate("() => navigator.clipboard.readText()")
    lines = clip.replace("\r", "").split("\n")
    check(
        "schowek: 11 wierszy (bez czystego C, bez pustego nazwiska)",
        len(lines) == 11,
        lines,
    )
    check("format Nazwisko<TAB>status", all("\t" in l for l in lines), lines)
    check("C+sp eksportowane jako C+sp", "Nowak Piotr\tC+sp" in lines, lines)
    check("NC+sp", "Zieliński Marek\tNC+sp" in lines)
    check("zwolniony długoterminowo -> ZW", "Bąk Karol\tZW" in lines)
    toast = page.text_content("#toast")
    check("toast mówi o pominiętych C", "pominięto 1" in toast, toast)

    # projekcja skryptem: siatka VULCAN "Nazwisko Imię"
    vulcan_names = [
        "Kowalski Jan",
        "Nowak Piotr",
        "Wiśniewski Adam",
        "Zieliński Marek",
        "Lis Tomasz",
        "Bąk Karol",
        "Mazur Filip",
        "Sowa Igor",
        "Dudek Ewa",
        "Kruk Oliwia",
        "Wilk Anna",
        "Wilk Marcin",
        "Obcy Uczeń",
    ]
    res = page.evaluate(
        "([fns, short, names, txt]) => { eval(fns + '\\n' + short);"
        " var pairs = names.map(n => ({cell:null, name:n}));"
        " var r = match(pairs, parseInput(txt));"
        " return {rows: r.rows.map(x => [x.pair.name, x.status, x.symbol ? SHORT[x.symbol] : null]), un: r.unmatchedInput}; }",
        [SCRIPT_FNS, SHORT, vulcan_names, clip],
    )
    got = {r[0]: r[2] for r in res["rows"]}
    exp = {
        "Kowalski Jan": None,
        "Nowak Piotr": "s",
        "Wiśniewski Adam": "nc",
        "Zieliński Marek": "s",
        "Lis Tomasz": "—",
        "Bąk Karol": "nc",  # decyzja 09-17: ZW -> nc, "zwolniony" VULCAN nieuzywany
        "Mazur Filip": "u",
        # bug 09-21 (8b): ⏱ doklejone do statusu zjadalo status bazowy — kazdy "+sp" szedl jako "s",
        # bo warunek "zawiera SP" stal PRZED tablica. Para kontrolna: ten sam status, jeden uczen
        # z ⏱, drugi bez — do VULCANa musza trafic TE SAME symbole.
        "Sowa Igor": "ns",  # NS bez ⏱
        "Dudek Ewa": "ns",  # NS + ⏱ — nieobecnosc zachowuje swoj symbol
        "Kruk Oliwia": "u",  # NU + ⏱
        # bug 09-21 (8b): para imiennikow blokowala sie nawzajem — dopasowanie szlo po nazwisku,
        # ktore wymagalo unikalnosci, wiec OBOJE zostawali bez wpisu. Rozstrzyga imie, mimo ze
        # appka pisze "Anna Wilk", a VULCAN "Wilk Anna".
        "Wilk Anna": "ns",
        "Wilk Marcin": "u",
        "Obcy Uczeń": None,
    }
    for n, e in exp.items():
        check("projekcja %s -> %r" % (n, e), got.get(n) == e, got.get(n))
    check("skrypt: nic niedopasowanego z inputu", res["un"] == [], res["un"])
    check("brak błędów JS", errors == [], errors)
    browser.close()
httpd.shutdown()
print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
