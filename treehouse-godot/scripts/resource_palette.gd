extends RefCounted
## Main 6416 assigns explicit VGA palette banks and retains the SHPL source.
var catalogs
var memory

func _init(source_catalogs) -> void:
	catalogs = source_catalogs
	memory = catalogs.memory

func load_palette(id: int, banks: int) -> int:
	assert(banks > 0 and banks <= 65535)
	var found = catalogs.resolve("SHPL",id)
	assert(not found.is_empty())
	var handle = catalogs.load_source(found.catalog.handle,"SHPL",id)
	memory.retain(handle)
	memory.address(handle)
	var payload: PackedByteArray = memory.resource_payloads[handle]
	assert(payload.size() >= 7)
	payload.encode_u16(4,banks)
	memory.resource_payloads[handle] = payload
	var saved: int = memory.handle(handle).state
	memory.address(handle)
	memory.lock(handle)
	memory.flags(handle,saved)
	return handle
