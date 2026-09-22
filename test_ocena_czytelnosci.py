# Bramka: każda trasa z ocena_czytelnosci.TRASY wciąż przechodzi na aktualnej apce.
#
# Po co: panel krytyków odpala się rzadko (na zgłoszenie Artura, decyzja 22.09), a selektory
# w trasach gniją przy każdej zmianie UI. Bez tej bramki pierwsze zgłoszenie po miesiącu
# zaczynałoby się od naprawiania skryptu. Bramka NIE ocenia czytelności — tylko to, że trasa
# daje komplet zrzutów bez błędów JS i że brief wymienia każdy z nich.
import sys
import tempfile
from pathlib import Path

from ocena_czytelnosci import TRASY, renderuj, zapisz_brief

PORT = 8813
FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name)


with tempfile.TemporaryDirectory() as tmp:
    for nazwa, trasa in TRASY.items():
        katalog = Path(tmp) / nazwa
        try:
            pliki, bledy = renderuj(nazwa, katalog, PORT)
        except Exception as e:
            check("%s: trasa przechodzi" % nazwa, False, str(e).splitlines()[0][:160])
            continue
        oczekiwane = len(trasa.kroki) * len(trasa.szerokosci)
        check(
            "%s: komplet zrzutów" % nazwa,
            len(pliki) == oczekiwane and all(p.stat().st_size > 5000 for p in pliki),
            "%d/%d" % (len(pliki), oczekiwane),
        )
        check("%s: bez błędów JS" % nazwa, not bledy, bledy[:2])
        check("%s: cele dla K4" % nazwa, len(trasa.cele) >= 1)
        brief = zapisz_brief(nazwa, pliki, katalog).read_text(encoding="utf-8")
        brak = [p.name for p in pliki if p.name not in brief]
        check("%s: brief wymienia każdy zrzut" % nazwa, not brak, brak[:3])

# Szerokość telefonu ma być telefonem (pointer: coarse) — inaczej apka pokazuje etykiety laptopa,
# a krytyk ocenia ekran, którego telefon nigdy nie widzi (K4, 22.09: „Wyślij kopię na telefon").
from playwright.sync_api import sync_playwright
from fixture_stan import otworz, serwer

with serwer(PORT) as p, sync_playwright() as pw:
    browser, ctx, page, errors = otworz(pw, p, viewport={"width": 390, "height": 900}, telefon=True)
    check("telefon: pointer coarse", page.evaluate("matchMedia('(pointer: coarse)').matches"))
    etykieta = page.evaluate("document.getElementById('pasekWyslij').textContent")
    check("telefon: kopia jedzie na laptop", "laptop" in etykieta, etykieta)
    browser.close()

print("WYNIK: %s" % ("OK" if not FAILS else "%d FAIL" % len(FAILS)))
sys.exit(1 if FAILS else 0)
