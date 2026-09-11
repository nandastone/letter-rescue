extends RefCounted
## WR1.EXE 247ae..248e0 and 24b67..24e23: DOS time -> C timestamp -> srand.
## The bundled runtime defaults to EST/EDT and its historical April/October rule.
const MONTH_DAYS := [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
const MONTH_START := [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]

static func seed_from_dos_time(date: Dictionary, tz: String = "") -> int:
	return timestamp(date, tz) & 0xffff

static func timestamp(date: Dictionary, tz: String = "") -> int:
	var years: int = int(date.year) - 1980
	var days: int = int(date.day) - 1
	for month in range(int(date.month) - 1):
		days += MONTH_DAYS[month]
	if int(date.month) > 2 and int(date.year) % 4 == 0:
		days += 1
	var zone := _timezone(tz)
	var hour: int = int(date.hour)
	if zone.daylight and _daylight(int(date.year), days, hour):
		hour -= 1
	var result: int = 0x12cea600 + int(zone.offset)
	result += (years >> 2) * 0x7861f80 + (years & 3) * 0x1e13380
	if years & 3:
		result += 86400
	result += (days * 24 + hour) * 3600 + int(date.minute) * 60 + int(date.second)
	return result & 0xffffffff

static func _letter(c: String) -> bool:
	return c >= "A" and c <= "Z" or c >= "a" and c <= "z"

static func _digit(c: String) -> bool:
	return c >= "0" and c <= "9"

static func _timezone(tz: String) -> Dictionary:
	var fallback := {"offset": 18000, "daylight": true}
	if tz.length() < 4:
		return fallback
	for i in range(3):
		if not _letter(tz[i]):
			return fallback
	var start := 3
	var sign_value := 1
	if tz[start] in ["+", "-"]:
		if tz[start] == "-":
			sign_value = -1
		start += 1
	if start >= tz.length() or not _digit(tz[start]):
		return fallback
	var hours := 0
	while start < tz.length() and _digit(tz[start]):
		hours = (hours * 10 + int(tz[start])) & 0xffffffff
		start += 1
	var daylight := false
	# The source scans for a three-letter daylight name after the numeric offset.
	while start < tz.length():
		if _letter(tz[start]):
			daylight = start + 2 < tz.length() and _letter(tz[start + 1]) and _letter(tz[start + 2])
			break
		start += 1
	return {"offset": hours * sign_value * 3600, "daylight": daylight}

static func _daylight(year: int, days: int, hour: int) -> bool:
	var adjusted := days
	if days >= 59 and year % 4 == 0:
		adjusted -= 1
	var month := 0
	while MONTH_START[month] <= adjusted:
		month += 1
	if month < 4 or month > 10:
		return false
	if month != 4 and month != 10:
		return true
	var boundary: int = MONTH_START[month]
	if month == 4 and year > 1986:
		boundary = MONTH_START[month - 1] + 7
	if year % 4 != 0:
		boundary -= 1
	var weekday: int = (365 * (year - 1970) + ((year - 1969) >> 2) + boundary + 4) & 0xffff
	boundary -= weekday % 7
	if month == 4:
		return days > boundary or days == boundary and hour >= 2
	return days < boundary or days == boundary and hour <= 1
