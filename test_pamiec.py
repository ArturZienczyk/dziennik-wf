# Bramka: dziennik ma dzialac, gdy pamiec przegladarki jest PELNA.
#
# Skad to sie wzielo: przy otwieraniu pliku z dysku (file://) Chrome daje wszystkim
# plikom HTML na komputerze JEDEN wspolny limit 10 MB. Inne projekty go zapelnily,
# a save() nie mial obslugi bledu - QuotaExceededError przerywal operacje w polowie.
# Objaw zgloszony przez uzytkownika: "nie moge dopisac klasy". Po cichu przepadaly
# tak samo wpisy frekwencji i oceny.
#
# Ten test odtwarza dokladnie ten stan (zapycha magazyn) i sprawdza, ze dziennik
# nadal dziala: klasa sie pojawia, uzytkownik dostaje komunikat, a dane przezywaja
# ponowne otwarcie (magazyn zapasowy = IndexedDB, wlasny limit).
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
PORT = 8768

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page()
    bledy = []
    page.on("pageerror", lambda e: bledy.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(500)

    # --- zapychamy wspolny magazyn, jak robia to inne pliki HTML z dysku ---
    page.evaluate(
        """() => {
        const kawal = 'x'.repeat(512 * 1024);
        try { for (let i = 0; i < 40; i++) localStorage.setItem('obcy_projekt_' + i, kawal); } catch (e) {}
        try { for (let i = 0; i < 4000; i++) localStorage.setItem('drobiazg_' + i, 'y'.repeat(1024)); } catch (e) {}
    }"""
    )
    pelny = page.evaluate(
        """() => { try { localStorage.setItem('probka', 'z'.repeat(1024)); localStorage.removeItem('probka');
                         return false; } catch (e) { return true; } }"""
    )
    check("magazyn faktycznie zapchany (inaczej test niczego nie sprawdza)", pelny)

    # --- dodanie klasy przy pelnym magazynie ---
    page.click('button:has-text("+ klasa")')
    page.wait_for_timeout(300)
    page.fill("#classPromptName", "7b")
    page.keyboard.press("Enter")
    page.wait_for_timeout(700)

    widoczne = page.evaluate(
        "() => { const s = document.querySelectorAll('#classBar select');"
        " const ost = s[s.length - 1]; return ost ? Array.from(ost.options).map(o => o.text) : []; }"
    )
    check("klasa pojawia sie w pasku mimo pelnej pamieci", "7b" in widoczne, widoczne)

    toast = page.evaluate(
        "() => { const t = document.getElementById('toast');"
        " return (t && t.style.display !== 'none') ? t.textContent : ''; }"
    )
    check(
        "uzytkownik dostaje potwierdzenie, nie cisze", "7b" in toast, toast or "(brak)"
    )

    baner = page.evaluate(
        "() => { const b = document.getElementById('magazynBaner');"
        " return b && b.style.display !== 'none' ? b.innerText.slice(0, 90) : ''; }"
    )
    check(
        "baner ostrzega o pelnej pamieci",
        "pe" in baner.lower(),
        baner or "(baner ukryty)",
    )

    # --- wpisy frekwencji tez musza przezyc ---
    page.click("h1")
    page.keyboard.press("n")
    page.wait_for_timeout(400)

    # --- najwazniejsze: dane przezywaja ponowne otwarcie ---
    page.reload()
    page.wait_for_timeout(1200)
    po = page.evaluate("() => state.classes.map(c => c.name)")
    check("klasa jest po ponownym otwarciu (magazyn zapasowy dziala)", "7b" in po, po)

    frekwencja = page.evaluate(
        "() => { const d = state.attendance[state.currentDate] || {};"
        " return Object.values(d).length; }"
    )
    check("wpis frekwencji tez przezyl ponowne otwarcie", frekwencja >= 1, frekwencja)

    # --- gdy miejsce wroci, dziennik wraca do zwyklego zapisu ---
    page.evaluate(
        """() => { Object.keys(localStorage).forEach(k => {
             if (k.indexOf('obcy_projekt_') === 0 || k.indexOf('drobiazg_') === 0) localStorage.removeItem(k); }); }"""
    )
    page.click("h1")
    page.keyboard.press("b")
    page.wait_for_timeout(500)
    wrocilo = page.evaluate(
        "() => { const s = localStorage.getItem('dziennik_wf_v1');"
        " return !!(s && JSON.parse(s).classes.length); }"
    )
    check("po zwolnieniu miejsca zapis wraca do localStorage", wrocilo)
    baner2 = page.evaluate(
        "() => { const b = document.getElementById('magazynBaner'); return b ? b.style.display : '?'; }"
    )
    check("baner znika, gdy problem minal", baner2 == "none", baner2)

    check("brak bledow JS", not bledy, bledy[:3])
    b.close()

httpd.shutdown()
print()
print("WYNIK: %s" % ("WSZYSTKO PASS" if not FAILS else ("%d FAIL" % len(FAILS))))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
