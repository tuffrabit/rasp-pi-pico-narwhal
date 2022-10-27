import board
import digitalio
import analogio
import usb_hid
import keypad
import gc
import time

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from hid_gamepad import Gamepad
from stickDeadzone import StickDeadzone
from stick import Stick
from led import Led
from startup import Startup
from kbMode import KbMode
from config import Config
from profileManager import ProfileManager
from profileHelper import ProfileHelper
from keyConverter import KeyConverter

# Performance stuff
# Speed values
# ActionType: KEY = 1
# ActionType: GAMEPAD = 2
# ActionType: PROFILE = 3

# Globals
keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)
gp = Gamepad(usb_hid.devices)
stickDeadzone = StickDeadzone()
stick = Stick()
led = Led()
kbMode = KbMode()
startup = Startup()
config = Config()
profileManager = ProfileManager()
profileHelper = ProfileHelper()
keyConverter = KeyConverter()
currentProfile = None
deadzone = 0
isKeyboardMode = False
keys = None
keyboardModeStickUpKey = None
keyboardModeStickDownKey = None
keyboardModeStickLeftKey = None
keyboardModeStickRightKey = None
stickButton = None
thumbAction = None

actionStates = {
    "stickButton": False,
    "thumbButton": False,
    "kbUp": False,
    "kbDown": False,
    "kbLeft": False,
    "kbRight": False,
    "0": False,
    "1": False,
    "2": False,
    "3": False,
    "4": False,
    "5": False,
    "6": False,
    "7": False,
    "8": False,
    "9": False,
    "10": False,
    "11": False,
    "12": False,
    "13": False,
    "14": False,
    "15": False,
    "16": False,
    "17": False,
    "18": False,
    "19": False
}

# Config
config.loadFromFile()
profileManager.setConfig(config)
profileHelper.setKeyConverter(keyConverter)
currentProfile = profileManager.getInitialProfile()

# Setup
kbMode.setXStartOffset(config.kbModeOffsets['x'])
kbMode.setYStartOffset(config.kbModeOffsets['y'])
kbMode.setKeyboard(keyboard)
led.setRGBLed(board.GP21, board.GP20, board.GP19)
startup.setLed(led)

# Create some buttons. The physical buttons are connected
# to ground on one side and these and these pins on the other.
joySelectButton = digitalio.DigitalInOut(board.GP0)
joySelectButton.direction = digitalio.Direction.INPUT
joySelectButton.pull = digitalio.Pull.UP
thumbButton = digitalio.DigitalInOut(board.GP10)
thumbButton.direction = digitalio.Direction.INPUT
thumbButton.pull = digitalio.Pull.UP

# Connect an analog two-axis joystick to A4 and A5.
ax = analogio.AnalogIn(board.A0)
ay = analogio.AnalogIn(board.A1)

# Setup keypad
keyMatrix = keypad.KeyMatrix(
    row_pins=(board.GP6, board.GP7, board.GP8, board.GP9),
    column_pins=(board.GP1, board.GP2, board.GP3, board.GP4, board.GP5),
)

# Handle deadzone calc
led.setLedState(True)
led.setRGBLedColor(0, 255, 0)
stickDeadzone.setDeadzoneBuffer(config.deadzoneSize)
stickDeadzone.initDeadzone(ax, ay)
deadzone = stickDeadzone.getDeadzone()
stick.setDeadzone(stickDeadzone)
led.setLedState(False)
led.setRGBLedColor(0, 0, 255)

# Handle startup flags
startup.detectStartupFlags(joySelectButton)

def setRunValuesFromCurrentProfile():
    # Profile specific stuff
    global profileHelper
    global currentProfile
    global rgbLedValues
    global led
    global isKeyboardMode
    global keys
    global keyboardModeStickUpKey
    global keyboardModeStickDownKey
    global keyboardModeStickLeftKey
    global keyboardModeStickRightKey
    global stickButton
    global thumbAction

    rgbLedValues = profileHelper.getRGBLedValues(currentProfile)
    led.setRGBLedColor(rgbLedValues["red"], rgbLedValues["green"], rgbLedValues["blue"])
    isKeyboardMode = profileHelper.getIsKbModeEnabled(currentProfile)
    keys = profileHelper.getKeypadBindings(currentProfile)
    keyboardModeStickUpKey = profileHelper.getKbModeBinding("up", currentProfile)
    keyboardModeStickDownKey = profileHelper.getKbModeBinding("down", currentProfile)
    keyboardModeStickLeftKey = profileHelper.getKbModeBinding("left", currentProfile)
    keyboardModeStickRightKey = profileHelper.getKbModeBinding("right", currentProfile)
    stickButton = profileHelper.getJoystickButton(currentProfile)
    thumbAction = profileHelper.getThumbButton(currentProfile)

def handleAction(stateIndex, trigger, action):
    global actionStates
    goToNextProfile = False
    goToPreviousProfile = False

    if trigger != actionStates[stateIndex]:
        actionStates[stateIndex] = trigger

        if action["type"] == 1:
            if trigger:
                keyboard.press(action["action"])
            else:
                keyboard.release(action["action"])
        elif action["type"] == 2:
            if trigger:
                gp.press_buttons(action["action"])
            else:
                gp.release_buttons(action["action"])
        elif action["type"] == 3:
            if trigger:
                if action["action"] == "nextProfile":
                    goToNextProfile = True
                elif action["action"] == "previousProfile":
                    goToPreviousProfile = True

    return goToNextProfile, goToPreviousProfile

setRunValuesFromCurrentProfile()
#print("free memory: " + str(gc.mem_alloc()))

goToNextProfile = False
goToPreviousProfile = False
#currentTime = time.monotonic()
#iterations = 0

while True:
    #if time.monotonic() - currentTime > 1.0:
    #    print("free memory: " + str(gc.mem_alloc()))
    #    print("iterations: " + str(iterations))
    #    print("")
    #    iterations = 0
    #    currentTime = time.monotonic()

    goToNextProfile, goToPreviousProfile = handleAction("stickButton", not joySelectButton.value, stickButton)
    goToNextProfile, goToPreviousProfile = handleAction("thumbButton", not thumbButton.value, thumbAction)
    stickValues = stick.doStickCalculations(ax, ay, True)

    if isKeyboardMode:
        up, down, left, right = kbMode.calculateStickInput(stickValues)
        goToNextProfile, goToPreviousProfile = handleAction("kbUp", up, keyboardModeStickUpKey)
        goToNextProfile, goToPreviousProfile = handleAction("kbDown", down, keyboardModeStickDownKey)
        goToNextProfile, goToPreviousProfile = handleAction("kbLeft", left, keyboardModeStickLeftKey)
        goToNextProfile, goToPreviousProfile = handleAction("kbRight", right, keyboardModeStickRightKey)
    else:
        gp.move_joysticks(x=stickValues[0], y=stickValues[1])

    keyEvent = keyMatrix.events.get()

    if keyEvent:
        keyNumber = keyEvent.key_number
        keyAction = keys[keyNumber]
        goToNextProfile, goToPreviousProfile = handleAction(str(keyNumber), keyEvent.pressed, keyAction)

    if goToNextProfile or goToPreviousProfile:
        profile = None

        if goToNextProfile:
            profile = profileManager.getNextProfile()
        elif goToPreviousProfile:
            profile = profileManager.getPreviousProfile()

        goToNextProfile = False
        goToPreviousProfile = False

        if profile != None:
            currentProfile = profile
            setRunValuesFromCurrentProfile()
            gp.release_all_buttons()
            keyboard.release_all()

    #iterations = iterations + 1
