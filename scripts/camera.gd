extends Camera2D

@export var target: NodePath
@export var smoothing: float = 8.0

var target_node: Node2D
var original_projection: bool = false

func apply_original(state: RefCounted) -> void:
	original_projection = true
	position_smoothing_enabled = false
	limit_left = -1000000
	limit_top = -1000000
	limit_right = 1000000
	limit_bottom = 1000000
	# Screen projection = world + (16,32) - 8*original_camera.
	global_position = Vector2(144 + state.camera_x * 8, 68 + state.camera_y * 8)
	force_update_scroll()

func _ready() -> void:
	if target:
		target_node = get_node(target)

func _process(delta: float) -> void:
	if original_projection:
		return
	if target_node:
		global_position = global_position.lerp(target_node.global_position, smoothing * delta)
