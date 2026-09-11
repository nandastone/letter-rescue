// WR1 observation-only instrumentation for DOSBox Pure 1.0-preview5.
// Copy to the core source root and apply wr1_core_trace.patch before building.
// SPDX-License-Identifier: GPL-2.0-or-later
#include "dosbox.h"
#include "cpu.h"
#include "mem.h"
#include "pic.h"
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <set>

extern const char* DBP_CPU_GetDecoderName();
extern double DBP_WR1_PIT0Start();
extern double DBP_WR1_PIT0Delay();
extern void DBP_WR1_PitState(FILE*);
extern void DBP_WR1_PicState(FILE*);
extern void DBP_WR1_VgaState(FILE*);
extern void DBP_WR1_KeyboardState(FILE*);
static std::mutex trace_mutex;
static std::atomic<unsigned> frontend_call(0), emulation_launch_call(0);
static unsigned observed_ds = 0;
static bool loader_active = false;
static bool opl_active = false;
static bool update_active = false;
static FILE* trace_file() {
    static FILE* file = []() -> FILE* {
        const char* path = std::getenv("DBP_WR1_TRACE_FILE");
        return path && *path ? std::fopen(path, "wb") : NULL;
    }();
    return file;
}

static int word(unsigned base, unsigned offset) { return (Bit16s)mem_readw(base + offset); }
static void movement_state(FILE* file,unsigned base,bool include_map) {
    struct Field { const char* name; unsigned offset; };
    const Field fields[]={{"x",0x662e},{"y",0x6630},{"gx",0x83f6},{"gy",0x83f8},
        {"phase",0x1c1},{"sprite",0x1c3},{"facing",0x9e82},{"previous_x",0x9790},{"previous_y",0x97a8},
        {"timer",0xf2e},{"up",0x190},{"down",0x192},{"left",0x194},{"right",0x196},
        {"speaker_index",0xf2c},{"sound_mode",0xf24},{"recap_pending",0x32b},
        {"door_state",0x18a},{"door_x",0x99b0},{"door_y",0x9af2},{"map_height",0x9792}};
    std::fprintf(file,",\"movement\":{");
    for (unsigned i=0;i<sizeof(fields)/sizeof(fields[0]);++i)
        std::fprintf(file,"%s\"%s\":%d",i ? ",":"",fields[i].name,word(base,fields[i].offset));
    std::fprintf(file,",\"support\":%d,\"idle_ticks\":%d,\"right_index\":%d,\"left_index\":%d,\"speaker_offset\":%u,\"speaker_segment\":%u,\"data_segment\":%u}",
        word(SegPhys(ss),(Bit16u)(reg_bp-6)),word(SegPhys(ss),(Bit16u)(reg_bp-8)),
        word(SegPhys(ss),(Bit16u)(reg_bp-10)),word(SegPhys(ss),(Bit16u)(reg_bp-12)),
        (unsigned)mem_readw(base+0xc40b),(unsigned)mem_readw(base+0xc40d),base>>4);
    if (include_map) {
        unsigned width=mem_readw(base+0x9778),height=mem_readw(base+0x9792);
        std::fprintf(file,",\"movement_attributes\":[");
        for (unsigned x=0;x<width;++x) {
            unsigned pointer=mem_readd(base+0x9afa+4*x),column=((pointer>>16)<<4)+(pointer&65535);
            std::fprintf(file,"%s[",x ? ",":"");
            for (unsigned y=0;y<height;++y) std::fprintf(file,"%s%u",y ? ",":"",(unsigned)mem_readb(column+y));
            std::fprintf(file,"]");
        }
        std::fprintf(file,"]");
    }
}
static void music_state(FILE* file) {
    unsigned vector = mem_readd(0x63*4), base = (vector>>16)<<4;
    // This layout is specific to WR1's embedded driver, whose live tick entry
    // was recovered from the dispatch table rather than assumed from file data.
    if (mem_readw(base+0x4a80)!=0x60da) return;
    unsigned segment=mem_readw(base+0x85c), offset=mem_readw(base+0x85e);
    std::fprintf(file,",\"music_driver\":{\"dispatcher_use_dx\":%u,\"external_timer\":%u,\"counter\":%u,\"beats\":%u,\"division\":%u,\"format\":%u,\"repeat\":%u,\"playing\":%u,\"data_segment\":%u,\"data_offset\":%u,\"prefix\":[",
        (unsigned)mem_readb(base+4),(unsigned)mem_readw(base+0x11),
        (unsigned)mem_readw(base+0x853),(unsigned)mem_readw(base+0x855),(unsigned)mem_readw(base+0x859),
        (unsigned)mem_readb(base+0x85b),(unsigned)mem_readb(base+0x860),(unsigned)mem_readb(base+0x961),segment,offset);
    for (int i=0;i<16;++i) std::fprintf(file,"%s%u",i ? "," : "",(unsigned)mem_readb((segment<<4)+((offset+i)&0xffff)));
    std::fprintf(file,"],\"tracks\":[");
    unsigned count=mem_readw(base+0x857);
    for (unsigned i=0;i<count && i<32;++i) std::fprintf(file,"%s{\"active\":%u,\"delay\":%u,\"cursor\":%u,\"status\":%u}",
        i ? "," : "",(unsigned)mem_readw(base+0x861+2*i),(unsigned)mem_readd(base+0x8a1+4*i),
        (unsigned)mem_readw(base+0x921+2*i),(unsigned)mem_readb(base+0x962+i));
    std::fprintf(file,"],\"opl_state\":{\"mode\":%u,\"rhythm\":%u,\"percussion\":%u,\"transpose\":%u",
        (unsigned)mem_readb(base+0x994),(unsigned)mem_readb(base+0x9a1),
        (unsigned)mem_readb(base+0x749),(unsigned)mem_readb(base+0x982));
    struct Array { const char* name; unsigned offset, count, width; };
    static const Array arrays[] = {{"voices",0x791,9,2},{"programs",0x7a3,16,1},
        {"volumes",0x7b3,16,1},{"notes",0x7c3,9,1},{"levels",0x7cc,9,1},{"bends",0x781,16,1}};
    for (const Array& array : arrays) {
        std::fprintf(file,",\"%s\":[",array.name);
        for (unsigned i=0;i<array.count;++i) std::fprintf(file,"%s%u",i ? "," : "",
            array.width==2 ? (unsigned)mem_readw(base+array.offset+2*i) : (unsigned)mem_readb(base+array.offset+i));
        std::fprintf(file,"]");
    }
    std::fprintf(file,"}}");
}
static void state(FILE* file, unsigned base) {
    struct Field { const char* name; unsigned offset; };
    static const Field fields[] = {
        {"x",0x662e},{"y",0x6630},{"gx",0x83f6},{"gy",0x83f8},
        {"camera_x",0x8480},{"camera_y",0x8482},{"phase",0x1c1},
        {"sprite",0x1c3},{"facing",0x9e82},{"background_frame",0x41be},
        {"render_page",0x807c},{"display_page",0x4879},{"timer",0xf2e},
        {"entity_timer",0xf54},{"threshold",0x8e8f},{"up",0x190},
        {"down",0x192},{"left",0x194},{"right",0x196},
        {"books_collected",0x15c},{"book_count",0x180},{"mistakes",0x334},
        {"source_x",0x26f},{"source_y",0x271},{"word_offset",0xa984},
        {"picture_offset",0x6634},{"gruzzle_count",0x237},
        {"gruzzle_difficulty",0x982a},{"gruzzle_cadence",0x21b},
        {"slime_request",0x19e},{"action_busy",0x17a},{"death",0x26b},
        {"slime_used",0x26d},{"slime_reward",0x154},
        {"miss_timer",0x239},{"miss_x",0xab06},{"miss_y",0xab08},
        {"mystery_index",0x847e},{"mystery_prefix",0x9491},
        {"reward_timer",0x150},{"reward_x",0x14c},{"reward_y",0x14e},{"reward_bonus",0x160},
        {"recap_pending",0x32b},{"door_state",0x18a},{"level_index",0x20b},
        {"slime_ever_used",0x15e},{"door_x",0x99b0},{"door_y",0x9af2},
        {"entrance_timer",0xc3dd},
        {"difficulty",0x17e},{"character",0x18e},
        {"music_enabled",0xf2a},{"sound_mode",0xf24},{"cached_level",0xfc8},{"map_width",0x9778},{"map_height",0x9792},
        {"level_key_z",0x1a4},{"level_key_l",0x1a6},{"keyboard_any",0xc48b}
    };
    for (const Field& f : fields) std::fprintf(file, ",\"%s\":%d", f.name, word(base, f.offset));
    std::fprintf(file, ",\"score\":%u,\"rng\":%u,\"active_word\":%u,\"active_index\":%u,\"matched_count\":%u",
        (unsigned)mem_readd(base+0x186), (unsigned)mem_readd(base+0x6378),
        (unsigned)mem_readb(base+0x32d), (unsigned)mem_readb(base+0x32e), (unsigned)mem_readb(base+0x32f));
    std::fprintf(file, ",\"world_x\":%d,\"world_y\":%d",
        word(base,0x662e)+8*word(base,0x8480), word(base,0x6630)+8*word(base,0x8482));
    std::fprintf(file,",\"gruzzle_move_timers\":[");
    for (int i=0; i<10; ++i) std::fprintf(file,"%s%d",i ? "," : "",word(base,0xf40+2*i));
    std::fprintf(file,"],\"gruzzles\":[");
    int count = word(base,0x237);
    for (int i=0; i<count && i<10; ++i) {
        std::fprintf(file, "%s{\"gx\":%d,\"gy\":%d,\"type\":%d,\"state\":%d,\"animation_index\":%d,\"jump_phase\":%d,\"move_timer\":%d}",
            i ? "," : "", word(base,0x977a+2*i), word(base,0x9794+2*i), word(base,0x6636+2*i),
            word(base,0xc3c9+2*i),word(base,0x982c+2*i),word(base,0xab0a+2*i),word(base,0xf40+2*i));
    }
    std::fprintf(file, "],\"slime_pickups\":[");
    count = word(base,0x182);
    for (int i=0; i<count && i<20; ++i) {
        int x=word(base,0xb8b9+2*i), y=word(base,0xb8db+2*i);
        unsigned column=mem_readd(base+0x9afa+8*x);
        unsigned address=((column>>16)<<4)+(column&0xffff)+2*y;
        std::fprintf(file,"%s{\"tile_x\":%d,\"tile_y\":%d,\"attribute\":%u}",
            i ? "," : "",x,y,(unsigned)mem_readb(address));
    }
    std::fprintf(file,"],\"mystery_pickups\":[");
    for (int i=0; i<7; ++i) {
        int x=word(base,0xb8ef+2*i), y=word(base,0xb97d+2*i);
        unsigned column=mem_readd(base+0x9afa+8*x);
        unsigned address=((column>>16)<<4)+(column&0xffff)+2*y;
        std::fprintf(file,"%s{\"tile_x\":%d,\"tile_y\":%d,\"attribute\":%u}",
            i ? "," : "",x,y,(unsigned)mem_readb(address));
    }
    std::fprintf(file,"],\"picture_timers\":[");
    for (int i=0; i<7; ++i) std::fprintf(file,"%s%d",i ? "," : "",word(base,0x41a2+2*i));
    std::fprintf(file,"],\"picture_frames\":[");
    for (int i=0; i<7; ++i) std::fprintf(file,"%s%d",i ? "," : "",word(base,0x41b0+2*i));
    std::fprintf(file,"],\"picture_animation_enabled\":%d",word(base,0x1bf));
    std::fprintf(file,",\"drips\":[");
    count = word(base,0x184);
    for (int i=0;i<count && i<10;++i) {
        std::fprintf(file,"%s{\"x\":%d,\"y\":%d,\"origin_y\":%d,\"max_y\":%d,\"frame\":%d}",
            i ? "," : "",word(base,0x65f2+2*i),word(base,0x9ade + 2*i),
            word(base,0x6606+2*i),word(base,0x661a+2*i),word(base,0xa914+2*i));
    }
    std::fprintf(file,"]");
    std::fprintf(file,",\"word_cursor\":%u,\"words\":[",(unsigned)mem_readd(base+0x330));
    for (int i=0;i<7;++i) {
        std::fprintf(file,"%s\"",i ? "," : "");
        for (int j=0;j<8;++j) {
            unsigned ch=mem_readb(base+0x9970+8*i+j);
            if (!ch) break;
            std::fprintf(file,"\\u%04x",ch);
        }
        std::fprintf(file,"\"");
    }
    std::fprintf(file,"]");
}

