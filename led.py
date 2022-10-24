import board
import digitalio
import adafruit_rgbled

class Led:
    def __init__(self):
        self.mainLedPin = digitalio.DigitalInOut(board.LED)
        self.mainLedPin.direction = digitalio.Direction.OUTPUT
        self.extraLedPin = None
        self.rgbLed = None

    def setExtraLed(self, pin):
        self.extraLedPin = digitalio.DigitalInOut(pin)
        self.extraLedPin.direction = digitalio.Direction.OUTPUT

    def setRGBLed(self, redPin, greenPin, bluePin):
        self.rgbLed = adafruit_rgbled.RGBLED(redPin, greenPin, bluePin)

    def setLedState(self, state):
        self.mainLedPin.value = state

        if self.extraLedPin != None:
            self.extraLedPin.value = state

    def setRGBLedColor(self, red, green, blue):
        if self.rgbLed != None:
            self.rgbLed.color = (red, green, blue)
