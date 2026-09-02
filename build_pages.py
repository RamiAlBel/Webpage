#!/usr/bin/env python3
"""
Generate the article pages, the article index, and the hobbies page.

These are plain static pages (no bundle, no build step) styled by site.css so
they match the homepage. Edit the ARTICLES / BANDS data below and re-run:

    python3 tools/build_pages.py
"""
import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NAV = [
    ("Home", "index.html"),
    ("About", "about.html"),
    ("Publications", "publications.html"),
    ("Articles", "articles.html"),
    ("Hobbies", "hobbies.html"),
    ("Contact", "contact.html"),
]


def head(title, desc, up=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html.escape(desc)}">
<title>{html.escape(title)} · Rami Al-Belmpeisi</title>
<link rel="stylesheet" href="{up}site.css">
</head>
<body>
"""


def header(current, up=""):
    parts = []
    for label, href in NAV:
        cur = ' aria-current="page"' if href == current else ""
        parts.append('<a href="' + up + href + '"' + cur + '>' + label + '</a>')
    links = "".join(parts)
    return f"""<header class="site-head mono">
  <a class="brand" href="{up}index.html">R. Al&#8209;Belmpeisi</a>
  <nav class="site-nav">{links}</nav>
</header>
"""


def footer(up=""):
    return f"""<footer class="site-foot mono">
  <span>&copy; 2026 Rami Al-Belmpeisi</span>
  <a href="{up}index.html">Home &#8599;</a>
</footer>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Articles. `body` is the write-up; keep it factual — these describe real runs.
# --------------------------------------------------------------------------
ARTICLES = [
    {
        "slug": "photoevaporation",
        "num": "01",
        "title": "Photoevaporation of planetary atmospheres",
        "sub": "A close-in planet loses its atmosphere to its host star's radiation. "
               "What the outflow looks like, and how fast it drains.",
        "video": "0bFUNvkc5_w",
        "kicker": "Planetary hydrodynamics",
        "meta": ["PLUTO / C++", "Hydrodynamics", "Niels Bohr Institute"],
        "body": [
            "A planet orbiting close to its star sits in a bath of high-energy "
            "ultraviolet radiation. That radiation heats the upper atmosphere far "
            "beyond what the planet's gravity can comfortably hold, and the gas "
            "starts to flow outward — not blown off in one event, but leaking "
            "continuously, in a steady transonic wind.",
            "The simulation follows that wind. Gas near the top of the atmosphere "
            "absorbs the incoming radiation, heats, expands, and accelerates "
            "outward until it passes through a sonic point and escapes. What makes "
            "this interesting is that the structure settles: after an initial "
            "transient the outflow reaches a quasi-steady state, and the mass-loss "
            "rate becomes a number you can actually quantify.",
            "<strong>What to watch for:</strong> the launch region low in the "
            "atmosphere where heating dominates, the acceleration through the "
            "sonic point, and how the whole structure stabilises rather than "
            "running away.",
            "The runs vary the irradiation level, which is the parameter that "
            "matters most: it sets both the mass-loss rate and the timescale on "
            "which the outflow reaches hydrodynamic stability. Over a planet's "
            "lifetime those numbers decide whether it keeps a thick envelope or "
            "ends up a stripped rocky core.",
        ],
    },
    {
        "slug": "galactic-winds",
        "num": "02",
        "title": "Supernova-driven galactic winds",
        "sub": "Repeated explosions carve escape routes through a galaxy's gas, "
               "and hot material pours out along them.",
        "video": "RUwtoE7kXNc",
        "kicker": "Interstellar medium",
        "meta": ["MHD", "Galactic outflows", "Two runs"],
        "extra_video": ("1DqsDATE2aU", "Run 2 — same setup, different realisation"),
        "body": [
            "Massive stars die in quick succession and in roughly the same places, "
            "which means a galaxy's interstellar medium is repeatedly hit by "
            "explosions in clustered bursts. A single supernova mostly stirs its "
            "surroundings. Many of them, overlapping in space and time, do "
            "something qualitatively different: they clear channels of low-density "
            "gas, and those channels become escape routes.",
            "Once a channel opens, hot gas that would otherwise stay bound flows "
            "out along it. The result is a galactic wind — an outflow that carries "
            "mass, metals and energy out of the disc entirely.",
            "<strong>What to watch for:</strong> the transition from isolated "
            "bubbles to connected channels, and the moment the outflow stops "
            "looking like local turbulence and starts looking like a coherent "
            "wind leaving the system.",
            "Two runs are shown. They use the same physical setup but different "
            "realisations, which is the honest way to look at this: the detailed "
            "structure is stochastic, so the features worth trusting are the ones "
            "that survive across both.",
        ],
    },
    {
        "slug": "interstellar-cloud",
        "num": "03",
        "title": "Seeing through an interstellar cloud",
        "sub": "The same cloud is opaque in visible light and transparent in the "
               "infrared. A sweep through wavelength shows the stars come back.",
        "video": "MNYxMEqgfec",
        "kicker": "Radiative transfer",
        "meta": ["RADMC-3D", "Dust opacity", "Synthetic observations"],
        "body": [
            "Interstellar dust does not block light equally at all wavelengths. "
            "Grains are comparable in size to visible-light wavelengths, so they "
            "scatter and absorb that light efficiently; infrared light has "
            "wavelengths much longer than the grains and passes through far more "
            "easily. A cloud that looks like a hole in the sky is often just a "
            "cloud you are looking at in the wrong band.",
            "This animation makes that concrete. It sweeps the observing "
            "wavelength across a fixed cloud and shows the same scene "
            "re-rendered at each step — the extinction drops, and background "
            "stars that were completely hidden reappear one by one.",
            "<strong>What to watch for:</strong> the point where the cloud stops "
            "being a silhouette and becomes a translucent structure with things "
            "visible behind and inside it.",
            "Producing these frames means solving the radiative transfer problem "
            "for a dusty medium at each wavelength — following light as it is "
            "absorbed, re-emitted and scattered through the volume. That is what "
            "turns a simulation into something you can compare against a real "
            "telescope image, which is the whole point of the exercise.",
        ],
    },
    {
        "slug": "mandelbrot-zoom",
        "num": "04",
        "title": "Mandelbrot zoom beyond numerical precision",
        "sub": "A deep zoom into the Mandelbrot set, continuing until "
               "floating-point arithmetic itself becomes the limiting factor.",
        "video": "h9ZEaS0Lotk",
        "kicker": "Numerics",
        "meta": ["Floating point", "Deep zoom", "For fun"],
        "body": [
            "The Mandelbrot set is defined by iterating one very short expression, "
            "and yet it has structure at every scale you care to look at. Zooming "
            "in never runs out of detail — which makes it an unusually honest "
            "stress test for the arithmetic doing the zooming.",
            "Every step inward means resolving smaller differences between "
            "neighbouring points. Double-precision floating point carries roughly "
            "sixteen significant decimal digits, so at some depth the coordinates "
            "of adjacent pixels stop being distinguishable numbers at all. The "
            "image does not gently blur; it degrades into blocks and banding, "
            "because the computer is genuinely no longer able to tell those points "
            "apart.",
            "<strong>What to watch for:</strong> the point where the failure stops "
            "looking like the fractal and starts looking like the hardware. Going "
            "deeper requires changing the arithmetic — arbitrary precision, or "
            "perturbation methods that track differences from a reference orbit.",
            "This one is not research. It is a good illustration of something that "
            "matters in research: the answer a simulation gives you is only ever as "
            "good as the numbers it is made of.",
        ],
    },
]