static void keyboard_game(FILE* file,unsigned base) {
    std::fprintf(file,",\"keyboard_game\":{\"pressed\":%u,\"scan\":%u,\"activity\":%u,\"custom\":%u,\"bindings\":[",
        (unsigned)mem_readw(base+0xc488),(unsigned)mem_readb(base+0xc48a),
        (unsigned)mem_readw(base+0xc48b),(unsigned)mem_readw(base+0x1b9));
    for (unsigned i=0;i<5;++i) std::fprintf(file,"%s%u",i ? "," : "",(unsigned)mem_readb(base+0x1b4+i));
    std::fprintf(file,"],\"flags\":{");
    const unsigned flags[]={0x190,0x192,0x194,0x196,0x19e,0x1a8,0x1a4,0x1a2,0x1b2,0x1b0,0x1a0,0x1ae,0x18c,0x1a6,0x19a,0x198,0x19c};
    for (unsigned i=0;i<sizeof(flags)/sizeof(flags[0]);++i)
        std::fprintf(file,"%s\"%04x\":%u",i ? "," : "",flags[i],(unsigned)mem_readw(base+flags[i]));
    std::fprintf(file,"}}");
}

static void renderer_prefix_state(FILE* file,unsigned base) {
    struct Field { const char* name; unsigned offset; };
    const Field fields[]={{"animation_enabled",0x1bf},{"player_x",0x662e},{"player_y",0x6630},
        {"camera_x",0x8480},{"camera_y",0x8482},{"attr_width",0x9778},{"attr_height",0x9792},{"render_page",0x807c}};
    std::fprintf(file,",\"renderer_prefix\":{");
    for (unsigned i=0;i<sizeof(fields)/sizeof(fields[0]);++i)
        std::fprintf(file,"%s\"%s\":%d",i ? ",":"",fields[i].name,word(base,fields[i].offset));
    const Field arrays[]={{"counters",0x41a2},{"phases",0x41b0},{"word_slots",0xb8cd}};
    for (const Field& field:arrays) {
        std::fprintf(file,",\"%s\":[",field.name);
        for (unsigned i=0;i<7;++i) std::fprintf(file,"%s%d",i ? ",":"",word(base,field.offset+2*i));
        std::fprintf(file,"]");
    }
    std::fprintf(file,",\"source_rects\":[");
    for (unsigned phase=0;phase<2;++phase) {
        std::fprintf(file,"%s[",phase ? ",":"");
        for (unsigned i=0;i<7;++i) {
            unsigned offset=phase*14+i*2;
            std::fprintf(file,"%s[%d,%d,%d,%d]",i ? ",":"",word(base,0x2ab+offset),word(base,0x2e3+offset),word(base,0x2c7+offset),word(base,0x2ff+offset));
        }
        std::fprintf(file,"]");
    }
    std::fprintf(file,"]}");
}

