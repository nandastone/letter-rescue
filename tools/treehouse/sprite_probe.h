// Read-only VGA sprite evidence. Cursor helper effects are outside pixel pairs.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehouseSpriteSample {
    uint32_t address,remaining;int32_t budget,left,maximum;
    uint32_t ticks,parts_left,lines_done;double milliseconds;
};
struct TreehouseSpriteRow {
    double begin,end;
    uint32_t ordinal,path_hash,counts[1002],sample_count;
    uint16_t kind,color,mode,x,y,context,shape[3],surface[16],rows[256],rect[4];
    uint32_t source_size,destination_size,drawn;
    float video_delays[5];uint32_t parts_total,parts_lines,lines_total;
    TreehouseSpriteSample samples[512];
    uint8_t source_pixels[65536],before_pixels[65536],after_pixels[65536];
};
static uint32_t treehouse_sprite_base=0,treehouse_sprite_count=0,treehouse_sprite_total=0,treehouse_sprite_error=0;
static unsigned treehouse_sprite_depth=0;
static TreehouseSpriteRow treehouse_sprite_stack[8],treehouse_sprite_rows[256];
static INLINE void TreehouseSpriteInstruction(uint32_t address){
    if(!treehouse_sprite_base)return;
    const uint32_t offset=address-treehouse_sprite_base;
    if(offset==0xa112||offset==0x9ed6||offset==0xa034){
        if(treehouse_sprite_depth>=8){treehouse_sprite_error=1;return;}
        TreehouseSpriteRow& r=treehouse_sprite_stack[treehouse_sprite_depth++];memset(&r,0,sizeof(r));
        r.ordinal=treehouse_sprite_total++;r.begin=PIC_FullIndex();r.path_hash=2166136261u;r.kind=offset==0xa034?2:offset==0x9ed6?1:0;
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;
        const PhysPt stack=SegPhys(ss),data=SegPhys(ds);
        const unsigned extra=2*(r.kind!=0);r.color=r.kind?mem_readw(stack+(uint16_t)(reg_sp+4)):0;
        r.mode=mem_readw(stack+(uint16_t)(reg_sp+4+extra));r.y=mem_readw(stack+(uint16_t)(reg_sp+6+extra));r.x=mem_readw(stack+(uint16_t)(reg_sp+8+extra));r.context=mem_readw(data+0x205a);
        PhysPt shape=0;
        if(r.kind==2){
            const PhysPt rect=16*mem_readw(stack+(uint16_t)(reg_sp+10))+mem_readw(stack+(uint16_t)(reg_sp+8));
            for(unsigned i=0;i<4;i++)r.rect[i]=mem_readw(rect+2*i);
        }else{
            shape=16*mem_readw(stack+(uint16_t)(reg_sp+12+extra))+mem_readw(stack+(uint16_t)(reg_sp+10+extra));
            for(unsigned i=0;i<3;i++)r.shape[i]=mem_readw(shape+2*i);
        }
        for(unsigned i=0;i<16;i++)r.surface[i]=mem_readw(data+r.context+2*i);
        const unsigned height=(uint16_t)(r.surface[4]-r.surface[2]);r.destination_size=height*r.surface[6];r.source_size=r.shape[0]*r.shape[2];
        if(height>256||r.destination_size>65536||r.source_size>65536){treehouse_sprite_error=2;return;}
        for(unsigned i=0;i<height;i++)r.rows[i]=mem_readw(data+r.surface[7]+2*i);
        if(r.source_size)MEM_BlockRead(shape+6,r.source_pixels,r.source_size);
    }
    if(!treehouse_sprite_depth||treehouse_sprite_error)return;
    TreehouseSpriteRow& r=treehouse_sprite_stack[treehouse_sprite_depth-1];
    if((!r.kind&&offset>=0xa112&&offset<0xa2c0)||(r.kind==1&&offset>=0x9ed6&&offset<0xa024)||(r.kind==2&&offset>=0xa034&&offset<0xa102)){
        ++r.counts[offset-0x9ed6];
        for(unsigned shift=0;shift<32;shift+=8)r.path_hash=(r.path_hash^((offset>>shift)&255))*16777619u;
        if(offset==0xa197||offset==0xa231||offset==0xa209||offset==0xa23c||offset==0x9f5b||offset==0x9fd6||offset==0x9fbe||offset==0xa0a9||offset==0xa0d8||offset==0xa0e3||offset==0xa0c5){
            if(r.sample_count>=512){treehouse_sprite_error=3;return;}
            TreehouseSpriteSample& s=r.samples[r.sample_count++];s.address=offset;s.remaining=reg_cx;s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.ticks=PIC_Ticks;s.milliseconds=PIC_FullIndex();s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;
        }
    }
    if((!r.kind&&offset==0xa197)||(r.kind==1&&offset==0x9f5b)||(r.kind==2&&offset==0xa0a9)){r.drawn=1;MEM_BlockRead(16*r.surface[1]+r.surface[0],r.before_pixels,r.destination_size);}
    if((!r.kind&&offset==0xa23c)||(r.kind==1&&offset==0x9fbe)||(r.kind==2&&offset==0xa0c5))MEM_BlockRead(16*r.surface[1]+r.surface[0],r.after_pixels,r.destination_size);
    if((!r.kind&&offset==0xa18c)||(r.kind==1&&offset==0x9f50)||(r.kind==2&&offset==0xa0d3)){
        r.end=PIC_FullIndex();if(treehouse_sprite_count>=256){treehouse_sprite_error=4;return;}
        treehouse_sprite_rows[treehouse_sprite_count++]=r;--treehouse_sprite_depth;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_sprite_size(void){return sizeof(TreehouseSpriteRow);}
extern "C" RETRO_API unsigned retro_treehouse_sprite_status(void){return treehouse_sprite_error;}
extern "C" RETRO_API unsigned retro_treehouse_sprite_partial(void){return treehouse_sprite_depth;}
extern "C" RETRO_API void retro_treehouse_sprite_configure(uint32_t base){treehouse_sprite_base=base;treehouse_sprite_count=treehouse_sprite_total=treehouse_sprite_error=treehouse_sprite_depth=0;}
extern "C" RETRO_API unsigned retro_treehouse_sprite_read(TreehouseSpriteRow* rows,unsigned capacity){
    unsigned n=treehouse_sprite_count<capacity?treehouse_sprite_count:capacity;memcpy(rows,treehouse_sprite_rows,n*sizeof(TreehouseSpriteRow));treehouse_sprite_count-=n;
    if(treehouse_sprite_count)memmove(treehouse_sprite_rows,treehouse_sprite_rows+n,treehouse_sprite_count*sizeof(TreehouseSpriteRow));return n;
}
