extends RefCounted
## Two-byte-header allocator used for resource handles and bookkeeping.

var blocks: Array
var start: int
var search: int
var end: int
var growth: Dictionary

func _init(state: Dictionary, growth_limits: Dictionary = {}) -> void:
	blocks = state.blocks.duplicate(true)
	start = state.start
	search = state.search
	end = state.end
	growth = growth_limits.duplicate()
	assert(blocks[0].address == start and blocks[-1].address == end, "Invalid near heap extent")
	for i in blocks.size()-1:
		var block: Dictionary = blocks[i]
		assert(block.size >= 0 and block.size % 2 == 0 and block.address+block.size+2 == blocks[i+1].address, "Invalid near heap chain")
	at(search)

func at(address: int) -> Dictionary:
	for block in blocks:
		if block.address == address: return block
	assert(false, "Near heap cursor is not a block: %d" % address)
	return {}

func reset_search() -> void:
	search = start

func allocate(payload: int) -> int:
	assert(payload >= 0 and payload <= 0xffe8, "Invalid near allocation size")
	var needed = (payload+1) & 0xfffe
	var previous = search
	for span in [[previous, end], [start, previous-1]]:
		if span[0] > span[1]: continue
		var block = at(span[0])
		for _guard in 32768:
			if block.free:
				var i = blocks.find(block)
				while block.size < needed and i+1 < blocks.size() and blocks[i+1].free:
					block.size += blocks[i+1].size+2
					blocks.remove_at(i+1)
				if block.size >= needed:
					if block.size != needed:
						blocks.insert(i+1, {"address":block.address+2+needed, "size":block.size-needed-2, "free":true})
					block.size = needed
					block.free = false
					search = block.address+2+needed
					return block.address+2
			if block.address >= span[1]: break
			block = at(block.address+block.size+2)
	search = start
	if not growth.is_empty() and grow(payload, growth.limit, growth.quantum): return allocate(payload)
	assert(false, "Near heap growth requires explicit platform limits")
	return 0

func grow(payload: int, limit: int, quantum: int) -> bool:
	assert(payload >= 0 and payload <= 0xffe8 and limit >= end+2 and limit <= 65536 and quantum >= 1 and quantum <= 65535, "Invalid near growth request")
	var needed = (payload+1) & 0xfffe
	var last: Dictionary = blocks[-2]
	var top = end+2
	var minimum: int = top+needed-(last.size if last.free else -2)
	var unit = 16
	while unit < quantum: unit *= 2
	var next = int(ceil(float(minimum)/unit))*unit
	if next > limit: next = int(ceil(float(minimum)/16))*16
	if next > limit or next <= top: return false
	blocks[-1].size = next-top-2
	blocks[-1].free = true
	end = next-2
	blocks.append({"address":end, "size":65534, "free":false})
	search = last.address
	return true

func release(pointer: int) -> void:
	if pointer <= start: return
	var block = at(pointer-2)
	assert(block.address != end, "Cannot release near heap terminator")
	block.free = true
	search = mini(search, block.address)

func snapshot() -> Dictionary:
	return {"blocks":blocks.duplicate(true), "start":start, "search":search, "end":end}
