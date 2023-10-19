import stickCommon as sc
import math

class Stick:
    def __init__(self):
        self.deadzone = None
        self.xHigh = 52535
        self.xLow = 15000
        self.yHigh = 52535
        self.yLow = 15000
        self.mappedDeadzone = 0
        self.deadzoneMagnitude = 0

    def setDeadzone(self, deadzone):
        self.deadzone = deadzone
        self.mappedDeadzone = sc.rangeMap(deadzone.getDeadzone(), 0, 32768, 0.0, 1.0)
        self.deadzoneMagnitude = deadzone.deadzoneMagnitude

    def setXHigh(self, xHigh):
        self.xHigh = sc.getStickValue(xHigh)

    def setXLow(self, xLow):
        self.xLow = sc.getStickValue(xLow)

    def setYHigh(self, yHigh):
        self.yHigh = sc.getStickValue(yHigh)

    def setYLow(self, yLow):
        self.yLow = sc.getStickValue(yLow)

    def doStickCalculations(self, analogX, analogY, constrainDeadzone = False):
        xStick = analogX.value
        yStick = analogY.value

        if constrainDeadzone:
            x = sc.constrain(sc.rangeMap(xStick, self.xLow, self.xHigh, -1.0, 1.0), -1.0, 1.0)
            y = sc.constrain(sc.rangeMap(yStick, self.yLow, self.yHigh, -1.0, 1.0), -1.0, 1.0)
            magnitude = sc.magnitude(x, y)

            if magnitude > self.deadzoneMagnitude:
                factor = (magnitude - self.deadzoneMagnitude) / (1 - self.deadzoneMagnitude)
                rawInputs = sc.normalize(magnitude, x, y)
                mappedX = sc.rangeMap(rawInputs[0] * factor, -1.0, 1.0, -127, 127)
                mappedY = sc.rangeMap(rawInputs[1] * factor, -1.0, 1.0, -127, 127)
                xStick = int(sc.constrain(mappedX, -127, 127))
                yStick = int(sc.constrain(mappedY, -127, 127))
            else:
                xStick = 0
                yStick = 0

        return [xStick, yStick]
