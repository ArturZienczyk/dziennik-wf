# Zwolniony długoterminowo a Systematyczność (user 19.09, 8c: „ćwiczyła 3 tygodnie, od niedawna zwolnienie lekarskie,
# ma kreskę”). Ptaszek wyłącza lekcje od zwolnienia, nie kasuje odbytych: Syst. z zapisów, % dotąd w tabeli dnia,
# wiersz w Ocenach i Statystykach (wyszarzony), a dni po zwolnieniu bez wpisu nie obniżają procentu.
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8787
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


FIXTURE = """() => {
  const st = (n, pref) => Array.from({length: n}, (_, i) => ({ id: pref + (i + 1), name: 'Uczennica ' + 'ABCDEF'[i], longTermReleased: false, height: '', weight: '' }));
  const c = state.classes[0]; c.school = 'ZSS'; c.name = '8c'; c.students = st(4, 'u'); c.plec = 'dz';
  activateClass(c.id);
  // 3 tygodnie ćwiczenia, potem zwolnienie lekarskie (u2): lekcje po zwolnieniu bez wpisu dla u2
  c.attendance['2026-09-01'] = { u1: 'C', u2: 'C', u3: 'C', u4: 'BS' };
  c.attendance['2026-09-08'] = { u1: 'C', u2: 'C', u3: 'NC', u4: 'C' };
  c.attendance['2026-09-15'] = { u1: 'C', u2: 'BS', u3: 'C', u4: 'C' };
  c.attendance['2026-09-22'] = { u1: 'C', u3: 'C', u4: 'C' };
  c.students[1].longTermReleased = true;
  state.currentDate = '2026-09-22';
  save(); refreshAll();
}"""

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
    page.evaluate(FIXTURE)
    page.wait_for_timeout(300)

    # dane: u2 = 2 ćwiczył z 3 w bazie → 67%
    st = page.evaluate("() => getStudentStats('u2')")
    check(
        "stats u2: baza 3, ćwiczył 2 (dzień po zwolnieniu bez wpisu nie liczy się)",
        st["baza"] == 3 and st["cwiczyl"] == 2,
        st,
    )

    # Syst. (kolumna auto) ma wartość dla u2
    sys_val = page.evaluate(
        "() => { const col = state.gradeColumns.find(c => c.auto); return col ? (state.grades[col.id] || {}).u2 : 'brak kolumny'; }"
    )
    check("Syst.: zwolniona ma procent z odbytych lekcji (67)", sys_val == 67, sys_val)

    # Oceny: wiersz zwolnionej widoczny, wyszarzony, z wartością
    page.click("button.tab:has-text('Oceny')")
    page.wait_for_timeout(300)
    row = page.locator("#ocenyBody tr.long-term-released")
    check("Oceny: wiersz zwolnionej jest (wyszarzony)", row.count() == 1, row.count())
    check(
        "Oceny: komórka Syst. zwolnionej = 67, nie „—”",
        row.count() == 1 and "67" in row.locator("td.cell-ocena").first.inner_text(),
    )
    check(
        "Oceny: pozostałe 3 uczennice bez zmian",
        page.locator("#ocenyBody tr").count() == 4,
    )

    page.locator("#tab-oceny table").screenshot(
        path=str(ROOT / "_zrzuty" / "zwolniona_oceny_1400.png")
    )

    # Statystyki: wiersz jest, z procentem
    page.click("button.tab:has-text('Statystyki')")
    page.wait_for_timeout(300)
    srow = page.locator("#statsBody tr.long-term-released")
    check("Statystyki: wiersz zwolnionej jest", srow.count() == 1, srow.count())
    check(
        "Statystyki: % zwolnionej = 67%",
        srow.count() == 1 and "67%" in srow.inner_text(),
        srow.inner_text() if srow.count() else "",
    )

    # Obecność (tabela dnia): % dotąd zwolnionej = 67%, nie „—”
    page.click("button.tab:has-text('Obecność')")
    page.wait_for_timeout(300)
    arow = page.locator("table.attendance tbody tr.long-term-released").first
    check(
        "Obecność: % dotąd zwolnionej = 67%",
        "67%" in arow.inner_text(),
        arow.inner_text()[:120],
    )

    # uczeń zwolniony od początku (zero zapisów): nadal „—”, bez NaN
    page.evaluate(
        "() => { state.classes[0].students.push({ id: 'u5', name: 'Uczennica E', longTermReleased: true, height: '', weight: '' }); save(); refreshAll(); }"
    )
    page.wait_for_timeout(300)
    check(
        "zwolniona bez zapisów: % dotąd „—”",
        "—"
        in page.locator("table.attendance tbody tr.long-term-released")
        .nth(1)
        .inner_text(),
    )
    page.click("button.tab:has-text('Oceny')")
    page.wait_for_timeout(200)
    check(
        "zwolniona bez zapisów: Syst. pusta, bez NaN",
        "NaN" not in page.text_content("#ocenyBody"),
    )

    check("bez błędów JS", not errors, str(errors[:3]))
    browser.close()

httpd.shutdown()
print("\nFAIL: %d" % len(FAILS))
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
