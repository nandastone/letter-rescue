extends RefCounted
## Conventional resource allocation. Addresses describe the original memory
## layout, never host pointers. Callers supply independently generated lifetimes.

var blocks: Array
var handles: Dictionary = {}
var start: int
var search: int
var moves: Array = []
var scans: int = 0
var merges: int = 0
var growth: Callable

func _init(state: Dictionary, grow: Callable = Callable()) -> void:
	blocks = state.blocks.duplicate(true)
	for handle in state.handles: handles[handle.id] = handle.duplicate(true)
	start = blocks[0].address
	search = state.search
	growth = grow
	for i in blocks.size():
		var block: Dictionary = blocks[i]
		assert(block.size >= 6 and block.size % 2 == 0, "Invalid resource block size")
		assert(i == 0 or blocks[i-1].address + blocks[i-1].size == block.address, "Broken resource block chain")
		assert(block.flags in [0, 0x4000, 0x8000, 0xc000], "Unsupported block flags")
		assert(block.flags != 0xc000 or handles.has(block.handle), "Missing resource handle")
		assert((block.flags == 0x4000) == (i == blocks.size()-1), "Invalid resource terminator")
	at(search)

func at(address: int) -> Dictionary:
	for block in blocks:
		if block.address == address: return block
	assert(false, "Resource cursor is not a block: %d" % address)
	return {}

func following(block: Dictionary) -> Dictionary:
	return at(block.address + block.size)

func required(payload: int) -> int:
	assert(payload >= 0 and payload <= 0xffff8, "Invalid resource allocation size")
	return (payload + 7) & ~1

func search_size(payload: int) -> int:
	assert(payload >= 0 and payload <= 0xffffffff, "Invalid resource search size")
	return mini(0xfffff, (payload + 7) & ~1)

func coalesce(block: Dictionary) -> Dictionary:
	assert(block.flags == 0, "Only free blocks can coalesce")
	var index = blocks.find(block)
	while blocks[index+1].flags == 0:
		block.size += blocks[index+1].size
		blocks.remove_at(index+1)
		merges += 1
	return block

func reserve(block: Dictionary, payload: int, tail: bool) -> Dictionary:
	var needed = required(payload)
	var remainder: int = block.size - needed
	assert(remainder >= 0 and block.flags == 0, "Resource allocation exceeds free block")
	if remainder >= 6:
		var index = blocks.find(block)
		if tail:
			block.size = remainder
			block.padding = 0
			block = {"address":block.address+remainder, "size":needed, "flags":0, "padding":0}
			blocks.insert(index+1, block)
		else:
			blocks.insert(index+1, {"address":block.address+needed, "size":remainder, "flags":0, "padding":0})
			block.size = needed
	block.padding = block.size - payload - 6
	search = block.address
	return block

func last_fit(payload: int) -> Dictionary:
	var block = at(search)
	var found: Dictionary = {}
	while block.flags != 0x4000:
		scans += 1
		if block.flags == 0:
			coalesce(block)
			if block.size >= required(payload): found = block
		block = following(block)
	return reserve(found, payload, true) if not found.is_empty() else {}

func find_first(payload: int) -> Dictionary:
	for beginning in [search, start]:
		var block = at(beginning)
		while block.flags != 0x4000:
			scans += 1
			if block.flags == 0:
				coalesce(block)
				if block.size >= required(payload): return reserve(block, payload, false)
			block = following(block)
	return {}

func first_fit(payload: int) -> Dictionary:
	var found = find_first(payload)
	if not found.is_empty(): return found
	# Resident 6D47 attempts packing before arena growth or cache eviction.
	if pack(required(payload)) >= required(payload):
		found = find_first(payload)
		if not found.is_empty(): return found
	if growth.is_valid() and growth.call(required(payload)) >= required(payload):
		found = find_first(payload)
		if not found.is_empty(): return found
	assert(false, "Resource pressure requires an explicit growth/eviction provider")
	return {}

func relocate(block: Dictionary) -> bool:
	var handle: Dictionary = handles[block.handle]
	if handle.state & 0x8000: return false
	var payload: int = block.size - 6 - block.padding
	var old_state: int = handle.state
	handle.state |= 0x8000
	search = block.address
	var destination = last_fit(payload)
	if destination.is_empty(): destination = first_fit(payload)
	handle.state = (old_state & 0xfff0) | (destination.address & 15)
	handle.segment = destination.address >> 4
	destination.flags = block.flags
	destination.handle = block.handle
	if block.has("payload"): destination.payload = block.payload
	moves.append({"handle":block.handle, "from":block.address, "to":destination.address, "bytes":payload})
	block.flags = 0
	block.erase("handle")
	block.erase("payload")
	return true

func prepare(payload: int) -> int:
	var needed = search_size(payload)
	var best = 6
	var block = at(start)
	for _guard in 100000:
		scans += 1
		if block.flags == 0x4000:
			search = block.address
			return best-6
		if block.flags == 0x8000 or (block.flags == 0xc000 and not relocate(block)):
			block = following(block)
			continue
		coalesce(block)
		best = maxi(best, block.size)
		if block.size >= needed:
			search = block.address
			return best-6
		var next = following(block)
		if next.flags == 0x4000:
			search = block.address
			return best-6
		if next.flags == 0xc000:
			# Keep the current hole unavailable while moving its neighbor.
			block.flags = 0x8000
			var moved = relocate(next)
			block.flags = 0
			if moved: continue
		block = following(block)
	assert(false, "Resource preparation failed to terminate")
	return -1

func pack(payload: int) -> int:
	# Forward packing preserves the moved block's size and padding, including
	# overlapping moves. Locked handles and raw allocations remain fixed.
	var needed = search_size(payload)
	var best = 6
	var block = at(start)
	for _guard in 100000:
		scans += 1
		if block.flags == 0x4000:
			search = block.address
			return best-6
		if block.flags != 0:
			block = following(block)
			continue
		coalesce(block)
		best = maxi(best, block.size)
		if block.size >= needed:
			search = block.address
			return best-6
		var next = following(block)
		if next.flags == 0x4000:
			search = block.address
			return best-6
		if next.flags != 0xc000 or handles[next.handle].state & 0x8000:
			block = next
			continue
		var index = blocks.find(block)
		var origin: int = next.address
		var destination: int = block.address
		var hole = {"address":destination+next.size, "size":block.size, "flags":0, "padding":0}
		next.address = destination
		var handle: Dictionary = handles[next.handle]
		handle.state = (handle.state & 0xfff0) | (destination & 15)
		handle.segment = destination >> 4
		blocks[index] = next
		blocks[index+1] = hole
		moves.append({"handle":next.handle, "from":origin, "to":destination, "bytes":next.size})
		block = hole
	assert(false, "Resource packing failed to terminate")
	return -1

func snapshot() -> Dictionary:
	var ordered = handles.values().duplicate(true)
	ordered.sort_custom(func(a, b): return a.id < b.id)
	return {"blocks":blocks.duplicate(true), "handles":ordered, "search":search}
