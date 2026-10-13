extends RefCounted
## Generated arena initialization from executable and platform parameters.
const DOS = preload("res://scripts/resource_dos_memory.gd")
const Near = preload("res://scripts/resource_near_heap.gd")
const Memory = preload("res://scripts/resource_memory.gd")

static func near(stack_pointer: int, stack_bias: int) -> Dictionary:
	assert(stack_pointer >= 0 and stack_bias >= 0 and stack_pointer+stack_bias <= 65535)
	var top = (stack_pointer+stack_bias) & 0xfffe
	var start = top-4
	var end = top-2
	assert(start >= 0)
	return {"blocks":[{"address":start,"size":0,"free":true},{"address":end,"size":65534,"free":false}],"start":start,"search":start,"end":end}

static func arena(segment: int, paragraphs: int) -> Dictionary:
	assert(segment > 0 and paragraphs >= 3 and segment+paragraphs <= 0xa000)
	var control = segment*16
	var start = control+22
	var end = control+paragraphs*16-6
	return {"control":control,"paragraphs":paragraphs,"committedParagraphs":paragraphs,"emsSegment":0,"closed":false,
		"heap":{"blocks":[{"address":start,"size":end-start,"flags":0,"padding":0},{"address":end,"size":6,"flags":0x4000,"padding":0}],"handles":[],"search":start}}

static func allocate_arena(dos, data_segment: int, requested_bytes: int = 0) -> Dictionary:
	assert(data_segment >= 0 and data_segment <= 65535 and requested_bytes >= 0 and requested_bytes <= 0xffffffff)
	var wanted = maxi(3,mini(65535,(requested_bytes+15) >> 4))
	var paragraphs = wanted
	for _attempt in 65536:
		var allocation = dos.allocate(paragraphs)
		if not allocation.ok:
			assert(allocation.paragraphs > 0, "No conventional memory for resources")
			paragraphs = allocation.paragraphs
			allocation = dos.allocate(paragraphs)
		assert(allocation.ok)
		if allocation.segment <= data_segment:
			dos.release(allocation.segment)
			paragraphs += 1
			continue
		var state = arena(allocation.segment, allocation.paragraphs)
		if state.paragraphs < wanted: grow_with_dos(state,16*(wanted-state.paragraphs),dos)
		return state
	assert(false, "Resource arena allocation did not terminate")
	return {}

static func grow_with_dos(state: Dictionary, requested_bytes: int, dos) -> int:
	if state.closed: return 0
	assert(requested_bytes >= 0 and requested_bytes <= 0xffffffff)
	var paragraphs = mini(65535, state.committedParagraphs+mini(65535,(requested_bytes+15) >> 4))
	var result = dos.resize(state.control >> 4, paragraphs)
	if not result.ok and result.error == 8: result = dos.resize(state.control >> 4, result.paragraphs)
	assert(result.ok, "Cannot resize conventional resource arena")
	return grow_arena(state, requested_bytes, result.paragraphs)

static func grow_arena(state: Dictionary, requested_bytes: int, maximum_paragraphs: int) -> int:
	assert(requested_bytes >= 0 and requested_bytes <= 0xffffffff and maximum_paragraphs >= state.committedParagraphs and maximum_paragraphs <= 65535 and state.control+16*maximum_paragraphs <= 0xa0000)
	assert(not state.emsSegment, "EMS growth is not implemented")
	if state.closed: return 0
	var requested = mini(65535, (requested_bytes+15) >> 4)
	var target = mini(mini(65535, state.committedParagraphs+requested), maximum_paragraphs)
	var paragraphs: int = target-state.committedParagraphs
	var bytes = 16*paragraphs
	if paragraphs:
		var terminal: Dictionary = state.heap.blocks[-1]
		assert(terminal.flags == 0x4000 and terminal.size == 6)
		terminal.flags = 0
		terminal.size = bytes
		terminal.padding = 0
		state.heap.blocks.append({"address":terminal.address+bytes,"size":6,"flags":0x4000,"padding":0})
		state.committedParagraphs = target
		state.paragraphs += paragraphs
	if not paragraphs or paragraphs < requested: state.closed = true
	return bytes

static func memory(input: Dictionary) -> Dictionary:
	assert(input.configurationBytes >= 0 and input.screenHeight > 0)
	var environment_bytes = 1
	for variable in input.environment:
		assert(variable is String and not variable.is_empty())
		for i in variable.length(): assert(variable.unicode_at(i) > 0 and variable.unicode_at(i) < 128)
		environment_bytes += variable.length()+1
	var platform = DOS.treehouse(input.dataSegmentRelative, maxi(256,environment_bytes+83))
	var local = Near.new(near(input.stackPointer,input.stackBias), {"limit":65536,"quantum":1024})
	platform.environmentPointer = local.allocate(environment_bytes)
	platform.environmentIndex = local.allocate(2*(input.environment.size()+1))
	local.growth.quantum = 8192
	platform.configuration = local.allocate(maxi(28,input.configurationBytes))
	var state = allocate_arena(platform.dos,platform.dataSegment)
	platform.scanlines = local.allocate(2*input.screenHeight)
	var dos = platform.dos
	var model = Memory.new({"heap":state.heap,"near":local.snapshot()}, func(bytes): return grow_with_dos(state,bytes,dos), local.growth)
	# Share the block array without capturing the heap object in its callback.
	state.heap.blocks = model.heap.blocks
	model.arena = state
	platform.memory = model
	return platform

static func arena_snapshot(model) -> Dictionary:
	var state = model.arena.duplicate()
	state.heap = model.heap.snapshot()
	return state
