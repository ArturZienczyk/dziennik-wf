# Test „nie było na kafelku” (2026-09-19): powód i przycisk „jednak była” na kafelku otwartej lekcji
# (pasek dnia), cofnięcie zdejmuje flagę; wpis statusu / zapis lekcji sam zdejmuje „nie było”;
# zakładka Plan bez kolumny „nie było”, kolumna „klasa w planie” tylko przy planie z pliku,
# wczytywanie pliku w sekcji zwijanej „Zaawansowane”.
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8777
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
        "(k) => { const c = state.classes[0]; c.odwolane = c.odwolane || {}; c.odwolane[k] = 'wycieczka'; save(); refreshAll(); }",
        K,
    )
    odw = lambda: page.evaluate("() => JSON.stringify(state.classes[0].odwolane || {})")

    # 1. Plan: bez kolumny „nie było”, plan ręczny → bez „klasa w planie”, plik w sekcji zwijanej
    page.click("button.tab:has-text('Plan')")
    page.wait_for_timeout(300)
    naglowki = page.inner_text("#planUstawienia table tr:first-child").lower()
    check("Plan: bez kolumny „nie było”", "nie było" not in naglowki, naglowki)
    check(
        "Plan ręczny: bez kolumny „klasa w planie”",
        "klasa w planie" not in naglowki,
        naglowki,
    )
    check(
        "Plan: wczytywanie pliku w zwiniętej sekcji Zaawansowane",
        not page.evaluate("() => document.querySelector('details.plan-zaaw').open")
        and not page.locator("#zaleglePlik").is_visible(),
    )
    page.evaluate(
        "() => { planAktywny(false).wygenerowano = '2026-09-04'; renderPlanUstawienia(); }"
    )
    check(
        "Plan z pliku: siatka nadal bez kolumny „klasa w planie” (19.09: przeniesiona do Zaawansowane)",
        "klasa w planie" not in page.inner_text("#planUstawienia table tr:first-child").lower(),
    )
    check(
        "Plan z pliku: dopasowanie nazw w Zaawansowane, jeden select na klasę",
        page.locator("details.plan-zaaw .plan-dopasowanie select").count() == len(page.evaluate("() => state.classes")),
    )
    page.evaluate(
        "() => { delete planAktywny(false).wygenerowano; renderPlanUstawienia(); }"
    )

    # 2. Kafelek otwartej lekcji: powód + „jednak była”
    page.click("button.tab:has-text('Obecność')")
    page.evaluate(
        "() => { ustawWidok('dzien'); wybierzLekcje(state.classes[0].id, '2026-09-04', 3); }"
    )
    page.wait_for_timeout(300)
    kaf = page.locator(".niebylo-info:visible").first
    check(
        "kafelek otwartej lekcji: „nie było: wycieczka”",
        kaf.count() > 0 and "wycieczka" in kaf.inner_text(),
        kaf.inner_text() if kaf.count() else "brak",
    )
    page.locator(".niebylo-cofnij:visible").first.click()
    page.wait_for_timeout(300)
    check("„jednak była” zdejmuje flagę", odw() == "{}", odw())
    check(
        "po cofnięciu kafelek bez „nie było”",
        page.locator(".niebylo-info:visible").count() == 0,
    )

    # 3. Wpis statusu zdejmuje „nie było” sam
    page.evaluate(
        "(k) => { state.classes[0].odwolane[k] = 'zawody'; save(); refreshAll(); }", K
    )
    page.evaluate("() => { state.pickerStudentId = 'u1'; setStatus('C'); }")
    page.wait_for_timeout(200)
    check("wpis statusu ucznia zdejmuje „nie było”", odw() == "{}", odw())
    check(
        "chip Zaległe przeliczony (lekcja z wpisem nie jest zaległa)",
        "L3"
        not in page.evaluate(
            "() => zaleglePolicz().filter(x => x.date === '2026-09-04' && x.clsName === '7b').map(x => 'L' + x.nr).join(',')"
        ),
    )

    # 4. Kafelek podglądu (lekcja nieotwarta) też ma „jednak była”
    page.evaluate(
        "() => { const c = state.classes[1]; c.odwolane = c.odwolane || {}; c.odwolane['2026-09-04#5'] = 'zastępstwo / zmiana planu'; save(); refreshAll(); }"
    )
    page.wait_for_timeout(200)
    pod = page.locator(".kol.podglad.niebylo .niebylo-cofnij:visible")
    check("kafelek podglądu 8c: „jednak była” widoczne", pod.count() == 1, pod.count())
    pod.first.click()
    page.wait_for_timeout(300)
    check(
        "klik na podglądzie cofa, nie otwiera lekcji",
        page.evaluate("() => JSON.stringify(state.classes[1].odwolane)") == "{}"
        and page.evaluate("() => getCurrentClass().name") == "7b",
    )

    # 5. Plan jako karty + pusty stan (19.09): 0 klas → karta „trzy kroki”, klasa bez uczniów → krok 1 ✓,
    #    z uczniami → cztery karty (Siatka / Inne zajęcia / Dyżury na przerwach / Dni wolne) i chipy numerów
    page.click("button.tab:has-text('Plan')")
    page.wait_for_timeout(200)
    check("Plan z klasami: cztery karty", page.locator("#planUstawienia .plan-karta").count() == 4)
    check("numer lekcji jako chip", page.locator("#planUstawienia .siatka-kom .chip").count() >= 4)
    check("„Zaawansowane” w stopce karty siatki", page.locator("#planUstawienia .plan-karta .stopka details.plan-zaaw").count() == 1)
    page.evaluate("() => { state.classes = [makeClass('ZSS', '1x', [])]; renderPlanUstawienia(); }")
    check("klasa bez uczniów: karta kroków, krok 1 odhaczony",
          page.locator("#planUstawienia .plan-pusty li.ok").count() == 1
          and page.inner_text("#planUstawienia .plan-pusty-akcja") == "Dodaj uczniów")
    page.evaluate("() => { state.classes = []; renderPlanUstawienia(); }")
    check("0 klas: karta kroków, przycisk + Dodaj klasę",
          page.locator("#planUstawienia .plan-pusty li.ok").count() == 0
          and page.inner_text("#planUstawienia .plan-pusty-akcja") == "+ Dodaj klasę"
          and page.locator("#planUstawienia table").count() == 0)

    check("brak błędów JS", not errors, errors)
    browser.close()

httpd.shutdown()
print("\n%d FAIL" % len(FAILS) if FAILS else "\nALL PASS")
sys.exit(1 if FAILS else 0)
