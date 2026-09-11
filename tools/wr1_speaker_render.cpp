// Offline adapter for DOSBox Pure's original PC-speaker kernel.
// SPDX-License-Identifier: GPL-2.0-or-later
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <vector>
#include <stdexcept>
using Bitu = uint32_t;
using Bit16s = int16_t;
static const uint32_t PIT_TICK_RATE = 1193182;
static uint32_t PIC_Ticks = 1;
static float tick_index;
static float PIC_TickIndex() { return tick_index; }
static int16_t MixTemp[192];
static std::ofstream output;
struct MixerChannel {
    void Enable(bool) {}
    void AddSamples_m16(Bitu n, const Bit16s* data) {
        output.write(reinterpret_cast<const char*>(data), n * 2);
    }
};
// ORIGINAL_SPEAKER_KERNEL
int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("Usage: speaker_render events.txt output.pcm");
        std::ifstream input(argv[1]);
        unsigned rate, total_ms, count;
        if (!(input >> rate >> total_ms >> count) || rate % 1000 || rate < 8000 || rate > 192000)
            throw std::runtime_error("Invalid header");
        struct Event { double ms; unsigned divisor; };
        std::vector<Event> events(count);
        for (auto& e : events) if (!(input >> e.ms >> e.divisor)) throw std::runtime_error("Truncated events");
        output.open(argv[2], std::ios::binary);
        if (!output) throw std::runtime_error("Cannot open output");
        MixerChannel channel;
        spkr.chan = &channel;
        spkr.rate = rate;
        spkr.mode = SPKR_OFF;
        spkr.pit_mode = 3;
        spkr.pit_max = spkr.pit_new_max = (1000.0f / PIT_TICK_RATE) * 1320;
        spkr.pit_half = spkr.pit_new_half = spkr.pit_max / 2;
        spkr.min_tr = (PIT_TICK_RATE + rate / 2 - 1) / (rate / 2);
        size_t cursor = 0;
        for (unsigned ms = 0; ms < total_ms; ++ms) {
            PIC_Ticks = ms + 1;
            while (cursor < events.size() && events[cursor].ms < ms + 1) {
                auto e = events[cursor++];
                tick_index = float(e.ms - ms);
                if (e.divisor) {
                    PCSPEAKER_SetType(3);
                    PCSPEAKER_SetCounter(e.divisor, 3);
                } else PCSPEAKER_SetType(0);
            }
            PCSPEAKER_CallBack(rate / 1000);
        }
        if (cursor != events.size() || !output) throw std::runtime_error("Incomplete output");
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