static void renderer_background_state(FILE* file,unsigned base) {
    unsigned width=mem_readw(base+0x9778)/2,height=mem_readw(base+0x9792)/2;
    std::fprintf(file,",\"renderer_background\":{\"full_redraw\":%d,\"color\":%d,\"source_columns\":[",word(base,0xaf8a),word(base,0x9af8));
    if (width>112 || height>128) { std::fprintf(file,"]}"); return; }
    for (unsigned x=0;x<width;++x) {
        unsigned px=mem_readd(base+0x8b13+4*x),py=mem_readd(base+0x8ccf+4*x);
        unsigned ax=((px>>16)<<4)+(px&65535),ay=((py>>16)<<4)+(py&65535);
        std::fprintf(file,"%s[",x ? ",":"");
        for (unsigned y=0;y<height;++y) std::fprintf(file,"%s[%d,%d]",y ? ",":"",word(ax,2*y),word(ay,2*y));
        std::fprintf(file,"]");
    }
    std::fprintf(file,"]}");
}

static void renderer_tiles_state(FILE* file,unsigned base) {
    unsigned count=mem_readw(base+0x9e72);
    std::fprintf(file,",\"renderer_tiles\":{\"phase\":%d,\"animated_count\":%u,\"pickups\":[",word(base,0x41be),count);
    for (unsigned i=0;i<7;++i) std::fprintf(file,"%s[%d,%d]",i ? ",":"",word(base,0xb8ef+2*i),word(base,0xb97d+2*i));
    std::fprintf(file,"],\"animated\":[");
    if (count<=112) for (unsigned i=0;i<count;++i) std::fprintf(file,"%s[%d,%d]",i ? ",":"",word(base,0xc18b+2*i),word(base,0xc26b+2*i));
    std::fprintf(file,"]}");
}

static void renderer_doors_state(FILE* file,unsigned base) {
    std::fprintf(file,",\"renderer_doors\":{\"theme\":%d,\"exit_x\":%d,\"exit_y\":%d,\"entrance_x\":%d,\"entrance_y\":%d,\"entrance_timer\":%d}",
        word(base,0x18e),word(base,0x99b0),word(base,0x9af2),word(base,0xaebe),word(base,0xb88c),word(base,0xc3dd));
}

static void renderer_matching_state(FILE* file,unsigned base) {
    std::fprintf(file,",\"renderer_matching\":{\"active\":%u,\"active_index\":%u,\"source_x\":%d,\"source_y\":%d,\"last_x\":%d,\"last_y\":%d,\"picture_offset\":%d,\"locations\":[",
        (unsigned)mem_readb(base+0x32d),(unsigned)mem_readb(base+0x32e),word(base,0x26f),word(base,0x271),word(base,0x83fa),word(base,0x83fc),word(base,0x6634));
    for (unsigned i=0;i<7;++i) {
        int x=word(base,0x9e74+2*i),y=word(base,0xa906+2*i);
        unsigned pointer=mem_readd(base+0x9afa+4*(x/8));
        unsigned address=((pointer>>16)<<4)+(Bit16u)((pointer&65535)+(y/8));
        std::fprintf(file,"%s[%d,%d,%u]",i ? ",":"",x,y,(unsigned)mem_readb(address));
    }
    std::fprintf(file,"],\"word_rects\":[");
    for (unsigned i=0;i<7;++i) std::fprintf(file,"%s[%d,%d,%d,%d]",i ? ",":"",word(base,0x273+2*i),word(base,0x29d+2*i),word(base,0x281+2*i),word(base,0x28f+2*i));
    std::fprintf(file,"]}");
}

static void renderer_player_state(FILE* file,unsigned base) {
    unsigned frame=mem_readw(base+0x1c3);
    std::fprintf(file,",\"renderer_player\":{\"visible\":%d,\"frame\":%u,\"images\":[",word(base,0x1bd),frame);
    for (unsigned i=0;i<2;++i) {
        unsigned offset=(Bit16u)((i ? 0x734a:0x664a)+128*frame);
        std::fprintf(file,"%s{\"pointer\":%u,\"header\":[",i ? ",":"",((base>>4)<<16)|offset);
        for (unsigned j=0;j<52;++j) std::fprintf(file,"%s%u",j ? ",":"",(unsigned)mem_readb(base+offset+j));
        std::fprintf(file,"]}");
    }
    std::fprintf(file,"]}");
}

