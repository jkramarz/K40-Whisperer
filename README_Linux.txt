Setting up K40whisperer on Linux (by Dr. med. Jan Schiefer):

# Requirements

Prerequirements:
* python
* unzip
* udev
* inkscape

## Instructions

1. Create a group for the users who are allowed to use the laser cutter: sudo groupadd lasercutter

2. Add your yourself to this group, replace [YOUR USERNAME] with your unix username: sudo usermod -a -G lasercutter [YOUR USERNAME]

3. Eventually add other users who will use the laser cutter to the group

4. Plug in your laser cutter to your computer

5. Create a udev control file four your laser cutter as root (i will use gedit in this example): sudo gedit /etc/udev/rules.d/97-ctc-lasercutter.rules

Put the following text into the file and replace [VENDOR ID] and [PRODUCT ID] with the information you obtained from lsusb:
SUBSYSTEM=="usb", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="5512", ENV{DEVTYPE}=="usb_device", MODE="0664", GROUP="lasercutter"

Now save the file.

6. Reboot your computer!

7. Download and the K40whisperer source code, for example "K40_Whisperer-0.07_src.zip"

8. Unzip the source code, for example: unzip K40_Whisperer-0.07_src.zip -d /home/[YOUR USERNAME]/

9. Go to the K40 whisperer source directory, for example: cd /home/[YOUR USERNAME]/K40_Whisperer-0.07_src/

10. Install the requires python packages using the following commands:
    pip install lxml
    pip install pyusb
    pip install pillow
    pip install pyclipper

11. Run K40whisperer: python ./k40_whisperer.py
11a. If K40 Whisperer starts but you cannot initialize the laser you can try running using the command: sudo python ./k40_whisperer.py
    If everything works that way you should revisit step 5. because the user is not able to access the usb port.  You can always run using sudo but it is generally a bad practice. 

12. Go to Setting --> General settings

13. Select your laser control board name (usually LASER-M2 which is the default.)

14. If you click the "save" button in the general settings your current settings will be saved for future sessions.
