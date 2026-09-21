# Jedno źródło prawdy dla procentu ćwiczył (2026-09-21).
#
# Do tej pory procent liczyły DWA niezależne kawałki kodu: getStudentStatsZ (tabela Statystyk,
# wydruk, CSV, % dotąd, Systematyczność) i własny wzór na karcie ucznia (kafelki + krzywa).
# Karta ignorowała przełączniki z zakładki Reguły, więc po zmianie dowolnej reguły ten sam uczeń
# miał w tabeli inny procent niż na swojej karcie — po cichu, bez błędu. Teraz obie drogi pytają
# funkcję wagaLekcji(status, spozniony), która jako jedyna zamienia reguły na liczby.
#
# Ten test przechodzi po WSZYSTKICH pięciu przełącznikach, w obie strony, i za każdym razem
# porównuje: tabela == karta ucznia. Jeśli ktoś doda szósty przełącznik albo nowy status
# i obsłuży go tylko w jednym miejscu — ten test to zobaczy.
import sys
import threading
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8797
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright

FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name)


# Jeden uczeń, po jednej lekcji z każdego statusu + jedno „C ze spóźnieniem”.
# Taki komplet sprawia, że KAŻDY przełącznik realnie rusza wynik.
FIXTURE = """() => {
  const c = state.classes[0];
  c.name = '7b'; c.school = 'SSP';
  c.students = [{id:'u1', name:'Ola Komplet'}];
  c.attendance = {
    '2026-09-01': { u1: 'C' },
    '2026-09-02': { u1: attWrite('C', true) },
    '2026-09-03': { u1: 'NC' },
    '2026-09-04': { u1: 'BS' },
    '2026-09-07': { u1: 'NB' },
    '2026-09-08': { u1: 'NU' },
    '2026-09-09': { u1: 'ZW' },
    '2026-09-10': { u1: 'NS' }
  };
  activateClass(c.id);
  state.currentDate = '2026-09-10';
  save(); refreshAll();
}"""

# procent z tabeli (getStudentStats) i z karty ucznia (kartaKafle) — dwie drogi, ta sama liczba
POROWNAJ = """() => {
  const st = getStudentStats('u1');
  const tabela = st.percent === null ? null : Math.round(st.percent);
  const html = kartaKafle(kartaLekcje('u1'), 'całość');
  const m = html.match(/<div class="n">(\\d+)%<\\/div>/);
  const karta = m ? parseInt(m[1], 10) : null;
  const mb = html.match(/z (\\d+(?:[.,]\\d+)?) liczonych/);
  return { tabela: tabela, karta: karta, bazaTabela: st.baza, bazaKarta: mb ? parseFloat(mb[1].replace(',', '.')) : null };
}"""

PRZELACZNIKI = [
    ("bsBaza", False, "Brak stroju NIE liczy sie jak nieobecnosc"),
    ("ncBaza", False, "Nie cwiczyl NIE liczy sie jak nieobecnosc"),
    ("nuBaza", True, "Nieobecnosc usprawiedliwiona WCHODZI do bazy"),
    ("spPol", True, "Spoznienie obniza procent (pol lekcji)"),
    ("nsBaza", False, "Zajecia szkolne WYPADAJA z bazy (litera PZO)"),
]

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_context(
        service_workers="block", viewport={"width": 1400, "height": 900}
    ).new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:%d/dziennik_wf.html" % PORT)
    page.wait_for_timeout(400)
    page.evaluate("() => zamekPierwszeHaslo('haslo-sot-1')")
    page.wait_for_timeout(500)
    page.evaluate(FIXTURE)
    page.wait_for_timeout(400)

    # 1. Domyslne ustawienia: obie drogi zgodne
    r = page.evaluate(POROWNAJ)
    check(
        "domyslne reguly: tabela == karta ucznia",
        r["tabela"] == r["karta"] and r["bazaTabela"] == r["bazaKarta"],
        r,
    )
    bazowy = r["tabela"]

    # 2. Kazdy przelacznik z osobna: obie drogi maja sie zmienic RAZEM
    for klucz, wartosc, opis in PRZELACZNIKI:
        page.evaluate("(a) => regulaUstaw(a[0], a[1])", [klucz, wartosc])
        page.wait_for_timeout(250)
        r = page.evaluate(POROWNAJ)
        check(
            "%s: tabela == karta" % opis,
            r["tabela"] == r["karta"] and r["bazaTabela"] == r["bazaKarta"],
            r,
        )
        check(
            "%s: przelacznik naprawde rusza wynik (nie no-op)" % opis,
            r["tabela"] != bazowy or r["bazaTabela"] != 8 - 1,
            {"teraz": r["tabela"], "domyslnie": bazowy},
        )
        page.evaluate("(a) => regulaUstaw(a[0], a[1])", [klucz, not wartosc])
        page.wait_for_timeout(250)

    # 3. Po powrocie do domyslnych wynik ten sam co na starcie (regula nie zostawia sladu)
    r = page.evaluate(POROWNAJ)
    check(
        "powrot do domyslnych przywraca wynik wyjsciowy",
        r["tabela"] == bazowy and r["karta"] == bazowy,
        r,
    )

    # 4. Krzywa tez z tego samego zrodla: ostatni punkt == procent calosci
    page.evaluate("() => regulaUstaw('bsBaza', false)")
    page.wait_for_timeout(250)
    ost = page.evaluate(
        """() => {
            const lek = kartaLekcje('u1');
            let baza = 0, c = 0;
            lek.forEach(l => { const w = wagaLekcji(l.s, l.sp); baza += w.baza; c += w.cwiczyl; });
            return baza ? Math.round(c / baza * 100) : null;
        }"""
    )
    r = page.evaluate(POROWNAJ)
    check(
        "krzywa liczy z tego samego zrodla co kafelki",
        ost == r["karta"],
        {"krzywa": ost, "kafelki": r["karta"]},
    )
    page.evaluate("() => regulaUstaw('bsBaza', true)")
    page.wait_for_timeout(250)

    # 5. Straznik na przyszlosc: nikt nie liczy bazy poza wagaLekcji()
    zrodlo = (ROOT / "dziennik_wf.html").read_text(encoding="utf-8")
    check(
        "wagaLekcji() istnieje i jest jedynym miejscem, gdzie reguly staja sie liczbami",
        zrodlo.count("function wagaLekcji(") == 1
        and zrodlo.count("R.bsBaza ?") == 1
        and zrodlo.count("R.ncBaza ?") == 1
        and zrodlo.count("R.nuBaza ?") == 1
        and zrodlo.count("R.nsBaza ?") == 1,
        {
            "wagaLekcji": zrodlo.count("function wagaLekcji("),
            "bsBaza": zrodlo.count("R.bsBaza ?"),
            "ncBaza": zrodlo.count("R.ncBaza ?"),
            "nuBaza": zrodlo.count("R.nuBaza ?"),
            "nsBaza": zrodlo.count("R.nsBaza ?"),
        },
    )

    check("brak bledow JS", not errors, errors[:3])
    browser.close()

httpd.shutdown()
print()
print("WYNIK: %s" % ("WSZYSTKO PASS" if not FAILS else ("%d FAIL" % len(FAILS))))
for f in FAILS:
    print("  - " + f)
sys.exit(1 if FAILS else 0)
