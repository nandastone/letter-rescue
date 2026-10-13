// Read-only completed resident:58E2 polling calls and selected instruction counts.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
extern void TreehouseCpuProbeContext(uint64_t* values);
struct TreehousePollCpu {
    uint64_t context[5];
    int64_t io;
    int32_t cycles,left,maximum;
    uint32_t ticks,flags;
    uint16_t cs,ss,sp,bp,stack[16],caller[16];
};
struct TreehousePollState {
    uint16_t mouse_present,joystick,modifier,edges[2],bindings[96];
    uint8_t keys[96],latches[96];
};
struct TreehousePollRow {
    double begin,end;
    uint32_t ordinal,path_hash;
    uint32_t gap_count,gap_hash,gap_addresses[256];
    uint16_t result,mouse_count,mouse_buttons[2];
    TreehousePollCpu cpu_before,cpu_after;
    TreehousePollState before,after;
    uint32_t counts[512];
};
static uint32_t treehouse_poll_base=0,treehouse_poll_count=0,treehouse_poll_total=0,treehouse_poll_error=0;
static uint16_t treehouse_poll_map[0x100000];
static TreehousePollRow treehouse_poll_rows[2048],treehouse_poll_current;
static bool treehouse_poll_active=false;
static uint32_t treehouse_poll_gap_count=0,treehouse_poll_gap_hash=2166136261u,treehouse_poll_gap_addresses[256];
struct TreehousePollGapCount {uint32_t ordinal,address,entries;};
static uint32_t treehouse_poll_gap_work[0x100000],treehouse_poll_gap_dirty[65536],treehouse_poll_gap_used=0,treehouse_poll_gap_row_count=0;
static TreehousePollGapCount treehouse_poll_gap_rows[65536];
static void TreehousePollCpuRead(TreehousePollCpu& s){
    TreehouseCpuProbeContext(s.context);s.io=CPU_IODelayRemoved;s.cycles=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.ticks=PIC_Ticks;s.flags=reg_flags;
    s.cs=SegValue(cs);s.ss=SegValue(ss);s.sp=reg_sp;s.bp=reg_bp;
    for(unsigned i=0;i<16;++i)s.stack[i]=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+2*i));
    const PhysPt dataSegment=SegPhys(ds);const uint16_t player=mem_readw(dataSegment+0x5250);
    for(unsigned i=0;i<4;++i)s.caller[i]=mem_readw(dataSegment+0x2016+2*i);
    s.caller[4]=mem_readw(dataSegment+0x55ec);s.caller[5]=mem_readw(mem_readw(dataSegment+0x49e6)*16+0x9d8);
    s.caller[6]=player;s.caller[7]=mem_readw(dataSegment + 0x529e);s.caller[8]=mem_readw(dataSegment + 0x52ee + 2*player);
    s.caller[9]=mem_readb(mem_readw(dataSegment+0x4ad0)*16+0x992+2*player);
    s.caller[10]=mem_readw(dataSegment+0x211c);s.caller[11]=mem_readw(dataSegment+0x2132);s.caller[12]=mem_readw(dataSegment+0x2144);
    s.caller[13]=mem_readb(dataSegment+0x211b);s.caller[14]=mem_readw(dataSegment+0x5698);s.caller[15]=mem_readw(dataSegment+0x2068);
}
static void TreehousePollStateRead(TreehousePollState& s){
    PhysPt dataSegment=SegPhys(ds),keyboard=mem_readw(dataSegment+0x4af6)*16,keys=mem_readw(dataSegment+0x4afe)*16,mouse=mem_readw(dataSegment+0x4b04)*16;
    s.mouse_present=mem_readw(dataSegment+0x2068);s.joystick=mem_readw(mem_readw(dataSegment+0x4afc)*16+0x9aa);s.modifier=mem_readb(0x417);
    for(unsigned i=0;i<2;++i)s.edges[i]=mem_readw(mouse + 0xa8e + 2*i);
    for(unsigned i=0;i<96;++i){s.keys[i]=mem_readb(dataSegment + 0x157e + i);s.latches[i]=mem_readb(keys + 0xa2a + i);s.bindings[i]=mem_readw(keyboard + 0x95 + 2*i);}
}
static INLINE void TreehousePollInstruction(uint32_t address){
    if(!treehouse_poll_base)return;
    if(address==treehouse_poll_base+0x58e2){
        if(treehouse_poll_active){treehouse_poll_error=1;return;}
        treehouse_poll_active=true;memset(&treehouse_poll_current,0,sizeof(treehouse_poll_current));
        for(unsigned i=0;i<treehouse_poll_gap_used;++i){
            const uint32_t a=treehouse_poll_gap_dirty[i];
            if(treehouse_poll_gap_count>1024){
                if(treehouse_poll_gap_row_count>=65536)treehouse_poll_error=1;
                else {TreehousePollGapCount& r=treehouse_poll_gap_rows[treehouse_poll_gap_row_count++];r.ordinal=treehouse_poll_total;r.address=a;r.entries=treehouse_poll_gap_work[a];}
            }
            treehouse_poll_gap_work[a]=0;
        }
        treehouse_poll_gap_used=0;
        treehouse_poll_current.gap_count=treehouse_poll_gap_count;treehouse_poll_current.gap_hash=treehouse_poll_gap_hash;memcpy(treehouse_poll_current.gap_addresses,treehouse_poll_gap_addresses,sizeof(treehouse_poll_gap_addresses));
        treehouse_poll_gap_count=0;treehouse_poll_gap_hash=2166136261u;TreehousePollCpuRead(treehouse_poll_current.cpu_before);
        treehouse_poll_current.ordinal=treehouse_poll_total++;treehouse_poll_current.path_hash=2166136261u;treehouse_poll_current.begin=PIC_FullIndex();TreehousePollStateRead(treehouse_poll_current.before);
    }
    if(!treehouse_poll_active){
        if(address>=0x100000)treehouse_poll_error=1;
        else {
            if(!treehouse_poll_gap_work[address]){
                if(treehouse_poll_gap_used>=65536)treehouse_poll_error=1;
                else treehouse_poll_gap_dirty[treehouse_poll_gap_used++]=address;
            }
            ++treehouse_poll_gap_work[address];
        }
        if(treehouse_poll_gap_count<256)treehouse_poll_gap_addresses[treehouse_poll_gap_count]=address;
        ++treehouse_poll_gap_count;
        for(unsigned shift=0;shift<32;shift+=8)treehouse_poll_gap_hash=(treehouse_poll_gap_hash^((address>>shift)&255))*16777619u;
        return;
    }
    if(address<0x100000){unsigned slot=treehouse_poll_map[address];if(slot){
        ++treehouse_poll_current.counts[slot-1];
        for(unsigned shift=0;shift<32;shift+=8)treehouse_poll_current.path_hash=(treehouse_poll_current.path_hash^(((slot-1)>>shift)&255))*16777619u;
    }}
    if(address==treehouse_poll_base+0x54d5){
        unsigned n=treehouse_poll_current.mouse_count++;
        if(n<2)treehouse_poll_current.mouse_buttons[n]=reg_bx;else treehouse_poll_error=1;
    }
    if(address==treehouse_poll_base+0x5993){
        treehouse_poll_current.end=PIC_FullIndex();treehouse_poll_current.result=reg_ax;TreehousePollStateRead(treehouse_poll_current.after);TreehousePollCpuRead(treehouse_poll_current.cpu_after);
        if(treehouse_poll_count>=2048)treehouse_poll_error=1;else treehouse_poll_rows[treehouse_poll_count++]=treehouse_poll_current;
        treehouse_poll_active=false;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_poll_size(void){return sizeof(TreehousePollRow);}
extern "C" RETRO_API unsigned retro_treehouse_poll_status(void){return treehouse_poll_error;}
extern "C" RETRO_API unsigned retro_treehouse_poll_partial(void){return treehouse_poll_active?1:0;}
extern "C" RETRO_API void retro_treehouse_poll_configure(uint32_t base,const uint32_t* addresses,unsigned count){
    treehouse_poll_base=base;treehouse_poll_count=treehouse_poll_total=treehouse_poll_error=0;treehouse_poll_active=false;memset(treehouse_poll_map,0,sizeof(treehouse_poll_map));
    treehouse_poll_gap_count=0;treehouse_poll_gap_hash=2166136261u;memset(treehouse_poll_gap_addresses,0,sizeof(treehouse_poll_gap_addresses));
    treehouse_poll_gap_used=treehouse_poll_gap_row_count=0;memset(treehouse_poll_gap_work,0,sizeof(treehouse_poll_gap_work));
    if(count>512){treehouse_poll_error=1;return;}
    for(unsigned i=0;i<count;++i){if(addresses[i]>=0x100000||treehouse_poll_map[addresses[i]]){treehouse_poll_error=1;return;}treehouse_poll_map[addresses[i]]=i+1;}
}
extern "C" RETRO_API unsigned retro_treehouse_poll_read(TreehousePollRow* rows,unsigned capacity){
    unsigned n=treehouse_poll_count<capacity?treehouse_poll_count:capacity;memcpy(rows,treehouse_poll_rows,n*sizeof(TreehousePollRow));treehouse_poll_count-=n;
    if(treehouse_poll_count)memmove(treehouse_poll_rows,treehouse_poll_rows+n,treehouse_poll_count*sizeof(TreehousePollRow));return n;
}
extern "C" RETRO_API unsigned retro_treehouse_poll_gap_size(void){return sizeof(TreehousePollGapCount);}
extern "C" RETRO_API unsigned retro_treehouse_poll_gap_read(TreehousePollGapCount* rows,unsigned capacity){
    unsigned n=treehouse_poll_gap_row_count<capacity?treehouse_poll_gap_row_count:capacity;memcpy(rows,treehouse_poll_gap_rows,n*sizeof(TreehousePollGapCount));treehouse_poll_gap_row_count-=n;
    if(treehouse_poll_gap_row_count)memmove(treehouse_poll_gap_rows,treehouse_poll_gap_rows+n,treehouse_poll_gap_row_count*sizeof(TreehousePollGapCount));return n;
}
