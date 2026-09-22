extends RefCounted
class_name Episode
## Content selection is independent of Legacy/Letter Rescue presentation.
## Episode 1 retains its original resource paths and save directory.

const NAMES := ["The Story Begins", "Gruzzled Caves", "The Haunted House"]
static var current: int = _initial_episode()
static var _manifest: Dictionary = {}

static func _initial_episode() -> int:
	var args := LaunchArgs.user_args()
	var option := args.find("--episode")
	if option >= 0 and option + 1 < args.size():
		return clampi(int(args[option + 1]), 1, 3)
	return 1

static func select(number: int) -> void:
	assert(number >= 1 and number <= 3)
	current = number
	_manifest.clear()

static func level_count() -> int:
	return 15 if current == 1 else 20

static func title() -> String:
	return NAMES[current - 1]

static func data_path(filename: String) -> String:
	return ("res://data/wr1/" if current == 1 else "res://data/episodes/wr%d/" % current) + filename

static func manifest() -> Dictionary:
	if _manifest.is_empty() and current != 1:
		_manifest = JSON.parse_string(FileAccess.get_file_as_string(data_path("episode.json")))
	return _manifest

static func level_path(number: int) -> String:
	return ("res://data/levels/" if current == 1 else data_path("levels/")) + "level_%02d.json" % number

static func rules_path(number: int) -> String:
	return data_path(("" if current == 1 else "rules/") + "level_%02d.json" % number)

static func art(name: String) -> String:
	name = name.to_upper()
	if current == 1:
		return "res://assets/extracted/wr1_1_png/" + name + ".png"
	return "res://assets/episodes/wr%d/art/%s.png" % [current, name.replace("WR1.", "WR%d." % current)]

static func picture(word: String, frame: int) -> String:
	var root := "res://assets/extracted/wr1_2_png/" if current == 1 else "res://assets/episodes/wr%d/pictures/" % current
	return root + "%s%s.WR%d.png" % [word.to_upper(), "2" if frame == 1 else "", current]

static func tileset(number: int) -> String:
	return "res://assets/tiles/tileset_back%d.png" % number if current == 1 else art("BACK%d.WR" % number)

static func backdrop(number: int) -> String:
	return "res://assets/tiles/backdrop_%d.png" % number if current == 1 else art("DROP%d.WR" % number)

static func sprite(name: String) -> String:
	if current != 1 and manifest().sprites.has(name):
		return "res://assets/episodes/wr%d/sprites/%s.png" % [current, name]
	return "res://assets/sprites/" + name + ".png"

static func save_extension() -> String:
	return ".wr%d" % current
