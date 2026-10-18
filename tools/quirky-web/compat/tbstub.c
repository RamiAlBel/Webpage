/* Web build: no Syzygy tablebases. */
#include <stdbool.h>
#include <stdint.h>
unsigned TB_LARGEST = 0;
bool tb_init_impl(const char* p) { (void)p; return false; }
bool tb_init(const char* p) { (void)p; return false; }
void tb_free(void) {}
unsigned tb_probe_wdl_impl(uint64_t a, uint64_t b, uint64_t c, uint64_t d, uint64_t e, uint64_t f, uint64_t g,
                           uint64_t h, unsigned ep, bool t) { return 0xFFFFFFFF; }
unsigned tb_probe_root_impl(uint64_t a, uint64_t b, uint64_t c, uint64_t d, uint64_t e, uint64_t f, uint64_t g,
                            uint64_t h, unsigned r50, unsigned ep, bool t, unsigned* res) { return 0xFFFFFFFF; }
