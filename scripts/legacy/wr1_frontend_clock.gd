extends RefCounted
## DOSBox Pure hands off at the next TIMER_AddTick after VGA drawing ends.
## CPU polling blocks can carry a callback across that boundary. Simulate the
## recovered idle path and IRQ work instead of rounding an ideal callback time.
var hardware: RefCounted
var idle: RefCounted
var dispatch: Array
var previous_ms: float

func configure(checkpoint: Dictionary) -> void:
	var clock = preload("res://scripts/legacy/wr1_music_clock.gd").new()
	clock.configure(checkpoint)
	idle = clock.idle
	hardware = idle.hardware
	dispatch = clock.dispatch
	hardware.record_video_completions = true
	previous_ms = round(float(checkpoint.initial.pic_ms))

func next_seconds() -> float:
	while hardware.video_handoffs.is_empty():
		if hardware.pending == 0:
			if hardware.cycles <= 0:
				hardware.begin_block()
			if hardware.interrupts.irq_check:
				idle._interrupt()
				continue
		if idle.pc == 0x371b and int(idle.game.timer) >= 8:
			hardware.run_driver(dispatch)
			idle.game.timer = 0
			idle.pc = 0x40d2
			continue
		if idle.pc == 0x34ba and hardware.pending == 0 and int(idle.game.timer) < 8:
			@warning_ignore("integer_division")
			var loops: int = (hardware.cycles - 1) / idle.loop_cost
			if loops > 0:
				hardware.cycles -= loops * idle.loop_cost
				idle.ax = int(idle.game.timer)
				idle.carry = true
				idle.zero = false
		var op: String = idle._instruction()
		hardware.pending += 1
		if op.begins_with("j") or hardware.pending == 32:
			hardware.end_block(hardware.pending)
			hardware.pending = 0
	var target: float = hardware.video_handoffs.pop_front()
	hardware.video_completions.pop_front()
	var seconds: float = (target - previous_ms) / 1000.0
	previous_ms = target
	return seconds
