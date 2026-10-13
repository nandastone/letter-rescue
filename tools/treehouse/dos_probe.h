// Offline, read-only observations of the pinned core's DOS transfer debit.
// Included only in the isolated research DLL's dos.cpp translation unit.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehouseDosTransfer {
    int32_t bytes, cycles_before, cycles_after;
    int64_t io_before, io_after;
};
static bool treehouse_dos_enabled=false;
static unsigned treehouse_dos_count=0,treehouse_dos_error=0;
static TreehouseDosTransfer treehouse_dos_transfers[4096];
extern "C" RETRO_API unsigned retro_treehouse_dos_size(void) { return sizeof(TreehouseDosTransfer); }
extern "C" RETRO_API void retro_treehouse_dos_configure(unsigned enabled) {
    treehouse_dos_enabled=enabled!=0;treehouse_dos_count=treehouse_dos_error=0;
}
extern "C" RETRO_API unsigned retro_treehouse_dos_status(void) { return treehouse_dos_error; }
extern "C" RETRO_API unsigned retro_treehouse_dos_read(TreehouseDosTransfer* out,unsigned capacity) {
    unsigned count=treehouse_dos_count<capacity?treehouse_dos_count:capacity;
    memcpy(out,treehouse_dos_transfers,count*sizeof(TreehouseDosTransfer));return count;
}
static inline void TreehouseObserveDosTransfer(Bits bytes,Bits cycles_before,Bit64s io_before) {
    if(!treehouse_dos_enabled)return;
    if(treehouse_dos_count>=4096){treehouse_dos_error=1;return;}
    TreehouseDosTransfer& row=treehouse_dos_transfers[treehouse_dos_count++];
    row.bytes=bytes;row.cycles_before=cycles_before;row.cycles_after=CPU_Cycles;
    row.io_before=io_before;row.io_after=CPU_IODelayRemoved;
}
