// Web build: AVX2/FMA intrinsics mapped to portable code (WebAssembly SIMD128) by SIMDe.
#pragma once
#define SIMDE_ENABLE_NATIVE_ALIASES
#include <simde/x86/avx2.h>
#include <simde/x86/fma.h>
#include <stdint.h>
static inline unsigned long long _tzcnt_u64(unsigned long long b) { return b ? __builtin_ctzll(b) : 64; }
static inline long long _mm_popcnt_u64(unsigned long long b) { return __builtin_popcountll(b); }
static inline int _mm_popcnt_u32(unsigned b) { return __builtin_popcount(b); }
static inline unsigned _tzcnt_u32(unsigned b) { return b ? __builtin_ctz(b) : 32; }
static inline unsigned long long _lzcnt_u64(unsigned long long b) { return b ? __builtin_clzll(b) : 64; }
