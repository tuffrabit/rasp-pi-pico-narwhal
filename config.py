import stickCommon as sc
import json
import os

_PROFILE_KB_MODE_DIRECTIONS = ("up", "down", "left", "right")
_PROFILE_DPAD_DIRECTIONS = ("up", "down", "left", "right", "center")
_PROFILE_RGB_CHANNELS = ("red", "green", "blue")

class Config:
    def __init__(self):
        self.stickBoundaries = {
            "lowX": 15000,
            "highX": 52535,
            "lowY": 15000,
            "highY": 52535
        }

        self.stickAxesOrientation = {
            "x": {
                "axis": 0,
                "reverse": False
            },
            "y": {
                "axis": 1,
                "reverse": True
            }
        }

        self.deadzoneSize = 3000
        self.kbModeOffsets = {
            "x": 10,
            "y": 10
        }
        self.kbModeYConeEnd = 90

        self.profiles = [self.getDefaultProfileData("1")]

    def getDefaultProfileData(self, name = ""):
        return {
            "name": name,
            "keys": [
                "1",
                "2",
                "3",
                "4",
                "5",
                "q",
                "w",
                "e",
                "r",
                "y",
                "6",
                "7",
                "8",
                "d",
                "f",
                "9",
                "z",
                "x",
                "c",
                "v"
            ],
            "thumbButton": "space",
            "joystickButton": "leftAlt",
            "isKbModeEnabled": False,
            "kbMode": {
                "up": "up",
                "down": "down",
                "left": "left",
                "right": "right"
            },
            "dpad": {
                "up": "w",
                "down": "s",
                "left": "a",
                "right": "d",
                "center": "g"
            },
            "rgb": {
                "red": 255,
                "green": 0,
                "blue": 0
            }
        }

    def _setStickBoundary(self, key, value):
        boundaries = self.stickBoundaries

        if key == "lowX":
            candidate = sc.getBoundaryValue(value, boundaries["highX"], True)
        elif key == "highX":
            candidate = sc.getBoundaryValue(value, boundaries["lowX"], False)
        elif key == "lowY":
            candidate = sc.getBoundaryValue(value, boundaries["highY"], True)
        else:
            candidate = sc.getBoundaryValue(value, boundaries["lowY"], False)

        if candidate is None:
            return False

        boundaries[key] = candidate
        return True

    def setStickXLow(self, value):
        return self._setStickBoundary("lowX", value)

    def setStickXHigh(self, value):
        return self._setStickBoundary("highX", value)

    def setStickYLow(self, value):
        return self._setStickBoundary("lowY", value)

    def setStickYHigh(self, value):
        return self._setStickBoundary("highY", value)

    def _setStickOrientation(self, axisKey, value):
        orientation = sc.getOrientationValue(value)

        if orientation is None:
            return False

        self.stickAxesOrientation[axisKey]["axis"] = orientation["axis"]
        self.stickAxesOrientation[axisKey]["reverse"] = orientation["reverse"]
        return True

    def setStickXOrientation(self, value):
        return self._setStickOrientation("x", value)

    def setStickYOrientation(self, value):
        return self._setStickOrientation("y", value)

    def setDeadzoneSize(self, value):
        value = sc.getStickValue(value)

        if value is None:
            return False

        self.deadzoneSize = value
        return True

    def setKbModeXOffset(self, value):
        value = sc.getIntValue(value, sc.KB_MODE_VALUE_MIN, sc.KB_MODE_VALUE_MAX)

        if value is None:
            return False

        self.kbModeOffsets["x"] = value
        return True

    def setKbModeYOffset(self, value):
        value = sc.getIntValue(value, sc.KB_MODE_VALUE_MIN, sc.KB_MODE_VALUE_MAX)

        if value is None:
            return False

        self.kbModeOffsets["y"] = value
        return True

    def setKbModeYConeEnd(self, value):
        value = sc.getIntValue(value, sc.KB_MODE_VALUE_MIN, sc.KB_MODE_VALUE_MAX)

        if value is None:
            return False

        self.kbModeYConeEnd = value
        return True

    def _normalizeDirectionBindings(self, defaultBindings, rawBindings, directions):
        # Each direction keeps its default unless the stored value is a valid
        # string binding; unknown nested fields are retained verbatim for
        # forward compatibility.
        bindings = dict(defaultBindings)

        if isinstance(rawBindings, dict):
            for direction in directions:
                if direction in rawBindings and isinstance(rawBindings[direction], str):
                    bindings[direction] = rawBindings[direction]

            for key in rawBindings:
                if key not in bindings:
                    bindings[key] = rawBindings[key]

        return bindings

    def _normalizeRgb(self, defaultRgb, rawRgb):
        rgb = dict(defaultRgb)

        if isinstance(rawRgb, dict):
            for channel in _PROFILE_RGB_CHANNELS:
                if channel in rawRgb:
                    value = sc.getIntValue(rawRgb[channel], 0, 255)

                    if value is not None:
                        rgb[channel] = value

            for key in rawRgb:
                if key not in rgb:
                    rgb[key] = rawRgb[key]

        return rgb

    def _normalizeProfile(self, rawProfile, usedNames):
        # Build each accepted profile from a fresh default so malformed stored
        # data can never leave a known field missing or wrongly typed. Names
        # must be valid and unique; duplicates after the first are skipped.
        if not isinstance(rawProfile, dict):
            return None

        name = sc.getProfileNameValue(rawProfile.get("name"))

        if name is None or name in usedNames:
            return None

        profile = self.getDefaultProfileData(name)

        rawKeys = rawProfile.get("keys")

        if isinstance(rawKeys, list) and len(rawKeys) == sc.MAX_PROFILE_KEY_COUNT:
            keysAreValid = True

            for keyId in rawKeys:
                if not isinstance(keyId, str):
                    keysAreValid = False
                    break

            if keysAreValid:
                profile["keys"] = list(rawKeys)

        if isinstance(rawProfile.get("thumbButton"), str):
            profile["thumbButton"] = rawProfile["thumbButton"]

        if isinstance(rawProfile.get("joystickButton"), str):
            profile["joystickButton"] = rawProfile["joystickButton"]

        if isinstance(rawProfile.get("isKbModeEnabled"), bool):
            profile["isKbModeEnabled"] = rawProfile["isKbModeEnabled"]

        profile["kbMode"] = self._normalizeDirectionBindings(profile["kbMode"], rawProfile.get("kbMode"), _PROFILE_KB_MODE_DIRECTIONS)
        profile["dpad"] = self._normalizeDirectionBindings(profile["dpad"], rawProfile.get("dpad"), _PROFILE_DPAD_DIRECTIONS)
        profile["rgb"] = self._normalizeRgb(profile["rgb"], rawProfile.get("rgb"))

        # Retain unknown top-level fields for forward compatibility.
        for key in rawProfile:
            if key not in profile:
                profile[key] = rawProfile[key]

        return profile

    def _normalizeProfiles(self, rawProfiles):
        normalizedProfiles = []
        usedNames = set()

        if isinstance(rawProfiles, list):
            for rawProfile in rawProfiles:
                if len(normalizedProfiles) >= sc.MAX_PROFILE_COUNT:
                    break

                profile = self._normalizeProfile(rawProfile, usedNames)

                if profile is not None:
                    usedNames.add(profile["name"])
                    normalizedProfiles.append(profile)

        # There is always at least one valid profile to run.
        if len(normalizedProfiles) == 0:
            normalizedProfiles = [self.getDefaultProfileData("1")]

        return normalizedProfiles

    def loadFromFile(self):
        configData = None

        try:
            with open('config.json', 'r') as configFilePointer:
                configData = json.load(configFilePointer)
        except Exception:
            # Missing or corrupt config file: keep the defaults.
            pass

        if not isinstance(configData, dict):
            return

        # Validate each global field before applying it. A missing or
        # invalid field keeps its default while the other fields still load.
        boundaries = configData.get("stickBoundaries")

        if isinstance(boundaries, dict):
            self._setStickBoundary("lowX", boundaries.get("lowX"))
            self._setStickBoundary("highX", boundaries.get("highX"))
            self._setStickBoundary("lowY", boundaries.get("lowY"))
            self._setStickBoundary("highY", boundaries.get("highY"))

        orientation = configData.get("stickAxesOrientation")

        if isinstance(orientation, dict):
            if "x" in orientation:
                self._setStickOrientation("x", orientation["x"])

            if "y" in orientation:
                self._setStickOrientation("y", orientation["y"])

        if "deadzoneSize" in configData:
            self.setDeadzoneSize(configData["deadzoneSize"])

        kbModeOffsets = configData.get("kbModeOffsets")

        if isinstance(kbModeOffsets, dict):
            if "x" in kbModeOffsets:
                self.setKbModeXOffset(kbModeOffsets["x"])

            if "y" in kbModeOffsets:
                self.setKbModeYOffset(kbModeOffsets["y"])

        if "kbModeYConeEnd" in configData:
            self.setKbModeYConeEnd(configData["kbModeYConeEnd"])

        profiles = configData.get("profiles")

        if isinstance(profiles, list):
            self.profiles = self._normalizeProfiles(profiles)

    def saveToFile(self):
        configData = {
            "stickBoundaries": self.stickBoundaries,
            "stickAxesOrientation": self.stickAxesOrientation,
            "deadzoneSize": self.deadzoneSize,
            "kbModeOffsets": self.kbModeOffsets,
            "kbModeYConeEnd": self.kbModeYConeEnd,
            "profiles": self.profiles
        }

        configJson = json.dumps(configData)
        written = 0

        try:
            with open('config.tmp', 'w') as f:
                written = f.write(configJson)
        except Exception as e:
            # Most common cause: filesystem is read-only because the device
            # booted with the thumb button held (host-drive mode). Saving
            # requires booting without it held so boot.py remounts "/" writable.
            print(f'Config save failed: {e}')
            return False

        if written > 0:
            # Rename over the old file so a power loss mid-save can't
            # leave a half-written config.json behind.
            try:
                os.rename('config.tmp', 'config.json')
            except OSError:
                # Some builds won't rename over an existing file.
                os.remove('config.json')
                os.rename('config.tmp', 'config.json')

            return True
        else:
            return False

    def getDataJson(self):
        configData = {
            "stickBoundaries": self.stickBoundaries,
            "stickAxesOrientation": self.stickAxesOrientation,
            "deadzoneSize": self.deadzoneSize,
            "kbModeOffsets": self.kbModeOffsets,
            "kbModeYConeEnd": self.kbModeYConeEnd,
            "profiles": self.profiles
        }

        return json.dumps(configData)
