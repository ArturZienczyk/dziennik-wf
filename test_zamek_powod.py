# Test: ekran blokady mówi, czemu prosi o hasło zamiast PIN-u (2026-11-17).
# Start/przeładowanie -> zdanie „otworzył się od nowa”; zasłona bez PIN-u -> zdanie „nie masz PIN-u”;
# zasłona z PIN-em -> ekran PIN, a „Użyj hasła” bez zdania (user wybrał sam).
# Użycie: py -3.14 test_zamek_powod.py [plik.html]
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fixture_stan import HASLO, otworz, serwer, zasiej  # noqa: E402

PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
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


def powod(page):
    el = page.locator("#zamek .zamek-powod")
    return el.inner_text() if el.count() else ""


with serwer(8800) as port, sync_playwright() as pw:
    browser, ctx, page, errors = otworz(pw, port, plik=PLIK)
    zasiej(page)
    page.evaluate("() => save(true)")
    page.wait_for_timeout(300)

    # 1. zasłona bez PIN-u
    page.evaluate("() => zamekZablokuj('ręcznie')")
    page.wait_for_timeout(150)
    check(
        "bez PIN-u: ekran hasła",
        page.locator("#zamekInput[autocomplete='current-password']").count() == 1,
    )
    check(
        "bez PIN-u: zdanie o braku PIN-u",
        "Nie masz ustawionego PIN-u" in powod(page),
        powod(page),
    )
    page.fill("#zamekInput", HASLO)
    page.keyboard.press("Enter")
    page.wait_for_timeout(600)
    page.evaluate(
        "() => { if (typeof zamekUI_pinPomin === 'function' && zamek.tryb === 'pin-ustaw') zamekUI_pinPomin(); }"
    )

    # 2. przeładowanie strony -> hasło ze zdaniem o otwarciu od nowa
    page.reload()
    page.wait_for_timeout(600)
    check(
        "po przeładowaniu: ekran hasła",
        page.locator("#zamekInput[autocomplete='current-password']").count() == 1,
    )
    check(
        "po przeładowaniu: zdanie „otworzył się od nowa”",
        "otworzył się od nowa" in powod(page),
        powod(page),
    )
    page.screenshot(path=str(ZRZUTY / "zamek_powod_start.png"))

    # 3. z PIN-em: zasłona -> PIN; „Użyj hasła” -> hasło bez zdania
    page.fill("#zamekInput", HASLO)
    page.keyboard.press("Enter")
    page.wait_for_timeout(800)
    if page.locator("#zamek .zamek-pin").count():  # apka proponuje PIN po odblokowaniu
        page.fill("#zamekInput", "1234")
        page.evaluate("() => zamekUI_pinUstaw()")
    else:
        page.evaluate("() => zamekUI_pinZmien()")
        page.fill("#zamekInput", "1234")
        page.evaluate("() => zamekUI_pinUstaw()")
    page.wait_for_timeout(400)
    page.evaluate("() => zamekZablokuj('ręcznie')")
    page.wait_for_timeout(150)
    check("z PIN-em: ekran PIN", page.locator("#zamek .zamek-pin").count() == 1)
    page.click("#zamek button:has-text('Użyj hasła')")
    page.wait_for_timeout(150)
    check("„Użyj hasła”: bez zdania o powodzie", powod(page) == "", powod(page))

    check("brak błędów JS", not errors, errors)
    browser.close()

print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
