// 8-bit board for playing Quirky2000. The engine runs in a Web Worker (engine.js + quirky.wasm),
// entirely in the visitor's browser. Click a piece, then a highlighted square.
(() => {
  const root = document.getElementById("qk");
  if (!root) return;
  const $ = (s) => root.querySelector(s);
  const boardEl = $(".qk-board"), statusEl = $(".qk-status"), movesEl = $(".qk-moves");
  const LEVELS = { easy: 3000, medium: 30000, hard: 150000 };
  const BOOK_PLIES = 12;

  // ---- 12x12 pixel sprites; outline is computed around each shape ----
  const SPR = {
    p: ["............", ".....##.....", "....####....", "....####....", ".....##.....", "....####....",
        ".....##.....", ".....##.....", "....####....", "...######...", "..########..", "............"],
    r: ["............", "..##.##.##..", "..########..", "...######...", "....####....", "....####....",
        "....####....", "....####....", "...######...", "..########..", "..########..", "............"],
    n: ["............", "......##....", ".....####...", "....######..", "...##.####..", "..########..",
        "..###.####..", "......####..", ".....#####..", "....######..", "...########.", "............"],
    b: ["............", ".....##.....", "....####....", "...##.###...", "...#.####...", "...######...",
        "....####....", ".....##.....", "....####....", "...######...", "..########..", "............"],
    q: ["............", "..#..##..#..", "..#..##..#..", "..##.##.##..", "..########..", "...######...",
        "....####....", "....####....", "...######...", "..########..", "..########..", "............"],
    k: ["............", ".....##.....", "....####....", ".....##.....", "..########..", "..########..",
        "...######...", "....####....", "....####....", "...######...", "..########..", "............"],
  };
  const sprite = (type, white) => {
    const g = SPR[type], on = (x, y) => y >= 0 && y < 12 && x >= 0 && x < 12 && g[y][x] === "#";
    let body = "", line = "";
    for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) {
      if (on(x, y)) body += `M${x} ${y}h1v1h-1z`;
      else if (on(x - 1, y) || on(x + 1, y) || on(x, y - 1) || on(x, y + 1)) line += `M${x} ${y}h1v1h-1z`;
    }
    const fill = white ? "#f6f1e3" : "#2b2a27";
    return `<svg viewBox="0 0 12 12" shape-rendering="crispEdges" aria-hidden="true">` +
      `<path d="${line}" fill="#0c0c0d"/><path d="${body}" fill="${fill}"/></svg>`;
  };
  const NAMES = { p: "pawn", n: "knight", b: "bishop", r: "rook", q: "queen", k: "king" };

  // ---- engine worker ----
  let worker = null, seq = 0;
  const pending = new Map();
  const ask = (cmd, extra = {}) => new Promise((res, rej) => {
    const id = ++seq;
    pending.set(id, { res, rej });
    worker.postMessage({ id, cmd, ...extra });
  });
  const startWorker = () => {
    worker = new Worker(root.dataset.engine || "quirky/engine.js");
    worker.onmessage = (e) => {
      const p = pending.get(e.data.id);
      if (!p) return;
      pending.delete(e.data.id);
      e.data.ok ? p.res(e.data) : p.rej(new Error(e.data.error));
    };
    worker.onerror = (e) => setStatus("Engine failed to load. " + (e.message || ""));
  };

  // ---- game state ----
  let st = null, moves = [], human = "w", sel = null, busy = false, lastMove = null;

  const parseFen = (fen) => {
    const rows = fen.split(" ")[0].split("/"), sq = {};
    rows.forEach((r, i) => {
      let f = 0;
      for (const c of r) {
        if (/\d/.test(c)) f += +c;
        else { sq["abcdefgh"[f] + (8 - i)] = c; f++; }
      }
    });
    return sq;
  };
  const turn = () => st.fen.split(" ")[1];
  const setStatus = (t) => { statusEl.textContent = t; };

  function render() {
    const pcs = parseFen(st.fen);
    const files = human === "w" ? "abcdefgh" : "hgfedcba";
    const ranks = human === "w" ? "87654321" : "12345678";
    const targets = sel ? st.legal.filter((m) => m.startsWith(sel)).map((m) => m.slice(2, 4)) : [];
    let kingSq = null;
    if (st.check) for (const [s, p] of Object.entries(pcs)) if (p === (turn() === "w" ? "K" : "k")) kingSq = s;
    let html = "";
    for (const r of ranks) for (const f of files) {
      const s = f + r, p = pcs[s], dark = ("abcdefgh".indexOf(f) + +r) % 2 === 0;
      const cls = ["qk-sq", dark ? "d" : "l"];
      if (sel === s) cls.push("sel");
      if (targets.includes(s)) cls.push(p ? "cap" : "tgt");
      if (lastMove && (lastMove.slice(0, 2) === s || lastMove.slice(2, 4) === s)) cls.push("last");
      if (kingSq === s) cls.push("chk");
      const label = p ? `${p === p.toUpperCase() ? "white" : "black"} ${NAMES[p.toLowerCase()]} on ${s}` : s;
      html += `<button class="${cls.join(" ")}" data-sq="${s}" aria-label="${label}">` +
        (p ? sprite(p.toLowerCase(), p === p.toUpperCase()) : "") +
        (f === files[0] ? `<i class="rk">${r}</i>` : "") + (r === ranks[7] ? `<i class="fl">${f}</i>` : "") +
        `</button>`;
    }
    boardEl.innerHTML = html;
    movesEl.textContent = moves.length
      ? moves.map((m, i) => (i % 2 === 0 ? `${i / 2 + 1}.` : "") + m).join(" ")
      : "No moves yet.";
    movesEl.scrollTop = movesEl.scrollHeight;
  }

  const END = { 1: "Checkmate", 2: "Stalemate", 3: "Draw (50 moves)", 4: "Draw (repetition)", 5: "Draw (material)" };
  function describe() {
    if (st.status) {
      if (st.status === 1) return turn() === human ? "Checkmate. Quirky wins." : "Checkmate. You win!";
      return END[st.status] + ".";
    }
    if (busy) return "Quirky is thinking...";
    return turn() === human ? (st.check ? "Check! Your move." : "Your move.") : "...";
  }

  async function engineMove() {
    if (st.status || turn() === human) return;
    busy = true; setStatus(describe());
    const nodes = LEVELS[$(".qk-level").value] || LEVELS.medium;
    const t0 = performance.now();
    const r = await ask("think", { nodes, bookPlies: BOOK_PLIES });
    const wait = 350 - (performance.now() - t0);  // let the "thinking" read as a move, not a flicker
    if (wait > 0) await new Promise((ok) => setTimeout(ok, wait));
    if (r.move) {
      st = await ask("play", { move: r.move });
      moves.push(r.move); lastMove = r.move;
    }
    busy = false; render(); setStatus(describe());
  }

  async function tryMove(from, to) {
    let m = st.legal.find((x) => x.slice(0, 4) === from + to);
    if (!m) return false;
    if (m.length === 5) m = from + to + "q";  // promotions: always a queen
    st = await ask("play", { move: m });
    moves.push(m); lastMove = m; sel = null;
    render(); setStatus(describe());
    await engineMove();
    return true;
  }

  boardEl.addEventListener("click", async (e) => {
    const b = e.target.closest(".qk-sq");
    if (!b || busy || !st || st.status || turn() !== human) return;
    const s = b.dataset.sq, p = parseFen(st.fen)[s];
    const mine = p && (p === p.toUpperCase()) === (human === "w");
    if (sel && sel !== s && (await tryMove(sel, s))) return;
    sel = mine && sel !== s ? s : null;
    render();
  });

  async function newGame(side) {
    if (busy) return;
    human = side; sel = null; moves = []; lastMove = null;
    st = await ask("new");
    render(); setStatus(describe());
    await engineMove();
  }

  $(".qk-white").addEventListener("click", () => newGame("w"));
  $(".qk-black").addEventListener("click", () => newGame("b"));
  $(".qk-undo").addEventListener("click", async () => {
    if (busy || !moves.length) return;
    moves.splice(-(turn() === human ? 2 : 1));
    if (moves.length && (moves.length % 2 === 0) !== (human === "w")) moves.pop();
    lastMove = moves[moves.length - 1] || null; sel = null;
    st = await ask("set", { moves });
    render(); setStatus(describe());
    await engineMove();
  });

  // start the engine only when the board is near the screen (the net is ~6 MB)
  const boot = async () => {
    setStatus("Loading Quirky2000...");
    startWorker();
    try { await newGame("w"); } catch (err) { setStatus("Engine failed to load: " + err.message); }
  };
  const io = new IntersectionObserver((es) => {
    if (es.some((x) => x.isIntersecting)) { io.disconnect(); boot(); }
  }, { rootMargin: "300px" });
  io.observe(root);
})();
