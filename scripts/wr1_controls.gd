extends RefCounted
## DOS set-1 make codes persisted by the original five-key selector.
const ACTIONS := ["move_right", "move_left", "jump", "move_down", "use_slime"]
const DEFAULTS := [77, 75, 72, 80, 57]
static func key_for_scan(scan: int) -> int:
	var special := {1:KEY_ESCAPE, 14:KEY_BACKSPACE, 15:KEY_TAB, 28:KEY_ENTER,
		29:KEY_CTRL, 42:KEY_SHIFT, 54:KEY_SHIFT, 55:KEY_KP_MULTIPLY, 56:KEY_ALT, 57:KEY_SPACE, 58:KEY_CAPSLOCK,
		59:KEY_F1, 60:KEY_F2, 61:KEY_F3, 62:KEY_F4, 63:KEY_F5, 64:KEY_F6,
		65:KEY_F7, 66:KEY_F8, 67:KEY_F9, 68:KEY_F10, 69:KEY_NUMLOCK, 70:KEY_SCROLLLOCK, 71:KEY_HOME,
		72:KEY_UP, 73:KEY_PAGEUP, 74:KEY_KP_SUBTRACT, 75:KEY_LEFT, 76:KEY_KP_5, 77:KEY_RIGHT, 78:KEY_KP_ADD, 79:KEY_END,
		80:KEY_DOWN, 81:KEY_PAGEDOWN, 82:KEY_INSERT, 83:KEY_DELETE, 87:KEY_F11, 88:KEY_F12}
	if special.has(scan):
		return special[scan]
	for row in [[2, "1234567890-="], [16, "QWERTYUIOP[]"], [30, "ASDFGHJKL;'`"], [43, "\\ZXCVBNM,./"]]:
		if scan >= row[0] and scan < row[0] + row[1].length():
			return row[1].unicode_at(scan-row[0])
	return 0

static func scan_for_key(key: int) -> int:
	for scan in range(1, 89):
		if scan != 42 and key_for_scan(scan) == key:
			return scan
	return -1

static func apply(scancodes: Array) -> void:
	# ISR c762..c7c8 checks Up, Down, Right, Left, Slime, then falls through
	# to the original defaults. Only the first matching custom binding wins.
	var bindings := {72:"jump",80:"move_down",77:"move_right",75:"move_left",
		57:"use_slime",56:"use_slime",29:"jump"}
	var seen: Array = []
	for i in [2,3,0,1,4]:
		var scan := int(scancodes[i])
		if scan not in seen:
			bindings[scan] = ACTIONS[i]
			seen.append(scan)
	for action in ACTIONS: InputMap.action_erase_events(action)
	for scan in bindings:
		if key_for_scan(scan) == 0: continue
		var event := InputEventKey.new()
		event.physical_keycode = key_for_scan(scan)
		InputMap.action_add_event(bindings[scan], event)
