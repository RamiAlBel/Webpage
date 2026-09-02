(() => {
  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());

  const btn = document.getElementById("copyLink");
  if (!btn) return;

  const copy = async () => {
    const url = window.location.href.split("#")[0];
    try {
      await navigator.clipboard.writeText(url);
      btn.textContent = "Copied";
      window.setTimeout(() => (btn.textContent = "Copy link"), 1200);
    } catch {
      btn.textContent = "Copy failed";
      window.setTimeout(() => (btn.textContent = "Copy link"), 1200);
    }
  };

  btn.addEventListener("click", copy);
})();

/* ========================================================================
   Blob-to-letter scroll effect
   ------------------------------------------------------------------------
   Each matched heading gets its own SVG filter: a Gaussian blur feeding a
   colour matrix that hard-thresholds the alpha channel. High blur + steep
   threshold = merged blobs. Both relax to identity as the heading travels
   from the bottom of the viewport to the centre, so the blobs resolve into
   normal type. No libraries.
   ======================================================================== */
(() => {
  // --- tuning ------------------------------------------------------------
  const SELECTOR = ".title, .h2, .h3";  // which headings get the effect
  const BLUR_RATIO = 0.10;   // max blur as a fraction of the element's font-size
  const THRESHOLD  = 0.30;   // alpha cutoff at full blob (higher = tighter blobs)
  const INTRO_MS   = 900;    // intro animation for headings already on screen
  const STAGGER_MS = 140;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const targets = Array.from(document.querySelectorAll(SELECTOR));
  if (!targets.length) return;

  // One <svg> holding every generated filter.
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("width", "0");
  svg.setAttribute("height", "0");
  svg.setAttribute("aria-hidden", "true");
  svg.style.cssText = "position:absolute;width:0;height:0;overflow:hidden";
  const defs = document.createElementNS(svgNS, "defs");
  svg.appendChild(defs);
  document.body.appendChild(svg);

  const IDENTITY = "1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0";

  const items = targets.map((el, i) => {
    const id = "goo-f" + i;

    const filter = document.createElementNS(svgNS, "filter");
    filter.setAttribute("id", id);
    filter.setAttribute("x", "-30%");
    filter.setAttribute("y", "-40%");
    filter.setAttribute("width", "160%");
    filter.setAttribute("height", "180%");
    filter.setAttribute("color-interpolation-filters", "sRGB");

    const blur = document.createElementNS(svgNS, "feGaussianBlur");
    blur.setAttribute("in", "SourceGraphic");
    blur.setAttribute("stdDeviation", "0");
    blur.setAttribute("result", "blur");

    const matrix = document.createElementNS(svgNS, "feColorMatrix");
    matrix.setAttribute("in", "blur");
    matrix.setAttribute("mode", "matrix");
    matrix.setAttribute("values", IDENTITY);

    filter.appendChild(blur);
    filter.appendChild(matrix);
    defs.appendChild(filter);

    el.classList.add("goo-target");
    el.style.filter = "url(#" + id + ")";

    return { el, blur, matrix, maxBlur: 0, intro: null };
  });

  function measure() {
    for (const it of items) {
      const fs = parseFloat(getComputedStyle(it.el).fontSize) || 20;
      it.maxBlur = fs * BLUR_RATIO;
    }
  }

  // 0 = fully blobby (heading centred on the bottom edge of the viewport)
  // 1 = fully sharp   (heading centred in the middle of the viewport)
  function scrollProgress(el) {
    const r = el.getBoundingClientRect();
    const vh = window.innerHeight;
    const centre = r.top + r.height / 2;
    return (vh - centre) / (vh * 0.5);
  }

  const clamp = (t) => (t < 0 ? 0 : t > 1 ? 1 : t);
  // smoothstep: keeps the blobs readable through the middle of the travel
  // instead of snapping sharp almost immediately.
  const ease  = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };

  function apply(it, p) {
    const inv = 1 - p;
    it.blur.setAttribute("stdDeviation", (it.maxBlur * inv).toFixed(2));
    if (inv < 0.001) {
      it.matrix.setAttribute("values", IDENTITY);
      return;
    }
    // Alpha row is "0 0 0 A B"; the visible cutoff sits at -B / A.
    const a = 1 + 19 * inv;
    const b = -(a * THRESHOLD) * inv;
    it.matrix.setAttribute(
      "values",
      "1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 " + a.toFixed(3) + " " + b.toFixed(3)
    );
  }

  let ticking = false;
  let introRunning = false;

  function frame(now) {
    ticking = false;
    let stillIntro = false;

    for (const it of items) {
      if (it.intro !== null) {
        const t = (now - it.intro) / INTRO_MS;
        if (t >= 1) {
          it.intro = null;
        } else {
          apply(it, ease(t));
          stillIntro = true;
          continue;
        }
      }
      apply(it, ease(scrollProgress(it.el)));
    }

    introRunning = stillIntro;
    if (stillIntro) requestAnimationFrame(frame);
  }

  function onScroll() {
    if (ticking || introRunning) return;
    ticking = true;
    requestAnimationFrame(frame);
  }

  function init() {
    measure();
    const start = performance.now();
    let n = 0;
    for (const it of items) {
      // Headings already at or above the centre would never animate on
      // scroll, so give those a one-off intro instead.
      if (scrollProgress(it.el) > 0) {
        it.intro = start + n * STAGGER_MS;
        n++;
      }
      apply(it, 0);
    }
    introRunning = true;
    requestAnimationFrame(frame);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", () => { measure(); onScroll(); });
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(() => { measure(); onScroll(); });
  }

  init();
})();

