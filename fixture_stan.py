# Fixture stanu dziennika — doprowadza apkę do stanu PEŁNEGO przed zrzutem/obchodem.
#
# Po co: audyt UX na pustej apce nad-raportuje (19.09: 4 findingi, 2 fałszywe —
# krytyk widział ekran bez uczniów). Pusty dziennik to stan, w którym user bywa
# przez pierwsze 5 minut życia klasy; przez resztę roku jest pełny. Zrzut ma
# pokazywać ten drugi.
#
# Dane są DETERMINISTYCZNE (Random(SEED)) — ten sam stan przy każdym uruchomieniu,
# inaczej zrzuty migoczą i nie da się porównać dwóch przebiegów.
#
# Użycie:
#     from fixture_stan import serwer, otworz, zasiej
#     with serwer(8781) as port, sync_playwright() as pw:
#         browser, ctx, page, errors = otworz(pw, port)
#         opis = zasiej(page)
#
# NIE dotyka localStorage wprost — seeduje przez to samo API, którego używa UI
# (makeClass/activateClass/save/refreshAll), więc szyfrowanie zamka działa jak
# w produkcji i test nie rozjedzie się z apką przy zmianie formatu zapisu.

import contextlib
import functools
import http.server
import random
import socketserver
import threading
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 42
HASLO = "test-haslo-123"

# 23 uczniów — tyle liczy realna klasa usera (VULCAN-INTEGRACJA-USTALENIA.md:
# "23 realnych, 46 to fantomy DOM"). Nazwiska bez ogonków: to dane testowe,
# a polskie znaki w nazwiskach mają własny test (dopasowanie VULCAN).
NAZWISKA = [
    "Adamczyk Hanna",
    "Baran Filip",
    "Chmiel Zofia",
    "Dabrowski Igor",
    "Front Maja",
    "Galka Szymon",
    "Hajduk Lena",
    "Iwanska Nikola",
    "Jarosz Kacper",
    "Kowalski Jan",
    "Lis Amelia",
    "Mazur Oliwier",
    "Nowak Piotr",
    "Olszewska Julia",
    "Pawlak Antoni",
    "Rutkowski Franciszek",
    "Sikora Pola",
    "Tomczyk Marcel",
    "Urbaniak Alicja",
    "Wisniewski Adam",
    "Zajac Wiktor",
    "Zielinski Marek",
    "Zurek Natalia",
]

# Rozkład statusów — realistyczny, nie równomierny: dominuje C, wyjątków mało.
# (Tak wygląda frekwencja WF i tak wygląda gest usera w VULCAN: "zaznacz tylko
# nieobecnych, reszta dostaje obecność automatycznie".)
ROZKLAD = ["C"] * 80 + ["NC"] * 4 + ["BS"] * 6 + ["NB"] * 2 + ["NU"] * 5 + ["ZW"] * 3


@contextlib.contextmanager
def serwer(port=8781):
    """Lokalny serwer plików na czas testu. Apka musi iść przez http://,
    nie file:// — service workery i IndexedDB inaczej nie wstaną."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(ROOT)
    )
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield port
    finally:
        httpd.shutdown()
        httpd.server_close()


def otworz(pw, port, viewport=None, plik="dziennik_wf.html"):
    """Czysta przeglądarka + odblokowany zamek. Zwraca (browser, ctx, page, errors).
    `errors` to żywa lista — rośnie sama przy każdym błędzie JS i console.error.
    `plik` pozwala obejrzeć wersję roboczą/piaskownicę tym samym fixture'm."""
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        service_workers="block",
        viewport=viewport or {"width": 1500, "height": 1000},
    )
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    page.on(
        "console",
        lambda m: errors.append("console.error: " + m.text)
        if m.type == "error"
        else None,
    )
    page.goto("http://127.0.0.1:%d/%s" % (port, plik))
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('%s')" % HASLO)
    page.wait_for_timeout(200)
    return browser, ctx, page, errors


def _dni_robocze(ile, do_dnia=None):
    """Ostatnie `ile` dni roboczych wstecz — frekwencji nie ma w weekend."""
    d = do_dnia or date.today()
    out = []
    while len(out) < ile:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return list(reversed(out))


def _plan_frekwencji(uczniowie, dni, lekcje, rng):
    """Buduje {'YYYY-MM-DD#nr': {idUcznia: 'C' | {'s':..,'sp':True}}}.

    Jeden uczeń (indeks 7) dostaje serię NU — żeby statystyki miały kogoś
    z realnie niską frekwencją, a nie 23 osoby z tym samym słupkiem.
    """
    att = {}
    for dzien in dni:
        for nr in lekcje:
            klucz = "%s#%d" % (dzien, nr)
            wpisy = {}
            for i, uid in enumerate(uczniowie):
                if i == 7 and rng.random() < 0.6:
                    status = "NU"
                else:
                    status = rng.choice(ROZKLAD)
                # spóźnienie doklejane do obecności, jak w apce (attWrite(status, sp))
                if status == "C" and rng.random() < 0.04:
                    wpisy[uid] = {"s": "C", "sp": True}
                else:
                    wpisy[uid] = status
            att[klucz] = wpisy
    return att


