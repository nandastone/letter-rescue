extends CharacterBody2D

# Tuned for 8x8 collision tiles at 320x200 native res.
@export var speed: float = 120.0
@export var climb_speed: float = 80.0
@export var jump_force: float = -220.0
@export var gravity: float = 500.0
@export var max_fall_speed: float = 300.0

# Mid-air control (original Word Rescue allowed full air control).
@export var air_control: float = 1.0

var facing_right: bool = true
var is_dead: bool = false
var on_ladder: bool = false
var coyote_timer: float = 0.0
const COYOTE_TIME: float = 0.08

signal died

func _ready() -> void:
	$Hurtbox.body_entered.connect(_on_hurtbox_body_entered)

func _on_hurtbox_body_entered(body: Node2D) -> void:
	if body is CharacterBody2D and body.has_method("get_slimed") and not body.is_slimed:
		die()

func _is_on_platform_tile() -> bool:
	# Check if player overlaps a one-way platform tile below feet.
	var space_state := get_world_2d().direct_space_state
	var query := PhysicsRayQueryParameters2D.create(
		global_position,
		global_position + Vector2(0, 4),
		16  # Platform layer (layer 5).
	)
	return not space_state.intersect_ray(query).is_empty()

func _is_near_ladder() -> bool:
	# Check if a platform tile exists near the player (center or feet).
	var platform_layer: TileMapLayer = get_node_or_null("../PlatformTileMapLayer")
	if not platform_layer:
		return false
	# Check at center and at feet.
	for offset in [Vector2(0, -8), Vector2(0, 0), Vector2(0, -16)]:
		var cell := platform_layer.local_to_map(global_position + offset)
		if platform_layer.get_cell_source_id(cell) != -1:
			return true
	return false

func _physics_process(delta: float) -> void:
	if is_dead:
		return

	var vert_input := Input.get_axis("jump", "move_down")
	var direction := Input.get_axis("move_left", "move_right")

	# Enter ladder when pressing up or down near a platform tile.
	if not on_ladder and vert_input != 0 and _is_near_ladder():
		enter_ladder()

	# Ladder climbing: hold up/down to climb continuously.
	if on_ladder:
		velocity.y = vert_input * climb_speed
		velocity.x = direction * speed * 0.5

		# Jump off ladder.
		if Input.is_action_just_pressed("jump") and vert_input <= 0:
			exit_ladder()
			velocity.y = jump_force
			AudioManager.play("jump")

		# Leave ladder when reaching ground while going down.
		if is_on_floor() and vert_input > 0:
			exit_ladder()
		# Left the ladder area: boost up to clear the top, then exit.
		elif not _is_near_ladder():
			if vert_input < 0:
				velocity.y = -climb_speed
			exit_ladder()
	else:
		# Coyote time: track how long since last on floor.
		if is_on_floor():
			coyote_timer = COYOTE_TIME
		else:
			coyote_timer -= delta

		# Gravity.
		if not is_on_floor():
			velocity.y += gravity * delta
			velocity.y = min(velocity.y, max_fall_speed)

		# Jump (allowed on floor or within coyote time).
		if Input.is_action_just_pressed("jump") and coyote_timer > 0:
			coyote_timer = 0.0
			velocity.y = jump_force
			AudioManager.play("jump")

		# Jump cut: releasing jump while rising cuts upward velocity.
		if Input.is_action_just_released("jump") and velocity.y < 0:
			velocity.y *= 0.4

		# Drop through one-way platforms.
		if Input.is_action_pressed("move_down") and is_on_floor() and _is_on_platform_tile():
			global_position.y += 2
			set_collision_mask_value(5, false)
			get_tree().create_timer(0.2).timeout.connect(_restore_platform_collision)

		# Horizontal movement (full control in air, matching original).
		var control := 1.0 if is_on_floor() else air_control
		velocity.x = direction * speed * control

	# Flip sprite.
	if direction > 0:
		facing_right = true
		$AnimatedSprite2D.flip_h = false
	elif direction < 0:
		facing_right = false
		$AnimatedSprite2D.flip_h = true

	# Animation.
	if on_ladder:
		if vert_input != 0 or direction != 0:
			$AnimatedSprite2D.play("run")
		else:
			$AnimatedSprite2D.play("idle")
	elif is_on_floor():
		if direction != 0:
			$AnimatedSprite2D.play("run")
		else:
			$AnimatedSprite2D.play("idle")
	else:
		if velocity.y < 0:
			$AnimatedSprite2D.play("jump")
		else:
			$AnimatedSprite2D.play("fall")

	move_and_slide()

	# Death pit: fall below map.
	if global_position.y > 1000:
		die()

func enter_ladder() -> void:
	on_ladder = true
	velocity.y = 0
	# Disable platform collision so player can climb through.
	set_collision_mask_value(5, false)

func exit_ladder() -> void:
	on_ladder = false
	# Re-enable platform collision after a short delay so the player
	# can clear the top of the platform before it becomes solid again.
	get_tree().create_timer(0.15).timeout.connect(_restore_platform_collision)

func die() -> void:
	if is_dead:
		return
	is_dead = true
	velocity = Vector2.ZERO
	$AnimatedSprite2D.play("death")
	died.emit()

func _restore_platform_collision() -> void:
	set_collision_mask_value(5, true)

func revive(spawn_position: Vector2) -> void:
	is_dead = false
	global_position = spawn_position
	velocity = Vector2.ZERO
	$AnimatedSprite2D.play("idle")
