extends RefCounted
## Continuous ordinary idle polling and IRQ0/IRQ1 delivery from one checkpoint.
## Changed keys use external delivery times; menus, repeats and rendering remain boundaries.
const COMPARE_FLAGS := {0x34ba:"0178", 0x3580:"019a", 0x3598:"01a0", 0x35ab:"01b2",
	0x35d3:"01b0", 0x35f4:"018c", 0x363a:"0198", 0x3657:"01ae", 0x366a:"01a4",
	0x3671:"01a6", 0x36d2:"01ac", 0x3727:"0146"}
const IDLE_NODES := [0x34bf, 0x34c1, 0x3585, 0x359d, 0x35b0, 0x35d8, 0x35f9,
	0x363f, 0x365c, 0x366f, 0x3676, 0x36d7, 0x371b, 0x371e, 0x3722, 0x3724,
	0x372c, 0x379f, 0x37a1, 0x40d2]
var instructions: Dictionary
var irq_instructions: Dictionary
var base: int
var pc: int
var cs: int
var ax: int
var carry: bool
var zero: bool
var game: Dictionary
var keyboard_game: Dictionary
var entries: Array = []
var keyboard_entries: Array = []
var loop_cost := 0
var fast_loops := 0
var hardware = preload("res://scripts/legacy/wr1_hardware.gd").new()
var music = preload("res://scripts/legacy/wr1_music.gd").new()
var opl = preload("res://scripts/legacy/wr1_opl.gd").new()
var irq = preload("res://scripts/legacy/wr1_irq_work.gd").new()
var keyboard_work = preload("res://scripts/legacy/wr1_keyboard_work.gd").new()

func configure(cmf: PackedByteArray, initial: Dictionary, names: Dictionary) -> void:
	var catalogue: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_work.json"))
	instructions = catalogue.main_instructions
	irq_instructions = catalogue.irq_instructions
	base = int(catalogue.main_file_base)
	pc = base + int(initial.cpu_ip)
	cs = int(initial.cpu_cs)
	ax = int(initial.cpu_ax)
	carry = bool(int(initial.cpu_flags) & 1)
	zero = bool(int(initial.cpu_flags) & 64)
	assert(int(initial.cpu_flags) & 512, "Idle checkpoint requires interrupts enabled")
	hardware.configure(initial, names)
	game = initial.clock_state.duplicate(true)
	keyboard_game = initial.get("keyboard_game", {}).duplicate(true)
	music.configure(cmf, initial.music_driver)
	opl.configure(cmf, initial.music_driver.opl_state)
	irq.configure(bool(initial.music_driver.dispatcher_use_dx), int(initial.music_driver.external_timer))
	keyboard_work.configure()
	entries = []
	keyboard_entries = []
	fast_loops = 0
	loop_cost = 0
	var saved := [pc, ax, carry, zero, game]
	game = game.duplicate(true)
	pc = 0x34ba
	game.timer = 0
	game.threshold = 1
	for key in COMPARE_FLAGS.values():
		game.control_flags[key] = 0
	while true:
		_instruction()
		loop_cost += 1
		if pc == 0x34ba:
			break
		assert(loop_cost <= 100, "Ordinary idle loop did not close")
	pc = saved[0]
	ax = saved[1]
	carry = saved[2]
	zero = saved[3]
	game = saved[4]

func _instruction() -> String:
	assert(COMPARE_FLAGS.has(pc) or pc in IDLE_NODES, "Outside ordinary idle path at file %05x" % pc)
	var instruction: Array = instructions[str(pc)]
	var op: String = instruction[0]
	var next_pc := int(instruction[1])
	if COMPARE_FLAGS.has(pc):
		carry = false
		zero = (int(game.control_flags[COMPARE_FLAGS[pc]]) & 65535) == 0
	elif pc == 0x371b:
		ax = int(game.timer) & 65535
	elif pc == 0x371e:
		var threshold := int(game.threshold) & 65535
		carry = ax < threshold
		zero = ax == threshold
	elif pc == 0x379f:
		ax = 0
		carry = false
		zero = true
	elif pc == 0x37a1:
		pass # Ancillary frame flag cleared before admission.
	elif op in ["jmp", "je", "jne", "jae"]:
		if {"jmp":true, "je":zero, "jne":not zero, "jae":not carry}[op]:
			next_pc = int(instruction[2])
	else:
		assert(false, "Unknown idle work at %05x" % pc)
	pc = next_pc
	return op

