# Test end-to-end parowania: siatka VULCANa (DOM) -> buildPairs -> match -> symbol w KONKRETNEJ kratce.
#
# Czego pilnuje, czego nie pilnowal zaden inny test: test_vulcan_kopiuj.py sprawdza projekcje
# statusow (parseInput/match/symbolFor) na LISCIE nazwisk podanej wprost, a wiec zaklada, ze pary
# kratka<->uczen sa juz zbudowane poprawnie. Tutaj zaczynamy o szczebel nizej: od DOM-u siatki.
# Blad w buildPairs nie sypie sie glosno — wpisuje WLASCIWY symbol w CUDZA kratke, czyli defekt,
# ktorego w VULCANie nie widac inaczej niz recznym porownaniem nazwisk (a kratka ma tylko znak).
#
# Cztery rzeczy, ktore musza zostac jak sa:
#   A. przy rownej liczbie kratek i nazwisk para idzie PO KOLEJNOSCI WIERSZY, nie po geometrii
#      i nie po kolejnosci wklejonych linii (wklejka celowo w innej kolejnosci niz siatka),
#   B. para imiennikow trafia kazde do swojej kratki (regresja 09-21, 8b: oboje bez wpisu),
#   C. duplikat kratki w DOM (ta sama data-key) nie tworzy drugiej pary i nie przesuwa kolejnosci,
#      a zostaje kopia WIDOCZNA,
#   D. gdy liczby sie nie zgadzaja (kratka bez czytelnego nazwiska) — galaz geometryczna paruje po
#      wysokosci i NIE dokleja kratce przypadkowego sasiada z innego wiersza.
#
# Funkcje wycinam ze skryptu (ten sam kod, co leci do VULCANa), od `symbolFor` do znacznika UI —
# ten kawalek jest czysty: same deklaracje, zero efektow ubocznych przy zaladowaniu.
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
start = src.index("function symbolFor(")
koniec = src.index("// ---------------- UI ----------------")
LOGIKA = src[start:koniec]
for nazwa in ["buildPairs", "editableCells", "nameCells", "match", "parseInput"]:
    assert "function %s(" % nazwa in LOGIKA, nazwa

JS = """([code, html, wklejone]) => {
  document.body.innerHTML = html;
  eval(code);
  var pairs = buildPairs();
  var m = match(pairs, parseInput(wklejone));
  return {
    pary: pairs.map(function(p){ return {
      key: p.cell.getAttribute('data-key'),
      kopia: p.cell.getAttribute('data-kopia') || '',
      name: p.name }; }),
    wiersze: m.rows.map(function(r){ return {
      key: r.pair.cell.getAttribute('data-key'),
      name: r.pair.name,
      status: r.status,
      symbol: r.symbol }; }),
    nieznalezione: m.unmatchedInput
  };
}"""


