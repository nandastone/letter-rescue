extends Camera2D

@export var target: NodePath
@export var smoothing: float = 8.0

var target_node: Node2D

func _ready() -> void:
	if target:
		target_node = get_node(target)

func _process(delta: float) -> void:
	if target_node:
		global_position = global_position.lerp(target_node.global_position, smoothing * delta)
