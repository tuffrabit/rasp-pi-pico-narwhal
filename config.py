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

    def setStickXLow(self, value):
        value = sc.getStickValue(value)

        if value is not None:
            self.stickBoundaries["lowX"] = value

    def setStickXHigh(self, value):
        value = sc.getStickValue(value)

        if value is not None:
            self.stickBoundaries["highX"] = value

    def setStickYLow(self, value):
        value = sc.getStickValue(value)

        if value is not None:
            self.stickBoundaries["lowY"] = value

    def setStickYHigh(self, value):
        value = sc.getStickValue(value)

        if value is not None:
            self.stickBoundaries["highY"] = value

    def setStickXOrientation(self, value):
        try:
            self.stickAxesOrientation["x"]["axis"] = int(value["axis"])
            self.stickAxesOrientation["x"]["reverse"] = bool(value["reverse"])
        except (TypeError, ValueError, KeyError):
            pass

    def setStickYOrientation(self, value):
        try:
            self.stickAxesOrientation["y"]["axis"] = int(value["axis"])
            self.stickAxesOrientation["y"]["reverse"] = bool(value["reverse"])
        except (TypeError, ValueError, KeyError):
            pass

    def setDeadzoneSize(self, value):
        value = sc.getStickValue(value)

        if value is not None:
            self.deadzoneSize = value

        return self.deadzoneSize

    def setKbModeXOffset(self, value):
        value = sc.getStickValue(value)

        if value is not None:
            self.kbModeOffsets["x"] = value

        return self.kbModeOffsets["x"]

    def setKbModeYOffset(self, value):
        value = sc.getStickValue(value)

        if value is not None:
            self.kbModeOffsets["y"] = value

        return self.kbModeOffsets["y"]

    def setKbModeYConeEnd(self, value):
        value = sc.getStickValue(value)

        if value is not None:
            self.kbModeYConeEnd = value

        return self.kbModeYConeEnd

    def loadFromFile(self):
        configData = None

        try:
            with open('config.json', 'r') as configFilePointer:
                configData = json.load(configFilePointer)
        except Exception:
            # Missing or corrupt config file: keep the defaults.
            pass

        if configData:
            if "stickBoundaries" in configData:
                self.stickBoundaries = configData["stickBoundaries"]

            if "stickAxesOrientation" in configData:
                self.stickAxesOrientation = configData["stickAxesOrientation"]

            if "deadzoneSize" in configData:
                self.deadzoneSize = configData["deadzoneSize"]

            if "kbModeOffsets" in configData:
                self.kbModeOffsets = configData["kbModeOffsets"]

            if "kbModeYConeEnd" in configData:
                self.kbModeYConeEnd = configData["kbModeYConeEnd"]

            if "profiles" in configData:
                self.profiles = configData["profiles"]

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
        except Exception:
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
