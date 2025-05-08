# UselessArnold

I've created this repository to properly document my efforts in building a useless box with conversational speaker AI features. 
Initially it will work on a Raspberry Pi Zero 2 W, but I plan to split AI features from servo controls and use Raspberry Pi Pico as a slave device.

# Table of Contents
1. Prerequisites - Hardware and software
2. Installation
3. Usage


# Prerequisites - Hardware and software
## Hardware
- Raspberry Pi Zero 2 W
- Adafruit I2S 3W Amplifier or ReSpeaker 2
- Speakers
- Power supply & sd card

## ReSpeaker drivers
You'll need drivers for ReSpeaker before you can utilize it.
Make sure you follow installation guidelines for you OS version. This can cause trouble and you might end up wiping your SD card several times, before you have it running, so make sure you can arecrd and aplay sounds using this card, before anything else.
My trial and error showed that only Bookworm 32-bit Lite works, provided that you carefuly follow the steps. Also note the Pi Zero setup collapsed section.
https://wiki.seeedstudio.com/respeaker_2_mics_pi_hat_raspberry_v2/ ()

## Software
- Raspberry Pi OS Lite
- Python 3.7 or higher
- All python dependencies are listed in requirements.txt

Start with Linux requirements:
Install following packages:
```bash
sudo apt-get install portaudio19-dev, python3-dev, gfortran
```

Create and activate Python environment
```bash
python3 -m venv venv
source venv/bin/activate
```

Then, upgrade pip to latest version
```bash
pip install --upgrade pip setuptools wheel
```

Now, run 
```bash
pip install -r requirements.txt
```

# Testing
=======

To run debugging session using Visual Studio code, first configure your interpreter by:
1. CTRL+Shit+P => Python: Select interpreter => Use recommended venv version
2. CTRL+Shift+D => create a launch.json file and select Python as the environment.
Other issues
## rpi_WS281x
Normally, that library requires sudo access to GPIO pins and there are 2 ways to run this code - either by running sudo on the virtual environment executable, or by granding access to GPIO system to your user. I think the first one is faster, but if you are after permanent solution, you might try following the steps below.
### VENV sudo
```bash
sudo /full/path/to/venv/bin/python /full/path/to/script.py
```
### Granting access to GPIO
The GPIO access can be provided without root permissions by adding your user to the `gpio` group.
Please follow the steps below:

1. Open the terminal and type the following command to add your user to the gpio group:
```bash
sudo usermod -a -G gpio your_username
```
2. You might need to log out and log back in for these changes to take effect.
3. Additionally, you might need to change the permissions of the GPIO device files. To do this, you can add a udev rule. Create a new rule file:
```bash
sudo nano /etc/udev/rules.d/99-gpio.rules
```
4. In the opened file, put the following line, then save and close it:
```bash
SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c '\
chown -R root:gpio /sys/class/gpio && chmod -R 770 /sys/class/gpio;\
chown -R root:gpio /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio;\
chown -R root:gpio /sys$devpath && chmod -R 770 /sys$devpath\
'"
```
5. Finally, restart the udev system by using the following command:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

This way, you will grant permissions to your user to access GPIO pins without needing to run your Python scripts as root. Now you should be able to run your script without using `sudo`, so the error should disappear.

Remember to replace `your_username` with your actual username. 

Note: These instructions are for a Raspberry Pi running a Debian-based Linux distribution like Raspbian or Raspberry Pi OS. If you're using a different Linux distribution, the steps might be slightly different.