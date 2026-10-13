// Read-only instruction-entry probe for the pinned normal CPU reference core.
// Included only in a separate research DLL, never in the browser runtime.
#include "libretro.h"
#include "vga.h"
#include <stdint.h>
#include <string.h>

struct TreehouseTraceEvent {
    double milliseconds;
    uint32_t address, pit;
    uint16_t ax, bx, cx, dx, si, di, bp, sp, ss, ds, es, cs;
    uint16_t stack[16];
};
static uint8_t treehouse_watch[0x100000];
static TreehouseTraceEvent treehouse_events[16384];
static unsigned treehouse_count = 0, treehouse_overflow = 0;
static uint32_t treehouse_clock = 0;
static bool treehouse_enabled = false;

// Heap fixtures exclude video memory and are retained only for offline model
// comparisons. No snapshot is fed to the browser game.
struct TreehouseHeapSnapshot { double milliseconds; uint32_t phase, requested; uint16_t ss, sp, ds; };
static uint32_t treehouse_heap_begin=0, treehouse_heap_end=0, treehouse_heap_request=0;
static unsigned treehouse_heap_count=0, treehouse_heap_error=0;
static bool treehouse_heap_active=false;
static TreehouseHeapSnapshot treehouse_heap_metadata[128];
static uint8_t treehouse_heap_memory[128][0xa0000];
extern "C" RETRO_API unsigned retro_treehouse_heap_snapshot_size(void) { return sizeof(TreehouseHeapSnapshot); }
extern "C" RETRO_API void retro_treehouse_heap_configure(uint32_t begin,uint32_t end,uint32_t requested) {
    treehouse_heap_begin=begin;treehouse_heap_end=end;treehouse_heap_request=requested;
    treehouse_heap_count=treehouse_heap_error=0;treehouse_heap_active=false;
}
extern "C" RETRO_API unsigned retro_treehouse_heap_count(void) { return treehouse_heap_count; }
extern "C" RETRO_API unsigned retro_treehouse_heap_status(void) { return treehouse_heap_error|(treehouse_heap_active?2:0); }
extern "C" RETRO_API unsigned retro_treehouse_heap_read(unsigned index,TreehouseHeapSnapshot* metadata,uint8_t* memory,unsigned capacity) {
    if(index>=treehouse_heap_count || capacity<0xa0000)return 0;
    *metadata=treehouse_heap_metadata[index];memcpy(memory,treehouse_heap_memory[index],0xa0000);return 0xa0000;
}
static INLINE void TreehouseHeapInstruction(PhysPt address) {
    if(!treehouse_heap_begin)return;
    unsigned phase;
    if(address==treehouse_heap_begin){
        if(treehouse_heap_active){treehouse_heap_error=1;return;}
        if(treehouse_heap_request && mem_readd(SegPhys(ss)+(uint16_t)(reg_sp+4))!=treehouse_heap_request)return;
        treehouse_heap_active=true;phase=0;
    }else if(address==treehouse_heap_end && treehouse_heap_active){treehouse_heap_active=false;phase=1;}
    else return;
    if(treehouse_heap_count>=128){treehouse_heap_error=1;return;}
    TreehouseHeapSnapshot& s=treehouse_heap_metadata[treehouse_heap_count];
    s.milliseconds=PIC_FullIndex();s.phase=phase;s.requested=phase ? treehouse_heap_metadata[treehouse_heap_count-1].requested : mem_readd(SegPhys(ss)+(uint16_t)(reg_sp+4));
    s.ss=SegValue(ss);s.sp=reg_sp;s.ds=SegValue(ds);
    MEM_BlockRead(0,treehouse_heap_memory[treehouse_heap_count],0xa0000);++treehouse_heap_count;
}

