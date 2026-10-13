extends RefCounted
## DOS STATUS.DAT: retain the source bytes; patch changed semantic fields only.
const SIZE = 2704
var data: PackedByteArray
var observed: Dictionary = {}
var warnings: Array = []
var initialize: bool = false

func _init(bytes: PackedByteArray) -> void:
	assert(bytes.size()>=SIZE)
	data = bytes.duplicate()

func word(offset: int) -> int:
	return data.decode_u16(offset)

func signed(offset: int) -> int:
	return data.decode_s16(offset)

func valid(value: int, low: int, high: int, fallback: int, label: String) -> int:
	if value>=low and value<=high:
		return value
	warnings.append(label)
	return fallback

func field(offset: int, low: int = 0, high: int = 1, fallback: int = 0) -> int:
	return valid(word(offset),low,high,fallback,"Field %x"%offset)

func changed(key: String, value) -> bool:
	var current = JSON.stringify(value)
	if not observed.has(key):
		observed[key] = current
		return initialize
	if observed[key]==current:
		return false
	observed[key] = current
	return true

func put(offset: int, value: int) -> void:
	data.encode_u16(offset,value&65535)

func scalar(offset: int, value: int) -> void:
	if changed("w%d"%offset,value):
		put(offset,value)

func array(offset: int, values: Array, bytes: bool = false) -> void:
	for i in values.size():
		var at = offset+i*(1 if bytes else 2)
		if changed(("b" if bytes else "w")+str(at),values[i]):
			if bytes:
				data[at] = int(values[i])&255
			else:
				put(at,int(values[i]))
