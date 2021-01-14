import datetime
from martech.sbs.sbe49 import SBE49
from martech.sbs.suna import SUNA
from martech.sbs.thetis import THETIS
from martech.sbs.tripletw import TRIPLETW
from martech.xylem.optode4831 import OPTODE4831
import time

#VELPT 1
#ACS 3
#Battery 4
#OCR 6
#Winch 7

#Fire it up.
thetis = THETIS("COM3")
if thetis.open_connection() is True: 
    thetis.power_sensors("ON") #Turn on the sensors.
    thetis.power_pump("OFF")  #Shut off the pump.
    thetis.close_connection()  #Close the connection to prevent confusion.

#SBE49 Passthru
if thetis.open_connection() is True:
    thetis.enter_passthru(5)  #Passthru to CTD.
    thetis.close_connection()
    sbe49 = SBE49("COM3")  #Connect to the CTD.
    if sbe49.open_connection(115200) is True: #Since we are using a passthru, the baud rate must be 115200.
        sbe49.stop_sampling()
        status = sbe49.get_status()
        coeffs = sbe49.get_calibration_coeffs()
        sbe49.exit_passthru()
        sbe49.close_connection()

#Optode4831 Passthru
if thetis.open_connection() is True:
    thetis.enter_passthru(2)
    thetis.close_connection()   
    optode4831 = OPTODE4831("COM3")
    if optode4831.open_connection(115200) is True:
        optode4831.stop_sampling()
        settings = optode4831.get_settings() 
        optode4831.exit_passthru()
        optode4831.close_connection()

#SUNAv2 Passthru
if thetis.open_connection() is True:
    thetis.enter_passthru(8)
    thetis.close_connection()   
    suna = SUNA("COM3")
    if suna.open_connection(115200) is True:
        


#Shut it down.    
if thetis.open_connection() is True:
    thetis.power_sensors("OFF")
    
    
    
    