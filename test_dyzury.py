# Bramka dyzurow na przerwach (2026-09-21): przerwa NIE jest kafelkiem jak lekcja — w widoku dnia
# to waski slupek MIEDZY kafelkami, z napisem pionowym (miejsce dyzuru). Powod: przerwa nie ma
# numeru lekcji, ona jest POMIEDZY numerami; kafelek "L3" klamalby o tym, czym jest.
# Inwarianty pilnowane tutaj:
#   1. slupek stoi dokladnie miedzy kafelkiem lekcji "po" a nastepna lekcja (kolejnosc w pasku),
#   2. jest waski (< 40 px) i ma napis pionowy (writing-mode: vertical-*),
#   3. nie da sie go kliknac jak lekcji (nie otwiera zadnej lekcji),
#   4. przy zawijaniu paska nie zostaje sam na poczatku wiersza (sklejony w .kol-para),
#   5. widok Tydzien: belka pozioma (tam kafelki stoja pionowo — pionowy napis nie mialby sensu),
#   6. dzien wolny nie pokazuje dyzuru.
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8783

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


DZIS = "2026-09-18"  # piatek (indeks 4)
WOLNY = "2026-09-25"  # nastepny piatek, wpisany jako dzien wolny
PLAN = {
    "od": "2026-09-01",
    "do": "2027-06-30",
    "klasy": {"7b": {"4": [1, 3]}, "8c": {"4": [5]}},
    "inne": {"EZ 4a": {"4": [4]}},
    "dyzury": {"parter": {"4": [3]}, "szatnie": {"4": [5]}},
    "wolne": [WOLNY],
}

FIXTURE = """(p) => {
  const st = (n, pref) => Array.from({length: n}, (_, i) => ({ id: pref + (i + 1), name: 'Uczen' + pref + ' ' + 'ABCDEFGHIJ'[i], longTermReleased: false, height: '', weight: '' }));
  state.classes[0].school = 'ZSS'; state.classes[0].name = '7b'; state.classes[0].students = st(6, 'u');
  const c8 = makeClass('ZSS', '8c', st(5, 'v')); state.classes.push(c8);
  activateClass(state.classes[0].id);
  zaleglePlanZastosuj(p);
  state.currentDate = '2026-09-18';
  save(); refreshAll();
}"""

