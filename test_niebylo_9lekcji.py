# Kafelki „nie było” przy pełnym dniu (9 lekcji, 1400 px, 2026-09-19): sam powód w jednej linii,
# „jednak była” w drugiej — wszystkie kafelki „nie było” tej samej wysokości, nie wyższe niż ~110 px.
# Regresja: „nie było: wycieczka · Kraków, 3 dni” łamało kafelek na 3-4 linie (145 px obok 83 px).
import sys
import pathlib
from playwright.sync_api import sync_playwright

FILE = pathlib.Path(__file__).with_name("dziennik_wf.html").resolve().as_uri()
SHOTS = pathlib.Path(__file__).with_name("_zrzuty")
PLAN = {
    "od": "2026-09-01",
    "do": "2027-06-30",
    "klasy": {
        "7b": {"4": [3]},
        "8c": {"4": [5, 8]},
        "4dLO": {"4": [2, 9]},
        "2 inf": {"4": [1, 6]},
        "3c": {"4": [7]},
    },
    "inne": {"EZ 4a": {"4": [4]}},
    "wolne": [],
}
FIX = """(p) => {
  const st = (n, pref) => Array.from({length: n}, (_, i) => ({ id: pref + (i + 1), name: 'Uczeń ' + pref + i, longTermReleased: false, height: '', weight: '' }));
  state.classes[0].school='ZSS'; state.classes[0].name='7b'; state.classes[0].students=st(6,'u');
  const c8 = makeClass('ZSS','8c',st(5,'v')); state.classes.push(c8);
  const c4 = makeClass('ZSS','4dLO',st(5,'w')); c4.plec='dz'; state.classes.push(c4);
  const c2 = makeClass('Technikum','2 inf',st(4,'x')); state.classes.push(c2);
  const c3 = makeClass('ZSS','3c',st(4,'y')); state.classes.push(c3);
  activateClass(state.classes[0].id);
  state.classes[0].attendance['2026-09-18'] = { u1:'C', u2:'BS' };
  c2.odwolane = {'2026-09-18':'wycieczka · Kraków, 3 dni', '2026-09-18#6':'zawody'};
  c4.odwolane = {'2026-09-18':'apel · pierwsza godzina', '2026-09-18#9':'inne · nauczyciel na szkoleniu'};
  c8.odwolane = {'2026-09-18#8':'choroba nauczyciela'};
  zaleglePlanZastosuj(p); state.currentDate='2026-09-18'; save(); refreshAll();
}"""
FAILS = []


def check(name, cond, detail=""):
    print(
        ("[PASS] " if cond else "[FAIL] ")
        + name
        + (" - %s" % (detail,) if detail != "" else "")
    )
    if not cond:
        FAILS.append(name)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_context(
        viewport={"width": 1400, "height": 900}, service_workers="block"
    ).new_page()
    page.clock.set_fixed_time("2026-09-18T10:00:00")
    page.goto(FILE)
    page.wait_for_timeout(800)
    page.evaluate("() => zamekPierwszeHaslo('x-haslo-123')")
    page.wait_for_timeout(400)
    page.evaluate(FIX, PLAN)
    page.wait_for_timeout(300)
    SHOTS.mkdir(exist_ok=True)
    page.locator("#dzienKolumny").screenshot(path=str(SHOTS / "niebylo_9lekcji_po.png"))
    h = page.evaluate(
        "() => [...document.querySelectorAll('#dzienKolumny .kol.podglad.niebylo')].map(k => k.offsetHeight)"
    )
    check("5 kafelków „nie było”", len(h) == 5, h)
    check("wszystkie tej samej wysokości", len(set(h)) == 1, h)
    check("nie wyższe niż 110 px", max(h) <= 110, h)
    txt = page.evaluate(
        "() => [...document.querySelectorAll('.kol.podglad.niebylo .niebylo-zmien')].map(b => b.textContent.trim())"
    )
    check(
        "kafelek pokazuje sam powód, bez komentarza",
        txt == ["wycieczka", "apel", "zawody", "choroba nauczyciela", "inne"],
        txt,
    )
    tit = page.evaluate(
        "() => document.querySelector('.kol.podglad.niebylo .niebylo-zmien').title"
    )
    check("komentarz w dymku", "Kraków, 3 dni" in tit, tit)
    lin = page.evaluate(
        "() => [...document.querySelectorAll('.kol.podglad.niebylo .niebylo-zmien')].map(b => b.getBoundingClientRect().height)"
    )
    check("powód w jednej linii (≤ 20 px)", max(lin) <= 20, lin)
    check(
        "„jednak była” na każdym",
        page.locator(".kol.podglad.niebylo .niebylo-cofnij:visible").count() == 5,
    )
    b.close()

print("\nWYNIK: " + ("OK (0 FAIL)" if not FAILS else "BŁĘDY (%d FAIL)" % len(FAILS)))
sys.exit(1 if FAILS else 0)
