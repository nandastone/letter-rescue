extends RefCounted
## Game timer, PC-speaker sequence, music and DOSBox BIOS chaining, before IRET.
const STATE_FIELDS := ["timer", "speaker_index", "speaker_elapsed", "bios_countdown", "bios_reload", "bios_ticks"]
var instructions: Dictionary
var music_work = preload("res://scripts/legacy/wr1_music_work.gd").new()
var timeline: Array
var state: Dictionary

func configure(driver_mode: bool, timer_mode: int) -> void:
	instructions = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_work.json")).irq_instructions
	music_work.configure(driver_mode, timer_mode)

func _span(start: int, end: int) -> void:
	while start <= end:
		var instruction: Array = instructions[str(start)]
		timeline.append(["eoi" if start == 0x308 else instruction[0], start])
		start = int(instruction[1])

func _signed16(value: int) -> int:
	return ((value + 32768) & 65535) - 32768

func _speaker(initial: Dictionary) -> void:
	_span(0x232, 0x245)
	state.timer = _signed16(state.timer + 1)
	state.speaker_elapsed = (state.speaker_elapsed + 1) & 0xffffffff
	if state.speaker_index < 0:
		_span(0x247, 0x247)
		return
	_span(0x24a, 0x260)
	var duration := int(initial.speaker_entry[1]) & 65535
	var high := 65535 if duration & 32768 else 0
	if high > state.speaker_elapsed >> 16:
		_span(0x262, 0x262)
		return
	_span(0x265, 0x265)
	if high == state.speaker_elapsed >> 16:
		_span(0x267, 0x26b)
		if duration > (state.speaker_elapsed & 65535):
			_span(0x26d, 0x26d)
			return
	_span(0x270, 0x297)
	state.speaker_elapsed = 0
	state.speaker_index = _signed16(state.speaker_index + 1)
	if initial.speaker_next[1] == 0:
		_span(0x299, 0x2a6)
		state.speaker_index = -1
	else:
		_span(0x2a8, 0x2d6)

func _bios(initial: Dictionary) -> void:
	var code := PackedByteArray(initial.bios_code)
	var user := PackedByteArray(initial.int1c_code)
	assert(code.slice(0, 3) == PackedByteArray([0xfb, 0xfe, 0x38]) and code.slice(5) == PackedByteArray([0x1e, 0x50, 0x52, 0xcd, 0x1c, 0xfa, 0xb0, 0x20, 0xe6, 0x20, 0x5a, 0x58, 0x1f, 0xcf]), "Unrecognized BIOS IRQ0 template")
	assert(user.slice(0, 2) == PackedByteArray([0xfe, 0x38]) and user[4] == 0xcf, "Unrecognized INT 1Ch template")
	var vector: int = initial.bios_handler
	var base := ((vector >> 16) << 4) + (vector & 65535)
	for pair in [["sti", 0], ["callback", 1], ["push", 5], ["push", 6], ["push", 7], ["int", 8]]:
		timeline.append([pair[0], base + int(pair[1])])
	vector = int(initial.int1c_handler)
	var user_base := ((vector >> 16) << 4) + (vector & 65535)
	timeline.append_array([["callback", user_base], ["iret", user_base + 4]])
	for pair in [["cli", 10], ["mov", 11], ["eoi", 13], ["pop", 15], ["pop", 16], ["pop", 17], ["iret", 18]]:
		timeline.append([pair[0], base + int(pair[1])])
	state.bios_ticks = (state.bios_ticks + 1) & 0xffffffff
	if state.bios_ticks >= 0x1800b0:
		state.bios_ticks = 0

func body(music, opl, initial: Dictionary) -> Dictionary:
	timeline = []
	state = {}
	for key in STATE_FIELDS:
		state[key] = int(initial[key])
	_speaker(initial)
	var result: Dictionary = music_work.tick(music, opl)
	timeline.append_array(result.work)
	_span(0x2dc, 0x2ef)
	state.bios_countdown = (state.bios_countdown - 1) & 0xffffffff
	if state.bios_countdown:
		_span(0x306, 0x308)
	else:
		state.bios_countdown = state.bios_reload
		_span(0x2f1, 0x300)
		_bios(initial)
		_span(0x304, 0x304)
	_span(0x30a, 0x312)
	return {"work":timeline, "writes":result.writes, "state":state}
