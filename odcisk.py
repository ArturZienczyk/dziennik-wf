# -*- coding: utf-8 -*-
"""Skip bramek pre-push po odcisku WEJSC (dziennik WF).

WZOREC: D:/Projects/karty/scripts/build_odcisk.py (BKK, 2026-08-25) — ten sam mechanizm,
inne wejscia i inna sol. Ledger: D:/Projects/docs/ledger/2026-08-25_build-skip-odcisk-wejsc-bkk.md.
Swiadoma KOPIA, nie import: dziennik-wf to osobne repo git, klonowane bez huba — narzedzie
musi dzialac po klonie samo. Poprawka mechanizmu w jednym miejscu nie wchodzi do drugiego
automatycznie; jak mechanizm sie zmieni, obie kopie trzeba ruszyc recznie.

MECHANIZM: wszystkie bramki (32 testy Playwright) zaleza WYLACZNIE od kodu repo — jednego
pliku dziennik_wf.html, tresci testow i srodowiska. Jesli wejscia sa identyczne jak przy
ostatnim ZIELONYM biegu, ponowny bieg jest powtorzeniem i pre-push go pomija. Typowy zysk:
uruchamiasz `sprawdz_wszystko.py` recznie przy pracy, potem pushujesz — push nie powtarza
75 s, ktore wlasnie zaplacilies.

ODCISK = sha256( sol srodowiska
                 | posortowane (sciezka, sha256 TRESCI Z DYSKU) plikow kodu:
                   `git ls-files` + `git ls-files --others --exclude-standard` dla .html/.js/.py
                   i pre-push )
- git sluzy TYLKO do wypisania listy plikow (respektuje .gitignore), hash liczymy z tresci:
  dzieki temu `git add` i `git commit` NIE uniewazniaja odciskiem (ta sama tresc = te same
  wejscia bramek), a kazda realna zmiana tresci uniewaznia. Pierwsza wersja mieszala blob-hashe
  z indeksu z brudna delta i commit tej samej tresci dawal STALE — zmierzone i poprawione 09-21;
- pliki ignorowane (_zrzuty/*.png) sa poza lista, wiec zrzuty z biegu nie robia falszywego STALE;
- sol: wersja pakietu playwright + katalog przegladarki chromium-* + wersja Pythona — update
  srodowiska sam uniewaznia werdykt, bez --clear.

GRANICE (nazwane, nie ukryte):
- Zmiana pliku .md (README, handoffy) NIE uniewaznia odcisku — bramki nie czytaja dokumentacji.
- FAIL nigdy nie jest cache'owany: --record wola sie WYLACZNIE po zielonym calym biegu.
- Odcisk mowi „te same wejscia", nie „ten sam wynik". Test zalezny od zegara albo od stanu
  poza repo (np. plan-wf.json w sasiednim projekcie, ktory czyta test_zalegle.py) moze
  zzieleniec dzis, a zczerwieniec jutro przy tym samym odcisku. Dlatego to zapadka na
  POWTORZENIA, nie zamiennik biegu przy zmianie kodu.
- Stan per-klon w .git/bramki_odcisk.json — znika z klonem, niewersjonowany.

Uzycie (z korzenia repo):
  py -3.14 odcisk.py --check    # exit 0 = SKIP (wejscia jak przy zielonym), exit 1 = biegnij
  py -3.14 odcisk.py --record   # zapisz zielony odcisk
  py -3.14 odcisk.py --status   # werdykt + oba odciski
  py -3.14 odcisk.py --clear    # wyczysc stan
"""

import hashlib
import os
import platform
import subprocess
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Co jest wejsciem bramek: kod aplikacji, kod testow, hook. NIE .md, NIE zrzuty.
WZORCE = ["*.html", "*.js", "*.py", "pre-push"]


