// Read-only complete IRQ0 guest path, including chained BIOS instructions.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehouseTimerExecutionSample {
    uint32_t address;int32_t budget,left,maximum;int64_t io;
    uint32_t ticks,parts_left,lines_done,flags;double milliseconds;
    uint16_t sp,ss,ds,es,ax,bx,cx,dx,si,di,bp;
};
struct TreehouseTimerExecutionRow {
    uint32_t ordinal,count,stack_low,bios_address,user_address;
    uint16_t data_segment,entry_ss,entry_sp;
    float video_delays[5];uint32_t parts_total,parts_lines,lines_total;
    uint8_t bios_code[64],user_code[64];
    TreehouseTimerExecutionSample samples[4096];
    uint8_t before[0xb0000],after[0xb0000];
};
static uint32_t treehouse_timer_execution_base=0,treehouse_timer_execution_count=0,treehouse_timer_execution_total=0,treehouse_timer_execution_error=0;
static bool treehouse_timer_execution_active=false;
static TreehouseTimerExecutionRow treehouse_timer_execution_current,treehouse_timer_execution_rows[8];
static INLINE void TreehouseTimerExecutionInstruction(uint32_t address){
    if(!treehouse_timer_execution_base)return;const unsigned offset=address-treehouse_timer_execution_base;
    if(offset==0x6447){
        if(treehouse_timer_execution_active){treehouse_timer_execution_error=1;return;}
        TreehouseTimerExecutionRow& r=treehouse_timer_execution_current;memset(&r,0,sizeof(r));treehouse_timer_execution_active=true;
        r.ordinal=treehouse_timer_execution_total++;r.entry_ss=SegValue(ss);r.entry_sp=reg_sp;r.stack_low=reg_sp;r.data_segment=mem_readw(treehouse_timer_execution_base+0x644b);
        const uint32_t data=16*r.data_segment;r.bios_address=mem_readw(data+0x202a)+16*mem_readw(data+0x202c);r.user_address=mem_readw(0x70)+16*mem_readw(0x72);
        MEM_BlockRead(r.bios_address,r.bios_code,64);MEM_BlockRead(r.user_address,r.user_code,64);
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;MEM_BlockRead(0,r.before,sizeof(r.before));
    }
    if(!treehouse_timer_execution_active||treehouse_timer_execution_error)return;TreehouseTimerExecutionRow& r=treehouse_timer_execution_current;
    if(SegValue(ss)!=r.entry_ss){treehouse_timer_execution_error=2;return;}if(reg_sp<r.stack_low)r.stack_low=reg_sp;
    if(r.count>=4096){treehouse_timer_execution_error=3;return;}TreehouseTimerExecutionSample& s=r.samples[r.count++];
    s.address=address;s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.io=CPU_IODelayRemoved;s.ticks=PIC_Ticks;s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;s.flags=reg_flags;s.milliseconds=PIC_FullIndex();
    s.sp=reg_sp;s.ss=SegValue(ss);s.ds=SegValue(ds);s.es=SegValue(es);s.ax=reg_ax;s.bx=reg_bx;s.cx=reg_cx;s.dx=reg_dx;s.si=reg_si;s.di=reg_di;s.bp=reg_bp;
    if(offset==0x6487){
        if(reg_sp!=r.entry_sp){treehouse_timer_execution_error=4;return;}MEM_BlockRead(0,r.after,sizeof(r.after));
        if(treehouse_timer_execution_count>=8){treehouse_timer_execution_error=5;return;}
        treehouse_timer_execution_rows[treehouse_timer_execution_count++]=r;treehouse_timer_execution_active=false;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_timer_execution_size(void){return sizeof(TreehouseTimerExecutionRow);}
extern "C" RETRO_API unsigned retro_treehouse_timer_execution_status(void){return treehouse_timer_execution_error;}
extern "C" RETRO_API unsigned retro_treehouse_timer_execution_partial(void){return treehouse_timer_execution_active?1:0;}
extern "C" RETRO_API void retro_treehouse_timer_execution_configure(uint32_t base){treehouse_timer_execution_base=base;treehouse_timer_execution_count=treehouse_timer_execution_total=treehouse_timer_execution_error=0;treehouse_timer_execution_active=false;}
extern "C" RETRO_API unsigned retro_treehouse_timer_execution_read(TreehouseTimerExecutionRow* out,unsigned capacity){
    unsigned n=treehouse_timer_execution_count<capacity?treehouse_timer_execution_count:capacity;memcpy(out,treehouse_timer_execution_rows,n*sizeof(TreehouseTimerExecutionRow));treehouse_timer_execution_count-=n;
    if(treehouse_timer_execution_count)memmove(treehouse_timer_execution_rows,treehouse_timer_execution_rows+n,treehouse_timer_execution_count*sizeof(TreehouseTimerExecutionRow));return n;
}