def article_page(a):
    body = "".join(f"<p>{p}</p>" for p in a["body"])
    meta = "".join(f"<span>{html.escape(m)}</span>" for m in a["meta"])
    extra = ""
    if a.get("extra_video"):
        vid, cap = a["extra_video"]
        extra = (
            f'<div class="video"><iframe src="https://www.youtube.com/embed/{vid}" '
            f'title="{html.escape(cap)}" loading="lazy" allowfullscreen '
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
            'gyroscope; picture-in-picture; web-share"></iframe></div>'
            f'<p class="caption">{html.escape(cap)}</p>'
        )
    return (
        head(a["title"], a["sub"], up="../")
        + header("articles.html", up="../")
        + f"""<main>
  <div class="sec-rule mono"><span>{a['num']} &#8212; {html.escape(a['kicker'])}</span><a href="../articles.html" style="color:inherit;text-decoration:none">All articles &#8599;</a></div>
  <h1 class="display">{html.escape(a['title'])}</h1>
  <p class="lede">{html.escape(a['sub'])}</p>
  <div class="meta mono">{meta}</div>
  <div class="video"><iframe src="https://www.youtube.com/embed/{a['video']}" title="{html.escape(a['title'])}" loading="lazy" allowfullscreen allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"></iframe></div>
  <div class="prose">{body}</div>
  {extra}
  <a class="back mono" href="../articles.html">&#8592; Back to articles</a>
</main>
"""
        + footer(up="../")
    )


def articles_index():
    items = "".join(
        f"""<a class="idx-item" href="articles/{a['slug']}.html">
  <span class="idx-num mono">{a['num']}</span>
  <div><h2 class="idx-title">{html.escape(a['title'])}</h2><span class="idx-sub">{html.escape(a['sub'])}</span></div>
  <span class="idx-go">&#8599;</span>
</a>"""
        for a in ARTICLES
    )
    return (
        head("Articles", "Short write-ups on simulations and numerical experiments.")
        + header("articles.html")
        + f"""<main>
  <div class="sec-rule mono"><span>Articles</span><span>{len(ARTICLES)} pieces</span></div>
  <h1 class="display">Numerical<br>experiments</h1>
  <p class="lede">Each of these started as a simulation I needed to look at. The
  videos are the output; the write-ups explain what is actually happening in
  them and why it was worth running.</p>
  <div style="margin-top:56px">{items}</div>
</main>
"""
        + footer()
    )


