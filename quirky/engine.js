// Quirky2000 engine worker: loads quirky.wasm (built by tools/quirky-web/build.sh) with its net
// and opening book, then answers {id, cmd, ...} messages. Everything runs in the visitor's browser.
// Also loadable from Node for testing: createEngine(bytes, net, book).
"use strict";

function createEngine(wasmBytes, netBytes, bookBytes) {
  let mem = null;
  const u8 = () => new Uint8Array(mem.buffer);
  const dv = () => new DataView(mem.buffer);
  const t0 = Date.now();
  let log = "";
  const ENOSYS = 52, EBADF = 8;
  // minimal WASI: stdout/stderr, clocks, random. Files come from qk_put_file (fmemopen), not WASI.
  const wasi = {
    environ_get: () => 0,
    environ_sizes_get: (pc, ps) => { dv().setUint32(pc, 0, true); dv().setUint32(ps, 0, true); return 0; },
    clock_time_get: (id, prec, out) => {
      const ns = BigInt(Math.round((typeof performance !== "undefined" ? performance.now() : Date.now() - t0) * 1e6));
      dv().setBigUint64(out, ns, true); return 0;
    },
    fd_close: () => 0,
    fd_fdstat_get: (fd, out) => {
      if (fd > 2) return EBADF;
      const d = dv(); d.setUint8(out, 2); d.setUint16(out + 2, 0, true);
      d.setBigUint64(out + 8, 0xffffffffn, true); d.setBigUint64(out + 16, 0xffffffffn, true); return 0;
    },
    fd_prestat_get: () => EBADF,
    fd_prestat_dir_name: () => EBADF,
    fd_seek: () => ENOSYS,
    fd_write: (fd, iovs, n, nw) => {
      const d = dv(); let total = 0;
      for (let i = 0; i < n; i++) {
        const p = d.getUint32(iovs + 8 * i, true), l = d.getUint32(iovs + 8 * i + 4, true);
        log += new TextDecoder().decode(u8().subarray(p, p + l)); total += l;
      }
      if (log.length > 4096) log = log.slice(-2048);
      d.setUint32(nw, total, true); return 0;
    },
    proc_exit: (c) => { throw new Error("engine exited " + c); },
    random_get: (p, l) => {
      const b = u8().subarray(p, p + l);
      if (typeof crypto !== "undefined" && crypto.getRandomValues) crypto.getRandomValues(b);
      else for (let i = 0; i < l; i++) b[i] = (Math.random() * 256) | 0;
      return 0;
    },
  };
  const inst = new WebAssembly.Instance(new WebAssembly.Module(wasmBytes), { wasi_snapshot_preview1: wasi });
  const X = inst.exports;
  mem = X.memory;
  X._initialize();

  const cstr = (s) => {
    const b = new TextEncoder().encode(s + "\0"), p = X.qk_alloc(b.length);
    u8().set(b, p); return p;
  };
  const read = (p) => { const a = u8(); let e = p; while (a[e]) e++; return new TextDecoder().decode(a.subarray(p, e)); };
  const call = (fn, s, ...rest) => { const p = cstr(s); try { return fn(p, ...rest); } finally { X.qk_free(p); } };
  const put = (name, bytes) => {
    if (!bytes) return;
    const p = X.qk_alloc(bytes.length);
    u8().set(bytes, p);
    call(X.qk_put_file, name, p, bytes.length);
    X.qk_free(p);
  };

  put("net.nnue", netBytes);
  put("book.bin", bookBytes);
  const ok = X.qk_init(16);
  if (!ok) throw new Error("could not load the network: " + log);

  return {
    book: ok === 2,
    newGame: () => X.qk_new_game(),
    fen: () => read(X.qk_fen()),
    legal: () => { const s = read(X.qk_legal()); return s ? s.split(" ") : []; },
    play: (m) => call(X.qk_play, m) === 1,
    setMoves: (moves) => call(X.qk_undo, moves.join(" ")) === 1,
    inCheck: () => X.qk_in_check() === 1,
    status: () => X.qk_status(),
    think: (nodes, bookPlies) => ({ move: read(X.qk_think(nodes, bookPlies)), score: X.qk_score() }),
  };
}

if (typeof module !== "undefined") module.exports = { createEngine };

// ---- Web Worker side ----
if (typeof self !== "undefined" && typeof WorkerGlobalScope !== "undefined" && self instanceof WorkerGlobalScope) {
  let eng = null;
  const state = () => ({ fen: eng.fen(), legal: eng.legal(), status: eng.status(), check: eng.inCheck() });
  const ready = (async () => {
    const get = async (u) => new Uint8Array(await (await fetch(u)).arrayBuffer());
    const [w, n, b] = await Promise.all([get("quirky.wasm"), get("net.nnue"), get("book.bin").catch(() => null)]);
    eng = createEngine(w, n, b);
  })();
  self.onmessage = async (e) => {
    const { id, cmd } = e.data;
    try {
      await ready;
      let res = {};
      if (cmd === "new") { eng.newGame(); res = state(); }
      else if (cmd === "state") res = state();
      else if (cmd === "set") { eng.setMoves(e.data.moves); res = state(); }
      else if (cmd === "play") { res = { ok: eng.play(e.data.move), ...state() }; }
      else if (cmd === "think") {
        const t = performance.now();
        const r = eng.think(e.data.nodes, e.data.bookPlies);
        res = { ...r, ms: Math.round(performance.now() - t) };
      }
      self.postMessage({ id, ok: true, ...res });
    } catch (err) {
      self.postMessage({ id, ok: false, error: String(err && err.message || err) });
    }
  };
}
