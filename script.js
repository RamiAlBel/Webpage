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
