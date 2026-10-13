// Read-only interpreter calls. Consecutive identical work/state records coalesce;
// repetition counts and timestamps are offline evidence, never runtime inputs.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
extern void TreehouseCpuProbeContext(uint64_t* values);
struct TreehouseScriptState {
    uint16_t instance,ds,context,display_count,sound_enabled,cue,wrapper[7],drawing[9],dimensions[60];
    uint32_t ticks;
    uint8_t memory[726],code[256];
};
struct TreehouseScriptPayload {
    TreehouseScriptState before,after;
    uint32_t counts[1533],path_hash;
    uint16_t result,reads;
    uint32_t tick_reads[16];
    uint32_t gap_count,gap_hash,gap_addresses[128];
    uint32_t drawing_counts[1462],drawing_hash;
};
struct TreehouseScriptRow {
    double begin,end;
    uint64_t first_instruction,last_instruction;
    uint32_t ordinal,repeats;
    TreehouseScriptPayload payload;
};
static uint32_t treehouse_script_base=0,treehouse_script_count=0,treehouse_script_total=0,treehouse_script_error=0;
static uint16_t treehouse_script_ss=0,treehouse_script_sp=0;
static bool treehouse_script_active=false;
static uint32_t treehouse_script_gap_count=0,treehouse_script_gap_hash=2166136261u,treehouse_script_gap_addresses[128];
static TreehouseScriptRow treehouse_script_current,treehouse_script_rows[256];
static void TreehouseScriptStateRead(TreehouseScriptState& s,uint16_t instance){
    s.instance=instance;s.ds=SegValue(ds);const PhysPt dataSegment=SegPhys(ds),object=dataSegment+instance;
    s.context=mem_readw(dataSegment+0x205a);s.display_count=mem_readw(dataSegment+0x5586);s.sound_enabled=mem_readw(dataSegment+0x5822);s.cue=mem_readb(dataSegment+0x211b);s.ticks=mem_readd(dataSegment + 0x201e);
    MEM_BlockRead(object,s.memory,sizeof(s.memory));
    const PhysPt code=mem_readw(object+0x50)*16+mem_readw(object + 0x4e);MEM_BlockRead(code,s.code,sizeof(s.code));
    const PhysPt stack=SegPhys(ss);
    s.wrapper[0]=mem_readw(stack+reg_sp);s.wrapper[1]=mem_readw(stack+(uint16_t)(reg_sp+2));
    s.wrapper[2]=mem_readw(stack+(uint16_t)(reg_bp+0x10));s.wrapper[3]=mem_readw(stack+(uint16_t)(reg_bp+0x1a));s.wrapper[4]=mem_readw(stack+(uint16_t)(reg_bp+0x18));
    s.wrapper[5]=mem_readw(dataSegment+0x5296);s.wrapper[6]=mem_readw(dataSegment+0xdc6);
    const unsigned globals[9]={0x5254,0x5520,0x57c0,0x52ca,0xd96,0xd98,0xd9a,0xd9c,0x5270};
    for(unsigned i=0;i<9;i++)s.drawing[i]=mem_readw(dataSegment+globals[i]);
    memset(s.dimensions,0,sizeof(s.dimensions));
    // This route's fixed 726-byte object has 29 shape handles. Headers are
    // independent input fixtures, not expected bounds or rendered output.
    for(unsigned i=1;i<30;i++){
        const unsigned handle=mem_readw(object+0x29a+2*i);
        if(!handle)continue;
        const unsigned flags=mem_readw(dataSegment+handle),segment=mem_readw(dataSegment+handle+2);
        if(flags&0x200)continue;
        const PhysPt header=16*segment+(flags&15)+6;
        if(header<6||header+4>0xa0000)continue;
        s.dimensions[2*i]=mem_readw(header);s.dimensions[2*i+1]=mem_readw(header+2);
    }
}
static INLINE void TreehouseScriptInstruction(uint32_t address){
    if(!treehouse_script_base)return;
    const uint32_t offset=address-treehouse_script_base;
    if(offset==0xbda0){
        if(treehouse_script_active){treehouse_script_error=1;return;}
        treehouse_script_active=true;memset(&treehouse_script_current,0,sizeof(treehouse_script_current));
        treehouse_script_current.payload.gap_count=treehouse_script_gap_count;treehouse_script_current.payload.gap_hash=treehouse_script_gap_hash;
        memcpy(treehouse_script_current.payload.gap_addresses,treehouse_script_gap_addresses,sizeof(treehouse_script_gap_addresses));
        treehouse_script_gap_count=0;treehouse_script_gap_hash=2166136261u;memset(treehouse_script_gap_addresses,0,sizeof(treehouse_script_gap_addresses));
        treehouse_script_ss=SegValue(ss);treehouse_script_sp=reg_sp;
        treehouse_script_current.ordinal=treehouse_script_total++;treehouse_script_current.repeats=1;treehouse_script_current.begin=PIC_FullIndex();
        uint64_t context[5];TreehouseCpuProbeContext(context);treehouse_script_current.first_instruction=context[0];
        treehouse_script_current.payload.path_hash=2166136261u;
        treehouse_script_current.payload.drawing_hash=2166136261u;
        TreehouseScriptStateRead(treehouse_script_current.payload.before,mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+4)));
    }
    if(!treehouse_script_active){
        if(treehouse_script_gap_count<128)treehouse_script_gap_addresses[treehouse_script_gap_count]=address;
        ++treehouse_script_gap_count;
        for(unsigned shift=0;shift<32;shift+=8)treehouse_script_gap_hash=(treehouse_script_gap_hash^((address>>shift)&255))*16777619u;
        return;
    }
    TreehouseScriptPayload& p=treehouse_script_current.payload;
    if(offset>=0xc78a&&offset<0xcd40){
        ++p.drawing_counts[offset-0xc78a];
        for(unsigned shift=0;shift<32;shift+=8)p.drawing_hash=(p.drawing_hash^((offset>>shift)&255))*16777619u;
    }
    if(offset==0xc799){
        if(p.reads>=16)treehouse_script_error=1;else p.tick_reads[p.reads++]=mem_readd(SegPhys(ds) + 0x201e);
    }
    if(offset<0xbda0||offset>=0xc39d)return;
    ++p.counts[offset-0xbda0];
    for(unsigned shift=0;shift<32;shift+=8)p.path_hash=(p.path_hash^((offset>>shift)&255))*16777619u;
    // Capture the actual shared timer read at each low-word load, separately
    // from call-entry state, so an interrupt inside the call is visible.
    if(offset==0xbde0||offset==0xbe15||offset==0xbe8f||offset==0xbec6||offset==0xbf0c){
        if(p.reads>=16)treehouse_script_error=1;else p.tick_reads[p.reads++]=mem_readd(SegPhys(ds) + 0x201e);
    }
    if(offset==0xc39a){
        if(SegValue(ss)!=treehouse_script_ss||reg_sp!=treehouse_script_sp){treehouse_script_error=1;return;}
        treehouse_script_current.end=PIC_FullIndex();p.result=reg_ax;TreehouseScriptStateRead(p.after,p.before.instance);
        uint64_t context[5];TreehouseCpuProbeContext(context);treehouse_script_current.last_instruction=context[0];
        if(treehouse_script_count&&memcmp(&treehouse_script_rows[treehouse_script_count-1].payload,&p,sizeof(p))==0){
            TreehouseScriptRow& prior=treehouse_script_rows[treehouse_script_count-1];++prior.repeats;prior.end=treehouse_script_current.end;prior.last_instruction=treehouse_script_current.last_instruction;
        }else if(treehouse_script_count>=256)treehouse_script_error=1;
        else treehouse_script_rows[treehouse_script_count++]=treehouse_script_current;
        treehouse_script_active=false;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_script_size(void){return sizeof(TreehouseScriptRow);}
extern "C" RETRO_API unsigned retro_treehouse_script_status(void){return treehouse_script_error;}
extern "C" RETRO_API unsigned retro_treehouse_script_partial(void){return treehouse_script_active?1:0;}
extern "C" RETRO_API void retro_treehouse_script_configure(uint32_t base){treehouse_script_base=base;treehouse_script_count=treehouse_script_total=treehouse_script_error=0;treehouse_script_active=false;treehouse_script_gap_count=0;treehouse_script_gap_hash=2166136261u;memset(treehouse_script_gap_addresses,0,sizeof(treehouse_script_gap_addresses));}
extern "C" RETRO_API unsigned retro_treehouse_script_read(TreehouseScriptRow* rows,unsigned capacity){
    unsigned n=treehouse_script_count<capacity?treehouse_script_count:capacity;memcpy(rows,treehouse_script_rows,n*sizeof(TreehouseScriptRow));treehouse_script_count-=n;
    if(treehouse_script_count)memmove(treehouse_script_rows,treehouse_script_rows+n,treehouse_script_count*sizeof(TreehouseScriptRow));return n;
}
