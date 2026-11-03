import stickCommon as sc

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

    def getProfileIndexByName(self, name):
        index = None

        if self.config != None:
            for tempIndex, tempProfile in enumerate(self.config.profiles):
                if isinstance(tempProfile, dict) and "name" in tempProfile and tempProfile["name"] == name:
                    index = tempIndex
                    break

        return index

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
        if self.config is None:
            return False

        name = sc.getProfileNameValue(newProfileName)

        if name is None:
            return False

        if len(self.config.profiles) >= sc.MAX_PROFILE_COUNT:
            return False

        if self.getProfileIndexByName(name) is not None:
            return False

        self.config.profiles.append(self.config.getDefaultProfileData(name))
        return True

    def deleteProfile(self, profileName):
        if not isinstance(profileName, str) or self.config is None:
            return False

        # The final profile can never be deleted; the device must always
        # have a valid profile to run.
        if len(self.config.profiles) <= 1:
            return False

        indexToRemove = None

        for index, profile in enumerate(self.config.profiles):
            if isinstance(profile, dict) and profile.get("name") == profileName:
                indexToRemove = index
                break

        if indexToRemove is None:
            return False

        del self.config.profiles[indexToRemove]
        success = True

        # Keep the active-profile pointer consistent with the list.
        if self.currentProfileIndex != None:
            if self.currentProfileIndex > indexToRemove:
                self.currentProfileIndex -= 1
            elif self.currentProfileIndex == indexToRemove:
                if len(self.config.profiles) == 0:
                    self.currentProfileIndex = None
                elif self.currentProfileIndex >= len(self.config.profiles):
                    self.currentProfileIndex = len(self.config.profiles) - 1

        return success

    def renameProfile(self, newProfileName, oldProfileName):
        if not isinstance(oldProfileName, str) or self.config is None:
            return False

        newName = sc.getProfileNameValue(newProfileName)

        if newName is None:
            return False

        indexToRename = None

        for index, profile in enumerate(self.config.profiles):
            if isinstance(profile, dict) and profile.get("name") == oldProfileName:
                indexToRename = index
                break

        if indexToRename is None:
            return False

        # Renaming to the current name is a no-op success: no order, name,
        # or runtime change.
        if self.config.profiles[indexToRename]["name"] == newName:
            return True

        if self.getProfileIndexByName(newName) is not None:
            return False

        self.config.profiles[indexToRename]["name"] = newName
        return True

    def reorderProfile(self, profileName, newIndex):
        if not profileName or self.config is None:
            return False

        try:
            newIndex = int(newIndex)
        except (TypeError, ValueError):
            return False

        targetProfileCurrentIndex = self.getProfileIndexByName(profileName)

        if targetProfileCurrentIndex is None or targetProfileCurrentIndex < 0:
            return False

        currentProfile = None

        if self.currentProfileIndex != None and 0 <= self.currentProfileIndex < len(self.config.profiles):
            currentProfile = self.config.profiles[self.currentProfileIndex]

        targetProfile = self.config.profiles[targetProfileCurrentIndex]
        self.config.profiles.pop(targetProfileCurrentIndex)

        if newIndex < 0:
            newIndex = 0
        elif newIndex > len(self.config.profiles):
            newIndex = len(self.config.profiles)

        self.config.profiles.insert(newIndex, targetProfile)

        # Keep the active-profile pointer aimed at the same profile.
        if currentProfile != None:
            for index, profile in enumerate(self.config.profiles):
                if profile is currentProfile:
                    self.currentProfileIndex = index
                    break

        return True

    def setProfileValue(self, profileName, valueName, value):
        success = False

        if self.config and isinstance(profileName, str) and isinstance(valueName, str) and value is not None:
            profileToUpdate = None

            for profile in self.config.profiles:
                if isinstance(profile, dict) and profile.get("name") == profileName:
                    profileToUpdate = profile
                    break

            if profileToUpdate is not None:
                if valueName.startswith("key"):
                    keyIndex = valueName[3::]

                    # Binding values must be strings; key indices are 0-19
                    # and must exist in the actual key list so no slot can be
                    # created past the matrix layout.
                    if isinstance(value, str) and keyIndex.isdigit():
                        keyIndex = int(keyIndex)

                        if isinstance(profileToUpdate.get("keys"), list) and keyIndex > -1 and keyIndex < sc.MAX_PROFILE_KEY_COUNT and keyIndex < len(profileToUpdate["keys"]):
                            profileToUpdate["keys"][keyIndex] = value
                            success = True
                elif valueName == "thumbButton":
                    if isinstance(value, str):
                        profileToUpdate["thumbButton"] = value
                        success = True
                elif valueName == "joystickButton":
                    if isinstance(value, str):
                        profileToUpdate["joystickButton"] = value
                        success = True
                elif valueName == "isKbModeEnabled":
                    if isinstance(value, bool):
                        profileToUpdate["isKbModeEnabled"] = value
                        success = True
                elif valueName.startswith("kb") and isinstance(profileToUpdate.get("kbMode"), dict):
                    kbName = valueName[2::]

                    if isinstance(value, str) and kbName == "up":
                        profileToUpdate["kbMode"]["up"] = value
                        success = True
                    elif isinstance(value, str) and kbName == "down":
                        profileToUpdate["kbMode"]["down"] = value
                        success = True
                    elif isinstance(value, str) and kbName == "left":
                        profileToUpdate["kbMode"]["left"] = value
                        success = True
                    elif isinstance(value, str) and kbName == "right":
                        profileToUpdate["kbMode"]["right"] = value
                        success = True
                elif valueName.startswith("dpad") and isinstance(profileToUpdate.get("dpad"), dict):
                    dpadName = valueName[4::]

                    if isinstance(value, str) and dpadName == "up":
                        profileToUpdate["dpad"]["up"] = value
                        success = True
                    elif isinstance(value, str) and dpadName == "down":
                        profileToUpdate["dpad"]["down"] = value
                        success = True
                    elif isinstance(value, str) and dpadName == "left":
                        profileToUpdate["dpad"]["left"] = value
                        success = True
                    elif isinstance(value, str) and dpadName == "right":
                        profileToUpdate["dpad"]["right"] = value
                        success = True
                    elif isinstance(value, str) and dpadName == "center":
                        profileToUpdate["dpad"]["center"] = value
                        success = True
                elif valueName == "rgb" and isinstance(profileToUpdate.get("rgb"), dict) and isinstance(value, str) and len(value) == 6:
                    try:
                        rgb = tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
                    except ValueError:
                        rgb = None

                    if rgb:
                        profileToUpdate["rgb"]["red"] = rgb[0]
                        profileToUpdate["rgb"]["green"] = rgb[1]
                        profileToUpdate["rgb"]["blue"] = rgb[2]
                        success = True

        return success
