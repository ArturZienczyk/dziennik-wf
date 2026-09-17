# Test Szczebel 2A: usprawiedliwienie z e-dziennika (u/ns/z) w kratce VULCAN nie jest nadpisywane
# nieobecnoscia (NB -> '—'). Sprawdza czysta funkcje keepExcused wycieta ze skryptu (ta sama mapa).
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


src = (ROOT / "vulcan-frekwencja.user.js").read_text(encoding="utf-8")
fn = re.search(r"^function keepExcused\(.*?^}", src, re.S | re.M).group(0)
ex = re.search(r"^var EXCUSED=.*?;$", src, re.M).group(0)

CASES = [
    # (symbol chciany przez apke, teksty kratek VULCAN, oczekiwane: zostaw?)
    ("nieobecność", ["u"], True),
    ("nieobecność", ["ns"], True),
    ("nieobecność", ["z"], True),
    ("nieobecność", ["", "u"], True),  # duplikat DOM: jedna kopia pusta
    ("nieobecność", ["U "], True),  # wielkosc liter / spacja
    ("nieobecność", ["•"], False),  # zwykla obecnosc -> nadpisz
    ("nieobecność", ["—"], False),  # juz nieobecny -> zwykly skip w apply
    ("nieobecność", [""], False),
    ("nieobecność", [], False),
    ("nie ćwiczy na zajęciach WF", ["u"], False),  # apka wygrywa dla nc
    ("spóźnienie", ["u"], False),  # apka wygrywa dla spoznienia
    ("nieob. uspraw.", ["u"], False),  # to samo -> skip, nie 'zostawione'
]

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    for sym, texts, exp in CASES:
        got = page.evaluate(
            "([code, sym, texts]) => { eval(code); return keepExcused(sym, texts); }",
            [ex + "\n" + fn, sym, texts],
        )
        check("keepExcused(%r, %r) == %r" % (sym, texts, exp), got == exp, got)
    browser.close()

# log koncowy i kontrola koncowa wiedza o zachowanych
check("apply: galaz keepExcused przed skip", "keepExcused(r.symbol,beforeAll)" in src)
check("kontrola koncowa pomija r.kept", "if(r.kept)return;" in src)
check("log wymienia usprawiedliwionych", "popraw w apce na NU" in src)

print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