static void renderer_actors_state(FILE* file,unsigned base,bool images) {
    unsigned enemies=mem_readw(base+0x237),drips=mem_readw(base+0x184);
    std::set<unsigned> offsets;
    std::fprintf(file,",\"renderer_actors\":{\"data_segment\":%u,\"enemy_count\":%u,\"drip_count\":%u,\"animation_frames\":[",base>>4,enemies,drips);
    for (unsigned i=0;i<12;++i) std::fprintf(file,"%s%d",i ? ",":"",word(base,0x21d+2*i));
    std::fprintf(file,"],\"enemies\":[");
    if (enemies<=10) for (unsigned i=0;i<enemies;++i) {
        unsigned type=mem_readw(base+0x6636+2*i);
        std::fprintf(file,"%s{\"x\":%d,\"y\":%d,\"type\":%u,\"state\":%d,\"animation_index\":%d}",i ? ",":"",
            word(base,0x977a+2*i),word(base,0x9794+2*i),type,word(base,0xc3c9+2*i),word(base,0x982c+2*i));
        for (unsigned j=0;j<12;++j) {
            unsigned frame=mem_readw(base+0x21d+2*j);
            offsets.insert((Bit16u)(0xb98b+512*type+128*frame));
            offsets.insert((Bit16u)(0xaf8c+512*type+128*frame));
        }
    }
    std::fprintf(file,"],\"drips\":[");
    if (drips<=10) for (unsigned i=0;i<drips;++i)
        std::fprintf(file,"%s{\"x\":%d,\"y\":%d,\"frame\":%d}",i ? ",":"",word(base,0x65f2+2*i),word(base,0x9ade + 2*i),word(base,0xa914+2*i));
    std::fprintf(file,"]}");
    if (!images) return;
    if (drips) for (unsigned frame=0;frame<12;++frame) {
        offsets.insert((Bit16u)(0xa986+128*frame));
        offsets.insert((Bit16u)(0x8513+128*frame));
    }
    for (unsigned frame=0;frame<24;++frame) {
        offsets.insert((Bit16u)(0x9e86+128*frame));
        offsets.insert((Bit16u)(0x8693+128*frame));
    }
    offsets.insert(0xa206); offsets.insert(0x8a13);
    offsets.insert(0xa286); offsets.insert(0x8a93);
    std::fprintf(file,",\"actor_images\":{");
    bool first=true;
    for (unsigned offset:offsets) {
        std::fprintf(file,"%s\"%u\":[",first ? "":",",offset); first=false;
        for (unsigned j=0;j<52;++j) std::fprintf(file,"%s%u",j ? ",":"",(unsigned)mem_readb(base+offset+j));
        std::fprintf(file,"]");
    }
    std::fprintf(file,"}");
}

static void renderer_tail_state(FILE* file,unsigned base) {
    struct Field { const char* name; unsigned offset; };
    const Field fields[]={{"action_busy",0x17a},{"death",0x26b},{"slime_reward",0x154},
        {"miss_timer",0x239},{"miss_x",0xab06},{"miss_y",0xab08},{"reward_timer",0x150},
        {"reward_x",0x14c},{"reward_y",0x14e},{"reward_bonus",0x160}};
    std::fprintf(file,",\"renderer_tail\":{\"score\":%u",(unsigned)mem_readd(base+0x186));
    for (const Field& field:fields) std::fprintf(file,",\"%s\":%d",field.name,word(base,field.offset));
    unsigned count=mem_readw(base+0xa928);
    std::fprintf(file,",\"foreground_count\":%u,\"foreground\":[",count);
    if (count<=165) for (unsigned i=0;i<count;++i) std::fprintf(file,"%s[%d,%d]",i ? ",":"",word(base,0xad76+2*i),word(base,0xaec0+2*i));
    std::fprintf(file,"],\"rescue_frames\":[");
    for (unsigned i=0;i<24;++i) std::fprintf(file,"%s%d",i ? ",":"",word(base,0x23b+2*i));
    std::fprintf(file,"]");
    const unsigned pointers[]={mem_readd(base+0x8486),((base>>4)<<16)|0x41c0,((base>>4)<<16)|0x41c9};
    const char* labels[]={"reward_text","perfect_text","bonus_text"};
    for (unsigned t=0;t<3;++t) {
        unsigned pointer=pointers[t],address=((pointer>>16)<<4)+(pointer&65535);
        std::fprintf(file,",\"%s\":{\"pointer\":%u,\"bytes\":[",labels[t],pointer);
        if (pointer) for (unsigned i=0;i<128;++i) { unsigned ch=mem_readb(address+i); std::fprintf(file,"%s%u",i ? ",":"",ch); if (!ch) break; }
        std::fprintf(file,"]}");
    }
    std::fprintf(file,"}");
}

static void clock_state(FILE* file,unsigned base) {
    std::fprintf(file,",\"clock_state\":{\"timer\":%d,\"threshold\":%u,\"speaker_index\":%d,\"speaker_elapsed\":%u,\"bios_countdown\":%u,\"bios_reload\":%u,\"bios_ticks\":%u,\"control_flags\":{",
        word(base,0xf2e),(unsigned)mem_readw(base+0x8e8f),word(base,0xf2c),(unsigned)mem_readd(base+0xf30),
        (unsigned)mem_readd(base+0xc41a),(unsigned)mem_readd(base+0xc41f),(unsigned)mem_readd(0x46c));
    const unsigned flags[]={0x178,0x146,0x19a,0x1a0,0x1b2,0x1b0,0x18c,0x198,0x1ae,0x1a4,0x1a6,0x1ac};
    for (unsigned i=0;i<sizeof(flags)/sizeof(flags[0]);++i)
        std::fprintf(file,"%s\"%04x\":%d",i ? "," : "",flags[i],word(base,flags[i]));
    unsigned sound=mem_readd(base+0xc40b);
    std::fprintf(file,"},\"speaker_sequence\":[");
    if (word(base,0xf2c)>=0) for (int i=0;i<256;++i) {
        unsigned address=((sound>>16)<<4)+(Bit16u)((sound&0xffff)+4*i);
        int duration=word(address,2);
        std::fprintf(file,"%s[%u,%d]",i ? "," : "",(unsigned)mem_readw(address),duration);
        if (!duration) break;
    }
    unsigned bios=mem_readd(base+0xf38),user=mem_readd(0x1c*4);
    std::fprintf(file,"],\"bios_handler\":%u,\"int1c_handler\":%u,\"bios_code\":[",bios,user);
    for (int i=0;i<19;++i) std::fprintf(file,"%s%u",i ? "," : "",(unsigned)mem_readb(((bios>>16)<<4)+(bios&0xffff)+i));
    std::fprintf(file,"],\"int1c_code\":[");
    for (int i=0;i<5;++i) std::fprintf(file,"%s%u",i ? "," : "",(unsigned)mem_readb(((user>>16)<<4)+(user&0xffff)+i));
    std::fprintf(file,"]}");
}

static void contact_state(FILE* file,unsigned base) {
    std::fprintf(file,",\"contact\":{\"data_segment\":%u",base>>4);
    state(file,base);
    std::fprintf(file,",\"last_x\":%d,\"last_y\":%d,\"speaker_index\":%d,\"speaker_offset\":%u,\"speaker_segment\":%u}",
        word(base,0x83fa),word(base,0x83fc),word(base,0xf2c),(unsigned)mem_readw(base+0xc40b),(unsigned)mem_readw(base+0xc40d));
    std::fprintf(file,",\"contact_attributes\":[");
    unsigned width=mem_readw(base+0x9778),height=mem_readw(base+0x9792);
    for (unsigned x=0;x<width;++x) {
        unsigned pointer=mem_readd(base+0x9afa+4*x),column=((pointer>>16)<<4)+(pointer&65535);
        std::fprintf(file,"%s[",x ? ",":"");
        for (unsigned y=0;y<height;++y) std::fprintf(file,"%s%u",y ? ",":"",(unsigned)mem_readb(column+y));
        std::fprintf(file,"]");
    }
    std::fprintf(file,"]");
}

