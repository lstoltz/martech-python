# martech-python
martech-python is a set of modules for communicating with a variety of oceanographic sensors over serial.
It is intended to be run on a Raspberry Pi, but can be deployed on Windows or MacOS systems with some modification.

## Dependencies
Every module heavily depends on the PySerial package.
To install PySerial...

`pip3 install pyserial`

The martech.sbs.suna module requires use of the XMODEM package if transferring datafiles.
To install XMODEM...

`pip3 install xmodem`