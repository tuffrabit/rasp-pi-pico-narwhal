import usb_hid
import usb_cdc
import board
import digitalio
import storage

# For Pi Pico
thumbButton = digitalio.DigitalInOut(board.GP10)
thumbButton.direction = digitalio.Direction.INPUT
thumbButton.pull = digitalio.Pull.UP

# If the switch pin is connected to ground the host OS can write to the drive, otherwise CircuitPython can
if thumbButton.value:
    storage.disable_usb_drive()
    storage.remount("/", False)

usb_cdc.enable(console=True, data=True)

# A conventional DirectInput-style gamepad descriptor: 16 buttons, an 8-way
# hat (POV) switch, and two analog sticks (X/Y and Z/Rz). Keeping the layout
# standard maximizes compatibility with Steam Input and other mapping layers.
GAMEPAD_REPORT_DESCRIPTOR = bytes(
    (
        0x05,
        0x01,  # Usage Page (Generic Desktop Ctrls)
        0x09,
        0x05,  # Usage (Game Pad)
        0xA1,
        0x01,  # Collection (Application)
        0x85,
        0x04,  #   Report ID (4)
        # 16 buttons
        0x05,
        0x09,  #   Usage Page (Button)
        0x19,
        0x01,  #   Usage Minimum (Button 1)
        0x29,
        0x10,  #   Usage Maximum (Button 16)
        0x15,
        0x00,  #   Logical Minimum (0)
        0x25,
        0x01,  #   Logical Maximum (1)
        0x75,
        0x01,  #   Report Size (1)
        0x95,
        0x10,  #   Report Count (16)
        0x81,
        0x02,  #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
        # 8-way hat switch (1-8 clockwise from up, 0 = neutral/centered)
        0x05,
        0x01,  #   Usage Page (Generic Desktop Ctrls)
        0x09,
        0x39,  #   Usage (Hat switch)
        0x15,
        0x01,  #   Logical Minimum (1)
        0x25,
        0x08,  #   Logical Maximum (8)
        0x35,
        0x00,  #   Physical Minimum (0)
        0x46,
        0x3B,
        0x01,  #   Physical Maximum (315)
        0x65,
        0x14,  #   Unit (System: English Rotation, Length: Centimeter)
        0x75,
        0x04,  #   Report Size (4)
        0x95,
        0x01,  #   Report Count (1)
        0x81,
        0x42,  #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,Null Position)
        # 4 bits of padding to byte-align the axes
        0x75,
        0x04,  #   Report Size (4)
        0x95,
        0x01,  #   Report Count (1)
        0x81,
        0x03,  #   Input (Const,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
        # Two analog sticks: X/Y and Z/Rz
        0x15,
        0x81,  #   Logical Minimum (-127)
        0x25,
        0x7F,  #   Logical Maximum (127)
        0x09,
        0x30,  #   Usage (X)
        0x09,
        0x31,  #   Usage (Y)
        0x09,
        0x32,  #   Usage (Z)
        0x09,
        0x35,  #   Usage (Rz)
        0x75,
        0x08,  #   Report Size (8)
        0x95,
        0x04,  #   Report Count (4)
        0x81,
        0x02,  #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
        0xC0,  # End Collection
    )
)

gamepad = usb_hid.Device(
    report_descriptor=GAMEPAD_REPORT_DESCRIPTOR,
    usage_page=0x01,  # Generic Desktop Control
    usage=0x05,  # Gamepad
    report_ids=(4,),  # Descriptor uses report ID 4.
    in_report_lengths=(7,),  # This gamepad sends 7 bytes in its report.
    out_report_lengths=(0,),  # It does not receive any reports.
)

# List the gamepad first so host software classifies the device as a gamepad
# rather than a keyboard that happens to have a gamepad attached.
usb_hid.enable(
    (gamepad, usb_hid.Device.KEYBOARD, usb_hid.Device.CONSUMER_CONTROL)
)
