import board
import digitalio
import analogio
import usb_hid
import usb_cdc
import keypad

from adafruit_hid.keyboard import Keyboard
from hid_gamepad import Gamepad
from stickDeadzone import StickDeadzone
from stick import Stick
from led import Led
from kbMode import KbMode
from config import Config
from profileManager import ProfileManager
from profileHelper import ProfileHelper
from keyConverter import KeyConverter
from serialHelper import SerialHelper

# Performance stuff
# Speed values
# ActionType: KEY = 1
# ActionType: GAMEPAD = 2
# ActionType: PROFILE = 3

# Globals
keyboard = Keyboard(usb_hid.devices)
gp = Gamepad(usb_hid.devices)
stickDeadzone = StickDeadzone()
stick = Stick()
led = Led()
kbMode = KbMode()
config = Config()
profileManager = ProfileManager()
profileHelper = ProfileHelper()
keyConverter = KeyConverter()
serialHelper = SerialHelper()
currentProfile = None
isKeyboardMode = False
keys = None
keyboardModeStickUpKey = None
keyboardModeStickDownKey = None
keyboardModeStickLeftKey = None
keyboardModeStickRightKey = None
stickButton = None
thumbAction = None
dpadUpAction = None
dpadDownAction = None
dpadLeftAction = None
dpadRightAction = None
dpadCenterAction = None
stickXOrientationAxis = 0
stickXOrientationReverse = False
stickYOrientationAxis = 1
stickYOrientationReverse = True

