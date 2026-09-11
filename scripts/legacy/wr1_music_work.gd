extends RefCounted
## Live CMF/voice state -> complete INT 63h instruction work and register writes.
## Repeat is modeled with the game's external timer mode. PIT reprogramming
## remains an explicit unsupported path.

var instructions: Dictionary
var driver = preload("res://scripts/legacy/wr1_driver_work.gd").new()
var dispatcher_use_dx: bool
var external_timer: int
var timeline: Array
var writes: Array
var events: Array

func configure(use_dx: bool, timer_owner: int = -1) -> void:
	instructions = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_work.json")).instructions
	driver.configure()
	dispatcher_use_dx = use_dx
	external_timer = timer_owner

func _span(start: int, end: int) -> void:
	while start <= end:
		var instruction: Array = instructions[str(start)]
		timeline.append([instruction[0], start])
		start = int(instruction[1])

func _file_span(start: int, end: int) -> void:
	_span(start - 0x19580, end - 0x19580)

func _delay(music, cursor: int) -> Array[int]:
	_file_span(0x1f824, 0x1f828)
	var delay := 0
	while true:
		var byte: int = music.byte(cursor)
		cursor = (cursor + 1) & 65535
		delay = ((delay << 7) | (byte & 127)) & 0xffffffff
		_file_span(0x1f82a, 0x1f838)
		if byte < 128:
			break
		_file_span(0x1f83a, 0x1f856)
	_file_span(0x1f858, 0x1f85a)
	return [delay, cursor]

func _repeat_memory(address: int, count: int) -> void:
	timeline.append(["rep:%d" % count, address - 0x19580])

func _reset_voices(opl) -> void:
	_file_span(0x1f1e9, 0x1f1f5)
	timeline.append(["opl", 0x579e])
	_file_span(0x1f1f8, 0x1f1fa)
	for i in range(9):
		_file_span(0x1f1fc, 0x1f1fc)
		timeline.append_array(driver.instrument_work())
		_file_span(0x1f1ff, 0x1f204)
	for item in [[0x1f206, 0x1f20f, 0x1f212, 16],
			[0x1f214, 0x1f21d, 0x1f220, 16],
			[0x1f222, 0x1f227, 0x1f22a, 9],
			[0x1f22c, 0x1f232, 0x1f235, 9]]:
		_file_span(item[0], item[1])
		_repeat_memory(item[2], item[3])
	_file_span(0x1f237, 0x1f23a)
	writes.append_array(opl.restart())

func _restart(music, opl) -> void:
	assert(external_timer == 1, "CMF timer programming requires observed external-timer mode 1")
	assert(music.state.data_offset >= 0 and music.state.data_offset < 16, "Expected normalized CMF segment offset")
	_file_span(0x1f56b, 0x1f56e)
	_file_span(0x1f85b, 0x1f88f)
	_file_span(0x1f571, 0x1f583)
	_reset_voices(opl)
	_file_span(0x1f586, 0x1f594)
	_file_span(0x1f596, 0x1f59a)
	_file_span(0x1f59c, 0x1f5a8)
	_repeat_memory(0x1f5aa, 32)
	_file_span(0x1f5ac, 0x1f5d6)
	_file_span(0x1f890, 0x1f898)
	_file_span(0x1f5d9, 0x1f602)
	var instruments: int = music.data.decode_u16(36)
	for i in range(instruments):
		_file_span(0x1f604, 0x1f605)
		_repeat_memory(0x1f608, 11)
		_file_span(0x1f60a, 0x1f60e)
		if i + 1 < instruments:
			_file_span(0x1f602, 0x1f602)
	_file_span(0x1f610, 0x1f618)
	_delay(music, (int(music.state.data_offset) + int(music.data.decode_u16(8))) & 65535)
	_file_span(0x1f61b, 0x1f637)
	_file_span(0x1f63a, 0x1f653)

func _track_end(music, opl) -> void:
	var s: Dictionary = music.state
	assert(s.tracks.size() == 1, "Work for ending one of several active tracks is not recovered")
	_file_span(0x1f7a6, 0x1f7bb)
	_file_span(0x1f7c0, 0x1f7ca)
	_file_span(0x1f7cc, 0x1f7cc)
	_file_span(0x1f7d7, 0x1f7dd)
	if s.repeat:
		_file_span(0x1f7df, 0x1f7f0)
		_file_span(0x1f7f6, 0x1f7f6)
		_restart(music, opl)
		_file_span(0x1f7f9, 0x1f7f9)
	else:
		_file_span(0x1f7fa, 0x1f800)

