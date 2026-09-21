# Test statusu NS (2026-09-21): „nieobecność z przyczyn szkolnych” — uczeń reprezentuje szkołę
# (zawody, konkurs, wycieczka, poczet). Decyzja usera: NS liczy się JAK ĆWICZYŁ — wchodzi do
# bazy I do licznika. Świadome odstępstwo od litery PZO (tam takie nieobecności z bazy
# wypadają), na korzyść ucznia: formalnie jest na zajęciach szkolnych, a większa baza
# rozcieńcza cenę pojedynczego niećwiczenia (3C+1NĆ+1NS: 75% wg litery PZO, 80% tutaj).
# Sprawdza: liczenie (baza/%), klawisze (7 i r), kafelek na karcie ucznia, kolumnę w tabelach,
# CSV, eksport do VULCANa (surowy kod NS — mapę trzyma vulcan-frekwencja.user.js).
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8791
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
        FAILS.append(name)


# 4 uczniów, 4 lekcje. Ala: C,C,C,NS — 100% (NS jak ćwiczył).
# Dawid: C,C,NĆ,NS — 3/4 = 75%; gdyby NS wypadało z bazy, miałby 2/3 = 67%.
FIXTURE = """() => {
  const c = state.classes[0];
  c.name = '7b'; c.school = 'SSP';
  c.students = [{id:'u1', name:'Ala Zawodniczka'}, {id:'u2', name:'Bartek Zwykly'}, {id:'u3', name:'Celina Chora'}, {id:'u4', name:'Dawid Wyjezdza'}];
  c.attendance = {
    '2026-09-01': { u1:'C', u2:'C',  u3:'NU', u4:'C'  },
    '2026-09-02': { u1:'C', u2:'NB', u3:'C',  u4:'C'  },
    '2026-09-03': { u1:'C', u2:'C',  u3:'C',  u4:'NC' },
    '2026-09-04': { u1:'NS', u2:'C', u3:'ZW', u4:'NS' }
  };
  activateClass(c.id);          // state.students/attendance to ZYWE wskazniki — po podmianie obiektu trzeba je przepiac
  state.currentDate = '2026-09-04';
  save(); refreshAll();
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block",
        accept_downloads=True,
        viewport={"width": 1500, "height": 1000},
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('test-haslo-123')")
    page.wait_for_timeout(500)
    page.evaluate(FIXTURE)
    page.wait_for_timeout(400)

    # ---------- 1. Liczenie: NS liczy sie JAK CWICZYL ----------
    st = page.evaluate("() => getStudentStats('u1')")
    check("NS policzone osobno", st.get("NS") == 1, st)
    check(
        "NS WCHODZI do bazy (4 lekcje)",
        st.get("baza") == 4,
        {"baza": st.get("baza"), "total": st.get("total")},
    )
    check(
        "NS liczy sie jak cwiczyl (licznik 4 z 4)",
        st.get("cwiczyl") == 4 and st.get("percent") == 100,
        {"cwiczyl": st.get("cwiczyl"), "percent": st.get("percent")},
    )
    check(
        "STATUS_INFO: NS w bazie i jako cwiczyl",
        page.evaluate(
            "() => STATUS_INFO.NS.baza === true && STATUS_INFO.NS.cwiczyl === true"
        ),
    )
    # rdzen decyzji: NS rozciencza cene niecwiczenia. Dawid: C,C,NC,NS
    d = page.evaluate("() => getStudentStats('u4')")
    check(
        "NS rozciencza niecwiczenie: 3/4 = 75% (wg litery PZO byloby 2/3 = 67%)",
        d.get("baza") == 4 and d.get("cwiczyl") == 3 and d.get("percent") == 75,
        {
            "baza": d.get("baza"),
            "cwiczyl": d.get("cwiczyl"),
            "percent": d.get("percent"),
        },
    )

    # NS nie ma manipulatora w Regulach — to decyzja, nie ustawienie: zadna regula go nie wyrzuca z bazy
    page.evaluate(
        "() => { regulaUstaw('nuBaza', true); regulaUstaw('bsBaza', false); regulaUstaw('ncBaza', false); }"
    )
    page.wait_for_timeout(300)
    st2 = page.evaluate("() => getStudentStats('u1')")
    check(
        "zadna regula nie wyrzuca NS z bazy",
        st2.get("baza") == 4 and st2.get("percent") == 100,
        st2,
    )
    page.evaluate(
        "() => { regulaUstaw('nuBaza', false); regulaUstaw('bsBaza', true); regulaUstaw('ncBaza', true); }"
    )
    page.wait_for_timeout(300)

    # ---------- 2. Klawiatura: 7 oraz r nadaja NS ----------
    page.click("button.tab:has-text('Obecność')")
    page.wait_for_timeout(300)
    page.evaluate("() => { state.currentDate = '2026-09-03'; renderAttendance(); }")
    page.wait_for_timeout(200)
    page.click("h1")
    page.evaluate("() => setKbdRow('u2')")
    page.keyboard.press("7")
    page.wait_for_timeout(250)
    check(
        "klawisz 7 nadaje NS",
        page.evaluate("() => attRead(state.attendance['2026-09-03']['u2']).s") == "NS",
        page.evaluate("() => state.attendance['2026-09-03']['u2']"),
    )
    page.evaluate("() => setKbdRow('u3')")
    page.keyboard.press("r")
    page.wait_for_timeout(250)
    check(
        "klawisz r nadaje NS (bo n i s sa zajete)",
        page.evaluate("() => attRead(state.attendance['2026-09-03']['u3']).s") == "NS",
    )
    # sprzatanie po tescie klawiatury
    page.evaluate(
        "() => { state.attendance['2026-09-03'].u2 = 'C'; state.attendance['2026-09-03'].u3 = 'C'; state.currentDate = '2026-09-04'; save(); refreshAll(); }"
    )
    page.wait_for_timeout(300)

    # ---------- 3. Picker statusu ma przycisk NS ----------
    btn = page.query_selector("#pickerModal button.status-ns") or page.query_selector(
        "button.status-ns"
    )
    check("picker ma przycisk NS", btn is not None)
    if btn:
        check(
            "opis NS mowi, ze liczy sie jak cwiczyl",
            "jak ćwiczył" in (btn.get_attribute("title") or "").lower(),
            btn.get_attribute("title"),
        )

    # ---------- 4. Kolumna NS w tabelach ----------
    page.click("button.tab:has-text('Obecność')")
    page.wait_for_timeout(300)
    naglowki = page.evaluate(
        "() => Array.from(document.querySelectorAll('#tab-obecnosc thead th')).map(t => t.textContent.trim())"
    )
    check("tabela Obecnosci ma kolumne NS", "NS" in naglowki, naglowki)
    page.click("button.tab:has-text('Statystyki')")
    page.wait_for_timeout(400)
    nagl2 = page.evaluate(
        "() => Array.from(document.querySelectorAll('#statsBody').length ? document.querySelectorAll('#tab-statystyki thead th') : []).map(t => t.textContent.trim())"
    )
    check("tabela Statystyk ma kolumne NS", "NS" in nagl2, nagl2)
    wiersz = page.evaluate(
        """() => { const tr = Array.from(document.querySelectorAll('#statsBody tr')).find(r => /Ala/.test(r.textContent));
                   return tr ? Array.from(tr.cells).map(c => c.textContent.trim()) : null; }"""
    )
    check("wiersz Ali pokazuje 1 w kolumnie NS", wiersz and "1" in wiersz, wiersz)

    # ---------- 5. Karta ucznia: kafelek NS ----------
    page.click('button:has-text("Statystyki")')
    page.wait_for_timeout(300)
    page.click('button.stats-name-btn:has-text("Ala Zawodniczka")')
    page.wait_for_timeout(500)
    kafle = page.evaluate(
        "() => Array.from(document.querySelectorAll('#kartaBody .kafel')).map(k => k.textContent.replace(/\\s+/g,' ').trim())"
    )
    check(
        "karta ucznia ma kafelek NS",
        any("NS" in k for k in kafle),
        kafle,
    )
    check(
        "karta ucznia liczy NS do bazy i do licznika (100% z 4)",
        any(k.startswith("100%") and "z 4 liczonych" in k for k in kafle),
        kafle,
    )
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # ---------- 6. Eksport do VULCANa: surowy kod NS ----------
    txt = page.evaluate(
        """() => { const s = state.students.find(x => x.id === 'u1');
                   const day = state.attendance['2026-09-04'];
                   return s.name + '\\t' + attRead(day[s.id]).s; }"""
    )
    check("wiersz dla VULCANa niesie kod NS", txt.endswith("\tNS"), txt)
    mapa = (ROOT / "vulcan-frekwencja.user.js").read_text(encoding="utf-8")
    check(
        "skrypt VULCANa zna NS -> 'nieob. uspr. szkolne'",
        "'NS':'nieob. uspr. szkolne'" in mapa,
    )

    # ---------- 7. CSV ma kolumne NS ----------
    with page.expect_download(timeout=15000) as dl_info:
        page.evaluate("() => exportCSV()")
    csv_path = ROOT / "_zrzuty" / "ns_eksport.csv"
    csv_path.parent.mkdir(exist_ok=True)
    dl_info.value.save_as(str(csv_path))
    csv = csv_path.read_text(encoding="utf-8-sig")
    head = csv.splitlines()[0]
    check("CSV ma kolumne NS", ";NS;" in head or ",NS," in head, head)
    check(
        "CSV: liczba kolumn naglowka = liczba kolumn wiersza",
        len(csv.splitlines()[1].split(head[3] if False else ";"))
        == len(head.split(";")),
        (len(head.split(";")), len(csv.splitlines()[1].split(";"))),
    )

    check("brak bledow JS", not errors, errors[:3])
    browser.close()

httpd.shutdown()
print()
print("WYNIK: %s" % ("WSZYSTKO PASS" if not FAILS else ("%d FAIL" % len(FAILS))))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
