from datetime import datetime,timezone
from martech.sbs.thetis import THETIS
import os
import time

directory = "C:/Users/Ian/Desktop/QCT"
os.chdir(directory)

port = "COM3"
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
opr8r = input("QCT Conductor: ")
cspp = THETIS(port)
if cspp.open_connection() is False:
    print("Unable to connect to profiler.")
    exit

info = cspp.get_version()
sn = info['profiler_id'][-1].rjust(3,"0")
log = open("QCT_WLP-{}_{}.txt".format(sn,today),'w')
log.write('Profiler: WLP-{}\n'.format(sn))
log.write("Operator: {}\n".format(opr8r))
log.write("QCT Date: {}\n".format(today))

cspp.change_to_root_directory("PC")
cspp.make_directory("TESTING","PC")
cspp.change_directory("TESTING","PC")
test_dir = "QT{}".format(datetime.now(timezone.utc).strftime("%y%m%d"))
cspp.make_directory(test_dir,"PC")
if cspp.change_directory(test_dir) is True:
    log.write("QCT Directory: {}\n".format(test_dir))
else:
    exit


log.write("---SETTINGS---\n")
dt,dt_msg = cspp.set_datetime()
log.write(dt_msg + '\n')
pkd,pkd_msg = cspp.set_parking_depth(65)
log.write(pkd_msg + '\n')
rd,rd_msg = cspp.set_radio_depth(1.0)
log.write(rd_msg + '\n')
gpsp,gpsp_msg = cspp.set_gps_power("OFF")
log.write(gpsp_msg + '\n')
ggf,ggf_msg = cspp.set_gps_acquistion_after_profile("OFF")
log.write(ggf_msg + '\n')
do,do_msg = cspp.set_depth_offset(0.6)
log.write(do_msg + '\n')
blv,blv_msg = cspp.set_battery_thresholds(28.5,28.5)
log.write(blv_msg + '\n')
slsf,slsf_msg = cspp.set_slsf(1.45)
log.write(slsf_msg + '\n')
scs,scs_msg = cspp.set_scooch()
log.write(scs_msg + '\n')
sta,sta_msg = cspp.set_sta(0.7)
log.write(sta_msg+'\n')
num,num_msg = cspp.set_profile_number(0)
log.write(num_msg + '\n')
hld,hld_msg = cspp.set_hld(1)
log.write(hld_msg + '\n')
whe,whe_msg = cspp.turn_off_wave_height_estimator()
log.write(whe_msg + '\n')
bd,bd_msg = cspp.set_breakaway_depth()
log.write(bd_msg + '\n')


cspp.logging("ON")
cspp.set_sensors_power("ON")
cspp.set_pump_power("OFF")
time.sleep(60)
cspp.set_sensors_power("OFF")
time.sleep(30)
cspp.logging("OFF")
time.sleep(1)
files = cspp.list_files('PC')
filenames = []
sizes = []
for file in files:
    filenames.append(file[0])
    sizes.append(file[1])
ppds = [f for f in filenames if 'PPD' in f]
snds = [f for f in filenames if 'SND' in f]
acds = [f for f in filenames if 'ACD' in f]
ppbs = [f for f in filenames if 'PPB' in f]
snas = [f for f in filenames if 'SNA' in f]
acss = [f for f in filenames if 'ACS' in f]
dbgs = [f for f in filenames if 'DBG' in f]
cspp.offload_files(snds,directory)
cspp.offload_files(snas,directory)
cspp.offload_files(ppds,directory)
cspp.offload_files(ppbs,directory)
cspp.offload_files(acds,directory)
cspp.offload_files(acss,directory)
cspp.offload_files(dbgs,directory)
log.write("QCT Files: ")
for filename in filenames:
    if filename == filenames[-1]:
        log.write(filename + '\n')
    else:
        log.write(filename + ', ')








log.close()
cspp.close_connection()