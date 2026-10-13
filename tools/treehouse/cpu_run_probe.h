// Read-only CPU decoder/callback boundaries. Defined in the isolated normal CPU TU.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehouseCpuEvent {
    double milliseconds;
    uint64_t instructions,strings,credits;
    int64_t io;
    int32_t cycles,left,maximum,result;
    uint32_t kind,id,ticks,eip,last_address,flags;
    uint16_t cs,ax,bx,cx,dx,ss,sp;
    uint8_t opcode[4];
};
static bool treehouse_cpu_run_enabled=false;
static unsigned treehouse_cpu_run_count=0,treehouse_cpu_run_error=0;
static uint64_t treehouse_cpu_run_instructions=0;
static uint64_t treehouse_cpu_run_strings=0;
static uint64_t treehouse_cpu_run_credits=0;
static uint64_t treehouse_cpu_run_phase=0,treehouse_cpu_run_serial=0;
static uint32_t treehouse_cpu_run_last=0;
static TreehouseCpuEvent treehouse_cpu_run_events[32768];
static INLINE void TreehouseCpuInstruction(uint32_t address) {
    if(!treehouse_cpu_run_enabled)return;
    ++treehouse_cpu_run_instructions;treehouse_cpu_run_last=address;
}
static INLINE void TreehouseCpuStringIteration(){if(treehouse_cpu_run_enabled)++treehouse_cpu_run_strings;}
static INLINE void TreehouseCpuCycleCredit(){if(treehouse_cpu_run_enabled)++treehouse_cpu_run_credits;}
void TreehouseCpuBoundary(unsigned kind,unsigned id,int result) {
    if(!treehouse_cpu_run_enabled)return;
    if(kind==1){treehouse_cpu_run_phase=1;++treehouse_cpu_run_serial;}
    else if(kind==3)treehouse_cpu_run_phase=2;
    if(treehouse_cpu_run_count>=32768){treehouse_cpu_run_error=1;return;}
    TreehouseCpuEvent& e=treehouse_cpu_run_events[treehouse_cpu_run_count++];memset(&e,0,sizeof(e));
    e.milliseconds=PIC_FullIndex();e.instructions=treehouse_cpu_run_instructions;e.strings=treehouse_cpu_run_strings;e.credits=treehouse_cpu_run_credits;e.io=CPU_IODelayRemoved;
    e.cycles=CPU_Cycles;e.left=CPU_CycleLeft;e.maximum=CPU_CycleMax;e.result=result;e.kind=kind;e.id=id;e.ticks=PIC_Ticks;
    e.eip=reg_eip;e.last_address=treehouse_cpu_run_last;e.flags=reg_flags;e.cs=SegValue(cs);
    e.ax=reg_ax;e.bx=reg_bx;e.cx=reg_cx;e.dx=reg_dx;e.ss=SegValue(ss);e.sp=reg_sp;
    if(e.last_address)for(unsigned i=0;i<4;++i)e.opcode[i]=mem_readb(e.last_address+i);
    if(kind==2||kind==4)treehouse_cpu_run_phase=0;
}
void TreehouseCpuProbeContext(uint64_t* values){values[0]=treehouse_cpu_run_instructions;values[1]=treehouse_cpu_run_strings;values[2]=treehouse_cpu_run_credits;values[3]=treehouse_cpu_run_phase;values[4]=treehouse_cpu_run_serial;}
extern "C" RETRO_API unsigned retro_treehouse_cpu_run_size(void){return sizeof(TreehouseCpuEvent);}
extern "C" RETRO_API unsigned retro_treehouse_cpu_run_status(void){return treehouse_cpu_run_error;}
extern "C" RETRO_API void retro_treehouse_cpu_run_configure(unsigned enabled){
    treehouse_cpu_run_enabled=enabled!=0;treehouse_cpu_run_count=treehouse_cpu_run_error=0;treehouse_cpu_run_instructions=treehouse_cpu_run_last=treehouse_cpu_run_strings=treehouse_cpu_run_credits=0;
    treehouse_cpu_run_phase=treehouse_cpu_run_serial=0;
}
extern "C" RETRO_API unsigned retro_treehouse_cpu_run_read(TreehouseCpuEvent* events,unsigned capacity){
    unsigned n=treehouse_cpu_run_count<capacity?treehouse_cpu_run_count:capacity;
    memcpy(events,treehouse_cpu_run_events,n*sizeof(TreehouseCpuEvent));treehouse_cpu_run_count-=n;
    if(treehouse_cpu_run_count)memmove(treehouse_cpu_run_events,treehouse_cpu_run_events+n,treehouse_cpu_run_count*sizeof(TreehouseCpuEvent));return n;
}
extern "C" RETRO_API const char* retro_treehouse_cpu_callback_description(unsigned id){return id<CB_MAX?CALLBACK_GetDescription(id):0;}
