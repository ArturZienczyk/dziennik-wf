# Test end-to-end „Scalanie kopii” (laptop ↔ telefon, 2026-09-18): znaczniki czasu z diffu w save(),
# scalKopie (nowszy wygrywa, remis 0/0 = lokalne, nagrobek), plan przez upsert, klasa nieznana dochodzi,
# checkbox „zastąp wszystko” usunięty (19.09) — klasa z pliku DOCHODZI, okno importu bez checkboxa, znaczniki przeżywają magazyn.
import sys
import json
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

    # 1. Laptop A: klasa 7b z 3 uczniami, lekcje 1 i 2 (klucz data#nr). Znaczniki po save().
    page.evaluate("""() => {
      const c = state.classes[0];
      c.name = '7b';
      c.students = [{id:'u1',name:'Ala',longTermReleased:false,height:'',weight:''},
                    {id:'u2',name:'Bartek',longTermReleased:false,height:'',weight:''},
                    {id:'u3',name:'Celina',longTermReleased:false,height:'',weight:''}];
      c.attendance = {'2026-09-14#1': {u1:'C',u2:'NC',u3:'C'}, '2026-09-14#2': {u1:'C',u2:'C',u3:'BS'}};
      activateClass(c.id); save(); refreshAll();
    }""")
    page.wait_for_timeout(300)
    t = page.evaluate("() => state.classes[0]._t")
    check(
        "znaczniki: wpisy frekwencji ostemplowane",
        t.get("a|2026-09-14#1|u2", 0) > 0 and t.get("a|2026-09-14#2|u3", 0) > 0,
        str(list(t)[:5]),
    )
    check(
        "znaczniki: uczniowie i meta klasy", t.get("s|u1", 0) > 0 and t.get("k", 0) > 0
    )

    # 2. Telefon B = kopia A, potem u B: lekcja 2 u2 → BS (nowsze), dodana lekcja 3, ocena, pomiar, nie było,
    #    skasowany wpis u3 z lekcji 1 (nagrobek), nowa klasa 8c, plan.
    cid = page.evaluate("() => state.classes[0].id")
    tel = page.evaluate(
        """() => JSON.parse(JSON.stringify({classes: state.classes, currentClassId: state.currentClassId, planWf: state.planWf}))"""
    )
    B = tel["classes"][0]
    tB = max(t.values()) + 60000
    B["attendance"]["2026-09-14#2"]["u2"] = "BS"
    B["_t"]["a|2026-09-14#2|u2"] = tB
    B["attendance"]["2026-09-15#3"] = {
        "u1": "C",
        "u2": "C",
        "u3": {"s": "C", "sp": True},
    }
    for sid in ("u1", "u2", "u3"):
        B["_t"]["a|2026-09-15#3|" + sid] = tB
    del B["attendance"]["2026-09-14#1"]["u3"]
    B["_t"]["a|2026-09-14#1|u3"] = tB  # nagrobek
    B["gradeColumns"].append(
        {
            "id": "gc_1",
            "fullName": "Skok",
            "shortName": "Sk",
            "date": "2026-09-15",
            "weight": 1,
        }
    )
    B["grades"]["gc_1"] = {"u1": 5}
    B["_t"]["gc|gc_1"] = tB
    B["_t"]["g|gc_1|u1"] = tB
    B["measurements"] = {"u2": {"height": "150"}}
    B["_t"]["m|u2"] = tB
    B["odwolane"] = {"2026-09-16#1": "wycieczka"}
    B["_t"]["o|2026-09-16#1"] = tB
    B["students"][2]["name"] = "Celina N."  # nowsze nazwisko
    B["_t"]["s|u3"] = tB
    tel["classes"].append(
        {
            "id": "k_telefon_8c",
            "school": "",
            "name": "8c",
            "students": [{"id": "u1", "name": "Darek"}],
            "attendance": {"2026-09-14#5": {"u1": "C"}},
            "measurements": {},
            "gradeColumns": [],
            "grades": {},
            "semesterBreak": "",
            "_t": {"a|2026-09-14#5|u1": tB},
        }
    )
    tel["planWf"] = {
        "plany": [
            {
                "od": "2026-09-01",
                "do": "2026-09-30",
                "klasy": {"7b": {"0": [1, 2]}},
                "wolne": ["2026-09-14"],
                "zrodlo": "test",
            }
        ]
    }

    # 2a. Laptop w międzyczasie: u1 lekcja 1 → NC (lokalnie nowsze niż kopia B? nie — B ma równy t dla u1 L1,
    #     bo nie zmienił; lokalny wygrywa przy remisie i przy nowszym).
    page.evaluate("() => { state.attendance['2026-09-14#1']['u1'] = 'NB'; save(); }")
    page.wait_for_timeout(200)

    w = page.evaluate("(d) => scalKopie(d)", tel)
    page.evaluate("() => { save(); refreshAll(); }")
    A = page.evaluate("() => state.classes[0]")
    check(
        "u2 L2 = wersja z telefonu (nowszy t)",
        A["attendance"]["2026-09-14#2"]["u2"] == "BS",
    )
    check(
        "lekcja 3 doszła w całości",
        A["attendance"].get("2026-09-15#3", {}).get("u3") == {"s": "C", "sp": True},
    )
    check(
        "u1 L1 = lokalne NB (lokalna zmiana nowsza)",
        A["attendance"]["2026-09-14#1"]["u1"] == "NB",
    )
    check(
        "nagrobek: u3 L1 skasowany na telefonie → znika",
        "u3" not in A["attendance"]["2026-09-14#1"],
    )
    check(
        "ocena i kolumna doszły",
        any(c["id"] == "gc_1" for c in A["gradeColumns"])
        and A["grades"]["gc_1"]["u1"] == 5,
    )
    check("pomiar doszedł", A["measurements"]["u2"]["height"] == "150")
    check("nie było doszło", A.get("odwolane", {}).get("2026-09-16#1") == "wycieczka")
    check("nazwisko nowsze z telefonu", A["students"][2]["name"] == "Celina N.")
    check(
        "klasa nieznana z pliku dochodzi",
        page.evaluate("() => state.classes.length") == 2 and w["klasyDodane"] == 1,
    )
    check(
        "plan scalony przez upsert",
        page.evaluate("() => zaleglePlany().length") == 1
        and page.evaluate("() => zaleglePlany()[0].wolne") == ["2026-09-14"],
    )
    check(
        "lista nadpisanych = 3 (u2 L2 + nagrobek u3 L1 + nazwisko u3)",
        len(w["nadpisane"]) == 3,
        str(w["nadpisane"]),
    )
    check("dodane = L3×3 + gc + g + m + o = 7", w["dodane"] == 7, w["dodane"])
    check(
        "pominięte = u1 L1 (lokalne nowsze)",
        w["pominiete"] == 1,
        str(w["pominieteSciezki"]),
    )
    check(
        "opis nadpisania czytelny",
        any(
            "Bartek" in n["co"] and n["bylo"] == "C" and n["jest"] == "BS"
            for n in w["nadpisane"]
        ),
        w["nadpisane"],
    )

    # 3. Idempotencja: ta sama kopia drugi raz = nic
    w2 = page.evaluate("(d) => scalKopie(d)", tel)
    check(
        "drugie scalenie tej samej kopii nic nie zmienia",
        w2["dodane"] == 0 and w2["nadpisane"] == [] and w2["klasyDodane"] == 0,
        w2,
    )

    # 4. Plik bez znaczników (stara kopia) nic nie nadpisuje, dokłada tylko brakujące
    stary = json.loads(json.dumps(tel))
    for c in stary["classes"]:
        c.pop("_t", None)
    stary["classes"][0]["attendance"]["2026-09-14#2"]["u2"] = (
        "NC"  # inna wartość, bez t
    )
    stary["classes"][0]["attendance"]["2026-09-17#1"] = {"u1": "C"}  # brakujący wpis
    w3 = page.evaluate("(d) => scalKopie(d)", stary)
    A = page.evaluate("() => state.classes[0]")
    check(
        "kopia bez t nie nadpisuje istniejących",
        A["attendance"]["2026-09-14#2"]["u2"] == "BS" and w3["nadpisane"] == [],
    )
    check(
        "kopia bez t dokłada brakujące (0 vs brak)",
        A["attendance"].get("2026-09-17#1", {}).get("u1") == "C" and w3["dodane"] == 1,
        w3,
    )

    # 5. Znaczniki przeżywają magazyn (reload + odblokowanie)
    page.evaluate("() => save(true)")
    page.wait_for_timeout(500)
    page.reload()
    page.wait_for_timeout(500)
    page.evaluate("() => zamekOdblokuj('test-haslo-123')")
    page.wait_for_timeout(700)
    t2 = page.evaluate("() => state.classes[0]._t")
    check(
        "po reloadzie znaczniki są",
        t2.get("a|2026-09-14#2|u2") == tB,
        t2.get("a|2026-09-14#2|u2"),
    )
    # zapis bez zmiany nie przestemplowuje
    page.evaluate("() => save()")
    page.wait_for_timeout(200)
    check(
        "save bez zmian nie zmienia znaczników",
        page.evaluate("() => state.classes[0]._t['a|2026-09-14#2|u2']") == tB,
    )

    # 6. importZastosuj z klasą nieznaną lokalnie = klasa dochodzi (dawniej checkbox „zastąp wszystko” — usunięty)
    page.evaluate(
        "(d) => importZastosuj(d)",
        {
            "classes": [
                {
                    "id": "k_nowa",
                    "school": "",
                    "name": "1a",
                    "students": [],
                    "attendance": {},
                    "measurements": {},
                    "gradeColumns": [],
                    "grades": {},
                    "semesterBreak": "",
                }
            ]
        },
    )
    page.wait_for_timeout(200)
    check(
        "klasa z pliku dochodzi, lokalna 7b zostaje (bez trybu podmiany)",
        sorted(page.evaluate("() => state.classes.map(c => c.name)")) == ["1a", "7b", "8c"],
    )

    # 7. Okno importu: tekst o scalaniu, BEZ checkboxa; po scaleniu okno informacyjne
    page.evaluate(
        "() => showConfirm('Wczytaj dane', IMPORT_TEKST, () => {})"
    )
    check(
        "okno importu bez checkboxa „zastąp wszystko”",
        not page.locator("#confirmOpcja").is_visible()
        and "SCALONA" in page.inner_text("#confirmMessage"),
    )
    page.screenshot(path=str(SHOTS / "scalanie_1_okno_importu.png"))
    page.evaluate("() => confirmCancel()")
    page.evaluate("(d) => importZastosuj(d)", tel)
    page.wait_for_timeout(300)
    check(
        "po scaleniu okno informacyjne z listą",
        page.locator("#confirmModal").evaluate("e => e.classList.contains('active')")
        and "Scalono" in page.inner_text("#confirmTitle"),
    )
    check(
        "okno informacyjne bez checkboxa",
        not page.locator("#confirmOpcja").is_visible(),
    )
    page.screenshot(path=str(SHOTS / "scalanie_2_wynik.png"))
    page.evaluate("() => confirmOk()")
    check(
        "po dwóch scaleniach: klasy 1a, 7b, 8c",
        sorted(page.evaluate("() => state.classes.map(c => c.name)"))
        == ["1a", "7b", "8c"],
    )

    # 7b. Kopia szyfrowana niesie plan (empiria 18.09: telefon nie dostał planu, bo snapshot go nie miał)
    kopia = page.evaluate(
        """async () => { const txt = await encryptSnapshot('haslo-kopii'); const d = await decryptBackup(txt, 'haslo-kopii');
             return { maPlan: !!(d.planWf && d.planWf.plany && d.planWf.plany.length), od: d.planWf && d.planWf.plany[0] && d.planWf.plany[0].od }; }"""
    )
    check(
        "szyfrowana kopia zawiera plan",
        kopia["maPlan"] and kopia["od"] == "2026-09-01",
        kopia,
    )

    # 8. Drugi folder kopii: przycisk i atrapa zapisu do obu
    check("przycisk zapasowego folderu jest", "Zapasowy folder" in page.inner_text("#btnFolderKopii2"))
    page.evaluate("""async () => {
      window._zapisy = [];
      const atrapa = nazwa => ({ name: nazwa, queryPermission: async () => 'granted',
        getFileHandle: async (fn) => ({ createWritable: async () => ({ write: async (t) => window._zapisy.push(nazwa + '/' + fn), close: async () => {} }) }) });
      _folderKopii = atrapa('Lokalny'); _folderKopiiNazwa = 'Lokalny';
      _folderKopii2 = atrapa('Dysk Google'); _folderKopii2Nazwa = 'Dysk Google';
      await zapiszDoFolderuKopii('x', 'a.enc.json'); await zapiszDoFolderuKopii('x', 'a.enc.json', 2);
    }""")
    z = page.evaluate("() => window._zapisy")
    check(
        "kopia idzie do obu folderów",
        z == ["Lokalny/a.enc.json", "Dysk Google/a.enc.json"],
        z,
    )

    check("brak błędów JS", not errors, str(errors))
    browser.close()

httpd.shutdown()
print("\n%d FAIL" % len(FAILS) if FAILS else "\nALL PASS")
sys.exit(1 if FAILS else 0)
