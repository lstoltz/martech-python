from datetime import datetime,timezone
import time

def clock_test(sensor_time):
    """Tests the sensor clock time against the system clock time. 
    @param sensor_time -- the sensor time in UTC, 
                            must be formatted as YYYY-mm-ddTHH:MM:SS
    @return -- a string flag
                "PASS" if the two times are within 1 second of each other
                "FAIL" if the two times differ by more than 1 second.
                The 1.5 second buffer allows for the consideration of
                sensor communication and conversion times.
    """
    tz = timezone.utc
    fmt = '%Y-%m-%dT%H:%M:%S'
    sensor = datetime.strptime(sensor_time,fmt).replace(tzinfo = tz)
    sys = datetime.now(tz)
    delta = abs(sys-sensor).total_seconds()
    if delta > 1:
        flag = "FAIL"
    else:
        flag = "PASS"
    return flag

def memory_test(used,total,percentage=25):
    """Tests the sensor used memory against the total memory size.
    @param used_memory -- the used memory of the sensor.
    @param total_memory -- the total memory of the sensor.
    @return -- a string flag
                "PASS" if the used memory is 25% or less of the total.
                "FAIL" if the used memory is greater than 25% of the total.
    """
    if used <= total*(percentage/100):
        flag = "PASS"
    else:
        flag = "FAIL"
    return flag


def wiper_test(sensor,run_wiper_command):
    print('Wiper on {} should move in 5 seconds.'.format(sensor))
    time.sleep(5)
    run_wiper_command
    yn = input('Did the {} wiper move? [Y/N]')
    if 'Y' in yn.upper():
        flag = "PASS"
    else:
        flag == "FAIL"
    return flag
