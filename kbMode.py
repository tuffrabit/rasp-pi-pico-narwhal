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
        up = False
        down = False
        left = False
        right = False
        xStick = stickValues[0]
        yStick = stickValues[1]

        if xStick > self.xStartOffset:
            right = True
        elif xStick < (self.xStartOffset * -1):
            left = True

        if yStick > self.yStartOffset:
            down = True
        elif yStick < (self.yStartOffset * -1):
            up = True

        return up, down, left, right

    def handleKeyboundModeKey(self, key, isPressed):
        if isPressed:
            self.keyboard.press(key)
        else:
            self.keyboard.release(key)
