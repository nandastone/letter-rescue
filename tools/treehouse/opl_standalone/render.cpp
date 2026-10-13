// Build-time synthesizer only. Input is generated from source MIDI/patch data.
// DBOPL itself is copied unchanged from the pinned GPL-2.0-or-later source.
#include "dbopl.h"
#include <algorithm>
#include <cstdio>
#include <fstream>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    std::ifstream input(argv[1]);
    uint32_t rate, total, count;
    if (!(input >> rate >> total >> count) || rate < 8000 || rate > 96000 || total > rate * 600) return 3;
    std::ofstream output(argv[2], std::ios::binary);
    if (!output) return 4;
    DBOPL::Handler synth(true);
    synth.Init(rate);
    synth.WriteReg(1, 0x20);
    uint32_t position = 0;
    Bit32s buffer[512];
    auto generate = [&](uint32_t end) {
        while (position < end) {
            auto size = std::min(uint32_t(512), end - position);
            synth.chip.GenerateBlock2(size, buffer);
            for (uint32_t i = 0; i < size; ++i) {
                // Pinned Adlib channel's 1.5 scale; full mixer parity is separate.
                int value = std::clamp(int(buffer[i] * 3 / 2), -32768, 32767);
                output.put(char(value & 255));
                output.put(char((value >> 8) & 255));
            }
            position += size;
        }
    };
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t sample, reg, value;
        if (!(input >> sample >> reg >> value) || sample < position || sample > total || reg > 255 || value > 255) return 5;
        generate(sample);
        synth.WriteReg(reg, value);
    }
    generate(total);
    return output.good() ? 0 : 6;
}