func _interrupt() -> void:
	var p: Dictionary = hardware.interrupts
	var possible: int = p.irr & ~p.imr & ~p.isr & ((1 << p.active_irq) - 1)
	if not (possible & 1) and (possible & 2):
		_keyboard_interrupt()
		return
	assert(possible & 1, "Pending non-timer interrupt")
	p.irr &= ~1
	p.isr |= 1
	p.active_irq = 0
	p.irq_check = 0
	var prologue: Array = []
	var ip := 0x224
	while ip < 0x232:
		var instruction: Array = irq_instructions[str(ip)]
		prologue.append([instruction[0], ip])
		ip = int(instruction[1])
	hardware.run_driver(prologue)
	entries.append({"hardware":hardware.snapshot(), "pic_cycle":roundi(hardware.observed_time() * 27000.0),
		"return_ip":pc - base, "return_cs":cs, "return_c":carry, "return_z":zero})
	var initial := game.duplicate(true)
	var index := int(initial.speaker_index)
	initial.speaker_entry = initial.speaker_sequence[index] if index >= 0 else [0, 0]
	initial.speaker_next = initial.speaker_sequence[index + 1] if index >= 0 else [0, 0]
	var result: Dictionary = irq.body(music, opl, initial)
	hardware.run_driver(result.work)
	game.merge(result.state, true)
	hardware.run_driver([["iret", 0x313]])
	entries[-1]["return_ms"] = hardware.observed_time()

func _keyboard_interrupt() -> void:
	assert(not keyboard_game.is_empty(), "IRQ1 requires game keyboard state")
	var p: Dictionary = hardware.interrupts
	p.irr &= ~2
	p.isr |= 2
	p.active_irq = 1
	p.irq_check = 0
	hardware.run_driver(keyboard_work.prologue())
	keyboard_entries.append({"hardware":hardware.snapshot(), "pic_cycle":roundi(hardware.observed_time() * 27000.0),
		"return_ip":pc - base, "return_cs":cs, "return_c":carry, "return_z":zero})
	var result: Dictionary = keyboard_work.body(keyboard_game, int(hardware.keyboard.port60))
	keyboard_game = result.state
	hardware.run_driver(result.work)
	for key in game.control_flags:
		if keyboard_game.flags.has(key):
			game.control_flags[key] = keyboard_game.flags[key]
	hardware.run_driver([["iret", 0xc95f]])

func until_admission(max_blocks: int = 2000000, input_events: Array = []) -> int:
	var blocks := 0
	var event_index := 0
	while pc != 0x37a4:
		if not hardware.pending:
			var cycle := roundi(hardware.observed_time() * 27000.0)
			while event_index < input_events.size() and input_events[event_index].cycle <= cycle:
				var event: Dictionary = input_events[event_index]
				assert(event.cycle == cycle, "External input did not fall on an idle CPU block boundary")
				hardware.keyboard_key(int(event.key), int(event.scan), bool(event.pressed), bool(event.extended))
				event_index += 1
			hardware.begin_block()
			if hardware.interrupts.irq_check:
				_interrupt()
				continue
			var ordinary := true
			for value in game.control_flags.values():
				if value:
					ordinary = false
			if pc == 0x34ba and (int(game.timer) & 65535) < (int(game.threshold) & 65535) and ordinary:
				@warning_ignore("integer_division")
				var loops: int = (hardware.cycles - 1) / loop_cost
				if loops > 0:
					hardware.cycles -= loops * loop_cost
					ax = int(game.timer) & 65535
					carry = true
					zero = false
					fast_loops += loops
		var op := _instruction()
		hardware.pending += 1
		if op.begins_with("j") or hardware.pending == 32:
			hardware.end_block(hardware.pending)
			hardware.pending = 0
			blocks += 1
			assert(blocks <= max_blocks, "Idle simulation did not reach admission")
	assert(event_index == input_events.size(), "Input plan extends beyond idle wait")
	return roundi(hardware.observed_time() * 27000.0)
