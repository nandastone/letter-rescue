"""Headless original-game reference runner using the public libretro C interface.

Adapted from the user's local Math Rescue tools/native_probe.py. Public ABI:
https://github.com/libretro/libretro-common/blob/master/include/libretro.h

No host keyboard or desktop automation. Keys are delivered to the emulator's
keyboard callback, held for explicit emulated frontend frames, and released.
Optional snapshots are original emulator video, RAM, save states and audio.
Requires an installed DOSBox Pure core; no dependency on Letter Rescue.
"""
from __future__ import annotations
import ctypes as C
from pathlib import Path
import struct
import wave
from PIL import Image

ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
BATCH = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
INPUT = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
KEYBOARD = C.CFUNCTYPE(None, C.c_bool, C.c_uint, C.c_uint32, C.c_uint16)


class Variable(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]


class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]


class Geometry(C.Structure):
    _fields_ = [('width', C.c_uint), ('height', C.c_uint), ('max_width', C.c_uint),
                ('max_height', C.c_uint), ('aspect', C.c_float)]


class Timing(C.Structure):
    _fields_ = [('fps', C.c_double), ('sample_rate', C.c_double)]


class AVInfo(C.Structure):
    _fields_ = [('geometry', Geometry), ('timing', Timing)]


class MemoryDescriptor(C.Structure):
    _fields_ = [('flags', C.c_uint64), ('ptr', C.c_void_p), ('offset', C.c_size_t),
                ('start', C.c_size_t), ('select', C.c_size_t), ('disconnect', C.c_size_t),
                ('length', C.c_size_t), ('addrspace', C.c_char_p)]


class MemoryMap(C.Structure):
    _fields_ = [('descriptors', C.POINTER(MemoryDescriptor)), ('count', C.c_uint)]


KEYS = {'enter':13, 'escape':27, 'space':32, 'up':273, 'down':274,
        'right':275, 'left':276, 'ctrl':306, 'alt':308, 'backspace':8,
        'f1':282, 'f2':283}


