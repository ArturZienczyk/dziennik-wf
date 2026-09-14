# -*- coding: utf-8 -*-
# Wkleja kroje Google Fonts do pliku dziennika jako data: URI.
# Efekt: zero zapytan na zewnatrz, identyczny wyglad bez internetu.
# Bierzemy tylko subsety latin i latin-ext (polskie znaki), reszte pomijamy.
import base64
import re
import urllib.request

HTML = r"D:\Projects\nauczyciel\wf\dziennik-wf\dziennik_wf.html"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)  # decyduje, czy dostaniemy woff2
SUBSETY = ("latin", "latin-ext")


def pobierz(url, binarny=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        dane = r.read()
    return dane if binarny else dane.decode("utf-8")


def bloki_font_face(css):
    """Dzieli CSS na bloki @font-face wraz z poprzedzajacym komentarzem /* subset */."""
    out = []
    for kawalek in css.split("@font-face")[1:]:
        koniec = kawalek.find("}")
        assert koniec > 0, "blok @font-face bez zamkniecia"
        out.append("@font-face" + kawalek[: koniec + 1])
    return out


def nazwa_subsetu(css, pozycja_bloku):
    """Google poprzedza kazdy blok komentarzem z nazwa subsetu."""
    przed = css[:pozycja_bloku]
    kom = re.findall(r"/\*\s*([a-z0-9-]+)\s*\*/", przed)
    return kom[-1] if kom else "?"


# --- samotest parsera (3 przypadki: typowy, brzegowy, wrogi) zanim ruszy na zywo ---
_typowy = "/* latin */\n@font-face {font-family: 'A'; src: url(https://x/a.woff2) format('woff2');}"
_brzegowy = "/* latin-ext */\n@font-face{src:url(https://x/b.woff2)}"
_wrogi = "/* greek */\n@font-face { src: url(https://x/c.woff2); /* } w komentarzu */ }"
assert len(bloki_font_face(_typowy)) == 1, "parser: typowy"
assert len(bloki_font_face(_brzegowy)) == 1, "parser: brzegowy"
assert len(bloki_font_face(_typowy + "\n" + _brzegowy)) == 2, "parser: dwa bloki"
assert nazwa_subsetu(_typowy, _typowy.index("@font-face")) == "latin", "subset: typowy"
assert nazwa_subsetu(_wrogi, _wrogi.index("@font-face")) == "greek", "subset: wrogi"
print("parser: 5/5 samotestow OK")

s = open(HTML, encoding="utf-8").read()
m = re.search(
    r'<link href="(https://fonts\.googleapis\.com/css2[^"]+)" rel="stylesheet">', s
)
assert m, "nie znalazlem <link> do Google Fonts"
# Wariant E (zmierzony 2026-09-14): zakresy wag zamiast pojedynczych + Serif bez osi opsz.
# 259 KB zamiast 1251 KB, te same trzy rodziny i te same wagi 400-600.
css_url = (
    "https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400..600"
    "&family=IBM+Plex+Sans:wght@400..600&family=IBM+Plex+Mono:wght@400&display=swap"
)

css = pobierz(css_url)
assert "woff2" in css, "Google oddal format inny niz woff2 - sprawdz User-Agent"

wynik, pominiete, razem_bajtow = [], [], 0
for blok in bloki_font_face(css):
    subset = nazwa_subsetu(css, css.index(blok))
    if subset not in SUBSETY:
        pominiete.append(subset)
        continue
    url = re.search(r"url\((https://[^)]+\.woff2)\)", blok)
    assert url, "blok @font-face bez pliku woff2"
    surowe = pobierz(url.group(1), binarny=True)
    razem_bajtow += len(surowe)
    b64 = base64.b64encode(surowe).decode("ascii")
    wynik.append(blok.replace(url.group(1), "data:font/woff2;base64," + b64))

assert wynik, "nie osadzono zadnego kroju"
print(
    "osadzone: %d krojow (%s), pominiete subsety: %s"
    % (len(wynik), ", ".join(SUBSETY), ", ".join(sorted(set(pominiete))) or "brak")
)
print(
    "woff2 razem: %.0f KB -> w pliku jako base64 ok. %.0f KB"
    % (razem_bajtow / 1024, razem_bajtow * 1.34 / 1024)
)

blok_css = (
    "<style>\n"
    "/* Kroje wklejone do pliku 2026-09-14: dziennik nie laczy sie z Google.\n"
    "   Zrodlo: " + css_url + "\n"
    "   Subsety latin + latin-ext (polskie znaki). Odswiezenie: scratchpad/osadz_fonty.py */\n"
    + "\n".join(wynik)
    + "\n</style>"
)

stare = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link href="' + m.group(1) + '" rel="stylesheet">'
)
assert s.count(stare) == 1, "kotwica <link> nie pasuje (%d)" % s.count(stare)
s = s.replace(stare, blok_css)
assert "fonts.googleapis.com/css2" not in s.replace(
    css_url, ""
), "zostal odnosnik do Google"

open(HTML, "w", encoding="utf-8").write(s)
print("plik po zmianie: %.0f KB" % (len(s.encode("utf-8")) / 1024))
