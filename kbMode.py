import stickCommon as sc

class KbMode:
    def __init__(self):
        self.xStartOffset = None
        self.yStartOffset = None
        self.yConeEnd = None
        self.keyboard = None

    def setXStartOffset(self, value):
        self.xStartOffset = value

    def setYStartOffset(self, value):
        self.yStartOffset = value

    def setYConeEnd(self, value):
        self.yConeEnd = value

    def setKeyboard(self, keyboard):
        self.keyboard = keyboard

    def calculateStickInput(self, stickValues):
        up = False
        down = False
        left = False
        right = False
        xStick = stickValues[0]
        yStick = stickValues[1]
        xStickAbs = abs(xStick)
        yStickAbs = abs(yStick)

        if xStickAbs > self.xStartOffset:
            extraOffset = sc.rangeMap(yStickAbs, 0, 127, self.xStartOffset, self.yConeEnd)

            if xStickAbs > extraOffset:
                if xStick > 0:
                    right = True
                elif xStick < 0:
                    left = True

        if yStickAbs > self.yStartOffset:
            if yStick > 0:
                down = True
            elif yStick < 0:
                up = True

        return up, down, left, right

    def handleKeyboundModeKey(self, key, isPressed):
        if isPressed:
            self.keyboard.press(key)
        else:
            self.keyboard.release(key)