func _finish(music) -> Dictionary:
	_span(0x5103, 0x5103)
	_span(0x5108, 0x510e)
	assert(music.tick() == events, "Work planner and sequencer disagree")
	return {"work":timeline, "writes":writes}

func tick(music, opl) -> Dictionary:
	timeline = [["mov", 0x2d8], ["int", 0x2da]]
	writes = []
	events = []
	_span(0x50d9, 0x50ea)
	if dispatcher_use_dx:
		_span(0x50ec, 0x50ec)
	_span(0x50ee, 0x5101)
	var s: Dictionary = music.state
	_file_span(0x1f65a, 0x1f664)
	if not s.playing:
		_file_span(0x1f666, 0x1f666)
	else:
		_file_span(0x1f667, 0x1f675)
		if ((int(s.counter) + 1) & 65535) >= s.division:
			_file_span(0x1f677, 0x1f67e)
		_file_span(0x1f683, 0x1f683)
		for track in s.tracks:
			_file_span(0x1f68a, 0x1f694)
			_file_span(0x1f697, 0x1f6a4)
			if not track.active:
				_file_span(0x1f6a6, 0x1f6ab)
				continue
			_file_span(0x1f6ad, 0x1f6c2)
			var delay: int = track.delay
			if (((delay & 65535) + (delay >> 16)) & 65535) > 1:
				_file_span(0x1f6c4, 0x1f6d0)
				continue
			_file_span(0x1f6d2, 0x1f6e2)
			var cursor: int = track.cursor
			var status: int = track.status
			while true:
				_file_span(0x1f6e4, 0x1f6ea)
				var byte: int = music.byte(cursor)
				cursor = (cursor + 1) & 65535
				if byte == 255:
					_file_span(0x1f763, 0x1f769)
					var kind: int = music.byte(cursor)
					cursor = (cursor + 1) & 65535
					if kind == 47:
						_track_end(music, opl)
						return _finish(music)
					_file_span(0x1f76b, 0x1f76d)
					assert(kind != 81, "Tempo-port programming needs its own IO model")
					_file_span(0x1f76f, 0x1f777)
					var size: int = music.byte(cursor)
					cursor = (cursor + 1) & 65535
					var payload := []
					for i in range(size):
						payload.append(music.byte((cursor + i) & 65535))
					events.append({"status":255, "kind":kind, "data":payload})
					cursor = (cursor + size) & 65535
				else:
					_file_span(0x1f6ec, 0x1f6ee)
					if byte < 128:
						cursor = (cursor - 1) & 65535
						_file_span(0x1f6f0, 0x1f6f1)
						_file_span(0x1f703, 0x1f70e)
					else:
						status = byte
						_file_span(0x1f6f4, 0x1f700)
					_file_span(0x1f70f, 0x1f725)
					var size: int = [2, 2, 2, 2, 1, 1, 2, 0][(status >> 4) - 8]
					var payload := []
					if size:
						_file_span(0x1f727, 0x1f72d)
						payload.append(music.byte(cursor))
						cursor = (cursor + 1) & 65535
						if size > 1:
							_file_span(0x1f72f, 0x1f732)
							payload.append(music.byte(cursor))
							cursor = (cursor + 1) & 65535
					var midi := {"status":status, "data":payload}
					events.append(midi)
					_file_span(0x1f733, 0x1f733)
					timeline.append_array(driver.event(midi, opl.state))
					timeline.append(["ret", 0x599f])
					writes.append_array(opl.event(midi))
				_file_span(0x1f736, 0x1f736)
				var decoded := _delay(music, cursor)
				delay = decoded[0]
				cursor = decoded[1]
				_file_span(0x1f739, 0x1f73c)
				if not delay & 65535:
					_file_span(0x1f73e, 0x1f741)
				if delay:
					break
			_file_span(0x1f743, 0x1f760)
		_file_span(0x1f68a, 0x1f696)
	return _finish(music)
