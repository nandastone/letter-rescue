// Read-only event queue observations for the isolated research DLL.
#include "libretro.h"
#include <stdint.h>
#include <string.h>
struct TreehousePicState {
    int32_t cycles,left,maximum;
    uint32_t ticks,count,head_handler,head_value,hash;
    float head_index,tick_index;
    double milliseconds;
    uint32_t servicing;
    float service_index;
};
struct TreehousePicRow {
    uint32_t kind,handler,value;
    float delay;
    TreehousePicState before,after;
};
struct TreehousePicEntry { uint32_t handler,value; float index; };
static bool treehouse_pic_enabled=false;
static unsigned treehouse_pic_count=0,treehouse_pic_error=0,treehouse_pic_handler_count=0,treehouse_pic_initial_count=0;
static PIC_EventHandler treehouse_pic_handlers[128];
static TreehousePicRow treehouse_pic_rows[262144];
static TreehousePicState treehouse_pic_initial_state;
static TreehousePicEntry treehouse_pic_initial_entries[512];
static unsigned TreehousePicHandler(PIC_EventHandler handler) {
    if(!handler)return 0;
    for(unsigned i=0;i<treehouse_pic_handler_count;++i)if(treehouse_pic_handlers[i]==handler)return i+1;
    if(treehouse_pic_handler_count>=128){treehouse_pic_error=1;return 0;}
    treehouse_pic_handlers[treehouse_pic_handler_count++]=handler;return treehouse_pic_handler_count;
}
static void TreehousePicStateRead(TreehousePicState& s) {
    memset(&s,0,sizeof(s));s.cycles=CPU_Cycles;s.left=CPU_CycleLeft;s.maximum=CPU_CycleMax;s.ticks=PIC_Ticks;
    s.tick_index=PIC_TickIndex();s.milliseconds=PIC_FullIndex();s.servicing=InEventService;s.service_index=srv_lag;
    s.hash=2166136261u;
    for(PICEntry* e=pic_queue.next_entry;e;e=e->next){
        uint32_t handler=TreehousePicHandler(e->pic_event),bits;memcpy(&bits,&e->index,4);
        if(!s.count){s.head_handler=handler;s.head_value=e->value;s.head_index=e->index;}
        uint32_t words[3]={handler,(uint32_t)e->value,bits};
        for(unsigned i=0;i<3;++i)for(unsigned shift=0;shift<32;shift+=8)s.hash=(s.hash^((words[i]>>shift)&255))*16777619u;
        ++s.count;
    }
}
static unsigned TreehousePicBegin(unsigned kind,PIC_EventHandler handler=0,float delay=0,Bitu value=0) {
    if(!treehouse_pic_enabled)return 262144;
    if(treehouse_pic_count>=262144){treehouse_pic_error=1;return 262144;}
    unsigned token=treehouse_pic_count++;TreehousePicRow& r=treehouse_pic_rows[token];
    memset(&r,0,sizeof(r));r.kind=kind;r.handler=TreehousePicHandler(handler);r.delay=delay;r.value=value;
    TreehousePicStateRead(r.before);return token;
}
static void TreehousePicEnd(unsigned token) { if(token<262144)TreehousePicStateRead(treehouse_pic_rows[token].after); }
extern "C" RETRO_API unsigned retro_treehouse_pic_state_size(void){return sizeof(TreehousePicState);}
extern "C" RETRO_API unsigned retro_treehouse_pic_row_size(void){return sizeof(TreehousePicRow);}
extern "C" RETRO_API unsigned retro_treehouse_pic_entry_size(void){return sizeof(TreehousePicEntry);}
extern "C" RETRO_API unsigned retro_treehouse_pic_status(void){return treehouse_pic_error;}
extern "C" RETRO_API void retro_treehouse_pic_configure(unsigned enabled){
    treehouse_pic_enabled=enabled!=0;treehouse_pic_count=treehouse_pic_error=treehouse_pic_handler_count=treehouse_pic_initial_count=0;
    if(!enabled)return;
    TreehousePicStateRead(treehouse_pic_initial_state);
    for(PICEntry* e=pic_queue.next_entry;e;e=e->next){
        if(treehouse_pic_initial_count>=512){treehouse_pic_error=1;break;}
        TreehousePicEntry& r=treehouse_pic_initial_entries[treehouse_pic_initial_count++];r.handler=TreehousePicHandler(e->pic_event);r.value=e->value;r.index=e->index;
    }
}
extern "C" RETRO_API unsigned retro_treehouse_pic_initial(TreehousePicState* state,TreehousePicEntry* entries,unsigned capacity){
    *state=treehouse_pic_initial_state;unsigned n=treehouse_pic_initial_count<capacity?treehouse_pic_initial_count:capacity;
    memcpy(entries,treehouse_pic_initial_entries,n*sizeof(TreehousePicEntry));return n;
}
extern "C" RETRO_API unsigned retro_treehouse_pic_read(TreehousePicRow* rows,unsigned capacity){
    unsigned n=treehouse_pic_count<capacity?treehouse_pic_count:capacity;memcpy(rows,treehouse_pic_rows,n*sizeof(TreehousePicRow));
    treehouse_pic_count-=n;if(treehouse_pic_count)memmove(treehouse_pic_rows,treehouse_pic_rows+n,treehouse_pic_count*sizeof(TreehousePicRow));return n;
}
