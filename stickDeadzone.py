import stickCommon as sc
import time
import math

class StickDeadzone:
    def __init__(self):
        self.deadzone = 0
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
        self.deadzoneBuffer = sc.constrain(sc.rangeMap(deadzoneBuffer, 0, 32768, 0.0, 1.0), 0.0, 1.0)

    def setXHigh(self, xHigh):
        self.xHigh = sc.getStickValue(xHigh)

    def setXLow(self, xLow):
        self.xLow = sc.getStickValue(xLow)

    def setYHigh(self, yHigh):
        self.yHigh = sc.getStickValue(yHigh)

    def setYLow(self, yLow):
        self.yLow = sc.getStickValue(yLow)

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
        self.originalDeadzoneMagnitude = largestMagnitude
        self.initBoundary()

    def initBoundary(self):
        #self.deadzone = self.deadzone + self.deadzoneBuffer
        self.deadzone = self.deadzone + 1000
        #self.deadzoneMagnitude = self.originalDeadzoneMagnitude + 0.2
        self.deadzoneMagnitude = self.originalDeadzoneMagnitude + self.deadzoneBuffer
        self.upperBoundary = 32768 + self.deadzone
        self.lowerBoundary = 32768 - self.deadzone
