extends Area2D

# Generic collectible: slime_bucket, book, or letter.

var type: String = ""
var data: String = ""
var original_tileset: Texture2D

signal collected(collectible: Area2D)

func _ready() -> void:
	body_entered.connect(_on_body_entered)
	if "--original-rules" in OS.get_cmdline_user_args():
		return
	# Gentle bobbing animation.
	var tween := create_tween().set_loops()
	tween.tween_property(self, "position:y", position.y - 1.5, 0.6).set_trans(Tween.TRANS_SINE)
	tween.tween_property(self, "position:y", position.y + 1.5, 0.6).set_trans(Tween.TRANS_SINE)

func setup(collectible_type: String, collectible_data: String = "") -> void:
	type = collectible_type
	data = collectible_data
	update_visual()

func update_visual() -> void:
	match type:
		"slime_bucket":
			$Sprite2D.texture = preload("res://assets/sprites/slime_bucket.png")
			if "--original-rules" in OS.get_cmdline_user_args():
				# Native level loader stamps opaque tile238 at the raw tile origin.
				var atlas := AtlasTexture.new()
				atlas.atlas = original_tileset
				atlas.region = Rect2(288, 176, 16, 16)
				$Sprite2D.texture = atlas
				$Sprite2D.centered = false
				$Sprite2D.position = Vector2.ZERO
			$Sprite2D.visible = true
			$Label.visible = false
		"book":
			# Book visual comes from BG tile 239 (wr1.exe stamps this at level
			# load). Sprite-entity stays in place as an invisible pickup
			# hitbox so collection still works.
			$Sprite2D.visible = false
			$Label.visible = false
			if preload("res://scripts/wr1_clear_text.gd").enabled() and not has_node("ClearBook"):
				var cover := ColorRect.new()
				cover.name = "ClearBook"
				cover.position = Vector2(1,5)
				cover.size = Vector2(12,6)
				cover.color = Color8(255,85,255)
				cover.visibility_layer = 2
				cover.mouse_filter = Control.MOUSE_FILTER_IGNORE
				add_child(cover)
				preload("res://scripts/wr1_clear_text.gd").label(cover, Rect2(-1,-2,14,10), "book", Color8(255,255,85), 5)
		"letter":
			if "--original-rules" in OS.get_cmdline_user_args():
				var atlas := AtlasTexture.new()
				atlas.atlas = preload("res://assets/sprites/wr1_letters.png")
				var index: int = data.to_lower().unicode_at(0) - 97
				atlas.region = Rect2((index % 9) * 16, (index / 9) * 16, 16, 16)
				$Sprite2D.texture = atlas
				$Sprite2D.centered = false
				$Sprite2D.position = Vector2.ZERO
				$Sprite2D.show()
				$Label.hide()
				if preload("res://scripts/wr1_clear_text.gd").enabled() and not has_node("ClearLetter"):
					preload("res://scripts/wr1_clear_text.gd").configure_letter(self)
				return
			# Letters are large yellow text with no background, matching original.
			$Sprite2D.visible = false
			$Label.text = data.to_upper()
			$Label.visible = true
			$Label.add_theme_color_override("font_color", Color(1.0, 1.0, 0.33))
			$Label.add_theme_font_size_override("font_size", 16)

func _on_body_entered(body: Node2D) -> void:
	if "--original-rules" in OS.get_cmdline_user_args():
		return # Raw-grid contact is handled at the original logical update.
	if body is CharacterBody2D and body.has_method("die"):
		AudioManager.play("collect")
		collected.emit(self)
		_handle_collection()
		queue_free()

func _handle_collection() -> void:
	match type:
		"slime_bucket":
			var slime_system := get_node_or_null("/root/Game/SlimeSystem")
			if slime_system:
				slime_system.add_slime()
			GameManager.add_score(5)
		"book":
			GameManager.add_score(10)
		"letter":
			var mystery := get_node_or_null("/root/Game/MysteryWord")
			if mystery:
				mystery.try_collect(data)
	# Always update score HUD after collection.
	var hud = get_node_or_null("/root/Game/HUD")
	if hud:
		hud.update_score(GameManager.score)
