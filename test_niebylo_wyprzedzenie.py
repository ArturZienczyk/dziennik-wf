# Test „nie będzie” z wyprzedzeniem (2026-10-02): przycisk na kafelku bez wpisu (przyszły dzień = „nie będzie”,
# miniony = „nie było”), zakres w oknie: ta lekcja / klasa do dnia / wszystkie moje lekcje do dnia; pomija
# lekcje z wpisem i zastępstwem. Wdrożone 21.10 — testuje dziennik_wf.html (arg: inny plik, np. roboczy).
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_zrzuty" / "niebylo-wyprzedzenie"
OUT.mkdir(parents=True, exist_ok=True)
PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
PORT = 8791
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
src = (ROOT / "test_widok_dzienny.py").read_text(encoding="utf-8")
ns = {}
exec(src[src.index("PLAN = {") : src.index("with sync_playwright()")], ns)
PLAN, FIXTURE = ns["PLAN"], ns["FIXTURE"]
from playwright.sync_api import sync_playwright
import datetime

# Piątki liczone od dziś (21.10: wpisane na sztywno 09/16/23.10 przeszły w przeszłość i test zaczął
# widzieć „nie było” zamiast „nie będzie”). P1 = najbliższy piątek po dziś, P2/P3 = kolejne.
_d = datetime.date.today() + datetime.timedelta(days=1)
while _d.weekday() != 4:
    _d += datetime.timedelta(days=1)
P1, P2, P3 = (str(_d + datetime.timedelta(days=7 * i)) for i in range(3))

F = []


def check(n, c, d=""):
    print("[%s] %s %s" % ("PASS" if c else "FAIL", n, d))
    c or F.append(n)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for W, H, tag in [(1400, 900, "lap"), (369, 608, "tel")]:
        pg = b.new_context(
            service_workers="block", viewport={"width": W, "height": H}
        ).new_page()
        err = []
        pg.on("pageerror", lambda e: err.append(str(e)))
        pg.goto("http://127.0.0.1:%d/%s" % (PORT, PLIK))
        pg.wait_for_timeout(400)
        pg.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
        pg.wait_for_timeout(600)
        pg.evaluate(FIXTURE, PLAN)
        pg.wait_for_timeout(300)
        odw = lambda: pg.evaluate(
            "() => state.classes.map(c => c.name + ':' + Object.keys(c.odwolane||{}).sort().join(',')).join(' | ')"
        )
        # przyszły piątek (P1)
        pg.evaluate("(d) => { wybierzLekcje(state.classes[0].id, d, 3); }", P1)
        pg.wait_for_timeout(300)
        if tag == "tel":
            pg.evaluate("() => { if (typeof dzienZwin === 'function') dzienZwin(); }")
            pg.wait_for_timeout(200)
        pg.screenshot(path=str(OUT / f"{tag}_1_przyszly_dzien.png"))
        n_btn = pg.locator(".niebylo-postaw:visible").count()
        txt = pg.locator(".niebylo-postaw:visible").all_inner_texts()
        check(
            f"{tag}: przyciski 'nie będzie' widoczne",
            n_btn >= 1 and all(t == "nie będzie" for t in txt),
            str(txt),
        )
        # klik na kafelku 8c
        pg.locator(
            ".kol.podglad[data-cls] .niebylo-postaw"
        ).first.click() if tag == "lap" else pg.locator(
            ".niebylo-postaw:visible"
        ).last.click()
        pg.wait_for_timeout(200)
        check(
            f"{tag}: okno tytuł 'Nie będzie lekcji'",
            pg.inner_text("#niebyloTytul") == "Nie będzie lekcji",
            pg.inner_text("#niebyloTytul"),
        )
        check(f"{tag}: zakres widoczny", pg.is_visible("#niebyloZakres"))
        check(
            f"{tag}: 'do dnia' ukryte przy 'tylko ta'",
            not pg.is_visible("#niebyloDoWrap"),
        )
        pg.check('input[name="niebyloZakres"][value="klasa"]')
        check(
            f"{tag}: 'do dnia' widoczne po wyborze klasy",
            pg.is_visible("#niebyloDoWrap"),
        )
        pg.fill("#niebyloDo", P2)
        pg.fill("#niebyloKomentarz", "wyjazd")
        pg.screenshot(path=str(OUT / f"{tag}_2_okno.png"))
        kl = pg.evaluate("() => _niebyloCtx.clsId")
        nm = pg.evaluate("(id) => state.classes.find(c=>c.id===id).name", kl)
        pg.click("#niebyloModal button:has-text('Zapisz')")
        pg.wait_for_timeout(300)
        o = odw()
        print(o)
        check(
            f"{tag}: klasa {nm} oznaczona 2 piątki",
            (nm + ":" + P1 + "," + P2) in o,
            o,
        )
        check(
            f"{tag}: inne klasy nietknięte",
            sum(1 for part in o.split(" | ") if part.split(":")[1]) == 1,
            o,
        )
        pg.screenshot(path=str(OUT / f"{tag}_3_po_zapisie.png"))
        # cały dzień P3 — wszystkie moje lekcje
        pg.evaluate(
            "(d) => { wybierzLekcje(state.classes[0].id, d, 3); nieByloOkno(state.classes[0].id, attKey()); }", P3
        )
        pg.wait_for_timeout(200)
        pg.check('input[name="niebyloZakres"][value="wszystkie"]')
        pg.click("#niebyloModal button:has-text('Zapisz')")
        pg.wait_for_timeout(300)
        n23 = pg.evaluate(
            "(d) => state.classes.filter(c => (c.odwolane||{})[d]).length", P3
        )
        check(f"{tag}: cały dzień P3 = 4 klasy", n23 == 4, n23)
        toast = pg.evaluate(
            "() => (document.querySelector('.toast, #toast')||{}).textContent || ''"
        )
        print("toast:", toast)
        pg.screenshot(path=str(OUT / f"{tag}_4_caly_dzien.png"))
        # zmiana powodu: zakres ukryty, tytuł 'zmień'
        pg.evaluate("(d) => nieByloOkno(state.classes[0].id, d)", P3)
        pg.wait_for_timeout(100)
        check(
            f"{tag}: przy zmianie powodu zakres ukryty",
            not pg.is_visible("#niebyloZakres"),
        )
        check(
            f"{tag}: 'jednak będzie' w oknie",
            pg.inner_text("#niebyloJednak") == "jednak będzie",
        )
        pg.evaluate("() => nieByloAnuluj()")
        # przeszły dzień bez wpisu: 'nie było'
        pg.evaluate("() => { wybierzLekcje(state.classes[1].id, '2026-09-25', 5); }")
        pg.wait_for_timeout(200)
        txt = pg.locator(".niebylo-postaw").all_inner_texts()
        check(
            f"{tag}: przeszły dzień -> 'nie było'",
            txt and all(t == "nie było" for t in txt),
            str(txt),
        )
        # lekcja z wpisem: brak przycisku
        pg.evaluate("() => { wybierzLekcje(state.classes[0].id, '2026-09-18', 3); }")
        pg.wait_for_timeout(200)
        c = pg.evaluate(
            "() => [...document.querySelectorAll('.niebylo-postaw')].filter(b => (b.closest('[data-klucz]')||{}).dataset?.klucz === '2026-09-18' && b.closest('[data-cls]').dataset.cls === state.classes[0].id).length"
        )
        check(f"{tag}: lekcja z wpisem bez przycisku", c == 0, c)
        check(f"{tag}: bez błędów JS", not err, err)
    b.close()
print("FAILS:", F)
sys.exit(1 if F else 0)
