# Produkt dla kolegów, p.4 (HANDOFF-plan-produkt, 19.09): PZO z kodu do danych per szkoła (zasiew ZSS jednorazowy,
# inna szkoła = puste + wskazówka), stopka z wersją z sw.js + link do start.html, start.html serwuje się i ma 6 kroków.
# Zrzuty: _zrzuty/p4_reguly_1400.png, p4_start_1400.png
import re
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
PORT = 8781

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


SW_VER = re.search(
    r"CACHE_VERSION = 'dziennik-wf-v(\d+)'",
    (ROOT / "sw.js").read_text(encoding="utf-8"),
).group(1)

FIXTURE = """() => {
  const st = (n, pref) => Array.from({length: n}, (_, i) => ({ id: pref + (i + 1), name: 'Uczeń ' + 'ABCDEF'[i], longTermReleased: false, height: '', weight: '' }));
  state.classes[0].school = 'ZSS'; state.classes[0].name = '7b'; state.classes[0].students = st(4, 'u');
  const c2 = makeClass('SP 99', '5a', st(3, 'x')); state.classes.push(c2);
  activateClass(state.classes[0].id);
  save(); refreshAll();
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(500)
    page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
    page.wait_for_timeout(600)
    page.evaluate(FIXTURE)
    page.wait_for_timeout(300)

    # stopka
    stopka = page.locator("footer").inner_text()
    check(
        "stopka: bez „Wygenerowane w rozmowie z Claude”",
        "Wygenerowane" not in stopka,
        stopka[-120:],
    )
    check(
        "stopka: wersja z sw.js (v%s)" % SW_VER,
        "wersja %s" % SW_VER in stopka,
        stopka[-120:],
    )
    check(
        "stopka: link do start.html",
        page.locator('footer a[href="start.html"]').count() == 1,
    )

    # Reguły — ZSS: zasiany cytat
    page.click('button.tab:has-text("Reguły")')
    page.wait_for_timeout(300)
    reg = page.text_content("#tab-reguly")
    check(
        "reguły ZSS: cytat PZO z danych",
        "wliczane są do puli wszystkich zajęć" in page.text_content("#regPzo"),
    )
    check(
        "reguły ZSS: źródło nazywa szkołę",
        "ZSS" in page.text_content("#regPzo .zrodlo"),
    )
    check(
        "reguły: notatki robocze wycięte",
        all(
            x not in reg
            for x in [
                "decyzja jeszcze nie zapadła",
                "decyzja 18.09",
                ".docx",
                "Skrypt wklejania istnieje",
            ]
        ),
    )
    check(
        "reguły: textarea PZO per szkoła (2 szkoły)",
        page.locator("#regSzkoly textarea.reg-pzo").count() == 2,
    )
    check(
        "reguły: dane niosą pzo dla ZSS",
        page.evaluate("() => (ustawienia().szkoly.ZSS || {}).pzo || ''").startswith(
            "Nieobecności nieusprawiedliwione"
        ),
    )
    page.screenshot(path=str(SHOTS / "p4_reguly_1400.png"), full_page=True)

    # Reguły — inna szkoła bez PZO: wskazówka, nie cytat ZSS
    page.evaluate("() => { activateClass(state.classes[1].id); save(); refreshAll(); }")
    page.wait_for_timeout(300)
    pz = page.text_content("#regPzo")
    check("reguły SP 99: bez cytatu ZSS", "wliczane są do puli" not in pz, pz[:80])
    check("reguły SP 99: wskazówka gdzie wpisać", "Szkoły i e-dziennik" in pz, pz[:80])
    # wpis przez textarea → pokazuje się w karcie
    ta = page.locator('#regSzkoly textarea.reg-pzo[placeholder*="SP 99"]')
    ta.fill("Próg klasyfikacji 60%.")
    ta.dispatch_event("change")
    page.wait_for_timeout(300)
    check(
        "reguły SP 99: wpis z textarea trafia do karty",
        "Próg klasyfikacji 60%" in page.text_content("#regPzo"),
        page.text_content("#regPzo")[:160],
    )
    check(
        "reguły SP 99: wpis w danych",
        page.evaluate("() => ustawienia().szkoly['SP 99'].pzo")
        == "Próg klasyfikacji 60%.",
    )
    # szkoła ze spacją w nazwie: select e-dziennika też musi działać (błąd cudzysłowów w onchange, złapany 19.09)
    page.locator("#regSzkoly .reg-row:has-text('SP 99') select").select_option("librus")
    page.wait_for_timeout(300)
    check(
        "reguły SP 99: e-dziennik zapisany mimo spacji w nazwie szkoły",
        page.evaluate("() => ustawienia().szkoly['SP 99'].edziennik") == "librus",
    )
    # snapshot kopii niesie ustawienia z pzo
    check(
        "kopia: snapshot niesie pzo",
        page.evaluate(
            "() => JSON.stringify(snapshotData()).includes('Próg klasyfikacji 60%')"
        ),
    )

    # start.html
    page.goto("http://127.0.0.1:%d/start.html" % PORT)
    page.wait_for_timeout(300)
    check("start.html: 6 kroków", page.locator("ol.kroki > li").count() == 6)
    check(
        "start.html: link do dziennika",
        page.locator('a[href="dziennik_wf.html"]').count() >= 1,
    )
    page.screenshot(path=str(SHOTS / "p4_start_1400.png"), full_page=True)

    check("bez błędów JS", not errors, str(errors[:3]))
    browser.close()

httpd.shutdown()
print("\nFAIL: %d" % len(FAILS))
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
