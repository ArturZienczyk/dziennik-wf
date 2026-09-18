# Test end-to-end „Zaległe lekcje”: plan-wf.json + kalendarium vs wpisy frekwencji.
# Sprawdza (v2 od 2026-09-18: numery lekcji, siatka, dni wolne): chip bez planu, wczytanie planu, dopasowanie klasy po nazwie, liczenie
# zaległości (dni tygodnia, dni wolne, dziś pominięte), „nie było” znika na stałe,
# „wpisz” przełącza klasę i datę, plan przeżywa zapis/odczyt z magazynu.
import sys
import json
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8769

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


# Plan testowy: 7b Pn/Wt/Śr/Pi, 8c Pn/Wt/Śr/Pi; wolne 2026-09-14 (Pn); ważny 1–30.09.
PLAN = {
    "od": "2026-09-01",
    "do": "2026-09-30",
    "wygenerowano": "2026-09-18",
    "klasy": {"7b": [0, 1, 2, 4], "8c": [0, 1, 2, 4], "4dLO": [0, 1, 2]},
    "wolne": ["2026-09-14"],
}
DZIS = "2026-09-18"  # piątek

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
    page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
    page.wait_for_timeout(600)

    # 1. bez planu: chip „brak planu”
    check("chip bez planu", "brak planu" in page.inner_text("#zalegleChip"))

    # 2. dwie klasy: „7 b” (auto po nazwie → 7b) i „5 inf” (brak w planie → nie licz)
    page.evaluate("""() => {
      state.classes[0].name = '7 b';
      const c2 = makeClass('', '5 inf', []); state.classes.push(c2);
      activateClass(state.classes[0].id); save(); refreshAll();
    }""")
    page.evaluate("(p) => { zaleglePlanZastosuj(p); refreshAll(); }", PLAN)
    check("plan wczytany", page.evaluate("() => zaleglePlany().length") == 1)
    check(
        "auto-dopasowanie '7 b' → 7b",
        page.evaluate("() => zaleglePlanKlasa(state.classes[0])") == "7b",
    )
    check(
        "'5 inf' bez klucza → nie licz",
        page.evaluate("() => zaleglePlanKlasa(state.classes[1])") == "",
    )

    # 3. liczenie: 1–17.09, dni Pn/Wt/Śr/Pi, minus 14.09 (wolne), dziś 18.09 pominięty
    oczek = [
        "2026-09-01",
        "2026-09-02",
        "2026-09-04",
        "2026-09-07",
        "2026-09-08",
        "2026-09-09",
        "2026-09-11",
        "2026-09-15",
        "2026-09-16",
    ]
    z = page.evaluate("(d) => zaleglePolicz(d).map(x => x.date)", DZIS)
    check("zaległe 7b = 9 dat (bez wolnego 14.09 i bez dziś)", z == oczek, z)

    # 4. wpis frekwencji zdejmuje datę
    page.evaluate(
        "() => { state.attendance['2026-09-01'] = { u1: 'C' }; save(); refreshAll(); }"
    )
    z = page.evaluate("(d) => zaleglePolicz(d).map(x => x.date)", DZIS)
    check("wpis 1.09 zdejmuje pozycję", "2026-09-01" not in z and len(z) == 8, z)

    # 5. modal + „nie było” z powodem
    page.click("#zalegleChipBtn")
    page.wait_for_timeout(200)
    check(
        "modal otwarty",
        page.evaluate(
            "() => document.getElementById('zalegleModal').classList.contains('active')"
        ),
    )
    check("lista ma 8 pozycji", page.locator("#zalegleLista .zalegle-poz").count() == 8)
    page.screenshot(path=str(SHOTS / "zalegle_1_modal.png"))
    cid = page.evaluate("() => state.classes[0].id")
    page.select_option("#zaleglePowod_%s_2026-09-02" % cid, "wycieczka")
    page.click("#zaleglePowod_%s_2026-09-02 + button" % cid)
    page.wait_for_timeout(200)
    check(
        "'nie było' zapisane z powodem",
        page.evaluate("() => state.classes[0].odwolane['2026-09-02']") == "wycieczka",
    )
    check(
        "lista po 'nie było' = 7",
        page.locator("#zalegleLista .zalegle-poz").count() == 7,
    )

    # 6. „wpisz” przełącza datę i zamyka modal
    page.click("#zalegleLista .zalegle-poz >> nth=0 >> button.primary")
    page.wait_for_timeout(200)
    check(
        "wpisz: data lekcji = 4.09",
        page.evaluate("() => state.currentDate") == "2026-09-04",
    )
    check(
        "wpisz: modal zamknięty",
        not page.evaluate(
            "() => document.getElementById('zalegleModal').classList.contains('active')"
        ),
    )
    check("wpisz: pole daty", page.input_value("#lessonDate") == "2026-09-04")
    page.screenshot(path=str(SHOTS / "zalegle_2_po_wpisz.png"))

    # 7. ręczne dopasowanie „5 inf” → 4dLO i zmiana licznika
    page.evaluate(
        "(id) => zaleglePlanKlasaZmien(id, '4dLO')",
        page.evaluate("() => state.classes[1].id"),
    )
    n = page.evaluate(
        "(d) => zaleglePolicz(d).filter(x => x.clsName === '5 inf').length", DZIS
    )
    check(
        "ręczne dopasowanie liczy 4dLO (Pn/Wt/Śr, 1–17.09 minus 14.09) = 7", n == 7, n
    )

    # 8. plan i „nie było” przeżywają zapis do magazynu
    page.wait_for_timeout(300)
    st = page.evaluate("() => zamekStanZapisany()")
    check(
        "planWf w magazynie",
        st.get("planWf", {}).get("plany", [{}])[0].get("od") == "2026-09-01",
    )
    check(
        "odwolane w magazynie",
        st["classes"][0].get("odwolane", {}).get("2026-09-02") == "wycieczka",
    )
    check("planKlasa w magazynie", st["classes"][1].get("planKlasa") == "4dLO")

    # 9. prawdziwy plik plan-wf.json z folderu planu wchodzi przez ten sam walidator
    real = ROOT.parent.parent / "plan-roczny" / "plan-lekcji-2026-09" / "plan-wf.json"
    if real.exists():
        page.evaluate(
            "(p) => { zaleglePlanZastosuj(p); refreshAll(); }",
            json.loads(real.read_text(encoding="utf-8")),
        )
        check(
            "prawdziwy plan-wf.json: upsert po 'od' (nadal 1 plan)",
            page.evaluate("() => zaleglePlany().length") == 1,
        )
        check(
            "prawdziwy plan: 8 klas",
            page.evaluate("() => zalegleKluczePlanu().length") == 8,
        )
    # 10. plan v2 (numery lekcji): klasa „2 inf” → klucz „2t”, piątek L2+L3 (dwie godziny z rzędu)
    page.evaluate("""() => {
      const c = makeClass('', '2 inf', [{id: 'u1', name: 'Uczeń Testowy'}]); state.classes.push(c);
      zaleglePlanKlasaZmien(c.id, '2t');
      zaleglePlanZastosuj({od: '2026-09-01', klasy: {'2t': {'4': [2, 3]}}});
      refreshAll();
    }""")
    cid2 = page.evaluate("() => state.classes[state.classes.length - 1].id")
    z2 = lambda: page.evaluate(
        "(d) => zaleglePolicz(d).filter(x => x.clsName === '2 inf').map(x => x.wpis)", DZIS
    )
    check(
        "v2: 2 piątki × 2 lekcje = 4 zaległe z numerami",
        z2() == ["2026-09-04#2", "2026-09-04#3", "2026-09-11#2", "2026-09-11#3"],
        z2(),
    )
    page.evaluate(
        "(id) => { const c = state.classes.find(x => x.id === id); c.attendance['2026-09-04'] = {u1: 'C'}; save(); refreshAll(); }",
        cid2,
    )
    check(
        "wpis pod samą datą pokrywa pierwszą lekcję dnia (zostaje L3)",
        z2() == ["2026-09-04#3", "2026-09-11#2", "2026-09-11#3"],
        z2(),
    )
    page.evaluate(
        "(id) => { const c = state.classes.find(x => x.id === id); c.attendance['2026-09-04#3'] = {u1: 'NB'}; save(); refreshAll(); }",
        cid2,
    )
    check("wpis 'data#3' pokrywa dokładnie L3", z2() == ["2026-09-11#2", "2026-09-11#3"], z2())
    check(
        "statystyki liczą obie lekcje 4.09 osobno",
        page.evaluate(
            "(id) => { activateClass(id); const s = getStudentStats('u1'); return [s.total, s.C, s.NB]; }",
            cid2,
        )
        == [2, 1, 1],
    )
    page.click("#zalegleChipBtn")
    page.wait_for_timeout(200)
    page.select_option("#zaleglePowod_%s_2026-09-11_L2" % cid2, "zastępstwo / zmiana planu")
    page.click("#zaleglePowod_%s_2026-09-11_L2 + button" % cid2)
    page.wait_for_timeout(150)
    check(
        "'nie było' pod kluczem z numerem",
        page.evaluate("(id) => state.classes.find(x => x.id === id).odwolane['2026-09-11#2']", cid2)
        == "zastępstwo / zmiana planu",
    )
    check("zostaje 1 zaległa (11.09 L3)", z2() == ["2026-09-11#3"], z2())
    page.screenshot(path=str(SHOTS / "zalegle_3_dwie_lekcje.png"))
    page.click("#zalegleLista .zalegle-poz:has-text('2 inf') >> button.primary")
    page.wait_for_timeout(200)
    check(
        "wpisz: data + numer lekcji",
        page.evaluate("() => [state.currentDate, state.currentNr, attKey()]")
        == ["2026-09-11", 3, "2026-09-11#3"],
    )
    check("selektor numeru lekcji = 3", page.input_value("#lessonNr") == "3")
    check(
        "podpowiedź przy dacie: L2 i L3 z planu",
        "L2" in page.inner_text("#lessonNrHint") and "L3" in page.inner_text("#lessonNrHint"),
        page.inner_text("#lessonNrHint"),
    )
    page.keyboard.press("c")  # klawiatura: status pod attKey()
    page.wait_for_timeout(150)
    check(
        "klawiatura zapisuje pod 'data#3'",
        page.evaluate("() => (state.attendance['2026-09-11#3'] || {}).u1") == "C",
        page.evaluate("() => Object.keys(state.attendance)"),
    )
    check("po wpisie 0 zaległych dla '2 inf'", z2() == [], z2())
    page.screenshot(path=str(SHOTS / "zalegle_4_obecnosc_L3.png"))

    # 11. siatka w Ustawieniach: klik dnia → numery, klik numeru → plan
    page.click("#zalegleChipBtn")
    page.wait_for_timeout(200)
    page.evaluate("() => { document.querySelector('#zalegleModal details').open = true; }")
    page.wait_for_timeout(100)
    n_kom = page.locator("#zalegleUstawienia .siatka-kom").count()
    check("siatka: 5 komórek na klasę", n_kom == 5 * page.evaluate("() => state.classes.length"), n_kom)
    page.click("#zalegleUstawienia .siatka-kom[data-cls='%s'][data-dzien='0']" % cid2)
    page.wait_for_timeout(150)
    check("klik komórki otwiera 12 numerów", page.locator("#zalegleUstawienia .siatka-nr").count() == 12)
    page.click("#zalegleUstawienia .siatka-nr[data-nr='5']")
    page.wait_for_timeout(150)
    plan2t = lambda: page.evaluate("() => planAktywny(false).klasy['2t']")
    check("klik numeru dopisuje Pn L5 do planu", plan2t() == {"0": [5], "4": [2, 3]}, plan2t())
    check("nowa lekcja w siatce od razu liczy się w Zaległych (Pn 7.09)", "2026-09-07#5" in z2(), z2())
    page.click("#zalegleUstawienia .siatka-nr[data-nr='5']")
    page.wait_for_timeout(150)
    check("drugi klik zdejmuje", plan2t() == {"4": [2, 3]}, plan2t())
    page.screenshot(path=str(SHOTS / "zalegle_5_siatka.png"))

    # 12. dni wolne: od–do + wklejenie tekstu
    page.evaluate("() => wolneDodaj('2026-09-10', '2026-09-11')")
    check(
        "dni wolne od–do dodane",
        page.evaluate("() => planAktywny(false).wolne.filter(x => x >= '2026-09-10' && x <= '2026-09-11')")
        == ["2026-09-10", "2026-09-11"],
    )
    check("wolny piątek 11.09 nie liczy się", z2() == [], z2())
    check(
        "wklejone kalendarium: ISO, DD.MM.RRRR, zakres w linii",
        page.evaluate("(t) => wolneZTekstu(t)", "23.12.2026 – 24.12.2026\nwolne 2027-01-06\nnic tu nie ma")
        == ["2026-12-23", "2026-12-24", "2027-01-06"],
    )
    page.evaluate("() => wolneUsun('2026-09-10', '2026-09-11')")
    check("cofnięcie wolnych: L3 ma wpis, L2 'nie było' → nadal 0", z2() == [], z2())

    # 13. plan v1 obok v2 w tej samej strukturze: 7b (lista dni) dalej liczy per dzień
    check(
        "v1 nadal działa obok v2",
        page.evaluate("(d) => zaleglePolicz(d).filter(x => x.clsName === '7 b').length", DZIS) > 0,
    )

    check(
        "odrzuca zły plik",
        page.evaluate(
            "() => { try { zaleglePlanZastosuj({x:1}); return false; } catch (e) { return true; } }"
        ),
    )

    check("brak błędów JS", not errors, errors)
    browser.close()

httpd.shutdown()
print("\nWYNIK: %s (%d FAIL)" % ("OK" if not FAILS else "BŁĘDY", len(FAILS)))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
