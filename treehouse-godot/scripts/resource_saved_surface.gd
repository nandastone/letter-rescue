extends RefCounted
## Saved screen rectangle descriptor, rows and separately owned raw pixels.
var memory
var stride: int
var bounds: Array
var descriptor: int
var pixels: int

func _init(model, rectangle: Array, pixels_per_byte: int = 1, origin_left: int = 0) -> void:
	assert(rectangle.size() == 4 and pixels_per_byte in [1,2,4,8])
	var height: int = rectangle[2]-rectangle[0]
	var width: int = rectangle[3]-rectangle[1]
	assert(height >= 0 and width >= 0)
	var alignment: int = (rectangle[1]-origin_left) & (pixels_per_byte-1)
	stride = int((alignment+width+pixels_per_byte-1)/pixels_per_byte)
	bounds = [rectangle[0],rectangle[1]-alignment,rectangle[2],rectangle[3]]
	memory = model
	descriptor = memory.near.allocate(24+2*height)
	pixels = memory.allocate_raw(stride*height)

func dispose() -> void:
	assert(descriptor, "Saved surface already released")
	memory.free_raw(pixels)
	memory.near.release(descriptor)
	pixels = 0
	descriptor = 0
