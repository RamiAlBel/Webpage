#!/bin/bash
# Build Quirky2000 for the browser -> ../../quirky/quirky.wasm (+ net and book copied next to it).
#   needs: python3 -m pip install ziglang==0.14.1   (zig c++ targets wasm32-wasi with libc++)
#   QK_SRC=/path/to/Quirky2000 ./build.sh   (default: clone github.com/RamiAlBel/Quirky2000 into .cache)
set -e
cd "$(dirname "$0")"
HERE=$(pwd); OUT=$HERE/../../quirky; CACHE=$HERE/.cache
mkdir -p "$CACHE" "$OUT"
QK_SRC=${QK_SRC:-$CACHE/Quirky2000}
[ -d "$QK_SRC/engine" ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 https://github.com/RamiAlBel/Quirky2000 "$QK_SRC"
[ -d "$CACHE/simde" ] || git clone -q --depth 1 https://github.com/simd-everywhere/simde.git "$CACHE/simde"
[ -d "$CACHE/fathom" ] || git clone -q --depth 1 https://github.com/jdart1/Fathom "$CACHE/fathom"
ZIG="python3 -m ziglang"
E=$QK_SRC/engine
COMMON="-target wasm32-wasi -O3 -msimd128 -DNDEBUG -w -I$HERE/compat -I$CACHE/simde -I$CACHE/fathom/src -I$E"
CXX="$COMMON -std=c++17 -fno-exceptions -DNNUE_LNN2 -DACC_WIDTH=512 -D_WASI_EMULATED_SIGNAL"
OBJ=$CACHE/obj; mkdir -p "$OBJ"
for f in search position; do $ZIG c++ $CXX -c "$E/$f.cpp" -o "$OBJ/$f.o"; done
for f in nnue nnue_small book; do $ZIG c++ $CXX -include "$HERE/compat/qk_fopen.h" -c "$E/$f.cpp" -o "$OBJ/$f.o"; done
$ZIG c++ $CXX -c wasm_api.cpp -o "$OBJ/wasm_api.o"
$ZIG cc $COMMON -c compat/tbstub.c -o "$OBJ/tbstub.o"
$ZIG c++ $CXX -mexec-model=reactor -rdynamic -Wl,--strip-all \
    "$OBJ"/*.o -o "$OUT/quirky.wasm"
cp "$QK_SRC/weights/W512_sf.nnue" "$OUT/net.nnue"
cp "$QK_SRC/assets/book_jul2200.bin" "$OUT/book.bin"
ls -la "$OUT"
