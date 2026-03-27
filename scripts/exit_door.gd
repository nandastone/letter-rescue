extends Area2D

var is_locked: bool = true

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
	if body is CharacterBody2D and body.has_method("die") and not is_locked:
		player_entered_door.emit()
