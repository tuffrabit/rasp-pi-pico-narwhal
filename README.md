# rasp-pi-pico-narwhal
Firmware for the TuFFpad on the RP2040 platform (Raspberry Pi Pico)
## Flashing

 1. Download a [release](https://github.com/tuffrabit/rasp-pi-pico-narwhal/releases) to your PC
 2. If you downloaded a zip, unzip it
 3. Unplug your tuffpad
 4. Hold down the thumb key/spacebar
 5. Plug in the tuffpad while holding down that key, you should see a new drive called CIRCUITPY appear
 6. In the new downloaded and unzipped firmware folder, select everything except for the .gitignore file
 7. Copy and then paste into the CIRCUITPY drive choosing to overwrite everything
 8. The tuffpad should auto reboot
 9. Unplug and replug the tuffpad so the CIRCUITPY drive disappears

**Be sure to match the version of the [management app](https://github.com/tuffrabit/godot-narwhal-manager/releases) to the version of the firmware your tuffpad is running**
