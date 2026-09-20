# Generuje piaskownicę — kopię dziennika z WŁASNYM magazynem.
#
# Po co: żeby klikać, testować i psuć bez cienia ryzyka dla prawdziwych wpisów.
# Sama kopia pliku NIE wystarcza — dane nie siedzą w HTML, tylko w localStorage
# i IndexedDB przeglądarki, pod stałymi kluczami. Dwie kopie tego samego pliku
# otwarte z tego samego originu widzą TE SAME dane; skasowanie klasy w "kopii"
# skasowałoby ją naprawdę. Dlatego piaskownica dostaje podmienione klucze
# magazynu — wtedy jest odcięta niezależnie od tego, skąd ją otworzysz.
#
# Generator, nie ręczna kopia: dziennik się zmienia, a piaskownica ma być
# odtwarzalna jednym poleceniem, nie zapomnianym plikiem sprzed miesiąca.
#
#     python zrob_piaskownice.py
#
# Wynik: dziennik_wf_piaskownica.html (w .gitignore — to artefakt, nie kod).

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROD = ROOT / "dziennik_wf.html"  # plik, w który celuje skrót "Dziennik WF" z pulpitu
ROBOCZY = ROOT / "dziennik_wf_roboczy.html"  # tu powstają zmiany przed akceptacją
CEL = ROOT / "dziennik_wf_piaskownica.html"

# Domyślnie bierzemy ROBOCZY: piaskownica ma pokazywać to, co dopiero ma wejść
# do dziennika, a nie to, co już w nim jest. `--z prod` wymusza wersję produkcyjną
# (np. żeby odtworzyć zgłoszony objaw na tym, czego user faktycznie używa).
ZRODLO = ROBOCZY if ROBOCZY.exists() else PROD

# Każdy klucz, pod którym apka trzyma stan. Podmiana WSZYSTKICH naraz jest
# warunkiem izolacji — zostawienie jednego (np. IndexedDB) zrobiłoby piaskownicę,
# która po cichu dopisuje się do prawdziwego magazynu.
PODMIANY = [
    (
        "const STORAGE_KEY = 'dziennik_wf_v1';",
        "const STORAGE_KEY = 'dziennik_wf_PIASKOWNICA';",
    ),
    ("const IDB_NAME = 'dziennik_wf';", "const IDB_NAME = 'dziennik_wf_PIASKOWNICA';"),
    ("<title>Dziennik WF</title>", "<title>PIASKOWNICA — Dziennik WF</title>"),
]

# Pasek na górze: piaskownica ma być rozpoznawalna od pierwszego spojrzenia,
# żeby nigdy nie wpisać do niej prawdziwej lekcji (i nie szukać jej potem w dzienniku).
# Pasek u DOŁU, nie u góry: górę zajmuje przyklejona belka apki (tytuł, zakładki,
# belka dnia) — pasek sticky top:0 przykrywał jej pierwszy wiersz i psuł ocenę wyglądu.
PASEK = (
    '<div style="position:fixed;left:0;right:0;bottom:0;z-index:99999;background:#b91c1c;color:#fff;'
    'padding:6px 14px;font:600 13px/1.4 system-ui,sans-serif;text-align:center">'
    "PIASKOWNICA — osobny magazyn danych. Wpisy STĄD NIE trafiają do Twojego dziennika "
    "(i odwrotnie). Do prób i klikania.</div>"
)


def main():
    zrodlo = PROD if "--z" in sys.argv and "prod" in sys.argv else ZRODLO
    if not zrodlo.exists():
        print("BLAD: brak %s" % zrodlo)
        return 1

    print("Zrodlo: %s" % zrodlo.name)
    html = zrodlo.read_text(encoding="utf-8")

    for stare, nowe in PODMIANY:
        if stare not in html:
            # Twardy stop, nie ostrzeżenie: gdyby apka zmieniła nazwę klucza,
            # cicha piaskownica dzieliłaby magazyn z prawdziwym dziennikiem.
            print("BLAD: nie znalazlem w zrodle fragmentu:\n  %s" % stare)
            print(
                "Apka zmienila nazwe klucza magazynu — popraw PODMIANY w tym skrypcie."
            )
            print(
                "NIE generuje piaskownicy: bez podmiany wszystkich kluczy nie jest odcieta."
            )
            return 1
        html = html.replace(stare, nowe)

    # W pasku nazwa źródła: inaczej po tygodniu nie wiadomo, czy klikasz nowość
    # z roboczego, czy to samo, co masz już w dzienniku.
    pasek = PASEK.replace("</div>", " Zrodlo: %s</div>" % zrodlo.name)
    html = re.sub(r"(<body[^>]*>)", r"\1\n" + pasek, html, count=1)

    CEL.write_text(html, encoding="utf-8")

    # Kontrola po fakcie: czy w gotowym pliku nie został ani jeden stary klucz.
    # Szukamy DEKLARACJI kluczy, nie samego napisu: apka ma też
    # `k.indexOf('dziennik_wf') === 0` (test prefiksu w diagnostyce magazynu),
    # który jest poprawny także w piaskownicy i nie jest kluczem do podmiany.
    zostalo = [
        k
        for k in ("STORAGE_KEY = 'dziennik_wf_v1'", "IDB_NAME = 'dziennik_wf'")
        if k in html
    ]
    if zostalo:
        print("BLAD: w piaskownicy zostal stary klucz magazynu: %s" % zostalo)
        CEL.unlink()
        return 1

    print("Gotowe: %s" % CEL)
    print("  magazyn: dziennik_wf_PIASKOWNICA (localStorage + IndexedDB)")
    print("  Twoj dziennik (dziennik_wf_v1) jest nietkniety.")
    print("\nOtworz dwuklikiem. Pierwsze uruchomienie poprosi o wlasne haslo —")
    print("to osobny zamek, nie ten z prawdziwego dziennika.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
