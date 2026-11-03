import math

# Shared validation limits for global settings.
STICK_VALUE_MIN = 1
STICK_VALUE_MAX = 65535
KB_MODE_VALUE_MIN = 1
KB_MODE_VALUE_MAX = 127

# Profile lifecycle limits.
MAX_PROFILE_COUNT = 32
MAX_PROFILE_NAME_BYTES = 64

# TuFFpad matrix layout: exactly 20 keys. Waveshare has no matrix and does
# not apply this limit.
MAX_PROFILE_KEY_COUNT = 20

def magnitude(x, y):
    return math.sqrt(x * x + y * y)

def constrain(x, a, b):
    if x < a:
        x = a
    elif x > b:
        x = b

    return x

def rangeMap(x, inMin, inMax, outMin, outMax):
    return (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin

def getProfileNameValue(value):
    # Profile names must be non-empty strings within the UTF-8 byte limit so
    # stored names stay unambiguous for management-app lookups.
    if not isinstance(value, str) or len(value) == 0:
        return None

    if len(value.encode("utf-8")) > MAX_PROFILE_NAME_BYTES:
        return None

    return value

def getIntValue(value, minValue, maxValue):
    # Accept real integers, integer-valued floats, and integer strings.
    # Reject Booleans, fractional floats, and everything else so malformed
    # input can never become a stored setting.
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        number = value
    elif isinstance(value, float):
        try:
            number = int(value)
        except (TypeError, ValueError, OverflowError):
            return None

        if number != value:
            return None
    elif isinstance(value, str):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None
    else:
        return None

    if number < minValue or number > maxValue:
        return None

    return number

def getStickValue(value):
    return getIntValue(value, STICK_VALUE_MIN, STICK_VALUE_MAX)

def getBoundaryValue(value, otherLimit, isLower):
    # Validate a raw stick boundary (integer 1..65535) and require it to
    # stay on the correct side of the axis's other current limit so the
    # stick math can never see equal or reversed limits.
    number = getStickValue(value)

    if number is None:
        return None

    if isLower and number >= otherLimit:
        return None

    if not isLower and number <= otherLimit:
        return None

    return number

def getOrientationValue(value):
    # Orientation must be {"axis": 0 or 1, "reverse": JSON Boolean}. Parse
    # the whole candidate so a failure can never partially update either
    # field. "false" strings and axis strings are rejected.
    if not isinstance(value, dict):
        return None

    if "axis" not in value or "reverse" not in value:
        return None

    axis = value["axis"]
    reverse = value["reverse"]

    if isinstance(axis, bool) or not isinstance(axis, int):
        return None

    if axis != 0 and axis != 1:
        return None

    if not isinstance(reverse, bool):
        return None

    return {"axis": axis, "reverse": reverse}
