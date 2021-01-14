import datetime
from martech.sbs.thetis import THETIS
from martech.sbs.tripletw import TRIPLETW
import time

port = 'COM3'
bps = 115200

thetis = THETIS(port)
if thetis.open_connection(bps) is True: 
    thetis.power_sensors("ON") #Turn on the sensors.
    thetis.power_pump("OFF")  #Shut off the pump
    thetis.enter_passthru(9)  #Passthru to CTD.
    thetis.close_connection()
    triplet = TRIPLETW(port)  #Connect to the CTD.
    if triplet.open_connection(bps) is True: #Since we are using a passthru, the baud rate must be 115200.
        print('Connected to Triplet-w')