actionStates = {
    "stickButton": False,
    "thumbButton": False,
    "kbUp": False,
    "kbDown": False,
    "kbLeft": False,
    "kbRight": False,
    "dpadUp": False,
    "dpadDown": False,
    "dpadLeft": False,
    "dpadRight": False,
    "dpadCenter": False,
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
serialHelper.setConfig(config)
serialHelper.setProfileManager(profileManager)
serialHelper.setStickDeadzone(stickDeadzone)
serialHelper.setStick(stick)
serialHelper.setKbMode(kbMode)

# Setup
kbMode.setXStartOffset(config.kbModeOffsets['x'])
kbMode.setYStartOffset(config.kbModeOffsets['y'])
kbMode.setYConeEnd(config.kbModeYConeEnd)
kbMode.setKeyboard(keyboard)
led.setRGBLed(board.GP21, board.GP20, board.GP19)

# Create some buttons. The physical buttons are connected
# to ground on one side and these and these pins on the other.
joySelectButton = digitalio.DigitalInOut(board.GP0)
joySelectButton.direction = digitalio.Direction.INPUT
joySelectButton.pull = digitalio.Pull.UP
thumbButton = digitalio.DigitalInOut(board.GP10)
thumbButton.direction = digitalio.Direction.INPUT
thumbButton.pull = digitalio.Pull.UP
dpadUpButton = digitalio.DigitalInOut(board.GP11)
dpadUpButton.direction = digitalio.Direction.INPUT
dpadUpButton.pull = digitalio.Pull.UP
dpadDownButton = digitalio.DigitalInOut(board.GP13)
dpadDownButton.direction = digitalio.Direction.INPUT
dpadDownButton.pull = digitalio.Pull.UP
dpadLeftButton = digitalio.DigitalInOut(board.GP14)
dpadLeftButton.direction = digitalio.Direction.INPUT
dpadLeftButton.pull = digitalio.Pull.UP
dpadRightButton = digitalio.DigitalInOut(board.GP12)
dpadRightButton.direction = digitalio.Direction.INPUT
dpadRightButton.pull = digitalio.Pull.UP
dpadCenterButton = digitalio.DigitalInOut(board.GP15)
dpadCenterButton.direction = digitalio.Direction.INPUT
dpadCenterButton.pull = digitalio.Pull.UP

# Connect an analog two-axis joystick to A4 and A5.
ax = analogio.AnalogIn(board.A0)
ay = analogio.AnalogIn(board.A1)

# Setup keypad
keyMatrix = keypad.KeyMatrix(
    row_pins=(board.GP6, board.GP7, board.GP8, board.GP9),
    column_pins=(board.GP1, board.GP2, board.GP3, board.GP4, board.GP5),
)

def resolveStickOrientation():
    global stickXOrientationAxis
    global stickXOrientationReverse
    global stickYOrientationAxis
    global stickYOrientationReverse

    stickAxesOrientation = config.stickAxesOrientation

    if "x" in stickAxesOrientation:
        stickXOrientationAxis = stickAxesOrientation["x"].get("axis", 0)
        stickXOrientationReverse = stickAxesOrientation["x"].get("reverse", False)

    if "y" in stickAxesOrientation:
        stickYOrientationAxis = stickAxesOrientation["y"].get("axis", 1)
        stickYOrientationReverse = stickAxesOrientation["y"].get("reverse", True)

# Handle deadzone calc
led.setLedState(True)
led.fadeToRGBLedColor(0, 255, 0)
stickDeadzone.setDeadzoneBuffer(config.deadzoneSize)
stickDeadzone.setXHigh(config.stickBoundaries["highX"])
stickDeadzone.setXLow(config.stickBoundaries["lowX"])
stickDeadzone.setYHigh(config.stickBoundaries["highY"])
stickDeadzone.setYLow(config.stickBoundaries["lowY"])
stickDeadzone.initDeadzone(ax, ay)
stick.setDeadzone(stickDeadzone)
stick.setXHigh(config.stickBoundaries["highX"])
stick.setXLow(config.stickBoundaries["lowX"])
stick.setYHigh(config.stickBoundaries["highY"])
stick.setYLow(config.stickBoundaries["lowY"])
led.setLedState(False)
led.fadeToRGBLedColor(0, 0, 255)

def setRunValuesFromCurrentProfile():
    # Profile specific stuff
    global profileHelper
    global currentProfile
    global led
    global isKeyboardMode
    global keys
    global keyboardModeStickUpKey
    global keyboardModeStickDownKey
    global keyboardModeStickLeftKey
    global keyboardModeStickRightKey
    global stickButton
    global thumbAction
    global dpadUpAction
    global dpadDownAction
    global dpadLeftAction
    global dpadRightAction
    global dpadCenterAction

    rgbLedValues = profileHelper.getRGBLedValues(currentProfile)

    if rgbLedValues is not None:
        led.fadeToRGBLedColor(rgbLedValues["red"], rgbLedValues["green"], rgbLedValues["blue"])

    isKeyboardMode = profileHelper.getIsKbModeEnabled(currentProfile)
    keys = profileHelper.getKeypadBindings(currentProfile)
    keyboardModeStickUpKey = profileHelper.getKbModeBinding("up", currentProfile)
    keyboardModeStickDownKey = profileHelper.getKbModeBinding("down", currentProfile)
    keyboardModeStickLeftKey = profileHelper.getKbModeBinding("left", currentProfile)
    keyboardModeStickRightKey = profileHelper.getKbModeBinding("right", currentProfile)
    stickButton = profileHelper.getJoystickButton(currentProfile)
    thumbAction = profileHelper.getThumbButton(currentProfile)
    dpadUpAction = profileHelper.getDpadBinding("up", currentProfile)
    dpadDownAction = profileHelper.getDpadBinding("down", currentProfile)
    dpadLeftAction = profileHelper.getDpadBinding("left", currentProfile)
    dpadRightAction = profileHelper.getDpadBinding("right", currentProfile)
    dpadCenterAction = profileHelper.getDpadBinding("center", currentProfile)

def handleAction(stateIndex, trigger, action):
    global goToNextProfile
    global goToPreviousProfile

    if action is None or action["type"] is None or action["action"] is None:
        return

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

setRunValuesFromCurrentProfile()
resolveStickOrientation()

goToNextProfile = False
goToPreviousProfile = False
reloadCurrentProfile = False

doReadStickValues = False
readStickValues = [
    {"x": 0, "y": 0},
    {"x": 0, "y": 0}
]

if usb_cdc.data:
    usb_cdc.data.reset_input_buffer()

while True:
    commandAction = serialHelper.checkForCommands()

    if commandAction is not None:
        if "profileChange" in commandAction and commandAction["profileChange"]:
            reloadCurrentProfile = True
        elif "readStickValues" in commandAction and commandAction["readStickValues"]:
            doReadStickValues = True
        elif "orientationChange" in commandAction and commandAction["orientationChange"]:
            resolveStickOrientation()

    handleAction("stickButton", not joySelectButton.value, stickButton)
    handleAction("thumbButton", not thumbButton.value, thumbAction)
    handleAction("dpadUp", not dpadUpButton.value, dpadUpAction)
    handleAction("dpadDown", not dpadDownButton.value, dpadDownAction)
    handleAction("dpadLeft", not dpadLeftButton.value, dpadLeftAction)
    handleAction("dpadRight", not dpadRightButton.value, dpadRightAction)
    handleAction("dpadCenter", not dpadCenterButton.value, dpadCenterAction)

    stickValues = stick.doStickCalculations(ax, ay, True)
    tempXValue = stickValues[0]
    tempYValue = stickValues[1]

    if stickXOrientationAxis == 1:
        stickValues[0] = tempYValue

    if stickXOrientationReverse:
        stickValues[0] = stickValues[0] * -1

    if stickYOrientationAxis == 0:
        stickValues[1] = tempXValue

    if stickYOrientationReverse:
        stickValues[1] = stickValues[1] * -1

    if doReadStickValues:
        doReadStickValues = False
        readStickValues[0]["x"] = ax.value
        readStickValues[0]["y"] = ay.value
        readStickValues[1]["x"] = stickValues[0]
        readStickValues[1]["y"] = stickValues[1]
        serialHelper.write("readStickValues", readStickValues)

    if isKeyboardMode:
        up, down, left, right = kbMode.calculateStickInput(stickValues)
        handleAction("kbUp", up, keyboardModeStickUpKey)
        handleAction("kbDown", down, keyboardModeStickDownKey)
        handleAction("kbLeft", left, keyboardModeStickLeftKey)
        handleAction("kbRight", right, keyboardModeStickRightKey)
    else:
        gp.move_joysticks(x=stickValues[0], y=stickValues[1])

    keyEvent = keyMatrix.events.get()

    if keyEvent:
        keyNumber = keyEvent.key_number

        if keys is not None and keyNumber < len(keys):
            keyAction = keys[keyNumber]
            handleAction(str(keyNumber), keyEvent.pressed, keyAction)

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

    if reloadCurrentProfile:
        reloadCurrentProfile = False
        currentProfile = profileManager.getCurrentProfile()

        if currentProfile != None:
            setRunValuesFromCurrentProfile()
            gp.release_all_buttons()
            keyboard.release_all()
