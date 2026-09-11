extends SceneTree
## Reproduce a window-focus release between replay input delivery and gameplay.
class ReleaseInput extends Node:
	func _physics_process(_delta: float) -> void:
		if get_node("/root/InputReplay").current_input_frame == 60:
			for action in get_node("/root/InputReplay").ACTIONS:
				Input.action_release(action)

func _initialize() -> void:
	var release := ReleaseInput.new()
	release.process_physics_priority = -50 # Replay=-100, player=0.
	root.add_child.call_deferred(release)
