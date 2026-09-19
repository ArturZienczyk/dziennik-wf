# Test zastępstw, poziom 1 (2026-09-19): (a) zastępstwo zamiast mojej lekcji — kafelek ciepły z klasą
# zastępowaną, planowa klasa przekreślona, lekcja nie jest zaległa, bez wpisu; (b) zastępstwo na okienku
# przez kafelek „+ zastępstwo” → modal (okienko + numer); kopia (snapshot → scalKopie) niesie oba;
# wpis frekwencji zdejmuje zastępstwo; Statystyki liczą; Plan: dopasowanie nazw w Zaawansowane.
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8782
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
    ISO = "2026-09-04"  # piątek: 2 inf L1, 4dLO L2, 7b L3, EZ L4, 8c L5
    page.evaluate(
        "(iso) => { ustawWidok('dzien'); wybierzLekcje(state.classes[0].id, iso, 3); }",
        ISO,
    )
    page.wait_for_timeout(300)
    c8 = page.evaluate("() => state.classes.find(c => c.name === '8c').id")
    K8 = ISO + "#5"

    # 1. Przed: 8c L5 zaległa (dzień miniony bez wpisu)
    zal = lambda: page.evaluate(
        "(d) => zaleglePolicz(d).map(x => x.clsName + ' ' + x.wpis)", "2026-09-10"
    )
    check("przed: 8c 4.09 L5 na liście zaległych", "8c " + K8 in zal(), zal())

    # 2. (a) zastępstwo zamiast lekcji 8c — z panelu Zaległe (przycisk) → modal → zapis
    page.click("#zalegleChip") if page.locator(
        "#zalegleChip"
    ).count() else page.evaluate("() => renderZalegle()")
    page.wait_for_timeout(200)
    page.evaluate("(a) => zastepstwoOkno(a[0], a[1])", [c8, K8])
    page.wait_for_timeout(150)
    check(
        "modal zastępstwa otwarty, bez wyboru lekcji (lekcja znana)",
        page.evaluate(
            "() => document.getElementById('zastModal').classList.contains('active') && document.getElementById('zastLekcja').parentElement.style.display === 'none'"
        ),
    )
    page.fill("#zastKlasa", "6a")
    page.fill("#zastZaKogo", "A.K.")
    page.click("#zastModal button:has-text('Zapisz')")
    page.wait_for_timeout(300)
    check(
        "cls.zastepstwa zapisane",
        page.evaluate(
            "(a) => JSON.stringify((state.classes.find(c => c.id === a) .zastepstwa || {}))",
            c8,
        )
        == '{"%s":{"klasa":"6a","zaKogo":"A.K."}}' % K8,
    )
    check("po zastępstwie: 8c L5 NIE jest zaległa", "8c " + K8 not in zal(), zal())
    kaf = page.locator("#kolPrzed .kol.zastepstwo[data-cls='%s']" % c8)
    check("kafelek 8c ma klasę .zastepstwo", kaf.count() == 1)
    txt = kaf.inner_text() if kaf.count() else ""
    check(
        "kafelek: 6a widoczna, 8c przekreślona, 'za A.K.'",
        "6a" in txt
        and "8c" in txt
        and "za A.K." in txt
        and "zastępstwo" in txt.lower(),
        txt,
    )
    check("kafelek: bez 'brak wpisu'", "brak wpisu" not in txt)
    check(
        "planowa klasa przekreślona (.plan-klasa)",
        kaf.locator(".plan-klasa").count() == 1
        and kaf.locator(".plan-klasa").inner_text() == "8c",
    )

    check(
        "lista Zaległych zostaje pod modalem (z-index), po zapisie nadal otwarta",
        page.evaluate(
            "() => document.getElementById('zalegleModal').classList.contains('active')"
        ),
    )
    page.evaluate("() => zamknijZalegle()")

    # 3. Pasek tygodnia: st = 'z'
    page.evaluate("() => ustawWidok('tydzien')")
    page.wait_for_timeout(250)
    pl = page.locator("#planTydzien .plan-lekcja.zastepstwo")
    check(
        "Tydzień: lekcja 8c oznaczona .zastepstwo, st 'z'",
        pl.count() == 1 and pl.locator(".st").inner_text() == "z",
    )
    page.evaluate("() => ustawWidok('dzien')")
    page.wait_for_timeout(250)

    # 4. (b) okienko przez kafelek „+ zastępstwo” → modal z wyborem → okienko L8
    check(
        "kafelek „+ zastępstwo” na pasku dnia",
        page.locator("#kolPrzed .kol.okienko-zast button").count() == 1,
    )
    page.click("#kolPrzed .kol.okienko-zast button")
    page.wait_for_timeout(150)
    opcje = page.evaluate(
        "() => [...document.querySelectorAll('#zastLekcja option')].map(o => o.textContent)"
    )
    check(
        "modal: wybór lekcji = moje lekcje bez wpisu + okienko (7b otwarta bez wpisu też)",
        any("2 inf" in o for o in opcje)
        and any("4dLO" in o for o in opcje)
        and opcje[-1].startswith("okienko"),
        opcje,
    )
    check(
        "modal: 8c (już zastępstwo) nie na liście",
        not any("8c" in o for o in opcje),
        opcje,
    )
    page.select_option("#zastLekcja", "okienko")
    page.wait_for_timeout(100)
    check("okienko → pole numeru widoczne", page.locator("#zastNr").is_visible())
    page.fill("#zastNr", "8")
    page.fill("#zastKlasa", "5b")
    page.click("#zastModal button:has-text('Zapisz')")
    page.wait_for_timeout(300)
    check(
        "state.zastepstwaOkienka['2026-09-04#8'] = 5b",
        page.evaluate("() => JSON.stringify(state.zastepstwaOkienka)")
        == '{"%s#8":{"klasa":"5b","zaKogo":""}}' % ISO,
    )
    ok = page.locator("#kolPrzed .kol.zastepstwo.okienko")
    check(
        "kafelek okienka L8 5b na pasku",
        ok.count() == 1 and "L8" in ok.inner_text() and "5b" in ok.inner_text(),
        ok.inner_text() if ok.count() else "",
    )

    # 5. Walidacja modalu: pusta klasa nie zapisuje
    page.evaluate("(a) => zastepstwoOkno(a[0], a[1])", [c8, K8])
    page.wait_for_timeout(100)
    page.fill("#zastKlasa", "")
    page.click("#zastModal button:has-text('Zapisz')")
    page.wait_for_timeout(100)
    check(
        "pusta klasa: modal zostaje, dane nietknięte",
        page.evaluate(
            "() => document.getElementById('zastModal').classList.contains('active')"
        )
        and page.evaluate(
            "(a) => !!state.classes.find(c => c.id === a).zastepstwa[%r]" % K8, c8
        ),
    )
    page.click("#zastModal button:has-text('Anuluj')")

    # 6. Statystyki: licznik
    page.click("button.tab:has-text('Statystyki')")
    page.wait_for_timeout(300)
    st = page.inner_text("#summaryGrid")
    check(
        "Statystyki: karta 'Zastępstw' = 2",
        "zastępstw" in st.lower() and page.evaluate("() => zastepstwaLicz()") == 2,
        st.replace("\n", " | "),
    )
    page.click("button.tab:has-text('Obecność')")

    # 7. Kopia: snapshot niesie oba, scalKopie na wyczyszczonym stanie przywraca
    snap = page.evaluate("() => JSON.parse(JSON.stringify(snapshotData()))")
    check(
        "snapshot ma zastepstwaOkienka",
        snap.get("zastepstwaOkienka") == {ISO + "#8": {"klasa": "5b", "zaKogo": ""}},
    )
    check(
        "snapshot: klasa 8c niesie zastepstwa",
        any(c.get("zastepstwa") for c in snap["classes"]),
    )
    # świeże urządzenie: liścia nigdy nie było (bez nagrobka) — lokalne skasowanie miałoby nowszy znacznik i słusznie wygrałoby
    page.evaluate(
        "(a) => { const c = state.classes.find(x => x.id === a); delete c.zastepstwa[%r]; delete c._t['z|%s']; state.zastepstwaOkienka = {}; stemplujBaza(); }"
        % (K8, K8),
        c8,
    )
    page.wait_for_timeout(200)
    w = page.evaluate("(d) => scalKopie(d)", snap)
    page.evaluate("() => { save(); refreshAll(); }")
    page.wait_for_timeout(300)
    check(
        "po scaleniu: zastępstwo 8c wróciło (liść z|klucz)",
        page.evaluate(
            "(a) => !!(state.classes.find(c => c.id === a).zastepstwa || {})[%r]" % K8,
            c8,
        ),
        w,
    )
    check(
        "po scaleniu: okienko wróciło",
        page.evaluate("() => !!state.zastepstwaOkienka[%r]" % (ISO + "#8")),
    )
    check(
        "kafelki po scaleniu: 2 × .zastepstwo",
        page.locator("#kolPrzed .kol.zastepstwo").count() == 2,
    )

    # 8. Wpis frekwencji przeczy zastępstwu: otwórz 8c L5, nieByloZdejmij (wołane przy zapisie statusu) zdejmuje
    page.evaluate(
        "(a) => { wybierzLekcje(a[0], a[1], 5); nieByloZdejmij(); save(); refreshAll(); }",
        [c8, ISO],
    )
    page.wait_for_timeout(300)
    check(
        "wpis frekwencji zdejmuje zastępstwo 8c",
        not page.evaluate(
            "(a) => !!(state.classes.find(c => c.id === a).zastepstwa || {})[%r]" % K8,
            c8,
        ),
    )
    check(
        "okienko zostaje (inny byt)",
        page.evaluate("() => !!state.zastepstwaOkienka[%r]" % (ISO + "#8")),
    )

    # 9. Zdejmij okienko przez modal
    page.evaluate("(k) => zastepstwoOkno(null, k)", ISO + "#8")
    page.wait_for_timeout(100)
    check(
        "modal edycji okienka: numer zablokowany, 'zdejmij' widoczny",
        page.evaluate("() => document.getElementById('zastNr').disabled")
        and page.locator("#zastUsun").is_visible(),
    )
    page.click("#zastUsun")
    page.wait_for_timeout(250)
    check(
        "okienko zdjęte",
        page.evaluate("() => Object.keys(state.zastepstwaOkienka).length === 0"),
    )
    check(
        "pasek bez .zastepstwo", page.locator("#kolPrzed .kol.zastepstwo").count() == 0
    )

    # 10. Render zestawu: 7b otwarta bez wpisu, 8c zastępstwo, 4dLO nie było — zrzut do obejrzenia
    page.evaluate(
        "(a) => { wybierzLekcje(state.classes[0].id, '2026-09-04', 3); zastepstwoZapisz(a[0], a[1], '6a', 'A.K.'); const c4 = state.classes.find(c => c.name === '4dLO'); c4.odwolane = { ['%s#2']: 'wycieczka' }; save(); refreshAll(); }"
        % ISO,
        [c8, K8],
    )
    page.wait_for_timeout(300)
    (ROOT / "_zrzuty").mkdir(exist_ok=True)
    page.locator("#tab-obecnosc .dzien-kolumny").screenshot(
        path=str(ROOT / "_zrzuty" / "zastepstwa-pasek.png")
    )
    wys = page.evaluate(
        "() => [...document.querySelectorAll('#kolPrzed .kol')].map(e => ({ k: e.className, h: Math.round(e.getBoundingClientRect().height) }))"
    )
    h_zast = [w["h"] for w in wys if "zastepstwo" in w["k"]]
    h_plain = [
        w["h"]
        for w in wys
        if "podglad" in w["k"]
        and "zastepstwo" not in w["k"]
        and "niebylo" not in w["k"]
    ]
    check(
        "rytm zestawu: kafelek zastępstwa tej wysokości co zwykły kafelek lekcji (1 linia)",
        bool(h_zast) and bool(h_plain) and set(h_zast) == set(h_plain),
        str(wys),
    )

    check("brak błędów JS", not errors, errors)
    browser.close()

print("\nWYNIK:", "OK" if not FAILS else "BŁĘDY (%d FAIL)" % len(FAILS))
sys.exit(1 if FAILS else 0)
