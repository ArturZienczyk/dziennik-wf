# Wdraża wersję roboczą do prawdziwego dziennika — po akceptacji usera.
#
# Układ pracy (ustalony 2026-09-20):
#   1. zmiany trafiają do dziennik_wf_roboczy.html — skrót "Dziennik WF" z pulpitu
#      go NIE widzi, wiec dziennik Artura zostaje nietkniety,
#   2. python zrob_piaskownice.py  -> piaskownica z roboczego, do klikania,
#   3. Artur mowi "pasuje",
#   4. python wdroz_roboczy.py     -> dopiero teraz zmiana wchodzi do dziennika.
#
# Dane NIE sa tu ruszane: siedza w localStorage/IndexedDB przegladarki, nie w HTML.
# Podmiana pliku zmienia KOD apki; wpisy zostaja na miejscu po odswiezeniu.
#
#     python wdroz_roboczy.py            — pokaz, co sie zmieni (nic nie rusza)
#     python wdroz_roboczy.py --wdroz    — wykonaj podmiane

import difflib
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROD = ROOT / "dziennik_wf.html"
ROBOCZY = ROOT / "dziennik_wf_roboczy.html"
ODLOZONE = ROOT / "_wersje-poprzednie"


def podsumuj_roznice(stary, nowy):
    """Ile linii dochodzi/znika i jakie fragmenty — żeby wdrożenie nie było
    skokiem w ciemno. Nie zastępuje przeglądu kodu, ale łapie niespodzianki
    w rodzaju 'roboczy jest starszy niż prod'."""
    a = stary.splitlines()
    b = nowy.splitlines()
    plus = minus = 0
    probki = []
    for linia in difflib.unified_diff(a, b, lineterm="", n=0):
        if linia.startswith("+++") or linia.startswith("---") or linia.startswith("@@"):
            continue
        if linia.startswith("+"):
            plus += 1
            if len(probki) < 6:
                probki.append("  + " + linia[1:].strip()[:100])
        elif linia.startswith("-"):
            minus += 1
            if len(probki) < 6:
                probki.append("  - " + linia[1:].strip()[:100])
    return plus, minus, probki


def main():
    if not ROBOCZY.exists():
        print("BLAD: brak %s" % ROBOCZY.name)
        print("Wersja robocza nie istnieje — nie ma czego wdrazac.")
        return 1
    if not PROD.exists():
        print("BLAD: brak %s" % PROD.name)
        return 1

    stary = PROD.read_text(encoding="utf-8")
    nowy = ROBOCZY.read_text(encoding="utf-8")

    if stary == nowy:
        print("Roboczy i dziennik sa IDENTYCZNE — nie ma czego wdrazac.")
        return 0

    plus, minus, probki = podsumuj_roznice(stary, nowy)
    print("Zmiany roboczy -> dziennik_wf.html:")
    print("  +%d linii, -%d linii" % (plus, minus))
    if probki:
        print("Probka:")
        for p in probki:
            print(p)

    if "--wdroz" not in sys.argv:
        print()
        print("To byl PODGLAD — nic nie ruszone.")
        print("Wdrozenie: python wdroz_roboczy.py --wdroz")
        return 0

    # Kopia poprzedniej wersji KODU (nie danych) — powrot jednym ruchem,
    # gdyby cos przeoczyl zarowno test, jak i oko.
    ODLOZONE.mkdir(exist_ok=True)
    znacznik = datetime.now().strftime("%Y-%m-%d_%H-%M")
    kopia = ODLOZONE / ("dziennik_wf_przed_%s.html" % znacznik)
    shutil.copy2(PROD, kopia)

    shutil.copy2(ROBOCZY, PROD)

    print()
    print("WDROZONE: %s" % PROD)
    print("Poprzednia wersja kodu: %s" % kopia)
    print("Twoje wpisy sa nietkniete — siedza w przegladarce, nie w pliku.")
    print("Odswiez dziennik (F5), zeby zobaczyc zmiane.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