/* ========================================================================
   Scroll-driven portrait morph
   ------------------------------------------------------------------------
   Any .morph block holds two stacked images. The top one (.morph-top) fades
   in as the block travels up the viewport, so the portrait moves from the
   photograph toward a blend of the photo and the drawing. Reversible.
   ======================================================================== */
(() => {
  const MAX_MIX = 0.72;   // how far toward the drawing it goes (1 = fully)
  const START   = 0.95;   // viewport fraction where the blend starts
  const END     = 0.30;   // viewport fraction where it reaches MAX_MIX

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const blocks = Array.from(document.querySelectorAll(".morph"));
  if (!blocks.length) return;

  const layers = blocks
    .map((el) => ({ el, top: el.querySelector(".morph-top") }))
    .filter((b) => b.top);
  if (!layers.length) return;

  const clamp = (t) => (t < 0 ? 0 : t > 1 ? 1 : t);
  const ease  = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };

  let ticking = false;

  function frame() {
    ticking = false;
    const vh = window.innerHeight;
    for (const b of layers) {
      const r = b.el.getBoundingClientRect();
      if (r.bottom < -vh || r.top > vh * 2) continue;
      const centre = (r.top + r.height / 2) / vh;   // 1 = bottom edge, 0 = top
      const p = ease((START - centre) / (START - END));
      b.top.style.opacity = (p * MAX_MIX).toFixed(3);
    }
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(frame);
  }

  // Some of these pages are only one screen tall, so there is no scroll to
  // drive the blend and it would sit frozen at whatever the portrait's fixed
  // position happens to map to. On those, blend on hover/tap instead.
  function scrollable() {
    return document.documentElement.scrollHeight - window.innerHeight;
  }

  function setMode() {
    const canScroll = scrollable() > 120;
    for (const b of layers) {
      b.el.classList.toggle("morph--hover", !canScroll);
      if (!canScroll) b.top.style.opacity = b.el.matches(":hover") ? MAX_MIX : 0;
    }
    if (canScroll) frame();
  }

  for (const b of layers) {
    const enter = () => {
      if (b.el.classList.contains("morph--hover")) b.top.style.opacity = MAX_MIX;
    };
    const leave = () => {
      if (b.el.classList.contains("morph--hover")) b.top.style.opacity = 0;
    };
    b.el.addEventListener("mouseenter", enter);
    b.el.addEventListener("mouseleave", leave);
    b.el.addEventListener("touchstart", enter, { passive: true });
    b.el.addEventListener("touchend", leave);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", setMode);
  window.addEventListener("load", setMode);
  setMode();
})();
