import stickCommon as sc

class KbMode:
    def __init__(self):
        self.xStartOffset = None
        self.yStartOffset = None
        self.yConeEnd = None
        self.keyboard = None
        # Reused every call so the main loop doesn't allocate.
        self.result = [False, False, False, False]

    def setXStartOffset(self, value):
        self.xStartOffset = value

    def setYStartOffset(self, value):
        self.yStartOffset = value

    def setYConeEnd(self, value):
        self.yConeEnd = value

    def setKeyboard(self, keyboard):
        self.keyboard = keyboard

    def calculateStickInput(self, stickValues):
        result = self.result
        result[0] = False
        result[1] = False
        result[2] = False
        result[3] = False

        if self.xStartOffset is None or self.yStartOffset is None or self.yConeEnd is None:
            return result

        xStick = stickValues[0]
        yStick = stickValues[1]
        xStickAbs = abs(xStick)
        yStickAbs = abs(yStick)

        if xStickAbs > self.xStartOffset:
            extraOffset = sc.rangeMap(yStickAbs, 0, 127, self.xStartOffset, self.yConeEnd)

            if xStickAbs > extraOffset:
                if xStick > 0:
                    result[3] = True
                elif xStick < 0:
                    result[2] = True

        if yStickAbs > self.yStartOffset:
            if yStick > 0:
                result[1] = True
            elif yStick < 0:
                result[0] = True

        return result

    def handleKeyboundModeKey(self, key, isPressed):
        if isPressed:
            self.keyboard.press(key)
        else:
            self.keyboard.release(key)
