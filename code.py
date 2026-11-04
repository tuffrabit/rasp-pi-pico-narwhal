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
from actionManager import ActionManager
from serialHelper import SerialHelper

# Performance stuff
# Speed values
# ActionType: KEY = 1
# ActionType: GAMEPAD = 2
# ActionType: PROFILE = 3
# ActionType: HAT = 4

# Globals
# ActionManager registers the matrix keys last so pending six-key overflow
# fills in stable matrix order.
MATRIX_KEY_COUNT = 20
# CircuitPython's keypad event queue holds 64 events by default; the extra
# margin bounds the drain even if a stubbed queue never reports empty.
MATRIX_EVENT_DRAIN_LIMIT = 128

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
actionManager = ActionManager(keyboard, gp)
serialHelper = SerialHelper()
currentProfile = None
isKeyboardMode = False
stickXOrientationAxis = 0
stickXOrientationReverse = False
stickYOrientationAxis = 1
stickYOrientationReverse = True

actionManager.registerControl("stickButton")
actionManager.registerControl("thumbButton")
actionManager.registerControl("kbUp")
actionManager.registerControl("kbDown")
actionManager.registerControl("kbLeft")
actionManager.registerControl("kbRight")
actionManager.registerControl("dpadUp", hatDirection="up")
actionManager.registerControl("dpadDown", hatDirection="down")
actionManager.registerControl("dpadLeft", hatDirection="left")
actionManager.registerControl("dpadRight", hatDirection="right")
actionManager.registerControl("dpadCenter")

for matrixKeyIndex in range(MATRIX_KEY_COUNT):
    actionManager.registerControl(str(matrixKeyIndex))

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

    if not isinstance(stickAxesOrientation, dict):
        return

    if isinstance(stickAxesOrientation.get("x"), dict):
        stickXOrientationAxis = stickAxesOrientation["x"].get("axis", 0)
        stickXOrientationReverse = stickAxesOrientation["x"].get("reverse", False)

    if isinstance(stickAxesOrientation.get("y"), dict):
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
    global actionManager

    rgbLedValues = profileHelper.getRGBLedValues(currentProfile)

    if rgbLedValues is not None:
        led.startRGBFade(rgbLedValues["red"], rgbLedValues["green"], rgbLedValues["blue"])

    isKeyboardMode = profileHelper.getIsKbModeEnabled(currentProfile)
    keypadBindings = profileHelper.getKeypadBindings(currentProfile)

    actionManager.setBinding("stickButton", profileHelper.getJoystickButton(currentProfile))
    actionManager.setBinding("thumbButton", profileHelper.getThumbButton(currentProfile))
    actionManager.setBinding("kbUp", profileHelper.getKbModeBinding("up", currentProfile))
    actionManager.setBinding("kbDown", profileHelper.getKbModeBinding("down", currentProfile))
    actionManager.setBinding("kbLeft", profileHelper.getKbModeBinding("left", currentProfile))
    actionManager.setBinding("kbRight", profileHelper.getKbModeBinding("right", currentProfile))
    actionManager.setBinding("dpadUp", profileHelper.getDpadBinding("up", currentProfile))
    actionManager.setBinding("dpadDown", profileHelper.getDpadBinding("down", currentProfile))
    actionManager.setBinding("dpadLeft", profileHelper.getDpadBinding("left", currentProfile))
    actionManager.setBinding("dpadRight", profileHelper.getDpadBinding("right", currentProfile))
    actionManager.setBinding("dpadCenter", profileHelper.getDpadBinding("center", currentProfile))

    for matrixKeyIndex in range(MATRIX_KEY_COUNT):
        matrixBinding = None

        if keypadBindings is not None and matrixKeyIndex < len(keypadBindings):
            matrixBinding = keypadBindings[matrixKeyIndex]

        actionManager.setBinding(str(matrixKeyIndex), matrixBinding)

setRunValuesFromCurrentProfile()
resolveStickOrientation()

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

    led.update()

    actionManager.setPhysicalState("stickButton", not joySelectButton.value)
    actionManager.setPhysicalState("thumbButton", not thumbButton.value)
    actionManager.setPhysicalState("dpadUp", not dpadUpButton.value)
    actionManager.setPhysicalState("dpadDown", not dpadDownButton.value)
    actionManager.setPhysicalState("dpadLeft", not dpadLeftButton.value)
    actionManager.setPhysicalState("dpadRight", not dpadRightButton.value)
    actionManager.setPhysicalState("dpadCenter", not dpadCenterButton.value)

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
        actionManager.setPhysicalState("kbUp", up)
        actionManager.setPhysicalState("kbDown", down)
        actionManager.setPhysicalState("kbLeft", left)
        actionManager.setPhysicalState("kbRight", right)
    else:
        gp.move_joysticks(x=stickValues[0], y=stickValues[1])

    # Drain every queued matrix event in order so a burst can never backlog;
    # the bound keeps a misbehaving queue from wedging the loop.
    matrixEventsDrained = 0

    while matrixEventsDrained < MATRIX_EVENT_DRAIN_LIMIT:
        keyEvent = keyMatrix.events.get()

        if keyEvent is None:
            break

        matrixEventsDrained += 1
        keyNumber = keyEvent.key_number

        if keyNumber < MATRIX_KEY_COUNT:
            actionManager.setPhysicalState(str(keyNumber), keyEvent.pressed)

    # Flush aggregated HID once, after all inputs for this iteration.
    actionManager.applyOutputs()

    navigationAction = actionManager.consumeNavigation()
    profile = None

    if navigationAction == "nextProfile":
        profile = profileManager.getNextProfile()
    elif navigationAction == "previousProfile":
        profile = profileManager.getPreviousProfile()

    if profile != None:
        currentProfile = profile
        setRunValuesFromCurrentProfile()
        actionManager.neutralizeOutputs()

    if reloadCurrentProfile:
        reloadCurrentProfile = False
        currentProfile = profileManager.getCurrentProfile()

        if currentProfile != None:
            setRunValuesFromCurrentProfile()
            actionManager.neutralizeOutputs()
