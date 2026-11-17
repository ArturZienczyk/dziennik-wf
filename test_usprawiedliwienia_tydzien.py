# Test: okno „Usprawiedliwienia — tydzień" (2026-11-17).
# Siatka jednej klasy na tydzień: klik NB -> NU bez okna, drugi klik cofa, „Cofnij zmiany z tego
# okna" przywraca stan sprzed otwarcia, inne statusy nieklikalne, spóźnienie zostaje przy komórce.
# Użycie: py -3.14 test_usprawiedliwienia_tydzien.py [plik.html]
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fixture_stan import otworz, serwer, zasiej  # noqa: E402

PLIK = sys.argv[1] if len(sys.argv) > 1 else "dziennik_wf.html"
ZRZUTY = ROOT / "_zrzuty"
ZRZUTY.mkdir(exist_ok=True)
FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name + " :: " + str(detail))


PRZYGOTUJ = """() => {
  const cls = getCurrentClass();
  const pon = tydzienPoniedzialek(state.currentDate);
  const kl = usprKlucze(cls, pon);
  // czysty tydzień: wszystkim C, potem trzy kontrolowane nieobecności + jedno NU + spóźniony NB
  kl.forEach(k => cls.students.forEach(s => { cls.attendance[k][s.id] = 'C'; }));
  cls.attendance[kl[0]]['u1'] = 'NB';
  cls.attendance[kl[1]]['u1'] = 'NB';
  cls.attendance[kl[2]]['u2'] = { s: 'NB', sp: true };
  cls.attendance[kl[0]]['u3'] = 'NU';
  cls.attendance[kl[0]]['u4'] = 'BS';
  save(); refreshAll();
  return kl;
}"""


def kom(page, k, sid):
    return page.evaluate("([k, sid]) => getCurrentClass().attendance[k][sid]", [k, sid])


def klik(page, k, sid):
    page.click('#usprSiatka tr[data-sid="%s"] button[data-k="%s"]' % (sid, k))


