# Audyt heurystyczny 19.09 (4 findingi, HANDOFF-zastepstwa-i-kontrast §4): ekran startowy mówi „ustaw hasło, żeby zacząć”,
# tytuł klasy ma jeden selektor, kolumna Syst. sygnalizuje „auto” PRZED kliknięciem, guzik usuwania ma etykietę tekstową.
# Zrzuty do _zrzuty/ux_*.png (oko usera).
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8779

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


FIXTURE = """() => {
  const st = (n, pref) => Array.from({length: n}, (_, i) => ({ id: pref + (i + 1), name: 'Uczeń ' + 'ABCDEFGHIJ'[i], longTermReleased: false, height: '', weight: '' }));
  state.classes[0].school = 'ZSS'; state.classes[0].name = '7b'; state.classes[0].students = st(6, 'u');
  activateClass(state.classes[0].id);
  state.classes[0].attendance['2026-09-18'] = { u1: 'C', u2: 'NC', u3: 'C', u4: 'C' };
  state.classes[0].attendance['2026-09-11'] = { u1: 'C', u2: 'C', u3: 'NB', u4: 'C' };
  state.currentDate = '2026-09-18';
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

    # 1. ekran startowy
    h2 = page.locator("#zamek h2").inner_text()
    check("start: h2 mówi o zaczynaniu", "Ustaw hasło" in h2, h2)
    check(
        "start: guzik = ustaw + otwórz",
        page.locator('#zamek button:has-text("Ustaw hasło i otwórz dziennik")').count()
        == 1,
    )
    check(
        "start: brak „Zamknij dziennik hasłem”",
        page.locator('#zamek:has-text("Zamknij dziennik hasłem")').count() == 0,
    )
    page.screenshot(path=str(SHOTS / "ux_1_start_1400.png"))

    page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
    page.wait_for_timeout(600)
    page.evaluate(FIXTURE)
    page.wait_for_timeout(300)

    # 4. obecność — guzik usuwania z etykietą, za licznikiem lekcji
    page.evaluate("() => ustawWidok('dzien')")
    page.wait_for_timeout(200)
    txt = page.locator(".dzien-row .dzien-usun").inner_text()
    check("obecność: guzik usuwania ma tekst", "usuń wpisy" in txt, txt)
    check(
        "obecność: guzik usuwania za licznikiem lekcji, nie przy ◀ dziś ▶",
        page.evaluate(
            "() => { const r = document.querySelector('.dzien-row'); const a = [...r.children].map(e => e.className || e.id); return a.indexOf('lesson-count') < a.indexOf('dzien-usun') && a.indexOf('nav') < a.indexOf('lesson-count'); }"
        ),
    )
    page.screenshot(
        path=str(SHOTS / "ux_4_obecnosc_1400.png"),
        clip={"x": 0, "y": 0, "width": 1400, "height": 420},
    )

    # 2 + 3. oceny
    page.click('button.tab:has-text("Oceny")')
    page.wait_for_timeout(300)
    lab = page.locator("#tab-oceny .klasa-tytul .s").inner_text()
    check(
        "oceny: etykieta obok selecta nie udaje drugiego selektora",
        "▾" not in lab and "ZSS" not in lab,
        lab,
    )
    check(
        "oceny: jeden select klasy w tytule",
        page.locator("#tab-oceny .klasa-tytul select").count() == 1,
    )
    check(
        "oceny: nagłówek Syst. ma klasę kol-auto + „auto”",
        page.locator("#tab-oceny th.col-ocena.kol-auto .auto-badge").count() >= 1,
    )
    check(
        "oceny: komórki Syst. mają kol-auto",
        page.locator("#tab-oceny td.cell-ocena.kol-auto").count() == 6,
    )
    check(
        "oceny: komórka Syst. bez kursora pointer",
        page.evaluate(
            "() => getComputedStyle(document.querySelector('td.cell-ocena.kol-auto .cell-ocena-content')).cursor"
        )
        == "default",
    )
    check(
        "oceny: pusta komórka Syst. pokazuje „—”, nie „+”",
        page.evaluate(
            "() => getComputedStyle(document.querySelector('td.cell-ocena.kol-auto.empty .cell-ocena-content'), '::before').content"
        )
        == '"—"',
    )
    # kolumna ręczna dla porównania afordancji
    page.evaluate(
        "() => { state.gradeColumns.push({ id: 'k1', shortName: 'Skok', fullName: 'Skok w dal', weight: 1, date: '2026-09-15' }); state.grades.k1 = { u1: 80, u3: 60 }; save(); refreshAll(); }"
    )
    page.wait_for_timeout(200)
    check(
        "oceny: kolumna ręczna dalej klikalna (pointer)",
        page.evaluate(
            "() => getComputedStyle(document.querySelector('td.cell-ocena[data-col=k1] .cell-ocena-content')).cursor"
        )
        == "pointer",
    )
    check(
        "oceny: nagłówek ręczny bez „auto”",
        page.locator("#tab-oceny th.col-ocena:not(.kol-auto) .auto-badge").count() == 0,
    )
    page.locator("#tab-oceny table").scroll_into_view_if_needed()
    page.screenshot(path=str(SHOTS / "ux_3_oceny_1400.png"), full_page=True)

    # 5. Plan — chipy dni wolnych w zapisie DD.MM, nie MM-DD (user 19.09: „zaczynają się od miesiąca")
    page.evaluate(
        "() => { const p = planAktywny(true); p.wolne = ['2026-11-11', '2026-12-23', '2026-12-24']; save(); renderPlanUstawienia(); }"
    )
    page.click('button.tab:has-text("Plan")')
    page.wait_for_timeout(300)
    chips = page.locator("#planUstawienia .wolny-chip").all_inner_texts()
    check(
        "plan: chip dnia wolnego = DD.MM",
        bool(chips) and chips[0].startswith("11.11"),
        str(chips),
    )
    check(
        "plan: zakres = DD.MM – DD.MM",
        len(chips) > 1 and chips[1].startswith("23.12 – 24.12"),
        str(chips),
    )

    check("bez błędów JS", not errors, str(errors[:3]))
    browser.close()

httpd.shutdown()
print("\nFAIL: %d" % len(FAILS))
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
