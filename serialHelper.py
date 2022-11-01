import usb_cdc
import json

class SerialHelper:
    def __init__(self):
        self.inBytes = bytearray()
        self.profileManager = None

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

                if "getProfiles" in jsonData:
                    self.handleGetProfiles()
                elif "getProfile" in jsonData:
                    self.handleGetProfile(jsonData)

    def handleGetProfiles(self):
        if self.profileManager is not None:
            profileNames = self.profileManager.getProfileNames()

            if profileNames:
                self.write("getProfiles", profileNames)

    def handleGetProfile(self, jsonData):
        if jsonData and self.profileManager is not None:
            profileName = jsonData["getProfile"]
            profile = self.profileManager.getProfileByName(profileName)

            if profile:
                self.write("getProfile", profile)