def zasiej(page, uczniow=23, dni=10, lekcje=(2, 4), szkola="ZSS Wodna", klasa="6A"):
    """Wypełnia dziennik realistyczną klasą. Zwraca opis zasianego stanu."""
    rng = random.Random(SEED)
    imiona = NAZWISKA[:uczniow]
    ids = ["u%d" % (i + 1) for i in range(uczniow)]
    daty = _dni_robocze(dni)
    att = _plan_frekwencji(ids, daty, list(lekcje), rng)

    uczniowie = []
    for i, (uid, name) in enumerate(zip(ids, imiona)):
        uczniowie.append(
            {
                "id": uid,
                "name": name,
                # jeden zwolniony długoterminowo — osobna ścieżka renderu, łatwa do przeoczenia
                "longTermReleased": (i == 11),
                "height": str(rng.randint(138, 172)),
                "weight": str(rng.randint(32, 64)),
            }
        )

    dane = {
        "szkola": szkola,
        "klasa": klasa,
        "uczniowie": uczniowie,
        "attendance": att,
        "oceny": [
            {"id": "gc_fix_1", "name": "Skok w dal"},
            {"id": "gc_fix_2", "name": "Bieg 60 m"},
        ],
        "stopnie": {
            "gc_fix_1": {
                uid: str(rng.randint(2, 6)) for uid in ids if rng.random() < 0.85
            },
            "gc_fix_2": {
                uid: str(rng.randint(2, 6)) for uid in ids if rng.random() < 0.7
            },
        },
        "pomiary": {uid: rng.randint(0, 3) for uid in ids},
    }

    page.evaluate(
        """async (d) => {
        // 1. klasa przez API apki — nie przez ręczny zapis do localStorage
        const st = d.uczniowie.map(u => Object.assign({}, u));
        const c = makeClass(d.szkola, d.klasa, st);
        c.attendance = d.attendance;
        c.gradeColumns = d.oceny.map(o => ({ id: o.id, name: o.name }));
        c.grades = d.stopnie;
        state.classes.length = 0;
        state.classes.push(c);
        activateClass(c.id);

        // 2. pomiary sprawności — tyle pól, ile klasa faktycznie ma zdefiniowanych
        const pola = (typeof getTestFields === 'function') ? getTestFields() : [];
        state.measurements = state.measurements || {};
        Object.keys(d.pomiary).forEach(uid => {
            const ile = d.pomiary[uid];
            if (!ile) return;
            const m = {};
            pola.slice(0, ile).forEach((f, i) => { m[f.id] = String(10 + i * 3); });
            state.measurements[uid] = m;
        });
        const cls = getCurrentClass();
        if (cls) cls.measurements = state.measurements;

        // 3. data bieżąca = ostatni zasiany dzień, żeby widok nie otwierał się pusty
        const klucze = Object.keys(d.attendance).sort();
        if (klucze.length) {
            const ost = klucze[klucze.length - 1];
            state.currentDate = kluczData(ost);
            state.currentNr = kluczNr(ost);
        }
        // save(true) = zapis natychmiastowy i czekamy na niego; bez tego bramka
        // sprawdza magazyn, zanim szyfrogram tam trafi.
        await save(true);
        if (typeof refreshAll === 'function') refreshAll();
    }""",
        dane,
    )
    page.wait_for_timeout(500)

    return {
        "uczniow": uczniow,
        "dni": len(daty),
        "lekcji": len(att),
        "wpisow": sum(len(v) for v in att.values()),
        "od": daty[0],
        "do": daty[-1],
        "klasa": "%s / %s" % (szkola, klasa),
    }


def sprawdz_zasiane(page):
    """Bramka samego fixture: czy apka NAPRAWDĘ ma dane, czy tylko je dostała.
    Bez tego obchód mógłby jechać po pustej apce i meldować sukces."""
    # zamekStanZapisany() jest async — bez await dostajemy Promise, a z niego
    # `undefined` zamiast klasy (pierwszy przebieg 20.09 wywrócił się właśnie tu).
    return page.evaluate("""async () => {
        const s = (typeof zamekStanZapisany === 'function') ? await zamekStanZapisany() : null;
        const c = s && s.classes && s.classes[0];
        if (!c) return { ok: false, powod: 'brak klasy w zapisanym stanie' };
        const uczniow = (c.students || []).filter(u => u.name).length;
        const lekcji = Object.keys(c.attendance || {}).length;
        const widoczne = document.querySelectorAll('#attendanceBody tr').length;
        return {
            ok: uczniow > 0 && lekcji > 0 && widoczne > 0,
            uczniow: uczniow,
            lekcji: lekcji,
            wierszyWidocznych: widoczne,
        };
    }""")
