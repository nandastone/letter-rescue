extends RefCounted
## Independently owned raw copies; scripts do not populate the source cache.
var memory
var operations: Array = []

func _init(model) -> void:
	memory = model

func load_copy(payload: PackedByteArray, catalog_handle: int, cached_handle: int = 0) -> int:
	var catalog = memory.handle(catalog_handle)
	var saved: int = catalog.state
	catalog.state |= 0x8000
	var source: int = memory.address(cached_handle) if cached_handle else 0
	var bytes = payload.size()
	if source:
		var block = memory.heap.at(source-6)
		bytes = block.size-6-block.padding
	catalog.state = saved
	catalog.state |= 0x8000
	var pointer = memory.allocate_raw(bytes)
	catalog.state = saved
	operations.append({"kind":"raw.allocate","bytes":bytes})
	operations.append({"kind":"resource.copy" if source else "resource.read","bytes":bytes})
	return pointer

func release(pointer: int) -> void:
	memory.free_raw(pointer)
	operations.append({"kind":"raw.free"})
