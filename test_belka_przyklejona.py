# Bramka (2026-09-20): w Obecnosci maja ZOSTAC na ekranie DWIE belki —
#   1) belka dnia (data, numer lekcji, ◀ dzis ▶),
#   2) naglowek tabeli (UCZEN, STATUS DZIS, CWICZYL, ...), przyklejony tuz pod nia.
# Powod: przy 23 uczniach obie uciekaly w gore i przy wpisywaniu statusow bylo widac
# liste nazwisk bez nazw kolumn i bez daty.
#
# Naglowek tabeli klei sie tylko powyzej 1100 px: ponizej tego progu tabela ma wlasne
# okno przewijania (regula z 19.09), a element z wlasnym przewijaniem nie pozwala
# naglowkowi kleic sie do okna przegladarki. Dlatego na waskim ekranie test pilnuje
# wylacznie belki dnia. (Obnizenie progu do 820 px probowano 2026-09-20 — user nie
# zobaczyl roznicy u siebie, zmiane wycofano.)
#
#     py -3.14 test_belka_przyklejona.py [plik.html]
import sys

from playwright.sync_api import sync_playwright

from fixture_stan import otworz, serwer, zasiej

PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
FAILS = []

# (nazwa, szerokosc, wysokosc, czy naglowek ma byc przyklejony)
EKRANY = [
    ("laptop", 1366, 768, True),
    ("telefon", 390, 780, False),  # wlasne okno przewijania — naglowek stoi w miejscu
]

POMIAR = """() => {
  const dr = document.querySelector('#tab-obecnosc .date-row.dzien-row');
  const th = document.querySelector('#tab-obecnosc table.attendance thead th');
  const tb = document.querySelector('.topbar');
  const r = dr.getBoundingClientRect();
  return {
    gora: Math.round(r.top), dol: Math.round(r.bottom),
    topbar: Math.round(tb.getBoundingClientRect().bottom),
    thead: th ? Math.round(th.getBoundingClientRect().top) : null,
    scrollY: Math.round(window.scrollY),
  };
}"""


def check(nazwa, ok, detal=""):
    print(
        "[%s] %s %s"
        % ("PASS" if ok else "FAIL", nazwa, ("- " + str(detal)) if detal else "")
    )
    if not ok:
        FAILS.append(nazwa)


with serwer(8793) as port, sync_playwright() as pw:
    for tag, w, h, naglowek_klei in EKRANY:
        b, ctx, page, errors = otworz(
            pw, port, viewport={"width": w, "height": h}, plik=PLIK
        )
        zasiej(page)
        page.wait_for_timeout(500)
        # kursor nad tabela: gdyby tabela miala wlasne okno przewijania, kolko
        # przewijaloby JEGO — dokladnie w tym ukladzie naglowek znikal
        page.mouse.move(w // 2, h // 2)
        page.mouse.wheel(0, 1400)
        page.wait_for_timeout(400)
        p = page.evaluate(POMIAR)
        check("%s: strona faktycznie zjechala" % tag, p["scrollY"] > 300, p["scrollY"])
        check(
            "%s: belka dnia tuz pod paskiem gornym" % tag,
            abs(p["gora"] - p["topbar"]) <= 2,
            (p["gora"], p["topbar"]),
        )
        if naglowek_klei:
            check(
                "%s: naglowek tabeli przyklejony pod belka dnia" % tag,
                abs(p["thead"] - p["dol"]) <= 2,
                (p["thead"], p["dol"]),
            )
        page.mouse.wheel(0, -3000)
        page.wait_for_timeout(400)
        g = page.evaluate(POMIAR)
        check("%s: powrot na gore nie gubi belki" % tag, g["gora"] >= 0, g["gora"])
        check("%s: bez bledow JS" % tag, not errors, errors[:3])
        b.close()

print("\n%s — %d bledow" % ("FAIL" if FAILS else "PASS", len(FAILS)))
sys.exit(1 if FAILS else 0)
