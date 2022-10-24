import time

class Startup:
    def __init__(self):
        self.led = None

    def setLed(self, led):
        self.led = led

    def detectStartupFlags(self, button):
        isKeyboardMode = False
        startTime = time.monotonic()
        lastBlinkTime = 0
        ledState = False

        while True:
            newTime = time.monotonic()

            if (newTime - startTime) > 5:
                break

            if (newTime - lastBlinkTime) >= 0.5:
                lastBlinkTime = newTime

                if ledState == False:
                    ledState = True
                else:
                    ledState = False

                self.led.setLedState(ledState)

            if button.value == False:
                isKeyboardMode = True
                self.led.setLedState(True)
                break

        if isKeyboardMode == False:
            self.led.setLedState(False)

        self.led.setRGBLedColor(3, 253, 252)#teal

        return isKeyboardMode