// Called only at selected instruction offsets by the normal/dynamic decoders.
static void observe(unsigned ip, unsigned pending_cycles) {
    FILE* file = trace_file();
    if (!file || cpu.pmode) return;
    if (observed_ds && update_active) {
        unsigned load_base=observed_ds-0x22550;
        unsigned segment=(SegPhys(cs)-load_base)>>4;
        const char* kind=NULL;
        unsigned entry=0,leave=0,count=0;
        if (segment==0x812) { kind="renderer"; entry=5; leave=0x1689; }
        if (segment==0x10ed) { kind="copy_rect"; entry=8; leave=0x21a; count=8; }
        if (segment==0x13ae) { kind="masked_sprite"; entry=2; leave=0x118; count=6; }
        if (segment==0x10ed && (ip==0x3be || ip==0x4a9 || ip==0x626 || ip==0x86d || ip==0x903 || ip==0xa63)) leave=ip;
        if (segment==0x13ae && (ip==0x313 || ip==0x4b5 || ip==0x543 || ip==0x6df || ip==0x820)) leave=ip;
        if (segment==0xc9d) { kind="draw_page"; entry=0x25; leave=0x83; count=1; }
        if (segment==0xc9d && (ip==0x138 || ip==0x187)) { kind="fill_style"; entry=0x138; leave=0x187; count=3; }
        if (segment==0xc6e) { kind="fill_rect"; entry=0x94; leave=0x2ee; count=5; }
        if (segment==0xa43) { kind="fill_raw"; entry=0x8; leave=0x570; count=4; }
        if (segment==0xa43 && ip==0xfb) leave=ip;
        if (segment==0x14c0) { kind="display_page"; entry=6; leave=0x95; count=1; }
        if (segment==0x97a) { kind="contact"; entry=0xa; leave=0x558; }
        if (segment==0xc9d && (ip==0x2f8 || ip==0x31f)) { kind="text_color"; entry=0x2f8; leave=0x31f; count=1; }
        if (segment==0xc9d && (ip==0x345 || ip==0x36c)) { kind="text_background"; entry=0x345; leave=0x36c; count=1; }
        if (segment==0xb18) { kind="text_cursor"; entry=6; leave=0x4f; count=2; }
        if (segment==0xd86) { kind="text_string"; entry=0x173; leave=0x327; count=2; }
        if (segment==0xd86 && (ip==0x36 || ip==0xde)) { kind="text_font"; entry=0x36; leave=0xde; count=2; }
        if (segment==0x1fa6) { kind="string_length"; entry=0; leave=0x1a; count=2; }
        bool prefix_end=segment==0x812 && (ip==0x1a5 || ip==0x671 || ip==0x848 || ip==0xad6 || ip==0xecc || ip==0xf18 || ip==0x113e);
        if (kind && (ip==entry || ip==leave || prefix_end)) {
            std::lock_guard<std::mutex> lock(trace_mutex);
            unsigned graphics_return_sp=prefix_end ? (Bit16u)(reg_bp+2) : reg_sp;
            std::fprintf(file,"{\"event\":\"%s\",\"kind\":\"%s\",\"entry\":%s,\"ip\":%u,\"cs\":%u,\"pic_ms\":%.9f,\"launch_call\":%u,\"cycles_remaining\":%d,\"pending_cycles\":%u,\"ax\":%u,\"return_ip\":%u,\"return_cs\":%u,\"args\":[",
                prefix_end ? "graphics_stage":"graphics",kind,ip==entry ? "true":"false",ip,(unsigned)SegValue(cs),PIC_FullIndex()+(double)pending_cycles/CPU_CycleMax,
                emulation_launch_call.load(),(int)CPU_Cycles,pending_cycles,(unsigned)reg_ax,
                (unsigned)mem_readw(SegPhys(ss)+graphics_return_sp),(unsigned)mem_readw(SegPhys(ss)+(Bit16u)(graphics_return_sp+2)));
            for (unsigned i=0;i<count;++i) std::fprintf(file,"%s%d",i ? ",":"",word(SegPhys(ss),(Bit16u)(reg_sp+4+2*i)));
            std::fprintf(file,"],\"graphics_state\":[");
            for (unsigned i=0;i<88;++i) std::fprintf(file,"%s%u",i ? ",":"",(unsigned)mem_readb(observed_ds+0x447b+i));
            std::fprintf(file,"]");
            if (segment==0x97a) contact_state(file,observed_ds);
            if (segment==0x97a || segment==0xd86 || segment==0x812) {
                std::fprintf(file,",\"text_state\":{\"ready\":%u,\"font_id\":%u,\"height\":%u,\"font_pointer\":%u}",
                    (unsigned)mem_readb(observed_ds+0x44d5),(unsigned)mem_readw(observed_ds+0x43ac),
                    (unsigned)mem_readw(observed_ds+0x43ae),(unsigned)mem_readd(observed_ds+0x43b0));
            }
            if ((segment==0xd86 && entry==0x173) || segment==0x1fa6) {
                unsigned pointer=mem_readd(SegPhys(ss)+(Bit16u)(reg_sp+4)),address=((pointer>>16)<<4)+(pointer&65535);
                std::fprintf(file,",\"text_bytes\":[");
                for (unsigned i=0;i<128;++i) { unsigned ch=mem_readb(address+i); std::fprintf(file,"%s%u",i ? ",":"",ch); if (!ch) break; }
                std::fprintf(file,"]");
            }
            if (segment==0x812) {
                renderer_prefix_state(file,observed_ds);
                renderer_tiles_state(file,observed_ds);
                renderer_doors_state(file,observed_ds);
                renderer_matching_state(file,observed_ds);
                renderer_player_state(file,observed_ds);
                renderer_actors_state(file,observed_ds,ip==entry);
                renderer_tail_state(file,observed_ds);
                if (ip==entry || ip==leave) {
                    std::fprintf(file,",\"renderer_post\":{\"door_state\":%u,\"iteration\":%u,\"cpu_flags\":%u}",
                        (unsigned)mem_readw(observed_ds+0x18a),(unsigned)mem_readw(SegPhys(ss)+(Bit16u)(reg_bp-2)),(unsigned)reg_flags);
                }
                if (ip==entry || ip==0x1a5) renderer_background_state(file,observed_ds);
            }
            if (segment==0xa43 || segment==0xc6e || segment==0x812 || segment==0x97a || segment==0xd86 || (segment==0xc9d && entry==0x138)) {
                unsigned mode=mem_readw(observed_ds+0x4875),table=0x453a;
                if (mem_readw(observed_ds+0x447b)==1) { mode=mem_readw(observed_ds+0x447d); table=0x464a; }
                std::fprintf(file,",\"fill_state\":{\"ready\":%u,\"mode\":%u,\"record\":[",(unsigned)mem_readb(observed_ds+0x44d6),mode);
                for (unsigned i=0;i<16;++i) std::fprintf(file,"%s%u",i ? ",":"",(unsigned)mem_readb(observed_ds+table+16*mode+i));
                std::fprintf(file,"]}");
            }
            unsigned video_vector=mem_readd(0x10*4),video_base=((video_vector>>16)<<4)+(video_vector&65535);
            std::fprintf(file,",\"graphics_flags\":{\"check_mode\":%u,\"copy_ready\":%u,\"sprite_ready\":%u,\"display_type\":%u,\"video_mode\":%u,\"video_handler\":%u,\"video_code\":[",
                (unsigned)mem_readw(observed_ds+0x5993),(unsigned)mem_readb(observed_ds+0x5ab4),
                (unsigned)mem_readb(observed_ds+0x5aaf),(unsigned)mem_readw(observed_ds+0x487b),(unsigned)mem_readb(0x449),video_vector);
            for (unsigned i=0;i<5;++i) std::fprintf(file,"%s%u",i ? ",":"",(unsigned)mem_readb(video_base+i));
            std::fprintf(file,"]}");
            if (segment==0x14c0 || segment==0x812) {
                std::fprintf(file,",\"display_state\":{\"game_page\":%u,\"bios_page\":%u,\"bios_start\":%u,\"page_size\":%u,\"columns\":%u,\"crtc_port\":%u,\"cursors\":[",
                    (unsigned)mem_readw(observed_ds+0x4879),(unsigned)mem_readb(0x462),(unsigned)mem_readw(0x44e),
                    (unsigned)mem_readw(0x44c),(unsigned)mem_readw(0x44a),(unsigned)mem_readw(0x463));
                for (unsigned i=0;i<16;++i) std::fprintf(file,"%s%u",i ? ",":"",(unsigned)mem_readb(0x450+i));
                std::fprintf(file,"]}");
            }
            if (segment==0x10ed || segment==0x13ae || segment==0xa43 || segment==0xc6e || segment==0x812 || segment==0x97a || segment==0xd86) {
                clock_state(file,observed_ds); music_state(file); keyboard_game(file,observed_ds); DBP_WR1_KeyboardState(file);
            }
            if (segment==0x13ae) {
                unsigned pointer=mem_readd(SegPhys(ss)+(Bit16u)(reg_sp+12));
                unsigned header=((pointer>>16)<<4)+(pointer&65535);
                std::fprintf(file,",\"image_header\":[");
                for (unsigned i=0;i<52;++i) std::fprintf(file,"%s%u",i ? ",":"",(unsigned)mem_readb(header+i));
                std::fprintf(file,"]");
            }
            unsigned handle=mem_readw(observed_ds+0x4873);
            for (unsigned slot=0;slot<44;++slot) {
                unsigned record=observed_ds+0x5e4c+6*slot;
                if (mem_readb(record)!=(handle&255)) continue;
                unsigned descriptor=observed_ds+0x5ab6+0x36*mem_readb(record+3);
                std::fprintf(file,",\"device_handle\":%u,\"device_slot\":%u,\"device_record\":[",handle,slot);
                for (unsigned i=0;i<6;++i) std::fprintf(file,"%s%u",i ? ",":"",(unsigned)mem_readb(record+i));
                std::fprintf(file,"],\"device_descriptor\":[");
                for (unsigned i=0;i<54;++i) std::fprintf(file,"%s%u",i ? ",":"",(unsigned)mem_readb(descriptor+i));
                std::fprintf(file,"]");
                break;
            }
            DBP_WR1_PitState(file); DBP_WR1_PicState(file); DBP_WR1_VgaState(file);
            std::fprintf(file,"}\n"); std::fflush(file);
            return;
        }
    }
    unsigned keyboard_vector=mem_readd(9*4),keyboard_base=(keyboard_vector>>16)<<4;
    if (observed_ds && (keyboard_vector&65535)==4 && SegPhys(cs)==keyboard_base &&
        SegPhys(cs)+0x18840==observed_ds && mem_readw(keyboard_base+0x12)==0x60e4 &&
        (ip==0x12 || ip==0x24f)) {
        std::lock_guard<std::mutex> lock(trace_mutex);
        unsigned return_sp=(Bit16u)(reg_sp+(ip==0x24f ? 0 : 18));
        std::fprintf(file,"{\"event\":\"keyboard_irq\",\"ip\":%u,\"cs\":%u,\"pic_ms\":%.9f,\"launch_call\":%u,\"cycles_remaining\":%d,\"pending_cycles\":%u,\"return_ip\":%u,\"return_cs\":%u,\"return_flags\":%u",
            ip,(unsigned)SegValue(cs),PIC_FullIndex()+(double)pending_cycles/CPU_CycleMax,emulation_launch_call.load(),(int)CPU_Cycles,pending_cycles,
            (unsigned)mem_readw(SegPhys(ss)+return_sp),(unsigned)mem_readw(SegPhys(ss)+(Bit16u)(return_sp+2)),(unsigned)mem_readw(SegPhys(ss)+(Bit16u)(return_sp+4)));
        keyboard_game(file,observed_ds); DBP_WR1_KeyboardState(file);
        DBP_WR1_PitState(file); DBP_WR1_PicState(file); DBP_WR1_VgaState(file);
        std::fprintf(file,"}\n"); std::fflush(file);
        return;
    }
    // Driver DS is its own CS, not WR1's data segment. Keep the previously
    // fingerprinted game DS intact while observing nested driver operations.
    unsigned driver_base = (mem_readd(0x63*4)>>16)<<4;
    bool work_probe = ip==0x5c92 || ip==0x5c94 || ip==0x5ca0 || ip==0x5ca2 ||
        ip==0x5caa || ip==0x5cac || ip==0x5cb5 || ip==0x5cb7 || ip==0x602a ||
        ip==0x602c || ip==0x6088 || ip==0x608a || ip==0x6310;
    if (observed_ds && SegPhys(cs)==driver_base && mem_readw(driver_base+0x4a80)==0x60da &&
        (ip==0x58f1 || ip==0x599f || ip==0x579e || ip==0x57c3 || work_probe)) {
        if (ip==0x579e) opl_active = true;
        if (ip==0x57c3) opl_active = false;
        std::lock_guard<std::mutex> lock(trace_mutex);
        std::fprintf(file,"{\"event\":\"%s\",\"ip\":%u,\"cs\":%u,\"ax\":%u,\"bx\":%u,\"cx\":%u,\"dx\":%u,\"si\":%u,\"di\":%u,\"pic_ms\":%.9f,\"launch_call\":%u,\"cycles_remaining\":%d,\"pending_cycles\":%u",
            work_probe ? "driver_work" : ((ip==0x579e || ip==0x57c3) ? "opl" : "driver_event"),ip,(unsigned)SegValue(cs),
            (unsigned)reg_ax,(unsigned)reg_bx,(unsigned)reg_cx,(unsigned)reg_dx,(unsigned)reg_si,(unsigned)reg_di,
            PIC_FullIndex()+(double)pending_cycles/CPU_CycleMax,emulation_launch_call.load(),(int)CPU_Cycles,pending_cycles);
        DBP_WR1_PitState(file); DBP_WR1_PicState(file); DBP_WR1_VgaState(file);
        std::fprintf(file,"}\n");
        std::fflush(file);
        return;
    }
    unsigned base = SegPhys(ds);
    // At IRET, DS has already been restored to the interrupted context.
    if (ip==0x313 && observed_ds && SegPhys(cs)+0x20e30==observed_ds) base=observed_ds;
    unsigned code = base - 0x21bf0;
    bool main_code = SegPhys(cs) == code;
    bool irq = SegPhys(cs) + 0x20e30 == base && (ip==0x232 || ip==0x2d8 || ip==0x2dc || ip==0x30a || ip==0x313);
    bool lifecycle = SegPhys(cs) + 0x20b20 == base;
    bool loader = SegPhys(cs) + 0x1ee80 == base;
    bool music = loader_active && SegPhys(cs) + 0x20e30 == base && (ip==0x2d8 || ip==0x2dc);
    bool exit_stage = main_code && (ip==0xa56 || ip==0xa61 || ip==0xaef || ip==0xc2e || ip==0xc42);
    if (!main_code && !lifecycle && !loader && !music && !irq) return;
    if (main_code && !exit_stage && !irq && !(ip==0x444 || ip==0x447 || ip==0xa1e || ip==0xa23 || ip==0xa39 || ip==0xa3e || ip==0xa43 || ip==0xd44 || ip==0xd72)) return;
    if (lifecycle && !(ip==0x8b1 || ip==0x1432 || ip==0x14a9 || ip==0x1504 || ip==0x1ace || ip==0x969 || ip==0xa0c || ip==0xa3d || ip==0x151c || ip==0x1960 || ip==0x1697 || ip==0x1789 || ip==0x17c0 || ip==0x17e2 || ip==0x18f9 || ip==0x197d || ip==0x1982 || ip==0x1a82 || ip==0x1a79 || ip==0x17dd || ip==0x18b0 || ip==0x175a || ip==0x194f || ip==0xcb5 || ip==0xc0b || ip==0xc10)) return;
    if (loader && !(ip==0x2b || ip==0x102 || ip==0x110 || ip==0xb || ip==0x115 || ip==0x13a || ip==0x34c || ip==0x355 || ip==0xa00 || ip==0xb28 || ip==0xd66 || ip==0xea4 || ip==0xfe6)) return;
    if (lifecycle && ip==0xa3d) loader_active = true;
    if (lifecycle && ip==0xcb5) loader_active = false;
    lifecycle = lifecycle || exit_stage || loader || music;
    // Three independent main-code signatures, no relocatable operands.
    if (mem_readw(code+0x444)!=0x2ea3 || mem_readb(code+0x446)!=0x0f ||
        mem_readw(code+0xd44)!=0x0beb || mem_readw(code+0xd72)!=0xe5e9 ||
        mem_readb(code+0xd74)!=0xf3) return;
    if (main_code && ip==0x444) update_active=true;
    if (main_code && ip==0xd72) update_active=false;
    std::lock_guard<std::mutex> lock(trace_mutex);
    observed_ds = base;
    std::fprintf(file, "{\"event\":\"%s\",\"ip\":%u,\"cs\":%u,\"ds\":%u,\"ss\":%u,\"bp\":%u,\"pic_ms\":%.9f,\"launch_call\":%u,\"decoder\":\"%s\",\"cycles_max\":%d,\"cycles_auto\":%s",
        irq ? (music ? "music" : "irq") : (loader ? "loader" : (lifecycle ? "lifecycle" : "instruction")),ip,(unsigned)SegValue(cs),(unsigned)SegValue(ds),(unsigned)SegValue(ss),(unsigned)reg_bp,
        PIC_FullIndex() + (double)pending_cycles / CPU_CycleMax,emulation_launch_call.load(),DBP_CPU_GetDecoderName(),(int)CPU_CycleMax,CPU_CycleAutoAdjust ? "true":"false");
    if (irq) {
        unsigned return_sp=(Bit16u)(reg_sp+(ip==0x313 ? 0 : 18));
        std::fprintf(file,",\"return_ip\":%u,\"return_cs\":%u,\"return_flags\":%u",
            (unsigned)mem_readw(SegPhys(ss)+return_sp),(unsigned)mem_readw(SegPhys(ss)+(Bit16u)(return_sp+2)),
            (unsigned)mem_readw(SegPhys(ss)+(Bit16u)(return_sp+4)));
        std::fprintf(file,",\"cycles_remaining\":%d,\"pending_cycles\":%u",(int)CPU_Cycles,pending_cycles);
        DBP_WR1_PitState(file); DBP_WR1_PicState(file); DBP_WR1_VgaState(file);
        unsigned driver_vector = mem_readd(0x63*4);
        unsigned driver_base = (driver_vector>>16)<<4;
        std::fprintf(file,",\"timer\":%d,\"pit0_elapsed_ms\":%.9f,\"speaker_index\":%d,\"bios_countdown\":%u,\"bios_reload\":%u,\"driver_vector\":%u,\"driver_tick_ip\":%u",
            word(base,0xf2e),PIC_FullIndex()+(double)pending_cycles/CPU_CycleMax-DBP_WR1_PIT0Start(),
            word(base,0xf2c),(unsigned)mem_readd(base+0xc41a),(unsigned)mem_readd(base+0xc41f),driver_vector,(unsigned)mem_readw(driver_base+0x4a80));
        std::fprintf(file,",\"speaker_elapsed\":%u",(unsigned)mem_readd(base+0xf30));
        unsigned sound = mem_readd(base+0xc40b);
        int sound_index = word(base,0xf2c);
        for (int step=0;step<2;++step) {
            unsigned entry=((sound>>16)<<4)+(Bit16u)((sound&0xffff)+4*(sound_index+step));
            std::fprintf(file,",\"speaker_%s\":[%u,%d]",step ? "next" : "entry",
                sound_index<0 ? 0 : (unsigned)mem_readw(entry),sound_index<0 ? 0 : word(entry,2));
        }
        unsigned bios_vector=mem_readd(base+0xf38),user_vector=mem_readd(0x1c*4);
        std::fprintf(file,",\"bios_handler\":%u,\"int1c_handler\":%u,\"bios_ticks\":%u,\"bios_code\":[",
            bios_vector,user_vector,(unsigned)mem_readd(0x46c));
        unsigned bios_base=((bios_vector>>16)<<4)+(bios_vector&0xffff);
        for (int i=0;i<19;++i) std::fprintf(file,"%s%u",i ? "," : "",(unsigned)mem_readb(bios_base+i));
        std::fprintf(file,"],\"int1c_code\":[");
        unsigned user_base=((user_vector>>16)<<4)+(user_vector&0xffff);
        for (int i=0;i<5;++i) std::fprintf(file,"%s%u",i ? "," : "",(unsigned)mem_readb(user_base+i));
        std::fprintf(file,"]");
        music_state(file);
        std::fprintf(file,"}\n");
        std::fflush(file);
        return;
    }
    state(file,base);
    if (main_code && (ip==0x444 || ip==0xa1e)) movement_state(file,base,ip==0x444);
    if (main_code && (ip==0xd72 || ip==0x444 || ip==0xa1e)) {
        std::fprintf(file,",\"cycles_remaining\":%d,\"pending_cycles\":%u,\"cpu_ax\":%u,\"cpu_flags\":%u",(int)CPU_Cycles,pending_cycles,(unsigned)reg_ax,(unsigned)reg_flags);
        clock_state(file,base); music_state(file);
        keyboard_game(file,base); DBP_WR1_KeyboardState(file);
        DBP_WR1_PitState(file); DBP_WR1_PicState(file); DBP_WR1_VgaState(file);
    }
    if (music) {
        music_state(file);
        std::fprintf(file,",\"cycles_remaining\":%d,\"pending_cycles\":%u",(int)CPU_Cycles,pending_cycles);
        DBP_WR1_PitState(file); DBP_WR1_PicState(file); DBP_WR1_VgaState(file);
    }
    if (lifecycle) {
        std::fprintf(file,",\"stack_args\":[");
        for (int i=0;i<5;++i) std::fprintf(file,"%s%d",i ? "," : "",word(SegPhys(ss),(Bit16u)(reg_bp+6+2*i)));
        std::fprintf(file,"],\"stack_locals\":[");
        for (int i=0;i<8;++i) std::fprintf(file,"%s%d",i ? "," : "",word(SegPhys(ss),(Bit16u)(reg_bp-2-2*i)));
        std::fprintf(file,"]");
        std::fprintf(file,",\"si\":%d,\"di\":%d,\"destination_x\":%d,\"destination_y\":%d,\"restart\":%d,\"player_draw\":%d}\n",
            (Bit16s)reg_si,(Bit16s)reg_di,word(base,0xaf88),word(base,0xb88e),word(base,0x1ac),word(base,0x1bd));
        std::fflush(file);
        return;
    }
    std::fprintf(file, ",\"main_iteration\":%u,\"idle_ticks\":%d,\"right_index\":%d,\"left_index\":%d}\n",
        (unsigned)mem_readw(SegPhys(ss)+(Bit16u)(reg_bp-2)),
        word(SegPhys(ss),(Bit16u)(reg_bp-8)),word(SegPhys(ss),(Bit16u)(reg_bp-10)),word(SegPhys(ss),(Bit16u)(reg_bp-12)));
    std::fflush(file);
}

