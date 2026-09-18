# Test widoku dziennego + belek C v2 (2026-09-18): lekcje dnia obok siebie (otwarta = tabela,
# podglądy = klik nagłówka), przełącznik Dzień/Tydzień, kolumna „inne", stopka kolumny
# (Zapisz + do VULCANa/Librusa), forma ćwiczył/ćwiczyła, reguły liczenia, 4 okna Systematyczności,
# telefon = przewijanie poziome. Zrzuty do _zrzuty/cv2_*.png (oko usera).
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8771

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


DZIS = "2026-09-18"  # piątek (indeks 4)
PLAN = {
    "od": "2026-09-01",
    "do": "2027-06-30",
    "klasy": {
        "7b": {"4": [3]},
        "8c": {"4": [5]},
        "4dLO": {"4": [2]},
        "2 inf": {"4": [1]},
    },
    "inne": {"EZ 4a": {"4": [4]}},
    "wolne": [],
}

FIXTURE = """(p) => {
  const st = (n, pref) => Array.from({length: n}, (_, i) => ({ id: pref + (i + 1), name: 'Uczeń' + pref + ' ' + 'ABCDEFGHIJ'[i], longTermReleased: false, height: '', weight: '' }));
  state.classes[0].school = 'ZSS'; state.classes[0].name = '7b'; state.classes[0].students = st(6, 'u');
  const c8 = makeClass('ZSS', '8c', st(5, 'v')); state.classes.push(c8);
  const c4 = makeClass('ZSS', '4dLO', st(5, 'w')); c4.plec = 'dz'; state.classes.push(c4);
  const c2 = makeClass('Technikum', '2 inf', st(4, 'x')); state.classes.push(c2);
  activateClass(state.classes[0].id);
  state.classes[0].attendance['2026-09-18'] = { u1: 'C', u2: 'BS', u3: attWrite('C', true) };
  state.classes[0].attendance['2026-09-11'] = { u1: 'C', u2: 'C', u3: 'NB', u4: 'C' };
  c2.attendance['2026-09-18'] = { x1: 'C', x2: 'NC', x3: 'C', x4: 'C' };
  zaleglePlanZastosuj(p);
  state.currentDate = '2026-09-18';
  save(); refreshAll();
}"""

