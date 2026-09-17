# Bramka: mikrofon rusza WYLACZNIE z lokalnym rozpoznawaniem (processLocally, pakiet pl-PL).
# Gdy Chrome nie ma pakietu i nie da sie go pobrac - mikrofon NIE startuje (fail-closed),
# zamiast po cichu wysylac nagranie z imionami dzieci do Google.
#
# Po co: do 2026-09-17 dyktowanie szlo przez serwery Google (README "Czego to NIE zalatwia").
# Test podstawia atrape SpeechRecognition o roznych stanach pakietu i sprawdza,
# czy start() sie wykonal i z jakim processLocally.
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

FILE = (Path(__file__).resolve().parent / "dziennik_wf.html").as_uri()
FAILS = []


def check(name, cond, detail=""):
    print(
        "[%s] %s %s"
        % ("PASS" if cond else "FAIL", name, ("- " + str(detail)) if detail else "")
    )
    if not cond:
        FAILS.append(name)


# atrapa: stan = wynik available(); instalacja = wynik install(); bezAvailable = stary Chrome
STUB = """(cfg) => {
  window.__mic = { start: 0, processLocally: null, lang: null, install: 0, toast: '' };
  if (!window.__origToast) window.__origToast = window.showToast;
  window.showToast = (m, t) => { window.__mic.toast = m; window.__origToast(m, t); };
  class SR {
    constructor() { this.processLocally = false; }
    start() { window.__mic.start++; window.__mic.processLocally = this.processLocally; window.__mic.lang = this.lang; }
    stop() {}
  }
  if (!cfg.bezAvailable) {
    SR.available = async () => cfg.stan;
    SR.install = async () => { window.__mic.install++; if (cfg.instalacja) cfg.stan = 'available'; return cfg.instalacja; };
  }
  window.SpeechRecognition = SR; window.webkitSpeechRecognition = SR;
}"""


def scenariusz(page, cfg):
    page.evaluate("() => { currentRecognition = null; currentMicTarget = null; }")
    page.evaluate(STUB, cfg)
    page.evaluate(
        "() => toggleMic('dictateField','micBtnObecnosc','micStatusObecnosc')"
    )
    page.wait_for_timeout(300)
    return page.evaluate("() => window.__mic")


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page()
    page.goto(FILE)
    page.wait_for_timeout(1200)
    page.evaluate("() => zamekPierwszeHaslo('x-haslo-123')")

    r = scenariusz(page, {"stan": "available"})
    check(
        "pakiet jest -> start z processLocally=true, pl-PL",
        r["start"] == 1 and r["processLocally"] is True and r["lang"] == "pl-PL",
        r,
    )

    r = scenariusz(page, {"stan": "downloadable", "instalacja": True})
    check(
        "pakiet do pobrania -> install() + start lokalnie",
        r["install"] == 1 and r["start"] == 1 and r["processLocally"] is True,
        r,
    )

    r = scenariusz(page, {"stan": "downloadable", "instalacja": False})
    check(
        "pobranie padlo -> brak startu + komunikat",
        r["start"] == 0 and "Google" in r["toast"],
        r,
    )

    r = scenariusz(page, {"stan": "unavailable"})
    check(
        "polski niewspierany lokalnie -> brak startu + komunikat",
        r["start"] == 0 and "Google" in r["toast"],
        r,
    )

    r = scenariusz(page, {"bezAvailable": True})
    check(
        "stary Chrome bez available() -> brak startu (nie spada do chmury)",
        r["start"] == 0 and "139" in r["toast"],
        r,
    )

    b.close()

if FAILS:
    print("\nWYNIK: FAIL - %d/5: %s" % (len(FAILS), FAILS))
    sys.exit(1)
print("\nWYNIK: PASS 5/5 - mikrofon tylko lokalnie, fail-closed.")
