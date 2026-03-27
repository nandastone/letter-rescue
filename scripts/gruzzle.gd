extends CharacterBody2D

@export var patrol_speed: float = 20.0
@export var chase_speed: float = 40.0
@export var gravity: float = 500.0
@export var detection_range: float = 80.0

enum State { PATROL, CHASE }

var state: State = State.PATROL
var direction: float = 1.0
var player: CharacterBody2D = null
var is_slimed: bool = false

signal hit_player(gruzzle: CharacterBody2D)

func _ready() -> void:
	# Apply difficulty speed multiplier.
	var multiplier := GameManager.get_gruzzle_speed_multiplier()
	patrol_speed *= multiplier
	chase_speed *= multiplier
	detection_range *= multiplier

	$AnimatedSprite2D.play("walk")

func set_player_reference(p: CharacterBody2D) -> void:
	player = p

func _physics_process(delta: float) -> void:
	if is_slimed:
		return

	# Gravity.
	if not is_on_floor():
		velocity.y += gravity * delta

	match state:
		State.PATROL:
			_patrol(delta)
		State.CHASE:
			_chase(delta)

	move_and_slide()

	# Check for wall and reverse.
	if is_on_wall():
		direction *= -1.0

	# Remove if fallen off map.
	if global_position.y > 1000:
		queue_free()
		return

	# Flip sprite to face movement direction.
	$AnimatedSprite2D.flip_h = direction < 0

func _patrol(_delta: float) -> void:
	velocity.x = direction * patrol_speed

	# Edge detection: use a raycast to check for floor ahead.
	if is_on_floor():
		var check_pos := global_position + Vector2(direction * 20, 20)
		var space_state := get_world_2d().direct_space_state
		var query := PhysicsRayQueryParameters2D.create(
			global_position + Vector2(direction * 8, 0),
			global_position + Vector2(direction * 8, 12),
			1  # World collision layer.
		)
		var result := space_state.intersect_ray(query)
		if result.is_empty():
			direction *= -1.0

	# Check if player is in detection range (medium/hard only).
	if player and GameManager.current_difficulty != GameManager.Difficulty.EASY:
		var dist := global_position.distance_to(player.global_position)
		if dist < detection_range:
			state = State.CHASE

func _chase(_delta: float) -> void:
	if player == null or player.is_dead:
		state = State.PATROL
		return

	var to_player := player.global_position - global_position
	direction = sign(to_player.x)
	velocity.x = direction * chase_speed

	# Lose interest if too far.
	if global_position.distance_to(player.global_position) > detection_range * 2.5:
		state = State.PATROL

func get_slimed() -> void:
	is_slimed = true
	velocity = Vector2.ZERO
	$AnimatedSprite2D.play("slimed")
	# Disappear after a short delay.
	var tween := create_tween()
	tween.tween_property($AnimatedSprite2D, "modulate:a", 0.0, 0.5)
	tween.tween_callback(queue_free)