VIS = "(sel) => { const e = document.querySelector(sel); return !!(e && e.offsetParent !== null); }"

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
    page.evaluate("(d) => wybierzLekcje(state.classes[0].id, d, 3)", DZIS)
    page.wait_for_timeout(300)
    page.click("details.pomoc[data-pomoc=obecnosc] > summary")
    page.wait_for_timeout(200)

    # --- belki ---
    check(
        "zakładka Reguły istnieje",
        page.locator('button.tab:has-text("Reguły")').count() == 1,
    )
    check(
        "w pasku górnym nie ma paska klasy",
        page.evaluate("() => !document.querySelector('.topbar #classBar')"),
    )
    check(
        "pasek klasy mieszka w Uczniowie",
        page.evaluate("() => !!document.querySelector('#tab-uczniowie #classBar')"),
    )
    check(
        "aktywna zakładka zlewa się z panelem (białe tło)",
        page.evaluate(
            "() => getComputedStyle(document.querySelector('.tab.active')).backgroundColor"
        )
        == page.evaluate(
            "() => getComputedStyle(document.querySelector('.tab-content.active')).backgroundColor"
        ),
    )

    # --- widok dnia ---
    check("domyślnie widok Dzień", page.evaluate("() => state.widok") == "dzien")
    check(
        "pasek tygodnia schowany w widoku Dzień", not page.evaluate(VIS, "#planTydzien")
    )
    check(
        "data słownie", page.text_content("#dzienData").strip() == "piątek, 18 września"
    )
    n_przed = page.locator("#kolPrzed .kol").count()
    n_po = page.locator("#kolPo .kol").count()
    check("kolumny przed otwartą: 2 (L1 2 inf, L2 4dLO)", n_przed == 2, n_przed)
    check("kolumny po otwartej: 2 (L4 EZ inne, L5 8c)", n_po == 2, n_po)
    check(
        "kolumna inne (EZ 4a) kreskowana, bez tabeli",
        page.locator("#kolPo .kol.inne[data-inne='EZ 4a']").count() == 1
        and page.locator("#kolPo .kol.inne table").count() == 0,
    )
    head = page.text_content("#kolOtwartaHead")
    check(
        "nagłówek otwartej: L3 · 7b · otwarta · % dotąd",
        "L3" in head and "7b" in head and "otwarta" in head and "%" in head,
        head,
    )
    check(
        "4dLO ma znacznik dz. w nagłówku",
        "dz."
        in page.text_content(
            "#kolPrzed .kol[data-cls='%s'] .kol-head"
            % page.evaluate("() => state.classes[2].id")
        ),
    )
    check(
        "kolumny liczników schowane w widoku dnia",
        not page.evaluate(VIS, "#attendanceTable th.stat"),
    )
    check("% dotąd widoczny", page.evaluate(VIS, "#attendanceTable .percent-cell"))
    # podgląd 2 inf: wpis jest → stopka „do Librusa" (szkoła Technikum)
    cid2 = page.evaluate("() => state.classes[3].id")
    check(
        "podgląd 2 inf ma klasę jest",
        "jest"
        in (page.get_attribute("#kolPrzed .kol[data-cls='%s']" % cid2, "class") or ""),
    )
    lib = page.text_content("#kolPrzed .kol[data-cls='%s'] .zapisz-mini button" % cid2)
    check("technikum → „do Librusa”", "do Librusa" in lib, lib)
    check(
        "podgląd 2 inf: 3 ćwiczyło · 1 nć",
        "3 ćwiczyło" in page.text_content("#kolPrzed .kol[data-cls='%s'] .sum" % cid2),
    )
    check(
        "stopka otwartej: „do VULCANa” (ZSS)",
        "do VULCANa" in page.text_content("#saveBarKopiuj"),
    )
    check(
        "stopka otwartej: Bez statusu 3 → ćwiczył",
        "Bez statusu" in page.text_content("#saveBarStatus")
        and "ćwiczył" in page.text_content("#saveBarStatus"),
    )
    page.screenshot(path=str(SHOTS / "cv2_dzien_1400.png"), full_page=True)

    # klik nagłówka podglądu 8c → otwiera lekcję (podgląd, nie edycja w kolumnie)
    cid8 = page.evaluate("() => state.classes[1].id")
    page.click("#kolPo .kol[data-cls='%s'] .kol-head" % cid8)
    page.wait_for_timeout(300)
    check(
        "klik nagłówka 8c: klasa bieżąca = 8c",
        page.evaluate("() => getCurrentClass().name") == "8c",
    )
    check(
        "klik nagłówka 8c: nr lekcji = 5 (jedyna → klucz bez nr)",
        page.evaluate("() => state.currentNr") is None
        and page.evaluate("() => attKey()") == DZIS,
    )
    check(
        "teraz przed otwartą 4 kolumny (2 inf, 4dLO, 7b, EZ), po 0",
        page.locator("#kolPrzed .kol").count() == 4
        and page.locator("#kolPo .kol").count() == 0,
    )
    check(
        "tabela nadal jedna (klawiatura ma jedno miejsce wpisu)",
        page.locator("#attendanceBody").count() == 1,
    )
    check(
        "7b w podglądzie ma ✓ i bs",
        "bs"
        in page.text_content(
            "#kolPrzed .kol[data-cls='%s'] table"
            % page.evaluate("() => state.classes[0].id")
        ),
    )

    # klawiatura działa w otwartej kolumnie
    page.click("h1")
    page.keyboard.press("n")
    page.wait_for_timeout(200)
    check(
        "klawisz n nadaje NĆ w otwartej kolumnie",
        page.evaluate("(d) => attRead(state.attendance[d].v1).s", DZIS) == "NC",
    )

    # forma ćwiczyła — 4dLO
    page.evaluate("(d) => wybierzLekcje(state.classes[2].id, d, 2)", DZIS)
    page.wait_for_timeout(200)
    check(
        "4dLO: stopka mówi „ćwiczyła”",
        "ćwiczyła" in page.text_content("#saveBarStatus"),
    )
    check(
        "cwLabel domyślnie ćwiczył",
        page.evaluate("() => cwLabel(state.classes[0])") == "ćwiczył",
    )

    # Zapisz lekcję → „zapisano HH:MM"
    page.evaluate("() => finalizeLesson()")
    page.wait_for_timeout(200)
    page.click(
        "#confirmModal button.primary, #confirmModal .btn-ok, #confirmModal button:has-text('OK')"
    )
    page.wait_for_timeout(300)
    check(
        "po zapisie stopka: zapisano HH:MM",
        "Zapisano" in page.text_content("#saveBarStatus")
        and ":" in page.text_content("#saveBarStatus"),
        page.text_content("#saveBarStatus"),
    )
    check(
        "po zapisie przycisk Zapisz schowany, Kopiuj zostaje",
        not page.evaluate(VIS, "#saveBarBtn") and page.evaluate(VIS, "#saveBarKopiuj"),
    )

    # przełącznik Tydzień
    page.click("#widokPrzel button[data-w=tydzien]")
    page.wait_for_timeout(300)
    check("Tydzień: pasek tygodnia widoczny", page.evaluate(VIS, "#planTydzien"))
    check("Tydzień: podglądy schowane", not page.evaluate(VIS, "#kolPrzed .kol"))
    check(
        "Tydzień: liczniki w tabeli widoczne",
        page.evaluate(VIS, "#attendanceTable th.stat"),
    )
    check(
        "preferencja widoku w localStorage",
        page.evaluate("() => localStorage.getItem('dziennik_wf_widok')") == "tydzien",
    )
    page.click("#widokPrzel button[data-w=dzien]")
    page.wait_for_timeout(200)

    # bez planu: otwarta kolumna stoi sama
    page.evaluate(
        "() => { const p = state.planWf; state.planWf = null; renderAttendance(); state._p = p; }"
    )
    check(
        "bez planu: zero podglądów, tabela jest",
        page.locator("#kolPrzed .kol").count() == 0
        and page.locator("#kolPo .kol").count() == 0
        and page.evaluate(VIS, "#attendanceTable"),
    )
    page.evaluate("() => { state.planWf = state._p; renderAttendance(); }")

    # --- reguły liczenia ---
    page.evaluate("(d) => wybierzLekcje(state.classes[0].id, d, 3)", DZIS)
    base = page.evaluate("() => getStudentStats('u2')")
    check(
        "domyślnie BS w bazie (u2: 1 C + 1 BS → 50%)",
        base["baza"] == 2 and round(base["percent"]) == 50,
        base,
    )
    page.evaluate("() => regulaUstaw('bsBaza', false)")
    page.wait_for_timeout(200)
    r2 = page.evaluate("() => getStudentStats('u2')")
    check(
        "bsBaza=off: BS wypada z bazy (100%)",
        r2["baza"] == 1 and round(r2["percent"]) == 100,
        r2,
    )
    page.evaluate("() => regulaUstaw('bsBaza', true)")
    page.evaluate("() => regulaUstaw('spPol', true)")
    r3 = page.evaluate("() => getStudentStats('u3')")
    check(
        "spPol=on: C ze spóźnieniem = pół (u3: 0.5/2)",
        r3["cwiczyl"] == 0.5 and r3["baza"] == 2,
        r3,
    )
    page.evaluate("() => regulaUstaw('spPol', false)")
    page.evaluate("() => regulaUstaw('progZielony', 95)")
    check(
        "próg zielony 95: 96% high, 94% mid",
        page.evaluate("() => pctKlasa(96) + ' ' + pctKlasa(94)") == "high mid",
    )
    page.evaluate("() => regulaUstaw('progZielony', 90)")
    check(
        "ustawienia w migawce kopii",
        page.evaluate(
            "() => !!snapshotData().ustawienia && snapshotData().ustawienia.reguly.progZielony === 90"
        ),
    )

    # --- e-dziennik per szkoła ---
    check(
        "Technikum domyślnie librus, ZSS vulcan",
        page.evaluate(
            "() => edziennikSzkoly('Technikum') + ' ' + edziennikSzkoly('ZSS')"
        )
        == "librus vulcan",
    )
    page.evaluate("() => { edziennikUstaw('ZSS', 'librus'); save(); refreshAll(); }")
    check(
        "ZSS → librus po ustawieniu (stopka)",
        "do Librusa" in page.text_content("#saveBarKopiuj"),
    )
    page.evaluate("() => { edziennikUstaw('ZSS', 'vulcan'); save(); refreshAll(); }")

    # --- 4 okna Systematyczności ---
    check(
        "bez granicy: 1 okno",
        page.evaluate("() => oknaSystematycznosci(getCurrentClass()).length") == 1,
    )
    page.evaluate("() => oknoUstaw('semesterBreak', '2027-01-25')")
    page.wait_for_timeout(200)
    okna = page.evaluate(
        "() => oknaSystematycznosci(getCurrentClass()).map(w => [w.shortName, w.from, w.to])"
    )
    check(
        "granica → 4 okna I.1 I.2 II.1 II.2",
        [o[0] for o in okna] == ["Syst. I.1", "Syst. I.2", "Syst. II.1", "Syst. II.2"],
        okna,
    )
    check(
        "środek I półrocza wyliczony między 1.09 a granicą",
        okna[0][2] == okna[1][1] and "2026-11" in okna[0][2],
        okna[0][2],
    )
    check(
        "środek II półrocza wyliczony między granicą a 30.06",
        okna[2][2] == okna[3][1] and "2027-04" in okna[2][2],
        okna[2][2],
    )
    page.evaluate("() => oknoUstaw('polI', '2026-11-30')")
    check(
        "ręczny środek I nadpisuje auto",
        page.evaluate("() => oknaSystematycznosci(getCurrentClass())[0].to")
        == "2026-11-30",
    )
    page.click('button.tab:has-text("Oceny")')
    page.wait_for_timeout(300)
    check(
        "Oceny: 4 kolumny auto Syst.",
        page.evaluate("() => state.gradeColumns.filter(c => c.auto).length") == 4,
    )
    check(
        "okna klasy w meta scalania (listki k)",
        page.evaluate("() => JSON.parse(listkiKlasy(getCurrentClass()).k).polI")
        == "2026-11-30",
    )

    # --- zakładka Reguły ---
    page.click('button.tab:has-text("Reguły")')
    page.wait_for_timeout(300)
    check(
        "Reguły cytują PZO",
        "Przedmiotowe Zasady Oceniania" in page.text_content("#tab-reguly"),
    )
    check(
        "Reguły: szkoły ZSS i Technikum z e-dziennikiem",
        page.locator("#regSzkoly select").count() == 2,
    )
    check(
        "Reguły: okna pokazują 4 daty",
        "I.1" in page.text_content("#regOknaOpis")
        and "II.2" in page.text_content("#regOknaOpis"),
    )
    page.screenshot(path=str(SHOTS / "cv2_reguly_1400.png"), full_page=True)

    page.click('button.tab:has-text("Uczniowie")')
    page.wait_for_timeout(300)
    check(
        "Uczniowie: select formy (płeć klasy)", page.locator("#klasaPlec").count() == 1
    )
    page.screenshot(path=str(SHOTS / "cv2_uczniowie_1400.png"))
    page.click('button.tab:has-text("Pomiary")')
    page.wait_for_timeout(200)
    check(
        "Pomiary: tytuł klasy z wyborem",
        page.locator("#tab-pomiary .klasa-tytul select").count() == 1,
    )

    # --- telefon 390 px ---
    page.set_viewport_size({"width": 390, "height": 800})
    page.click('button.tab:has-text("Obecno")')
    page.wait_for_timeout(400)
    sw, cw = page.evaluate(
        "() => { const e = document.getElementById('dzienKolumny'); return [e.scrollWidth, e.clientWidth]; }"
    )
    check("390 px: kolumny przewijane poziomo", sw > cw, (sw, cw))
    nav_top = page.evaluate(
        "() => [...document.querySelectorAll('.dzien-row .nav button')].map(b => Math.round(b.getBoundingClientRect().top))"
    )
    check("390 px: ◀ dziś ▶ w jednym wierszu", len(set(nav_top)) == 1, nav_top)
    check(
        "390 px: strona nie przewija się poziomo",
        page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth + 1"
        ),
    )
    page.screenshot(path=str(SHOTS / "cv2_dzien_390.png"), full_page=True)

    check("brak błędów JS", not errors, errors[:3])
    browser.close()

if FAILS:
    print("\nWYNIK: %d FAIL\n  " % len(FAILS) + "\n  ".join(FAILS))
    sys.exit(1)
print("\nWYNIK: OK (0 FAIL) — widok dzienny + belki C v2")