# --------------------------------------------------------------------------
# Music timeline. Add a URL to a band's "links" list to make it clickable.
# --------------------------------------------------------------------------
BANDS = [
    {
        "years": "2017 &#8212; 2019",
        "role": "Fuzzma",
        "part": "Bassist",
        "body": "Four years in Thessaloniki playing bass, and the first time I was "
                "in a room where a record got made rather than talked about.",
        # Add ("Listen &#8599;", "<url>", False) to links once there is one.
        "links": [],
        "note": "",
    },
    {
        "years": "2019 &#8212; 2023",
        "role": "Solo projects",
        "part": "Bubblewalker &#183; For Her Eyes",
        "body": "Two solo projects written and recorded on my own, mostly during "
                "the move to Copenhagen and the years of the MSc.",
        # Add ("Bubblewalker &#8599;", "<url>", False) etc. once there are links.
        "links": [],
        "note": "",
    },
    {
        "years": "2023 &#8212; 2026",
        "role": "Simulated Analogues",
        "part": "Copenhagen",
        "body": "<strong>Multiplicity</strong>, the debut record &#8212; twelve "
                "tracks, 43:36, released 10 May 2026 on LP and digital, mastered "
                "by Volt Motion Productions. Guitar, bass, synths and voice. "
                "The name is not a coincidence.",
        "links": [
            ("Listen &#8212; simulatedanalogues.com", "https://simulatedanalogues.com/", True),
            ("Full album &#8599;",
             "https://www.youtube.com/playlist?list=OLAK5uy_meTV0qohTJ_auPtF5lv4UMeCwjThxDXj0", False),
            ("All links &#8599;", "https://linktr.ee/simulatedanalogues", False),
        ],
        "note": "",
        "now": True,
    },
]


def hobbies_page():
    items = []
    for b in BANDS:
        links = "".join(
            f'<a class="chip mono{" chip--solid" if solid else ""}" href="{url}" '
            f'target="_blank" rel="noreferrer">{label}</a>'
            for label, url, solid in b["links"]
        )
        links = f'<div class="tl-links">{links}</div>' if links else ""
        note = f'<p class="tl-note">{b["note"]}</p>' if b["note"] else ""
        items.append(
            f"""<li class="tl-item{' is-now' if b.get('now') else ''}">
  <span class="tl-years mono">{b['years']}</span>
  <h3 class="tl-role">{b['role']}</h3>
  <p class="tl-note" style="margin-top:6px">{b['part']}</p>
  <p class="tl-body">{b['body']}</p>
  {links}{note}
</li>"""
        )
    timeline = "".join(items)
    return (
        head("Hobbies", "Music, chess and table tennis.")
        + header("hobbies.html")
        + f"""<main>
  <div class="sec-rule mono"><span>Hobbies</span><span>Off duty</span></div>
  <h1 class="display">Hobbies</h1>
  <p class="lede">What I do when I am not looking at simulations. Mostly this
  means music, which has been running alongside everything else since long
  before the PhD.</p>

  <div class="sec-rule mono" style="margin-top:20px"><span>Music</span><span>2017 &#8212; present</span></div>
  <ul class="timeline">{timeline}</ul>

  <div class="sec-rule mono"><span>Elsewhere</span><span>Less organised</span></div>
  <div class="cards">
    <div class="card-lite">
      <h3>Chess</h3>
      <p>First place in the Thermaikos Chess Championship in 2014 and again in
      2015. These days it is mostly blitz and the occasional over-the-board game.</p>
    </div>
    <div class="card-lite">
      <h3>Table tennis</h3>
      <p>Played regularly and competitively enough to care about it. Good for
      the kind of thinking that does not happen at a desk.</p>
    </div>
  </div>
</main>
"""
        + footer()
    )


def main():
    written = []

    for a in ARTICLES:
        path = os.path.join(ROOT, "articles", a["slug"] + ".html")
        open(path, "w", encoding="utf-8").write(article_page(a))
        written.append(path)

    for name, content in [("articles.html", articles_index()),
                          ("hobbies.html", hobbies_page())]:
        path = os.path.join(ROOT, name)
        open(path, "w", encoding="utf-8").write(content)
        written.append(path)

    # movies.html kept as a redirect so old links and bookmarks still resolve.
    redirect = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=articles.html">
<link rel="canonical" href="articles.html">
<title>Moved to Articles</title>
</head>
<body>
<p>This page is now <a href="articles.html">Articles</a>.</p>
</body>
</html>
"""
    path = os.path.join(ROOT, "movies.html")
    open(path, "w", encoding="utf-8").write(redirect)
    written.append(path)

    for p in written:
        print("wrote", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()
