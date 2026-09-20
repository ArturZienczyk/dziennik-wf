# Obchód aplikacji w stanie PEŁNYM — klika po wszystkich zakładkach i sprawdza,
# czy coś się psuje. Uzupełnia audyt heurystyczny (test_audyt_ux.py), który
# ocenia POJEDYNCZY ekran; tu chodzi o przejście przez całość z realnymi danymi.
#
# Dlaczego stan pełny: audyt 19.09 dał 4 findingi, z których 2 były nad-raportem
# ze stanu pustego (krytyk widział dziennik bez uczniów). Fixture kasuje tę klasę
# fałszywych alarmów u źródła — nie przez lepszą ocenę, tylko przez właściwy stan.
#
# Co ten test ORZEKA (deterministycznie, bez oceniania wyglądu):
#   1. zero błędów JS i console.error na każdej zakładce,
#   2. brak poziomego scrolla dokumentu (layout nie wylewa się w bok),
#   3. tabela zakładki ma wiersze — czyli dane faktycznie dojechały do renderu,
#   4. nagłówek tabeli trzyma się po przewinięciu (realny bug z README:
#      "przy 20+ uczniach po przewinięciu znikał wiersz z opisami kolumn"),
#   5. żaden element nie wystaje poza prawą krawędź viewportu.
# Czego NIE orzeka: czy to ładne. Zrzuty idą do _zrzuty/obchod_*.png — klika user.

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from fixture_stan import otworz, serwer, sprawdz_zasiane, zasiej

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "_zrzuty"
SHOTS.mkdir(exist_ok=True)
PORT = 8781

# zakładka -> tabela, która MUSI mieć wiersze w stanie pełnym.
# plan/reguly nie mają tabeli danych — sprawdzamy je tylko na błędy i layout.
ZAKLADKI = [
    ("obecnosc", "#attendanceBody"),
    ("uczniowie", "#studentsBody"),
    ("pomiary", "#pomiaryBody"),
    ("oceny", "#ocenyBody"),
    ("statystyki", "#statsBody"),
    ("plan", None),
    ("reguly", None),
]

# Przyciski zakladek celujemy w onclick, nie w etykiete: etykiety maja emoji
# i polskie znaki, a onclick jest stabilnym kontraktem nawigacji.
TAB_BTN = "button.tab[onclick=\"switchTab('%s')\"]"

FAILS = []


def check(nazwa, warunek, detal=""):
    if not warunek:
        FAILS.append("%s :: %s" % (nazwa, detal))


def bez_bledow(errors, gdzie):
    """Błędy zebrane od ostatniego sprawdzenia. Lista jest żywa — czyścimy ją,
    żeby jeden błąd nie obciążał każdej kolejnej zakładki."""
    if errors:
        FAILS.append("%s :: blad JS: %s" % (gdzie, " | ".join(errors[:3])))
        errors.clear()


