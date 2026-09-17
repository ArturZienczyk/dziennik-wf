# Buduje bookmarklet z vulcan-frekwencja.user.js -> vulcan-frekwencja.bookmarklet.txt
# Ta sama tresc co snippet: naglowek ==UserScript== wyciety, reszta URL-encoded pod "javascript:".
# Weryfikacja: odkodowany adres == kod zrodlowy (bez naglowka). Uzycie: py -3.14 build_bookmarklet.py
import sys
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "vulcan-frekwencja.user.js"
OUT = ROOT / "vulcan-frekwencja.bookmarklet.txt"

src = SRC.read_text(encoding="utf-8")
lines = src.split("\n")
body = []
in_hdr = False
for ln in lines:
    if "==UserScript==" in ln:
        in_hdr = True
        continue
    if "==/UserScript==" in ln:
        in_hdr = False
        continue
    if in_hdr:
        continue
    body.append(ln)
code = "\n".join(body).strip("\n")
assert code.startswith("(function(){") and code.endswith(
    "})();"
), "nieoczekiwany ksztalt IIFE"

# safe='' -> koduje tez / ? # & + (w adresie zakladki musza byc zakodowane)
url = "javascript:" + quote(code, safe="")
assert unquote(url[len("javascript:") :]) == code, "dekodowanie nie odtwarza kodu"

OUT.write_text(url, encoding="utf-8", newline="\n")
ver = ""
for ln in body:
    if 'font-weight:normal">v' in ln:
        ver = ln.split('font-weight:normal">')[1].split("<")[0]
print(
    "OK %s: %d znakow adresu (kod %d), wersja panelu %s"
    % (OUT.name, len(url), len(code), ver)
)
if len(url) > 60000:
    print(
        "UWAGA: adres > 60 000 znakow - sprawdz, czy Chrome/Edge przyjmuje",
        file=sys.stderr,
    )
