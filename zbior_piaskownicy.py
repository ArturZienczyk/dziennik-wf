# Zbiór testowy do piaskownicy — zaszyfrowana kopia ze ZMYŚLONYMI danymi, do wczytania i klikania.
#
# Po co: piaskownica ma własny, pusty magazyn, więc nowej funkcji nie da się w niej przeklikać bez
# danych (2026-11-17: Artur musiał o zbiór dopytać). Dwie klasy, 5 tygodni lekcji (L2 i L4),
# NB rozrzucone jak w życiu — często cały dzień (obie lekcje). Nazwiska z fixture_stan (zmyślone).
#
# Szyfruje TĄ SAMĄ funkcją, co kopie apki (encryptSnapshot), więc plik wczytuje się zwykłą drogą:
# Uczniowie → Kopia dziennika → wczytaj kopię → hasło. Na końcu skrypt sam go odszyfrowuje (kontrola).
#
# Nazwa pliku celowo BEZ prefiksu „dziennik-wf_” — skrót `kopia` w D:/Projects/tools szuka tego
# prefiksu i mógłby wysłać zmyślone dane na telefon jako prawdziwą kopię.
#
#     python zrob_piaskownice.py        # najpierw: piaskownica z roboczego
#     py -3.14 zbior_piaskownicy.py     # -> backups/PIASKOWNICA-dane-testowe.enc.json, hasło: piaskownica
#
# Uwaga: daty to ostatnie 25 dni roboczych bez kalendarza — lekcje wypadają też w święta (np. 11.11).
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from fixture_stan import NAZWISKA, otworz, serwer, zasiej  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

HASLO = "piaskownica"
PORT = 8797  # nie 8765/8766 — tam bywa plansza
CEL = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else ROOT / "backups" / "PIASKOWNICA-dane-testowe.enc.json"
)

DOLOZ = """(d) => {
  const rng = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
  const dodajNB = (cls) => {
    const klucze = Object.keys(cls.attendance).sort();
    const dni = [...new Set(klucze.map(kluczData))];
    dni.forEach(dz => {
      const ile = Math.floor(rng() * 3);           // 0–2 uczniów nieobecnych w dniu
      for (let i = 0; i < ile; i++) {
        const s = cls.students[Math.floor(rng() * cls.students.length)];
        if (s.longTermReleased) continue;
        klucze.filter(k => kluczData(k) === dz).forEach(k => { cls.attendance[k][s.id] = 'NB'; });   // cały dzień
      }
    });
  };
  const a = getCurrentClass();
  a.name = '6A (test)';
  dodajNB(a);
  // druga klasa: te same daty, inni uczniowie
  const st = d.nazwiska.map((n, i) => ({ id: 'b' + (i + 1), name: n }));
  const b = makeClass(a.school, '7B (test)', st);
  Object.keys(a.attendance).forEach(k => {
    b.attendance[k] = {};
    st.forEach(s => { b.attendance[k][s.id] = rng() < 0.08 ? 'NU' : (rng() < 0.06 ? 'BS' : 'C'); });
  });
  dodajNB(b);
  state.classes.push(b);
  activateClass(a.id);
  save(); refreshAll();
  const ile = c => Object.values(c.attendance).reduce((x, day) => x + Object.values(day).filter(v => attRead(v).s === 'NB').length, 0);
  return { lekcji: Object.keys(a.attendance).length, nbA: ile(a), nbB: ile(b) };
}"""


def main():
    plik = "dziennik_wf_piaskownica.html"
    if not (ROOT / plik).exists():
        sys.exit("Brak %s — najpierw: python zrob_piaskownice.py" % plik)
    CEL.parent.mkdir(exist_ok=True)
    with serwer(PORT) as port, sync_playwright() as pw:
        browser, ctx, page, errors = otworz(pw, port, plik=plik)
        opis = zasiej(page, dni=25, lekcje=(2, 4))
        rng = random.Random(3)
        drugie = sorted(
            {
                n.split()[0]
                + " "
                + rng.choice(["Ola", "Kuba", "Ewa", "Tymon", "Iga", "Leon"])
                for n in NAZWISKA[:18]
            }
        )
        wynik = page.evaluate(DOLOZ, {"nazwiska": drugie})
        tekst = page.evaluate("(p) => encryptSnapshot(p)", HASLO)
        CEL.write_bytes(tekst.encode("utf-8"))
        dane = page.evaluate("([t, p]) => decryptBackup(t, p)", [tekst, HASLO])
        browser.close()
    klasy = [c["name"] for c in dane["classes"]]
    if klasy != ["6A (test)", "7B (test)"] or errors:
        sys.exit("FAIL: klasy po odszyfrowaniu %s, bledy JS %s" % (klasy, errors))
    print("Zbiór: %s" % CEL)
    print("Hasło: %s · lekcje %s → %s · %s" % (HASLO, opis["od"], opis["do"], wynik))
    print(
        "W piaskownicy: Uczniowie → Kopia dziennika → wczytaj; w oknie ✋ wybierz klasę „6A (test)”."
    )


if __name__ == "__main__":
    main()