// Optional function-work observer. Counts instruction entries without changing
// any guest registers, memory, cycle budgets or timer scheduling. REP re-entry
// after a CPU slice is reported separately from its logical instruction.
struct TreehouseWorkCount { uint32_t call, address, entries, repetitions; };
struct TreehouseWorkSlice { uint32_t call, address, remaining; int32_t budget; };
struct TreehouseWorkCall {
    double begin, end;
    uint32_t ordinal;
    uint16_t stack[16], header[3];
};
struct TreehouseWorkBlock { uint32_t call; uint16_t header[3]; };
static TreehouseWorkBlock treehouse_work_blocks[4096];
struct TreehouseWorkResult { uint32_t call; uint16_t ax,cx,dx; };
static TreehouseWorkResult treehouse_work_results[4096];
struct TreehouseTimerState { uint32_t call; uint16_t before[9], after[9]; };
static TreehouseTimerState treehouse_timer_states[4096];
static INLINE void TreehouseReadTimerState(uint16_t* out) {
    // Pinned resident DS offsets relative to the configured 201E tick word.
    static const int offsets[9]={0,2,-8,-6,-4,-2,18,20,22};
    for(unsigned i=0;i<9;++i)out[i]=mem_readw(treehouse_clock+offsets[i]);
}
static uint32_t treehouse_work_begin=0, treehouse_work_end=0, treehouse_work_base=0;
static uint32_t treehouse_work_length=0, treehouse_work_header=0, treehouse_work_last=0;
static uint32_t treehouse_work_entries[65536], treehouse_work_repetitions[65536];
static uint8_t treehouse_work_allowed[65536];
static bool treehouse_work_filtered=false;
static TreehouseWorkCall treehouse_work_calls[4096];
static TreehouseWorkCount treehouse_work_counts[524288];
static TreehouseWorkSlice treehouse_work_slices[2048];
static unsigned treehouse_work_slice_count=0;
static unsigned treehouse_work_call_count=0, treehouse_work_count=0, treehouse_work_error=0;
static bool treehouse_work_active=false;

extern "C" RETRO_API unsigned retro_treehouse_work_version(void) { return 1; }
extern "C" RETRO_API unsigned retro_treehouse_work_call_size(void) { return sizeof(TreehouseWorkCall); }
extern "C" RETRO_API void retro_treehouse_work_configure(uint32_t begin, uint32_t end, uint32_t base, uint32_t length, uint32_t header) {
    treehouse_work_begin=begin; treehouse_work_end=end; treehouse_work_base=base;
    treehouse_work_length=length<=65536?length:0; treehouse_work_header=header;
    treehouse_work_call_count=treehouse_work_count=treehouse_work_error=0;
    treehouse_work_slice_count=0;
    treehouse_work_active=false;
    treehouse_work_filtered=false;
}
// Optional disjoint code regions allow a caller and specific external helpers
// to be counted without including unrelated callees in the intervening space.
extern "C" RETRO_API void retro_treehouse_work_regions(const uint32_t* pairs,unsigned count) {
    memset(treehouse_work_allowed,0,sizeof(treehouse_work_allowed));
    treehouse_work_filtered=true;
    for(unsigned i=0;i<count;++i){
        uint32_t begin=pairs[2*i],end=pairs[2*i+1];
        if(begin<treehouse_work_base || end<begin || end>treehouse_work_base+treehouse_work_length){treehouse_work_error=1;return;}
        memset(treehouse_work_allowed+begin-treehouse_work_base,1,end-begin);
    }
}
extern "C" RETRO_API unsigned retro_treehouse_work_read_calls(TreehouseWorkCall* out, unsigned capacity) {
    unsigned count=treehouse_work_call_count<capacity?treehouse_work_call_count:capacity;
    memcpy(out,treehouse_work_calls,count*sizeof(TreehouseWorkCall)); return count;
}
extern "C" RETRO_API unsigned retro_treehouse_work_block_size(void) { return sizeof(TreehouseWorkBlock); }
extern "C" RETRO_API unsigned retro_treehouse_work_read_blocks(TreehouseWorkBlock* out,unsigned capacity) {
    unsigned count=treehouse_work_call_count<capacity?treehouse_work_call_count:capacity;
    memcpy(out,treehouse_work_blocks,count*sizeof(TreehouseWorkBlock));return count;
}
extern "C" RETRO_API unsigned retro_treehouse_work_result_size(void) { return sizeof(TreehouseWorkResult); }
extern "C" RETRO_API unsigned retro_treehouse_timer_state_size(void) { return sizeof(TreehouseTimerState); }
extern "C" RETRO_API unsigned retro_treehouse_timer_read_states(TreehouseTimerState* out,unsigned capacity) {
    if(treehouse_work_header!=17)return 0;
    unsigned count=treehouse_work_call_count<capacity?treehouse_work_call_count:capacity;
    memcpy(out,treehouse_timer_states,count*sizeof(TreehouseTimerState));return count;
}
extern "C" RETRO_API unsigned retro_treehouse_work_read_results(TreehouseWorkResult* out,unsigned capacity) {
    unsigned count=treehouse_work_call_count<capacity?treehouse_work_call_count:capacity;
    memcpy(out,treehouse_work_results,count*sizeof(TreehouseWorkResult));return count;
}
extern "C" RETRO_API unsigned retro_treehouse_work_read_counts(TreehouseWorkCount* out, unsigned capacity) {
    unsigned count=treehouse_work_count<capacity?treehouse_work_count:capacity;
    memcpy(out,treehouse_work_counts,count*sizeof(TreehouseWorkCount)); return count;
}
extern "C" RETRO_API unsigned retro_treehouse_work_read_slices(TreehouseWorkSlice* out, unsigned capacity) {
    unsigned count=treehouse_work_slice_count<capacity?treehouse_work_slice_count:capacity;
    memcpy(out,treehouse_work_slices,count*sizeof(TreehouseWorkSlice)); return count;
}
extern "C" RETRO_API unsigned retro_treehouse_work_status(void) { return treehouse_work_error | (treehouse_work_active?2:0); }

