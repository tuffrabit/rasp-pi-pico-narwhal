import board
import digitalio
import analogio
import usb_hid
import keypad

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from hid_gamepad import Gamepad
from stickDeadzone import StickDeadzone
from stick import Stick
from led import Led
from startup import Startup
from kbMode import KbMode

# Key Bindings
BUTTON_JOYSTICK_1_KEY = 1
KEYBOARD_MODE_STICK_UP_KEY = Keycode.W
KEYBOARD_MODE_STICK_DOWN_KEY = Keycode.S
KEYBOARD_MODE_STICK_LEFT_KEY = Keycode.A
KEYBOARD_MODE_STICK_RIGHT_KEY = Keycode.D

# Configurable Values
KEYBOARD_MODE_X_START_OFFSET = 10
KEYBOARD_MODE_Y_START_OFFSET = 10

# Globals
keyboard = Keyboard(usb_hid.devices)
keyboard_layout = KeyboardLayoutUS(keyboard)
gp = Gamepad(usb_hid.devices)
stickDeadzone = StickDeadzone()
stick = Stick()
led = Led()
kbMode = KbMode()
startup = Startup()
deadzone = 0
isKeyboardMode = False

#Setup
kbMode.setXStartOffset(KEYBOARD_MODE_X_START_OFFSET)
kbMode.setYStartOffset(KEYBOARD_MODE_Y_START_OFFSET)
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

keys = [Keycode.ESCAPE,
    Keycode.ONE,
    Keycode.O,
    Keycode.F1,
    Keycode.M,
    Keycode.TAB,
    Keycode.B,
    Keycode.Q,
    Keycode.R,
    Keycode.E,
    Keycode.LEFT_CONTROL,
    Keycode.F,
    Keycode.X,
    Keycode.LEFT_SHIFT,
    Keycode.SPACE,
    Keycode.F12,
    Keycode.Z,
    Keycode.X,
    Keycode.V,
    Keycode.C]

# Handle deadzone calc
led.setLedState(True)
led.setRGBLedColor(0, 255, 0)
stickDeadzone.initDeadzone(ax, ay)
deadzone = stickDeadzone.getDeadzone()
stick.setDeadzone(stickDeadzone)
led.setLedState(False)
led.setRGBLedColor(0, 0, 255)

# Handle startup flags
isKeyboardMode = startup.detectStartupFlags(joySelectButton)

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
        kbMode.handleKeyboundModeKey(KEYBOARD_MODE_STICK_UP_KEY, pressedValues[0])
        kbMode.handleKeyboundModeKey(KEYBOARD_MODE_STICK_DOWN_KEY, pressedValues[1])
        kbMode.handleKeyboundModeKey(KEYBOARD_MODE_STICK_LEFT_KEY, pressedValues[2])
        kbMode.handleKeyboundModeKey(KEYBOARD_MODE_STICK_RIGHT_KEY, pressedValues[3])
    else:
        gp.move_joysticks(x=stickValues[0], y=stickValues[1])

    keyEvent = keyMatrix.events.get()

    if keyEvent:
        if keyEvent.pressed:
            keyboard.press(keys[keyEvent.key_number])
        else:
            keyboard.release(keys[keyEvent.key_number])
