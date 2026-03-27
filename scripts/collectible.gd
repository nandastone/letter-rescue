extends Area2D

# Generic collectible: slime_bucket, book, or letter.

var type: String = ""
var data: String = ""

signal collected(collectible: Area2D)

func _ready() -> void:
	body_entered.connect(_on_body_entered)
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
			$Sprite2D.visible = true
			$Label.visible = false
		"book":
			$Sprite2D.texture = preload("res://assets/sprites/book.png")
			$Sprite2D.visible = true
			$Label.visible = false
		"letter":
			# Letters are large yellow text with no background, matching original.
			$Sprite2D.visible = false
			$Label.text = data.to_upper()
			$Label.visible = true
			$Label.add_theme_color_override("font_color", Color(1.0, 1.0, 0.33))
			$Label.add_theme_font_size_override("font_size", 16)

func _on_body_entered(body: Node2D) -> void:
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
