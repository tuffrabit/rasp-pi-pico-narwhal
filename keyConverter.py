from adafruit_hid.keycode import Keycode

class KeyConverter:
    def getKeycodeFromId(self, keyId):
        keycode = None

        if keyId == "nextProfile" or keyId == "previousProfile":
            keycode = keyId
        elif keyId == "1":
            keycode = Keycode.ONE
        elif keyId == "2":
            keycode = Keycode.TWO
        elif keyId == "3":
            keycode = Keycode.THREE
        elif keyId == "4":
            keycode = Keycode.FOUR
        elif keyId == "5":
            keycode = Keycode.FIVE
        elif keyId == "6":
            keycode = Keycode.SIX
        elif keyId == "7":
            keycode = Keycode.SEVEN
        elif keyId == "8":
            keycode = Keycode.EIGHT
        elif keyId == "9":
            keycode = Keycode.NINE
        elif keyId == "0":
            keycode = Keycode.ZERO
        elif keyId == "leftCtrl":
            keycode = Keycode.LEFT_CONTROL
        elif keyId == "leftAlt":
            keycode = Keycode.LEFT_ALT
        elif keyId == "leftShift":
            keycode = Keycode.LEFT_SHIFT
        elif keyId == "rightCtrl":
            keycode = Keycode.RIGHT_CONTROL
        elif keyId == "rightAlt":
            keycode = Keycode.RIGHT_ALT
        elif keyId == "rightShift":
            keycode = Keycode.RIGHT_SHIFT
        elif keyId == "space":
            keycode = Keycode.SPACE
        elif keyId == "enter":
            keycode = Keycode.ENTER
        elif keyId == "escape":
            keycode = Keycode.ESCAPE
        elif keyId == "backspace":
            keycode = Keycode.BACKSPACE
        elif keyId == "tab":
            keycode = Keycode.TAB
        elif keyId == "minus":
            keycode = Keycode.MINUS
        elif keyId == "equals":
            keycode = Keycode.EQUALS
        elif keyId == "leftBracket":
            keycode = Keycode.LEFT_BRACKET
        elif keyId == "rightBracket":
            keycode = Keycode.RIGHT_BRACKET
        elif keyId == "backslash":
            keycode = Keycode.BACKSLASH
        elif keyId == "semicolon":
            keycode = Keycode.SEMICOLON
        elif keyId == "quote":
            keycode = Keycode.QUOTE
        elif keyId == "comma":
            keycode = Keycode.COMMA
        elif keyId == "period":
            keycode = Keycode.PERIOD
        elif keyId == "slash":
            keycode = Keycode.FORWARD_SLASH
        elif keyId == "grave":
            keycode = Keycode.GRAVE_ACCENT
        elif keyId == "del":
            keycode = Keycode.DELETE
        elif keyId == "caps":
            keycode = Keycode.CAPS_LOCK
        elif keyId == "f1":
            keycode = Keycode.F1
        elif keyId == "f2":
            keycode = Keycode.F2
        elif keyId == "f3":
            keycode = Keycode.F3
        elif keyId == "f4":
            keycode = Keycode.F4
        elif keyId == "f5":
            keycode = Keycode.F5
        elif keyId == "f6":
            keycode = Keycode.F6
        elif keyId == "f7":
            keycode = Keycode.F7
        elif keyId == "f8":
            keycode = Keycode.F8
        elif keyId == "f9":
            keycode = Keycode.F9
        elif keyId == "f10":
            keycode = Keycode.F10
        elif keyId == "f11":
            keycode = Keycode.F11
        elif keyId == "f12":
            keycode = Keycode.F12
        elif keyId == "up":
            keycode = Keycode.UP_ARROW
        elif keyId == "down":
            keycode = Keycode.DOWN_ARROW
        elif keyId == "left":
            keycode = Keycode.LEFT_ARROW
        elif keyId == "right":
            keycode = Keycode.RIGHT_ARROW
        elif keyId == "a":
            keycode = Keycode.A
        elif keyId == "b":
            keycode = Keycode.B
        elif keyId == "c":
            keycode = Keycode.C
        elif keyId == "d":
            keycode = Keycode.D
        elif keyId == "e":
            keycode = Keycode.E
        elif keyId == "f":
            keycode = Keycode.F
        elif keyId == "g":
            keycode = Keycode.G
        elif keyId == "h":
            keycode = Keycode.H
        elif keyId == "i":
            keycode = Keycode.I
        elif keyId == "j":
            keycode = Keycode.J
        elif keyId == "k":
            keycode = Keycode.K
        elif keyId == "l":
            keycode = Keycode.L
        elif keyId == "m":
            keycode = Keycode.M
        elif keyId == "n":
            keycode = Keycode.N
        elif keyId == "o":
            keycode = Keycode.O
        elif keyId == "p":
            keycode = Keycode.P
        elif keyId == "q":
            keycode = Keycode.Q
        elif keyId == "r":
            keycode = Keycode.R
        elif keyId == "s":
            keycode = Keycode.S
        elif keyId == "t":
            keycode = Keycode.T
        elif keyId == "u":
            keycode = Keycode.U
        elif keyId == "v":
            keycode = Keycode.V
        elif keyId == "w":
            keycode = Keycode.W
        elif keyId == "x":
            keycode = Keycode.X
        elif keyId == "y":
            keycode = Keycode.Y
        elif keyId == "z":
            keycode = Keycode.Z
        elif keyId == "numSlash":
            keycode = Keycode.KEYPAD_FORWARD_SLASH
        elif keyId == "numAsterisk":
            keycode = Keycode.KEYPAD_ASTERISK
        elif keyId == "numMinus":
            keycode = Keycode.KEYPAD_MINUS
        elif keyId == "numPlus":
            keycode = Keycode.KEYPAD_PLUS
        elif keyId == "numEnter":
            keycode = Keycode.KEYPAD_ENTER
        elif keyId == "numPeriod":
            keycode = Keycode.KEYPAD_PERIOD
        elif keyId == "numBackslash":
            keycode = Keycode.KEYPAD_BACKSLASH
        elif keyId == "num1":
            keycode = Keycode.KEYPAD_ONE
        elif keyId == "num2":
            keycode = Keycode.KEYPAD_TWO
        elif keyId == "num3":
            keycode = Keycode.KEYPAD_THREE
        elif keyId == "num4":
            keycode = Keycode.KEYPAD_FOUR
        elif keyId == "num5":
            keycode = Keycode.KEYPAD_FIVE
        elif keyId == "num6":
            keycode = Keycode.KEYPAD_SIX
        elif keyId == "num7":
            keycode = Keycode.KEYPAD_SEVEN
        elif keyId == "num8":
            keycode = Keycode.KEYPAD_EIGHT
        elif keyId == "num9":
            keycode = Keycode.KEYPAD_NINE
        elif keyId == "num0":
            keycode = Keycode.KEYPAD_ZERO

        return keycode