def _git(args, root=ROOT):
    """stdout gita jako bytes; None przy bledzie (brak HEAD, brak repo)."""
    try:
        proc = subprocess.run(
            ["git"] + args, cwd=str(root), capture_output=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def cache_path(root=ROOT):
    git_dir = _git(["rev-parse", "--git-dir"], root)
    base = root / git_dir.decode("utf-8", "replace").strip() if git_dir else root
    return base / "bramki_odcisk.json"


def env_salt(root=ROOT):
    """Wersja playwright + katalog przegladarki + wersja Pythona. Wchodzi do kazdego odcisku."""
    parts = []
    try:
        from importlib.metadata import version

        parts.append("playwright " + version("playwright"))
    except Exception:
        parts.append("playwright-unknown")
    # Katalog Chromium zainstalowany przez playwright (nazwa niesie numer builda).
    try:
        base = Path(
            os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
            or (Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ms-playwright")
        )
        chromium = sorted(p.name for p in base.glob("chromium-*") if p.is_dir())
        parts.append("chromium " + (",".join(chromium) if chromium else "?"))
    except OSError:
        parts.append("chromium-unknown")
    parts.append("python " + platform.python_version())
    return "ENV:" + "|".join(parts)


def _sciezki(args, root):
    """Lista sciezek z `git ls-files -z ...`. None = blad gita."""
    out = _git(args + ["-z", "--"] + WZORCE, root)
    if out is None:
        return None
    return [p.decode("utf-8", "replace") for p in out.split(b"\0") if p]


def stan_kodu(root=ROOT):
    """Posortowane 'sciezka sha256-tresci-Z-DYSKU' dla plikow kodu. None = blad gita.

    Liczone z TRESCI drzewa roboczego, nie ze stanu gita — dlatego `git add`/`git commit`
    same w sobie NIE zmieniaja odcisku (treść ta sama = te same wejscia bramek). Pierwsza
    wersja tego pliku mieszala blob-hashe z indeksu z brudna delta i commit tej samej tresci
    dawal STALE, czyli push po biegu-i-commicie powtarzal caly zestaw — zmierzone 2026-09-21.
    """
    sledzone = _sciezki(["ls-files"], root)
    nowe = _sciezki(["ls-files", "--others", "--exclude-standard"], root)
    if sledzone is None or nowe is None:
        return None
    entries = []
    for path in set(sledzone) | set(nowe):
        full = root / path
        digest = (
            hashlib.sha256(full.read_bytes()).hexdigest() if full.is_file() else "DEL"
        )
        entries.append("%s %s" % (path, digest))
    return sorted(entries)


def fingerprint(root=ROOT, salt=None):
    """Odcisk wejsc bramek albo None (git niedostepny -> zawsze biegnij)."""
    kod = stan_kodu(root)
    if kod is None:
        return None
    h = hashlib.sha256()
    h.update((salt if salt is not None else env_salt(root)).encode("utf-8"))
    for linia in kod:
        h.update(b"KOD:" + linia.encode("utf-8"))
    return h.hexdigest()


def load_state(root=ROOT):
    p = cache_path(root)
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def save_state(state, root=ROOT):
    p = cache_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")


def main(argv):
    if len(argv) != 1 or argv[0] not in ("--check", "--record", "--status", "--clear"):
        print(__doc__.split("Uzycie")[1])
        return 2
    cmd = argv[0]

    if cmd == "--clear":
        p = cache_path()
        if p.is_file():
            p.unlink()
        print("stan wyczyszczony: %s" % p)
        return 0

    fp = fingerprint()
    stored = load_state().get("green_fp")

    if cmd == "--status":
        print("zielony odcisk: %s" % (stored or "BRAK"))
        print("biezacy odcisk: %s" % (fp or "NIEDOSTEPNY (git?)"))
        print(
            "werdykt: %s"
            % (
                "SKIP (wejscia identyczne z ostatniego zielonego biegu)"
                if fp is not None and fp == stored
                else "BIEGNIJ"
            )
        )
        return 0

    if cmd == "--check":
        return 0 if (fp is not None and fp == stored) else 1

    if cmd == "--record":
        if fp is None:
            return 0  # nie zgadujemy — cicho nic nie zapisujemy
        save_state({"green_fp": fp})
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
