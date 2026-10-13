// Read-only IRQ7/IRQ12 guest execution, including BIOS/user callbacks.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
extern "C" void TreehouseReadSoundHardware(uint32_t* out);
extern "C" void TreehouseReadMouseHardware(uint32_t* out);
struct TreehouseDeviceExecutionSample {
    uint32_t address;int32_t budget,left,maximum;int64_t io;
    uint32_t ticks,parts_left,lines_done,flags;double milliseconds;
    uint16_t sp,ss,ds,es,cs,ax,bx,cx,dx,si,di,bp;uint8_t code[8];
};
struct TreehouseDeviceExecutionRow {
    uint32_t ordinal,vector,count,stack_low,entry_address;
    uint16_t data_segment,entry_ss,entry_sp;
    float video_delays[5];uint32_t parts_total,parts_lines,lines_total;
    uint32_t hardware_before[32],hardware_after[32];
    uint32_t mouse_before[96],mouse_after[96];
    TreehouseDeviceExecutionSample samples[32768];
    uint8_t before[0xb0000],after[0xb0000];
};
static uint32_t treehouse_device_execution_base=0,treehouse_device_execution_count=0,treehouse_device_execution_total=0,treehouse_device_execution_error=0;
static bool treehouse_device_execution_active=false;
static TreehouseDeviceExecutionRow treehouse_device_execution_current,treehouse_device_execution_rows[8];
static INLINE void TreehouseDeviceExecutionInstruction(uint32_t address){
    if(!treehouse_device_execution_base)return;
    if(!treehouse_device_execution_active){
        unsigned vector=0;const unsigned vectors[]={15,0x74};
        for(unsigned i=0;i<2;i++){unsigned v=vectors[i];if(address==mem_readw(4*v)+16*mem_readw(4*v+2)){vector=v;break;}}
        if(!vector)return;
        TreehouseDeviceExecutionRow& r=treehouse_device_execution_current;memset(&r,0,sizeof(r));treehouse_device_execution_active=true;
        r.ordinal=treehouse_device_execution_total++;r.vector=vector;r.entry_address=address;r.entry_ss=SegValue(ss);r.entry_sp=reg_sp;r.stack_low=reg_sp;r.data_segment=mem_readw(treehouse_device_execution_base+0x644b);
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;TreehouseReadSoundHardware(r.hardware_before);TreehouseReadMouseHardware(r.mouse_before);MEM_BlockRead(0,r.before,sizeof(r.before));
    }
    if(treehouse_device_execution_error)return;TreehouseDeviceExecutionRow& r=treehouse_device_execution_current;
    if(SegValue(ss)!=r.entry_ss){treehouse_device_execution_error=2;return;}if(reg_sp<r.stack_low)r.stack_low=reg_sp;
    if(r.count>=32768){treehouse_device_execution_error=3;return;}TreehouseDeviceExecutionSample& s=r.samples[r.count++];
    s.address=address;s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.io=CPU_IODelayRemoved;s.ticks=PIC_Ticks;s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;s.flags=reg_flags;s.milliseconds=PIC_FullIndex();
    s.sp=reg_sp;s.ss=SegValue(ss);s.ds=SegValue(ds);s.es=SegValue(es);s.cs=SegValue(cs);s.ax=reg_ax;s.bx=reg_bx;s.cx=reg_cx;s.dx=reg_dx;s.si=reg_si;s.di=reg_di;s.bp=reg_bp;MEM_BlockRead(address,s.code,8);
    if(s.code[0]==0xcf&&reg_sp==r.entry_sp){
        TreehouseReadSoundHardware(r.hardware_after);TreehouseReadMouseHardware(r.mouse_after);MEM_BlockRead(0,r.after,sizeof(r.after));if(treehouse_device_execution_count>=8){treehouse_device_execution_error=5;return;}
        treehouse_device_execution_rows[treehouse_device_execution_count++]=r;treehouse_device_execution_active=false;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_device_execution_size(void){return sizeof(TreehouseDeviceExecutionRow);}
extern "C" RETRO_API unsigned retro_treehouse_device_execution_status(void){return treehouse_device_execution_error;}
extern "C" RETRO_API unsigned retro_treehouse_device_execution_partial(void){return treehouse_device_execution_active?1:0;}
extern "C" RETRO_API void retro_treehouse_device_execution_configure(uint32_t base){treehouse_device_execution_base=base;treehouse_device_execution_count=treehouse_device_execution_total=treehouse_device_execution_error=0;treehouse_device_execution_active=false;}
extern "C" RETRO_API unsigned retro_treehouse_device_execution_read(TreehouseDeviceExecutionRow* out,unsigned capacity){
    unsigned n=treehouse_device_execution_count<capacity?treehouse_device_execution_count:capacity;memcpy(out,treehouse_device_execution_rows,n*sizeof(TreehouseDeviceExecutionRow));treehouse_device_execution_count-=n;
    if(treehouse_device_execution_count)memmove(treehouse_device_execution_rows,treehouse_device_execution_rows+n,treehouse_device_execution_count*sizeof(TreehouseDeviceExecutionRow));return n;
}
