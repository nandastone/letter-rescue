extends RefCounted
## WR1.EXE1ec59..1f26a: original MIDI voice allocation and AdLib register output.
## Pure register generation. Synthesis and emulated IO duration are separate.

var tables: Dictionary
var state: Dictionary
var instruments: Array = []
var writes: Array = []

func configure(cmf: PackedByteArray, initial: Dictionary) -> void:
	tables = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_tables.json"))
	state = _integers(initial)
	instruments = tables.default_instruments.duplicate(true)
	var offset := cmf.decode_u16(6)
	for i in range(cmf.decode_u16(36)):
		instruments[i] = Array(cmf.slice(offset + 16 * i, offset + 16 * i + 11))

func _integers(value: Variant) -> Variant:
	if value is Dictionary:
		var result := {}
		for key in value:
			result[key] = _integers(value[key])
		return result
	if value is Array:
		var result := []
		for item in value:
			result.append(_integers(item))
		return result
	return int(value)

func _write(register: int, value: int) -> void:
	writes.append([register & 255, value & 255])

func _instrument(voice: int, program: int) -> void:
	var values: Array = instruments[program]
	var modulator := int(tables.modulators[voice])
	var carrier := int(tables.carriers[voice])
	var bases := [0x20, 0x40, 0x60, 0x80, 0xe0]
	for i in range(5):
		_write(bases[i] + modulator, int(values[2 * i]))
		_write(bases[i] + carrier, int(values[2 * i + 1]))
	state.levels[voice] = int(values[3])
	_write(0xc0 + voice, int(values[10]))

func _frequency(voice: int, channel: int, note: int, on: bool) -> void:
	state.notes[voice] = note
	var adjusted := (note - 1) & 255
	@warning_ignore("integer_division")
	var octave := adjusted / 12
	var key := adjusted % 12
	var frequency := int(tables.frequencies[key])
	var bend: int = state.bends[channel]
	if bend:
		var step := int(tables.bend_steps[key + int(bend >= 128)])
		var delta := ((bend * step * 2) & 65535) >> 8
		frequency = (frequency + (delta if bend == 128 else -delta)) & 65535
	_write(0xa0 + voice, frequency & 255)
	var block := (octave * 4) & 255
	if on and not (state.rhythm & 32 and channel >= 11):
		block |= 32
	_write(0xb0 + voice, block | ((frequency >> 8) & 3))
	var level: int = state.levels[voice]
	var scale := ((mini(state.volumes[channel], 95) + 32) * 2) & 255
	var attenuation := (63 - ((((63 - (level & 63)) * scale) >> 8) + 1)) & 255
	_write(0x40 + int(tables.carriers[voice]), (level & 192) | attenuation)

func restart() -> Array:
	# CMF repeat preserves channel volume and percussion type (EXE1f1e9).
	writes = []
	state.rhythm = 192
	_write(0xbd, 192)
	for voice in range(9):
		_instrument(voice, 0)
	state.programs.fill(0)
	state.bends.fill(0)
	state.notes.fill(0)
	state.voices.fill(65535)
	return writes

func _note(channel: int, note: int, on: bool) -> void:
	var count := 6 if state.rhythm & 32 else 9
	if state.rhythm & 32 and ((state.percussion == 1 and channel == 9) or channel >= 11):
		var mask := int(tables.percussion[(note - 35) & 255]) if state.percussion == 1 and channel == 9 else 16 >> (channel - 11)
		state.rhythm ^= mask
		_write(0xbd, state.rhythm)
		return
	if not on:
		for voice in range(count):
			if state.voices[voice] >> 8 == channel and state.notes[voice] == note:
				_frequency(voice, channel, note, false)
				state.notes[voice] = 0
				return
		return
	var voice := -1
	for i in range(count):
		if state.voices[i] >> 8 == channel and not state.notes[i]:
			voice = i
			break
	if voice < 0:
		for i in range(count):
			if state.voices[i] >> 8 == 255 and not state.notes[i]:
				voice = i
				break
	if voice < 0:
		for i in range(count):
			if not state.notes[i]:
				voice = i
				state.voices[i] = 65535
				break
	if voice < 0:
		return
	var program: int = state.programs[channel]
	if state.voices[voice] & 255 != program:
		state.voices[voice] = (channel << 8) | program
		_instrument(voice, program)
	_frequency(voice, channel, note, true)

func _control(channel: int, controller: int, value: int) -> void:
	match controller:
		7:
			state.volumes[channel] = value
		104, 105:
			# Original BH is cleared before its 68h comparison (EXE1ee5a).
			state.bends[channel] = value
		103:
			if value not in [0, 1]:
				return
			state.rhythm = 192 if value == 0 else 224
			state.percussion = value
			_write(0xbd, state.rhythm)
			for i in range(6, 9):
				state.voices[i] = 65535 if value == 0 else 4351
			if value:
				for pair in tables.rhythm_registers:
					_write(int(pair[0]), int(pair[1]))
				_write(0xbd, 224)
				_write(8, 0)
		123:
			# Loop target 57fc reloads the table base on each iteration.
			for voice in range(9):
				if state.voices[voice] >> 8 == channel:
					_write(0xa0 + voice, 0)
					_write(0xb0 + voice, 0)
					state.notes[voice] = 0

func event(midi: Dictionary) -> Array:
	writes = []
	assert(state.mode == 1, "Only the observed AdLib mode is implemented")
	var status := int(midi.status)
	var kind := status & 240
	var channel := status & 15
	if kind in [128, 144]:
		var note := int(midi.data[0])
		var percussion: bool = bool(state.rhythm & 32) and ((state.percussion == 1 and channel == 9) or channel >= 11)
		if not percussion:
			note = (note + state.transpose) & 255
		_note(channel, note, kind == 144 and int(midi.data[1]) != 0)
	elif kind in [160, 176]:
		_control(channel, int(midi.data[0]), int(midi.data[1]))
	elif kind == 192:
		state.programs[channel] = int(midi.data[0])
	return writes

func snapshot() -> Dictionary:
	return state.duplicate(true)