static INLINE void TreehouseProfileInstruction(PhysPt address) {
    if (!treehouse_work_length) return;
    if (address==treehouse_work_begin) {
        if (treehouse_work_active || treehouse_work_call_count>=4096) { treehouse_work_error=1; return; }
        treehouse_work_active=true; treehouse_work_last=0;
        memset(treehouse_work_entries,0,treehouse_work_length*sizeof(uint32_t));
        memset(treehouse_work_repetitions,0,treehouse_work_length*sizeof(uint32_t));
        TreehouseWorkCall& call=treehouse_work_calls[treehouse_work_call_count];
        memset(&call,0,sizeof(call)); call.begin=PIC_FullIndex(); call.ordinal=treehouse_work_call_count;
        if(treehouse_work_header==17){
            TreehouseTimerState& state=treehouse_timer_states[treehouse_work_call_count];
            state.call=treehouse_work_call_count;TreehouseReadTimerState(state.before);
        }
        TreehouseWorkBlock& block=treehouse_work_blocks[treehouse_work_call_count];
        memset(&block,0,sizeof(block));block.call=treehouse_work_call_count;
        for (unsigned i=0;i<16;++i) call.stack[i]=mem_readw(SegPhys(ss)+(uint16_t)(reg_sp+i*2));
        if (treehouse_work_header && treehouse_work_header<15) {
            PhysPt ptr=(call.stack[treehouse_work_header+1]<<4)+call.stack[treehouse_work_header];
            for (unsigned i=0;i<3;++i) call.header[i]=mem_readw(ptr+2*i);
        } else if(treehouse_work_header==16) {
            // Offline cache-entry input: directory handle and its state before
            // the function changes anything. No guest memory is written.
            call.header[0]=mem_readw(SegPhys(ds)+reg_di+9);
            if(call.header[0]) {
                call.header[1]=mem_readw(SegPhys(ss)+call.header[0]);
                call.header[2]=mem_readw(SegPhys(ss)+call.header[0]+2);
                PhysPt ptr=(call.header[2]<<4)+(call.header[1]&15);
                if(ptr && !(call.header[1]&0x200))for(unsigned i=0;i<3;++i)block.header[i]=mem_readw(ptr+2*i);
            }
        }
    }
    if (!treehouse_work_active) return;
    if (address>=treehouse_work_base && address<treehouse_work_base+treehouse_work_length && (!treehouse_work_filtered || treehouse_work_allowed[address-treehouse_work_base])) {
        unsigned at=address-treehouse_work_base;
        ++treehouse_work_entries[at];
        uint8_t op=mem_readb(address);
        // The configured routines have no address/operand-size prefixes.
        // Count the original CX once, not the remaining CX on REP resumption.
        if (op==0xf2 || op==0xf3) {
            if (address!=treehouse_work_last) treehouse_work_repetitions[at]+=reg_cx;
            if (treehouse_work_slice_count>=2048) treehouse_work_error=1;
            else {
                TreehouseWorkSlice& slice=treehouse_work_slices[treehouse_work_slice_count++];
                slice.call=treehouse_work_call_count; slice.address=address;
                slice.remaining=reg_cx; slice.budget=CPU_Cycles;
            }
        }
        treehouse_work_last=address;
    }
    if (address==treehouse_work_end) {
        if(treehouse_work_header==17)TreehouseReadTimerState(treehouse_timer_states[treehouse_work_call_count].after);
        treehouse_work_calls[treehouse_work_call_count].end=PIC_FullIndex();
        TreehouseWorkResult& result=treehouse_work_results[treehouse_work_call_count];
        result.call=treehouse_work_call_count;result.ax=reg_ax;result.cx=reg_cx;result.dx=reg_dx;
        for (unsigned i=0;i<treehouse_work_length;++i) if (treehouse_work_entries[i]) {
            if (treehouse_work_count>=524288) { treehouse_work_error=1; break; }
            TreehouseWorkCount& row=treehouse_work_counts[treehouse_work_count++];
            row.call=treehouse_work_call_count; row.address=treehouse_work_base+i;
            row.entries=treehouse_work_entries[i]; row.repetitions=treehouse_work_repetitions[i];
        }
        ++treehouse_work_call_count; treehouse_work_active=false;
    }
}

