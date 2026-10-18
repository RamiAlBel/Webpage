// Quirky2000 for the browser: a tiny C API over the engine, compiled to WebAssembly.
// The page's Web Worker owns one game: it registers the net (and book) bytes, then
// plays moves and asks for engine moves. Search is single-threaded and node-limited.
#include "position.h"
#include "nnue.h"
#include "search.h"
#include "tune.h"
#include "book.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>
#include <vector>

#define EXPORT extern "C" __attribute__((visibility("default")))

static const char* START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

// ---- in-memory files for fopen() (see compat/qk_fopen.h) ----
static std::map<std::string, std::vector<unsigned char>> Files;
#undef fopen
FILE* qk_fopen(const char* path, const char* mode) {
    auto it = Files.find(path);
    if (it == Files.end() || it->second.empty()) return nullptr;
    return fmemopen(it->second.data(), it->second.size(), "rb");
}

static Position Pos;
static std::vector<uint64_t> Hist;
static std::string Out;
static bool BookOn = false;

EXPORT void* qk_alloc(int n) { return malloc((size_t)n); }
EXPORT void qk_free(void* p) { free(p); }
EXPORT const char* qk_out() { return Out.c_str(); }

// copy n bytes at p into the virtual file `name`
EXPORT int qk_put_file(const char* name, const unsigned char* p, int n) {
    Files[name].assign(p, p + n);
    return n;
}

EXPORT void qk_new_game() {
    Pos.set_fen(START_FEN);
    Hist.assign(1, Pos.key);
    search::clear_hash();
}

EXPORT int qk_init(int hashMb) {
    bb::init();
    // version G search options (experiments/options/G_opts.txt), minus Syzygy and its book
    const char* g = "UseFinny=1 UseLazyAcc=1 UseContHist=1 UseCaptHist=1 UseSingular=1 SingMargin=3 RfpMargin=81 "
                    "RfpImp=24 NmpEvalDiv=196 LmpBase=4 FutBase=99 FutMul=114 SeeQuiet=26 SeeNoisy=99 HistDiv=5715 "
                    "LmrBase=85 LmrDiv=206 AspDelta=17 UseCorr2=1 UseDblExt=1 UseAspFH=1 UseDeeper=1";
    char name[64]; int v; const char* s = g; int k;
    while (sscanf(s, " %63[^=]=%d%n", name, &v, &k) == 2) { set_tunable(name, v); s += k; }
    if (!nnue::load("net.nnue")) return 0;
    search::init();
    search::set_hash_mb((size_t)hashMb);
    BookOn = book::open("book.bin");
    qk_new_game();
    return BookOn ? 2 : 1;
}

EXPORT const char* qk_fen() { Out = Pos.fen(); return Out.c_str(); }

// legal moves of the current position, space separated UCI
EXPORT const char* qk_legal() {
    MoveList l;
    generate_legal(Pos, l);
    Out.clear();
    for (int i = 0; i < l.size; i++) { if (i) Out += ' '; Out += move_to_uci(l.moves[i]); }
    return Out.c_str();
}

EXPORT int qk_play(const char* uci) {
    MoveList l;
    generate_legal(Pos, l);
    Move m = parse_uci_move(Pos, uci);
    for (int i = 0; i < l.size; i++)
        if (l.moves[i] == m) { Pos.do_move(m); Hist.push_back(Pos.key); return 1; }
    return 0;
}

EXPORT int qk_in_check() { return Pos.checkers ? 1 : 0; }

// 0 playing, 1 checkmate, 2 stalemate, 3 fifty-move rule, 4 threefold repetition, 5 insufficient material
EXPORT int qk_status() {
    MoveList l;
    generate_legal(Pos, l);
    if (!l.size) return Pos.checkers ? 1 : 2;
    if (Pos.halfmove >= 100) return 3;
    int rep = 0;
    for (size_t i = 0; i + 1 < Hist.size(); i++) rep += Hist[i] == Pos.key;
    if (rep >= 2) return 4;
    Bitboard minors = 0, other = 0;
    for (int c = 0; c < 2; c++) {
        minors |= Pos.pcs(c, KNIGHT) | Pos.pcs(c, BISHOP);
        other |= Pos.pcs(c, PAWN) | Pos.pcs(c, ROOK) | Pos.pcs(c, QUEEN);
    }
    if (!other && popcount(minors) <= 1) return 5;
    return 0;
}

static int LastScore = 0;
EXPORT int qk_score() { return LastScore; }

// engine move for the current position (not played): book first, then a node-limited search
EXPORT const char* qk_think(int nodes, int bookPlies) {
    Out.clear();
    if (BookOn && (int)Hist.size() - 1 < bookPlies) {
        if (Move bm = book::probe(Pos, false)) { LastScore = 0; Out = move_to_uci(bm); return Out.c_str(); }
    }
    Move best = 0;
    int score = 0;
    search::search_nodes(Pos, Hist, (uint64_t)nodes, best, score);
    LastScore = score;
    if (best) Out = move_to_uci(best);
    return Out.c_str();
}

// undo: replay the game without its last n plies
EXPORT int qk_undo(const char* movesSpaceSeparated) {
    Pos.set_fen(START_FEN);
    Hist.assign(1, Pos.key);
    std::string s = movesSpaceSeparated, tok;
    size_t i = 0;
    while (i < s.size()) {
        size_t j = s.find(' ', i);
        if (j == std::string::npos) j = s.size();
        tok = s.substr(i, j - i);
        if (!tok.empty() && !qk_play(tok.c_str())) return 0;
        i = j + 1;
    }
    return 1;
}
