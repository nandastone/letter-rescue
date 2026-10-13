// Read-only GenerateDMASound boundaries. Input PCM and mixer deltas are fixtures.
#include "libretro.h"
#include "cpu.h"
#include "mem.h"
#include <stdint.h>
#include <string.h>
extern "C" void TreehouseReadSoundHardware(uint32_t* out);
extern "C" void TreehouseReadMixerState(uint32_t* out);
extern "C" void TreehouseReadMixerWork(uint32_t offset,int32_t* out,uint32_t count);
struct TreehouseAudioDmaRow {
    uint32_t ordinal,requested,ticks,frames;
    int32_t budget,left,maximum;int64_t io;double milliseconds,last_before,last_after;
    uint32_t hardware_before[32],hardware_after[32],dma_before[8],dma_after[8];
    int32_t channel_before[16],channel_after[16];uint32_t mixer_before[10],mixer_after[10];
    uint8_t source[1024],pcm[1024];int32_t mixed_delta[8192];
};
static bool treehouse_audio_dma_enabled=false,treehouse_audio_dma_active=false;
static uint32_t treehouse_audio_dma_count=0,treehouse_audio_dma_total=0,treehouse_audio_dma_error=0;
static TreehouseAudioDmaRow treehouse_audio_dma_current,treehouse_audio_dma_rows[128];
static int32_t treehouse_audio_dma_work_before[32768];
static void TreehouseAudioDmaState(uint32_t* dma,int32_t* channel){
    const uint32_t d[]={sb.dma.autoinit,sb.dma.autosize,sb.dma.stereo,sb.dma.sign,sb.dma.fade,sb.dma.mul,sb.dma.remain_size,sb.dma.chan?sb.dma.chan->DMA16:0};memcpy(dma,d,sizeof(d));
    MixerChannel* c=sb.chan;
    const int32_t values[]={(int32_t)c->enabled,(int32_t)c->done,(int32_t)c->needed,(int32_t)c->freq_add,(int32_t)c->freq_counter,(int32_t)c->prevSample[0],(int32_t)c->prevSample[1],(int32_t)c->nextSample[0],(int32_t)c->nextSample[1],(int32_t)c->interpolate,(int32_t)c->last_samples_were_silence,(int32_t)c->last_samples_were_stereo,(int32_t)c->offset[0],(int32_t)c->offset[1],c->volmul[0],c->volmul[1]};memcpy(channel,values,sizeof(values));
}
struct TreehouseAudioDmaScope {
    bool recording;
    TreehouseAudioDmaScope(uint32_t requested):recording(treehouse_audio_dma_enabled&&!treehouse_audio_dma_error){
        if(!recording)return;if(treehouse_audio_dma_active){treehouse_audio_dma_error=1;recording=false;return;}treehouse_audio_dma_active=true;
        TreehouseAudioDmaRow& r=treehouse_audio_dma_current;memset(&r,0,sizeof(r));r.ordinal=treehouse_audio_dma_total++;r.requested=requested;r.ticks=PIC_Ticks;r.budget=CPU_Cycles;r.left=CPU_CycleLeft;r.maximum=CPU_CycleMax;r.io=CPU_IODelayRemoved;r.milliseconds=PIC_FullIndex();r.last_before=last_dma_callback;
        TreehouseReadSoundHardware(r.hardware_before);TreehouseAudioDmaState(r.dma_before,r.channel_before);TreehouseReadMixerState(r.mixer_before);
        if(!sb.dma.chan||sb.dma.chan->DMA16){treehouse_audio_dma_error=2;recording=false;treehouse_audio_dma_active=false;return;}
        for(unsigned i=0;i<1024;i++)r.source[i]=mem_readb(sb.dma.chan->pagebase+((sb.dma.chan->curraddr+i)&0xffff));
        TreehouseReadMixerWork(sb.chan->done,treehouse_audio_dma_work_before,16384);
    }
    ~TreehouseAudioDmaScope(){
        if(!recording)return;TreehouseAudioDmaRow& r=treehouse_audio_dma_current;
        r.last_after=last_dma_callback;TreehouseReadSoundHardware(r.hardware_after);TreehouseAudioDmaState(r.dma_after,r.channel_after);TreehouseReadMixerState(r.mixer_after);memcpy(r.pcm,sb.dma.buf.b8,1024);
        r.frames=sb.chan->done-r.channel_before[1];if(r.frames>4096){treehouse_audio_dma_error=3;treehouse_audio_dma_active=false;return;}
        TreehouseReadMixerWork(r.channel_before[1],r.mixed_delta,r.frames);
        for(unsigned i=0;i<r.frames*2;i++)r.mixed_delta[i]=(int32_t)((uint32_t)r.mixed_delta[i]-(uint32_t)treehouse_audio_dma_work_before[i]);
        if(treehouse_audio_dma_count>=128){treehouse_audio_dma_error=4;treehouse_audio_dma_active=false;return;}
        treehouse_audio_dma_rows[treehouse_audio_dma_count++]=r;treehouse_audio_dma_active=false;
    }
};
extern "C" RETRO_API unsigned retro_treehouse_audio_dma_size(void){return sizeof(TreehouseAudioDmaRow);}
extern "C" RETRO_API unsigned retro_treehouse_audio_dma_status(void){return treehouse_audio_dma_error;}
extern "C" RETRO_API void retro_treehouse_audio_dma_configure(unsigned enabled){treehouse_audio_dma_enabled=!!enabled;treehouse_audio_dma_count=treehouse_audio_dma_total=treehouse_audio_dma_error=0;treehouse_audio_dma_active=false;}
extern "C" RETRO_API unsigned retro_treehouse_audio_dma_read(TreehouseAudioDmaRow* out,unsigned capacity){
    unsigned n=treehouse_audio_dma_count<capacity?treehouse_audio_dma_count:capacity;memcpy(out,treehouse_audio_dma_rows,n*sizeof(TreehouseAudioDmaRow));treehouse_audio_dma_count-=n;
    if(treehouse_audio_dma_count)memmove(treehouse_audio_dma_rows,treehouse_audio_dma_rows+n,treehouse_audio_dma_count*sizeof(TreehouseAudioDmaRow));return n;
}
