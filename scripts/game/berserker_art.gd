extends RefCounted
## Authored player atlases plus small, code-native transient effects.
static var players := {}
# Pixelorama export: 26 native WR1 poses, each 48x40, body padded by (12,8).
# Kept separate from the legacy generated atlas builder's output.
const BOY_SHEET := "res://assets/sprites/berserker_boy_handdrawn.png"
const BOY_LEFT_POSES := [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 24]
# Barrel tip in frame-local pixels (before centering / optional mirroring).
const BOY_MUZZLES := [
	Vector2(43,26.5), Vector2(43,26.5), Vector2(43,26.5),
	Vector2(45,26.5), Vector2(45,24.5), Vector2(45,26.5),
	Vector2(45,26.5), Vector2(45,24.5), Vector2(45,26.5),
	Vector2(41,29.5), Vector2(45,17.5), Vector2(48,17.5),
	Vector2(5,26.5), Vector2(3,26.5), Vector2(3,24.5),
	Vector2(3,26.5), Vector2(3,26.5), Vector2(3,24.5),
	Vector2(3,26.5), Vector2(7,29.5), Vector2(3,17.5),
	Vector2(0,17.5), Vector2(45,26.5), Vector2(48,17.5),
	Vector2(3,12.5), Vector2(45,12.5)]

static func player(character: String) -> Texture2D:
	if not players.has(character):
		players[character] = load(BOY_SHEET if character == "boy" else "res://assets/sprites/berserker_%s.png" % character)
	return players[character]

static func frame_count(character: String) -> int:
	return 26 if character == "boy" else 28

static func flip_player(character: String, frame: int, facing_left: bool) -> bool:
	# Native left poses must not be mirrored a second time. Front/back poses
	# carry a right-pointing gun; turn those (and direction changes mid-jump).
	return facing_left != (frame in BOY_LEFT_POSES) if character == "boy" else facing_left

static func muzzle_offset(character: String, frame: int, flipped: bool) -> Vector2:
	var at: Vector2 = BOY_MUZZLES[frame] - Vector2(24,20) if character == "boy" else Vector2(20, -8 if frame == 26 else 0)
	if flipped:
		at.x = -at.x
	return at

static func muzzle_flash() -> Texture2D:
	return _pixels([
		"    o       ",
		"  oyyo  o   ",
		"oyywwyyyo   ",
		"yywwwwwwyyyo",
		"oyywwyyyo   ",
		"  oyyo  o   ",
		"    o       "], {"o":Color("#ff6600"),"y":Color("#ffff55"),"w":Color.WHITE})

static func shell() -> Texture2D:
	return _pixels(["yrrr","YRRR"], {"y":Color("#ffaa00"),"Y":Color("#ffff55"),"r":Color("#aa0000"),"R":Color("#ff5555")})

static func smoke() -> Texture2D:
	return _pixels([" gg ","gggg"," gg "], {"g":Color(0.75,0.75,0.75,0.55)})

static func gore(kind: int, index: int) -> Texture2D:
	var skin: Color = [Color("#aa00aa"),Color("#55ff55"),Color("#ff5555"),Color("#5555ff")][kind % 4]
	return _pixels([" ss","sbs","ss "] if index % 2 else ["ss","bs"], {"s":skin,"b":Color("#aa0000")})

static func _pixels(rows: Array, palette: Dictionary) -> Texture2D:
	var result := Image.create(rows[0].length(), rows.size(), false, Image.FORMAT_RGBA8)
	result.fill(Color.TRANSPARENT)
	for y in range(rows.size()):
		for x in range(rows[y].length()):
			if palette.has(rows[y][x]):
				result.set_pixel(x,y,palette[rows[y][x]])
	return ImageTexture.create_from_image(result)
