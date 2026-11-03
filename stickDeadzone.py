import stickCommon as sc
import time

# Inclusive maximum for the radial deadzone magnitude. The deadzone scaling
# formula divides by (1 - deadzoneMagnitude), so the value must stay below 1.0.
MAX_DEADZONE_MAGNITUDE = 0.99

class StickDeadzone:
    def __init__(self):
        self.deadzone = 0
        self.baseDeadzone = 0
        self.upperBoundary = 0
        self.lowerBoundary = 0
        self.deadzoneBuffer = 1000
        self.xHigh = 52535
        self.xLow = 15000
        self.yHigh = 52535
        self.yLow = 15000
        self.originalDeadzoneMagnitude = 0
        self.deadzoneMagnitude = 0

    def getDeadzone(self):
        return self.deadzone

    def getUpperBoundary(self):
        return self.upperBoundary

    def getLowerBoundary(self):
        return self.lowerBoundary

    def setDeadzoneBuffer(self, deadzoneBuffer):
        value = sc.getStickValue(deadzoneBuffer)

        if value is not None:
            self.deadzoneBuffer = sc.constrain(sc.rangeMap(value, 0, 32768, 0.0, 1.0), 0.0, 1.0)

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

    def diff(self, x, y):
        if x > y:
            return x - y
        elif x < y:
            return y - x
        else:
            return 0

    def initDeadzone(self, analogX, analogY):
        startTime = time.monotonic()
        biggestDiff = 0
        lowestX = 65535
        highestX = 0
        lowestY = 65535
        highestY = 0
        largestMagnitude = 0

        # loop for 5 seconds
        while True:
            newTime = time.monotonic()

            if (newTime - startTime) > 5:
                break

            #65535 is full range
            xValue = analogX.value
            yValue = analogY.value
            x = sc.constrain(sc.rangeMap(xValue, self.xLow, self.xHigh, -1.0, 1.0), -1.0, 1.0)
            y = sc.constrain(sc.rangeMap(yValue, self.yLow, self.yHigh, -1.0, 1.0), -1.0, 1.0)
            currentMagnitude = sc.magnitude(x, y)

            if currentMagnitude > largestMagnitude:
                largestMagnitude = currentMagnitude

            if xValue > highestX:
                highestX = xValue

            if xValue < lowestX:
                lowestX = xValue

            if yValue > highestY:
                highestY = yValue

            if yValue < lowestY:
                lowestY = yValue

        lowest = lowestX
        highest = highestX

        if lowestY < lowest:
            lowest = lowestY

        if highestY > highest:
            highest = highestY

        lowDiff = self.diff(32768, lowest)
        highDiff = self.diff(32768, highest)
        biggestDiff = highDiff

        if lowDiff > biggestDiff:
            biggestDiff = lowDiff

        self.deadzone = biggestDiff
        self.baseDeadzone = biggestDiff
        self.originalDeadzoneMagnitude = largestMagnitude
        self.initBoundary()

    def initBoundary(self):
        # Recompute from the base so repeated calls (e.g. every setDeadzone
        # command from the app) don't keep growing the deadzone.
        self.deadzone = self.baseDeadzone + 1000
        #self.deadzoneMagnitude = self.originalDeadzoneMagnitude + 0.2
        self.deadzoneMagnitude = sc.constrain(
            self.originalDeadzoneMagnitude + self.deadzoneBuffer,
            0.0,
            MAX_DEADZONE_MAGNITUDE,
        )
        self.upperBoundary = 32768 + self.deadzone
        self.lowerBoundary = 32768 - self.deadzone
