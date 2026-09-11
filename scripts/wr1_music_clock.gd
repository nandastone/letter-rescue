extends RefCounted
## Continuous IRQ/music service from one post-load hardware checkpoint.
## Main work is instantaneous here; instruction-level drawing remains separate.
var idle = preload("res://scripts/wr1_idle_clock.gd").new()
var origin_ms: float
var now_ms: float
var admissions: Array[Dictionary] = []
var dispatch: Array = []
var pending_admission: Dictionary = {}

func configure(checkpoint: Dictionary) -> void:
	var bytes := FileAccess.get_file_as_bytes(checkpoint.music_file)
	assert(FileAccess.get_sha256(checkpoint.music_file) == checkpoint.music_sha256)
	assert(bytes.slice(0, 16) == PackedByteArray(checkpoint.initial.music_driver.prefix), "CMF asset disagrees with initial native header")
	idle.configure(bytes, checkpoint.initial, checkpoint.event_names)
	origin_ms = float(checkpoint.initial.pic_ms)
	now_ms = origin_ms
	# The admitted demo reads its five controls before the 37A4 observation.
	# Recover the executed instruction path, including the stop/key tests.
	for span in [[0x371b, 0x3740], [0x374a, 0x37a1]]:
		var pc: int = span[0]
		while pc <= int(span[1]):
			var instruction: Array = idle.instructions[str(pc)]
			if pc != 0x3724: # Taken JAE skips the idle back-edge.
				dispatch.append([instruction[0], pc])
			pc = int(instruction[1])

func resume_main(remaining_seconds: float) -> Dictionary:
	var at: float = (now_ms - origin_ms) / 1000.0 - remaining_seconds
	# The last recap draw leaves its eight-tick gate ready. The next ordinary
	# admission resets it; retain only interrupts serviced after that admission.
	idle.game.timer = 0
	var resumed_ms: float = now_ms - remaining_seconds * 1000.0
	for index in range(idle.entries.size() - 1, -1, -1):
		if float(idle.entries[index].return_ms) <= resumed_ms:
			break
		if float(idle.entries[index].return_ms) <= now_ms:
			idle.game.timer += 1
	return {"at":at, "timer":8}

func advance(seconds: float, admit: bool = true) -> Array[Dictionary]:
	now_ms += seconds * 1000.0
	admissions = []
	var hardware = idle.hardware
	if not pending_admission.is_empty() and pending_admission.at < (now_ms - origin_ms) / 1000.0:
		admissions.append(pending_admission)
		pending_admission = {}
	# Handoff occurs before work in the following millisecond budget. An
	# admission exactly on the boundary belongs to the next frontend interval.
	while hardware.observed_time() < now_ms:
		# Service all pending interrupts before returning control to the game.
		# The PIC stores one pending bit: repeated edges during a long music
		# reset coalesce, and the main gate then clears its whole timer count.
		if hardware.interrupts.irq_check:
			idle._interrupt()
			continue
		if admit and int(idle.game.timer) >= 8:
			hardware.run_driver(dispatch)
			var admission := {"at":(hardware.observed_time() - origin_ms) / 1000.0,
				"timer":int(idle.game.timer)}
			idle.game.timer = 0
			if hardware.observed_time() >= now_ms:
				pending_admission = admission
				break
			admissions.append(admission)
		if hardware.observed_time() >= now_ms - 0.0000001:
			break
		if hardware.cycles <= 0:
			hardware.begin_block()
			continue
		var remaining := maxi(1, int(ceil((now_ms - hardware.observed_time()) * 27000.0)))
		hardware.end_block(mini(hardware.cycles, remaining))
	return admissions
