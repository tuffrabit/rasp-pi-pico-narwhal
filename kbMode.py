class KbMode:
    def __init__(self):
        self.xStartOffset = None
        self.yStartOffset = None
        self.keyboard = None

    def setXStartOffset(self, value):
        self.xStartOffset = value

    def setYStartOffset(self, value):
        self.yStartOffset = value

    def setKeyboard(self, keyboard):
        self.keyboard = keyboard

    def calculateStickInput(self, stickValues):
        pressedValues = [False, False, False, False]
        xStick = stickValues[0]
        yStick = stickValues[1]

        if xStick > self.xStartOffset:
            pressedValues[3] = True
        elif xStick < (self.xStartOffset * -1):
            pressedValues[2] = True

        if yStick > self.yStartOffset:
            pressedValues[1] = True
        elif yStick < (self.yStartOffset * -1):
            pressedValues[0] = True

        return pressedValues

    def handleKeyboundModeKey(self, key, isPressed):
        if isPressed:
            self.keyboard.press(key)
        else:
            self.keyboard.release(key)
