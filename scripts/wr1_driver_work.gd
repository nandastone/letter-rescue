extends RefCounted
## Recovered AdLib control flow. Static spans retain instruction boundaries;
## current voice state chooses their order. No binary interpreter or trace input.

var instructions: Dictionary
var rhythm_writes: int
var state: Dictionary
var timeline: Array
var kind: int
var channel: int
var velocity: int
var note_value: int

func configure() -> void:
	instructions = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_work.json")).instructions
	rhythm_writes = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_tables.json")).rhythm_registers.size()

func _span(start: int, end: int) -> void:
	while start <= end:
		var instruction: Array = instructions[str(start)]
		timeline.append([instruction[0], start])
		start = int(instruction[1])

func _opl() -> void:
	timeline.append(["opl", 0x579e])

func instrument_work() -> Array:
	timeline = []
	_instrument()
	return timeline

func _instrument() -> void:
	for pair in [[0x56d9, 0x56fb], [0x56fe, 0x570a], [0x570d, 0x5719],
			[0x571c, 0x572d], [0x5730, 0x573c], [0x573f, 0x574b],
			[0x574e, 0x575a], [0x575d, 0x5769], [0x576c, 0x5778],
			[0x577b, 0x5787], [0x578a, 0x5795]]:
		_span(pair[0], pair[1])
		_opl()
	_span(0x5798, 0x579d)

func _frequency() -> void:
	_span(0x5b55, 0x5b94)
	var bend: int = state.bends[channel]
	if bend:
		_span(0x5b96, 0x5b9f)
		if bend >= 128:
			_span(0x5ba1, 0x5ba1)
		_span(0x5ba2, 0x5baf)
		if bend == 128:
			_span(0x5bb1, 0x5bb5)
		else:
			_span(0x5bb8, 0x5bbc)
	_span(0x5bbe, 0x5bc8)
	_opl()
	_span(0x5bcb, 0x5bdf)
	var on := kind != 128
	if on:
		_span(0x5be1, 0x5be7)
		on = velocity != 0
		if on:
			_span(0x5be9, 0x5bef)
			if state.rhythm & 32:
				_span(0x5bf1, 0x5bf7)
				on = channel < 11
	if on:
		_span(0x5bf9, 0x5bf9)
	_span(0x5bfc, 0x5c00)
	_opl()
	_span(0x5c03, 0x5c26)
	if state.volumes[channel] >= 96:
		_span(0x5c28, 0x5c28)
	_span(0x5c2a, 0x5c50)
	_opl()
	_span(0x5c53, 0x5c56)

func _note() -> void:
	var count := 9
	_span(0x59f7, 0x5a0c)
	if state.rhythm & 32:
		count = 6
		_span(0x5a0e, 0x5a1b)
		var drum: bool = state.percussion == 1 and channel == 9
		if state.percussion == 1:
			_span(0x5a1d, 0x5a23)
		if drum:
			_span(0x5a4b, 0x5a66)
			_opl()
			_span(0x5a69, 0x5a69)
			_span(0x5b54, 0x5b54)
			return
		_span(0x5a25, 0x5a2b)
		if channel >= 11:
			_span(0x5a2d, 0x5a45)
			_opl()
			_span(0x5a48, 0x5a48)
			_span(0x5b54, 0x5b54)
			return
	_span(0x5a6c, 0x5a72)
	if kind > 128:
		_span(0x5ab0, 0x5ab6)
	if kind <= 128 or velocity == 0:
		_span(0x5a74, 0x5a7b)
		for voice in range(count):
			_span(0x5a7e, 0x5a89)
			if state.voices[voice] >> 8 == channel:
				_span(0x5a91, 0x5a9b)
				if state.notes[voice] == note_value:
					_span(0x5aa2, 0x5aa7)
					_frequency()
					_span(0x5aaa, 0x5aad)
					_span(0x5b54, 0x5b54)
					return
				_span(0x5a9d, 0x5aa0)
			_span(0x5a8b, 0x5a8c)
		_span(0x5a8e, 0x5a8e)
		_span(0x5b54, 0x5b54)
		return
	# Preserve the native search path, including a channel-scan restart after
	# finding a busy candidate in the unassigned pass.
	var voices: Array = state.voices.duplicate()
	for retry in range(2):
		_span(0x5ab8, 0x5aba)
		var voice := 0
		var phase := 0
		var found := false
		var iterations := 0
		while true:
			iterations += 1
			assert(iterations <= 100, "Unbounded voice search")
			if phase == 0:
				_span(0x5abd, 0x5ac3)
			else:
				_span(0x5ad2, 0x5ad6)
			var matched: bool = voices[voice] >> 8 == (channel if phase == 0 else 255)
			if matched:
				_span(0x5b00, 0x5b0a)
				if not state.notes[voice]:
					found = true
					break
				_span(0x5b0c, 0x5b12)
				voice += 1
				if voice < count:
					phase = 0
					continue
				_span(0x5b14, 0x5b14)
			else:
				if phase == 0:
					_span(0x5ac5, 0x5acb)
				else:
					_span(0x5ad8, 0x5ade)
				voice += 1
				if voice < count:
					continue
				if phase == 1:
					break
			_span(0x5acd, 0x5acf)
			voice = 0
			phase = 1
		if found:
			_span(0x5b16, 0x5b2f)
			if voices[voice] & 255 != state.programs[channel]:
				_span(0x5b31, 0x5b4d)
				_instrument()
			_span(0x5b50, 0x5b50)
			_frequency()
			_span(0x5b53, 0x5b53)
			return
		_span(0x5ae0, 0x5ae0)
		var recycled := false
		for candidate in range(count):
			_span(0x5ae2, 0x5ae8)
			if not state.notes[candidate]:
				_span(0x5af5, 0x5afe)
				voices[candidate] = 65535
				_span(0x5ab0, 0x5ab6)
				recycled = true
				break
			_span(0x5aea, 0x5af0)
		if not recycled:
			_span(0x5af2, 0x5af2)
			_span(0x5b54, 0x5b54)
			return
	assert(false, "Voice recycling did not terminate")

