import usb_cdc
import json

class SerialHelper:
    def __init__(self):
        self.inBytes = bytearray()
        self.config = None
        self.profileManager = None

    def setConfig(self, config):
        self.config = config

    def setProfileManager(self, profileManager):
        self.profileManager = profileManager

    def read(self):
        out = None

        if usb_cdc.data and usb_cdc.data.in_waiting > 0:
            byte = usb_cdc.data.read(1)
            #print("Serial In Byte: " + str(byte))

            if byte == b'\n':
                print("Serial In: " + self.inBytes.decode("utf-8"))
                out = self.inBytes.decode("ascii")
                self.inBytes = bytearray()
            else:
                self.inBytes += byte

                if len(self.inBytes) == 129:
                    self.inBytes = self.inBytes[128] + self.inBytes[0:127]

        return out

    def write(self, command, data):
        if usb_cdc.data:
            serialOut = bytearray(json.dumps({command: data}) + "\r\n")
            print("Bytes written: " + str(usb_cdc.data.write(serialOut)))

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
                print("jsonData:")
                print(jsonData)
                print("")

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

        return returnAction

    def handleGetGlobalSettings(self):
        if self.config is not None:
            self.write(
                "getGlobalSettings",
                {
                    "stickBoundaries": self.config.stickBoundaries,
                    "deadzoneSize": self.config.deadzoneSize,
                    "kbModeOffsets": self.config.kbModeOffsets
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
