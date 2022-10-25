import time

class StickDeadzone:
    def __init__(self):
        self.deadzone = 0
        self.edgeAdjust = 0
        self.upperBoundary = 0
        self.lowerBoundary = 0
        self.deadzoneBuffer = 1000

    def getDeadzone(self):
        return self.deadzone

    def getEdgeAdjust(self):
        return self.edgeAdjust

    def getUpperBoundary(self):
        return self.upperBoundary

    def getLowerBoundary(self):
        return self.lowerBoundary

    def setDeadzoneBuffer(self, deadzoneBuffer):
        self.deadzoneBuffer = deadzoneBuffer

    def initDeadzone(self, analogX, analogY):
        startTime = time.monotonic()
        highValue = 0

        # loop for 5 seconds
        while True:
            newTime = time.monotonic()

            if (newTime - startTime) > 5:
                break

            #65535 is full range
            xValue = analogX.value
            yValue = analogY.value
            diffX = 0
            diffY = 0

            if xValue < 32768:
                diffX = 32768 - xValue

            if xValue > 32768:
                diffX = xValue - 32768

            if yValue < 32768:
                diffY = 32768 - yValue

            if yValue > 32768:
                diffY = yValue - 32768

            if diffX >= diffY:
                highValue = diffX
            else:
                highValue = diffY

        self.deadzone = highValue
        self.initBoundary()

    def initBoundary(self):
        self.deadzone = self.deadzone + self.deadzoneBuffer
        self.edgeAdjust = self.deadzone + 250
        self.upperBoundary = 32768 + self.deadzone
        self.lowerBoundary = 32768 - self.deadzone
