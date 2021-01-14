from datetime import datetime,timezone

def clock_test(sensor_time):
    """Tests the sensor clock time against the system clock time. 
    @param sensor_time -- the sensor time in UTC, 
                            must be formatted as YYYY-mm-ddTHH:MM:SS
    @return -- a string flag
                "PASS" if the two times are within 1 second of each other
                "FAIL" if the two times differ by more than 1 second.
                The one second buffer allows for the consideration of
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