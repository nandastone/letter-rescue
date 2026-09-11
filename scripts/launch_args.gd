extends RefCounted
class_name LaunchArgs

# User command-line args (after `--`). Web builds have no command line, so they
# always run the original rules with Clear Text, and read optional flags from
# the page URL, e.g. index.html?pixel-text&skip-intro.

const WEB_FLAGS := ["skip-intro", "mute-original-audio"]

static var _args: PackedStringArray = _read()

static func user_args() -> PackedStringArray:
	return _args

static func _read() -> PackedStringArray:
	var args := OS.get_cmdline_user_args()
	if not OS.has_feature("web"):
		return args
	args.append("--original-rules")
	var keys := str(JavaScriptBridge.eval("[...new URLSearchParams(location.search).keys()].join(' ')")).split(" ")
	# Installed web apps launch from the manifest's start URL, which drops the
	# query string, so the readable text has to be the default rather than a flag.
	if not "pixel-text" in keys:
		args.append("--clear-text")
	for flag in WEB_FLAGS:
		if flag in keys:
			args.append("--" + flag)
	return args
