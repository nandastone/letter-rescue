extends RefCounted
class_name LaunchArgs

# User command-line args (after `--`), plus the flags each mode implies.
# The default is the new game, which always uses Clear Text. `--legacy` runs the
# pixel-exact original; add `--clear-text` there for readable text.
# Web builds have no command line, so they read ?legacy, ?pixel-text,
# ?skip-intro and ?mute-original-audio from the page URL.

const WEB_FLAGS := ["legacy", "skip-intro", "mute-original-audio", "square-pixels"]

static var _args: PackedStringArray = _read()

static func user_args() -> PackedStringArray:
	return _args

## True for the pixel-exact original game, which the demo parity suite checks.
static func legacy() -> bool:
	return "--legacy" in _args

## The original's 320x200 filled a 4:3 monitor, so its pixels were 1.2x taller
## than wide, and its round objects are drawn wider than tall to suit. The
## default game reproduces that; legacy keeps the square pixels its captures use.
static func square_pixels() -> bool:
	return legacy() or "--square-pixels" in _args

static func _read() -> PackedStringArray:
	var args := OS.get_cmdline_user_args()
	# The legacy export ships without the default game's scripts, so it always
	# runs legacy (see the "legacy" custom feature in export_presets.cfg).
	if OS.has_feature("legacy") and not "--legacy" in args:
		args.append("--legacy")
	var pixel_text := "--legacy" in args
	if OS.has_feature("web"):
		var keys := str(JavaScriptBridge.eval("[...new URLSearchParams(location.search).keys()].join(' ')")).split(" ")
		for flag in WEB_FLAGS:
			if flag in keys:
				args.append("--" + flag)
		# Installed web apps launch from the manifest's start URL, which drops the
		# query string, so readable text stays the default even in legacy mode.
		pixel_text = "--legacy" in args and "pixel-text" in keys
	if not pixel_text and not "--clear-text" in args:
		args.append("--clear-text")
	return args
