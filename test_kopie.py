# Test kopii zapasowych: kazdy plik, ktory ladunku z dziennika trafia na dysk,
# ma byc zaszyfrowany. Kluczowa asercja: w pliku NIE MA nazwiska dziecka.
import json
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8766
HASLO = "tajne-haslo-2026"
NAZWISKO = "Brzeczyszczykiewicz Grzegorz"

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


def przez_okno_kopii(page, tekst):
    """Od 22.09 (blok kopii): „Zrób kopię dziennika teraz" stoi w bloku, hasło i PIN pod „⚙" w bloku."""
    if tekst.startswith("Zrób kopię"):
        page.click('#kopiaBlok button:has-text("%s")' % tekst)
        page.wait_for_timeout(200)
        return
    page.click("#kopiaStan a")
    page.wait_for_timeout(200)
    # „Ustawienia kopii" sa zwiniete swiadomie (konfiguracja nie udaje czynnosci) — rozwijam jak user
    page.evaluate("() => { const d = document.querySelector('#kopiaModal details'); if (d) d.open = true; }")
    page.click('#kopiaModal button:has-text("%s")' % tekst)
    page.wait_for_timeout(200)


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
    page.evaluate(
        "() => zamekPierwszeHaslo('tajne-haslo-2026')"
    )  # zamek (Szczebel 5): pusty magazyn -> pierwsze haslo
    page.evaluate(
        "() => { state.students.length = 0; save(); renderStudents(); renderAttendance(); }"
    )

    # uczen z nazwiskiem, ktorego nie da sie pomylic z niczym innym w pliku
    page.click('button:has-text("Uczniowie")')
    page.click("#quickAddStudent")
    page.keyboard.type(NAZWISKO)
    page.keyboard.press("Enter")
    page.keyboard.type("Nowak Piotr")
    page.keyboard.press("Enter")

    check(
        "jawny przycisk 'Zapis JSON (backup)' zniknal z paska",
        page.query_selector('button:has-text("Zapis JSON")') is None,
    )

    # ---------- 1. Auto-kopia przy pierwszym zapisie lekcji NIE pyta o haslo ----------
    # (Szczebel 5: haslo dziennika = haslo kopii, apka zna je po odblokowaniu)
    page.click('button:has-text("Obecność")')
    page.wait_for_timeout(200)
    page.click("h1")
    page.keyboard.press("n")  # status dla 1. ucznia
    page.keyboard.press("Enter")  # zapisz lekcje
    page.wait_for_timeout(200)
    with page.expect_download(timeout=15000) as dl_info:
        page.keyboard.press("Enter")  # potwierdz -> auto-kopia
    page.wait_for_timeout(400)
    check(
        "auto-kopia nie pyta o haslo (haslo dziennika = haslo kopii)",
        page.query_selector("#pwdPromptModal.modal-bg.active") is None,
    )
    dl = dl_info.value
    auto_path = SHOTS / "auto_kopia.json"
    dl.save_as(str(auto_path))
    raw = auto_path.read_text(encoding="utf-8")

    check(
        "auto-kopia: plik ma nazwe wskazujaca szyfrowanie",
        "SZYFROWANA" in dl.suggested_filename,
        dl.suggested_filename,
    )
    check(
        "auto-kopia: NIE ZAWIERA nazwiska dziecka",
        NAZWISKO not in raw and "Brzeczy" not in raw,
    )
    obj = json.loads(raw)
    check(
        "auto-kopia: format zaszyfrowany (AES-GCM + PBKDF2)",
        obj.get("app") == "dziennik-wf-enc"
        and obj.get("cipher") == "AES-GCM-256"
        and len(obj.get("ct", "")) > 40,
        {k: obj.get(k) for k in ("app", "cipher", "kdf")},
    )

    # ---------- 1b. Auto-kopia takze przy ODBLOKOWANIU dziennika ----------
    # (2026-09-21: dzien bez zapisanej lekcji nie zostawial zadnej kopii, choc stan
    #  sie zmienial - import z telefonu, same oceny. Samo otwarcie dziennika ma wystarczyc.)
    page.evaluate("() => localStorage.removeItem('dziennik_wf_last_autobackup')")
    page.reload()
    page.wait_for_timeout(500)
    page.fill("#zamekInput", HASLO)
    with page.expect_download(timeout=15000) as dl_odb_info:
        page.click('#zamek button:has-text("Otw")')
    dl_odb = dl_odb_info.value
    page.evaluate("() => zamekUI_pinPomin()")   # apka proponuje PIN po odblokowaniu z ekranu
    check(
        "odblokowanie dziennika robi auto-kopie, gdy dzis jeszcze zadnej nie bylo",
        "AUTO-codzienna" in dl_odb.suggested_filename
        and "SZYFROWANA" in dl_odb.suggested_filename,
        dl_odb.suggested_filename,
    )
    odb_path = SHOTS / "auto_kopia_odblokowanie.enc.json"
    dl_odb.save_as(str(odb_path))
    check(
        "kopia z odblokowania: NIE ZAWIERA nazwiska dziecka",
        NAZWISKO not in odb_path.read_text(encoding="utf-8"),
    )

    # drugie odblokowanie tego samego dnia -> licznik dnia trzyma, kopii nie ma
    page.reload()
    page.wait_for_timeout(500)
    page.fill("#zamekInput", HASLO)
    druga = "BRAK"
    try:
        with page.expect_download(timeout=2500):
            page.click('#zamek button:has-text("Otw")')
        druga = "POWSTALA"
    except Exception:
        pass
    page.evaluate("() => zamekUI_pinPomin()")
    check(
        "drugie odblokowanie tego samego dnia NIE mnozy kopii",
        druga == "BRAK",
        druga,
    )
    page.wait_for_timeout(300)

    # ---------- 2. Kolejna kopia NIE pyta juz o haslo ----------
    page.click('button:has-text("Uczniowie")')
    page.wait_for_timeout(200)
    with page.expect_download(timeout=15000) as dl2_info:
        przez_okno_kopii(page, "Zrób kopię dziennika teraz")
    dl2 = dl2_info.value
    ręczna = SHOTS / "reczna_kopia.enc.json"
    dl2.save_as(str(ręczna))
    check(
        "reczna kopia nie pyta ponownie o haslo",
        page.query_selector("#pwdPromptModal.modal-bg.active") is None,
    )
    raw2 = ręczna.read_text(encoding="utf-8")
    check("reczna kopia: NIE ZAWIERA nazwiska dziecka", NAZWISKO not in raw2)

    # ---------- 3. Round-trip: kopie da sie odczytac haslem ----------
    back = page.evaluate(
        """async ([txt, pwd]) => {
            const d = await decryptBackup(txt, pwd);
            return d.classes[0].students.map(s => s.name);
        }""",
        [raw2, HASLO],
    )
    check(
        "kopie da sie odszyfrowac wlasnym haslem (dane wracaja w calosci)",
        NAZWISKO in back and "Nowak Piotr" in back,
        back,
    )

    zle = page.evaluate(
        """async ([txt]) => { try { await decryptBackup(txt, 'zle-haslo'); return 'ODCZYTANO'; }
                              catch (e) { return 'ODRZUCONO'; } }""",
        [raw2],
    )
    check("zle haslo nie otwiera kopii", zle == "ODRZUCONO", zle)

    # ---------- 4. Hasla NIE da sie podejrzec; da sie zmienic po podaniu starego ----------
    # (Szczebel 5: dawny przycisk „Hasło kopii" pokazywal haslo kazdemu przy odblokowanej apce)
    check(
        "przycisk 'Haslo kopii' (pokaz haslo) zniknal",
        page.query_selector('button:has-text("Hasło kopii")') is None,
    )
    przez_okno_kopii(page, "Zmień hasło dziennika")
    page.wait_for_timeout(300)
    check(
        "'Zmien haslo' nie podstawia biezacego hasla do pola",
        page.input_value("#pwdPromptInput") == "",
    )
    page.fill("#pwdPromptInput", "zle-stare-haslo")
    page.click("#pwdPromptOk")
    page.wait_for_timeout(300)
    check(
        "zle stare haslo: nic nie zmieniono",
        page.evaluate("() => zamek.haslo") == HASLO
        and page.query_selector("#pwdPromptModal.modal-bg.active") is None,
    )
    przez_okno_kopii(page, "Zmień hasło dziennika")
    page.wait_for_timeout(200)
    page.fill("#pwdPromptInput", HASLO)
    page.click("#pwdPromptOk")
    page.wait_for_timeout(200)
    page.fill("#pwdPromptInput", "nowe-haslo-777")
    page.click("#pwdPromptOk")
    page.wait_for_timeout(800)
    check(
        "po zmianie apka szyfruje nowym haslem",
        page.evaluate("() => zamek.haslo") == "nowe-haslo-777",
    )
    check(
        "magazyn przepisany nowym haslem (dane w calosci)",
        NAZWISKO
        in page.evaluate(
            "() => zamekStanZapisany().then(d => d.classes[0].students.map(s => s.name))"
        ),
    )
    with page.expect_download(timeout=15000) as dl3_info:
        przez_okno_kopii(page, "Zrób kopię dziennika teraz")
    dl3 = dl3_info.value
    raw3 = SHOTS / "kopia_po_zmianie.enc.json"
    dl3.save_as(str(raw3))
    zle_stare = page.evaluate(
        """async ([txt, pwd]) => { try { await decryptBackup(txt, pwd); return 'ODCZYTANO'; }
                                   catch (e) { return 'ODRZUCONO'; } }""",
        [raw3.read_text(encoding="utf-8"), HASLO],
    )
    check(
        "nowa kopia NIE otwiera sie starym haslem", zle_stare == "ODRZUCONO", zle_stare
    )

    # ---------- 5. Operacja niszczaca bez kopii NIE rusza danych ----------
    page.evaluate(
        "() => { zamek.haslo = ''; }"
    )  # zamek: bez hasla w pamieci kopia nie powstaje
    page.click('button:has-text("Wyczyść wszystko")')
    page.wait_for_timeout(200)
    page.keyboard.press("Enter")  # pierwszy confirm
    page.wait_for_timeout(200)
    page.keyboard.press("Enter")  # ostatnia szansa
    page.wait_for_timeout(600)
    toast = page.evaluate("() => document.getElementById('toast').textContent")
    check(
        "czyszczenie bez mozliwej kopii przerwane z komunikatem",
        "kopia" in toast.lower(),
        toast,
    )
    names = page.evaluate("() => state.students.map(s => s.name)")
    check(
        "anulowanie hasla przerywa czyszczenie — dane NIETKNIETE",
        NAZWISKO in names,
        names,
    )

    check("brak bledow JS", not errors, errors[:3])
    browser.close()

httpd.shutdown()
print()
print("WYNIK: %s" % ("WSZYSTKO PASS" if not FAILS else ("%d FAIL" % len(FAILS))))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
