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
        self._recalculateConstants()
        # Reused every call so the main loop doesn't allocate.
        self.result = [0, 0]

    def _recalculateConstants(self):
        self._xScale = 2.0 / (self.xHigh - self.xLow)
        self._xOffset = -1.0 - self.xLow * self._xScale
        self._yScale = 2.0 / (self.yHigh - self.yLow)
        self._yOffset = -1.0 - self.yLow * self._yScale
        self._deadzoneMagnitudeSquared = self.deadzoneMagnitude * self.deadzoneMagnitude
        self._deadzoneDenominator = 1.0 - self.deadzoneMagnitude

    def setDeadzone(self, deadzone):
        self.deadzone = deadzone
        self.mappedDeadzone = sc.rangeMap(deadzone.getDeadzone(), 0, 32768, 0.0, 1.0)
        # Clamp defensively; deadzone.deadzoneMagnitude must stay below 1.0
        # so the scaling denominator can never reach zero or go negative.
        self.deadzoneMagnitude = sc.constrain(deadzone.deadzoneMagnitude, 0.0, MAX_DEADZONE_MAGNITUDE)
        self._recalculateConstants()

    def setXHigh(self, xHigh):
        value = sc.getBoundaryValue(xHigh, self.xLow, False)

        if value is None:
            return False

        self.xHigh = value
        self._recalculateConstants()
        return True

    def setXLow(self, xLow):
        value = sc.getBoundaryValue(xLow, self.xHigh, True)

        if value is None:
            return False

        self.xLow = value
        self._recalculateConstants()
        return True

    def setYHigh(self, yHigh):
        value = sc.getBoundaryValue(yHigh, self.yLow, False)

        if value is None:
            return False

        self.yHigh = value
        self._recalculateConstants()
        return True

    def setYLow(self, yLow):
        value = sc.getBoundaryValue(yLow, self.yHigh, True)

        if value is None:
            return False

        self.yLow = value
        self._recalculateConstants()
        return True

    def doStickCalculations(self, analogX, analogY, constrainDeadzone = False):
        result = self.result
        xStick = analogX.value
        yStick = analogY.value

        if constrainDeadzone:
            xScale = self._xScale
            xOffset = self._xOffset
            yScale = self._yScale
            yOffset = self._yOffset
            deadzoneMagnitude = self.deadzoneMagnitude

            if xStick <= self.xLow:
                x = -1.0
            elif xStick >= self.xHigh:
                x = 1.0
            else:
                x = xStick * xScale + xOffset

            if yStick <= self.yLow:
                y = -1.0
            elif yStick >= self.yHigh:
                y = 1.0
            else:
                y = yStick * yScale + yOffset

            if x * x + y * y > self._deadzoneMagnitudeSquared:
                magnitude = sc.magnitude(x, y)
                factor = (magnitude - deadzoneMagnitude) / self._deadzoneDenominator
                mappedX = sc.rangeMap(x / magnitude * factor, -1.0, 1.0, -127, 127)
                mappedY = sc.rangeMap(y / magnitude * factor, -1.0, 1.0, -127, 127)

                if mappedX < -127:
                    mappedX = -127
                elif mappedX > 127:
                    mappedX = 127

                if mappedY < -127:
                    mappedY = -127
                elif mappedY > 127:
                    mappedY = 127

                xStick = int(mappedX)
                yStick = int(mappedY)
            else:
                xStick = 0
                yStick = 0

        result[0] = xStick
        result[1] = yStick
        return result