extern "C" RETRO_API unsigned retro_treehouse_trace_version(void) { return 1; }
extern "C" RETRO_API double retro_treehouse_milliseconds(void) { return PIC_FullIndex(); }
extern "C" RETRO_API unsigned retro_treehouse_trace_size(void) { return sizeof(TreehouseTraceEvent); }
extern "C" RETRO_API void retro_treehouse_video_timing(double* out) {
    out[0]=vga.mode; out[1]=vga.draw.mode; out[2]=vga.draw.width; out[3]=vga.draw.height;
    out[4]=vga.draw.bpp; out[5]=vga.draw.delay.framestart; out[6]=vga.draw.delay.vtotal;
    out[7]=vga.draw.delay.htotal; out[8]=vga.draw.delay.parts; out[9]=vga.draw.parts_total;
    out[10]=vga.draw.parts_lines; out[11]=vga.draw.lines_total; out[12]=vga.draw.address_add;
    out[13]=vga.draw.address_line_total; out[14]=vga.draw.lines_scaled; out[15]=vga.config.real_start;
}
extern "C" RETRO_API unsigned retro_treehouse_live_rgb(uint8_t* out, unsigned capacity) {
    if (vga.draw.width!=320 || vga.draw.height!=200 || vga.draw.bpp!=8 || capacity<192000) return 0;
    bool planar=(vga.mode==M_EGA || vga.mode==M_LIN4);
    Bitu start=(vga.config.real_start+vga.draw.bytes_skip)*(planar?8:4)+vga.draw.panning;
    for (unsigned y=0;y<200;++y) for (unsigned x=0;x<320;++x) {
        unsigned index=vga.draw.linear_base[(start+y*vga.draw.address_add+x)&vga.draw.linear_mask];
        if (planar) index=vga.dac.combine[index&15];
        const RGBEntry& c=vga.dac.rgb[index&vga.dac.pel_mask];
        *out++=(c.red<<2)|(c.red>>4); *out++=(c.green<<2)|(c.green>>4); *out++=(c.blue<<2)|(c.blue>>4);
    }
    return 192000;
}
// Call exports only while the deterministic capture boundary holds the worker.
extern "C" RETRO_API void retro_treehouse_trace_configure(const uint32_t* addresses, unsigned count, uint32_t clock) {
    treehouse_enabled = false;
    memset(treehouse_watch, 0, sizeof(treehouse_watch));
    for (unsigned i = 0; i < count; ++i)
        if (addresses[i] < sizeof(treehouse_watch)) treehouse_watch[addresses[i]] = 1;
    treehouse_clock = clock;
    treehouse_count = treehouse_overflow = 0;
    treehouse_enabled = count != 0;
}
extern "C" RETRO_API unsigned retro_treehouse_trace_read(TreehouseTraceEvent* out, unsigned capacity) {
    unsigned count = treehouse_count < capacity ? treehouse_count : capacity;
    memcpy(out, treehouse_events, count * sizeof(TreehouseTraceEvent));
    memmove(treehouse_events, treehouse_events + count, (treehouse_count - count) * sizeof(TreehouseTraceEvent));
    treehouse_count -= count;
    return count;
}
extern "C" RETRO_API unsigned retro_treehouse_trace_overflow(void) { return treehouse_overflow; }

static INLINE void TreehouseTraceInstruction(PhysPt address) {
    TreehouseHeapInstruction(address);
    TreehouseProfileInstruction(address);
    if (!treehouse_enabled || address >= sizeof(treehouse_watch) || !treehouse_watch[address]) return;
    if (treehouse_count == sizeof(treehouse_events) / sizeof(treehouse_events[0])) { ++treehouse_overflow; return; }
    TreehouseTraceEvent& e = treehouse_events[treehouse_count++];
    e.milliseconds = PIC_FullIndex(); e.address = address; e.pit = mem_readd(treehouse_clock);
    e.ax = reg_ax; e.bx = reg_bx; e.cx = reg_cx; e.dx = reg_dx;
    e.si = reg_si; e.di = reg_di; e.bp = reg_bp; e.sp = reg_sp;
    e.ss = SegValue(ss); e.ds = SegValue(ds); e.es = SegValue(es); e.cs = SegValue(cs);
    for (unsigned i = 0; i < 16; ++i) e.stack[i] = mem_readw(SegPhys(ss) + (uint16_t)(reg_sp + i * 2));
}
