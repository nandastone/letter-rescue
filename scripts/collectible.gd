extends Node2D

# Display for an original-level pickup: slime_bucket, book, or letter. Contact
# runs on the raw attribute grid at the original logical update (game.gd).

var type: String = ""
var data: String = ""
var original_tileset: Texture2D

func setup(collectible_type: String, collectible_data: String = "") -> void:
	type = collectible_type
	data = collectible_data
	update_visual()

func update_visual() -> void:
	match type:
		"slime_bucket":
			# Native level loader stamps opaque tile238 at the raw tile origin.
			var atlas := AtlasTexture.new()
			atlas.atlas = original_tileset
			atlas.region = Rect2(288, 176, 16, 16)
			$Sprite2D.texture = atlas
			$Sprite2D.centered = false
			$Sprite2D.position = Vector2.ZERO
			$Sprite2D.visible = true
		"book":
			# Book visual comes from BG tile 239 (wr1.exe stamps this at level
			# load). Clear Text adds a readable cover over that tile.
			$Sprite2D.visible = false
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
			var atlas := AtlasTexture.new()
			atlas.atlas = preload("res://assets/sprites/wr1_letters.png")
			var index: int = data.to_lower().unicode_at(0) - 97
			atlas.region = Rect2((index % 9) * 16, (index / 9) * 16, 16, 16)
			$Sprite2D.texture = atlas
			$Sprite2D.centered = false
			$Sprite2D.position = Vector2.ZERO
			$Sprite2D.show()
			if preload("res://scripts/wr1_clear_text.gd").enabled() and not has_node("ClearLetter"):
				preload("res://scripts/wr1_clear_text.gd").configure_letter(self)
