extends RefCounted
## VGA font conversion and transfer into the existing cached font handle.

static func convert_glyphs(source: PackedByteArray) -> PackedByteArray:
	assert(source.size() >= 10 and source[1] >= source[0])
	var count = source[1]-source[0]+1
	assert(source.size() >= 10+2*count)
	var glyphs: Array = []
	var length = 10+8*count
	for i in count:
		var offset = source.decode_u16(10+2*i)
		assert(offset+6 <= source.size())
		var height = source.decode_u16(offset)
		var width = source.decode_u16(offset+2)
		var stride = (width+7) >> 3
		assert(offset+6+height*stride <= source.size())
		length += width*height
		glyphs.append({"offset":offset,"height":height,"width":width,"stride":stride})
	assert(length <= 65535)
	var output = PackedByteArray()
	output.resize(length)
	for i in 10: output[i] = source[i]
	var at = 10+2*count
	for i in count:
		var glyph: Dictionary = glyphs[i]
		output.encode_u16(10+2*i,at)
		output.encode_u16(at,glyph.height)
		output.encode_u16(at+2,glyph.width)
		output.encode_u16(at+4,glyph.width)
		for y in glyph.height:
			for x in glyph.width:
				output[at+6+y*glyph.width+x] = 255 if source[glyph.offset+6+y*glyph.stride+(x >> 3)] & (0x80 >> (x & 7)) else 0
		at += 6+glyph.height*glyph.width
	return output

static func activate(loader, id: int) -> int:
	var m = loader.memory
	var saved: int = m.handle(id).state
	if saved & 0x2000: return id
	assert(m.resource_payloads.has(id))
	m.lock(id)
	var bytes = convert_glyphs(m.resource_payloads[id])
	var converted = m.allocate_handle(bytes.size())
	m.lock(converted)
	m.unlock(converted)
	m.flags(id,saved)
	var pointer = m.detach_handle(converted)
	if not m.attach_handle(id,pointer):
		m.free_raw(pointer)
		m.free_handle(converted)
		return 0
	m.keep_resident(id)
	m.free_handle(converted)
	m.resource_payloads[id] = bytes
	loader.operations.append({"kind":"font.convert","bytes":bytes.size()})
	return id
