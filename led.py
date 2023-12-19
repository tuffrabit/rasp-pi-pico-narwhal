import board
import digitalio
import pwmio
import time
import stickCommon as sc

class Led:
    def __init__(self):
        self.mainLedPin = digitalio.DigitalInOut(board.LED)
        self.mainLedPin.direction = digitalio.Direction.OUTPUT
        self.extraLedPin = None
        self.redPwm = None
        self.greenPwm = None
        self.bluePwm = None

    def setExtraLed(self, pin):
        self.extraLedPin = digitalio.DigitalInOut(pin)
        self.extraLedPin.direction = digitalio.Direction.OUTPUT

    def setRGBLed(self, redPin, greenPin, bluePin):
        self.redPwm = pwmio.PWMOut(redPin, frequency=1000, duty_cycle=0)
        self.greenPwm = pwmio.PWMOut(greenPin, frequency=1000, duty_cycle=0)
        self.bluePwm = pwmio.PWMOut(bluePin, frequency=1000, duty_cycle=0)

    def setLedState(self, state):
        self.mainLedPin.value = state

        if self.extraLedPin != None:
            self.extraLedPin.value = state

    def fadeToRGBLedColor(self, red, green, blue):
        if self.redPwm != None and self.greenPwm != None and self.bluePwm != None:
            sleepAmount = 10  # Number of milliseconds to delay between changes.
            # Increase to slow down, decrease to speed up.
            sleepTime = sleepAmount / 1000

            red = self.duty_cycle(sc.constrain(sc.rangeMap(red, 0, 255, 0.0, 100.0), 0.0, 100.0))
            green = self.duty_cycle(sc.constrain(sc.rangeMap(green, 0, 255, 0.0, 100.0), 0.0, 100.0))
            blue = self.duty_cycle(sc.constrain(sc.rangeMap(blue, 0, 255, 0.0, 100.0), 0.0, 100.0))
            self.redPwm.duty_cycle = 0
            self.greenPwm.duty_cycle = 0
            self.bluePwm.duty_cycle = 0

            for i in range(100):
                brightness = self.duty_cycle(i)

                if brightness < red:
                    self.redPwm.duty_cycle = brightness
                else:
                    self.redPwm.duty_cycle = red

                if brightness < green:
                    self.greenPwm.duty_cycle = brightness
                else:
                    self.greenPwm.duty_cycle = green

                if brightness < blue:
                    self.bluePwm.duty_cycle = brightness
                else:
                    self.bluePwm.duty_cycle = blue

                time.sleep(sleepTime)

    def duty_cycle(self, percent):
        return int(percent / 100.0 * 65535.0)
