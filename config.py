import  json

class Config:
    def __init__(self):
        self.stickBoundaries = {
            "lowX": 15000,
            "highX": 52535,
            "lowY": 15000,
            "highY": 52535
        }

        self.deadzoneSize = 1000
        self.kbModeOffsets = {
            "x": 10,
            "y": 10
        }

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
                "right": "d"
            },
            "rgb": {
                "red": 255,
                "green": 0,
                "blue": 0
            }
        }

    def loadFromFile(self):
        configFilePointer = None

        try:
            configFilePointer = open('config.json', 'r')
        except:
            pass

        if configFilePointer != None:
            configData = json.load(configFilePointer)
            configFilePointer.close()

            if configData:
                if "stickBoundaries" in configData:
                    self.stickBoundaries = configData["stickBoundaries"]

                if "deadzoneSize" in configData:
                    self.deadzoneSize = configData["deadzoneSize"]

                if "kbModeOffsets" in configData:
                    self.kbModeOffsets = configData["kbModeOffsets"]

                if "profiles" in configData:
                    self.profiles = configData["profiles"]
