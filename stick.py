import stickCommon as sc
from stickDeadzone import MAX_DEADZONE_MAGNITUDE

class Stick:
    def __init__(self):
        self.deadzone = None
        self.xHigh = 52535
        self.xLow = 15000
        self.yHigh = 52535
        self.yLow = 15000
        self.mappedDeadzone = 0
        self.deadzoneMagnitude = 0
        # Reused every call so the main loop doesn't allocate.
        self.result = [0, 0]

    def setDeadzone(self, deadzone):
        self.deadzone = deadzone
        self.mappedDeadzone = sc.rangeMap(deadzone.getDeadzone(), 0, 32768, 0.0, 1.0)
        # Clamp defensively; deadzone.deadzoneMagnitude must stay below 1.0
        # so the scaling denominator can never reach zero or go negative.
        self.deadzoneMagnitude = sc.constrain(deadzone.deadzoneMagnitude, 0.0, MAX_DEADZONE_MAGNITUDE)

    def setXHigh(self, xHigh):
        value = sc.getBoundaryValue(xHigh, self.xLow, False)

        if value is None:
            return False

        self.xHigh = value
        return True

    def setXLow(self, xLow):
        value = sc.getBoundaryValue(xLow, self.xHigh, True)

        if value is None:
            return False

        self.xLow = value
        return True

    def setYHigh(self, yHigh):
        value = sc.getBoundaryValue(yHigh, self.yLow, False)

        if value is None:
            return False

        self.yHigh = value
        return True

    def setYLow(self, yLow):
        value = sc.getBoundaryValue(yLow, self.yHigh, True)

        if value is None:
            return False

        self.yLow = value
        return True

    def doStickCalculations(self, analogX, analogY, constrainDeadzone = False):
        result = self.result
        xStick = analogX.value
        yStick = analogY.value

        if constrainDeadzone:
            x = sc.constrain(sc.rangeMap(xStick, self.xLow, self.xHigh, -1.0, 1.0), -1.0, 1.0)
            y = sc.constrain(sc.rangeMap(yStick, self.yLow, self.yHigh, -1.0, 1.0), -1.0, 1.0)
            magnitude = sc.magnitude(x, y)

            if magnitude > self.deadzoneMagnitude:
                factor = (magnitude - self.deadzoneMagnitude) / (1 - self.deadzoneMagnitude)
                mappedX = sc.rangeMap(x / magnitude * factor, -1.0, 1.0, -127, 127)
                mappedY = sc.rangeMap(y / magnitude * factor, -1.0, 1.0, -127, 127)
                xStick = int(sc.constrain(mappedX, -127, 127))
                yStick = int(sc.constrain(mappedY, -127, 127))
            else:
                xStick = 0
                yStick = 0

        result[0] = xStick
        result[1] = yStick
        return result
