// Read-only PIC controller operations, included after pinned controller globals.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
extern void TreehouseCpuProbeContext(uint64_t* values);
struct TreehouseIrqController {
    uint32_t icw_words,icw_index,special,auto_eoi,rotate,single,request_isr,vector,irr,imr,imrr,isr,isrr,active;
};
struct TreehouseIrqState {
    int32_t cycles,left;
    uint32_t check,interrupt_enabled,trap;
    TreehouseIrqController controllers[2];
};
struct TreehouseIrqRow {
    double milliseconds;
    uint64_t context[5];
    int64_t io;
    uint32_t kind,arg,value;
    int32_t vector;
    TreehouseIrqState before,after;
};
static bool treehouse_irq_enabled=false;
static unsigned treehouse_irq_count=0,treehouse_irq_error=0,treehouse_irq_active=65536;
static TreehouseIrqRow treehouse_irq_rows[65536];
static TreehouseIrqState treehouse_irq_initial;
static void TreehouseIrqStateRead(TreehouseIrqState& s){
    memset(&s,0,sizeof(s));s.cycles=CPU_Cycles;s.left=CPU_CycleLeft;s.check=PIC_IRQCheck;s.interrupt_enabled=GETFLAG(IF)?1:0;s.trap=cpudecoder==CPU_Core_Normal_Trap_Run;
    for(unsigned i=0;i<2;++i){PIC_Controller& p=pics[i];TreehouseIrqController& c=s.controllers[i];
        c.icw_words=p.icw_words;c.icw_index=p.icw_index;c.special=p.special;c.auto_eoi=p.auto_eoi;c.rotate=p.rotate_on_auto_eoi;c.single=p.single;c.request_isr=p.request_issr;c.vector=p.vector_base;
        c.irr=p.irr;c.imr=p.imr;c.imrr=p.imrr;c.isr=p.isr;c.isrr=p.isrr;c.active=p.active_irq;
    }
}
class TreehouseIrqScope {
    unsigned token,previous;
public:
    TreehouseIrqScope(unsigned kind,unsigned arg=0,unsigned value=0):token(65536),previous(treehouse_irq_active){
        if(!treehouse_irq_enabled)return;
        if(treehouse_irq_count>=65536){treehouse_irq_error=1;return;}
        token=treehouse_irq_count++;treehouse_irq_active=token;TreehouseIrqRow& r=treehouse_irq_rows[token];memset(&r,0,sizeof(r));
        r.kind=kind;r.arg=arg;r.value=value;r.vector=-1;r.milliseconds=PIC_FullIndex();r.io=CPU_IODelayRemoved;TreehouseCpuProbeContext(r.context);TreehouseIrqStateRead(r.before);
    }
    ~TreehouseIrqScope(){if(token<65536){TreehouseIrqStateRead(treehouse_irq_rows[token].after);treehouse_irq_active=previous;}}
};
static void TreehouseIrqVector(unsigned vector){if(treehouse_irq_enabled&&treehouse_irq_active<65536){TreehouseIrqRow& r=treehouse_irq_rows[treehouse_irq_active];if(r.vector!=-1)treehouse_irq_error=1;r.vector=vector;}}
extern "C" RETRO_API unsigned retro_treehouse_irq_state_size(void){return sizeof(TreehouseIrqState);}
extern "C" RETRO_API unsigned retro_treehouse_irq_row_size(void){return sizeof(TreehouseIrqRow);}
extern "C" RETRO_API unsigned retro_treehouse_irq_status(void){return treehouse_irq_error;}
extern "C" RETRO_API void retro_treehouse_irq_configure(unsigned enabled){treehouse_irq_enabled=enabled!=0;treehouse_irq_count=treehouse_irq_error=0;treehouse_irq_active=65536;TreehouseIrqStateRead(treehouse_irq_initial);}
extern "C" RETRO_API void retro_treehouse_irq_initial(TreehouseIrqState* state){*state=treehouse_irq_initial;}
extern "C" RETRO_API unsigned retro_treehouse_irq_read(TreehouseIrqRow* rows,unsigned capacity){
    if(treehouse_irq_active<65536){treehouse_irq_error=1;return 0;}
    unsigned n=treehouse_irq_count<capacity?treehouse_irq_count:capacity;memcpy(rows,treehouse_irq_rows,n*sizeof(TreehouseIrqRow));treehouse_irq_count-=n;
    if(treehouse_irq_count)memmove(treehouse_irq_rows,treehouse_irq_rows+n,treehouse_irq_count*sizeof(TreehouseIrqRow));return n;
}
