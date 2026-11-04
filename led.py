import board
import digitalio
import pwmio
import time
import stickCommon as sc

RGB_FADE_DURATION = 0.21
RGB_FADE_FRAME_SECONDS = 0.01

class Led:
    def __init__(self):
        self.mainLedPin = digitalio.DigitalInOut(board.LED)
        self.mainLedPin.direction = digitalio.Direction.OUTPUT
        self.extraLedPin = None
        self.redPwm = None
        self.greenPwm = None
        self.bluePwm = None
        self.fadeActive = False
        self.fadeTargetRed = 0
        self.fadeTargetGreen = 0
        self.fadeTargetBlue = 0
        self.fadeStartTime = 0
        self.fadeLastFrameTime = 0

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

            for i in range(0, 101, 5):
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

    def startRGBFade(self, red, green, blue):
        if self.redPwm == None or self.greenPwm == None or self.bluePwm == None:
            return

        self.fadeTargetRed = self.duty_cycle(sc.constrain(sc.rangeMap(red, 0, 255, 0.0, 100.0), 0.0, 100.0))
        self.fadeTargetGreen = self.duty_cycle(sc.constrain(sc.rangeMap(green, 0, 255, 0.0, 100.0), 0.0, 100.0))
        self.fadeTargetBlue = self.duty_cycle(sc.constrain(sc.rangeMap(blue, 0, 255, 0.0, 100.0), 0.0, 100.0))
        self.redPwm.duty_cycle = 0
        self.greenPwm.duty_cycle = 0
        self.bluePwm.duty_cycle = 0
        self.fadeStartTime = time.monotonic()
        self.fadeLastFrameTime = self.fadeStartTime
        self.fadeActive = True

    def update(self):
        if not self.fadeActive:
            return

        if self.redPwm == None or self.greenPwm == None or self.bluePwm == None:
            return

        now = time.monotonic()

        if now - self.fadeLastFrameTime < RGB_FADE_FRAME_SECONDS:
            return

        self.fadeLastFrameTime = now
        progress = (now - self.fadeStartTime) / RGB_FADE_DURATION

        if progress > 1.0:
            progress = 1.0

        brightness = self.duty_cycle(progress * 100)

        if brightness < self.fadeTargetRed:
            self.redPwm.duty_cycle = brightness
        else:
            self.redPwm.duty_cycle = self.fadeTargetRed

        if brightness < self.fadeTargetGreen:
            self.greenPwm.duty_cycle = brightness
        else:
            self.greenPwm.duty_cycle = self.fadeTargetGreen

        if brightness < self.fadeTargetBlue:
            self.bluePwm.duty_cycle = brightness
        else:
            self.bluePwm.duty_cycle = self.fadeTargetBlue

        if progress == 1.0:
            self.fadeActive = False

    def duty_cycle(self, percent):
        return int(percent / 100.0 * 65535.0)
