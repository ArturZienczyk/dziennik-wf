# Test "Kopie w folderze" (2026-09-21): kopie lezace w folderze kopii jako lista z datami.
# Powod: kopie z telefonu Artur przynosi mailem, a po pobraniu zalacznika plik ginie w Pobranych.
# Okna systemowego (showDirectoryPicker) nie da sie kliknac w headless, wiec uchwyt folderu jest
# podstawiony atrapa — testowana jest CALA reszta drogi: odczyt katalogu, sortowanie, render listy,
# haslo, scalenie danych.
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8793
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright

HASLO = "haslo-kopii-1"
FAILS = []


def zamknij_modale(page):
    """Raport po scaleniu zostaje na ekranie i przykrywa zakladki — w tescie domykam go wprost."""
    page.evaluate(
        "() => document.querySelectorAll('.modal-bg.active').forEach(m => m.classList.remove('active'))"
    )
    page.wait_for_timeout(120)


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


# Stan A (w apce): 7b z jednym wpisem. Kopia "z telefonu" niesie drugi wpis, ktorego apka nie ma.
FIX_A = """() => {
  const c = state.classes[0];
  c.name = '7b'; c.school = 'SSP';
  c.students = [{id:'u1', name:'Ala Test'}, {id:'u2', name:'Bartek Test'}];
  c.attendance = { '2026-09-21': { u1:'C' } };
  activateClass(c.id);
  state.currentDate = '2026-09-21';
  save(); refreshAll();
}"""

