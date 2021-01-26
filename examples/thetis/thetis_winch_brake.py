'''An example script that will power cycle the winch and brake state.'''

from martech.sbs.thetis import THETIS
import time

port = 'COM3'
thetis = THETIS(port)
if thetis.open_connection(115200) is True:
    info = thetis.get_version()
    print('Connected to {}.'.format(info['profiler_id']))
    thetis.send_break()   
    if thetis.set_winch_power("ON") is True:
        time.sleep(3)
        thetis.set_winch_brake("OFF")
        time.sleep(5)
        thetis.set_winch_brake("ON")
        time.sleep(3)
        if thetis.set_winch_power("OFF") is True:
            thetis.close_connection()