func _control(controller: int, value: int) -> void:
	_span(0x582d, 0x5835)
	if controller == 123:
		_span(0x5837, 0x5837)
		_span(0x57c4, 0x57ca)
		_span(0x57e9, 0x57ef)
		_span(0x57f7, 0x57fa)
		for voice in range(9):
			_span(0x57fc, 0x5808)
			if state.voices[voice] >> 8 == channel:
				_span(0x580a, 0x5810)
				_opl()
				_span(0x5813, 0x5819)
				_opl()
				_span(0x581c, 0x5823)
			_span(0x5825, 0x5829)
		_span(0x582b, 0x582c)
		_span(0x583a, 0x583a)
		_span(0x58f0, 0x58f0)
		return
	_span(0x583d, 0x5840)
	if controller == 7:
		_span(0x5842, 0x584b)
	else:
		_span(0x584e, 0x5851)
		if controller == 103:
			_span(0x5853, 0x5856)
			if value == 0:
				_span(0x5860, 0x586f)
				_opl()
				_span(0x5872, 0x5884)
			else:
				_span(0x5858, 0x585b)
				if value == 1:
					_span(0x5887, 0x5896)
					_opl()
					_span(0x5899, 0x58a8)
					for i in range(rhythm_writes):
						_span(0x58ab, 0x58b1)
						_span(0x58b3, 0x58b3)
						_opl()
						_span(0x58b6, 0x58b6)
					_span(0x58ab, 0x58b1)
					_span(0x58b8, 0x58bb)
					_opl()
					_span(0x58be, 0x58c1)
					_opl()
					_span(0x58c4, 0x58ca)
				else:
					_span(0x585d, 0x585d)
		else:
			_span(0x58cd, 0x58d0)
			if controller != 105:
				_span(0x58d2, 0x58d5)
			if controller in [104, 105]:
				_span(0x58da, 0x58e9)
				_span(0x58ee, 0x58ee)
			else:
				_span(0x58d7, 0x58d7)
	_span(0x58f0, 0x58f0)

func event(midi: Dictionary, voice_state: Dictionary) -> Array:
	assert(voice_state.mode == 1, "Work model supports AdLib mode only")
	state = voice_state
	timeline = []
	kind = int(midi.status) & 240
	channel = int(midi.status) & 15
	var data: Array = midi.data + [0, 0]
	velocity = int(data[1])
	note_value = int(data[0])
	_span(0x58f1, 0x58f7)
	_span(0x592b, 0x594c)
	if kind > 144:
		_span(0x594e, 0x5954)
		if kind <= 176:
			_span(0x5956, 0x5956)
			_control(data[0], data[1])
			_span(0x5959, 0x5959)
		else:
			_span(0x595c, 0x5962)
			if kind <= 192:
				_span(0x5964, 0x5964)
				_span(0x5cc4, 0x5ccd)
				if state.rhythm & 32:
					_span(0x5ccf, 0x5cd5)
				_span(0x5cd7, 0x5cea)
				_span(0x5967, 0x5967)
	else:
		_span(0x596a, 0x5970)
		var transpose := true
		if state.rhythm & 32:
			_span(0x5972, 0x5978)
			if state.percussion == 1:
				_span(0x597a, 0x5980)
				transpose = channel != 9
				if transpose:
					_span(0x5982, 0x5982)
			else:
				_span(0x5985, 0x598b)
				transpose = channel < 11
		if transpose:
			_span(0x598d, 0x5996)
			note_value = (note_value + int(state.transpose)) & 255
		_span(0x599a, 0x599a)
		_note()
	_span(0x599d, 0x599e)
	return timeline
