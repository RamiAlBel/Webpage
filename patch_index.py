#!/usr/bin/env python3
"""
Re-apply the site's custom scroll effects to index.html.

index.html is a self-unpacking Claude Design bundle: the real page lives as a
JSON string inside a <script type="__bundler/template"> tag, and its images
live as base64 in <script type="__bundler/manifest">. This script edits those
payloads in place and writes the file back.

Run it again after regenerating the page from Claude Design:

    python3 tools/patch_index.py

It adds:
  * the blob-to-letter scroll effect on the h1 and section h2s
  * the photo -> photo+drawing portrait morph in the hero
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bundle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
PHOTO = "./images/rami-photo.jpg"
CARTOON = "./images/rami-cartoon.jpg"

# JWST imagery (NASA/ESA/CSA/STScI, public domain). Swap these two filenames to
# change which image sits behind which section - everything under images/jwst/
# is available.
HERO_BACKDROP = "./images/jwst/nebula-cavity.jpg"
BAND_BACKDROP = "./images/jwst/spiral-galaxy.jpg"

MARKER = "/* site-effects */"

EFFECTS_JS = r"""
(() => {
  if (window.__siteEffects) return;
  window.__siteEffects = true;

  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;

  const clamp = (t) => (t < 0 ? 0 : t > 1 ? 1 : t);
  const ease = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };

  // This page renders asynchronously and REPLACES its DOM nodes after the
  // first paint, so anything captured at DOMContentLoaded ends up detached
  // (offsetHeight 0) and silently stops updating. Everything below therefore
  // re-queries the document on every rebuild rather than caching elements.
  //
  // It also applies parallax/reveal transforms, so getBoundingClientRect
  // reports transformed positions that do not track real scroll. offsetTop is
  // layout-based and immune to transforms, so positions are measured with it.
  function docTop(el) {
    let y = 0, n = el;
    while (n) { y += n.offsetTop; n = n.offsetParent; }
    return y;
  }

  /* ---- blob-to-letter headings -------------------------------------- */
  const BLUR_RATIO = 0.10;
  const THRESHOLD = 0.30;
  const IDENTITY = "1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0";
  const NS = "http://www.w3.org/2000/svg";

  let defs = null;
  let goo = [];

  function wireGoo() {
    if (!defs) {
      const svg = document.createElementNS(NS, "svg");
      svg.setAttribute("aria-hidden", "true");
      svg.style.cssText = "position:absolute;width:0;height:0;overflow:hidden";
      defs = document.createElementNS(NS, "defs");
      svg.appendChild(defs);
      document.body.appendChild(svg);
    }
    while (defs.firstChild) defs.removeChild(defs.firstChild);

    goo = Array.from(document.querySelectorAll("h1, h2")).map((el, i) => {
      const id = "site-goo-" + i;
      const f = document.createElementNS(NS, "filter");
      f.setAttribute("id", id);
      f.setAttribute("x", "-30%");
      f.setAttribute("y", "-40%");
      f.setAttribute("width", "160%");
      f.setAttribute("height", "180%");
      f.setAttribute("color-interpolation-filters", "sRGB");
      const blur = document.createElementNS(NS, "feGaussianBlur");
      blur.setAttribute("in", "SourceGraphic");
      blur.setAttribute("stdDeviation", "0");
      blur.setAttribute("result", "blur");
      const mat = document.createElementNS(NS, "feColorMatrix");
      mat.setAttribute("in", "blur");
      mat.setAttribute("mode", "matrix");
      mat.setAttribute("values", IDENTITY);
      f.appendChild(blur);
      f.appendChild(mat);
      defs.appendChild(f);
      el.style.filter = "url(#" + id + ")";
      el.style.willChange = "filter";
      return {
        el: el,
        blur: blur,
        mat: mat,
        max: (parseFloat(getComputedStyle(el).fontSize) || 20) * BLUR_RATIO,
        top: docTop(el)
      };
    });
  }

  function drawGoo() {
    const vh = innerHeight, y = scrollY;
    for (const it of goo) {
      const h = it.el.offsetHeight;
      if (!h) continue;
      const centre = it.top + h / 2 - y;
      if (centre < -vh || centre > vh * 2) continue;
      const p = ease((vh - centre) / (vh * 0.5));
      const inv = 1 - p;
      it.blur.setAttribute("stdDeviation", (it.max * inv).toFixed(2));
      if (inv < 0.001) { it.mat.setAttribute("values", IDENTITY); continue; }
      const a = 1 + 19 * inv;
      const b = -(a * THRESHOLD) * inv;
      it.mat.setAttribute("values",
        "1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 " + a.toFixed(3) + " " + b.toFixed(3));
    }
  }

  /* ---- portrait morph ------------------------------------------------ */
  const MAX_MIX = 0.72;
  const START = 0.95;
  const END = 0.30;

  let morphs = [];

  function wireMorph() {
    morphs = Array.from(document.querySelectorAll(".site-morph"))
      .map((el) => ({ el: el, top: el.querySelector(".site-morph-top"), docTop: docTop(el) }))
      .filter((b) => b.top);
  }

  function drawMorph() {
    const vh = innerHeight, y = scrollY;
    for (const b of morphs) {
      const h = b.el.offsetHeight;
      if (!h) continue;
      const centre = (b.docTop + h / 2 - y) / vh;
      b.top.style.opacity = (ease((START - centre) / (START - END)) * MAX_MIX).toFixed(3);
    }
  }

  /* ---- driver -------------------------------------------------------- */
  let ticking = false;
  function draw() { ticking = false; drawGoo(); drawMorph(); }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(draw); } }

  function rebuild() { wireGoo(); wireMorph(); draw(); }

  function boot() {
    rebuild();
    addEventListener("scroll", onScroll, { passive: true });
    addEventListener("resize", rebuild);
    addEventListener("load", rebuild);
    // Re-bind whenever the page finishes (re)rendering: the node set and the
    // document height both change when the design runtime swaps its DOM in.
    [60, 250, 700, 1500, 2500].forEach((ms) => setTimeout(rebuild, ms));
    if (window.ResizeObserver) {
      let last = -1;
      new ResizeObserver(() => {
        const h = document.documentElement.scrollHeight;
        if (h !== last) { last = h; rebuild(); }
      }).observe(document.documentElement);
    }
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(rebuild);
  }

  if (document.readyState === "loading") addEventListener("DOMContentLoaded", boot);
  else boot();
})();
"""


# ---------------------------------------------------------------- research
# Rebuilt "01 - Research" section: four threads, each with real paper links.
# Links are the canonical ones already used in publications.html.
RESEARCH_CSS = """<style>
.rw-row{display:grid;grid-template-columns:80px 1fr 1fr;gap:32px;align-items:center;
  padding:44px 0;border-bottom:1px solid rgba(12,12,13,.2)}
