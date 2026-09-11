extends RefCounted
class_name LaunchArgs

# User command-line args (after `--`). Web builds have no command line, so they
# always run the original rules and read optional flags from the page URL,
# e.g. index.html?clear-text&skip-intro.

const WEB_FLAGS := ["clear-text", "skip-intro", "mute-original-audio"]

static var _args: PackedStringArray = _read()

static func user_args() -> PackedStringArray:
	return _args

static func _read() -> PackedStringArray:
	var args := OS.get_cmdline_user_args()
	if not OS.has_feature("web"):
		return args
	args.append("--original-rules")
	var keys := str(JavaScriptBridge.eval("[...new URLSearchParams(location.search).keys()].join(' ')")).split(" ")
	for flag in WEB_FLAGS:
		if flag in keys:
			args.append("--" + flag)
	return args