class Native:
    def __init__(self, core: Path, content: Path, output: Path, audio=False):
        self.output = output.resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.paths = {9: str(self.output).encode(), 31: str(self.output).encode()}
        self.values = {b'dosbox_pure_cycles': b'10000', b'dosbox_pure_cpu_core': b'normal',
                       b'dosbox_pure_forcefps': b'false', b'dosbox_pure_savestate': b'on',
                       b'dosbox_pure_conf': b'inside', b'dosbox_pure_menu_time': b'0',
                       b'dosbox_pure_mouse_input': b'virtual',
                       b'dosbox_pure_memory_size': b'16'}
        self.callbacks = []
        self.keyboard = None
        self.keyboard_events = []
        self.held = set()
        self.frame = None
        self.frame_count = 0
        self.pixel_format = 1
        self.capture_audio = audio
        self.memory = []
        self.audio = bytearray()
        self.av = AVInfo()
        self.shutdown = False
        self.callback_error = None
        self.core = C.CDLL(str(core.resolve()))
        version = getattr(self.core, 'retro_treehouse_capture_version', None)
        self.capture_boundary_version = version() if version else 0
        # Version 2 also synchronizes snapshot operations. The original adapter
        # only held the worker during input/video callbacks, leaving restore
        # dependent on whether the asynchronously resumed frame had finished.
        self.snapshot_boundary_version = 2
        for name, callback_type, callback in [
            ('environment', ENV, self.environment), ('video_refresh', VIDEO, self.video),
            ('audio_sample', AUDIO, self.sound_sample), ('audio_sample_batch', BATCH, self.sound),
            ('input_poll', POLL, self.poll), ('input_state', INPUT, self.input)]:
            def guarded(*args, function=callback):
                try:
                    return function(*args)
                except Exception as error:
                    self.callback_error = error
                    return 0
            cb = callback_type(guarded)
            self.callbacks.append(cb)
            fn = getattr(self.core, 'retro_set_' + name)
            fn.argtypes = [callback_type]
            fn(cb)
        self.core.retro_load_game.argtypes = [C.POINTER(GameInfo)]
        self.core.retro_load_game.restype = C.c_bool
        self.core.retro_serialize_size.restype = C.c_size_t
        for name in ['retro_serialize', 'retro_unserialize']:
            fn = getattr(self.core, name)
            fn.argtypes = [C.c_void_p, C.c_size_t]
            fn.restype = C.c_bool
        self.core.retro_get_memory_size.argtypes = [C.c_uint]
        self.core.retro_get_memory_size.restype = C.c_size_t
        self.core.retro_get_memory_data.argtypes = [C.c_uint]
        self.core.retro_get_memory_data.restype = C.c_void_p
        self.core.retro_init()
        self.before_load()
        self.content_path = str(content.resolve()).encode()
        self.info = GameInfo(self.content_path, None, 0, None)
        if not self.core.retro_load_game(C.byref(self.info)):
            raise RuntimeError('Core refused content')
        self.core.retro_set_controller_port_device.argtypes = [C.c_uint, C.c_uint]
        self.core.retro_set_controller_port_device(0, 3)  # Keyboard; core binds native mouse alongside it.
        self.core.retro_get_system_av_info(C.byref(self.av))

    def before_load(self):
        """Optional offline observer setup while the emulation worker is stopped."""
        pass

    def environment(self, command, data):
        command &= 0xFFFF
        if command in self.paths:
            C.cast(data, C.POINTER(C.c_char_p))[0] = self.paths[command]
            return True
        if command == 3:
            C.cast(data, C.POINTER(C.c_bool))[0] = True
            return True
        if command == 10:
            self.pixel_format = C.cast(data, C.POINTER(C.c_uint))[0]
            return self.pixel_format in (0, 1, 2)
        if command == 12:
            self.keyboard = KEYBOARD(C.cast(data, C.POINTER(C.c_void_p))[0])
            return True
        if command == 15:
            var = C.cast(data, C.POINTER(Variable)).contents
            var.value = self.values.get(var.key)
            return var.value is not None
        if command == 16:
            variables = C.cast(data, C.POINTER(Variable))
            for i in range(256):
                if not variables[i].key: break
                key, desc = variables[i].key, variables[i].value
                if key not in self.values and desc and b'; ' in desc:
                    self.values[key] = desc.split(b'; ',1)[1].split(b'|')[0]
            return True
        if command in (17, 49):
            C.cast(data, C.POINTER(C.c_bool))[0] = False
            return True
        if command in (39, 52):
            C.cast(data, C.POINTER(C.c_uint))[0] = 0
            return True
        if command == 50:
            C.cast(data, C.POINTER(C.c_float))[0] = 60.0
            return True
        if command == 36:
            maps = C.cast(data, C.POINTER(MemoryMap)).contents
            self.memory = [(d.start, d.ptr, d.offset, d.length) for d in maps.descriptors[:maps.count]]
            return True
        if command == 32:
            self.av = AVInfo.from_buffer_copy(C.string_at(data, C.sizeof(AVInfo)))
            return True
        if command == 7:
            self.shutdown = True
            return True
        if command in (18, 11, 37, 35): return True
        return False

    def video(self, data, width, height, pitch):
        if not data or data == C.c_void_p(-1).value: return
        raw = C.string_at(data, height * pitch)
        if self.pixel_format == 1:
            self.frame = Image.frombytes('RGB', (width, height), raw, 'raw', 'BGRX', pitch)
        else:
            import numpy as np
            pixels = np.frombuffer(raw, dtype='<u2').reshape(height, pitch//2)[:, :width].astype('uint32')
            if self.pixel_format == 2:
                rgb = np.stack(((pixels>>11)*255//31, ((pixels>>5)&63)*255//63, (pixels&31)*255//31), axis=2)
            else:
                rgb = np.stack((((pixels>>10)&31)*255//31, ((pixels>>5)&31)*255//31, (pixels&31)*255//31), axis=2)
            self.frame = Image.fromarray(rgb.astype('uint8'))

    def sound(self, data, frames):
        if self.capture_audio: self.audio.extend(C.string_at(data, frames * 4))
        return frames

    def sound_sample(self, left, right):
        if self.capture_audio:
            self.audio.extend(struct.pack('<hh', left, right))

    def poll(self):
        if self.keyboard:
            for event in self.keyboard_events:
                self.keyboard(*event)
        self.keyboard_events.clear()

    def input(self, port, device, index, button):
        return int(button in self.held) if device == 3 else 0

    def key(self, name, down):
        code = KEYS.get(name.lower(), ord(name.lower()) if len(name) == 1 else None)
        if code is None: raise ValueError('Unknown key: ' + name)
        if down: self.held.add(code)
        else: self.held.discard(code)
        self.keyboard_events.append((down, code, code if 32 <= code < 127 else 0, 0))

    def run(self, frames, keys=()):
        for key in keys: self.key(key, True)
        try:
            for _ in range(frames):
                self.core.retro_run()
                if self.callback_error:
                    raise RuntimeError('Libretro callback failed') from self.callback_error
                if self.shutdown:
                    raise RuntimeError('Emulated program requested shutdown')
                self.frame_count += 1
        finally:
            for key in keys: self.key(key, False)

    def save(self, name, ram=False):
        self.snapshot_boundary()
        if self.frame is not None: self.frame.save(self.output / (name + '.png'))
        size = self.core.retro_serialize_size()
        buffer = C.create_string_buffer(size)
        if not self.core.retro_serialize(buffer, size): raise RuntimeError('Save state failed')
        (self.output / (name + '.state')).write_bytes(buffer.raw)
        if ram:
            ptr = self.core.retro_get_memory_data(2)
            size = self.core.retro_get_memory_size(2)
            if ptr and size: (self.output / (name + '.ram')).write_bytes(C.string_at(ptr, size))
            for start, ptr, offset, length in self.memory:
                if ptr and start in (0, 0x100000):
                    (self.output / (name + f'.ram-{start:x}')).write_bytes(C.string_at(ptr + offset, length))

    def restore(self, path):
        data = path.read_bytes()
        buf = C.create_string_buffer(data)
        self.snapshot_boundary()
        if not self.core.retro_unserialize(buf, len(data)): raise RuntimeError('State restore failed')

    def snapshot_boundary(self):
        # In the pinned core, this public API calls TCM_FINISH_FRAME without
        # resuming the worker. Serialize/unserialize then sees a completed
        # frame rather than interrupting and resuming a partially executed one.
        self.core.retro_get_system_av_info(C.byref(self.av))

    def close(self):
        if self.capture_audio:
            with wave.open(str(self.output/'audio.wav'), 'wb') as f:
                f.setnchannels(2); f.setsampwidth(2); f.setframerate(round(self.av.timing.sample_rate))
                f.writeframes(self.audio)
        self.core.retro_unload_game()
        self.core.retro_deinit()

