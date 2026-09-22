# Test „Folder kopii": kopia idzie do wskazanego folderu (mock showDirectoryPicker + uchwytu), a gdy
# folderu nie ma / brak zgody — wraca do zwykłego pobierania. Prawdziwy picker weryfikuje user w Chrome.
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8774

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


# Atrapa uchwytu folderu: zapisy lądują w window.__folder, zgoda sterowana window.__perm
MOCK = """() => {
  window.__folder = {}; window.__perm = 'granted'; window.__downloads = [];
  const mk = () => ({
    name: 'Kopie WF',
    queryPermission: async () => window.__perm,
    requestPermission: async () => window.__perm,
    getFileHandle: async (name) => ({ createWritable: async () => ({ write: async (t) => { window.__folder[name] = t; }, close: async () => {} }) })
  });
  window.showDirectoryPicker = async () => mk();
  // podsłuch zwykłego pobierania
  const origClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () { if (this.download) window.__downloads.push(this.download); else origClick.call(this); };
}"""

SEED = """() => {
  state.students.length = 0;
  state.students.push({id:'u1', name:'Jan Kowalski', longTermReleased:false});
  save();
}"""

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block", viewport={"width": 1200, "height": 800}
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.add_init_script("(" + MOCK + ")()")
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(500)
    page.evaluate("() => zamekPierwszeHaslo('haslo-x1')")  # zamek (Szczebel 5): pusty magazyn -> pierwsze haslo
    page.evaluate(SEED)
    page.click('button.tab:has-text("Uczniowie")')
    page.wait_for_timeout(200)
    # Od 22.09 foldery kopii mieszkaja w oknie „Kopia zapasowa" -> „Ustawienia kopii".
    # Otwieram je raz i zostawiam otwarte: klikanie folderu okna nie zamyka.
    page.click('#tab-uczniowie button:has-text("Kopia zapasowa")')
    page.wait_for_timeout(200)
    page.evaluate("() => { document.querySelector('#kopiaModal details').open = true; }")

    check(
        "start: przycisk mówi Pobrane",
        page.text_content("#btnFolderKopii").strip() == "📁 Folder kopii: Pobrane",
    )

    # kopia bez folderu -> pobieranie
    page.evaluate("() => exportEncrypted()")
    page.wait_for_timeout(1500)
    dl = page.evaluate("() => window.__downloads")
    check(
        "bez folderu: kopia pobrana zwykłą drogą",
        len(dl) == 1 and "_SZYFROWANA_" in dl[0],
        dl,
    )
    check(
        "bez folderu: nic w folderze",
        page.evaluate("() => Object.keys(window.__folder).length") == 0,
    )

    # wskaż folder (mock) -> przycisk pokazuje nazwę
    page.click("#btnFolderKopii")
    page.wait_for_timeout(300)
    check(
        "po wyborze: przycisk pokazuje nazwę folderu",
        page.text_content("#btnFolderKopii").strip() == "📁 Folder kopii: Kopie WF",
    )

    # kopia z folderem -> do folderu, nie do pobierania
    page.evaluate("() => exportEncrypted()")
    page.wait_for_timeout(1500)
    keys = page.evaluate("() => Object.keys(window.__folder)")
    check(
        "z folderem: plik w folderze",
        len(keys) == 1 and keys[0].endswith(".enc.json"),
        keys,
    )
    check(
        "z folderem: bez zwykłego pobierania",
        page.evaluate("() => window.__downloads.length") == 1,
    )
    check(
        "plik w folderze to szyfrowana kopia (bez nazwiska)",
        page.evaluate(
            "() => { const t = Object.values(window.__folder)[0]; return t.length > 100 && t.indexOf('Kowalski') < 0; }"
        ),
    )
    toast = page.text_content("#toast")
    check("dymek mówi, gdzie poszła kopia", "Kopie WF" in toast, toast)

    # brak zgody -> fallback do pobierania + dymek ostrzegawczy
    page.evaluate("() => { window.__perm = 'denied'; }")
    page.evaluate("() => exportEncrypted()")
    page.wait_for_timeout(1500)
    check(
        "brak zgody: kopia pobrana zwykłą drogą",
        page.evaluate("() => window.__downloads.length") == 2,
    )
    check(
        "brak zgody: folder bez nowego pliku",
        page.evaluate("() => Object.keys(window.__folder).length") == 1,
    )
    check(
        "brak zgody: dymek o Pobranych",
        "Pobranych" in page.text_content("#toast"),
        page.text_content("#toast"),
    )

    # Shift+klik = powrót do Pobranych
    page.click("#btnFolderKopii", modifiers=["Shift"])
    page.wait_for_timeout(300)
    check(
        "Shift+klik: wraca Pobrane",
        page.text_content("#btnFolderKopii").strip() == "📁 Folder kopii: Pobrane",
    )

    # auto-kopia dzienna też idzie tą samą drogą (folder ustawiony ponownie)
    page.evaluate("() => { window.__perm = 'granted'; }")
    page.click("#btnFolderKopii")
    page.wait_for_timeout(300)
    page.evaluate(
        "() => { localStorage.removeItem('dziennik_wf_last_autobackup'); autoBackupDaily(); }"
    )
    page.wait_for_timeout(1500)
    keys = page.evaluate("() => Object.keys(window.__folder)")
    check(
        "auto-kopia dzienna w folderze", any("AUTO-codzienna" in k for k in keys), keys
    )

    check("brak błędów JS", errors == [], errors)
    browser.close()
httpd.shutdown()
print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
