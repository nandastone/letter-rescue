extends RefCounted
## WR1.EXE 5309..53c6 (updates), bba0..bc5e (drawing), 66db..672b (load).
var drips: Array[Dictionary] = []
var frames: Array[int] = [0,0,0,0,0,0,0,0,0,0]

func configure(positions: Array) -> void:
	drips.clear()
	for i in range(positions.size()):
		var source: Dictionary = positions[i]
		var origin: int = int(source.pos[1] * 2) - 2
		drips.append({"x":int(source.pos[0] * 2), "y":origin, "origin_y":origin,
			"max_y":int(source.max_y), "frame":frames[i]})

func step(gx: int, gy: int, difficulty: int) -> bool:
	var hit := false
	for i in range(drips.size()):
		var drip: Dictionary = drips[i]
		drip.y += 1
		if drip.frame == 0:
			drip.frame = 1
			drip.y += 2
		if drip.y > drip.max_y:
			drip.y = drip.origin_y
			drip.frame = 0
		if difficulty != 0 and drip.x > gx and drip.x < gx + 3 and drip.y < gy - 1 and drip.y > gy - 4:
			drip.frame = 2
			hit = true
		frames[i] = drip.frame
	return hit

func draws(camera_x: int, camera_y: int) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for drip in drips:
		if drip.x > camera_x and drip.x < camera_x + 36 and drip.y > camera_y and drip.y < camera_y + 19:
			result.append({"position":Vector2i(drip.x * 8,drip.y * 8), "frame":drip.frame})
	return result

func snapshot() -> Array:
	return drips.duplicate(true)
