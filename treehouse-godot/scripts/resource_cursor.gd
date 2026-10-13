extends RefCounted
## Cursor source and converted image/mask ownership, for the VGA descriptor.
var loader
var stride: int
var background: int
var source: int = 0
var image: int = 0
var mask: int = 0
var hotspot_x: int
var hotspot_y: int

func _init(cache, pixels_per_byte: int) -> void:
	assert(pixels_per_byte > 0 and 16 % pixels_per_byte == 0)
	loader = cache
	stride = int(16/pixels_per_byte)
	background = loader.memory.allocate_raw(16*stride)

func load_source(key: String, payload: PackedByteArray, flags: int) -> int:
	source = loader.source(key,payload,flags)
	return source

func converted(payload: PackedByteArray, base: int, invert: bool) -> int:
	var m = loader.memory
	var bytes = PackedByteArray([16,0,16,0,16,0])
	bytes.resize(262)
	for y in 16:
		for x in 16:
			var bit = (payload[base+2*y+1-(x >> 3)] >> (7-(x & 7))) & 1
			bytes[6+16*y+x] = 255 if (bit ^ int(invert)) else 0
	var id = m.allocate_handle(bytes.size())
	m.lock(id)
	m.unlock(id)
	var resized = m.resize_handle(id,bytes.size())
	assert(resized)
	m.resource_payloads[id] = bytes
	return id

func activate() -> void:
	assert(stride == 16, "Only VGA cursor conversion is implemented")
	var m = loader.memory
	var payload: PackedByteArray = m.resource_payloads[source]
	assert(payload.size() == 68)
	var saved: int = m.handle(source).state
	m.lock(source)
	var new_image = converted(payload,36,false)
	var new_mask = converted(payload,4,true)
	for id in [image,mask]:
		if id: m.free_handle(id)
	m.promote(new_mask)
	m.lock(new_mask)
	m.promote(new_image)
	m.lock(new_image)
	image = new_image
	mask = new_mask
	hotspot_x = payload.decode_s16(0)
	hotspot_y = payload.decode_s16(2)
	m.flags(source,saved)