# Stan B: to samo + wpis zrobiony "na telefonie" — z niego robimy zaszyfrowana kopie.
FIX_B = """() => {
  state.attendance['2026-09-21'].u2 = 'NS';
  save();
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1500, "height": 1000}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate("(h) => zamekPierwszeHaslo(h)", HASLO)
    page.wait_for_timeout(500)
    page.evaluate(FIX_A)
    page.wait_for_timeout(300)

    # kopia "z telefonu": stan B zaszyfrowany tym samym haslem
    page.evaluate(FIX_B)
    kopia = page.evaluate("async (h) => await encryptSnapshot(h)", HASLO)
    # szyfrogram, nie jawny JSON: kopert a AES-GCM i zadnego klucza danych w tresci
    check(
        "kopia powstala i jest szyfrogramem",
        bool(kopia) and "AES-GCM" in kopia and "attendance" not in kopia,
        kopia[:80] if kopia else kopia,
    )

    # Wracamy do stanu A. Na prawdziwym laptopie wpisu u2 nigdy nie bylo; tutaj powstal i zniknal,
    # a to zostawia NAGROBEK (skasowany wpis nie wraca ze starej kopii — regula scalania z 18.09).
    # Kasuje wiec slad po u2, zeby fixture odwzorowywal laptop, ktory tego wpisu nie widzial.
    page.evaluate(FIX_A)
    page.evaluate(
        "() => { const c = state.classes[0];"
        " if (c._t) Object.keys(c._t).forEach(k => { if (k.indexOf('|u2') >= 0) delete c._t[k]; });"
        " save(); }"
    )
    page.wait_for_timeout(200)
    check(
        "przed scaleniem u2 nie ma statusu",
        page.evaluate("() => attRead((state.attendance['2026-09-21']||{}).u2).s")
        is None,
    )

    # atrapa uchwytu folderu: dwa pliki .json + jeden obcy, rozne daty modyfikacji
    page.evaluate(
        """([kopia]) => {
          const plik = (name, mtime, tresc) => ({
            kind: 'file', name,
            getFile: async () => ({ lastModified: mtime, size: tresc.length, text: async () => tresc })
          });
          _folderKopii = {
            name: 'FolderTest',
            queryPermission: async () => 'granted',
            requestPermission: async () => 'granted',
            values: async function* () {
              yield plik('dziennik-wf_STARA_2026-09-01_08-00.json', Date.parse('2026-09-01T08:00:00'), '{}');
              yield plik('dziennik-wf_TELEFON_2026-09-21_19-30.json', Date.parse('2026-09-21T19:30:00'), kopia);
              yield plik('notatka.txt', Date.parse('2026-09-21T20:00:00'), 'nie kopia');
            }
          };
        }""",
        [kopia],
    )

    zamknij_modale(page)
    page.click("text=👥 Uczniowie")
    page.click("text=📂 Kopie w folderze")
    page.wait_for_timeout(400)
    check(
        "modal otwarty",
        page.eval_on_selector(
            "#kopieFolderModal", "e => e.classList.contains('active')"
        ),
    )
    nazwy = page.eval_on_selector_all(
        "#kopieFolderLista button", "bs => bs.map(b => b.children[0].textContent)"
    )
    check("lista pomija pliki spoza .json", "notatka.txt" not in nazwy, nazwy)
    check("dwie kopie na liscie", len(nazwy) == 2, nazwy)
    check("najnowsza na gorze", nazwy and "TELEFON" in nazwy[0], nazwy)
    daty = page.eval_on_selector_all(
        "#kopieFolderLista button", "bs => bs.map(b => b.children[1].textContent)"
    )
    check("kazdy wiersz ma date i rozmiar", all("kB" in d for d in daty), daty)
    # kopia z telefonu ma taki sam wzorzec nazwy co wlasna reczna — rejestr wlasnych nazw je rozroznia
    check(
        "kopia przyniesiona z zewnatrz nie jest oznaczona jako wlasna",
        all("zapisana tutaj" not in d for d in daty),
        daty,
    )
    page.evaluate(
        "() => zapamietajWlasnaKopie('dziennik-wf_STARA_2026-09-01_08-00.json')"
    )
    page.click(
        "#kopieFolderLista button >> nth=1"
    )  # zamyka modal (wczytanie starej atrapy)
    page.wait_for_timeout(200)
    page.click("#pwdPromptCancel") if page.query_selector("#pwdPromptCancel") else None
    zamknij_modale(page)
    page.click("text=📂 Kopie w folderze")
    page.wait_for_timeout(400)
    daty2 = page.eval_on_selector_all(
        "#kopieFolderLista button", "bs => bs.map(b => b.children[1].textContent)"
    )
    check(
        "wlasna kopia oznaczona „zapisana tutaj”",
        len(daty2) == 2
        and "zapisana tutaj" in daty2[1]
        and "zapisana tutaj" not in daty2[0],
        daty2,
    )
    zamknij_modale(page)
    page.click("text=📂 Kopie w folderze")
    page.wait_for_timeout(400)

    # klik w kopie z telefonu -> haslo -> potwierdzenie -> scalenie
    page.click("#kopieFolderLista button >> nth=0")
    page.wait_for_timeout(300)
    check(
        "pyta o haslo tej kopii",
        page.eval_on_selector("#pwdPromptModal", "e => e.classList.contains('active')"),
    )
    check(
        "w pytaniu o haslo widac nazwe pliku",
        "TELEFON" in (page.text_content("#pwdPromptHint") or ""),
        page.text_content("#pwdPromptHint"),
    )
    page.fill("#pwdPromptInput", HASLO)
    page.click("#pwdPromptOk")
    page.wait_for_timeout(500)
    check(
        "po hasle pyta o wczytanie",
        page.eval_on_selector("#confirmModal", "e => e.classList.contains('active')"),
    )
    page.click("#confirmModal button >> nth=1")
    page.wait_for_timeout(900)
    check(
        "wpis z telefonu doszedl przez scalenie",
        page.evaluate("() => attRead((state.attendance['2026-09-21']||{}).u2).s")
        == "NS",
        page.evaluate("() => JSON.parse(JSON.stringify(state.attendance))"),
    )
    check(
        "wlasny wpis przetrwal",
        page.evaluate("() => attRead((state.attendance['2026-09-21']||{}).u1).s")
        == "C",
    )

    # zle haslo nie rusza danych
    page.evaluate(
        "() => { state.attendance['2026-09-21'] = {u1:'C'}; save(); renderAttendance(); }"
    )
    zamknij_modale(page)
    page.click("text=👥 Uczniowie")
    page.click("text=📂 Kopie w folderze")
    page.wait_for_timeout(400)
    page.click("#kopieFolderLista button >> nth=0")
    page.wait_for_timeout(300)
    page.fill("#pwdPromptInput", "zle-haslo")
    page.click("#pwdPromptOk")
    page.wait_for_timeout(600)
    check(
        "zle haslo: dane nietkniete",
        page.evaluate("() => attRead((state.attendance['2026-09-21']||{}).u2).s")
        is None,
    )

    # bez wskazanego folderu: komunikat, nie cisza i nie wyjatek
    page.evaluate("() => { _folderKopii = null; }")
    zamknij_modale(page)
    page.click("text=👥 Uczniowie")
    page.click("text=📂 Kopie w folderze")
    page.wait_for_timeout(400)
    check(
        "bez folderu mowi co zrobic",
        "wskaż folder" in (page.text_content("#toast") or ""),
        page.text_content("#toast"),
    )

    check("brak bledow JS", errors == [], errors)
    browser.close()
httpd.shutdown()
print("\nWYNIK:", "WSZYSTKO PASS" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
