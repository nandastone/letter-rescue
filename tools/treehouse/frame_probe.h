// Complete main C78A frame call. RAM and instruction paths stay offline.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehouseFrameSample { uint32_t address,remaining;int32_t budget,left,maximum;uint32_t ticks,parts_left,lines_done;double milliseconds; };
struct TreehouseFrameStage { uint32_t address,stack_low;uint16_t args[12],ax,bx,cx,dx,si,di,ds,es;uint8_t memory[0xb0000]; };
struct TreehouseFrameRow {
    double begin,end;uint32_t ordinal,path_hash,instructions,sample_count;
    uint16_t ds,ss,sp,instance;float video_delays[5];uint32_t parts_total,parts_lines,lines_total;
    TreehouseFrameSample samples[4096];
    uint32_t addresses[262144];
    uint8_t before[0xb0000],after[0xb0000];
    uint32_t conversion_source,conversion_palette;
    uint8_t conversion[0xb0000];
    uint32_t stack_low,conversion_stack_low,stage_count;
    TreehouseFrameStage stages[5];
};
static uint32_t treehouse_frame_base=0,treehouse_frame_count=0,treehouse_frame_total=0,treehouse_frame_error=0;
static bool treehouse_frame_active=false;
static TreehouseFrameRow treehouse_frame_current,treehouse_frame_rows[8];
static INLINE void TreehouseFrameInstruction(uint32_t address){
    if(!treehouse_frame_base)return;const unsigned main_offset=address-treehouse_frame_base,resident_offset=main_offset-0xd510;
    if(main_offset==0xc78a){
        if(treehouse_frame_active){treehouse_frame_error=1;return;}
        TreehouseFrameRow& r=treehouse_frame_current;memset(&r,0,sizeof(r));treehouse_frame_active=true;
        r.ordinal=treehouse_frame_total++;r.begin=PIC_FullIndex();r.path_hash=2166136261u;r.ds=SegValue(ds);r.ss=SegValue(ss);r.sp=reg_sp;r.instance=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+2));
        r.stack_low=reg_sp;
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;
        MEM_BlockRead(0,r.before,sizeof(r.before));
    }
    if(!treehouse_frame_active||treehouse_frame_error)return;TreehouseFrameRow& r=treehouse_frame_current;
    if(SegValue(ss)!=r.ss){treehouse_frame_error=7;return;}if(reg_sp<r.stack_low)r.stack_low=reg_sp;
    if(r.instructions>=262144){treehouse_frame_error=2;return;}r.addresses[r.instructions++]=address;
    for(unsigned shift=0;shift<32;shift+=8)r.path_hash=(r.path_hash^((address>>shift)&255))*16777619u;
    if(resident_offset==0xd580){
        if(r.conversion_source){treehouse_frame_error=6;return;}
        r.conversion_palette=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+4))+16*mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+6));
        r.conversion_source=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+8))+16*mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+10));
        r.conversion_stack_low=r.stack_low;
        MEM_BlockRead(0,r.conversion,sizeof(r.conversion));
    }
    if(resident_offset==0xd5a7||resident_offset==0x652a||resident_offset==0xe03e||resident_offset==0xde10||resident_offset==0x64ce){
        if(r.stage_count>=5){treehouse_frame_error=8;return;}TreehouseFrameStage& s=r.stages[r.stage_count++];s.address=resident_offset;s.stack_low=r.stack_low;
        for(unsigned i=0;i<12;i++)s.args[i]=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+4+2*i));
        s.ax=reg_ax;s.bx=reg_bx;s.cx=reg_cx;s.dx=reg_dx;s.si=reg_si;s.di=reg_di;s.ds=SegValue(ds);s.es=SegValue(es);MEM_BlockRead(0,s.memory,sizeof(s.memory));
    }
    bool sample=main_offset==0xc78a||main_offset==0xc9ea||main_offset==0xc799||main_offset==0xc9ed||main_offset==0xcbd2||main_offset==0xcc1e;
    const unsigned selected[]={0x7db6,0x7e1c,0x8242,0x83b4,0x7ee6,0x84fa,0x096e,0x099a,0x9a68,0x9b47,0x9c01,0x9bf6,0xa112,0xa18c,0xa209,0x9ed6,0x9f50,0xa034,0xa0d3,0xa0d8,0x8955,0x8822,0x857a,0xd580,0xd5a7,0x652a,0xe03e,0xde10,0x64ce};
    for(unsigned i=0;i<sizeof(selected)/sizeof(selected[0]);i++)if(resident_offset==selected[i])sample=true;
    if(sample){
        if(r.sample_count>=4096){treehouse_frame_error=3;return;}
        TreehouseFrameSample& s=r.samples[r.sample_count++];s.address=address;s.remaining=reg_cx;s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.ticks=PIC_Ticks;s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;s.milliseconds=PIC_FullIndex();
    }
    if(main_offset==0xc9ea){
        if(SegValue(ss)!=r.ss||reg_sp!=r.sp){treehouse_frame_error=4;return;}
        r.end=PIC_FullIndex();MEM_BlockRead(0,r.after,sizeof(r.after));
        if(treehouse_frame_count>=8){treehouse_frame_error=5;return;}
        treehouse_frame_rows[treehouse_frame_count++]=r;treehouse_frame_active=false;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_frame_size(void){return sizeof(TreehouseFrameRow);}
extern "C" RETRO_API unsigned retro_treehouse_frame_status(void){return treehouse_frame_error;}
extern "C" RETRO_API unsigned retro_treehouse_frame_partial(void){return treehouse_frame_active?1:0;}
extern "C" RETRO_API void retro_treehouse_frame_configure(uint32_t base){treehouse_frame_base=base;treehouse_frame_count=treehouse_frame_total=treehouse_frame_error=0;treehouse_frame_active=false;}
extern "C" RETRO_API unsigned retro_treehouse_frame_read(TreehouseFrameRow* rows,unsigned capacity){
    unsigned n=treehouse_frame_count<capacity?treehouse_frame_count:capacity;memcpy(rows,treehouse_frame_rows,n*sizeof(TreehouseFrameRow));treehouse_frame_count-=n;
    if(treehouse_frame_count)memmove(treehouse_frame_rows,treehouse_frame_rows+n,treehouse_frame_count*sizeof(TreehouseFrameRow));return n;
}
