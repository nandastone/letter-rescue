// Read-only VGA surface copy evidence. Pixel snapshots surround the copy loop,
// after cursor preparation and before cursor restoration, never alter guest RAM.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehouseBlitSlice { uint32_t address,remaining;int32_t budget,left,maximum;uint32_t ticks,parts_left,lines_done;double milliseconds; };
struct TreehouseBlitRow {
    double begin,end;
    uint32_t ordinal,path_hash,counts[496],slice_count;
    uint16_t mode,context,source_id,destination_id,source[16],destination[16],source_rect[4],destination_rect[4];
    uint16_t source_rows[256],destination_rows[256];
    uint32_t source_size,destination_size,copied;
    float video_delays[5];
    uint32_t parts_total,parts_lines,lines_total;
    TreehouseBlitSlice slices[512];
    uint8_t source_pixels[65536],before_pixels[65536],after_pixels[65536];
};
static uint32_t treehouse_blit_base=0,treehouse_blit_count=0,treehouse_blit_total=0,treehouse_blit_error=0;
static unsigned treehouse_blit_depth=0;
static TreehouseBlitRow treehouse_blit_stack[8],treehouse_blit_rows[64];
static PhysPt TreehouseBlitPointer(uint16_t* surface){return 16*surface[1]+surface[0];}
static void TreehouseBlitSurface(uint16_t* surface,uint16_t* rows,unsigned& size,PhysPt data,unsigned id){
    for(unsigned i=0;i<16;i++)surface[i]=mem_readw(data+id+2*i);
    const unsigned height=(uint16_t)(surface[4]-surface[2]);size=height*surface[6];
    if(height>256||size>65536){treehouse_blit_error=2;return;}
    for(unsigned i=0;i<height;i++)rows[i]=mem_readw(data+surface[7]+2*i);
}
static INLINE void TreehouseBlitInstruction(uint32_t address){
    if(!treehouse_blit_base)return;
    const uint32_t offset=address-treehouse_blit_base;
    if(offset==0x9a68){
        if(treehouse_blit_depth>=8){treehouse_blit_error=1;return;}
        TreehouseBlitRow& r=treehouse_blit_stack[treehouse_blit_depth++];memset(&r,0,sizeof(r));
        r.ordinal=treehouse_blit_total++;r.begin=PIC_FullIndex();r.path_hash=2166136261u;
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;
        const PhysPt stack=SegPhys(ss),data=SegPhys(ds);
        r.mode=mem_readw(stack+(uint16_t)(reg_sp+4));r.context=mem_readw(data+0x205a);
        r.source_id=mem_readw(stack+(uint16_t)(reg_sp+14));r.destination_id=mem_readw(stack+(uint16_t)(reg_sp+16));
        const PhysPt sr=16*mem_readw(stack+(uint16_t)(reg_sp+8))+mem_readw(stack+(uint16_t)(reg_sp+6));
        const PhysPt dr=16*mem_readw(stack+(uint16_t)(reg_sp+12))+mem_readw(stack+(uint16_t)(reg_sp+10));
        for(unsigned i=0;i<4;i++){r.source_rect[i]=mem_readw(sr+2*i);r.destination_rect[i]=mem_readw(dr+2*i);}
        TreehouseBlitSurface(r.source,r.source_rows,r.source_size,data,r.source_id);
        TreehouseBlitSurface(r.destination,r.destination_rows,r.destination_size,data,r.destination_id);
    }
    if(!treehouse_blit_depth||treehouse_blit_error)return;
    TreehouseBlitRow& r=treehouse_blit_stack[treehouse_blit_depth-1];
    if(offset>=0x9a68&&offset<0x9c58){
        ++r.counts[offset-0x9a68];
        for(unsigned shift=0;shift<32;shift+=8)r.path_hash=(r.path_hash^((offset>>shift)&255))*16777619u;
        if(offset==0x9bf6||offset==0x9c01){
            if(r.slice_count>=512){treehouse_blit_error=3;return;}
            TreehouseBlitSlice& slice=r.slices[r.slice_count++];slice.address=offset;slice.remaining=reg_cx;slice.budget=CPU_Cycles;
            slice.left=CPU_CycleLeft;slice.maximum=CPU_CycleMax;slice.ticks=PIC_Ticks;slice.milliseconds=PIC_FullIndex();slice.parts_left=vga.draw.parts_left;slice.lines_done=vga.draw.lines_done;
        }
    }
    if(offset==0x9b73){
        r.copied=1;MEM_BlockRead(TreehouseBlitPointer(r.source),r.source_pixels,r.source_size);MEM_BlockRead(TreehouseBlitPointer(r.destination),r.before_pixels,r.destination_size);
    }
    if(offset==0x9c22)MEM_BlockRead(TreehouseBlitPointer(r.destination),r.after_pixels,r.destination_size);
    if(offset==0x9b47){
        r.end=PIC_FullIndex();
        if(treehouse_blit_count>=64){treehouse_blit_error=4;return;}
        treehouse_blit_rows[treehouse_blit_count++]=r;--treehouse_blit_depth;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_blit_size(void){return sizeof(TreehouseBlitRow);}
extern "C" RETRO_API unsigned retro_treehouse_blit_status(void){return treehouse_blit_error;}
extern "C" RETRO_API unsigned retro_treehouse_blit_partial(void){return treehouse_blit_depth;}
extern "C" RETRO_API void retro_treehouse_blit_configure(uint32_t base){treehouse_blit_base=base;treehouse_blit_count=treehouse_blit_total=treehouse_blit_error=treehouse_blit_depth=0;}
extern "C" RETRO_API unsigned retro_treehouse_blit_read(TreehouseBlitRow* rows,unsigned capacity){
    unsigned n=treehouse_blit_count<capacity?treehouse_blit_count:capacity;memcpy(rows,treehouse_blit_rows,n*sizeof(TreehouseBlitRow));treehouse_blit_count-=n;
    if(treehouse_blit_count)memmove(treehouse_blit_rows,treehouse_blit_rows+n,treehouse_blit_count*sizeof(TreehouseBlitRow));return n;
}
