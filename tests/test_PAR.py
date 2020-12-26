import datetime
from martech.sbs.par import PAR

par = PAR('COM3')  #Instantiate a serial object on the defined port.
connection = par.open_connection(19200) #Open a connection at 19200bps.
if connection is True:  
    par.stop_sampling()
    par.log_data("ON")

    sensor_now = par.get_sensor_datetime()
    system_now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    if sensor_now != system_now:
        par.set_datetime()
    par.print_settings_from_flash()
    par.open_wiper()
    par.close_wiper()
    print(par.collect_data(10))
    print(par.get_data())
    par.log_data("OFF")
    sn = par.get_serial_number()
    fw = par.get_firmware_version()
    used = par.get_memory()
    print('SN: {}'.format(sn))
    print('FW: {}'.format(fw))
    print('Memory Used: {}'.format(used))
    
    
    par.erase_memory()
    
    erased = par.get_memory()
    print(erased)
    print(par.get_data())
    
    par.close_connection()