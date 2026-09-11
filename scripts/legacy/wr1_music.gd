extends RefCounted
## CMF sequencing from WR1.EXE1f56b..1f858. One tick per IRQ0; emits MIDI events.
## Register synthesis and instruction timing live in separate original-driver models.
const FIELDS := ["counter", "beats", "division", "format", "repeat", "playing", "data_offset"]
const PARAMETERS := [2, 2, 2, 2, 1, 1, 2, 0]
var data: PackedByteArray
var state: Dictionary = {}
var restarted := false

func configure(stream: PackedByteArray, initial: Dictionary) -> void:
	restarted = false
	data = stream
	assert(data.slice(0, 4).get_string_from_ascii() == "CTMF")
	assert(int(initial.format) == 1)
	for key in FIELDS:
		state[key] = int(initial[key])
	state.tracks = []
	for source in initial.tracks:
		var track := {}
		for key in ["active", "delay", "cursor", "status"]:
			track[key] = int(source[key])
		state.tracks.append(track)

func byte(cursor: int) -> int:
	return data[(cursor - state.data_offset) & 0xffff]

func _vlq(cursor: int) -> Array[int]:
	var value := 0
	while true:
		var byte := byte(cursor)
		cursor = (cursor + 1) & 0xffff
		value = ((value << 7) | (byte & 127)) & 0xffffffff
		if byte < 128:
			return [value, cursor]
	return []

func _restart() -> void:
	restarted = true
	state.counter = 0
	state.beats = 0
	state.division = data.decode_u16(10)
	var delay := _vlq((state.data_offset + data.decode_u16(8)) & 0xffff)
	# Native initialization clears active slots, but preserves running status.
	var status: int = state.tracks[0].status if not state.tracks.is_empty() else 0
	state.tracks = [{"active":1, "delay":delay[0], "cursor":delay[1], "status":status}]
	state.playing = 1

func tick() -> Array[Dictionary]:
	restarted = false
	var events: Array[Dictionary] = []
	if not state.playing:
		return events
	state.counter = (state.counter + 1) & 0xffff
	if state.counter >= state.division:
		state.counter = 0
		state.beats = (state.beats + 1) & 0xffff
	for track in state.tracks:
		if not track.active:
			continue
		var delay: int = track.delay
		if (((delay & 0xffff) + (delay >> 16)) & 0xffff) > 1:
			track.delay = (delay - 1) & 0xffffffff
			continue
		var cursor: int = track.cursor
		while true:
			var status := byte(cursor)
			cursor = (cursor + 1) & 0xffff
			if status == 255:
				var kind := byte(cursor)
				cursor = (cursor + 1) & 0xffff
				if kind == 47:
					track.active = 0
					var active := false
					for other in state.tracks:
						active = active or bool(other.active)
					if not active:
						if state.repeat:
							_restart()
						else:
							state.playing = 0
						return events
					break
				var size := byte(cursor)
				cursor = (cursor + 1) & 0xffff
				var payload: Array[int] = []
				for i in range(size):
					payload.append(byte((cursor + i) & 0xffff))
				events.append({"status":255, "kind":kind, "data":payload})
				cursor = (cursor + size) & 0xffff
			else:
				if status < 128:
					cursor = (cursor - 1) & 0xffff
					status = track.status
				else:
					track.status = status
				var size: int = PARAMETERS[(status >> 4) - 8]
				var payload: Array[int] = []
				for i in range(size):
					payload.append(byte((cursor + i) & 0xffff))
				events.append({"status":status, "data":payload})
				cursor = (cursor + size) & 0xffff
			var next := _vlq(cursor)
			delay = next[0]
			cursor = next[1]
			if delay:
				track.delay = delay
				track.cursor = cursor
				break
	return events

func snapshot() -> Dictionary:
	return state.duplicate(true)
