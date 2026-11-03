import usb_cdc
import json

# A single inbound command line may be at most this many bytes. Once a line
# exceeds the limit its bytes are discarded through its next newline so the
# tail of an oversized line can never merge with the next valid command.
MAX_COMMAND_LENGTH = 512

def _isNonEmptyString(value):
    return isinstance(value, str) and len(value) > 0

def _getIntegerCompatibleValue(value):
    # Matches what ProfileManager.reorderProfile() already accepts through
    # int(): real integers, integer-valued floats, and integer strings.
    # Booleans are rejected so True can never become position 1.
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        number = int(value)

        if number != value:
            return None

        return number

    if isinstance(value, str):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return None

class SerialHelper:
    def __init__(self):
        self.inBytes = bytearray()
        self.discardThroughNewline = False
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

    def _appendIncomingBytes(self, readBytes):
        if self.discardThroughNewline:
            newlineIndex = readBytes.find(b'\n')

            if newlineIndex == -1:
                # Still inside the oversized line; keep discarding.
                return

            # The oversized line ends inside this chunk; drop it and resume
            # normal buffering with the bytes that follow its newline.
            readBytes = readBytes[newlineIndex + 1:]
            self.discardThroughNewline = False

            if not readBytes:
                return

        self.inBytes += readBytes

        # A valid line is at most MAX_COMMAND_LENGTH bytes before its
        # newline. If no newline has arrived by then, the line can never be
        # valid: discard everything through its next newline.
        if self.inBytes.find(b'\n') == -1 and len(self.inBytes) > MAX_COMMAND_LENGTH:
            self.inBytes = bytearray()
            self.discardThroughNewline = True

    def read(self):
        out = None

        if usb_cdc.data:
            if usb_cdc.data.in_waiting > 0:
                readBytes = usb_cdc.data.read(usb_cdc.data.in_waiting)

                if readBytes:
                    self._appendIncomingBytes(readBytes)

            newlineIndex = self.inBytes.find(b'\n')

            if newlineIndex > -1:
                if newlineIndex > MAX_COMMAND_LENGTH:
                    # The line exceeds the command limit. Discard it
                    # entirely; its tail must never combine with the next
                    # command. The next valid line, if any, is picked up on
                    # a later read so one iteration still handles at most
                    # one complete inbound command.
                    self.inBytes = self.inBytes[newlineIndex + 1:]
                else:
                    try:
                        out = self.inBytes[:newlineIndex].decode("utf-8")
                    except UnicodeError:
                        out = ""

                    self.inBytes = self.inBytes[newlineIndex + 1:]

                    if "ping" not in out:
                        print(f'Serial In: {out}')

        return out

    def write(self, command, data):
        if usb_cdc.data:
            serialOut = json.dumps({command: data}) + "\r\n"
            bytesWritten = str(usb_cdc.data.write(serialOut.encode("utf-8")))

            if "ping" not in serialOut:
                print("Bytes written: " + bytesWritten)

    def checkForCommands(self):
        returnAction = None
        serialOut = self.read()

        if serialOut is not None:
            serialOut = serialOut.strip()

        if serialOut == "areyouatuffpad?":
            self.write("areyouatuffpad?", True)
        elif serialOut:
            jsonData = None

            try:
                jsonData = json.loads(serialOut)
            except ValueError:
                print(f'Invalid JSON received: {serialOut}')

            # The app sends value-less commands as single-element arrays
            # (e.g. ["getProfiles"]); normalize them to dict form.
            if isinstance(jsonData, list) and len(jsonData) == 1 and isinstance(jsonData[0], str):
                jsonData = {jsonData[0]: True}

            if jsonData and isinstance(jsonData, dict):
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
                    returnAction = self.handleDeleteProfile(jsonData)
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
                    returnAction = self.handleSetStickXOrientation(jsonData)
                elif "setStickYOrientation" in jsonData:
                    returnAction = self.handleSetStickYOrientation(jsonData)
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
                elif "reorderProfile" in jsonData:
                    self.handleReorderProfile(jsonData)

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
        # Always respond, even with an empty list, so the management app
        # never waits on a silently dropped query.
        if self.profileManager is not None:
            self.write("getProfiles", self.profileManager.getProfileNames())

    def handleGetActiveProfile(self):
        if self.profileManager is not None:
            currentProfile = self.profileManager.getCurrentProfile()
            profileName = None

            if isinstance(currentProfile, dict):
                profileName = currentProfile.get("name")

            self.write("getActiveProfile", profileName)

    def handleSetActiveProfile(self, jsonData):
        success = False
        returnValue = None
        profileName = jsonData["setActiveProfile"]

        if self.profileManager is not None and _isNonEmptyString(profileName):
            newIndex = self.profileManager.getProfileIndexByName(profileName)

            if newIndex is not None:
                profile = self.profileManager.getProfileByIndex(newIndex)

                if profile is not None:
                    success = True

        if success:
            returnValue = {"profileChange": True}

        self.write("setActiveProfile", success)
        return returnValue

    def handleGetProfile(self, jsonData):
        if self.profileManager is not None:
            profileName = jsonData["getProfile"]
            profile = None

            if _isNonEmptyString(profileName):
                foundProfile = self.profileManager.getProfileByName(profileName)

                if foundProfile is not None:
                    profile = foundProfile

            self.write("getProfile", profile)

    def handleCreateNewProfile(self, jsonData):
        result = False
        newProfileName = jsonData["createNewProfile"]

        if self.profileManager is not None and _isNonEmptyString(newProfileName):
            result = self.profileManager.createNewProfile(newProfileName)

        self.write("createNewProfile", result)

    def handleDeleteProfile(self, jsonData):
        returnValue = None
        result = False
        profileName = jsonData["deleteProfile"]

        if self.profileManager is not None and _isNonEmptyString(profileName):
            result = self.profileManager.deleteProfile(profileName)

            if result:
                # The active profile may have moved or been deleted; have the
                # main loop reload it so it isn't running a stale profile.
                returnValue = {"profileChange": True}

        self.write("deleteProfile", result)
        return returnValue

    def handleRenameProfile(self, jsonData):
        result = False
        payload = jsonData["renameProfile"]

        if self.profileManager is not None and isinstance(payload, dict):
            oldProfileName = payload.get("oldProfileName")
            newProfileName = payload.get("newProfileName")

            if _isNonEmptyString(oldProfileName) and _isNonEmptyString(newProfileName):
                result = self.profileManager.renameProfile(newProfileName, oldProfileName)

        self.write("renameProfile", result)

    def handleSetProfileValue(self, jsonData):
        # Request a runtime profile reload only when the mutation succeeded;
        # a rejected value must leave the running profile untouched.
        returnValue = None
        result = False
        payload = jsonData["setProfileValue"]

        if self.profileManager is not None and isinstance(payload, dict):
            profileName = payload.get("profile")
            valueName = payload.get("valueName")

            if "value" in payload:
                value = payload["value"]

                if isinstance(profileName, str) and isinstance(valueName, str) and value is not None:
                    result = self.profileManager.setProfileValue(profileName, valueName, value)

        if result and self.profileManager is not None:
            # Editing an inactive profile needs no runtime rebuild; only a
            # successful edit of the active profile reloads live bindings.
            currentProfile = self.profileManager.getCurrentProfile()

            if isinstance(currentProfile, dict) and currentProfile.get("name") == profileName:
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

        if self.config is not None:
            result = self.config.setStickXHigh(jsonData["setStickXHigh"])

            if result:
                # Propagate the validated stored value, not the raw payload,
                # so runtime objects never see an unconverted string.
                value = self.config.stickBoundaries["highX"]

                if self.stickDeadzone is not None:
                    self.stickDeadzone.setXHigh(value)

                if self.stick is not None:
                    self.stick.setXHigh(value)

        self.write("setStickXHigh", result)

    def handleSetStickXLow(self, jsonData):
        result = False

        if self.config is not None:
            result = self.config.setStickXLow(jsonData["setStickXLow"])

            if result:
                value = self.config.stickBoundaries["lowX"]

                if self.stickDeadzone is not None:
                    self.stickDeadzone.setXLow(value)

                if self.stick is not None:
                    self.stick.setXLow(value)

        self.write("setStickXLow", result)

    def handleSetStickYHigh(self, jsonData):
        result = False

        if self.config is not None:
            result = self.config.setStickYHigh(jsonData["setStickYHigh"])

            if result:
                value = self.config.stickBoundaries["highY"]

                if self.stickDeadzone is not None:
                    self.stickDeadzone.setYHigh(value)

                if self.stick is not None:
                    self.stick.setYHigh(value)

        self.write("setStickYHigh", result)

    def handleSetStickYLow(self, jsonData):
        result = False

        if self.config is not None:
            result = self.config.setStickYLow(jsonData["setStickYLow"])

            if result:
                value = self.config.stickBoundaries["lowY"]

                if self.stickDeadzone is not None:
                    self.stickDeadzone.setYLow(value)

                if self.stick is not None:
                    self.stick.setYLow(value)

        self.write("setStickYLow", result)

    def handleSetStickXOrientation(self, jsonData):
        returnValue = None

        if self.config is not None:
            result = self.config.setStickXOrientation(jsonData["setStickXOrientation"])
            self.write("setStickXOrientation", result)

            if result:
                returnValue = {"orientationChange": True}

        return returnValue

    def handleSetStickYOrientation(self, jsonData):
        returnValue = None

        if self.config is not None:
            result = self.config.setStickYOrientation(jsonData["setStickYOrientation"])
            self.write("setStickYOrientation", result)

            if result:
                returnValue = {"orientationChange": True}

        return returnValue

    def handleSetDeadzone(self, jsonData):
        result = False

        if self.config is not None:
            result = self.config.setDeadzoneSize(jsonData["setDeadzone"])

            if result:
                value = self.config.deadzoneSize

                if self.stickDeadzone is not None:
                    self.stickDeadzone.setDeadzoneBuffer(value)
                    self.stickDeadzone.initBoundary()

                if self.stick is not None:
                    self.stick.setDeadzone(self.stickDeadzone)

        self.write("setDeadzone", result)

    def handleSetKbModeXStartOffset(self, jsonData):
        result = False

        if self.config is not None and self.kbMode is not None:
            result = self.config.setKbModeXOffset(jsonData["setKbModeXStartOffset"])

            if result:
                self.kbMode.setXStartOffset(self.config.kbModeOffsets["x"])

        self.write("setKbModeXStartOffset", result)

    def handleSetKbModeYStartOffset(self, jsonData):
        result = False

        if self.config is not None and self.kbMode is not None:
            result = self.config.setKbModeYOffset(jsonData["setKbModeYStartOffset"])

            if result:
                self.kbMode.setYStartOffset(self.config.kbModeOffsets["y"])

        self.write("setKbModeYStartOffset", result)

    def handleSetKbModeYConeEnd(self, jsonData):
        result = False

        if self.config is not None and self.kbMode is not None:
            result = self.config.setKbModeYConeEnd(jsonData["setKbModeYConeEnd"])

            if result:
                self.kbMode.setYConeEnd(self.config.kbModeYConeEnd)

        self.write("setKbModeYConeEnd", result)

    def handleReadStickValues(self):
        return {"readStickValues": True}

    def handleReorderProfile(self, jsonData):
        result = False
        payload = jsonData["reorderProfile"]

        if self.profileManager is not None and isinstance(payload, dict):
            profileName = payload.get("profileName")
            position = _getIntegerCompatibleValue(payload.get("position"))

            if _isNonEmptyString(profileName) and position is not None:
                result = self.profileManager.reorderProfile(profileName, position)

        self.write("reorderProfile", result)
