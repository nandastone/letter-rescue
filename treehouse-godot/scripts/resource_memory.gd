extends RefCounted
## Resource ownership on the original conventional/near allocation models.
## Resource payloads and catalog links are owned here, not in capture fixtures.

const Heap = preload("res://scripts/resource_heap.gd")
const NearHeap = preload("res://scripts/resource_near_heap.gd")
var heap
var near
var arena: Dictionary = {}
var resource_payloads: Dictionary = {}
var resource_owners: Dictionary = {}

func _init(state: Dictionary, grow: Callable = Callable(), near_growth: Dictionary = {}) -> void:
	heap = Heap.new(state.heap, grow)
	near = NearHeap.new(state.near, near_growth)

func handle(id: int) -> Dictionary:
	assert(heap.handles.has(id), "Unknown resource handle: %d" % id)
	return heap.handles[id]

func claim_raw(block: Dictionary) -> int:
	block.flags = 0x8000
	return block.address+6

func claim_handle(block: Dictionary, id: int) -> int:
	block.flags = 0xc000
	block.handle = id
	heap.handles[id] = {"id":id, "state":(block.address & 15) | 0x1f0, "segment":block.address >> 4}
	return id

func move_handle_to(id: int, destination: Dictionary) -> void:
	var h = handle(id)
	var source = heap.at((h.state & 15) + 16*h.segment)
	destination.flags = source.flags
	destination.handle = id
	if source.has("payload"): destination.payload = source.payload
	h.state = (h.state & 0xfff0) | (destination.address & 15)
	h.segment = destination.address >> 4
	source.flags &= 0x3fff
	source.erase("handle")
	source.erase("payload")

func resize(block: Dictionary, payload: int) -> Dictionary:
	var needed = heap.required(payload)
	var old_flags: int = block.flags
	var grew: bool = block.size < needed
	if grew:
		var previous_payload: int = block.size-6-block.padding
		for _guard in 100000:
			block.flags = 0
			heap.coalesce(block)
			block.flags = old_flags
			if block.size >= needed: break
			var next = heap.following(block)
			if next.flags == 0xc000:
				block.flags = 0x8000
				var moved = heap.relocate(next)
				block.flags = old_flags
				if moved: continue
			resize(block, previous_payload)
			return {}
		assert(block.size >= needed, "Resource resize failed to terminate")
	# Exact rounded size leaves existing padding intact unless this call grew.
	if grew or block.size != needed:
		block.flags = 0
		heap.reserve(block, payload, false)
		block.flags = old_flags
	else:
		heap.search = block.address
	return block

func allocate_raw(payload: int) -> int:
	heap.prepare(payload)
	return claim_raw(heap.first_fit(payload))

func available() -> int:
	if heap.growth.is_valid(): heap.growth.call(0xffffff)
	for h in heap.handles.values():
		if (h.state & 0xc000) == 0x4000: discard(h.id)
	for block in heap.blocks.duplicate():
		if block.flags == 0 and heap.blocks.has(block): heap.coalesce(block)
	return heap.pack(0xffffff)

func allocate_handle(payload: int) -> int:
	near.reset_search()
	var id = near.allocate(4)
	return claim_handle(heap.first_fit(payload), id)

func resize_handle(id: int, payload: int) -> bool:
	var pointer = address(id)
	if not pointer: return reallocate(id, payload)
	if not resize(heap.at(pointer-6), payload).is_empty(): return true
	var h = handle(id)
	if h.state & 0x8000: return false
	h.state |= 0x8000
	var destination = heap.first_fit(payload)
	h.state &= 0x7fff
	move_handle_to(id, destination)
	return true

func promote(id: int) -> int:
	if not id: return id
	var saved: int = handle(id).state
	var pointer = lock(id)
	if pointer:
		var source = heap.at(pointer-6)
		var payload: int = source.size-6-source.padding
		var space = heap.prepare(payload)
		var destination = heap.at(heap.search)
		if space >= payload and destination.address <= source.address and not resize(destination, payload).is_empty():
			move_handle_to(id, destination)
	flags(id, saved)
	return id

func reallocate(id: int, payload: int) -> bool:
	if not id or not discard(id): return false
	var saved: int = handle(id).state
	claim_handle(heap.first_fit(payload), id)
	handle(id).state |= saved & 0xfdf0
	return true

func address(id: int) -> int:
	if not id: return 0
	var h = handle(id)
	assert(not h.state & 0x200, "EMS resource materialization is not implemented")
	var pointer: int = (h.state & 15) + 16*h.segment
	if pointer: h.state |= 0x1f0
	return pointer+6 if pointer else 0

func lock(id: int) -> int:
	var pointer = address(id)
	if pointer: handle(id).state |= 0x81f0
	return pointer

func unlock(id: int) -> void:
	if id: handle(id).state &= 0x7fff

func retain(id: int) -> int:
	if id: handle(id).state &= 0xbfff
	return id

func keep_resident(id: int) -> int:
	if id: handle(id).state |= 0x2000
	return id

func discardable(id: int) -> int:
	if id: handle(id).state |= 0x4000
	return id

func flags(id: int, value: int) -> int:
	if id:
		var h = handle(id)
		h.state = (h.state & 0x1fff) | (value & 0xe000)
	return id

func free_raw(pointer: int) -> void:
	if pointer:
		var block = heap.at(pointer-6)
		block.flags &= 0x3fff
		block.erase("payload")

func detach_handle(id: int) -> int:
	var pointer = address(id)
	if not pointer: return 0
	var h = handle(id)
	var block = heap.at(pointer-6)
	block.flags = (block.flags & 0x3fff) | 0x8000
	block.erase("handle")
	h.state &= 0xdc00
	h.segment = 0
	return pointer

func attach_handle(id: int, pointer: int) -> bool:
	if not discard(id) or not pointer: return false
	var block = heap.at(pointer-6)
	var h = handle(id)
	assert((block.flags & 0xc000) == 0x8000, "Resource adoption requires raw allocation")
	block.flags = (block.flags & 0x3fff) | 0xc000
	block.handle = id
	h.state |= block.address & 15
	h.segment = block.address >> 4
	return true

func discard(id: int) -> bool:
	if not id: return false
	var h = handle(id)
	if h.state & 0x8000: return false
	assert(not h.state & 0x200, "EMS resource release is not implemented")
	var pointer: int = (h.state & 15) + 16*h.segment
	h.state &= 0xdc00
	h.segment = 0
	if pointer:
		var block = heap.at(pointer)
		block.flags &= 0x3fff
		block.erase("handle")
		block.erase("payload")
	resource_payloads.erase(id)
	return true

func free_handle(id: int) -> void:
	if not id: return
	if resource_owners.has(id):
		var owner: Dictionary = resource_owners[id]
		if owner.cache.get(owner.key) == id: owner.cache.erase(owner.key)
		if owner.has("entry") and owner.entry.get("handle") == id: owner.entry.handle = 0
		resource_owners.erase(id)
	unlock(id)
	discard(id)
	heap.handles.erase(id)
	near.release(id)
