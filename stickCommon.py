import math

def magnitude(x, y):
    return math.sqrt(x * x + y * y)

def normalize(magnitude, x, y):
    return [x / magnitude, y / magnitude]

def constrain(x, a, b):
    if x < a:
        x = a
    elif x > b:
        x = b

    return x

def rangeMap(x, inMin, inMax, outMin, outMax):
    return (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin

def getStickValue(value):
    try:
        value = int(value)
    except:
        value = None

    if value is not None and (value < 1 or value > 65535):
        value = None

    return value
