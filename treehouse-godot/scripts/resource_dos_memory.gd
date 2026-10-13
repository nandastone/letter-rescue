extends RefCounted
## Conventional allocation for the pinned VGA DOS platform, in paragraphs.
var blocks: Array
var owner: int

func _init(initial: Array, process_owner: int = 8) -> void:
	blocks = initial.duplicate(true)
	owner = process_owner
	assert(not blocks.is_empty() and blocks[-1].type == 0x5a)
	for i in blocks.size():
		var b: Dictionary = blocks[i]
		assert(b.paragraphs >= 0 and b.segment+b.paragraphs < 0xa000 and b.type in [0x4d,0x5a])
		assert(i == blocks.size()-1 or (b.type == 0x4d and b.segment+b.paragraphs+1 == blocks[i+1].segment))

static func platform():
	# DOS_SetupMemory: reliable-addresses build, conventional VGA memory.
	var beginning = 0x16f
	var low = beginning+2
	var locked = low+5
	var available = locked+16
	return load("res://scripts/resource_dos_memory.gd").new([
		{"segment":beginning,"paragraphs":1,"owner":8,"type":0x4d},
		{"segment":low,"paragraphs":4,"owner":0,"type":0x4d},
		{"segment":locked,"paragraphs":15,"owner":0x40,"type":0x4d},
		{"segment":available,"paragraphs":0x9ffe-available,"owner":0,"type":0x5a}])

static func treehouse(relative_data_segment: int, environment_bytes: int = 256) -> Dictionary:
	assert(relative_data_segment >= 0 and relative_data_segment <= 0xffff and environment_bytes >= 256)
	var dos = platform()
	var environment = dos.allocate((environment_bytes+15) >> 4)
	assert(environment.ok)
	var probe = dos.allocate(65535)
	assert(not probe.ok)
	var program = dos.allocate(probe.paragraphs)
	assert(program.ok)
	var process_segment: int = program.segment
	var data_segment = process_segment+16+relative_data_segment
	dos.owner = process_segment
	dos.block(process_segment).owner = process_segment
	dos.block(environment.segment).owner = process_segment
	var resized = dos.resize(process_segment, 16+relative_data_segment+0x1000)
	assert(resized.ok)
	return {"dos":dos,"processSegment":process_segment,"dataSegment":data_segment,"environmentSegment":environment.segment}

func block(segment: int) -> Dictionary:
	for b in blocks:
		if b.segment+1 == segment: return b
	assert(false, "Unknown DOS allocation")
	return {}

func compress() -> void:
	var i = 0
	while i < blocks.size()-1:
		var a: Dictionary = blocks[i]
		var b: Dictionary = blocks[i+1]
		if not a.owner and not b.owner:
			a.paragraphs += b.paragraphs+1
			a.type = b.type
			blocks.remove_at(i+1)
		else: i += 1

func allocate(paragraphs: int) -> Dictionary:
	assert(paragraphs >= 0 and paragraphs <= 65535)
	compress()
	var largest = 0
	for i in blocks.size():
		var b: Dictionary = blocks[i]
		if b.owner: continue
		largest = maxi(largest, b.paragraphs)
		if b.paragraphs < paragraphs: continue
		if b.paragraphs > paragraphs:
			blocks.insert(i+1, {"segment":b.segment+paragraphs+1,"paragraphs":b.paragraphs-paragraphs-1,"owner":0,"type":b.type})
			b.paragraphs = paragraphs
			b.type = 0x4d
		b.owner = owner
		return {"ok":true,"segment":b.segment+1,"paragraphs":paragraphs}
	return {"ok":false,"paragraphs":largest,"error":8}

func release(segment: int) -> Dictionary:
	for b in blocks:
		if b.segment+1 == segment and segment >= 0x170:
			b.owner = 0
			return {"ok":true}
	return {"ok":false,"error":9}

func resize(segment: int, paragraphs: int) -> Dictionary:
	assert(paragraphs >= 0 and paragraphs <= 65535)
	compress()
	var index = -1
	for i in blocks.size():
		if blocks[i].segment+1 == segment: index = i; break
	if index < 0: return {"ok":false,"error":7}
	var b: Dictionary = blocks[index]
	var total: int = b.paragraphs
	var type: int = b.type
	if paragraphs > total and b.type != 0x5a and blocks[index+1].owner == 0:
		var next: Dictionary = blocks[index+1]
		total += next.paragraphs+1
		type = next.type
		blocks.remove_at(index+1)
	var actual = mini(paragraphs,total)
	b.paragraphs = actual
	b.owner = owner
	b.type = type
	if actual < total:
		blocks.insert(index+1, {"segment":b.segment+actual+1,"paragraphs":total-actual-1,"owner":0,"type":type})
		b.type = 0x4d
		compress()
	return {"ok":true,"paragraphs":actual} if actual == paragraphs else {"ok":false,"paragraphs":actual,"error":8}

func snapshot() -> Array:
	return blocks.duplicate(true)