def siatka(wiersze):
    """wiersze: lista (nazwisko_w_komorce, data-key kratki, atrybuty dodatkowe)."""
    out = ['<table class="v-grid"><tbody>']
    for i, (nazwa, key, extra) in enumerate(wiersze, 1):
        out.append("<tr>")
        out.append('<td class="v-grid-body-cell">%d</td>' % i)
        if nazwa is not None:
            out.append('<td class="v-grid-body-cell">%s</td>' % nazwa)
        if key is not None:
            out.append(
                '<td class="v-grid-body-cell f-editable" data-value-field="Wpis"'
                ' data-key="%s" %s style="min-width:40px;height:22px"></td>'
                % (key, extra)
            )
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    def uruchom(html, wklejone):
        return page.evaluate(JS, [LOGIKA, html, wklejone])

    # ---------- A. rowna liczba -> po kolejnosci wierszy, wklejka w innej kolejnosci ----------
    html_a = siatka(
        [
            ("Abacki Piotr", "wf-101", ""),
            ("Bober Anna", "wf-102", ""),
            ("Cichy Marek", "wf-103", ""),
            ("Dudek Ewa", "wf-104", ""),
        ]
    )
    r = uruchom(
        html_a,
        "Dudek Ewa\tNB\nAbacki Piotr\tC\nCichy Marek\tNC\nBober Anna\tSP",
    )
    check(
        "A: 4 pary w kolejnosci wierszy siatki",
        [p["key"] for p in r["pary"]] == ["wf-101", "wf-102", "wf-103", "wf-104"],
        [p["key"] for p in r["pary"]],
    )
    check(
        "A: nazwisko przypisane do kratki z tego samego wiersza",
        [p["name"] for p in r["pary"]]
        == ["Abacki Piotr", "Bober Anna", "Cichy Marek", "Dudek Ewa"],
        [p["name"] for p in r["pary"]],
    )
    got = {w["key"]: w["symbol"] for w in r["wiersze"]}
    check(
        "A: status z wklejki trafia do kratki wlasciwego ucznia (kolejnosc wklejki bez wplywu)",
        got
        == {
            "wf-101": "obecność",
            "wf-102": "spóźnienie",
            "wf-103": "nie ćwiczy na zajęciach WF",
            "wf-104": "nieobecność",
        },
        got,
    )
    check(
        "A: nic nie zostalo bez dopasowania",
        r["nieznalezione"] == [],
        r["nieznalezione"],
    )

    # ---------- B. para imiennikow (regresja 09-21, klasa 8b) ----------
    html_b = siatka(
        [
            ("Nowak Jan", "wf-201", ""),
            ("Kowalska Zofia", "wf-202", ""),
            ("Nowak Zofia", "wf-203", ""),
        ]
    )
    r = uruchom(html_b, "Nowak Jan\tNS\nNowak Zofia\tNU\nKowalska Zofia\tC")
    got = {w["name"]: (w["status"], w["symbol"]) for w in r["wiersze"]}
    check(
        "B: Nowak Jan -> NS w SWOJEJ kratce",
        got.get("Nowak Jan") == ("NS", "nieob. uspr. szkolne"),
        got.get("Nowak Jan"),
    )
    check(
        "B: Nowak Zofia -> NU w SWOJEJ kratce",
        got.get("Nowak Zofia") == ("NU", "nieob. uspraw."),
        got.get("Nowak Zofia"),
    )
    check(
        "B: imiennicy nie blokuja sie nawzajem (zaden bez wpisu)",
        all(w["symbol"] for w in r["wiersze"]),
        [(w["name"], w["symbol"]) for w in r["wiersze"]],
    )
    keys = {w["name"]: w["key"] for w in r["wiersze"]}
    check(
        "B: kratki imiennikow nie zamienione",
        keys.get("Nowak Jan") == "wf-201" and keys.get("Nowak Zofia") == "wf-203",
        keys,
    )

    # ---------- B2. imiennicy, a VULCAN trzyma DRUGIE IMIE (regresja 09-22, zmierzona na zywej klasie) ----------
    # Ksztalt wziety z realnego przypadku (22.09), nazwiska FIKCYJNE — w repo nie trzymamy
    # danych dzieci. Apka ma "Jan Zawadzki", siatka "Zawadzki Jan Piotr" (drugie imie).
    # Szczebel 2 (rownosc tokenow) tego nie zrownuje, szczebel 3 (samo nazwisko) przy imiennikach
    # slusznie odmawia — panel meldowal "nie znalazlem (2): jan zawadzki, michal zawadzki",
    # czyli DWOJE dzieci po cichu bez wpisu. Domyka to szczebel 2B (zawieranie tokenow).
    html_b2 = siatka(
        [
            ("Zawadzki Jan Piotr", "wf-214", ""),
            ("Zawadzki Michal Karol", "wf-215", ""),
            ("Borecki Krzysztof", "wf-218", ""),
        ]
    )
    r = uruchom(
        html_b2, "Jan Zawadzki\tNS\nMichal Zawadzki\tBS\nKrzysztof Borecki\tNB"
    )
    got = {w["key"]: (w["status"], w["symbol"]) for w in r["wiersze"]}
    check(
        "B2: Zawadzki Jan -> NS (drugie imie w siatce nie blokuje)",
        got.get("wf-214") == ("NS", "nieob. uspr. szkolne"),
        got.get("wf-214"),
    )
    check(
        "B2: Zawadzki Michal -> BS w SWOJEJ kratce, nie w kratce brata",
        got.get("wf-215") == ("BS", "nie ćwiczy na zajęciach WF"),
        got.get("wf-215"),
    )
    check(
        "B2: nikt nie wypada z dopasowania",
        r["nieznalezione"] == [],
        r["nieznalezione"],
    )
    # Granica szczebla 2B: samo nazwisko pasuje do OBU braci — wtedy ma NIE zgadywac.
    r = uruchom(html_b2, "Zawadzki\tNS\nKrzysztof Borecki\tNB")
    got = {w["key"]: w["symbol"] for w in r["wiersze"]}
    check(
        "B2: wpis pasujacy do obu imiennikow nie trafia do zadnego",
        got.get("wf-214") is None and got.get("wf-215") is None,
        got,
    )
    check(
        "B2: niejednoznaczny wpis zgloszony w 'nie znalazlem'",
        r["nieznalezione"] == ["zawadzki"],
        r["nieznalezione"],
    )

    # ---------- C. duplikat kratki w DOM: ta sama data-key, kopia ukryta ----------
    # VULCAN trzyma bufor wierszy — ta sama kratka potrafi byc w DOM dwa razy. Dedup ma zostawic
    # kopie WIDOCZNA (w ukryta klikniecie nie trafi) i nie ruszyc kolejnosci pozostalych.
    wiersze_c = [
        ("Abacki Piotr", "wf-301", 'data-kopia="widoczna"'),
        ("Bober Anna", "wf-302", 'data-kopia="widoczna"'),
        ("Cichy Marek", "wf-303", 'data-kopia="widoczna"'),
    ]
    html_c = siatka(wiersze_c)
    # doklejam ukryty duplikat wiersza Bober (ten sam data-key) PRZED reszta, jak bufor ExtJS
    dup = (
        '<table class="v-grid" style="display:none"><tbody><tr>'
        '<td class="v-grid-body-cell">2</td>'
        '<td class="v-grid-body-cell">Bober Anna</td>'
        '<td class="v-grid-body-cell f-editable" data-value-field="Wpis" data-key="wf-302"'
        ' data-kopia="ukryta"></td></tr></tbody></table>'
    )
    r = uruchom(dup + html_c, "Abacki Piotr\tC\nBober Anna\tNB\nCichy Marek\tC")
    check(
        "C: duplikat DOM nie tworzy drugiej pary",
        len(r["pary"]) == 3,
        [(p["key"], p["kopia"]) for p in r["pary"]],
    )
    check(
        "C: zostala kopia WIDOCZNA",
        all(p["kopia"] == "widoczna" for p in r["pary"]),
        [(p["key"], p["kopia"]) for p in r["pary"]],
    )
    check(
        "C: kolejnosc kratek nietknieta przez dedup",
        [p["key"] for p in r["pary"]] == ["wf-302", "wf-301", "wf-303"],
        [p["key"] for p in r["pary"]],
    )
    got = {w["name"]: w["symbol"] for w in r["wiersze"]}
    check(
        "C: statusy mimo duplikatu trafiaja po nazwisku",
        got
        == {
            "Abacki Piotr": "obecność",
            "Bober Anna": "nieobecność",
            "Cichy Marek": "obecność",
        },
        got,
    )

    # ---------- D. nierowna liczba -> galaz geometryczna ----------
    # Uczen, ktorego komorka nazwiska jest nieczytelna dla nameCells (jeden wyraz) — kratek 3,
    # nazwisk 2. Parowanie po wysokosci: dwie pary, a kratka bez nazwiska NIE dostaje sasiada.
    html_d = siatka(
        [
            ("Abacki Piotr", "wf-401", ""),
            ("Bober", "wf-402", ""),  # jeden wyraz -> nameCells to odrzuca
            ("Cichy Marek", "wf-403", ""),
        ]
    )
    r = uruchom(html_d, "Abacki Piotr\tC\nCichy Marek\tNB")
    check(
        "D: geometria paruje tylko kratki majace nazwisko w swoim wierszu",
        [(p["key"], p["name"]) for p in r["pary"]]
        == [("wf-401", "Abacki Piotr"), ("wf-403", "Cichy Marek")],
        [(p["key"], p["name"]) for p in r["pary"]],
    )
    got = {w["key"]: w["symbol"] for w in r["wiersze"]}
    check(
        "D: statusy trafiaja bez przesuniecia o wiersz",
        got == {"wf-401": "obecność", "wf-403": "nieobecność"},
        got,
    )

    # ---------- E. wpis dla ucznia spoza kolumny zglaszany, nie wpychany na sile ----------
    r = uruchom(html_a, "Abacki Piotr\tC\nZajac Igor\tNB")
    check(
        "E: nieobecny w siatce ladnie w 'nie znalazlem', nie w cudzej kratce",
        r["nieznalezione"] == ["zajac igor"],
        r["nieznalezione"],
    )
    check(
        "E: reszta kratek zostaje pusta (brak danych != zgadywanie)",
        [w["symbol"] for w in r["wiersze"]] == ["obecność", None, None, None],
        [(w["name"], w["symbol"]) for w in r["wiersze"]],
    )

    check("brak bledow JS na stronie", not errors, errors)
    browser.close()

# ---------- kontrola, ze galaz "po kolejnosci" nadal jest w kodzie ----------
check(
    "kod: galaz rownej liczby kratek i nazwisk istnieje",
    "eds.length===ncs.length" in src,
)
check(
    "kod: dedup po data-key zachowuje kolejnosc (tablica order)",
    "order.map(" in src and "data-key" in src,
)

print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
