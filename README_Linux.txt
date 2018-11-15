Setting up K40whisperer on Linux (by Dr. med. Jan Schiefer):

# Requirements

Prerequirements:
* python 2.7.x (python versions 3.x.x and higher will not work)
* unzip
* udev
* inkscape

## Instructions

1. Create a group for the users who are allowed to use the laser cutter: sudo groupadd lasercutter

2. Add your yourself to this group, replace [YOUR USERNAME] with your unix username: sudo usermod -a -G lasercutter [YOUR USERNAME]

3. Eventually add other users who will use the laser cutter to the group

4. Plug in your laser cutter to your computer

5. Find out the usb device id of your laser cutter: lsusb

lsusb will output something like this:
Bus 002 Device 003: ID 04f2:b34c Chicony Electronics Co., Ltd 
Bus 002 Device 002: ID 8087:0024 Intel Corp. Integrated Rate Matching Hub
Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 001 Device 003: ID 8087:07da Intel Corp. 
Bus 001 Device 002: ID 8087:0024 Intel Corp. Integrated Rate Matching Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 004 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 003 Device 003: ID 1a86:5512 QinHeng Electronics CH341 in EPP/MEM/I2C mode, EPP/I2C adapter
Bus 003 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

"QinHeng Electronics CH341 in EPP/MEM/I2C mode, EPP/I2C adapter" is your laser cutter in this case.
In this example "1a86" is the VENDOR ID and "5512" the PRODUCT ID.

6. Create a udev control file four your laser cutter as root (i will use gedit in this example): sudo gedit /etc/udev/rules.d/97-ctc-lasercutter.rules

Put the following text into the file and replace [VENDOR ID] and [PRODUCT ID] with the information you obtained from lsusb:
SUBSYSTEM=="usb", ATTRS{idVendor}=="[VENDOR ID]", ATTRS{idProduct}=="[PRODUCT ID]", ENV{DEVTYPE}=="usb_device", MODE="0664", GROUP="lasercutter"

Now save the file.

6. Reboot your computer!

7. Download and the K40whisperer source code, for example "K40_Whisperer-0.07_src.zip"

8. Unzip the source code, for example: unzip K40_Whisperer-0.07_src.zip -d /home/[YOUR USERNAME]/

9. Go to the K40 whisperer source directory, for example: cd /home/[YOUR USERNAME]/K40_Whisperer-0.07_src/

10. Install the requires python packages: pip install -r requirements.txt

11. Run K40whisperer: python2 ./k40_whisperer.py OR python ./k40_whisperer.py

12. Go to Setting --> General settings

13. Select your laser control board name (usually LASER-M2) and put in the location of the inkscape executable (should be /usr/bin/inkscape in the most cases)

14. HAPPY CUTTING!
