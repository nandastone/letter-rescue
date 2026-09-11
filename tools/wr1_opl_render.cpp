// Offline PCM renderer using the same DBOPL implementation as the native probe.
// SPDX-License-Identifier: GPL-2.0-or-later
// Build against the pinned DOSBox Pure source; no emulator code enters Godot.
#include <cmath>
#include "dbopl.h"
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace DBOPL { void InitTables(); }
// DBOPL's unused DOSBox mixer adapter is linked on Windows. The offline path
// calls Chip directly; fail loudly if it ever reaches that adapter.
void MixerChannel::AddSamples_m32(Bitu, const Bit32s*) { throw std::runtime_error("Unexpected DOSBox mixer call"); }
void MixerChannel::AddSamples_s32(Bitu, const Bit32s*) { throw std::runtime_error("Unexpected DOSBox mixer call"); }

static uint32_t read32(std::istream& in) {
    unsigned char b[4];
    if (!in.read(reinterpret_cast<char*>(b),4)) throw std::runtime_error("Truncated register stream");
    return uint32_t(b[0])|(uint32_t(b[1])<<8)|(uint32_t(b[2])<<16)|(uint32_t(b[3])<<24);
}

int main(int argc, char** argv) {
    try {
        if (argc!=3) throw std::runtime_error("Usage: wr1_opl_render events.bin output.pcm");
        std::ifstream input(argv[1],std::ios::binary);
        std::ofstream output(argv[2],std::ios::binary);
        if (!input || !output) throw std::runtime_error("Cannot open input/output");
        const auto rate=read32(input),count=read32(input),total=read32(input);
        if (rate<8000 || rate>192000) throw std::runtime_error("Unsupported sample rate");
        DBOPL::InitTables();
        // The reference capture uses SB16 / automatic AdLib mode: OPL3 hardware
        // operating in its OPL2-compatible mode (registers below 100h).
        DBOPL::Chip chip(true);
        chip.Setup(rate);
        uint32_t cursor=0;
        auto generate = [&](uint32_t end) {
            if (end<cursor || end>total) throw std::runtime_error("Invalid event sample position");
            while (cursor<end) {
                Bit32s buffer[512];
                const auto n=std::min(uint32_t(512),end-cursor);
                chip.GenerateBlock2(n,buffer);
                for (uint32_t i=0;i<n;++i) {
                    const auto sample=static_cast<uint16_t>(std::max(-32768,std::min(32767,int(buffer[i]))));
                    const char bytes[2]={char(sample&255),char(sample>>8)};
                    output.write(bytes,2);
                }
                cursor+=n;
            }
        };
        for (uint32_t i=0;i<count;++i) {
            const auto sample=read32(input);
            const int reg=input.get(),value=input.get();
            if (reg<0 || value<0) throw std::runtime_error("Truncated register event");
            generate(sample);
            chip.WriteReg(reg,value);
        }
        generate(total);
        if (!output) throw std::runtime_error("PCM write failed");
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
