// Read-only resident animation support helpers. Nested callees retain own rows.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehouseGeometrySample { uint32_t address,remaining;int32_t budget,left,maximum;uint32_t ticks,parts_left,lines_done;double milliseconds; };
struct TreehouseGeometryRow {
    double begin,end;uint32_t ordinal,kind,path_hash,count_size,addresses[128],counts[128],sample_count;
    uint32_t data,output;int32_t parent;
    uint16_t args[8],context,surface[16],after_surface[16],a[4],b[4],before[4],after[4],result[2];
    uint8_t source_bytes[64],before_bytes[64],after_bytes[64];
    TreehouseGeometrySample samples[32];
};
static const uint32_t treehouse_geometry_entries[]={0x8242,0x83b4,0x7ee6,0x84fa,0x81f0,0x7db6,0x7e1c,0x7f08,0x096e,0x099a};
static const uint32_t treehouse_geometry_returns[]={0x826a,0x841a,0x7f05,0x8546,0x8213,0x7e19,0x7e31,0x7f1c,0x0999,0x09c6};
static uint32_t treehouse_geometry_base=0,treehouse_geometry_count=0,treehouse_geometry_total=0,treehouse_geometry_error=0;
static unsigned treehouse_geometry_depth=0;
static TreehouseGeometryRow treehouse_geometry_stack[16],treehouse_geometry_rows[4096];
static PhysPt TreehouseGeometryFar(const uint16_t* a,unsigned at){return 16*a[at+1]+a[at];}
static void TreehouseGeometryWords(uint16_t* out,PhysPt at,unsigned n=4){for(unsigned i=0;i<n;i++)out[i]=mem_readw(at+2*i);}
static INLINE void TreehouseGeometryInstruction(uint32_t address){
    if(!treehouse_geometry_base)return;const unsigned offset=address-treehouse_geometry_base;
    int kind=-1;for(unsigned i=0;i<10;i++)if(offset==treehouse_geometry_entries[i])kind=i;
    if(kind>=8&&mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+8))>64)kind=-1;
    if(kind>=0){
        if(treehouse_geometry_depth>=16){treehouse_geometry_error=1;return;}
        int parent=treehouse_geometry_depth?treehouse_geometry_stack[treehouse_geometry_depth-1].ordinal:-1;
        TreehouseGeometryRow& r=treehouse_geometry_stack[treehouse_geometry_depth++];memset(&r,0,sizeof(r));
        r.kind=kind;r.ordinal=treehouse_geometry_total++;r.parent=parent;r.begin=PIC_FullIndex();r.path_hash=2166136261u;r.data=SegPhys(ds);
        for(unsigned i=0;i<8;i++)r.args[i]=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+4+2*i));
        r.context=mem_readw(r.data+0x205a);TreehouseGeometryWords(r.surface,r.data+r.context,16);
        if(kind==0){TreehouseGeometryWords(r.a,TreehouseGeometryFar(r.args,2));r.output=TreehouseGeometryFar(r.args,4);}
        else if(kind==1||kind==3){TreehouseGeometryWords(r.a,TreehouseGeometryFar(r.args,0));TreehouseGeometryWords(r.b,TreehouseGeometryFar(r.args,2));r.output=TreehouseGeometryFar(r.args,4);}
        else if(kind==2)TreehouseGeometryWords(r.a,TreehouseGeometryFar(r.args,0));
        else if(kind==4){TreehouseGeometryWords(r.a,TreehouseGeometryFar(r.args,0),2);r.output=TreehouseGeometryFar(r.args,2);}
        else if(kind==5){if(TreehouseGeometryFar(r.args,0))TreehouseGeometryWords(r.a,TreehouseGeometryFar(r.args,0));r.output=r.data+r.context+24;}
        else if(kind==6){for(unsigned i=0;i<4;i++)r.b[i]=r.args[i];r.output=r.data+r.context+24;}
        else if(kind==7)TreehouseGeometryWords(r.a,TreehouseGeometryFar(r.args,1));
        if(r.output)TreehouseGeometryWords(r.before,r.output,kind==4?2:4);
        if(kind>=8)for(unsigned i=0;i<r.args[2];i++){
            r.before_bytes[i]=mem_readb(r.data+(uint16_t)(r.args[0]+i));
            if(kind==8)r.source_bytes[i]=mem_readb(r.data+(uint16_t)(r.args[1]+i));
        }
    }
    if(!treehouse_geometry_depth||treehouse_geometry_error)return;
    TreehouseGeometryRow& r=treehouse_geometry_stack[treehouse_geometry_depth-1];
    if(offset<treehouse_geometry_entries[r.kind]||offset>treehouse_geometry_returns[r.kind])return;
    unsigned index=0;while(index<r.count_size&&r.addresses[index]!=offset)index++;
    if(index==r.count_size){if(index>=128){treehouse_geometry_error=2;return;}r.addresses[r.count_size++]=offset;}
    ++r.counts[index];for(unsigned shift=0;shift<32;shift+=8)r.path_hash=(r.path_hash^((offset>>shift)&255))*16777619u;
    if(offset==treehouse_geometry_entries[r.kind]||offset==treehouse_geometry_returns[r.kind]||offset==0x8415||offset==0x7de9||offset==0x098e||offset==0x0992||offset==0x09bc||offset==0x09c0){
        if(r.sample_count>=32){treehouse_geometry_error=3;return;}
        TreehouseGeometrySample& s=r.samples[r.sample_count++];s.address=offset;s.remaining=reg_cx;s.budget=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.ticks=PIC_Ticks;s.parts_left=vga.draw.parts_left;s.lines_done=vga.draw.lines_done;s.milliseconds=PIC_FullIndex();
    }
    if(offset==treehouse_geometry_returns[r.kind]){
        r.end=PIC_FullIndex();r.result[0]=reg_ax;r.result[1]=reg_dx;TreehouseGeometryWords(r.after_surface,r.data+r.context,16);
        if(r.output)TreehouseGeometryWords(r.after,r.output,r.kind==4?2:4);
        if(r.kind>=8)for(unsigned i=0;i<r.args[2];i++)r.after_bytes[i]=mem_readb(r.data+(uint16_t)(r.args[0]+i));
        if(treehouse_geometry_count>=4096){treehouse_geometry_error=4;return;}
        treehouse_geometry_rows[treehouse_geometry_count++]=r;--treehouse_geometry_depth;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_geometry_size(void){return sizeof(TreehouseGeometryRow);}
extern "C" RETRO_API unsigned retro_treehouse_geometry_status(void){return treehouse_geometry_error;}
extern "C" RETRO_API unsigned retro_treehouse_geometry_partial(void){return treehouse_geometry_depth;}
extern "C" RETRO_API void retro_treehouse_geometry_configure(uint32_t base){treehouse_geometry_base=base;treehouse_geometry_count=treehouse_geometry_total=treehouse_geometry_error=treehouse_geometry_depth=0;}
extern "C" RETRO_API unsigned retro_treehouse_geometry_read(TreehouseGeometryRow* rows,unsigned capacity){
    unsigned n=treehouse_geometry_count<capacity?treehouse_geometry_count:capacity;memcpy(rows,treehouse_geometry_rows,n*sizeof(TreehouseGeometryRow));treehouse_geometry_count-=n;
    if(treehouse_geometry_count)memmove(treehouse_geometry_rows,treehouse_geometry_rows+n,treehouse_geometry_count*sizeof(TreehouseGeometryRow));return n;
}
