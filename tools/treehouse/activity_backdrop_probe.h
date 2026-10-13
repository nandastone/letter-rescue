// Read-only main 4E15 backdrop callback, including the overlay and temporary surface.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
extern "C" void TreehouseReadSoundHardware(uint32_t* out);
extern "C" uint32_t TreehouseReadSoundDmaAutoInit(void);
struct TreehouseActivityBackdropSample {
    uint32_t address;int32_t budget,left,maximum;int64_t io;
    uint32_t ticks,parts_left,lines_done,flags;double milliseconds;
    uint16_t sp,ss,ds,es,cs,ax,bx,cx,dx,si,di,bp;uint8_t code[8];
};
struct TreehouseActivityBackdropRow {
    uint32_t ordinal,attribute,count,stack_low,entry_address;
    uint16_t data_segment,entry_ss,entry_sp;
    float video_delays[5];uint32_t parts_total,parts_lines,lines_total;
    uint32_t hardware_before[32],hardware_after[32];
    uint32_t dma_autoinit_before,dma_autoinit_after;
    TreehouseActivityBackdropSample samples[262144];
    uint32_t checkpoint_count,checkpoint_instruction[8],checkpoint_address[8];
    uint8_t checkpoint_ram[8][0xb0000];
    uint8_t before[0xb0000],after[0xb0000];
};
static uint32_t treehouse_activity_backdrop_target=0,treehouse_activity_backdrop_base=0,treehouse_activity_backdrop_count=0,treehouse_activity_backdrop_total=0,treehouse_activity_backdrop_error=0;
static bool treehouse_activity_backdrop_active=false;
static TreehouseActivityBackdropRow treehouse_activity_backdrop_current,treehouse_activity_backdrop_rows[8];
static INLINE void TreehouseActivityBackdropInstruction(uint32_t address){
    if(!treehouse_activity_backdrop_base)return;
    if(!treehouse_activity_backdrop_active){
        if(address!=treehouse_activity_backdrop_base+0x4e15)return;
        
        TreehouseActivityBackdropRow& r=treehouse_activity_backdrop_current;memset(&r,0,sizeof(r));treehouse_activity_backdrop_active=true;
        r.ordinal=treehouse_activity_backdrop_total++;r.attribute=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+4));r.entry_address=address;r.entry_ss=SegValue(ss);r.entry_sp=reg_sp;r.stack_low=reg_sp;r.data_segment=mem_readw(treehouse_activity_backdrop_base+0xd510+0x644b);
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;TreehouseReadSoundHardware(r.hardware_before);r.dma_autoinit_before=TreehouseReadSoundDmaAutoInit();MEM_BlockRead(0,r.before,sizeof(r.before));
    }
    if(treehouse_activity_backdrop_error)return;TreehouseActivityBackdropRow& r=treehouse_activity_backdrop_current;
    if(SegValue(ss)!=r.entry_ss){treehouse_activity_backdrop_error=2;return;}if(reg_sp<r.stack_low)r.stack_low=reg_sp;
    const uint32_t resident=treehouse_activity_backdrop_base+0xd510;
    if(address==resident+0x6b06||address==resident+0x6bb2||address==resident+0x7d9f||address==treehouse_activity_backdrop_base+0x4e52){
        if(r.checkpoint_count>=8){treehouse_activity_backdrop_error=6;return;}
        const unsigned n=r.checkpoint_count++;r.checkpoint_instruction[n]=r.count;r.checkpoint_address[n]=address;MEM_BlockRead(0,r.checkpoint_ram[n],0xb0000);
    }
    if(r.count>=262144){treehouse_activity_backdrop_error=3;return;}TreehouseActivityBackdropSample& s=r.samples[r.count++];
    s.address=address;s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.io=CPU_IODelayRemoved;s.ticks=PIC_Ticks;s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;s.flags=reg_flags;s.milliseconds=PIC_FullIndex();
    s.sp=reg_sp;s.ss=SegValue(ss);s.ds=SegValue(ds);s.es=SegValue(es);s.cs=SegValue(cs);s.ax=reg_ax;s.bx=reg_bx;s.cx=reg_cx;s.dx=reg_dx;s.si=reg_si;s.di=reg_di;s.bp=reg_bp;MEM_BlockRead(address,s.code,8);
    if(address==treehouse_activity_backdrop_base+0x4e9b&&reg_sp==r.entry_sp){
        TreehouseReadSoundHardware(r.hardware_after);r.dma_autoinit_after=TreehouseReadSoundDmaAutoInit();MEM_BlockRead(0,r.after,sizeof(r.after));if(treehouse_activity_backdrop_count>=8){treehouse_activity_backdrop_error=5;return;}
        treehouse_activity_backdrop_rows[treehouse_activity_backdrop_count++]=r;treehouse_activity_backdrop_active=false;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_activity_backdrop_size(void){return sizeof(TreehouseActivityBackdropRow);}
extern "C" RETRO_API unsigned retro_treehouse_activity_backdrop_status(void){return treehouse_activity_backdrop_error;}
extern "C" RETRO_API unsigned retro_treehouse_activity_backdrop_partial(void){return treehouse_activity_backdrop_active?1:0;}
extern "C" RETRO_API void retro_treehouse_activity_backdrop_configure(uint32_t base,uint32_t attribute){treehouse_activity_backdrop_target=attribute;treehouse_activity_backdrop_base=base;treehouse_activity_backdrop_count=treehouse_activity_backdrop_total=treehouse_activity_backdrop_error=0;treehouse_activity_backdrop_active=false;}
extern "C" RETRO_API unsigned retro_treehouse_activity_backdrop_read(TreehouseActivityBackdropRow* out,unsigned capacity){
    unsigned n=treehouse_activity_backdrop_count<capacity?treehouse_activity_backdrop_count:capacity;memcpy(out,treehouse_activity_backdrop_rows,n*sizeof(TreehouseActivityBackdropRow));treehouse_activity_backdrop_count-=n;
    if(treehouse_activity_backdrop_count)memmove(treehouse_activity_backdrop_rows,treehouse_activity_backdrop_rows+n,treehouse_activity_backdrop_count*sizeof(TreehouseActivityBackdropRow));return n;
}
