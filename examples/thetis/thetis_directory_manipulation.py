"""An example script that moves to the control can root directory, then creates
a DATA directory, then creates a subdirectory titled by YYYYMMDD, then creates
a log, power cycles the sensors for 30 seconds, then closes the log.
"""
from datetime import datetime,timezone
from martech.sbs.thetis import THETIS
import time


port = 'COM3'
thetis = THETIS(port)
if thetis.open_connection(115200) is True:
    info = thetis.get_version()
    print('Connected to {}.'.format(info['profiler_id']))
    
    if thetis.change_to_root_directory('PC') is True:
        thetis.make_directory("DATA","PC")
        if "DATA" in thetis.list_subdirectories("PC"):
            thetis.change_directory("DATA")
        
        today = datetime.now(timezone.utc).strftime('%Y%m%d')
        
        thetis.make_directory(today,"PC")
        thetis.change_directory(today)
        wd = thetis.get_working_directory('PC')
        print(wd)
        
        thetis.logging("ON","PC")
        thetis.set_sensors_power("ON")
        time.sleep(1)
        thetis.set_pump_power("OFF")
        time.sleep(30)
        thetis.set_sensors_power("OFF")
        time.sleep(10)
        thetis.logging("OFF","PC")
        
        files = thetis.list_files("PC")       
        filenames = []
        for filename in files:
            filenames.append(filename[0])
        print(filenames)
        
        yn = input("Do you want to delete the files you just created?")
        if 'Y' in yn.upper():
            ppds = [f for f in filenames if 'PPD' in f]
            acds = [f for f in filenames if 'ACD' in f]
            snds = [f for f in filenames if 'SND' in f]
    
            #Delete the decimated files.
            thetis.delete_file(ppds,"PC")  
            thetis.delete_file(acds,"PC")
            thetis.delete_file(snds,"PC")
            thetis.delete_file(filenames,"PC") #Delete the rest.
        
        yn2 = input("Do you want to delete the directory you just created?")
        if 'Y' in yn2.upper():
            files = thetis.list_files("PC")
            if files == []: #If the directory is empty.
                thetis.change_directory('..') #Move back one directory.
                if thetis.remove_directory(today) is True:
                    print('Directory removed.')
                    subs = thetis.list_subdirectories()
                    print(subs)
                    if today not in subs:
                        print('Success!')
                
                