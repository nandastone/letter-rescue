// Included only in the isolated pinned cpu.cpp capture build. Read-only.
#include "libretro.h"
#include "pic.h"
#include <stdint.h>
#include <string.h>
struct TreehouseInterruptState {
    int32_t cycles,left,maximum;int64_t io;uint32_t ticks;double milliseconds;
    uint32_t eip,flags,registers[8],segments[6],ss_base,cs_base,stack_mask,stack_notmask,code_big,extflags_toggle;
    int32_t direction;
};
struct TreehouseInterruptEntryRow {
    uint32_t ordinal,kind,parent,vector,old_eip,vector_base,vector_ip,vector_cs;
    uint32_t stack_addresses[3];uint16_t stack_before[3],stack_after[3];
    TreehouseInterruptState before,after;
};
struct TreehouseInterruptPending {uint32_t ordinal,vector,ss,esp;};
static bool treehouse_entry_enabled=false,treehouse_entry_recording=false;
static unsigned treehouse_entry_count=0,treehouse_entry_total=0,treehouse_entry_depth=0,treehouse_entry_error=0;
static TreehouseInterruptEntryRow treehouse_entry_rows[128],treehouse_entry_current;
static TreehouseInterruptPending treehouse_entry_pending[16];
static void TreehouseInterruptSnapshot(TreehouseInterruptState& s){
    s.cycles=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.io=CPU_IODelayRemoved;s.ticks=PIC_Ticks;s.milliseconds=PIC_FullIndex();
    s.eip=reg_eip;s.flags=reg_flags;
    s.registers[0]=reg_eax;s.registers[1]=reg_ecx;s.registers[2]=reg_edx;s.registers[3]=reg_ebx;s.registers[4]=reg_esp;s.registers[5]=reg_ebp;s.registers[6]=reg_esi;s.registers[7]=reg_edi;
    s.segments[0]=SegValue(es);s.segments[1]=SegValue(cs);s.segments[2]=SegValue(ss);s.segments[3]=SegValue(ds);s.segments[4]=SegValue(fs);s.segments[5]=SegValue(gs);
    s.ss_base=SegPhys(ss);s.cs_base=SegPhys(cs);s.stack_mask=cpu.stack.mask;s.stack_notmask=cpu.stack.notmask;s.code_big=cpu.code.big;s.extflags_toggle=CPU_extflags_toggle;s.direction=cpu.direction;
}
static void TreehouseInterruptRecord(){
    TreehouseInterruptEntryRow& r=treehouse_entry_current;TreehouseInterruptSnapshot(r.after);
    for(unsigned i=0;i<3;i++)r.stack_after[i]=mem_readw(r.stack_addresses[i]);
    if(treehouse_entry_count>=128){treehouse_entry_error=1;return;}treehouse_entry_rows[treehouse_entry_count++]=r;
}
static void TreehouseInterruptEnterBefore(Bitu num,Bitu type,Bitu oldeip){
    treehouse_entry_recording=false;
    if(!treehouse_entry_enabled||cpu.pmode||type||!(num==8||num==15||num==0x74))return;
    if(treehouse_entry_depth>=16){treehouse_entry_error=2;return;}
    TreehouseInterruptEntryRow& r=treehouse_entry_current;memset(&r,0,sizeof(r));r.ordinal=treehouse_entry_total++;r.kind=1;r.parent=treehouse_entry_depth?treehouse_entry_pending[treehouse_entry_depth-1].ordinal:0xffffffff;
    r.vector=num;r.old_eip=oldeip;r.vector_base=cpu.idt.GetBase();r.vector_ip=mem_readw(r.vector_base+4*num);r.vector_cs=mem_readw(r.vector_base+4*num+2);TreehouseInterruptSnapshot(r.before);
    for(unsigned i=0;i<3;i++){r.stack_addresses[i]=SegPhys(ss)+((reg_esp-2*(i+1))&cpu.stack.mask);r.stack_before[i]=mem_readw(r.stack_addresses[i]);}
    treehouse_entry_recording=true;
}
static void TreehouseInterruptEnterAfter(){
    if(!treehouse_entry_recording)return;TreehouseInterruptRecord();TreehouseInterruptPending& p=treehouse_entry_pending[treehouse_entry_depth++];
    p.ordinal=treehouse_entry_current.ordinal;p.vector=treehouse_entry_current.vector;p.ss=SegValue(ss);p.esp=reg_esp;treehouse_entry_recording=false;
}
static bool TreehouseInterruptReturnBefore(bool use32){
    if(!treehouse_entry_enabled||cpu.pmode||use32||!treehouse_entry_depth)return false;
    const TreehouseInterruptPending& p=treehouse_entry_pending[treehouse_entry_depth-1];
    if(SegValue(ss)!=p.ss||reg_esp!=p.esp)return false;
    TreehouseInterruptEntryRow& r=treehouse_entry_current;memset(&r,0,sizeof(r));r.ordinal=treehouse_entry_total++;r.kind=2;r.parent=p.ordinal;r.vector=p.vector;TreehouseInterruptSnapshot(r.before);
    for(unsigned i=0;i<3;i++){r.stack_addresses[i]=SegPhys(ss)+((reg_esp+2*i)&cpu.stack.mask);r.stack_before[i]=mem_readw(r.stack_addresses[i]);}
    return true;
}
static void TreehouseInterruptReturnAfter(){TreehouseInterruptRecord();treehouse_entry_depth--;}
extern "C" RETRO_API unsigned retro_treehouse_interrupt_entry_size(void){return sizeof(TreehouseInterruptEntryRow);}
extern "C" RETRO_API unsigned retro_treehouse_interrupt_entry_status(void){return treehouse_entry_error;}
extern "C" RETRO_API unsigned retro_treehouse_interrupt_entry_partial(void){return treehouse_entry_depth;}
extern "C" RETRO_API void retro_treehouse_interrupt_entry_configure(void){treehouse_entry_enabled=true;treehouse_entry_count=treehouse_entry_total=treehouse_entry_depth=treehouse_entry_error=0;}
extern "C" RETRO_API unsigned retro_treehouse_interrupt_entry_read(TreehouseInterruptEntryRow* out,unsigned capacity){
    const unsigned n=treehouse_entry_count<capacity?treehouse_entry_count:capacity;memcpy(out,treehouse_entry_rows,n*sizeof(TreehouseInterruptEntryRow));treehouse_entry_count-=n;
    if(treehouse_entry_count)memmove(treehouse_entry_rows,treehouse_entry_rows+n,treehouse_entry_count*sizeof(TreehouseInterruptEntryRow));return n;
}
