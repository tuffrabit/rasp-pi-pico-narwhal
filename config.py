import stickCommon as sc
import json
import os

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

        # Profile normalization arrives in a later phase; for now only a
        # list replaces the defaults so other shapes can't crash startup.
        profiles = configData.get("profiles")

        if isinstance(profiles, list):
            self.profiles = profiles

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
