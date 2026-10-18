#!/usr/bin/env python3
"""
Generate research.html and about.html inside the same shell as vitae.html
(header with the menu, name banner, footer). Edit vitae.html for shared
styles/menu, patch_index.research_html() for the papers, tools/about_main.html
for the About text, then re-run:

    python3 tools/build_subpages.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_index  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHELL = os.path.join(ROOT, "vitae.html")

RESEARCH_INTRO = (
    "My work uses deep learning to connect models and simulations with real "
    "data, in astrophysics and in medical imaging. Papers are grouped by topic "
    "below; the full list is on <a href=\"./vitae.html\">the vitae page</a> and "
    "<a href=\"" + patch_index.SCHOLAR + "\" target=\"_blank\" rel=\"noreferrer\">"
    "Google Scholar</a>."
)

SHARED_CSS = """<style>
.intro{margin:0 0 8px;max-width:70ch;font-size:18px;line-height:1.65;color:var(--body)}
.para{margin:14px 0 0;max-width:70ch;font-size:17px;line-height:1.65;color:var(--body)}
</style>"""


def shell(title, description, current, heading):
    s = open(SHELL, encoding="utf-8").read()
    s = s.replace("<title>Vitae · Rami Al-Belmpeisi</title>",
                  "<title>" + title + " · Rami Al-Belmpeisi</title>")
    s = re.sub(r'<meta name="description" content="[^"]*">',
               lambda m: '<meta name="description" content="' + description + '">', s, count=1)
    s = s.replace(' aria-current="page"', "")
    s = s.replace('<a href="./' + current + '">', '<a href="./' + current + '" aria-current="page">', 1)
    s = s.replace("<h1>Vitae</h1>", "<h1>" + heading + "</h1>")
    return s.replace("</head>", SHARED_CSS + "\n</head>", 1)


def put_main(s, main_html, head_extra=""):
    if head_extra:
        s = s.replace("</head>", head_extra + "\n</head>", 1)
    return re.sub(r"<main>.*?</main>", lambda m: main_html, s, count=1, flags=re.S)


def write(name, s):
    open(os.path.join(ROOT, name), "w", encoding="utf-8").write(s)
    print("wrote", name)


def research():
    s = shell("Research", "Research of Rami Al-Belmpeisi: astrophysics, 3D imaging and deep "
              "learning, with papers by topic.", "research.html", "Research")
    rows = patch_index.research_html()
    css = rows[: rows.index("</style>") + len("</style>")]
    rows = rows[len(css):].replace(' data-reveal=""', "").replace(' data-cursor="Open"', "")
    css = css.replace("<style>", "<style>\n/* research rows (from patch_index.RESEARCH_CSS) */\n")
    css += "\n<style>.rw-h2{color:#0c0c0d;font-weight:600}</style>"
    main_html = '<main>\n  <p class="intro">' + RESEARCH_INTRO + "</p>\n  " + rows + "\n</main>"
    write("research.html", put_main(s, main_html, css))


def about():
    s = shell("About", "Rami Al-Belmpeisi outside research: music, chess, table tennis, and "
              "Quirky2000, a chess engine you can play in the browser.", "about.html", "About")
    main_html = open(os.path.join(HERE, "about_main.html"), encoding="utf-8").read().strip()
    head = ('<link rel="stylesheet" href="./quirky/play.css">\n'
            '<script src="./quirky/play.js" defer></script>')
    write("about.html", put_main(s, main_html, head))


if __name__ == "__main__":
    research()
    about()
