extends Node2D

@export var drip_speed: float = 60.0
@export var drip_interval: float = 2.5

var origin_pos: Vector2 = Vector2.ZERO
var max_y: float = 0.0
var drip_active: bool = false

@onready var drip_sprite: Sprite2D = $DripSprite
@onready var drip_area: Area2D = $DripArea
@onready var timer: Timer = $Timer

func _ready() -> void:
	origin_pos = global_position
	drip_sprite.visible = false
	drip_area.body_entered.connect(_on_drip_hit)
	timer.wait_time = drip_interval + randf() * 1.0
	timer.timeout.connect(_start_drip)
	timer.start()

func setup(max_fall_y: float) -> void:
	max_y = max_fall_y

func _start_drip() -> void:
	drip_active = true
	drip_sprite.visible = true
	drip_sprite.position = Vector2.ZERO
	drip_area.position = Vector2.ZERO

func _process(delta: float) -> void:
	if not drip_active:
		return

	drip_sprite.position.y += drip_speed * delta
	drip_area.position = drip_sprite.position

	# Reset when drip falls past max distance.
	if drip_sprite.position.y > max_y * 16:
		_reset_drip()

func _reset_drip() -> void:
	drip_active = false
	drip_sprite.visible = false
	drip_sprite.position = Vector2.ZERO
	drip_area.position = Vector2.ZERO
	timer.wait_time = drip_interval + randf() * 1.0
	timer.start()

func _on_drip_hit(body: Node2D) -> void:
	if body is CharacterBody2D and body.has_method("die"):
		# Only lethal on medium/hard.
		if GameManager.current_difficulty != GameManager.Difficulty.EASY:
			body.die()
		_reset_drip()
