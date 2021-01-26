'''An example script that sets the time on the control can to your computer's
system time in UTC. 
'''

from martech.sbs.thetis import THETIS

port = 'COM3'
thetis = THETIS(port)
if thetis.open_connection(115200) is True:
    info = thetis.get_version()
    print('Connected to {}.'.format(info['profiler_id']))
    if thetis.set_datetime(tzo=0) is True:
        print('Time has been updated on the control can.')
    if thetis.close_connection() is True:
        exit
        
        