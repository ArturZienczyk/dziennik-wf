# Bramka: dziennik NIE MOZE wykonywac zadnych zapytan poza laptop.
# Przechwytuje kazde zapytanie sieciowe podczas typowej pracy (otwarcie, dopisanie
# ucznia, nadanie statusu, zapis lekcji) i przepuszcza wylacznie file://.
#
# Po co: do 2026-09-14 kroje pisma ciagnely sie z fonts.googleapis.com, wiec przy
# kazdym otwarciu dziennika laptop laczyl sie z Google (bez danych dzieci, ale
# jednak). Kroje sa teraz wklejone w plik. Ten test pilnuje, zeby jakas przyszla
# zmiana - biblioteka z CDN, ikonka, czcionka - nie otworzyla tego kanalu na nowo.
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

FILE = (Path(__file__).resolve().parent / "dziennik_wf.html").as_uri()
zapytania = []

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page()
    page.on("request", lambda r: zapytania.append(r.url))
    page.goto(FILE)
    page.wait_for_timeout(1500)

    # typowa praca: uczen + status + zapis lekcji (haslo kopii podstawione z gory)
    page.evaluate(
        "() => { state.students.length = 0; save();"
        " localStorage.setItem('dziennik_wf_backup_pwd', 'x-haslo-123'); }"
    )
    page.click('button:has-text("Uczniowie")')
    page.click("#quickAddStudent")
    page.keyboard.type("Testowy Uczen")
    page.keyboard.press("Enter")
    page.click('button:has-text("Obecność")')
    page.click("h1")
    page.keyboard.press("n")
    page.wait_for_timeout(800)

    b.close()

zewnetrzne = [u for u in zapytania if not u.startswith("file://")]
print("Zapytan lacznie: %d, w tym poza laptop: %d" % (len(zapytania), len(zewnetrzne)))
for u in sorted(set(zewnetrzne)):
    print("   -> " + u[:110])

if zewnetrzne:
    print("\nWYNIK: FAIL - dziennik laczy sie ze swiatem. Wklej zasob do pliku")
    print("(wzorzec: scratchpad/osadz_fonty.py -> kroje jako data: URI).")
    sys.exit(1)

print("\nWYNIK: PASS - zero zapytan poza laptop.")
