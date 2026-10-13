extends "res://scripts/resource_cache.gd"
## Converted VGA shape and decoder scratch ownership. Pixels are rendered by
## the independent graphics decoder; this module controls resource lifetimes.

static func plan_shape(payload: PackedByteArray) -> Dictionary:
	assert(payload.size() >= 6)
	var height = payload.decode_u16(0)
	var width = payload.decode_u16(2)
	var flags = payload.decode_u16(4)
	var codec = (flags >> 8) & 15
	var bits = ((flags >> 12) & 7)+1 if flags & 0x8000 else 1
	assert(width > 0 and height > 0 and width*height <= 64000 and bits in [1,4,8] and codec <= 4)
	var stride = (width*bits+7) >> 3
	var converted = width*height+6
	return {"width":width,"height":height,"flags":flags,"codec":codec,"bits":bits,"stride":stride,
		"sourceBytes":payload.size(),"convertedBytes":maxi(converted,stride*height+6),"finalBytes":converted,"scratchBytes":1024 if codec in [3,4] else 0}

func load_shape(key: String, payload: PackedByteArray, palette_handle: int, directory_flags: int) -> int:
	var plan = plan_shape(payload)
	var palette_state: int = memory.handle(palette_handle).state
	memory.lock(palette_handle)
	var original = source(key,payload,directory_flags)
	var source_state: int = memory.handle(original).state
	memory.lock(original)
	var converted = memory.allocate_handle(plan.convertedBytes)
	operations.append({"kind":"handle.allocate","bytes":plan.convertedBytes})
	memory.lock(converted)
	if plan.scratchBytes:
		var scratch = memory.near.allocate(plan.scratchBytes)
		operations.append({"kind":"near.allocate","bytes":plan.scratchBytes})
		memory.near.release(scratch)
		operations.append({"kind":"near.free"})
	memory.unlock(converted)
	var resized = memory.resize_handle(converted,plan.finalBytes)
	assert(resized)
	operations.append({"kind":"resize","bytes":plan.finalBytes})
	memory.flags(original,source_state)
	memory.flags(palette_handle,palette_state)
	return converted
