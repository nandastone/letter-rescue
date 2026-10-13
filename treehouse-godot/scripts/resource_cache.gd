extends RefCounted
## Resident 7A66 source-cache ownership. No instruction-work dependencies.
var memory
var catalog_handle: int
var embedded_catalog: Dictionary = {}
var sources: Dictionary = {}
var operations: Array = []

func _init(model, catalog: int, embedded: bool = false) -> void:
	assert(not embedded or catalog == 0)
	memory = model
	catalog_handle = catalog
	if embedded: embedded_catalog = {"state":0}

func source(key: String, payload: PackedByteArray, directory_flags: int) -> int:
	assert(not directory_flags & ~0xf0, "Unsupported resource directory flags")
	assert(embedded_catalog.is_empty() or directory_flags & 0x10)
	var catalog = memory.handle(catalog_handle) if embedded_catalog.is_empty() else embedded_catalog
	var saved: int = catalog.state
	catalog.state |= 0x8000
	var id: int = sources.get(key,0)
	var h: Dictionary = memory.handle(id) if id else {"state":0,"segment":0}
	assert(not id or not h.state & 0x200, "EMS source cache is not implemented")
	var resident: bool = id != 0 and ((h.state & 15) != 0 or h.segment != 0)
	var promote: bool = not id and directory_flags & 0x80 != 0
	var discardable: bool = not id and directory_flags & 0x40 != 0
	if id: memory.address(id)
	if resident:
		catalog.state = saved
		return id
	if id:
		var reallocated = memory.reallocate(id,payload.size())
		assert(reallocated)
		operations.append({"kind":"handle.reallocate","bytes":payload.size()})
	else:
		id = memory.allocate_handle(payload.size())
		operations.append({"kind":"handle.allocate","bytes":payload.size()})
	var flags: int = memory.handle(id).state
	memory.lock(id)
	memory.resource_payloads[id] = payload.duplicate()
	operations.append({"kind":"resource.copy" if directory_flags & 0x10 else "resource.read","bytes":payload.size()})
	memory.handle(id).state = flags | 0x1000
	sources[key] = id
	memory.resource_owners[id] = {"cache":sources,"key":key}
	if promote:
		memory.promote(id)
		memory.lock(id)
	if discardable: memory.discardable(id)
	catalog.state = saved
	return id
