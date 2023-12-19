import usb_cdc
import json

class SerialHelper:
    def __init__(self):
        self.inBytes = bytearray()
        self.config = None
        self.profileManager = None
        self.stick = None
        self.stickDeadzone = None
        self.kbMode = None

    def setConfig(self, config):
        self.config = config

    def setProfileManager(self, profileManager):
        self.profileManager = profileManager

    def setStickDeadzone(self, stickDeadzone):
        self.stickDeadzone = stickDeadzone

    def setStick(self, stick):
        self.stick = stick

    def setKbMode(self, kbMode):
        self.kbMode = kbMode

    def read(self):
        out = None

        if usb_cdc.data and usb_cdc.data.in_waiting > 0:
            readBytes = usb_cdc.data.read(1)

            if readBytes == b'\n':
                out = self.inBytes.decode("utf-8")

                if "ping" not in out:
                    print(f'Serial In: {out}')

                self.inBytes = bytearray()
            else:
                self.inBytes += readBytes

                if len(self.inBytes) == 129:
                    self.inBytes = self.inBytes[128] + self.inBytes[0:127]

        return out

    def write(self, command, data):
        if usb_cdc.data:
            serialOut = bytearray(json.dumps({command: data}) + "\r\n")
            bytesWritten = str(usb_cdc.data.write(serialOut))

            if "ping" not in serialOut:
                print("Bytes written: " + bytesWritten)

    def checkForCommands(self):
        returnAction = None
        serialOut = self.read()

        if serialOut is not None:
            serialOut = serialOut.strip()

        if serialOut == "areyouatuffpad?":
            self.write("areyouatuffpad?", True)
        elif serialOut is not None:
            jsonData = json.loads(serialOut)

            if jsonData:
                if "ping" not in serialOut:
                    print(f'jsonData: {jsonData}')

                if "getGlobalSettings" in jsonData:
                    self.handleGetGlobalSettings()
                elif "getProfiles" in jsonData:
                    self.handleGetProfiles()
                elif "getActiveProfile" in jsonData:
                    self.handleGetActiveProfile()
                elif "setActiveProfile" in jsonData:
                    returnAction = self.handleSetActiveProfile(jsonData)
                elif "getProfile" in jsonData:
                    self.handleGetProfile(jsonData)
                elif "createNewProfile" in jsonData:
                    self.handleCreateNewProfile(jsonData)
                elif "deleteProfile" in jsonData:
                    self.handleDeleteProfile(jsonData)
                elif "renameProfile" in jsonData:
                    self.handleRenameProfile(jsonData)
                elif "setProfileValue" in jsonData:
                    returnAction = self.handleSetProfileValue(jsonData)
                elif "ping" in jsonData:
                    self.handlePing()
                elif "save" in jsonData:
                    self.handleSave()
                elif "getSaveData" in jsonData:
                    self.handleGetSaveData()
                elif "setStickXHigh" in jsonData:
                    self.handleSetStickXHigh(jsonData)
                elif "setStickXLow" in jsonData:
                    self.handleSetStickXLow(jsonData)
                elif "setStickYHigh" in jsonData:
                    self.handleSetStickYHigh(jsonData)
                elif "setStickYLow" in jsonData:
                    self.handleSetStickYLow(jsonData)
                elif "setStickXOrientation" in jsonData:
                    self.handleSetStickXOrientation(jsonData)
                elif "setStickYOrientation" in jsonData:
                    self.handleSetStickYOrientation(jsonData)
                elif "setDeadzone" in jsonData:
                    self.handleSetDeadzone(jsonData)
                elif "setKbModeXStartOffset" in jsonData:
                    self.handleSetKbModeXStartOffset(jsonData)
                elif "setKbModeYStartOffset" in jsonData:
                    self.handleSetKbModeYStartOffset(jsonData)
                elif "setKbModeYConeEnd" in jsonData:
                    self.handleSetKbModeYConeEnd(jsonData)
                elif "readStickValues" in jsonData:
                    returnAction = self.handleReadStickValues()

        return returnAction

    def handleGetGlobalSettings(self):
        if self.config is not None:
            self.write(
                "getGlobalSettings",
                {
                    "stickBoundaries": self.config.stickBoundaries,
                    "deadzoneSize": self.config.deadzoneSize,
                    "kbModeOffsets": self.config.kbModeOffsets,
                    "kbModeYConeEnd": self.config.kbModeYConeEnd,
                    "stickAxesOrientation": self.config.stickAxesOrientation
                }
            )

    def handleGetProfiles(self):
        if self.profileManager is not None:
            profileNames = self.profileManager.getProfileNames()

            if profileNames:
                self.write("getProfiles", profileNames)

    def handleGetActiveProfile(self):
        if self.profileManager is not None:
            currentProfile = self.profileManager.getCurrentProfile()

            if currentProfile:
                self.write("getActiveProfile", currentProfile["name"])

    def handleSetActiveProfile(self, jsonData):
        success = False
        returnValue = None

        if jsonData and self.profileManager is not None:
            newIndex = None

            for index, profile in enumerate(self.config.profiles):
                if profile and "name" in profile and profile["name"] == jsonData["setActiveProfile"]:
                    newIndex = index
                    break

            if newIndex is not None:
                profile = self.profileManager.getProfileByIndex(newIndex)
                returnValue = {"profileChange": True}

                if profile:
                    success = True

        self.write("setActiveProfile", success)
        return returnValue

    def handleGetProfile(self, jsonData):
        if jsonData and self.profileManager is not None:
            profileName = jsonData["getProfile"]
            profile = self.profileManager.getProfileByName(profileName)

            if profile:
                self.write("getProfile", profile)

    def handleCreateNewProfile(self, jsonData):
        if jsonData and self.profileManager is not None:
            newProfileName = jsonData["createNewProfile"]

            if newProfileName:
                result = self.profileManager.createNewProfile(newProfileName)
                self.write("createNewProfile", result)

    def handleDeleteProfile(self, jsonData):
        if jsonData and self.profileManager is not None:
            profileName = jsonData["deleteProfile"]

            if profileName:
                result = self.profileManager.deleteProfile(profileName)
                self.write("deleteProfile", result)

    def handleRenameProfile(self, jsonData):
        if jsonData and self.profileManager is not None:
            newProfileName = jsonData["renameProfile"]["newProfileName"]
            oldProfileName = jsonData["renameProfile"]["oldProfileName"]

            if newProfileName and oldProfileName:
                result = self.profileManager.renameProfile(newProfileName, oldProfileName)
                self.write("renameProfile", result)

    def handleSetProfileValue(self, jsonData):
        returnValue = None

        if jsonData and self.profileManager is not None:
            profileName = jsonData["setProfileValue"]["profile"]
            valueName = jsonData["setProfileValue"]["valueName"]
            value = jsonData["setProfileValue"]["value"]

            if profileName and valueName and value is not None:
                result = self.profileManager.setProfileValue(profileName, valueName, value)
                returnValue = {"profileChange": True}
                self.write("setProfileValue", result)

        return returnValue

    def handlePing(self):
        self.write("ping", True)

    def handleSave(self):
        if self.config:
            if self.config.saveToFile():
                self.write("save", True)
            else:
                self.write("save", False)

    def handleGetSaveData(self):
        if self.config:
            self.write("getSaveData", self.config.getDataJson())

    def handleSetStickXHigh(self, jsonData):
        result = False

        if jsonData:
            if self.stickDeadzone is not None:
                self.stickDeadzone.setXHigh(jsonData["setStickXHigh"])

            if self.stick is not None:
                self.stick.setXHigh(jsonData["setStickXHigh"])

            result = True

        self.write("setStickXHigh", result)

    def handleSetStickXLow(self, jsonData):
        result = False

        if jsonData:
            if self.stickDeadzone is not None:
                self.stickDeadzone.setXLow(jsonData["setStickXLow"])

            if self.stick is not None:
                self.stick.setXLow(jsonData["setStickXLow"])

            result = True

        self.write("setStickXLow", result)

    def handleSetStickYHigh(self, jsonData):
        result = False

        if jsonData:
            if self.stickDeadzone is not None:
                self.stickDeadzone.setYHigh(jsonData["setStickYHigh"])

            if self.stick is not None:
                self.stick.setYHigh(jsonData["setStickYHigh"])

            result = True

        self.write("setStickYHigh", result)

    def handleSetStickYLow(self, jsonData):
        result = False

        if jsonData:
            if self.stickDeadzone is not None:
                self.stickDeadzone.setYLow(jsonData["setStickYLow"])

            if self.stick is not None:
                self.stick.setYLow(jsonData["setStickYLow"])

            result = True

        self.write("setStickYLow", result)

    def handleSetStickXOrientation(self, jsonData):
        if jsonData and self.config is not None:
            self.config.setStickXOrientation(jsonData["setStickXOrientation"])
            self.write("setStickXOrientation", True)

    def handleSetStickYOrientation(self, jsonData):
        if jsonData and self.config is not None:
            self.config.setStickYOrientation(jsonData["setStickYOrientation"])
            self.write("setStickYOrientation", True)

    def handleSetDeadzone(self, jsonData):
        if jsonData and self.config is not None:
            self.config.setDeadzoneSize(jsonData["setDeadzone"])
            self.stickDeadzone.setDeadzoneBuffer(jsonData["setDeadzone"])
            self.stickDeadzone.initBoundary()
            self.stick.setDeadzone(self.stickDeadzone)
            self.write("setDeadzone", True)

    def handleSetKbModeXStartOffset(self, jsonData):
        if jsonData and self.config is not None and self.kbMode is not None:
            result = self.config.setKbModeXOffset(jsonData["setKbModeXStartOffset"])
            self.kbMode.setXStartOffset(result)
            self.write("setKbModeXStartOffset", True)

    def handleSetKbModeYStartOffset(self, jsonData):
        if jsonData and self.config is not None and self.kbMode is not None:
            result = self.config.setKbModeYOffset(jsonData["setKbModeYStartOffset"])
            self.kbMode.setYStartOffset(result)
            self.write("setKbModeYStartOffset", True)

    def handleSetKbModeYConeEnd(self, jsonData):
        if jsonData and self.config is not None and self.kbMode is not None:
            result = self.config.setKbModeYConeEnd(jsonData["setKbModeYConeEnd"])
            self.kbMode.setYConeEnd(result)
            self.write("setKbModeYConeEnd", True)

    def handleReadStickValues(self):
        return {"readStickValues": True}
