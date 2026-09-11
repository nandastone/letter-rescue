extends Area2D

var is_locked: bool = true
var original_frame: int = 0
var original_bonus_sprite: Sprite2D

signal player_entered_door

func _ready() -> void:
	body_entered.connect(_on_body_entered)
	update_visual()

func unlock() -> void:
	is_locked = false
	update_visual()

func lock() -> void:
	is_locked = true
	update_visual()

func update_visual() -> void:
	if "--original-rules" in LaunchArgs.user_args():
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
		$Label.hide()
		return
	if is_locked:
		$Sprite2D.modulate = Color(0.5, 0.2, 0.2, 1.0)
		$Label.text = "X"
	else:
		$Sprite2D.modulate = Color(0.2, 0.8, 0.2, 1.0)
		$Label.text = ">"
		# Pulsing animation to draw attention.
		var tween := create_tween().set_loops()
		tween.tween_property($Sprite2D, "modulate:a", 0.6, 0.5)
		tween.tween_property($Sprite2D, "modulate:a", 1.0, 0.5)

func _on_body_entered(body: Node2D) -> void:
	if "--original-rules" in LaunchArgs.user_args():
		return # Raw 8px contact runs in the original gameplay update.
	if body is CharacterBody2D and body.has_method("die") and not is_locked:
		player_entered_door.emit()

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
