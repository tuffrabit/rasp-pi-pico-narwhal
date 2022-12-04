class ProfileManager:
    def __init__(self):
        self.config = None
        self.currentProfileIndex = None

    def setConfig(self, config):
        self.config = config

    def getProfileByIndex(self, index):
        profile = None

        if self.config != None and 0 <= index < len(self.config.profiles):
            self.currentProfileIndex = index
            profile = self.config.profiles[index]

        return profile

    def getProfileByName(self, name):
        profile = None

        if self.config != None:
            for tempProfile in self.config.profiles:
                if isinstance(tempProfile, dict) and "name" in tempProfile and tempProfile["name"] == name:
                    profile = tempProfile
                    break

        return profile

    def getInitialProfile(self):
        return self.getProfileByIndex(0)

    def getCurrentProfile(self):
        profile = None

        if self.currentProfileIndex != None:
            profile = self.getProfileByIndex(self.currentProfileIndex)

        return profile

    def getNextProfile(self):
        profile = None

        if self.config != None:
            if self.currentProfileIndex == None:
                profile = self.getInitialProfile()
            else:
                newIndex = None

                if self.currentProfileIndex == len(self.config.profiles) - 1:
                    newIndex = 0
                else:
                    newIndex = self.currentProfileIndex + 1

                profile = self.getProfileByIndex(newIndex)

        return profile

    def getPreviousProfile(self):
        profile = None

        if self.config != None:
            if self.currentProfileIndex == None:
                profile = self.getInitialProfile()
            else:
                newIndex = None

                if self.currentProfileIndex == 0:
                    newIndex = len(self.config.profiles) - 1
                else:
                    newIndex = self.currentProfileIndex - 1

                profile = self.getProfileByIndex(newIndex)

        return profile

    def getProfileNames(self):
        names = []

        if self.config != None and self.config.profiles and len(self.config.profiles) > 0:
            for profile in self.config.profiles:
                if isinstance(profile, dict) and "name" in profile:
                    names.append(profile["name"])

        return names

    def createNewProfile(self, newProfileName):
        success = False

        if newProfileName and self.config:
            newProfile = self.config.getDefaultProfileData(newProfileName)

            if newProfile:
                self.config.profiles.append(newProfile)
                success = True

        return success

    def deleteProfile(self, profileName):
        success = False

        if profileName and self.config:
            indexToRemove = None

            for index, profile in enumerate(self.config.profiles):
                if profile["name"] == profileName:
                    indexToRemove = index
                    break

            if indexToRemove != None:
                del self.config.profiles[indexToRemove]
                success = True

        return success

    def renameProfile(self, newProfileName, oldProfileName):
        success = False

        if newProfileName and oldProfileName and self.config:
            indexToRename = None

            for index, profile in enumerate(self.config.profiles):
                if profile["name"] == oldProfileName:
                    indexToRename = index
                    break

            if indexToRename != None:
                self.config.profiles[indexToRename]["name"] = newProfileName
                success = True

        return success

    def setProfileValue(self, profileName, valueName, value):
        success = False

        if profileName and valueName and value is not None and self.config:
            profileToUpdate = None
            profileIndexToUpdate = None

            for index, profile in enumerate(self.config.profiles):
                if profile["name"] == profileName:
                    profileToUpdate = profile
                    profileIndexToUpdate = index
                    break

            if profileToUpdate and profileIndexToUpdate is not None:
                if valueName.startswith("key"):
                    keyIndex = valueName[3::]

                    if keyIndex.isdigit():
                        keyIndex = int(keyIndex)

                        if keyIndex > -1 and keyIndex < 20:
                            profileToUpdate["keys"][keyIndex] = value
                            success = True
                elif valueName == "thumbButton":
                    profileToUpdate["thumbButton"] = value
                    success = True
                elif valueName == "joystickButton":
                    profileToUpdate["joystickButton"] = value
                    success = True
                elif valueName == "isKbModeEnabled":
                    profileToUpdate["isKbModeEnabled"] = value
                    success = True
                elif valueName.startswith("kb"):
                    kbName = valueName[2::]

                    if kbName == "up":
                        profileToUpdate["kbMode"]["up"] = value
                        success = True
                    elif kbName == "down":
                        profileToUpdate["kbMode"]["down"] = value
                        success = True
                    elif kbName == "left":
                        profileToUpdate["kbMode"]["left"] = value
                        success = True
                    elif kbName == "right":
                        profileToUpdate["kbMode"]["right"] = value
                        success = True
                elif valueName.startswith("dpad"):
                    dpadName = valueName[4::]

                    if dpadName == "up":
                        profileToUpdate["dpad"]["up"] = value
                        success = True
                    elif dpadName == "down":
                        profileToUpdate["dpad"]["down"] = value
                        success = True
                    elif dpadName == "left":
                        profileToUpdate["dpad"]["left"] = value
                        success = True
                    elif dpadName == "right":
                        profileToUpdate["dpad"]["right"] = value
                        success = True
                elif valueName == "rgb" and len(value) == 6:
                    rgb = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

                    if rgb:
                        profileToUpdate["rgb"]["red"] = rgb[0]
                        profileToUpdate["rgb"]["green"] = rgb[1]
                        profileToUpdate["rgb"]["blue"] = rgb[2]
                        success = True

        return success
