// Web build: fopen() of a registered name returns a read-only stream over a memory blob (fmemopen).
#pragma once
#include <cstdio>
FILE* qk_fopen(const char* path, const char* mode);
#define fopen qk_fopen
