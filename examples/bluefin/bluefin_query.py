#Tested in Python 3 (Spyder 3.3.3) on Windows 10.
from datetime import datetime,timezone
from martech.gdms.bluefin import BLUEFIN
import os

os.chdir("C:/Users/Ian/Documents/GitHub/examples/bluefin")

opr8r = 'Ian'
port = 'COM4' #COM port the battery is connected to.
address = 0  #Default battery address.

bf = BLUEFIN(port) #Instantiate a serial object specific to the BF 1.5kWh.
if bf.open_connection(9600) is True: #If a connection is made at 9600 bps...
    sn = bf.get_battery_sn(address)    
    actual = bf.get_address()
    fw = bf.get_fw_version(address)
    device = bf.get_device_sn(address)
    model = bf.get_battery_model(address)
    water = bf.water_detected(address)
    temp = bf.get_temperature(address)
    state,state_msg = bf.get_battery_state(address)
    error,error_msg = bf.get_error_state(address)
    v = bf.get_voltage(address)
    mincell = bf.get_min_cell_voltage(address)
    maxcell = bf.get_max_cell_voltage(address)
    balance = bf.balance_test(address)
    runtime = bf.get_runtime(address)
    h = int(runtime[0])
    m = int(runtime[1])
    s = int(runtime[2])
    bf.output_off(address)
    bf.close_connection()

    #Throw it all into a text file.
    today = datetime.now(timezone.utc).date().strftime('%Y-%m-%d')
    filename = 'bf_{}_report_{}.txt'.format(sn,today)
    with open(filename,'w') as f:
        f.write('Operator: {}\n'.format(opr8r))
        f.write('Date: {}\n'.format(today))
        f.write('\n')
        f.write('Battery Serial Number: {}\n'.format(sn))
        f.write('Battery Board Serial Number: {}\n'.format(device))
        f.write('Battery Board Model: {}\n'.format(model))
        f.write('Battery Board Firmware: {}\n'.format(fw))
        f.write('Battery Address: {}\n'.format(actual))
        f.write('Battery State: {}\n'.format(state_msg))
        f.write('Error State: {}\n'.format(error_msg))
        if water is False:
            f.write('Water Intrusion Detected: False\n')
        elif water is True:
            f.write('Water Intrusion Detected: True\n')
        f.write('Overall Voltage: {}\n'.format(v))
        f.write('Minimum Cell Voltage: {}\n'.format(mincell))
        f.write('Maximum Cell Voltage: {}\n'.format(maxcell))
        f.write('Battery Temperature: {}\n'.format(temp))
        f.write('Battery has been on for {}h, {}m, {}s.\n'.format(h,m,s))
        f.write('Balance Test Result: {}\n'.format(balance))
        

