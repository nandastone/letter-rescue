extends "res://scripts/resource_cache.gd"
## Digital-sound decompression ownership; playback timing is handled elsewhere.

static func decoded_payload(payload: PackedByteArray) -> PackedByteArray:
	assert(payload.size() >= 13 and payload[0] & 1 and payload[3] == 255)
	var count = payload.decode_u16(10)
	assert(count > 0)
	var result = payload.slice(0,10)
	result.resize(count+10)
	result[3] = 8
	result.encode_u16(4,count)
	var value = payload[12]
	var width = 0
	var bit = 104
	var written = 1
	result[10] = value
	while written < count:
		var code = 0
		for _remaining in (width if width else 3):
			assert(bit < payload.size()*8, "Truncated compressed sound")
			code = 2*code+((payload[bit >> 3] >> (7-(bit & 7))) & 1)
			bit += 1
		if width:
			var marker = 1 << (width-1)
			if code == marker:
				width = 0
				continue
			value = (value+(code-(1 << width) if code > marker else code)) & 255
			result[10+written] = value
			written += 1
		elif code == 7:
			value = (value+128) & 255
			result[10+written] = value
			written += 1
		else: width = code+2
	return result

func prepare(id: int, payload: PackedByteArray, rates: Dictionary) -> Dictionary:
	if memory.handle(id).state & 0x2000: return {"action":"prepared"}
	var pointer = memory.address(id)
	if not pointer: return {"action":"missing"}
	if not payload[0] & 1: return {"action":"non-digital"}
	assert(payload.size() >= 10)
	var rate = payload.decode_u16(1)
	var codec = payload[3]
	assert(rate >= rates.minimumRate and rate <= rates.maximumRate, "Sound resampling ownership is not implemented")
	var block = memory.heap.at(pointer-6)
	if codec == 8: return {"action":"uncompressed","bytes":block.size-6-block.padding}
	assert(codec == 255 and payload.size() >= 13 and payload.decode_u16(10) > 0)
	var count = payload.decode_u16(10)
	var packed_bytes: int = block.size-6-block.padding-10
	var temporary_bytes = maxi(count,packed_bytes)+266
	var final_bytes = count+10
	var decoded = decoded_payload(payload)
	var expanded = memory.resize_handle(id,temporary_bytes)
	assert(expanded)
	operations.append({"kind":"handle.resize","bytes":temporary_bytes})
	var expanded_pointer = memory.address(id)
	var copy = {"from":expanded_pointer+10,"to":expanded_pointer+temporary_bytes-packed_bytes,"bytes":packed_bytes}
	memory.resource_payloads[id] = decoded
	var shrunk = memory.resize_handle(id,final_bytes)
	assert(shrunk)
	operations.append({"kind":"handle.resize","bytes":final_bytes})
	memory.keep_resident(id)
	return {"action":"decoded","temporaryBytes":temporary_bytes,"finalBytes":final_bytes,"count":count,"copy":copy}
