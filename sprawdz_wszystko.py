# Runner wszystkich bramek dziennika WF — jedna komenda zamiast 33 recznych uruchomien.
#
# Po co grupowanie po porcie: kazdy test stawia wlasny serwer HTTP na stalym porcie wpisanym
# w pliku, a kilka testow dzieli ten sam numer (8771 ma cztery, 8769 trzy). Na Windows
# SO_REUSEADDR pozwala drugiemu procesowi przejac zajety port — dwa testy na tym samym porcie
# uruchomione naraz zaczelyby sobie podawac cudze strony i sypac losowo. Dlatego: testy z tym
# samym portem ida po kolei w jednej grupie, a rozne grupy leca rownolegle. Bez tego trzeba by
# bylo przenumerowac porty w 33 plikach.
#
# Uzycie:
#   py -3.14 sprawdz_wszystko.py            — wszystko (tak wola pre-push)
#   py -3.14 sprawdz_wszystko.py -k dyzur   — tylko testy z fragmentem nazwy
#   py -3.14 sprawdz_wszystko.py --szybko   — pomija testy wymagajace recznego srodowiska (POMIJANE)
import argparse
import concurrent.futures as cf
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import odcisk  # sasiedni plik: odcisk wejsc bramek (SKIP pre-pusha po zielonym biegu)

ROOT = Path(__file__).resolve().parent
PY = [sys.executable]

# Testy wymagajace czegos, czego zwykly push nie ma (sprzet, recznie zbudowany plik).
# Nie sa czerwone — po prostu nie odpalaja sie bez przygotowania. Trzymam liste jawnie,
# zeby nikt nie mysli, ze "przechodza", kiedy sa tylko pomijane.
POMIJANE = {
    "test_mikrofon_lokalny.py": "wymaga mikrofonu / recznego kliku",
}

RE_PORT = re.compile(r"^PORT\s*=\s*(\d+)", re.M)
# Testy koncza sie roznymi formulkami (WYNIK: OK / ALL PASS / FAIL: 0 / "3 FAIL") — lapie wszystkie,
# bo podsumowanie w tabelce ma byc czytelne bez otwierania logu.
RE_WYNIK = re.compile(r"^(?:WYNIK\b.*|ALL PASS.*|PASS\b.*|FAIL\b.*|\d+ FAIL.*)$", re.M)


def grupuj(pliki):
    """Testy z tym samym portem -> jedna grupa (ida po kolei). Bez portu -> grupa wlasna."""
    grupy = defaultdict(list)
    for i, f in enumerate(pliki):
        m = RE_PORT.search(f.read_text(encoding="utf-8", errors="replace"))
        grupy[m.group(1) if m else "bez-portu-%d" % i].append(f)
    return list(grupy.values())


def odpal(f):
    t0 = time.time()
    p = subprocess.run(
        PY + [f.name], cwd=str(ROOT), capture_output=True, text=True, errors="replace"
    )
    out = (p.stdout or "") + (p.stderr or "")
    wyniki = RE_WYNIK.findall(out)
    return {
        "plik": f.name,
        "ok": p.returncode == 0,
        "czas": time.time() - t0,
        "podsumowanie": (wyniki[-1].strip() if wyniki else "(brak linii WYNIK)"),
        "out": out,
    }


def odpal_grupe(grupa):
    return [odpal(f) for f in grupa]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", help="uruchom tylko testy z tym fragmentem w nazwie")
    ap.add_argument("-j", type=int, default=5, help="ile grup naraz (domyslnie 5)")
    ap.add_argument(
        "--szybko", action="store_true", help="pomin testy z listy POMIJANE"
    )
    a = ap.parse_args()

    pliki = sorted(ROOT.glob("test_*.py"))
    if a.k:
        pliki = [f for f in pliki if a.k in f.name]
    pominiete = [f for f in pliki if f.name in POMIJANE]
    pliki = [f for f in pliki if f.name not in POMIJANE]
    if not pliki:
        print("Nie znalazlem testow do uruchomienia.")
        return 1

    grupy = grupuj(pliki)
    print(
        "Uruchamiam %d testow w %d grupach (max %d naraz)...\n"
        % (len(pliki), len(grupy), a.j)
    )
    # odcisk liczony PRZED biegiem — to jego stan bedzie sprawdzony przez testy
    fp_przed = odcisk.fingerprint()
    t0 = time.time()
    wyniki = []
    with cf.ThreadPoolExecutor(max_workers=a.j) as ex:
        for r in ex.map(odpal_grupe, grupy):
            wyniki.extend(r)

    wyniki.sort(key=lambda r: r["plik"])
    for r in wyniki:
        print(
            "[%s] %-34s %5.1fs  %s"
            % ("OK  " if r["ok"] else "FAIL", r["plik"], r["czas"], r["podsumowanie"])
        )
    for f in pominiete:
        print("[--  ] %-34s        pominiete: %s" % (f.name, POMIJANE[f.name]))

    zle = [r for r in wyniki if not r["ok"]]
    # Zielony PELNY bieg (bez -k) zapisuje odcisk wejsc — dzieki temu push zaraz po recznym
    # biegu nie powtarza tych samych 75 s. Bieg zawezony -k NIE zapisuje: nie widzial calosci.
    # Zapisujemy odcisk SPRZED biegu i tylko gdy jest nadal aktualny: edycja pliku W TRAKCIE
    # biegu znaczy, ze zielony werdykt dotyczy juz nieistniejacego stanu — wtedy nic nie zapisujemy.
    if not zle and not a.k:
        if fp_przed is not None and odcisk.fingerprint() == fp_przed:
            odcisk.save_state({"green_fp": fp_przed})
        else:
            print(
                "(kod zmienil sie w trakcie biegu — odcisk NIE zapisany, push odpali bramki)"
            )
    print(
        "\n%d/%d zielonych w %.0f s"
        % (len(wyniki) - len(zle), len(wyniki), time.time() - t0)
    )
    if zle:
        for r in zle:
            print("\n" + "=" * 70 + "\n%s — ostatnie linie:\n" % r["plik"])
            print("\n".join(r["out"].strip().splitlines()[-25:]))
        print("\nWYNIK: FAIL — %s" % ", ".join(r["plik"] for r in zle))
        return 1
    print("WYNIK: PASS — wszystkie bramki dziennika zielone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
