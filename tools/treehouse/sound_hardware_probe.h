// Included after the pinned Sound Blaster implementation. Read-only state.
#include <stdint.h>
extern "C" void TreehouseReadSoundHardware(uint32_t* out){
    for(unsigned i=0;i<32;i++)out[i]=0;
    const uint32_t values[]={sb.hw.base,sb.hw.irq,sb.hw.dma8,sb.dsp.state,sb.dsp.write_busy,sb.dsp.out.used,sb.irq.pending_8bit,sb.irq.pending_16bit,sb.dsp.cmd,sb.dsp.cmd_len,sb.dsp.in.pos,sb.time_constant,sb.freq,(uint32_t)sb.mode,(uint32_t)sb.dma.mode,sb.dma.left,sb.dma.singlesize};
    for(unsigned i=0;i<sizeof(values)/sizeof(values[0]);i++)out[i]=values[i];
    DmaChannel* channel=GetDMAChannel(sb.hw.dma8);if(!channel)return;
    const uint32_t dma[]={channel->baseaddr,channel->curraddr,channel->basecnt,channel->currcnt,channel->pagenum,channel->masked,channel->request,channel->tcount,channel->autoinit,channel->increment};
    for(unsigned i=0;i<sizeof(dma)/sizeof(dma[0]);i++)out[17+i]=dma[i];
    out[27]=sb.speaker;out[28]=sb.type;out[29]=sb.mixer.stereo;out[30]=sb.dma.rate;out[31]=sb.dma.min;
}

extern "C" uint32_t TreehouseReadSoundDmaAutoInit(void){return sb.dma.autoinit;}

extern "C" void TreehouseReadSoundPlayback(uint32_t* dma,int32_t* channel,double* last){
    *last=last_dma_callback;
    const uint32_t d[]={sb.dma.autoinit,sb.dma.autosize,sb.dma.stereo,sb.dma.sign,sb.dma.fade,(uint32_t)sb.dma.mul,(uint32_t)sb.dma.remain_size,(uint32_t)(sb.dma.chan?sb.dma.chan->DMA16:0)};memcpy(dma,d,sizeof(d));
    MixerChannel* c=sb.chan;
    const int32_t values[]={(int32_t)c->enabled,(int32_t)c->done,(int32_t)c->needed,(int32_t)c->freq_add,(int32_t)c->freq_counter,(int32_t)c->prevSample[0],(int32_t)c->prevSample[1],(int32_t)c->nextSample[0],(int32_t)c->nextSample[1],(int32_t)c->interpolate,(int32_t)c->last_samples_were_silence,(int32_t)c->last_samples_were_stereo,(int32_t)c->offset[0],(int32_t)c->offset[1],c->volmul[0],c->volmul[1]};memcpy(channel,values,sizeof(values));
}
