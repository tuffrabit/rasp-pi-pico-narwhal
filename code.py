import board
import digitalio
import analogio
import usb_hid
import keypad
import gc

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

# Key Bindings
BUTTON_JOYSTICK_1_KEY = 1

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

# Profile specific stuff
rgbLedValues = profileHelper.getRGBLedValues(currentProfile)
led.setRGBLedColor(rgbLedValues["red"], rgbLedValues["green"], rgbLedValues["blue"])
isKeyboardMode = profileHelper.getIsKbModeEnabled(currentProfile)
keys = profileHelper.getKeypadBindings(currentProfile)
keyboardModeStickUpKey = profileHelper.getKbModeBinding("up", currentProfile)
keyboardModeStickDownKey = profileHelper.getKbModeBinding("down", currentProfile)
keyboardModeStickLeftKey = profileHelper.getKbModeBinding("left", currentProfile)
keyboardModeStickRightKey = profileHelper.getKbModeBinding("right", currentProfile)

print("free memory: " + str(gc.mem_alloc()))

while True:
    if joySelectButton.value:
        gp.release_buttons(BUTTON_JOYSTICK_1_KEY)
    else:
        gp.press_buttons(BUTTON_JOYSTICK_1_KEY)

    if thumbButton.value:
        keyboard.release(Keycode.ENTER)
    else:
        keyboard.press(Keycode.ENTER)

    stickValues = stick.doStickCalculations(ax, ay, True)

    if isKeyboardMode:
        pressedValues = kbMode.calculateStickInput(stickValues)
        kbMode.handleKeyboundModeKey(keyboardModeStickUpKey, pressedValues[0])
        kbMode.handleKeyboundModeKey(keyboardModeStickDownKey, pressedValues[1])
        kbMode.handleKeyboundModeKey(keyboardModeStickLeftKey, pressedValues[2])
        kbMode.handleKeyboundModeKey(keyboardModeStickRightKey, pressedValues[3])
    else:
        gp.move_joysticks(x=stickValues[0], y=stickValues[1])

    keyEvent = keyMatrix.events.get()

    if keyEvent:
        if keyEvent.pressed:
            keyboard.press(keys[keyEvent.key_number])
        else:
            keyboard.release(keys[keyEvent.key_number])