void DBP_WR1_Observe(unsigned ip) { observe(ip,0); }
// Dynamic blocks account cycles at exit. Add pending cycles to the timestamp
// without writing CPU_Cycles or inserting any emulated instruction.
void DBP_WR1_ObserveDynamic(unsigned ip, unsigned pending_cycles) { observe(ip,pending_cycles); }

bool DBP_WR1_OplActive() { return opl_active; }
void DBP_WR1_PicSlice(long long event_id, double event_index) {
    FILE* file = trace_file();
    if (!file || !opl_active) return;
    std::lock_guard<std::mutex> lock(trace_mutex);
    std::fprintf(file,"{\"event\":\"pic_slice\",\"pic_ticks\":%u,\"pic_ms\":%.9f,\"cycles\":%d,\"cycle_left\":%d,\"next_event_id\":%lld,\"next_event_index\":%.9f,\"launch_call\":%u}\n",
        (unsigned)PIC_Ticks,PIC_FullIndex(),(int)CPU_Cycles,(int)CPU_CycleLeft,event_id,event_index,emulation_launch_call.load());
    std::fflush(file);
}

void DBP_WR1_Input(unsigned port, unsigned device, unsigned index, unsigned id, int value) {
    FILE* file = trace_file();
    if (!file || !value) return;
    std::lock_guard<std::mutex> lock(trace_mutex);
    std::fprintf(file,"{\"event\":\"input\",\"call\":%u,\"port\":%u,\"device\":%u,\"index\":%u,\"id\":%u,\"value\":%d}\n",
        frontend_call.load(),port,device,index,id,value);
}

