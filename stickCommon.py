import math

# Shared validation limits for global settings.
STICK_VALUE_MIN = 1
STICK_VALUE_MAX = 65535
KB_MODE_VALUE_MIN = 1
KB_MODE_VALUE_MAX = 127

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
