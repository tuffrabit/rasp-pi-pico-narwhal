class ProfileHelper:
    def __init__(self):
        self.keyConverter = None

    def setKeyConverter(self, keyConverter):
        self.keyConverter = keyConverter

    def checkProfile(self, profile):
        isValid = False

        if isinstance(profile, dict):
            isValid = True

        return isValid

    def getAction(self, name):
        action = {"type": None, "action": None}

        if name == "nextProfile" or name == "previousProfile":
            action["type"] = 3
            action["action"] = name
        elif name.startswith("gamepadButton"):
            action["type"] = 2
            action["action"] = int(name[13:])
        else:
            action["type"] = 1
            action["action"] = self.keyConverter.getKeycodeFromId(name)

        return action

    def getProfileProperty(self, propertyName, profile):
        profileProperty = None

        if self.checkProfile(profile) and propertyName in profile:
            profileProperty = profile[propertyName]

        return profileProperty

    def getKbModeBinding(self, direction, profile):
        binding = None
        kbModeBindings = self.getProfileProperty("kbMode", profile)

        if isinstance(kbModeBindings, dict) and direction in kbModeBindings:
            binding = self.getAction(kbModeBindings[direction])

        return binding

    def getName(self, profile):
        return self.getProfileProperty("name", profile)

    def getIsKbModeEnabled(self, profile):
        return self.getProfileProperty("isKbModeEnabled", profile)

    def getJoystickButton(self, profile):
        joystickButton = self.getProfileProperty("joystickButton", profile)
        return self.getAction(joystickButton)

    def getThumbButton(self, profile):
        thumbButton = self.getProfileProperty("thumbButton", profile)
        return self.getAction(thumbButton)

    def getKeypadBindings(self, profile):
        bindings = None
        profileKeyBindings = self.getProfileProperty("keys", profile)

        if isinstance(profileKeyBindings, list) and len(profileKeyBindings) > 0:
            bindings = []

            for keyId in profileKeyBindings:
                bindings.append(self.getAction(keyId))

        return bindings

    def getRGBLedValues(self, profile):
        rgbLedValues = self.getProfileProperty("rgb", profile)

        if isinstance(rgbLedValues, dict) == False or "red" not in rgbLedValues or "green" not in rgbLedValues or "blue" not in rgbLedValues:
            rgbLedValues = None

        return rgbLedValues