with serwer(PORT) as port, sync_playwright() as pw:
    browser, ctx, page, errors = otworz(pw, port)

    opis = zasiej(page)
    print(
        "Zasiano: %(uczniow)d uczniow, %(lekcji)d lekcji (%(od)s..%(do)s), "
        "%(wpisow)d wpisow frekwencji, klasa %(klasa)s" % opis
    )

    # Bramka fixture: apka ma dane NAPRAWDĘ, nie tylko je dostała.
    # Bez tego cały obchód mógłby przejść po pustej apce i zameldować sukces.
    stan = sprawdz_zasiane(page)
    check("fixture: apka widzi zasiany stan", stan.get("ok"), stan)
    if not stan.get("ok"):
        print("STOP: fixture nie zasiał stanu — obchod bez danych nic nie znaczy.")
        print("  " + str(stan))
        browser.close()
        sys.exit(1)
    bez_bledow(errors, "po zasianiu")

    for tab, tabela in ZAKLADKI:
        # KLIK w zakladke, nie switchTab() z konsoli: funkcja czyta globalny
        # `event.target`, wiec wywolana programowo wywala sie na undefined.
        # Obchod ma zreszta klikac dokladnie tak jak user, nie omijac UI.
        page.click(TAB_BTN % tab)
        page.wait_for_timeout(350)
        gdzie = "zakladka " + tab

        bez_bledow(errors, gdzie)

        # 3. dane dojechały do renderu
        if tabela:
            wierszy = page.locator(tabela + " tr").count()
            check("%s: tabela ma wiersze" % gdzie, wierszy > 0, "wierszy=%d" % wierszy)

        # 2. layout nie wylewa się w bok
        szer = page.evaluate(
            "() => ({ doc: document.documentElement.scrollWidth,"
            " win: document.documentElement.clientWidth })"
        )
        check(
            "%s: brak poziomego scrolla dokumentu" % gdzie,
            szer["doc"] <= szer["win"] + 2,
            szer,
        )

        # 5. nic nie wystaje poza prawą krawędź (łapie pojedynczy zbyt szeroki
        #    element nawet wtedy, gdy kontener go przycina i scroll się nie pojawia)
        wystajace = page.evaluate(
            """(win) => {
            const out = [];
            document.querySelectorAll('.tab-content.active *').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width > 0 && r.right > win + 2) {
                    out.push((el.id || el.className || el.tagName) + ' right=' + Math.round(r.right));
                }
            });
            return out.slice(0, 3);
        }""",
            szer["win"],
        )
        check("%s: nic nie wystaje poza viewport" % gdzie, not wystajace, wystajace)

        page.screenshot(path=str(SHOTS / ("obchod_%s.png" % tab)), full_page=False)

    # 4. nagłówek tabeli po przewinięciu — bug z README wracał już raz.
    #    Sprawdzamy na Uczniach, bo tam lista jest najdłuższa (23 wiersze).
    page.click(TAB_BTN % "uczniowie")
    page.wait_for_timeout(300)
    naglowek_przed = page.locator("#tab-uczniowie thead tr").first.is_visible()
    page.evaluate(
        "() => { const w = document.querySelector('#tab-uczniowie .table-wrap');"
        " if (w) w.scrollTop = w.scrollHeight; }"
    )
    page.wait_for_timeout(300)
    naglowek_po = page.locator("#tab-uczniowie thead tr").first.is_visible()
    check(
        "uczniowie: naglowek kolumn widoczny po przewinieciu do konca",
        naglowek_przed and naglowek_po,
        "przed=%s po=%s" % (naglowek_przed, naglowek_po),
    )
    page.screenshot(path=str(SHOTS / "obchod_uczniowie_przewiniete.png"))
    bez_bledow(errors, "przewijanie uczniow")

    # Obchód klikania: karta ucznia to osobna ścieżka renderu (kartaBody),
    # łatwa do zepsucia, bo pokazuje dane ze wszystkich zakładek naraz.
    page.click(TAB_BTN % "uczniowie")
    page.wait_for_timeout(200)
    otwarto_karte = page.evaluate("""() => {
        if (typeof openKarta !== 'function') return null;
        const s = state.students.find(x => x.name);
        if (!s) return null;
        openKarta(s.id);
        return s.name;
    }""")
    if otwarto_karte:
        page.wait_for_timeout(400)
        tresc = page.locator("#kartaBody").inner_text()
        check(
            "karta ucznia: ma tresc dla %s" % otwarto_karte,
            len(tresc.strip()) > 40,
            "dlugosc=%d" % len(tresc.strip()),
        )
        page.screenshot(path=str(SHOTS / "obchod_karta_ucznia.png"))
        bez_bledow(errors, "karta ucznia")
    else:
        print("UWAGA: openKarta niedostepna — karta ucznia pominieta w obchodzie.")

    browser.close()

print()
if FAILS:
    print("FAIL (%d):" % len(FAILS))
    for f in FAILS:
        print("  - " + f)
    print("\nZrzuty: %s\\obchod_*.png" % SHOTS)
    sys.exit(1)

print("PASS — obchod przeszedl przez %d zakladek w stanie pelnym." % len(ZAKLADKI))
print("Zrzuty do obejrzenia (klik = Twoje oko): %s\\obchod_*.png" % SHOTS)
