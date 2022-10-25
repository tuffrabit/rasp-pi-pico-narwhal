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

    def getProfileProperty(self, propertyName, profile):
        profileProperty = None

        if self.checkProfile(profile) and propertyName in profile:
            profileProperty = profile[propertyName]

        return profileProperty

    def getKbModeBinding(self, direction, profile):
        binding = None
        kbModeBindings = self.getProfileProperty("kbMode", profile)

        if isinstance(kbModeBindings, dict) and direction in kbModeBindings:
            binding = self.keyConverter.getKeycodeFromId(kbModeBindings[direction])

        return binding

    def getName(self, profile):
        return self.getProfileProperty("name", profile)

    def getIsKbModeEnabled(self, profile):
        return self.getProfileProperty("isKbModeEnabled", profile)

    def getJoystickButton(self, profile):
        joystickButton = self.getProfileProperty("joystickButton", profile)
        return self.keyConverter.getKeycodeFromId(joystickButton)

    def getKeypadBindings(self, profile):
        bindings = None
        profileKeyBindings = self.getProfileProperty("keys", profile)

        if isinstance(profileKeyBindings, list) and len(profileKeyBindings) > 0:
            bindings = []

            for keyId in profileKeyBindings:
                bindings.append(self.keyConverter.getKeycodeFromId(keyId))

        return bindings

    def getRGBLedValues(self, profile):
        rgbLedValues = self.getProfileProperty("rgb", profile)

        if isinstance(rgbLedValues, dict) == False or "red" not in rgbLedValues or "green" not in rgbLedValues or "blue" not in rgbLedValues:
            rgbLedValues = None

        return rgbLedValues
