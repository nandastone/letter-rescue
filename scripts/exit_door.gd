extends Node2D

var original_frame: int = 0
var original_bonus_sprite: Sprite2D

func _ready() -> void:
	update_visual()

func update_visual() -> void:
	var args := LaunchArgs.user_args()
	var option := args.find("--character")
	var boy: bool = option >= 0 and option + 1 < args.size() and args[option + 1] == "boy"
	var atlas := AtlasTexture.new()
	atlas.atlas = preload("res://assets/extracted/wr1_1_png/STATIC.WR.png")
	atlas.region = Rect2(16 + 32 * original_frame, 33 if boy else 73, 32, 40)
	$Sprite2D.texture = atlas
	$Sprite2D.centered = false
	$Sprite2D.position = Vector2.ZERO
	$Sprite2D.modulate = Color.WHITE

func present_original_frame(frame: int, bonus: bool, flash: int) -> void:
	original_frame = frame
	z_index = 20
	update_visual()
	if bonus:
		if original_bonus_sprite == null:
			original_bonus_sprite = Sprite2D.new()
			original_bonus_sprite.centered = false
			add_child(original_bonus_sprite)
		var raster := Image.create(64, 16, false, Image.FORMAT_RGBA8)
		raster.fill(Color.TRANSPARENT)
		var ink := Color8(255,85,255) if (frame + flash) % 2 == 0 else Color8(255,255,85)
		preload("res://scripts/wr1_text.gd").draw(raster, "Bonus #2", Vector2i.ZERO, ink, Color.TRANSPARENT)
		preload("res://scripts/wr1_text.gd").draw(raster, "500", Vector2i(20,8), ink, Color.TRANSPARENT)
		original_bonus_sprite.texture = ImageTexture.create_from_image(raster)
		original_bonus_sprite.position = Vector2(-20,-8)
		preload("res://scripts/wr1_clear_text.gd").reward(original_bonus_sprite, raster, "Bonus #2", "500", ink)
