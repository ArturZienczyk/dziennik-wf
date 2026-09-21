# Bramka odcisku wejsc (2026-09-21). Odcisk decyduje, czy pre-push POMIJA wszystkie bramki —
# falszywy SKIP przepuszcza zepsuty kod na GitHuba, wiec sam odcisk potrzebuje bramki.
# Wzorzec i mechanizm: odcisk.py (kopia z D:/Projects/karty/scripts/build_odcisk.py).
#
# Sprawdzane (kazdy przypadek na KOPII repo w tmp, zeby nie ruszac zywego drzewa):
#   1. stabilnosc: dwa odczyty pod rzad = ten sam odcisk,
#   2. edycja pliku kodu (niezacommitowana) -> STALE,
#   3. powrot do poprzedniej tresci -> znowu SKIP (odcisk jest o TRESCI, nie o fakcie dotkniecia),
#   4. commit tej samej zmiany -> nadal STALE wzgledem starego odcisku,
#   5. nowy plik .py nieśledzony -> STALE (inaczej nowy test wjechalby bez biegu),
#   6. zmiana .md -> SKIP (bramki nie czytaja dokumentacji),
#   7. nowy plik ignorowany (_zrzuty/*.png) -> SKIP (zrzuty z biegu nie moga robic STALE),
#   8. inna sol srodowiska -> STALE (update playwrighta uniewaznia werdykt),
#   9. --record zapisuje, --clear kasuje, --check zwraca 0/1 zgodnie z werdyktem.
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ZRODLO = Path(__file__).resolve().parent
FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


def git(repo, *args):
    return subprocess.run(
        ["git"] + list(args), cwd=str(repo), capture_output=True, text=True
    )


def zrob_repo(tmp):
    """Male repo git z ta sama struktura co dziennik: kod + .md + .gitignore na _zrzuty/."""
    repo = Path(tmp) / "repo"
    repo.mkdir()
    shutil.copy(ZRODLO / "odcisk.py", repo / "odcisk.py")
    (repo / "dziennik_wf.html").write_text("<h1>kod</h1>", encoding="utf-8")
    (repo / "test_cos.py").write_text("print('test')", encoding="utf-8")
    (repo / "README.md").write_text("dokumentacja", encoding="utf-8")
    (repo / ".gitignore").write_text("_zrzuty/\n", encoding="utf-8")
    (repo / "_zrzuty").mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@test")
    git(repo, "config", "user.name", "test")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "start")
    return repo


def odcisk(repo, *args):
    """Uruchamia odcisk.py W KOPII repo (ROOT liczy sie od polozenia pliku)."""
    return subprocess.run(
        [sys.executable, "odcisk.py"] + list(args),
        cwd=str(repo),
        capture_output=True,
        text=True,
    )


def fp(repo, salt="SOL-TESTOWA"):
    """Odcisk liczony w procesie repo, ze stala sola (sol srodowiska ma wlasny przypadek)."""
    kod = subprocess.run(
        [
            sys.executable,
            "-c",
            "import odcisk, sys; print(odcisk.fingerprint(salt=%r) or 'NONE')" % salt,
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    return kod.stdout.strip()


with tempfile.TemporaryDirectory() as tmp:
    repo = zrob_repo(tmp)

    a = fp(repo)
    check("odcisk w ogole sie liczy", len(a) == 64, a)
    check("stabilnosc: dwa odczyty = ten sam odcisk", a == fp(repo))

    # 2 + 3: tresc, nie fakt dotkniecia
    html = repo / "dziennik_wf.html"
    oryginal = html.read_text(encoding="utf-8")
    html.write_text("<h1>zmiana</h1>", encoding="utf-8")
    check("edycja pliku kodu -> STALE", fp(repo) != a)
    html.write_text(oryginal, encoding="utf-8")
    check("powrot do tej samej tresci -> znowu ten sam odcisk", fp(repo) == a)

    # 4: commit tej samej zmiany tez jest zmiana wejsc
    html.write_text("<h1>zmiana</h1>", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "zmiana")
    check("commit zmiany kodu -> STALE", fp(repo) != a)
    b = fp(repo)

    # 5: nowy test nieśledzony musi uniewaznic (inaczej wjechalby bez ani jednego biegu)
    (repo / "test_nowy.py").write_text("print('nowy')", encoding="utf-8")
    check("nowy plik .py nieśledzony -> STALE", fp(repo) != b)
    (repo / "test_nowy.py").unlink()
    check("po usunieciu nowego pliku -> odcisk wraca", fp(repo) == b)

    # 6: dokumentacja nie jest wejsciem bramek
    (repo / "README.md").write_text("inna dokumentacja", encoding="utf-8")
    check("zmiana .md -> SKIP (odcisk bez zmian)", fp(repo) == b)
    (repo / "NOWY-HANDOFF.md").write_text("notatka", encoding="utf-8")
    check("nowy plik .md -> SKIP (odcisk bez zmian)", fp(repo) == b)

    # 7: zrzuty z biegu testow sa ignorowane przez git i nie moga robic falszywego STALE
    (repo / "_zrzuty" / "shot.png").write_bytes(b"\x89PNG fake")
    check("nowy zrzut w ignorowanym _zrzuty/ -> SKIP (odcisk bez zmian)", fp(repo) == b)

    # 8: sol srodowiska
    check("inna sol (update playwrighta) -> STALE", fp(repo, salt="INNA-SOL") != b)

    # 9: CLI --record / --check / --clear
    odcisk(repo, "--clear")
    check(
        "po --clear: --check mowi BIEGNIJ (exit 1)",
        odcisk(repo, "--check").returncode == 1,
    )
    odcisk(repo, "--record")
    check(
        "po --record: --check mowi SKIP (exit 0)",
        odcisk(repo, "--check").returncode == 0,
    )
    html.write_text("<h1>jeszcze inna</h1>", encoding="utf-8")
    check(
        "po zmianie kodu: --check znowu BIEGNIJ (exit 1)",
        odcisk(repo, "--check").returncode == 1,
    )
    st = odcisk(repo, "--status").stdout
    check(
        "--status nazywa werdykt po ludzku",
        "BIEGNIJ" in st,
        st.strip().splitlines()[-1:],
    )

if FAILS:
    print("\nWYNIK: FAIL - %d: %s" % (len(FAILS), FAILS))
    sys.exit(1)
print(
    "\nWYNIK: PASS - odcisk lapie kazda zmiane wejsc i nie lapie dokumentacji ani zrzutow."
)