void DBP_WR1_BeginFrontend() { ++frontend_call; }

void DBP_WR1_KeyboardInput(unsigned key,bool pressed) {
    FILE* file=trace_file();
    if (!file || !observed_ds) return;
    std::lock_guard<std::mutex> lock(trace_mutex);
    std::fprintf(file,"{\"event\":\"keyboard_input\",\"key\":%u,\"pressed\":%s,\"pic_ms\":%.9f,\"launch_call\":%u,\"cpu_ip\":%u,\"cpu_cs\":%u,\"cycles_remaining\":%d,\"pending_cycles\":0",
        key,pressed ? "true":"false",PIC_FullIndex(),emulation_launch_call.load(),(unsigned)reg_eip,(unsigned)SegValue(cs),(int)CPU_Cycles);
    DBP_WR1_KeyboardState(file); DBP_WR1_PitState(file); DBP_WR1_PicState(file); DBP_WR1_VgaState(file);
    std::fprintf(file,"}\n"); std::fflush(file);
}

// Called after joining the prior worker frame, before launching the next one.
void DBP_WR1_FrontendBoundary() {
    FILE* file = trace_file();
    if (!file) return;
    std::lock_guard<std::mutex> lock(trace_mutex);
    std::fprintf(file,"{\"event\":\"frontend\",\"call\":%u,\"pic_ms\":%.9f,\"decoder\":\"%s\"",
        frontend_call.load(),PIC_FullIndex(),DBP_CPU_GetDecoderName());
    if (observed_ds) state(file,observed_ds);
    if (observed_ds) music_state(file);
    if (observed_ds) clock_state(file,observed_ds);
    if (observed_ds) { keyboard_game(file,observed_ds); DBP_WR1_KeyboardState(file); }
    std::fprintf(file,",\"cpu_cs\":%u,\"cpu_ip\":%u,\"cpu_ax\":%u,\"cpu_flags\":%u,\"cycles_remaining\":%d",
        (unsigned)SegValue(cs),(unsigned)reg_eip,(unsigned)reg_ax,(unsigned)reg_flags,(int)CPU_Cycles);
    if (observed_ds) { DBP_WR1_PitState(file); DBP_WR1_PicState(file); DBP_WR1_VgaState(file); }
    std::fprintf(file,",\"pit0_elapsed_ms\":%.9f,\"pit0_delay_ms\":%.9f",
        PIC_FullIndex()-DBP_WR1_PIT0Start(),DBP_WR1_PIT0Delay());
    std::fprintf(file,"}\n");
    std::fflush(file);
    emulation_launch_call.store(frontend_call.load());
}

// Called while emulation is paused, immediately after loading a savestate.
void DBP_WR1_LoadBoundary() {
    FILE* file = trace_file();
    if (!file) return;
    std::lock_guard<std::mutex> lock(trace_mutex);
    frontend_call.store(0);
    update_active=false;
    emulation_launch_call.store(0);
    observed_ds=0;
    opl_active=false;
    std::fprintf(file,"{\"event\":\"load\",\"pic_ms\":%.9f,\"decoder\":\"%s\"}\n",PIC_FullIndex(),DBP_CPU_GetDecoderName());
    std::fflush(file);
}
