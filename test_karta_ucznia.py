# Test karty ucznia: 30 lekcji z półroczem, oceny, pomiary; kafle-filtr; druk; brak błędów JS.
import functools
import http.server
import socketserver
import sys
import threading
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


SEED = """() => {
  state.students.length = 0;
  localStorage.setItem('dziennik_wf_backup_pwd', 'x-1');
  state.students.push({id:'u1', name:'Jan Kowalski', longTermReleased:false, height:'152', weight:'44'});
  state.students.push({id:'u2', name:'Piotr Nowak', longTermReleased:false});
  const seq = ['C','C','BS','C','C','NB','C','NC','C','C','NU','C','C','BS','C','ZW','C','C','C','NB','C','C','BS','C','C','C','NC','C','C','C'];
  const d = new Date('2026-09-02T00:00:00');
  seq.forEach((s, i) => {
    const iso = new Date(d.getTime() + i*3*86400000).toISOString().slice(0,10);
    state.attendance[iso] = { u1: (i === 4 || i === 7) ? attWrite(s, true) : s, u2: 'C' };
  });
  getCurrentClass().semesterBreak = '2026-10-20';
  state.gradeColumns.push({id:'g1', fullName:'Bieg 60 m', shortName:'60m', weight:1, date:'2026-09-20'});
  state.gradeColumns.push({id:'g2', fullName:'Aktywność', shortName:'Akt', weight:2, date:'2026-10-05'});
  state.grades.g1 = {u1: 70}; state.grades.g2 = {u1: 90};
  state.measurements.u1 = {jump:'165', shuttle:'11.2', beep:'6.5', plank:'48'};
  save(); renderStats();
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1200, "height": 900}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate(SEED)
    page.click('button:has-text("Statystyki")')
    page.click('button.stats-name-btn:has-text("Jan Kowalski")')
    page.wait_for_timeout(300)
    check(
        "modal otwarty",
        page.evaluate(
            "() => document.getElementById('kartaUcznia').classList.contains('active')"
        ),
    )
    kratki = page.locator("#kartaBody .kratka").count()
    check("oś czasu: 30 kratek", kratki == 30, kratki)
    sp = page.locator("#kartaBody .kratka .sp").count()
    check("oś czasu: 2 znaczniki spóźnienia", sp == 2, sp)
    okna = page.locator("#kartaBody .karta-okno-tytul").count()
    check("3 okna bilansu (I, II, rok)", okna == 3, okna)
    tytuly = page.locator("#kartaBody .karta-okno-tytul").all_text_contents()
    check(
        "I półrocze liczy lekcje < granicy",
        any("I półrocze" in x and "lekcji: 17" in x for x in tytuly),
        tytuly,
    )
    pct = page.locator("#kartaBody .karta-okna .kafel.static .n").all_text_contents()
    # rok: C=21, NC=2, BS=3, NB=2 -> baza 28 -> 75%
    check("% ćwiczył za rok = 75%", pct[-1] == "75%", pct)
    pts = page.locator("#kartaBody .karta-wykres .pkt").count()
    check("krzywa: 30 punktów", pts == 30, pts)
    check(
        "krzywa: linia półrocza",
        page.locator("#kartaBody .karta-wykres .brk").count() == 1,
    )
    rows = page.locator("#kartaBody table.lista").first.locator("tbody tr").count()
    check("lista: 30 wierszy", rows == 30, rows)
    check(
        "oceny: średnia ważona 83",
        "83" in page.locator("#kartaBody .dwie .karta-uwaga").first.text_content(),
    )
    check("pomiary: skok 165", "165" in page.locator("#kartaBody .dwie").text_content())
    page.screenshot(path=str(SHOTS / "karta_ucznia.png"), full_page=False)
    page.locator("#kartaBody").screenshot(path=str(SHOTS / "karta_ucznia_pelna.png"))

    # filtr: klik kafla BS (w oknie "Cały rok" - ostatnie)
    page.locator("#kartaBody .kafel:has-text('BS')").last.click()
    page.wait_for_timeout(200)
    dim = page.locator("#kartaBody .kratka.dim").count()
    check("filtr BS: 27 kratek przyciemnionych", dim == 27, dim)
    check(
        "filtr BS: kafel podświetlony",
        page.locator("#kartaBody .kafel.on").count() >= 1,
    )
    check(
        "filtr: opis widoczny",
        "Filtr" in page.locator("#kartaBody .karta-filtr").text_content(),
    )
    page.locator("#kartaBody").screenshot(path=str(SHOTS / "karta_ucznia_filtr_bs.png"))
    page.locator("#kartaBody .kafel:has-text('BS')").last.click()
    page.wait_for_timeout(200)
    check("filtr zdjęty", page.locator("#kartaBody .kratka.dim").count() == 0)

    # druk: emulacja media print
    page.evaluate("() => document.body.classList.add('karta-print')")
    page.emulate_media(media="print")
    page.wait_for_timeout(200)
    vis = page.evaluate(
        "() => getComputedStyle(document.querySelector('.container')).display"
    )
    check("druk: reszta strony ukryta", vis == "none", vis)
    page.pdf(path=str(SHOTS / "karta_ucznia.pdf"), format="A4", print_background=True)
    page.emulate_media(media="screen")
    page.evaluate("() => document.body.classList.remove('karta-print')")

    # zamknięcie
    page.click('#kartaBody button:has-text("Zamknij")')
    check(
        "modal zamknięty",
        not page.evaluate(
            "() => document.getElementById('kartaUcznia').classList.contains('active')"
        ),
    )

    # uczeń bez lekcji: brak crasha
    page.evaluate(
        "() => { state.students.push({id:'u9', name:'Nowy Bez', longTermReleased:false}); openKarta('u9'); }"
    )
    check(
        "uczeń bez lekcji: komunikat",
        "Brak zapisanych lekcji" in page.locator("#kartaBody").text_content(),
    )
    check("brak błędów JS", errors == [], errors)
    browser.close()
httpd.shutdown()
print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
