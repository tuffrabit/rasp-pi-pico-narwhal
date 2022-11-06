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
