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
import base64
import mimetypes
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bundle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
PHOTO = os.path.join(ROOT, "images", "rami-photo.jpg")
CARTOON = os.path.join(ROOT, "images", "rami-cartoon.jpg")
# JWST "Cosmic Cliffs" in the Carina Nebula (NASA/ESA/CSA/STScI, public domain)
BACKDROP = os.path.join(ROOT, "images", "space_photo.jpg")

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


def add_asset(manifest, path):
    """Add a file to the bundle manifest, returning its uuid."""
    data = open(path, "rb").read()
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    for uid, entry in manifest.items():
        if entry.get("__source") == os.path.basename(path):
            manifest[uid] = {
                "mime": mime,
                "compressed": False,
                "data": base64.b64encode(data).decode("ascii"),
                "__source": os.path.basename(path),
            }
            return uid
    uid = str(uuid.uuid4())
    manifest[uid] = {
        "mime": mime,
        "compressed": False,
        "data": base64.b64encode(data).decode("ascii"),
        "__source": os.path.basename(path),
    }
    return uid


def main():
    b = bundle.load(INDEX)
    manifest = b["__bundler/manifest"]
    template = b["__bundler/template"]

    if MARKER in template:
        # strip the previous patch so the script is re-runnable
        template = re.sub(
            r"<script>\s*" + re.escape(MARKER) + r".*?</script>", "", template, flags=re.S
        )

    photo_id = add_asset(manifest, PHOTO)
    cartoon_id = add_asset(manifest, CARTOON)

    # --- swap the hero portrait for a two-layer morph block ---
    m = re.search(r'<img\b[^>]*alt="Portrait of Rami Al-Belmpeisi"[^>]*>', template)
    if not m:
        raise SystemExit("hero portrait <img> not found - did the design change?")
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

    # --- preloader counter: show a % after the number ---
    old_progress = "progress: String(progress).padStart(3, \'0\'),"
    if old_progress in template:
        template = template.replace(
            old_progress, "progress: String(progress).padStart(3, \'0\') + \'%\',", 1
        )
    elif "padStart(3, \'0\') + \'%\'" not in template:
        raise SystemExit("preloader counter not found - did the design change?")

    # --- JWST backdrop behind the hero headline ---
    backdrop_id = add_asset(manifest, BACKDROP)
    hero = re.search(r'<section id="top"[^>]*>', template)
    if not hero:
        raise SystemExit("hero <section> not found - did the design change?")
    backdrop = (
        '<img src="' + backdrop_id + '" alt="" aria-hidden="true" '
        'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
        'opacity:.42;z-index:0;pointer-events:none">'
        '<div aria-hidden="true" style="position:absolute;inset:0;z-index:0;'
        'pointer-events:none;background:linear-gradient(180deg,rgba(12,12,13,.55) 0%,'
        'rgba(12,12,13,.25) 35%,rgba(12,12,13,.85) 100%)"></div>'
    )
    template = template.replace(hero.group(0), hero.group(0) + backdrop, 1)

    # --- inject the effects script ---
    script = "<script>" + MARKER + EFFECTS_JS + "</script>"
    if "</body>" not in template:
        raise SystemExit("no </body> in template")
    template = template.replace("</body>", script + "</body>", 1)

    b["__bundler/template"] = template
    bundle.save(INDEX, b)
    print("patched", INDEX)
    print("  photo  ", photo_id)
    print("  cartoon", cartoon_id)


if __name__ == "__main__":
    main()
