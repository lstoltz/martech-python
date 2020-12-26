'''A test script for driving an ECO Triplet-w.
In this test, we will set the sensor up for sampling at 1Hz on power up.
We will also grab the calibration coefficients so that we can later
confirm that the .DEV file provided by Sea-Bird matches the values found
on the sensor.

Physical Requirements: 
- SBS provided RS232 test cable
- Power supply (7-15 VDC, ~ 1A)
    The ECO Triplet-w will draw up to 200mA when the wiper is running.
- Computer with Python 3 
    Testing was performed on a RPi4 and Windows 10 machine.
    
Initial Commit: Ian Black, 2020-12-13
'''

#Import the module that allows us to drive the ECO Triplet-w.
from martech.sbs.tripletw import TRIPLETW

triplet = TRIPLETW('COM3')  #Instantiate a serial object on the defined port.
connection = triplet.open_connection(19200) #Open a connection at 19200bps.
if connection is True:    
    fw = triplet.get_firmware_version()
    sn = triplet.get_serial_number()
    mem = triplet.get_memory()



    triplet.stop_sampling() 
    triplet.set_datetime()  
    
    
    
    
    
    
    
    
    triplet.close_connection()