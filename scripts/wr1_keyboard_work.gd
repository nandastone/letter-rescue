extends RefCounted
## Original IRQ1 scan-code dispatch and instruction work, before IRET.
const HELD := {0xc882:"01a8", 0xc88b:"01a4", 0xc894:"01a2", 0xc8cd:"0192", 0xc8d6:"0190",
	0xc8df:"0194", 0xc8e7:"0196", 0xc91c:"01a6", 0xc924:"019a", 0xc93b:"019c"}
const LATCHED := {0xc89d:"01b2", 0xc8ad:"01b0", 0xc8bd:"019e", 0xc8ef:"01a0",
	0xc8fe:"01ae", 0xc90d:"018c", 0xc92c:"0198"}
var instructions: Dictionary
var targets: Array
var path: Array

func configure() -> void:
	var catalogue: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_work.json"))
	instructions = catalogue.keyboard_instructions
	targets = catalogue.keyboard_targets

func span(start: int, end: int) -> void:
	while start <= end:
		var instruction: Array = instructions[str(start)]
		var op: String = instruction[0]
		if start == 0xc722:
			op = "keyboard_read"
		elif start == 0xc953:
			op = "eoi"
		path.append([op, start])
		start = int(instruction[1])

func prologue() -> Array:
	path = []
	span(0xc714, 0xc720)
	return path

func body(initial: Dictionary, scan: int) -> Dictionary:
	path = []
	var state := initial.duplicate(true)
	state.scan = scan
	span(0xc722, 0xc739)
	if state.pressed == 0xe0:
		span(0xc73b, 0xc73b)
	else:
		span(0xc73e, 0xc743)
		state.pressed = 0 if scan & 128 else 1
		if scan & 128:
			span(0xc745, 0xc74b)
		else:
			span(0xc74d, 0xc74d)
		state.scan = scan & 127
		span(0xc753, 0xc75d)
		var handled := false
		if not state.custom:
			span(0xc75f, 0xc75f)
		else:
			var bindings := [[0xc762,"0190"], [0xc776,"0192"], [0xc78a,"0196"], [0xc79e,"0194"], [0xc7b2,"019e"]]
			for i in range(bindings.size()):
				var start := int(bindings[i][0])
				var key: String = bindings[i][1]
				span(start, start + 7)
				if state.scan != state.bindings[i]:
					continue
				if i < 4:
					span(start + 9, start + 15)
					state.flags[key] = state.pressed
				else:
					span(0xc7bb, 0xc7c0)
					if state.pressed:
						span(0xc7c2, 0xc7c2)
						state.flags[key] = 1
					span(0xc7c8, 0xc7c8)
				handled = true
				break
		if not handled:
			span(0xc7cb, 0xc7d4)
			if state.scan < 1 or state.scan > 80:
				span(0xc7d6, 0xc7d6)
			else:
				span(0xc7d9, 0xc7dd)
				var target := int(targets[state.scan - 1])
				if HELD.has(target):
					span(target, target + 6)
					state.flags[HELD[target]] = state.pressed
				elif LATCHED.has(target):
					span(target, target + 5)
					if state.pressed:
						span(target + 7, target + 7)
						state.flags[LATCHED[target]] = 1
					span(target + 13, target + 13)
				else:
					assert(target == 0xc943, "Unsupported keyboard target")
	span(0xc943, 0xc948)
	if state.pressed:
		span(0xc94a, 0xc94a)
		state.activity = 1
	span(0xc950, 0xc95e)
	return {"work":path, "state":state}
