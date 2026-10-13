"""Build an isolated read-only CPU probe using the existing pinned core objects.

No reference DLL, original source, emulated instructions or cycle costs change.
The probe DLL must pass a traced/untraced replay comparison before use as evidence.
"""
from pathlib import Path
import argparse, hashlib, json, os, subprocess
from instrument_core import COMMIT,instrument_frontend


def build(checkout, compiler, output, pic=False, cpu_runs=False, irq=False, poll=False, script=False, blit=False, sprite=False, cursor=False, geometry=False, frame=False, timer_execution=False, device_execution=False, interrupt_entry=False, animation_loop=False, sound_start=False, audio_dma=False, activity_backdrop=False):
    if animation_loop:audio_dma=True
    if animation_loop or sound_start or audio_dma or activity_backdrop:device_execution=True
    if irq:pic=cpu_runs=True
    if poll or script:cpu_runs=True
    checkout=checkout.resolve(); compiler=compiler.resolve(); output=output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    revision=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()
    if revision!=COMMIT:raise ValueError('Unresearched core revision')
    original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/cpu/core_normal.cpp']).replace(b'\r\n',b'\n')
    current=(checkout/'src/cpu/core_normal.cpp').read_bytes().replace(b'\r\n',b'\n')
    if original!=current:raise ValueError('Normal CPU source has other changes')
    source=original.decode()
    entry='Bits CPU_Core_Normal_Run(void) {'
    hook='\t\tLOADIP;'
    if source.count(entry)!=1 or entry+'\n\twhile (CPU_Cycles-->0) {\n'+hook not in source:raise ValueError('CPU hooks differ')
    source=source.replace(entry,'#include "trace_probe.h"\n\n'+entry).replace(hook,hook+'\n\t\tTreehouseTraceInstruction(core.cseip);',1)
    if cpu_runs:
        source=source.replace('#include "core_normal/string.h"','#include "cpu_run_probe.h"\n#include "core_normal/string.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseCpuInstruction(core.cseip);')
        cpu_probe=Path(__file__).with_name('cpu_run_probe.h').read_bytes();(output/'cpu_run_probe.h').write_bytes(cpu_probe)
        string_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/cpu/core_normal/string.h']).replace(b'\r\n',b'\n')
        if string_original!=(checkout/'src/cpu/core_normal/string.h').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('CPU string source has other changes')
        strings=string_original.decode()
        if strings.count('--CPU_Cycles')!=21:raise ValueError('CPU string iteration hooks differ')
        (output/'core_normal').mkdir()
        (output/'core_normal/string.h').write_text(strings.replace('--CPU_Cycles','(TreehouseCpuStringIteration(), --CPU_Cycles)'),encoding='utf-8')
        prefix_hashes={}
        for filename,count in [('prefix_none.h',2),('prefix_66.h',1)]:
            rel='src/cpu/core_normal/'+filename
            original_prefix=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:'+rel]).replace(b'\r\n',b'\n')
            if original_prefix!=(checkout/rel).read_bytes().replace(b'\r\n',b'\n'):raise ValueError('CPU prefix source has other changes')
            prefix=original_prefix.decode()
            if prefix.count('CPU_Cycles++;')!=count:raise ValueError('CPU cycle credit hooks differ')
            (output/'core_normal'/filename).write_text(prefix.replace('CPU_Cycles++;','CPU_Cycles++; TreehouseCpuCycleCredit();'),encoding='utf-8')
            prefix_hashes[rel]=hashlib.sha256(original_prefix).hexdigest()
    if poll:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "poll_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehousePollInstruction(core.cseip);')
        poll_probe=Path(__file__).with_name('poll_probe.h').read_bytes();(output/'poll_probe.h').write_bytes(poll_probe)
    if script:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "script_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseScriptInstruction(core.cseip);')
        script_probe=Path(__file__).with_name('script_probe.h').read_bytes();(output/'script_probe.h').write_bytes(script_probe)
    if blit:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "blit_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseBlitInstruction(core.cseip);')
        blit_probe=Path(__file__).with_name('blit_probe.h').read_bytes();(output/'blit_probe.h').write_bytes(blit_probe)
    if sprite:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "sprite_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseSpriteInstruction(core.cseip);')
        sprite_probe=Path(__file__).with_name('sprite_probe.h').read_bytes();(output/'sprite_probe.h').write_bytes(sprite_probe)
    if cursor:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "cursor_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseCursorInstruction(core.cseip);')
        cursor_probe=Path(__file__).with_name('cursor_probe.h').read_bytes();(output/'cursor_probe.h').write_bytes(cursor_probe)
    if geometry:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "geometry_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseGeometryInstruction(core.cseip);')
        geometry_probe=Path(__file__).with_name('geometry_probe.h').read_bytes();(output/'geometry_probe.h').write_bytes(geometry_probe)
    if frame:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "frame_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseFrameInstruction(core.cseip);')
        frame_probe=Path(__file__).with_name('frame_probe.h').read_bytes();(output/'frame_probe.h').write_bytes(frame_probe)
    if timer_execution:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "timer_execution_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseTimerExecutionInstruction(core.cseip);')
        timer_execution_probe=Path(__file__).with_name('timer_execution_probe.h').read_bytes();(output/'timer_execution_probe.h').write_bytes(timer_execution_probe)
    if device_execution:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "device_execution_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseDeviceExecutionInstruction(core.cseip);')
        device_execution_probe=Path(__file__).with_name('device_execution_probe.h').read_bytes();(output/'device_execution_probe.h').write_bytes(device_execution_probe)
    if animation_loop:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "animation_loop_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseAnimationLoopInstruction(core.cseip);')
        animation_loop_probe=Path(__file__).with_name('animation_loop_probe.h').read_bytes();(output/'animation_loop_probe.h').write_bytes(animation_loop_probe)
    if sound_start:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "sound_start_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseSoundStartInstruction(core.cseip);')
        sound_start_probe=Path(__file__).with_name('sound_start_probe.h').read_bytes();(output/'sound_start_probe.h').write_bytes(sound_start_probe)
    if activity_backdrop:
        source=source.replace('#include "trace_probe.h"','#include "trace_probe.h"\n#include "activity_backdrop_probe.h"')
        source=source.replace('TreehouseTraceInstruction(core.cseip);','TreehouseTraceInstruction(core.cseip);\n\t\tTreehouseActivityBackdropInstruction(core.cseip);')
        activity_backdrop_probe=Path(__file__).with_name('activity_backdrop_probe.h').read_bytes();(output/'activity_backdrop_probe.h').write_bytes(activity_backdrop_probe)
    (output/'core_normal.cpp').write_text(source,encoding='utf-8')
    probe=Path(__file__).with_name('trace_probe.h').read_bytes();(output/'trace_probe.h').write_bytes(probe)
    dos_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/dos/dos.cpp']).replace(b'\r\n',b'\n')
    if dos_original!=(checkout/'src/dos/dos.cpp').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('DOS source has other changes')
    dos=dos_original.decode();begin='static inline void modify_cycles(Bits value) {'
    end='\t\tCPU_Cycles = 5;\n\t}\n}'
    if dos.count(begin)!=1 or dos.count(end)!=1:raise ValueError('DOS transfer hooks differ')
    dos=dos.replace(begin,'#include "dos_probe.h"\n'+begin+'\n\tconst Bits trace_cycles=CPU_Cycles;\n\tconst Bit64s trace_io=CPU_IODelayRemoved;')
    dos=dos.replace(end,end[:-1]+'\tTreehouseObserveDosTransfer(value,trace_cycles,trace_io);\n}')
    (output/'dos.cpp').write_text(dos,encoding='utf-8')
    dos_probe=Path(__file__).with_name('dos_probe.h').read_bytes();(output/'dos_probe.h').write_bytes(dos_probe)
    env=dict(os.environ);env['PATH']=str(compiler.parent)+os.pathsep+env['PATH']
    obj=output/'core_normal.o';dll=output/'dosbox_pure_trace.dll'
    flags=['-DNDEBUG','-O2','-std=gnu++11','-fomit-frame-pointer','-fexceptions','-Wno-address-of-packed-member','-Wno-format','-Wno-switch','-fvisibility=hidden','-ffunction-sections','-D__LIBRETRO__','-D_FILE_OFFSET_BITS=64','-pthread','-I'+str(checkout/'include'),'-I'+str(checkout/'libretro-common/include'),'-I'+str(checkout/'src/cpu')]
    commands=[[str(compiler),*flags,'-c',str(output/'core_normal.cpp'),'-o',str(obj)]]
    dos_obj=output/'dos.o';commands.append([str(compiler),*flags,'-I'+str(checkout/'src/dos'),'-c',str(output/'dos.cpp'),'-o',str(dos_obj)])
    extra_objects=[];extra_manifest={}
    if device_execution:
        sound_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/hardware/sblaster.cpp']).replace(b'\r\n',b'\n')
        if sound_original!=(checkout/'src/hardware/sblaster.cpp').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('Sound Blaster source has other changes')
        sound_probe=Path(__file__).with_name('sound_hardware_probe.h').read_bytes();(output/'sound_hardware_probe.h').write_bytes(sound_probe)
        sound_source=sound_original.decode()
        if audio_dma:
            audio_probe=Path(__file__).with_name('audio_dma_probe.h').read_bytes();(output/'audio_dma_probe.h').write_bytes(audio_probe)
            needle='static void GenerateDMASound(Bitu size) {'
            if sound_source.count(needle)!=1:raise ValueError('DMA sound hook differs')
            sound_source=sound_source.replace(needle,'#include "audio_dma_probe.h"\n'+needle+'\n\tTreehouseAudioDmaScope treehouse_audio_observer(size);')
            extra_manifest['audio_dma_probe_sha256']=hashlib.sha256(audio_probe).hexdigest()
        (output/'sblaster.cpp').write_bytes(sound_source.encode()+b'\n#include "sound_hardware_probe.h"\n');sound_obj=output/'sblaster.o';extra_objects.append(sound_obj)
        commands.append([str(compiler),*flags,'-I'+str(checkout/'src/hardware'),'-c',str(output/'sblaster.cpp'),'-o',str(sound_obj)])
        extra_manifest.update(sound_source_sha256=hashlib.sha256(sound_original).hexdigest(),sound_hardware_probe_sha256=hashlib.sha256(sound_probe).hexdigest())
        mouse_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/ints/mouse.cpp']).replace(b'\r\n',b'\n')
        if mouse_original!=(checkout/'src/ints/mouse.cpp').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('Mouse source has other changes')
        mouse_probe=Path(__file__).with_name('mouse_hardware_probe.h').read_bytes();(output/'mouse_hardware_probe.h').write_bytes(mouse_probe)
        (output/'mouse.cpp').write_bytes(mouse_original+b'\n#include "mouse_hardware_probe.h"\n');mouse_obj=output/'mouse.o';extra_objects.append(mouse_obj)
        commands.append([str(compiler),*flags,'-I'+str(checkout/'src/ints'),'-c',str(output/'mouse.cpp'),'-o',str(mouse_obj)])
        extra_manifest.update(mouse_source_sha256=hashlib.sha256(mouse_original).hexdigest(),mouse_hardware_probe_sha256=hashlib.sha256(mouse_probe).hexdigest())
    if audio_dma:
        mixer_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/hardware/mixer.cpp']).replace(b'\r\n',b'\n')
        if mixer_original!=(checkout/'src/hardware/mixer.cpp').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('Mixer source has other changes')
        mixer_probe=Path(__file__).with_name('mixer_state_probe.h').read_bytes();(output/'mixer_state_probe.h').write_bytes(mixer_probe)
        (output/'mixer.cpp').write_bytes(mixer_original+b'\n#include "mixer_state_probe.h"\n');mixer_obj=output/'mixer.o';extra_objects.append(mixer_obj)
        commands.append([str(compiler),*flags,'-I'+str(checkout/'src/hardware'),'-c',str(output/'mixer.cpp'),'-o',str(mixer_obj)])
        extra_manifest.update(mixer_source_sha256=hashlib.sha256(mixer_original).hexdigest(),mixer_state_probe_sha256=hashlib.sha256(mixer_probe).hexdigest())
    if animation_loop:
        frontend_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:dosbox_pure_libretro.cpp']).replace(b'\r\n',b'\n')
        frontend=instrument_frontend(frontend_original.decode())
        if frontend.encode()!=(checkout/'dosbox_pure_libretro.cpp').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('Prepared frontend source has other changes')
        signature='static bool GFX_AdvanceFrame(bool force_skip, bool force_no_auto_adjust)'
        frontend=frontend.replace(signature,'static Bit32u* treehouse_lastframe_ptr=nullptr;\n'+signature)
        if frontend.count('\tSt.FrameTicks++;')!=1:raise ValueError('Frame state observer hook differs')
        frontend=frontend.replace('\tSt.FrameTicks++;','\ttreehouse_lastframe_ptr=&St.LastFrameCount;\n\tSt.FrameTicks++;')
        frontend+='\nextern "C" void TreehouseReadAudioFrontend(double* out){out[0]=dbp_audio_remain;out[1]=av_info.timing.sample_rate;out[2]=av_info.timing.fps;out[3]=dbp_throttle.mode;out[4]=dbp_throttle.rate;out[5]=treehouse_lastframe_ptr?*treehouse_lastframe_ptr:0;out[6]=dbp_framecount;}\n'
        (output/'dosbox_pure_libretro.cpp').write_text(frontend,encoding='utf-8');frontend_obj=output/'frontend.o';extra_objects.append(frontend_obj)
        commands.append([str(compiler),*flags,'-I'+str(checkout),'-c',str(output/'dosbox_pure_libretro.cpp'),'-o',str(frontend_obj)])
        extra_manifest.update(frontend_original_sha256=hashlib.sha256(frontend_original).hexdigest(),frontend_observed_sha256=hashlib.sha256(frontend.encode()).hexdigest())
    if interrupt_entry:
        cpu_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/cpu/cpu.cpp']).replace(b'\r\n',b'\n')
        if cpu_original!=(checkout/'src/cpu/cpu.cpp').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('CPU source has other changes')
        entry_probe=Path(__file__).with_name('interrupt_entry_probe.h').read_bytes();(output/'interrupt_entry_probe.h').write_bytes(entry_probe)
        cpu_source=cpu_original.decode()
        replacements={
            'Bit8u lastint;':'#include "interrupt_entry_probe.h"\nBit8u lastint;',
            '\tlastint=num;\n\tFillFlags();':'\tlastint=num;\n\tFillFlags();\n\tTreehouseInterruptEnterBefore(num,type,oldeip);',
            '\t\tSegs.phys[cs]=Segs.val[cs]<<4;\n\t\tcpu.code.big=false;\n\t\treturn;':'\t\tSegs.phys[cs]=Segs.val[cs]<<4;\n\t\tcpu.code.big=false;\n\t\tTreehouseInterruptEnterAfter();\n\t\treturn;',
            'void CPU_IRET(bool use32,Bitu oldeip) {':'void CPU_IRET(bool use32,Bitu oldeip) {\n\tconst bool treehouse_return=TreehouseInterruptReturnBefore(use32);',
            '\t\tcpu.code.big=false;\n\t\tDestroyConditionFlags();\n\t\treturn;':'\t\tcpu.code.big=false;\n\t\tDestroyConditionFlags();\n\t\tif(treehouse_return)TreehouseInterruptReturnAfter();\n\t\treturn;'
        }
        for before,after in replacements.items():
            if cpu_source.count(before)!=1:raise ValueError('Interrupt entry hook differs: '+repr(before))
            cpu_source=cpu_source.replace(before,after)
        (output/'cpu.cpp').write_text(cpu_source,encoding='utf-8');cpu_obj=output/'cpu.o';extra_objects.append(cpu_obj)
        commands.append([str(compiler),*flags,'-c',str(output/'cpu.cpp'),'-o',str(cpu_obj)])
        extra_manifest.update(interrupt_cpu_source_sha256=hashlib.sha256(cpu_original).hexdigest(),interrupt_entry_probe_sha256=hashlib.sha256(entry_probe).hexdigest())
    if sound_start:extra_manifest['sound_start_probe_sha256']=hashlib.sha256(sound_start_probe).hexdigest()
    if activity_backdrop:extra_manifest['activity_backdrop_probe_sha256']=hashlib.sha256(activity_backdrop_probe).hexdigest()
    if animation_loop:extra_manifest['animation_loop_probe_sha256']=hashlib.sha256(animation_loop_probe).hexdigest()
    if poll:extra_manifest['poll_probe_sha256']=hashlib.sha256(poll_probe).hexdigest()
    if script:extra_manifest['script_probe_sha256']=hashlib.sha256(script_probe).hexdigest()
    if blit:extra_manifest['blit_probe_sha256']=hashlib.sha256(blit_probe).hexdigest()
    if sprite:extra_manifest['sprite_probe_sha256']=hashlib.sha256(sprite_probe).hexdigest()
    if cursor:extra_manifest['cursor_probe_sha256']=hashlib.sha256(cursor_probe).hexdigest()
    if geometry:extra_manifest['geometry_probe_sha256']=hashlib.sha256(geometry_probe).hexdigest()
    if frame:extra_manifest['frame_probe_sha256']=hashlib.sha256(frame_probe).hexdigest()
    if timer_execution:extra_manifest['timer_execution_probe_sha256']=hashlib.sha256(timer_execution_probe).hexdigest()
    if device_execution:extra_manifest['device_execution_probe_sha256']=hashlib.sha256(device_execution_probe).hexdigest()
    if cpu_runs:
        loop_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/dosbox.cpp']).replace(b'\r\n',b'\n')
        if loop_original!=(checkout/'src/dosbox.cpp').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('Main loop source has other changes')
        loop=loop_original.decode()
        substitutions={
            'static Bitu Normal_Loop(void) {':'extern void TreehouseCpuBoundary(unsigned kind,unsigned id,int result);\nstatic Bitu Normal_Loop(void) {',
            '\t\t\tret = (*cpudecoder)();':'\t\t\tunsigned trace_decoder=cpudecoder==CPU_Core_Normal_Run?1:cpudecoder==CPU_Core_Normal_Trap_Run?2:3;\n\t\t\tTreehouseCpuBoundary(1,trace_decoder,0);\n\t\t\tret = (*cpudecoder)();\n\t\t\tTreehouseCpuBoundary(2,trace_decoder,ret);',
            '\t\t\t\tBitu blah = (*CallBack_Handlers[ret])();':'\t\t\t\tTreehouseCpuBoundary(3,ret,0);\n\t\t\t\tBitu blah = (*CallBack_Handlers[ret])();\n\t\t\t\tTreehouseCpuBoundary(4,ret,blah);'
        }
        for before,after in substitutions.items():
            if loop.count(before)!=1:raise ValueError('CPU run hook differs')
            loop=loop.replace(before,after)
        (output/'dosbox.cpp').write_text(loop,encoding='utf-8');loop_obj=output/'dosbox.o';extra_objects.append(loop_obj)
        commands.append([str(compiler),*flags,'-I'+str(checkout/'src'),'-I'+str(checkout/'src/gui'),'-c',str(output/'dosbox.cpp'),'-o',str(loop_obj)])
        extra_manifest.update(cpu_run_probe_sha256=hashlib.sha256(cpu_probe).hexdigest(),loop_source_sha256=hashlib.sha256(loop_original).hexdigest(),string_source_sha256=hashlib.sha256(string_original).hexdigest(),prefix_source_sha256=prefix_hashes)
    if pic:
        from instrument_pic import instrument
        pic_original=subprocess.check_output(['git','-C',str(checkout),'show','HEAD:src/hardware/pic.cpp']).replace(b'\r\n',b'\n')
        if pic_original!=(checkout/'src/hardware/pic.cpp').read_bytes().replace(b'\r\n',b'\n'):raise ValueError('PIC source has other changes')
        (output/'pic.cpp').write_text(instrument(pic_original.decode(),irq),encoding='utf-8')
        pic_probe=Path(__file__).with_name('pic_probe.h').read_bytes();(output/'pic_probe.h').write_bytes(pic_probe)
        pic_obj=output/'pic.o';extra_objects.append(pic_obj)
        commands.append([str(compiler),*flags,'-I'+str(checkout/'src/hardware'),'-c',str(output/'pic.cpp'),'-o',str(pic_obj)])
        extra_manifest.update(pic_source_sha256=hashlib.sha256(pic_original).hexdigest(),pic_probe_sha256=hashlib.sha256(pic_probe).hexdigest())
        if irq:
            irq_probe=Path(__file__).with_name('irq_probe.h').read_bytes();(output/'irq_probe.h').write_bytes(irq_probe)
            extra_manifest['irq_probe_sha256']=hashlib.sha256(irq_probe).hexdigest()
    objects=sorted((checkout/'build/release').glob('*.o'))
    if len(objects)<100:raise ValueError('Build the ordinary pinned capture core first')
    objects=[p for p in objects if p.name not in ('src~cpu~core_normal.cpp.o','src~dos~dos.cpp.o')]
    if audio_dma:objects=[p for p in objects if p.name!='src~hardware~mixer.cpp.o']
    if animation_loop:objects=[p for p in objects if p.name!='dosbox_pure_libretro.cpp.o']
    if interrupt_entry:objects=[p for p in objects if p.name!='src~cpu~cpu.cpp.o']
    if pic:objects=[p for p in objects if p.name!='src~hardware~pic.cpp.o']
    if cpu_runs:objects=[p for p in objects if p.name!='src~dosbox.cpp.o']
    if device_execution:objects=[p for p in objects if p.name not in ['src~hardware~sblaster.cpp.o','src~ints~mouse.cpp.o']]
    commands.append([str(compiler),'-shared','-static-libgcc','-static-libstdc++','-Wl,--gc-sections','-o',str(dll),str(obj),str(dos_obj),*[str(p) for p in extra_objects+objects],'-lpthread'])
    for i,cmd in enumerate(commands):
        result=subprocess.run(cmd,cwd=checkout,env=env,capture_output=True,text=True)
        (output/f'build-{i}.log').write_text(result.stdout+result.stderr)
        if result.returncode:raise RuntimeError(f'Compiler failed; see {output}/build-{i}.log')
    report=dict(core_revision=revision,probe_sha256=hashlib.sha256(probe).hexdigest(),dll_sha256=hashlib.sha256(dll.read_bytes()).hexdigest(),
        dos_probe_sha256=hashlib.sha256(dos_probe).hexdigest(),dos_source_sha256=hashlib.sha256(dos_original).hexdigest(),
        original_core_sha256=hashlib.sha256((checkout/'dosbox_pure_libretro.dll').read_bytes()).hexdigest(),
        linked_object_sha256={str(p.relative_to(checkout)):hashlib.sha256(p.read_bytes()).hexdigest() for p in objects},commands=commands,**extra_manifest)
    (output/'build.json').write_text(json.dumps(report,indent=2));print(dll)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkout',type=Path,required=True);p.add_argument('--compiler',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--pic',action='store_true');p.add_argument('--cpu-runs',action='store_true');p.add_argument('--irq',action='store_true');p.add_argument('--poll',action='store_true');p.add_argument('--script',action='store_true');p.add_argument('--blit',action='store_true');p.add_argument('--sprite',action='store_true');p.add_argument('--cursor',action='store_true');p.add_argument('--geometry',action='store_true');p.add_argument('--frame',action='store_true');p.add_argument('--timer-execution',action='store_true');p.add_argument('--device-execution',action='store_true');p.add_argument('--interrupt-entry',action='store_true');p.add_argument('--animation-loop',action='store_true');p.add_argument('--sound-start',action='store_true');p.add_argument('--audio-dma',action='store_true');p.add_argument('--activity-backdrop',action='store_true');a=p.parse_args();build(a.checkout,a.compiler,a.output,a.pic,a.cpu_runs,a.irq,a.poll,a.script,a.blit,a.sprite,a.cursor,a.geometry,a.frame,a.timer_execution,a.device_execution,a.interrupt_entry,a.animation_loop,a.sound_start,a.audio_dma,a.activity_backdrop)
