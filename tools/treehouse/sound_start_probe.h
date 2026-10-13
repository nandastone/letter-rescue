// Read-only resident E5E2 sound starts, including cached preparation and driver calls.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
extern "C" void TreehouseReadSoundHardware(uint32_t* out);
extern "C" uint32_t TreehouseReadSoundDmaAutoInit(void);
struct TreehouseSoundStartSample {
    uint32_t address;int32_t budget,left,maximum;int64_t io;
    uint32_t ticks,parts_left,lines_done,flags;double milliseconds;
    uint16_t sp,ss,ds,es,cs,ax,bx,cx,dx,si,di,bp;uint8_t code[8];
};
struct TreehouseSoundStartRow {
    uint32_t ordinal,sound_id,count,stack_low,entry_address;
    uint16_t data_segment,entry_ss,entry_sp;
    float video_delays[5];uint32_t parts_total,parts_lines,lines_total;
    uint32_t hardware_before[32],hardware_after[32];
    uint32_t dma_autoinit_before,dma_autoinit_after;
    TreehouseSoundStartSample samples[32768];
    uint8_t before[0xb0000],after[0xb0000];
};
static uint32_t treehouse_sound_start_target=0,treehouse_sound_start_base=0,treehouse_sound_start_count=0,treehouse_sound_start_total=0,treehouse_sound_start_error=0;
static bool treehouse_sound_start_active=false;
static TreehouseSoundStartRow treehouse_sound_start_current,treehouse_sound_start_rows[8];
static INLINE void TreehouseSoundStartInstruction(uint32_t address){
    if(!treehouse_sound_start_base)return;
    if(!treehouse_sound_start_active){
        if(address!=treehouse_sound_start_base+0xe5e2)return;
        if(treehouse_sound_start_target&&mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+4))!=treehouse_sound_start_target)return;
        TreehouseSoundStartRow& r=treehouse_sound_start_current;memset(&r,0,sizeof(r));treehouse_sound_start_active=true;
        r.ordinal=treehouse_sound_start_total++;r.sound_id=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+4));r.entry_address=address;r.entry_ss=SegValue(ss);r.entry_sp=reg_sp;r.stack_low=reg_sp;r.data_segment=mem_readw(treehouse_sound_start_base+0x644b);
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;TreehouseReadSoundHardware(r.hardware_before);r.dma_autoinit_before=TreehouseReadSoundDmaAutoInit();MEM_BlockRead(0,r.before,sizeof(r.before));
    }
    if(treehouse_sound_start_error)return;TreehouseSoundStartRow& r=treehouse_sound_start_current;
    if(SegValue(ss)!=r.entry_ss){treehouse_sound_start_error=2;return;}if(reg_sp<r.stack_low)r.stack_low=reg_sp;
    if(r.count>=32768){treehouse_sound_start_error=3;return;}TreehouseSoundStartSample& s=r.samples[r.count++];
    s.address=address;s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.io=CPU_IODelayRemoved;s.ticks=PIC_Ticks;s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;s.flags=reg_flags;s.milliseconds=PIC_FullIndex();
    s.sp=reg_sp;s.ss=SegValue(ss);s.ds=SegValue(ds);s.es=SegValue(es);s.cs=SegValue(cs);s.ax=reg_ax;s.bx=reg_bx;s.cx=reg_cx;s.dx=reg_dx;s.si=reg_si;s.di=reg_di;s.bp=reg_bp;MEM_BlockRead(address,s.code,8);
    if(address==treehouse_sound_start_base+0xe5f6&&reg_sp==r.entry_sp){
        TreehouseReadSoundHardware(r.hardware_after);r.dma_autoinit_after=TreehouseReadSoundDmaAutoInit();MEM_BlockRead(0,r.after,sizeof(r.after));if(treehouse_sound_start_count>=8){treehouse_sound_start_error=5;return;}
        treehouse_sound_start_rows[treehouse_sound_start_count++]=r;treehouse_sound_start_active=false;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_sound_start_size(void){return sizeof(TreehouseSoundStartRow);}
extern "C" RETRO_API unsigned retro_treehouse_sound_start_status(void){return treehouse_sound_start_error;}
extern "C" RETRO_API unsigned retro_treehouse_sound_start_partial(void){return treehouse_sound_start_active?1:0;}
extern "C" RETRO_API void retro_treehouse_sound_start_configure(uint32_t base,uint32_t sound_id){treehouse_sound_start_target=sound_id;treehouse_sound_start_base=base;treehouse_sound_start_count=treehouse_sound_start_total=treehouse_sound_start_error=0;treehouse_sound_start_active=false;}
extern "C" RETRO_API unsigned retro_treehouse_sound_start_read(TreehouseSoundStartRow* out,unsigned capacity){
    unsigned n=treehouse_sound_start_count<capacity?treehouse_sound_start_count:capacity;memcpy(out,treehouse_sound_start_rows,n*sizeof(TreehouseSoundStartRow));treehouse_sound_start_count-=n;
    if(treehouse_sound_start_count)memmove(treehouse_sound_start_rows,treehouse_sound_start_rows+n,treehouse_sound_start_count*sizeof(TreehouseSoundStartRow));return n;
}
