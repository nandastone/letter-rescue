// Read-only 4855..48C0 animation caller spans, including all nested work/IRQs.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
extern "C" void TreehouseReadMixerState(uint32_t* out);
extern "C" void TreehouseReadAudioFrontend(double* out);
extern "C" void TreehouseReadSoundPlayback(uint32_t* dma,int32_t* channel,double* last);
extern "C" void TreehouseReadSoundHardware(uint32_t* out);
extern "C" uint32_t TreehouseReadSoundDmaAutoInit(void);
extern "C" void TreehouseReadMouseHardware(uint32_t* out);
struct TreehouseAnimationLoopSample {
    uint32_t instruction,address;int32_t budget,left,maximum;int64_t io;
    uint32_t ticks,parts_left,lines_done,flags;double milliseconds;
    uint16_t ss,sp,bp,cs,ds,es,ax,bx,cx,dx,si,di;
};
struct TreehouseAnimationLoopRow {
    uint32_t ordinal,instructions,path_hash,sample_count,stack_low;
    uint16_t instance,ds,ss,sp,bp,first_frame,base_id,activity;
    float video_delays[5];uint32_t parts_total,parts_lines,lines_total;
    uint32_t sound_initial[32],mouse_initial[96],dma_autoinit;
    uint32_t dma_initial[8],mixer_initial[10];int32_t channel_initial[16];double last_dma_callback,audio_frontend[7];
    TreehouseAnimationLoopSample samples[131072];
    uint8_t before[0xb0000],after[0xb0000];
};
static uint32_t treehouse_loop_base=0,treehouse_loop_count=0,treehouse_loop_total=0,treehouse_loop_error=0;
static bool treehouse_loop_active=false;
static TreehouseAnimationLoopRow treehouse_loop_current,treehouse_loop_rows[4];
static INLINE void TreehouseAnimationLoopInstruction(uint32_t address){
    if(!treehouse_loop_base)return;
    if(!treehouse_loop_active){
        if(address!=treehouse_loop_base+0x4855)return;
        TreehouseAnimationLoopRow& r=treehouse_loop_current;memset(&r,0,sizeof(r));r.ordinal=treehouse_loop_total++;r.path_hash=2166136261u;
        r.ds=SegValue(ds);r.ss=SegValue(ss);r.sp=reg_sp;r.bp=reg_bp;r.stack_low=reg_sp;
        r.instance=mem_readw(SegPhys(ss)+(uint16_t)(reg_bp-0x14));r.first_frame=mem_readw(SegPhys(ss)+(uint16_t)(reg_bp+0x10));r.base_id=mem_readw(SegPhys(ss)+(uint16_t)(reg_bp+0x1a));r.activity=mem_readw(SegPhys(ss)+(uint16_t)(reg_bp+0x18));
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;
        TreehouseReadMixerState(r.mixer_initial);TreehouseReadSoundPlayback(r.dma_initial,r.channel_initial,&r.last_dma_callback);TreehouseReadAudioFrontend(r.audio_frontend);r.dma_autoinit=TreehouseReadSoundDmaAutoInit();TreehouseReadSoundHardware(r.sound_initial);TreehouseReadMouseHardware(r.mouse_initial);MEM_BlockRead(0,r.before,sizeof(r.before));treehouse_loop_active=true;
    }
    if(treehouse_loop_error)return;TreehouseAnimationLoopRow& r=treehouse_loop_current;
    if(SegValue(ss)!=r.ss){treehouse_loop_error=2;return;}if(reg_sp<r.stack_low)r.stack_low=reg_sp;
    const bool end=address==treehouse_loop_base+0x48c0&&reg_bp==r.bp;
    if(!(r.instructions%1024)||end||address==treehouse_loop_base+0xc78a){
        if(r.sample_count>=131072){treehouse_loop_error=3;return;}TreehouseAnimationLoopSample& s=r.samples[r.sample_count++];
        s.instruction=r.instructions;s.address=address;s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.io=CPU_IODelayRemoved;s.ticks=PIC_Ticks;s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;s.flags=reg_flags;s.milliseconds=PIC_FullIndex();
        s.ss=SegValue(ss);s.sp=reg_sp;s.bp=reg_bp;s.cs=SegValue(cs);s.ds=SegValue(ds);s.es=SegValue(es);s.ax=reg_ax;s.bx=reg_bx;s.cx=reg_cx;s.dx=reg_dx;s.si=reg_si;s.di=reg_di;
    }
    for(unsigned shift=0;shift<32;shift+=8)r.path_hash=(r.path_hash^((address>>shift)&255))*16777619u;
    r.instructions++;
    if(end){
        MEM_BlockRead(0,r.after,sizeof(r.after));if(treehouse_loop_count>=4){treehouse_loop_error=4;return;}
        treehouse_loop_rows[treehouse_loop_count++]=r;treehouse_loop_active=false;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_animation_loop_size(void){return sizeof(TreehouseAnimationLoopRow);}
extern "C" RETRO_API unsigned retro_treehouse_animation_loop_status(void){return treehouse_loop_error;}
extern "C" RETRO_API unsigned retro_treehouse_animation_loop_partial(void){return treehouse_loop_active?1:0;}
extern "C" RETRO_API void retro_treehouse_animation_loop_configure(uint32_t base){treehouse_loop_base=base;treehouse_loop_count=treehouse_loop_total=treehouse_loop_error=0;treehouse_loop_active=false;}
extern "C" RETRO_API unsigned retro_treehouse_animation_loop_read(TreehouseAnimationLoopRow* out,unsigned capacity){
    const unsigned n=treehouse_loop_count<capacity?treehouse_loop_count:capacity;memcpy(out,treehouse_loop_rows,n*sizeof(TreehouseAnimationLoopRow));treehouse_loop_count-=n;
    if(treehouse_loop_count)memmove(treehouse_loop_rows,treehouse_loop_rows+n,treehouse_loop_count*sizeof(TreehouseAnimationLoopRow));return n;
}
