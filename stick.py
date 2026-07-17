import stickCommon as sc

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
        self.deadzoneMagnitude = deadzone.deadzoneMagnitude

    def setXHigh(self, xHigh):
        value = sc.getStickValue(xHigh)

        if value is not None:
            self.xHigh = value

    def setXLow(self, xLow):
        value = sc.getStickValue(xLow)

        if value is not None:
            self.xLow = value

    def setYHigh(self, yHigh):
        value = sc.getStickValue(yHigh)

        if value is not None:
            self.yHigh = value

    def setYLow(self, yLow):
        value = sc.getStickValue(yLow)

        if value is not None:
            self.yLow = value

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
