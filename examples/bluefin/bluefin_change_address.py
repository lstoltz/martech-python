#Tested in Python 3 (Spyder 3.3.3) on Windows 10.
from martech.gdms.bluefin import BLUEFIN

port = 'COM11' #COM port the battery is connected to.
address = 0  #Default battery address.

bf = BLUEFIN(port) #Instantiate a serial object specific to the BF 1.5kWh.
if bf.open_connection(9600) is True: #If a connection is made at 9600 bps...
    sn = bf.get_battery_sn(address)    
    old = bf.get_address()
    bf.set_address(1)
    new = bf.get_address()
    
    msg = "Old: {} | New: {}"
    print(msg.format(old,new))
    
    bf.close_connection()