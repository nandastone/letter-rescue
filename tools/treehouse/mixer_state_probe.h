// Included after the pinned mixer implementation. Pure observations only.
#include <stdint.h>
extern "C" void TreehouseReadMixerState(uint32_t* out){
    const uint32_t values[]={mixer.freq,(uint32_t)mixer.done,(uint32_t)mixer.needed,(uint32_t)mixer.pos,mixer.tick_add,mixer.tick_counter,mixer.blocksize,(uint32_t)mixer.min_needed,(uint32_t)mixer.max_needed,mixer.nosound};
    for(unsigned i=0;i<10;i++)out[i]=values[i];
}
extern "C" void TreehouseReadMixerWork(uint32_t offset,int32_t* out,uint32_t count){
    for(unsigned i=0;i<count;i++){unsigned at=(mixer.pos+offset+i)&MIXER_BUFMASK;out[2*i]=mixer.work[at][0];out[2*i+1]=mixer.work[at][1];}
}
