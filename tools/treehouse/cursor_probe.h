// Read-only cursor state and intrinsic instruction evidence, including nesting.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehouseCursorSample { int32_t budget,left,maximum;uint32_t ticks,parts_left,lines_done;double milliseconds; };
struct TreehouseCursorRow {
    double begin,end;
    uint32_t ordinal,kind,edge,path_hash,last,counts[1080];
    int32_t parent;
    uint16_t pointer[2],rect[4],before[42],after[42];
    TreehouseCursorSample samples[2];
    float video_delays[5];uint32_t parts_total,parts_lines,lines_total;
    uint16_t handles[4];
};
static uint32_t treehouse_cursor_base=0,treehouse_cursor_count=0,treehouse_cursor_total=0,treehouse_cursor_error=0;
static unsigned treehouse_cursor_depth=0;
static TreehouseCursorRow treehouse_cursor_stack[16],treehouse_cursor_rows[1024];
static INLINE void TreehouseCursorClock(TreehouseCursorSample& s){
    s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.ticks=PIC_Ticks;s.milliseconds=PIC_FullIndex();s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;
}
static INLINE void TreehouseCursorState(uint16_t* state){
    const PhysPt data=SegPhys(ds);const uint16_t offsets[]={0x2062,0x205a,0x2100,0x2064,0x2066,0x20ca,0x20cc,0x20ce,0x20c8,0x2060};
    for(unsigned i=0;i<10;i++)state[i]=mem_readw(data+offsets[i]);
    for(unsigned i=0;i<16;i++){state[10+i]=mem_readw(data+0x2088+2*i);state[26+i]=mem_readw(data+0x20d0+2*i);}
}
static INLINE void TreehouseCursorInstruction(uint32_t address){
    if(!treehouse_cursor_base)return;const uint32_t offset=address-treehouse_cursor_base;
    if(offset==0x8955||offset==0x857a||offset==0x8822){
        if(treehouse_cursor_depth>=16){treehouse_cursor_error=1;return;}
        const int parent=treehouse_cursor_depth?treehouse_cursor_stack[treehouse_cursor_depth-1].ordinal:-1;
        const unsigned edge=treehouse_cursor_depth?treehouse_cursor_stack[treehouse_cursor_depth-1].last:0;
        TreehouseCursorRow& r=treehouse_cursor_stack[treehouse_cursor_depth++];memset(&r,0,sizeof(r));
        r.ordinal=treehouse_cursor_total++;r.kind=offset==0x8955?0:offset==0x857a?1:2;r.parent=parent;r.edge=edge;r.path_hash=2166136261u;r.begin=PIC_FullIndex();
        r.pointer[0]=reg_ax;r.pointer[1]=SegValue(es);
        for(unsigned i=0;i<4;i++)r.rect[i]=mem_readw(SegPhys(ss)+(uint16_t)(reg_bp-8+2*i));
        TreehouseCursorState(r.before);
        TreehouseCursorClock(r.samples[0]);
        r.video_delays[0]=(float)vga.draw.delay.vtotal;r.video_delays[1]=(float)vga.draw.delay.vrstart;r.video_delays[2]=(float)vga.draw.delay.vrend;r.video_delays[3]=(float)(vga.draw.delay.vdend+0.005);r.video_delays[4]=(float)vga.draw.delay.parts;
        r.parts_total=vga.draw.parts_total;r.parts_lines=vga.draw.parts_lines;r.lines_total=vga.draw.lines_total;
        for(unsigned i=0;i<2;i++){r.handles[2*i]=mem_readw(SegPhys(ds)+r.before[7+i]);r.handles[2*i+1]=mem_readw(SegPhys(ds)+r.before[7+i]+2);}
    }
    if(!treehouse_cursor_depth||treehouse_cursor_error)return;
    TreehouseCursorRow& r=treehouse_cursor_stack[treehouse_cursor_depth-1];
    if((r.kind==0&&offset>=0x8955&&offset<0x89b2)||(r.kind==1&&offset>=0x857a&&offset<0x85b1)||(r.kind==2&&offset>=0x8822&&offset<0x88ca)){
        ++r.counts[offset-0x857a];r.last=offset;
        for(unsigned shift=0;shift<32;shift+=8)r.path_hash=(r.path_hash^((offset>>shift)&255))*16777619u;
    }
    if((r.kind==0&&(offset==0x8960||offset==0x89b1))||(r.kind==1&&(offset==0x85ab||offset==0x85b0))||(r.kind==2&&offset==0x8846)){
        r.end=PIC_FullIndex();TreehouseCursorState(r.after);
        TreehouseCursorClock(r.samples[1]);
        if(treehouse_cursor_count>=1024){treehouse_cursor_error=2;return;}
        treehouse_cursor_rows[treehouse_cursor_count++]=r;--treehouse_cursor_depth;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_cursor_size(void){return sizeof(TreehouseCursorRow);}
extern "C" RETRO_API unsigned retro_treehouse_cursor_status(void){return treehouse_cursor_error;}
extern "C" RETRO_API unsigned retro_treehouse_cursor_partial(void){return treehouse_cursor_depth;}
extern "C" RETRO_API void retro_treehouse_cursor_configure(uint32_t base){treehouse_cursor_base=base;treehouse_cursor_count=treehouse_cursor_total=treehouse_cursor_error=treehouse_cursor_depth=0;}
extern "C" RETRO_API unsigned retro_treehouse_cursor_read(TreehouseCursorRow* rows,unsigned capacity){
    unsigned n=treehouse_cursor_count<capacity?treehouse_cursor_count:capacity;memcpy(rows,treehouse_cursor_rows,n*sizeof(TreehouseCursorRow));treehouse_cursor_count-=n;
    if(treehouse_cursor_count)memmove(treehouse_cursor_rows,treehouse_cursor_rows+n,treehouse_cursor_count*sizeof(TreehouseCursorRow));return n;
}
