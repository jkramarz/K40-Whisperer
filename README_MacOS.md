------------------------------------------------------------------------------------
Thanks to Pete Peterson (@ipetepete on Twitter) for these instructions
for setting up K40 Whisperer on a Mac computer 
------------------------------------------------------------------------------------

# Requirements

* Python 2.7 (this works nicely if you use virtualenv)
* Inkscape (build from source using brew)
* Must be run as `root` -see below for more info

## Instructions

### Install Inkscape

This did not work using the Quartz binary for Inkscape. Only by building from source did it work correctly.
Suggested approach is installing using __Homebrew__:

` brew install caskformula/caskformula/inkscape`

### Install Python & Libraries

Suggested approach is to use [Virtualenv](https://virtualenv.pypa.io/en/stable/) and install Python 2.7 even if your system is currently running 2.7.

__Install requirements:__

`pip install -r requirements.txt`

__Run K40Whisperer__

`sudo python k40_whisperer.py`

_Why does this need to be run as root?_

In general all devices require elevated permissions. To allow PyUSB access to a certain device as non-root, some work needs to be done, namely; create a user-group, set perms to the device when connected as belonging to the group, add your user to the newly created user-group.

Read more here: https://stackoverflow.com/questions/3738173/why-does-pyusb-libusb-require-root-sudo-permissions-on-linux#8582398

This can potentially be automated, but more work needs to be done.



------------------------------------------------------------------------------------
Thanks to Pete Peterson (@ipetepete on Twitter) for these instructions
for setting up K40 Whisperer on a Mac computer 
------------------------------------------------------------------------------------