.rw-num{font:500 13px/1.2 'JetBrains Mono',monospace;color:#ff4e1a;align-self:start;padding-top:6px}
.rw-h2{margin:0;font-stretch:125%;font-weight:600;font-size:clamp(36px,5vw,84px);
  line-height:.92;letter-spacing:-.03em;text-transform:uppercase}
.rw-right{display:flex;flex-direction:column;gap:22px;max-width:520px}
.rw-glabel{display:block;font:400 12px/1 'JetBrains Mono',monospace;letter-spacing:.14em;
  text-transform:uppercase;color:#6f6d68;margin-bottom:10px}
.rw-paper{display:block;color:#0c0c0d;text-decoration:none;padding:9px 0;
  border-top:1px solid rgba(12,12,13,.14);
  transition:padding-left .35s cubic-bezier(.2,.7,.2,1),color .35s}
.rw-paper:hover{padding-left:12px;color:#ff4e1a}
.rw-title{display:block;font-size:16px;line-height:1.4;text-wrap:pretty}
.rw-meta{display:block;margin-top:4px;font:400 11px/1 'JetBrains Mono',monospace;
  letter-spacing:.1em;text-transform:uppercase;color:#6f6d68}
.rw-note{display:block;padding:9px 0;border-top:1px solid rgba(12,12,13,.14);
  font:400 12px/1.4 'JetBrains Mono',monospace;letter-spacing:.1em;
  text-transform:uppercase;color:#6f6d68}
@media (max-width:860px){
  .rw-row{grid-template-columns:44px 1fr;gap:18px;align-items:start}
  .rw-right{grid-column:1/-1;max-width:none}
}
</style>"""


def _paper(href, title, meta):
    return (
        '<a class="rw-paper" href="' + href + '" target="_blank" rel="noreferrer" '
        'data-cursor="Open"><span class="rw-title">' + title + '</span>'
        '<span class="rw-meta">' + meta + ' &#8599;</span></a>'
    )


def _row(num, heading, right):
    return (
        '<div class="rw-row" data-reveal="">'
        '<span class="rw-num">' + num + '</span>'
        '<h2 class="rw-h2">' + heading + '</h2>'
        '<div class="rw-right">' + right + '</div>'
        '</div>'
    )


def _group(label, body):
    return '<div><span class="rw-glabel">' + label + '</span>' + body + '</div>'


def research_html():
    astro = _group(
        "Star formation",
        _paper("https://academic.oup.com/mnras/article/534/4/3176/7783277",
               "Simulated analogues I: apparent and physical evolution of young "
               "binary protostellar systems", "MNRAS 534.4 &#183; 2024")
        + _paper("https://academic.oup.com/mnras/article/534/4/3194/7774401",
                 "Simulated analogues II: a new methodology for non-parametric "
                 "matching of models to observations", "MNRAS 534.4 &#183; 2024"),
    ) + _group(
        "Black holes",
        _paper("https://arxiv.org/abs/2608.18208",
               "A deep learning algorithm for black hole spin estimation using "
               "hot-spot secondary images", "arXiv &#183; 2026"),
    )

    medical = (
        _paper("https://link.springer.com/chapter/10.1007/978-3-031-73290-4_22",
               "Identifying Nonalcoholic Fatty Liver Disease and Advanced Liver "
               "Fibrosis from MRI in UK Biobank", "MLMI @ MICCAI &#183; 2024")
        + _paper("https://openreview.net/forum?id=PH9Ty1t8F6",
                 "Deep Learning for Liver Disease Stratification: Findings from "
                 "UKBB MRI", "MIDL &#183; 2026")
    )

    xai = _paper("./papers/reshape.pdf",
                 "RESHAPE: Representation Learning for the Explainability of Shapes",
                 "Preprint &#183; to appear")

    geo = '<span class="rw-note">Under submission</span>'

    return (
        RESEARCH_CSS
        + _row("01", "Astro&#8209;<br>physics", astro)
        + _row("02", "Medical<br>imaging", medical)
        + _row("03", "Explainable<br>AI", xai)
        + _row("04", "Geometric<br>deep learning", geo)
    )



def main():
    b = bundle.load(INDEX)
    manifest = b["__bundler/manifest"]
    template = b["__bundler/template"]

    if MARKER in template:
        # strip the previous patch so the script is re-runnable
        template = re.sub(
            r"<script>\s*" + re.escape(MARKER) + r".*?</script>", "", template, flags=re.S
        )

    # --- swap the hero portrait for a two-layer morph block ---
    # Skip if a previous run already wrapped it, so the script is re-runnable
    # against an already-patched file instead of nesting a second morph block.
    photo_id, cartoon_id = PHOTO, CARTOON
    if 'class="site-morph"' in template:
        m = None
    else:
        m = re.search(r'<img\b[^>]*alt="Portrait of Rami Al-Belmpeisi"[^>]*>', template)
        if not m:
            raise SystemExit("hero portrait <img> not found - did the design change?")
    if m is not None:
      old = m.group(0)
      style = re.search(r'style="([^"]*)"', old)
      style = style.group(1) if style else "width:120px;height:150px;object-fit:cover"
      layer = ("position:absolute;inset:0;width:100%;height:100%;"
               "object-fit:cover;filter:grayscale(1) contrast(1.1)")
      new = (
          '<div class="site-morph" data-reveal="" style="position:relative;'
          + style.replace("object-fit:cover", "").replace("filter:grayscale(1) contrast(1.1)", "")
          + ';overflow:hidden;isolation:isolate">'
          + '<img src="' + photo_id + '" alt="Portrait of Rami Al-Belmpeisi" style="' + layer + '">'
          + '<img class="site-morph-top" src="' + cartoon_id + '" alt="" aria-hidden="true" '
          + 'style="' + layer + ';opacity:0;will-change:opacity">'
          + "</div>"
      )
      template = template.replace(old, new, 1)

    # --- hero standfirst ---
    # The original copy contains non-breaking hyphens and an em dash, so match
    # it by shape rather than by an exact literal.
    new_hero = "Doctorate Candidate at DTU Compute, Visual Computing section."
    hero_p = re.search(r'(>)(PhD researcher at DTU Visual Computing\..*?)(</p>)', template)
    if hero_p:
        template = template[:hero_p.start(2)] + new_hero + template[hero_p.end(2):]
    elif new_hero not in template:
        raise SystemExit("hero standfirst not found - did the design change?")

    # --- research section: four threads with clickable papers ---
    sec = re.search(r'(<section id="research".*?margin-bottom:8px">.*?</div>)(.*?)(</section>)',
                    template, re.S)
    if not sec:
        raise SystemExit("research section not found - did the design change?")
    template = template[:sec.start(2)] + research_html() + template[sec.end(2):]
    template = template.replace("Three threads", "Four threads", 1)

    # --- preloader counter: show a % after the number ---
    old_progress = "progress: String(progress).padStart(3, \'0\'),"
    if old_progress in template:
        template = template.replace(
            old_progress, "progress: String(progress).padStart(3, \'0\') + \'%\',", 1
        )
    elif "padStart(3, \'0\') + \'%\'" not in template:
        raise SystemExit("preloader counter not found - did the design change?")

    # --- JWST backdrop behind the hero headline ---
    if 'data-site-backdrop' in template:
        hero = None
    else:
        backdrop_id = HERO_BACKDROP
        # Insert AFTER the design's own gradient + grain layers, not before them:
        # those sit on top with a 40px blur and mute the photograph to brown.
        hero = re.search(
            r'<section id="top".*?filter:url\(#grain\)[^>]*></div>', template, re.S)
        if not hero:
            raise SystemExit("hero <section> not found - did the design change?")
    if hero is not None:
        backdrop = (
            '<img data-site-backdrop="" src="' + backdrop_id + '" alt="" aria-hidden="true" '
            'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
            'opacity:1;z-index:0;pointer-events:none">'
            '<div aria-hidden="true" style="position:absolute;inset:0;z-index:0;'
            'pointer-events:none;background:linear-gradient(180deg,rgba(12,12,13,.60) 0%,'
            'rgba(12,12,13,.12) 26%,rgba(12,12,13,.55) 60%,rgba(12,12,13,.90) 100%)"></div>'
        )
        template = template.replace(hero.group(0), hero.group(0) + backdrop, 1)

    # --- second JWST image behind the dark statement band ---
    if 'data-site-band' not in template:
        # Again: insert after this section's own gradient + grain layers, which
        # are blurred and would otherwise sit on top of the photograph.
        band = re.search(
            r'<section data-screen-label="Statement".*?filter:url\(#grain\)[^>]*></div>',
            template, re.S)
        if band:
            layer = (
                '<img data-site-band="" src="' + BAND_BACKDROP + '" alt="" aria-hidden="true" '
                'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
                'opacity:.85;z-index:0;pointer-events:none">'
                '<div aria-hidden="true" style="position:absolute;inset:0;z-index:0;'
                'pointer-events:none;background:rgba(12,12,13,.45)"></div>'
            )
            template = template.replace(band.group(0), band.group(0) + layer, 1)

    # --- inject the effects script ---
    script = "<script>" + MARKER + EFFECTS_JS + "</script>"
    if "</body>" not in template:
        raise SystemExit("no </body> in template")
    template = template.replace("</body>", script + "</body>", 1)

    b["__bundler/template"] = template
    bundle.save(INDEX, b)
    print("patched", INDEX)
    print("  portrait  ", PHOTO, "+", CARTOON)
    print("  hero       ", HERO_BACKDROP)
    print("  band       ", BAND_BACKDROP)


if __name__ == "__main__":
    main()