# kolejnosc elementow paska dnia: 'L<nr> <klasa>' dla lekcji, 'przerwa:<miejsce>' dla slupka
PASEK = """() => [...document.querySelectorAll('#kolPrzed .kol')].map(e => {
  if (e.classList.contains('przerwa')) return 'przerwa:' + e.dataset.miejsce;
  if (e.classList.contains('okienko-zast')) return '+zast';
  const nr = (e.querySelector('.nr') || {}).textContent || '';
  const kl = (e.querySelector('.kl') || {}).textContent || '';
  return (nr.trim() + ' ' + kl.trim()).trim();
})"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
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
    page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
    page.wait_for_timeout(600)
    page.evaluate("() => ustawWidok('dzien')")
    page.evaluate(FIXTURE, PLAN)
    page.evaluate("(d) => wybierzLekcje(state.classes[0].id, d, 1)", DZIS)
    page.wait_for_timeout(300)

    pasek = page.evaluate(PASEK)
    # plan piatku: L1 7b, L3 7b, L4 EZ 4a (inne), L5 8c; dyzur po L3 (parter) i po L5 (szatnie)
    check(
        "slupek 'parter' stoi po lekcji L3, przed L4",
        pasek.index("przerwa:parter") == pasek.index("L3 7b") + 1
        and pasek.index("przerwa:parter") < pasek.index("L4 EZ 4a"),
        pasek,
    )
    check(
        "slupek 'szatnie' (dyzur po ostatniej lekcji) stoi za L5",
        pasek.index("przerwa:szatnie") > pasek.index("L5 8c"),
        pasek,
    )
    check(
        "dwa slupki, ani jednego wiecej",
        pasek.count("przerwa:parter") + pasek.count("przerwa:szatnie") == 2,
        pasek,
    )

    geo = page.evaluate(
        """() => [...document.querySelectorAll('#kolPrzed .kol.przerwa')].map(e => {
             const r = e.getBoundingClientRect(), cs = getComputedStyle(e.querySelector('.txt'));
             return { w: Math.round(r.width), h: Math.round(r.height), wm: cs.writingMode, txt: e.textContent.trim() };
           })"""
    )
    check(
        "slupek waski (< 40 px) i wyzszy niz szerszy",
        all(g["w"] < 40 and g["h"] > g["w"] for g in geo),
        geo,
    )
    check(
        "napis pionowy (writing-mode: vertical-*)",
        all(g["wm"].startswith("vertical") for g in geo),
        geo,
    )
    check(
        "na slupku miejsce dyzuru, bez slowa 'L' i numeru",
        [g["txt"] for g in geo] == ["parter", "szatnie"],
        geo,
    )

    # slupek nie jest kafelkiem lekcji: klik nie przelacza lekcji
    przed_klik = page.evaluate("() => state.currentNr")
    page.click("#kolPrzed .kol.przerwa >> nth=0", force=True)
    page.wait_for_timeout(200)
    check(
        "klik w slupek nie otwiera zadnej lekcji",
        page.evaluate("() => state.currentNr") == przed_klik,
        (przed_klik, page.evaluate("() => state.currentNr")),
    )
    check(
        "slupek nie ma naglowka kafelka (.kol-head) ani guzika 'otworz'",
        page.locator("#kolPrzed .kol.przerwa .kol-head").count() == 0,
    )

    # zawijanie paska: slupek nie zostaje sam na poczatku wiersza
    check(
        "slupek sklejony z kafelkiem po lewej (.kol-para)",
        page.locator("#kolPrzed .kol-para > .kol.przerwa").count() == 2,
        page.locator("#kolPrzed .kol-para").count(),
    )
    page.set_viewport_size({"width": 430, "height": 900})
    page.wait_for_timeout(300)
    lewe = page.evaluate(
        """() => [...document.querySelectorAll('#kolPrzed .kol.przerwa')].map(e => {
             const s = e.getBoundingClientRect(), l = e.previousElementSibling.getBoundingClientRect();
             return { sameRow: Math.abs(s.top - l.top) < 12, dx: Math.round(s.left - l.right) };
           })"""
    )
    check(
        "telefon 430 px: slupek w tym samym wierszu co kafelek po lewej",
        all(x["sameRow"] for x in lewe),
        lewe,
    )
    page.set_viewport_size({"width": 1400, "height": 900})
    page.wait_for_timeout(300)

    # widok Tydzien: belka pozioma, nie slupek
    page.evaluate("() => ustawWidok('tydzien')")
    page.wait_for_timeout(300)
    belki = page.evaluate(
        """() => [...document.querySelectorAll('#planTydzien .plan-przerwa')].map(e => {
             const r = e.getBoundingClientRect();
             return { w: Math.round(r.width), h: Math.round(r.height), txt: e.textContent.trim() };
           })"""
    )
    check(
        "Tydzien: dwie belki przerwy, poziome (szersze niz wyzsze)",
        len(belki) == 2 and all(b["w"] > b["h"] for b in belki),
        belki,
    )
    check(
        "Tydzien: w widoku Tydzien nie ma pionowych slupkow",
        page.locator("#planTydzien .kol.przerwa").count() == 0,
    )
    page.screenshot(path=str(SHOTS / "dyzury_tydzien.png"), full_page=False)
    page.evaluate("() => ustawWidok('dzien')")
    page.wait_for_timeout(200)

    # dzien wolny: dyzuru nie ma
    page.evaluate("(d) => { state.currentDate = d; renderAttendance(); }", WOLNY)
    page.wait_for_timeout(300)
    check(
        "dzien wolny: zadnego slupka dyzuru",
        page.locator("#kolPrzed .kol.przerwa").count() == 0,
    )
    page.evaluate("(d) => { state.currentDate = d; renderAttendance(); }", DZIS)
    page.wait_for_timeout(300)

    # zakladka Plan: grafik dyzurow klika sie jak siatka lekcji
    page.click('button.tab:has-text("Plan")')
    page.wait_for_timeout(300)
    check(
        "Plan: karta 'Dyzury na przerwach' z wierszami miejsc",
        page.locator('.plan-karta:has-text("Dyżury na przerwach") .siatka-kom').count()
        >= 10,
    )
    page.click(
        '.plan-karta:has-text("Dyżury na przerwach") .siatka-kom[data-cls="dyzur:parter"][data-dzien="3"]'
    )
    page.wait_for_timeout(200)
    page.click('.s-nr .siatka-nr[data-nr="2"]')
    page.wait_for_timeout(300)
    check(
        "Plan: klik numeru dopisuje dyzur do planu (czwartek, po L2)",
        page.evaluate("() => (zaleglePlany()[0].dyzury || {}).parter['3']") == [2],
        page.evaluate("() => JSON.stringify((zaleglePlany()[0].dyzury || {}).parter)"),
    )

    page.locator('.plan-karta:has-text("Dyżury na przerwach")').screenshot(
        path=str(SHOTS / "dyzury_plan.png")
    )

    # Przypadek wrogi: nazwa miejsca z apostrofem i backslashem. escapeHtml zamienia ' na &#39;,
    # ale przegladarka dekoduje encje ZANIM atrybut trafi do parsera JS - bez JSON.stringify
    # taka nazwa wykonuje sie jako kod (XSS z pliku planu / ze scalonej kopii).
    ZLE = "x'); window.__xss = 1; ('\\\\"
    page.evaluate(
        "(m) => { const p = zaleglePlany()[0]; p.dyzury[m] = { '4': [1] }; save(); renderPlanUstawienia(); }",
        ZLE,
    )
    page.wait_for_timeout(200)
    page.click(
        '.plan-karta:has-text("Dyżury na przerwach") tr.plan-inne:last-of-type button.usun'
    )
    page.wait_for_timeout(300)
    # sprawdzane PO kliku: onclick odpala sie dopiero przy kliknieciu, sam render niczego nie wykonuje
    check(
        "wroga nazwa miejsca nie wykonuje sie jako kod (po kliku w ×)",
        page.evaluate("() => window.__xss === undefined"),
    )
    check(
        "usuwanie miejsca dziala tez dla nazwy z apostrofem i backslashem",
        page.evaluate("(m) => !(m in (zaleglePlany()[0].dyzury || {}))", ZLE),
        page.evaluate("() => Object.keys(zaleglePlany()[0].dyzury || {})"),
    )

    page.click('button.tab:has-text("Obecno")')
    page.wait_for_timeout(300)
    page.screenshot(path=str(SHOTS / "dyzury_dzien.png"), full_page=False)
    page.locator("#dzienKolumny").screenshot(path=str(SHOTS / "dyzury_pasek.png"))

    check("bez bledow JS", not errors, errors[:3])
    browser.close()

httpd.shutdown()
if FAILS:
    print("\nWYNIK: FAIL - %d: %s" % (len(FAILS), FAILS))
    sys.exit(1)
print(
    "\nWYNIK: PASS - dyzur to slupek miedzy kafelkami, nie kafelek. Zrzuty: _zrzuty/dyzury_*.png"
)
