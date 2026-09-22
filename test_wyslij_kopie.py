# -*- coding: utf-8 -*-
# Bramka dla przycisku „Wyslij kopie" (handoff „jedna droga kopii", punkt 1).
# Pilnuje dwoch rzeczy, ktore lamia sie po cichu:
#   1. to, co wychodzi z apki do systemowego okna udostepniania, JEST ZASZYFROWANE
#      (wysylka mailem jest bezpieczna wylacznie dlatego),
#   2. przegladarka bez navigator.share nie zostawia userowi milczacego przycisku —
#      kopia i tak powstaje zwykla droga.
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
PORT = 8799
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


STUB = """
() => {
  window.__udostepnione = null;
  navigator.canShare = (d) => !!(d && d.files && d.files.length);
  navigator.share = async (d) => {
    const f = d.files[0];
    window.__udostepnione = { name: f.name, type: f.type, text: await f.text(), title: d.title };
  };
}
"""

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
    page.evaluate("() => zamekPierwszeHaslo('%s')" % HASLO)
    page.evaluate(
        "() => { state.students.length = 0; save(); renderStudents(); renderAttendance(); }"
    )

    page.click('button:has-text("Uczniowie")')
    page.click("#quickAddStudent")
    page.keyboard.type(NAZWISKO)
    page.keyboard.press("Enter")
    page.wait_for_timeout(200)

    check(
        "przycisk Wyslij kopie dziennika jest w bloku kopii",
        page.query_selector('#kopiaBlok button:has-text("Wyślij kopię dziennika")')
        is not None,
    )

    # ---------- 0. ZAPADKA „blok kopii w dwoch krokach" (22.09, decyzja Artura) ----------
    # Inwariant, nie gust. Historia: 12 przyciskow w pasku (8 wokol kopii) -> dwa („Wyślij kopię" /
    # „Kopia zapasowa") -> Artur: „nie wiadomo, jaką kopię, czego i gdzie". Teraz: krok 1 = kopia
    # dziennika (najnowsza widoczna), krok 2 = ta kopia jedzie na drugie urzadzenie / przychodzi z niego.
    # Kazda czynnosc mowi o TEJ SAMEJ rzeczy („kopię dziennika") — inaczej wracamy do enigmy.
    pasek = page.eval_on_selector_all(
        "#tab-uczniowie .toolbar button",
        "bs => bs.filter(b => b.offsetParent !== null).map(b => b.textContent.trim())",
    )
    check("pasek Uczniowie ma najwyzej 5 przyciskow", len(pasek) <= 5, pasek)
    check(
        "kopie nie wracaja do paska — mieszkaja w bloku",
        not [t for t in pasek if "kopi" in t.lower()],
        pasek,
    )
    blok = page.eval_on_selector_all(
        "#kopiaBlok button", "bs => bs.map(b => b.textContent.trim())"
    )
    check("blok kopii ma dokladnie trzy czynnosci", len(blok) == 3, blok)
    check(
        "kazda czynnosc mowi o tej samej rzeczy: „kopię dziennika”",
        all("kopię dziennika" in t for t in blok),
        blok,
    )
    check(
        "czynnosci zaczynaja sie od tego, co sie stanie (Zrób / Wyślij / Wczytaj)",
        all(any(w in t for w in ("Zrób", "Wyślij", "Wczytaj")) for t in blok),
        blok,
    )
    check(
        "krok 1 widac: linia „Najnowsza:”",
        "Najnowsza:" in page.inner_text("#kopiaBlok"),
    )
    zargon = [
        t
        for t in pasek + blok
        if "JSON" in t or "szyfrowan" in t.lower() or "Kopia 2" in t
    ]
    check(
        "w pasku i bloku nie ma slowa z innego swiata (JSON / szyfrowana / Kopia 2)",
        not zargon,
        zargon,
    )

    page.click("#kopiaStan a")
    page.wait_for_timeout(300)
    check(
        "⚙ otwiera same ustawienia: lista zwinieta, Chrome o nic nie pyta",
        page.eval_on_selector("#kopiaListaBox", "e => e.style.display === 'none'"),
    )
    check(
        "⚙ otwiera ustawienia rozwiniete",
        page.eval_on_selector("#kopiaModal details", "e => e.open"),
    )
    check(
        "okno nie powtarza czynnosci z bloku (szum)",
        page.query_selector("#kopiaCzynnosci") is None,
    )
    page.click('#kopiaModal button:has-text("Zamknij")')
    page.wait_for_timeout(200)

    # ---------- 0b. PARSER opisu kopii: typowy / brzegowy / wrogi ----------
    # Wiersz listy kopii przestal byc surowa nazwa pliku (panel krytykow 22.09). Nowy parser
    # dostaje trzy klasy wejscia PRZED pierwszym uzyciem: nazwa z apki, nazwa obca/pusta,
    # nazwa wroga (cudzyslowy, backslash, znacznik HTML, dlugosc).
    typowe = page.evaluate("""() => [
        rodzajKopii('dziennik-wf_AUTO-codzienna_SZYFROWANA_2026-09-22_07-12.enc.json'),
        rodzajKopii('dziennik-wf_WYSLANA_SZYFROWANA_2026-09-21_19-30.enc.json'),
        rodzajKopii('dziennik-wf_RECZNA_SZYFROWANA_2026-09-21_08-00.enc.json'),
        rodzajKopii('dziennik-wf_PRZED-IMPORT-ENC_SZYFROWANA_2026-09-20_10-00.enc.json')
    ]""")
    check(
        "parser (typowy): kazdy rodzaj kopii z apki ma nazwe po ludzku",
        typowe
        == [
            "Kopia automatyczna",
            "Kopia wysłana stąd",
            "Kopia zapisana ręcznie",
            "Kopia sprzed ryzykownej zmiany",
        ],
        typowe,
    )

    brzegowe = page.evaluate("""() => [
        rodzajKopii(''), rodzajKopii(null), rodzajKopii(undefined),
        rodzajKopii('cokolwiek.json'), rodzajKopii('x'.repeat(5000))
    ]""")
    check(
        "parser (brzegowy): pusta / nieznana / bardzo dluga nazwa nie wywraca sie, daje 'Kopia'",
        brzegowe == ["Kopia"] * 5,
        brzegowe,
    )

    wrogie = page.evaluate("""() => {
        const bs = String.fromCharCode(92), tab = String.fromCharCode(9), nl = String.fromCharCode(10);
        const zle = ['plik \u201eAUTO-codzienna\u201d .json', 'a' + bs + 'b_WYSLANA_c.json',
                     '<script>alert(1)</script>_RECZNA_.json',
                     'kopia' + tab + 'z' + nl + 'bialymi_AUTO-codzienna_.json'];
        return zle.map(n => rodzajKopii(n));
    }""")
    check(
        "parser (wrogi): cudzyslowy, backslash, znacznik HTML i biale znaki nie wysadzaja parsera",
        all(isinstance(x, str) and x for x in wrogie),
        wrogie,
    )

    wstrzykniecie = page.evaluate("""() => {
        const d = document.createElement('div');
        d.textContent = rodzajKopii('<img src=x onerror=alert(1)>_AUTO-codzienna_.json');
        return d.innerHTML.indexOf('<img') === -1;
    }""")
    check(
        "parser (wrogi): nazwa pliku nie moze wstrzyknac HTML w wiersz listy",
        wstrzykniecie,
    )

    czasy = page.evaluate("""() => {
        const teraz = Date.now();
        return [kiedyKopii(teraz), kiedyKopii(teraz - 86400000 * 1),
                kiedyKopii(Date.parse('2026-01-02T08:30:00')), kiedyKopii(NaN)];
    }""")
    check(
        "czas kopii: dzis / wczoraj / data / smiec sa rozroznione i zadne nie jest puste",
        czasy[0].startswith("dziś")
        and czasy[1].startswith("wczoraj")
        and "2026" in czasy[2]
        and czasy[3] == "data nieznana",
        czasy,
    )

    skad = page.evaluate("() => [skadKopia(true), skadKopia(false)]")
    check(
        "pochodzenie opisane przy KAZDEJ kopii, nie tylko przy wlasnej (K4 22.09)",
        "tutaj" in skad[0] and "nie zapisywana tutaj" in skad[1],
        skad,
    )

    # ---------- 1. Droga glowna: navigator.share dostaje ZASZYFROWANY plik ----------
    page.evaluate(STUB)
    page.click('#tab-uczniowie button:has-text("Wyślij kopię")')
    page.wait_for_timeout(1500)
    wys = page.evaluate("() => window.__udostepnione")
    check("wysylka oddaje plik do systemowego okna udostepniania", wys is not None)
    if wys:
        check(
            "nazwa wyslanego pliku mowi, ze jest szyfrowany",
            "SZYFROWANA" in wys["name"] and wys["name"].endswith(".enc.txt"),
            wys["name"],
        )
        # Chrome nie udostepnia .json (canShare=true, share() -> NotAllowedError w 1 ms;
        # przycisk milczal, 22.09). Stub tego nie odtworzy — pilnujemy koncowki i typu.
        check(
            "wysylany plik to .txt / text/plain (Chrome odrzuca .json)",
            wys["type"] == "text/plain",
            wys["type"],
        )
        check(
            "wyslany plik NIE ZAWIERA nazwiska dziecka",
            NAZWISKO not in wys["text"] and "Brzeczy" not in wys["text"],
        )
        obj = json.loads(wys["text"])
        check(
            "wyslany plik ma format AES-GCM + PBKDF2",
            obj.get("app") == "dziennik-wf-enc"
            and obj.get("cipher") == "AES-GCM-256"
            and len(obj.get("ct", "")) > 40,
            {k: obj.get(k) for k in ("app", "cipher", "kdf")},
        )
        wrocilo = page.evaluate(
            """async ([txt, pwd]) => {
                 const d = await decryptBackup(txt, pwd);
                 return d.classes[0].students.map(s => s.name);
               }""",
            [wys["text"], HASLO],
        )
        check(
            "wyslana kopia da sie odszyfrowac haslem dziennika (dane sa w srodku)",
            NAZWISKO in wrocilo,
            wrocilo,
        )

    check(
        "wysylka nie pyta o haslo drugi raz",
        page.query_selector("#pwdPromptModal.modal-bg.active") is None,
    )

    # ---------- 2. Anulowanie okna udostepniania to nie blad ----------
    page.evaluate("""() => {
        navigator.share = async () => { const e = new Error('cancel'); e.name = 'AbortError'; throw e; };
    }""")
    anulowane = "BRAK"
    try:
        with page.expect_download(timeout=2500):
            page.click('#tab-uczniowie button:has-text("Wyślij kopię")')
        anulowane = "POWSTAL PLIK"
    except Exception:
        pass
    check(
        "zamkniecie okna udostepniania nie zapisuje kopii awaryjnie",
        anulowane == "BRAK",
        anulowane,
    )

    # ---------- 3. Fallback: przegladarka bez share zapisuje kopie jak dotad ----------
    page.evaluate("() => { delete navigator.canShare; delete navigator.share; }")
    with page.expect_download(timeout=15000) as dl_info:
        page.click('#tab-uczniowie button:has-text("Wyślij kopię")')
    dl = dl_info.value
    check(
        "bez navigator.share kopia i tak powstaje (przycisk nie milczy)",
        "SZYFROWANA" in dl.suggested_filename,
        dl.suggested_filename,
    )
    fb = SHOTS / "wyslij_fallback.enc.json"
    dl.save_as(str(fb))
    check(
        "kopia z fallbacku tez NIE ZAWIERA nazwiska dziecka",
        NAZWISKO not in fb.read_text(encoding="utf-8"),
    )

    check("brak bledow JS w konsoli", not errors, errors[:3])
    browser.close()

httpd.shutdown()
print()
if FAILS:
    print("FAIL: %d" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("WYNIK: OK — wszystkie bramki wysylki kopii zielone")
