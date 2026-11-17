# Test: korekty tygodnia rotacji hali (2026-11-17).
# Szkoła powtórzyła krótki tydzień 9–13.11 jako II → od 16.11 jest III, choć z daty wychodzi IV.
# Sprawdza: rotacjaTydzien() z kotwicą i bez, plakietkę miejsca, klik w zakładce Plan (ustaw / zdejmij),
# zachowanie kotwic przy ponownym wczytaniu plan-wf.json.
# Użycie: py -3.14 test_rotacja_korekty.py [plik.html]
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fixture_stan import otworz, serwer, zasiej  # noqa: E402

PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
PLAN = ROOT.parent.parent / "plan-roczny" / "plan-lekcji-2026-09" / "plan-wf.json"
ZRZUTY = ROOT / "_zrzuty"
ZRZUTY.mkdir(exist_ok=True)
FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


plan = json.loads(PLAN.read_text(encoding="utf-8"))
bez = json.loads(json.dumps(plan))
bez["rotacja"].pop("korekty", None)
check(
    "plan-wf.json niesie korektę 09.11 = II",
    plan["rotacja"].get("korekty", {}).get("2026-11-09") == 2,
    plan["rotacja"].get("korekty"),
)

TYG = "(pon) => rotacjaTydzien(zaleglePlany().find(p => p.rotacja), pon)"

with serwer(8798) as port, sync_playwright() as pw:
    browser, ctx, page, errors = otworz(pw, port, plik=PLIK)
    zasiej(page)

    # 1. bez korekty: liczenie z daty jak przed 17.11
    page.evaluate("(p) => { zaleglePlanZastosuj(p); }", bez)
    z_daty = {
        d: page.evaluate(TYG, d)
        for d in ["2026-09-28", "2026-11-02", "2026-11-09", "2026-11-16"]
    }
    check(
        "bez korekty: 28.09=I, 02.11=II, 09.11=III, 16.11=IV",
        z_daty == {"2026-09-28": 0, "2026-11-02": 1, "2026-11-09": 2, "2026-11-16": 3},
        z_daty,
    )
    check(
        "przed startem cyklu: brak tygodnia", page.evaluate(TYG, "2026-09-21") is None
    )

    # 2. wczytanie planu z korektą: kotwica dochodzi do istniejącego planu
    page.evaluate("(p) => { zaleglePlanZastosuj(p); }", plan)
    k = {
        d: page.evaluate(TYG, d)
        for d in ["2026-11-02", "2026-11-09", "2026-11-16", "2026-11-23", "2026-11-30"]
    }
    check(
        "z korektą: 02.11=II (bez zmian), 09.11=II, 16.11=III, 23.11=IV, 30.11=I",
        k
        == {
            "2026-11-02": 1,
            "2026-11-09": 1,
            "2026-11-16": 2,
            "2026-11-23": 3,
            "2026-11-30": 0,
        },
        k,
    )

    # 3. plakietka idzie za korektą: lekcja, gdzie tydzień III i IV różnią się miejscem
    tyg = plan["rotacja"]["tygodnie"]
    rozne = [
        (d, nr)
        for d in tyg[2]
        for nr in tyg[2][d]
        if tyg[3].get(d, {}).get(nr) != tyg[2][d][nr]
    ]
    check("w danych jest lekcja z innym miejscem w III i IV", bool(rozne), rozne[:3])
    if rozne:
        d, nr = rozne[0]
        iso = "2026-11-%02d" % (16 + int(d))
        m = page.evaluate("([iso, nr]) => miejsceLekcji(iso, nr)", [iso, int(nr)])
        check(
            "plakietka %s L%s = miejsce z tygodnia III" % (iso, nr),
            m and m["kod"] == tyg[2][d][nr],
            (m, tyg[2][d][nr], tyg[3].get(d, {}).get(nr)),
        )

    # 4. zakładka Plan: karta, klik ustawia i zdejmuje korektę
    page.click("button.tab:has-text('Plan')")
    page.wait_for_timeout(200)
    ten = page.evaluate("() => tydzienPoniedzialek(dzisISO())")
    wiersz = '#planUstawienia .rot-wiersz[data-pon="%s"]' % ten
    check(
        "karta Rotacja hali z wierszem tego tygodnia", page.locator(wiersz).count() == 1
    )
    auto = page.evaluate(TYG, ten)
    on = page.eval_on_selector(wiersz + " .rot-nr.on", "e => +e.dataset.n")
    check("podświetlony numer = policzony", on == auto + 1, (on, auto))
    page.locator(wiersz).screenshot(path=str(ZRZUTY / "rot_1_karta_wiersz.png"))
    page.locator(".plan-karta:has(.rot-lista)").screenshot(
        path=str(ZRZUTY / "rot_2_karta.png")
    )
    inny = (auto + 1) % 4 + 1  # numer 1-4 różny od policzonego
    page.click(wiersz + ' .rot-nr[data-n="%d"]' % inny)
    page.wait_for_timeout(150)
    check(
        "klik: tydzień = wybrany numer",
        page.evaluate(TYG, ten) == inny - 1,
        page.evaluate(TYG, ten),
    )
    check(
        "klik: wiersz oznaczony „korekta”",
        page.locator(wiersz + " .rot-kor").count() == 1,
    )
    nast = page.evaluate("(t) => usprDodajDni(t, 7)", ten)
    check(
        "następny tydzień liczy się dalej po kolei",
        page.evaluate(TYG, nast) == inny % 4,
        page.evaluate(TYG, nast),
    )

    # 5. ponowne wczytanie planu nie kasuje kliknięcia
    page.evaluate("(p) => { zaleglePlanZastosuj(p); }", plan)
    check(
        "reimport plan-wf.json: kliknięta korekta zostaje",
        page.evaluate(TYG, ten) == inny - 1,
    )
    page.evaluate("() => renderPlanUstawienia()")

    # 6. klik w numer z daty zdejmuje korektę
    bez_kotwicy = page.evaluate(
        "(t) => rotacjaTydzien(zaleglePlany().find(p => p.rotacja), t, t)", ten
    )
    page.click(wiersz + ' .rot-nr[data-n="%d"]' % (bez_kotwicy + 1))
    page.wait_for_timeout(150)
    kor = page.evaluate("() => zaleglePlany().find(p => p.rotacja).rotacja.korekty")
    check("klik w numer z daty: kotwica zdjęta", ten not in kor, kor)
    check("korekta 09.11 z pliku nietknięta", kor.get("2026-11-09") == 2, kor)

    # 7. telefon: karta mieści się w szerokości
    b2, c2, p2, e2 = otworz(
        pw, port, viewport={"width": 369, "height": 608}, plik=PLIK, telefon=True
    )
    zasiej(p2)
    p2.evaluate("(p) => { zaleglePlanZastosuj(p); }", plan)
    p2.click("button.tab:has-text('Plan')")
    p2.wait_for_timeout(200)
    p2.locator(".plan-karta:has(.rot-lista)").scroll_into_view_if_needed()
    p2.screenshot(path=str(ZRZUTY / "rot_3_telefon.png"))
    sz = p2.evaluate(
        "() => document.querySelector('.plan-karta:has(.rot-lista)').scrollWidth <= document.querySelector('.plan-karta:has(.rot-lista)').clientWidth + 1"
    )
    check("telefon: karta bez poziomego przewijania", sz)
    check("telefon: brak błędów JS", not e2, e2)
    b2.close()

    check("brak błędów JS", not errors, errors)
    browser.close()

print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
