# „Nie było” z kafelka (19.09, user: „koniecznie zrobić plus miejsce na własny komentarz”): klik w „nie było: powód”
# na kafelku (otwarta lekcja i podgląd) otwiera okno zmiany powodu + komentarz, bez „jednak była”. Zapis = jeden
# string „powód · komentarz” w cls.odwolane[k] (scalanie/statystyki/pasek tygodnia bez zmian). Zrzut: _zrzuty/niebylo_komentarz_1400.png
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
PORT = 8785
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

src = (ROOT / "test_widok_dzienny.py").read_text(encoding="utf-8")
ns = {}
exec(src[src.index("PLAN = {") : src.index("with sync_playwright()")], ns)
PLAN, FIXTURE = ns["PLAN"], ns["FIXTURE"]

from playwright.sync_api import sync_playwright

FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
    ).new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
    page.wait_for_timeout(600)
    page.evaluate(FIXTURE, PLAN)
    page.wait_for_timeout(300)
    K = "2026-09-04#3"
    page.evaluate(
        "(k) => { const c = state.classes[0]; c.odwolane = c.odwolane || {}; c.odwolane[k] = 'inne'; save(); refreshAll(); }",
        K,
    )
    odw = lambda: page.evaluate("(k) => (state.classes[0].odwolane || {})[k] || ''", K)

    page.click("button.tab:has-text('Obecność')")
    page.evaluate(
        "() => { ustawWidok('dzien'); wybierzLekcje(state.classes[0].id, '2026-09-04', 3); }"
    )
    page.wait_for_timeout(300)

    # 1. otwarta lekcja: klik w „nie było: inne” otwiera okno, flaga zostaje
    page.locator(".niebylo-zmien:visible").first.click()
    page.wait_for_timeout(200)
    check(
        "klik w „nie było: inne” otwiera okno",
        page.locator("#niebyloModal.active").count() == 1,
    )
    check("flaga nie zdjęta przez otwarcie okna", odw() == "inne", odw())
    check(
        "okno: powód wstępnie „inne”",
        page.locator("#niebyloPowod").input_value() == "inne",
    )
    check(
        "okno: „jednak była” widoczne przy edycji",
        page.locator("#niebyloJednak").is_visible(),
    )
    page.select_option("#niebyloPowod", "wycieczka")
    page.fill("#niebyloKomentarz", "Kraków, 3 dni")
    page.locator("#niebyloModal .modal").screenshot(
        path=str(SHOTS / "niebylo_komentarz_modal.png")
    )
    page.click("#niebyloModal button:has-text('Zapisz')")
    page.wait_for_timeout(300)
    check(
        "zapis: powód · komentarz w danych", odw() == "wycieczka · Kraków, 3 dni", odw()
    )
    kaf = page.locator(".niebylo-info:visible").first
    check(
        "kafelek pokazuje powód i komentarz",
        "wycieczka · Kraków, 3 dni" in kaf.inner_text(),
        kaf.inner_text(),
    )
    check(
        "„jednak była” nadal na kafelku",
        page.locator(".niebylo-cofnij:visible").count() >= 1,
    )
    page.locator("#dzienKolumny").screenshot(
        path=str(SHOTS / "niebylo_komentarz_1400.png")
    )

    # 2. ponowne otwarcie: rozbicie na powód + komentarz
    page.locator(".niebylo-zmien:visible").first.click()
    page.wait_for_timeout(200)
    check(
        "ponowne otwarcie: powód wycieczka",
        page.locator("#niebyloPowod").input_value() == "wycieczka",
    )
    check(
        "ponowne otwarcie: komentarz wraca do pola",
        page.locator("#niebyloKomentarz").input_value() == "Kraków, 3 dni",
    )
    # pusty komentarz = sam powód
    page.fill("#niebyloKomentarz", "   ")
    page.click("#niebyloModal button:has-text('Zapisz')")
    page.wait_for_timeout(300)
    check("pusty komentarz → sam powód", odw() == "wycieczka", odw())

    # 3. „jednak była” z okna zdejmuje flagę
    page.locator(".niebylo-zmien:visible").first.click()
    page.wait_for_timeout(200)
    page.click("#niebyloJednak")
    page.wait_for_timeout(300)
    check("„jednak była” w oknie zdejmuje flagę", odw() == "", odw())
    check("okno zamknięte", page.locator("#niebyloModal.active").count() == 0)
    check(
        "lekcja wraca do zaległych",
        "L3"
        in page.evaluate(
            "() => zaleglePolicz().filter(x => x.date === '2026-09-04' && x.clsName === '7b').map(x => 'L' + x.nr).join(',')"
        ),
    )

    # 4. kafelek podglądu (8c, nieotwarta): klik w powód otwiera okno, nie otwiera lekcji
    page.evaluate(
        "() => { const c = state.classes[1]; c.odwolane = c.odwolane || {}; c.odwolane['2026-09-04#5'] = 'zawody'; save(); refreshAll(); }"
    )
    page.wait_for_timeout(200)
    page.locator(".kol.podglad.niebylo .niebylo-zmien:visible").first.click()
    page.wait_for_timeout(200)
    check(
        "podgląd: klik w powód otwiera okno",
        page.locator("#niebyloModal.active").count() == 1,
    )
    check(
        "podgląd: lekcja 8c NIE została otwarta",
        page.evaluate("() => getCurrentClass().name") == "7b",
    )
    page.fill("#niebyloKomentarz", "ja na zawodach z 4d")
    page.click("#niebyloModal button:has-text('Zapisz')")
    page.wait_for_timeout(300)
    check(
        "podgląd: komentarz zapisany do 8c",
        page.evaluate("() => state.classes[1].odwolane['2026-09-04#5']")
        == "zawody · ja na zawodach z 4d",
    )
    # Esc / Anuluj nie zmienia
    page.locator(".kol.podglad.niebylo .niebylo-zmien:visible").first.click()
    page.fill("#niebyloKomentarz", "zmiana")
    page.click("#niebyloModal button:has-text('Anuluj')")
    page.wait_for_timeout(200)
    check(
        "Anuluj nie zapisuje",
        page.evaluate("() => state.classes[1].odwolane['2026-09-04#5']")
        == "zawody · ja na zawodach z 4d",
    )

    # 5. pasek tygodnia: title niesie pełny tekst
    page.evaluate("() => ustawWidok('tydzien')")
    page.wait_for_timeout(300)
    t = page.locator(".plan-lekcja.niebylo").first.get_attribute("title") or ""
    check(
        "pasek tygodnia: title z powodem i komentarzem",
        "zawody · ja na zawodach" in t,
        t,
    )

    check("bez błędów JS", not errors, str(errors[:3]))
    browser.close()

httpd.shutdown()
print("\nFAIL: %d" % len(FAILS))
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