with serwer(8793) as port, sync_playwright() as pw:
    browser, ctx, page, errors = otworz(pw, port, plik=PLIK)
    zasiej(page)
    kl = page.evaluate(PRZYGOTUJ)
    check("tydzień ma >= 3 lekcje", len(kl) >= 3, kl)
    nb_przed = page.evaluate("() => getStudentStats('u1').NB")

    page.click("#usprOtworzBtn")
    page.wait_for_timeout(150)
    check("okno otwarte", page.is_visible("#usprModal"))
    wiersze = page.eval_on_selector_all(
        "#usprSiatka tbody tr[data-sid]", "els => els.map(e => e.dataset.sid)"
    )
    check(
        "domyślnie tylko uczniowie z NB/NU",
        sorted(wiersze) == ["u1", "u2", "u3"],
        wiersze,
    )
    check(
        "licznik NB = 3",
        page.inner_text("#usprIleNB") == "3",
        page.inner_text("#usprIleNB"),
    )
    check("BS nie ma wiersza (tylko NB/NU)", "u4" not in wiersze)
    check("cofnij ukryty na starcie", not page.is_visible("#usprCofnijBtn"))
    page.screenshot(path=str(ZRZUTY / "uspr_1_start.png"), full_page=False)

    # klik NB -> NU, bez okna potwierdzenia
    klik(page, kl[0], "u1")
    page.wait_for_timeout(100)
    check("NB -> NU po kliku", kom(page, kl[0], "u1") == "NU", kom(page, kl[0], "u1"))
    check("bez okna potwierdzenia", not page.is_visible("#confirmModal"))
    check("licznik NB = 2", page.inner_text("#usprIleNB") == "2")
    check(
        "cofnij widoczny (1)",
        page.is_visible("#usprCofnijBtn")
        and "(1)" in page.inner_text("#usprCofnijBtn"),
    )
    check(
        "statystyki ucznia poszły za zmianą",
        page.evaluate("() => getStudentStats('u1').NB") == nb_przed - 1,
    )

    # drugi klik cofa
    klik(page, kl[0], "u1")
    page.wait_for_timeout(100)
    check("drugi klik: NU -> NB", kom(page, kl[0], "u1") == "NB")
    check("po powrocie brak zmian w oknie", not page.is_visible("#usprCofnijBtn"))

    # spóźnienie zostaje
    klik(page, kl[2], "u2")
    page.wait_for_timeout(100)
    check(
        "NB+sp -> NU+sp",
        kom(page, kl[2], "u2") == {"s": "NU", "sp": True},
        kom(page, kl[2], "u2"),
    )

    # NU wpisane wcześniej też da się cofnąć na NB (pomyłka sprzed okna)
    klik(page, kl[1], "u1")
    page.wait_for_timeout(100)
    page.screenshot(path=str(ZRZUTY / "uspr_2_po_klikach.png"), full_page=False)

    # status inny niż NB/NU nie jest przyciskiem
    page.check("#usprWszyscy")
    page.wait_for_timeout(100)
    przyc_u4 = page.eval_on_selector_all(
        '#usprSiatka tr[data-sid="u4"] button', "els => els.length"
    )
    check(
        "cała klasa: widać ucznia z BS",
        page.locator('#usprSiatka tr[data-sid="u4"]').count() == 1,
    )
    check("BS/C nieklikalne", przyc_u4 == 0, przyc_u4)
    page.uncheck("#usprWszyscy")

    # Cofnij wszystko
    page.click("#usprCofnijBtn")
    page.wait_for_timeout(100)
    check("cofnij: u1 lekcja 2 znów NB", kom(page, kl[1], "u1") == "NB")
    check("cofnij: u2 znów NB+sp", kom(page, kl[2], "u2") == {"s": "NB", "sp": True})
    check("licznik NB = 3 po cofnięciu", page.inner_text("#usprIleNB") == "3")

    # nawigacja tygodni
    l1 = page.inner_text("#usprTydzLabel")
    page.click("#usprModal .uspr-nav button[title='poprzedni tydzień']")
    page.wait_for_timeout(100)
    l2 = page.inner_text("#usprTydzLabel")
    check("◀ zmienia tydzień", l1 != l2, (l1, l2))
    page.click("#usprModal .uspr-nav button[title='następny tydzień']")
    check("▶ wraca", page.inner_text("#usprTydzLabel") == l1)

    # Esc zamyka, główny widok przeliczony
    klik(page, kl[0], "u1")
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    check("Esc zamyka okno", not page.is_visible("#usprModal"))
    check("zmiana zostaje po zamknięciu", kom(page, kl[0], "u1") == "NU")

    # telefon 369x608 (pamięć: telefon Artura)
    b2, c2, p2, e2 = otworz(
        pw, port, viewport={"width": 369, "height": 608}, plik=PLIK, telefon=True
    )
    zasiej(p2)
    p2.evaluate(PRZYGOTUJ)
    check("telefon: przycisk w belce dnia widoczny", p2.is_visible("#usprOtworzBtnTel"))
    check(
        "telefon: przycisk z górnego paska schowany",
        not p2.is_visible("#usprOtworzBtn"),
    )
    p2.screenshot(path=str(ZRZUTY / "uspr_3_telefon_belka.png"))
    p2.click("#usprOtworzBtnTel")
    p2.wait_for_timeout(150)
    sz = p2.evaluate("() => document.documentElement.scrollWidth")
    check("telefon: brak poziomego przewijania strony", sz <= 369, sz)
    p2.screenshot(path=str(ZRZUTY / "uspr_4_telefon_okno.png"))
    check("telefon: brak błędów JS", not e2, e2)
    b2.close()

    check("brak błędów JS", not errors, errors)
    browser.close()

    # laptop 1280: wejście w górnym pasku, belka dnia w jednym wierszu (przycisk w belce dawał 59 -> 98 px)
    b3, c3, p3, e3 = otworz(
        pw, port, viewport={"width": 1280, "height": 700}, plik=PLIK
    )
    zasiej(p3)
    check("1280: przycisk w górnym pasku widoczny", p3.is_visible("#usprOtworzBtn"))
    check(
        "1280: przycisk w belce dnia schowany", not p3.is_visible("#usprOtworzBtnTel")
    )
    hb = p3.evaluate(
        "() => document.querySelector('#tab-obecnosc .dzien-row').getBoundingClientRect().height"
    )
    check("1280: belka dnia w jednym wierszu (<= 60 px)", hb <= 60, hb)
    ht = p3.evaluate(
        "() => document.querySelector('.topbar').getBoundingClientRect().height"
    )
    check("1280: górny pasek nie urósł (<= 85 px)", ht <= 85, ht)
    b3.close()

print("\nWYNIK:", "OK" if not FAILS else "FAIL %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
