import datetime
from martech.sbs.thetis import THETIS
import time

def get_time():
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    return now

def y_log_msg(qct_log,user_input,msg):
    if "Y" in user_input.upper():
        qct_log.write("{}, {}".format(user_input,msg))


#Header Info
input("If at any point during this QCT the answer to a prompt is no, the QCT should be stopped and the issue resolved before proceeding. Hit enter to continue.")
opr8r = input('QCT Conductor: ')
doc_num = input('Enter the sequential QCT form number: ')
doc_num = "3310-00200-{}".format(doc_num.rjust(5,'0'))
qct_log = open("QCT_LOG_{}.txt".format(doc_num),"w")
host = input('Enter the JProfilerHost version: ')
processor = input('Enter the JMAFileProcessor version: ')
today = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
qct_log.write("{}, Operator: {}\n".format(get_time(),opr8r))
qct_log.write("{}, QCT performed on {}\n".format(get_time(),today))
qct_log.write("{}, Document Number: {}\n".format(get_time(),doc_num))
qct_log.write("{}, JProfilerHost Version: {}\n".format(get_time(),host))

#Physical Inspection
print("Physically inspect the profiler.")
components = input("Are sensor components present and in reasonable condition? [Y/N]")
if "Y" in components.upper():
    qct_log.write("{}, Sensor components look okay.".format(get_time()))

cables = input("Are sensor cables present and connected appropriately? [Y/N]")
hardware = input("Are hardware components present and in reasonable condition? [Y/N]")

#Sensor Serial Numbers
print("Gather sensor serial numbers from vendor documentation or serial number stickers.")
print("If sensor serial numbers are not present, stop this QCT and resolve.")
print("If sensor serial numbers are not visible, stop this QCT and resolve.")
sbe49_sn = input("Enter the SBE 49 SN (49-XXX): ")
nrtk_aqd = input("Enter Nortek AQD SN: ")
nrtk_aqs = input("Enter Nortek AQS SN: ")
optode_sn = input("Enter Optode 4831 SN: ")
ocr_sn = input("Enter OCR-507 SN: ")
trip_sn = input("Enter ECO Triplet-w SN: ")
suna_sn = input("Enter SUNAv2 SN: ")
acs_sn = input("Enter ACS SN: ")
par_sn = input("Enter ECO PAR SN: ")
atm_sn = input("Enter ATM-914 Case SN: ")
ducer_sn = input("Enter ATM-914 Transducer SN: ")
winch_sn = input("Enter Winch SN: ")
ibcn_head = input("Enter iBCN head SN: ")
ibcn_body = input("Enter iBCN body SN: ")
flasher_sn = input("Enter Flasher SN: ")
pba1_sn = input("Enter PBA #1 SN: ")
pba2_sn = input("Enter PBA #2 SN: ")

                
#Calibration Certificates
print("Gather sensor calibration certificates.")
print("If sensor calibration certificates are missing, stop this QCT and resolve.")
print("If sensor calibration certificates are incomplete, stop this QCT and resolve.")
certs = input("Are all calibration certificates present? [Y/N]")

#Start
port = input("Enter profiler COM port: ")
print("Attach a serial cable and charged batteries to the profiler.")
input("Apply power to the profiler. Once power is supplied, hit enter to continue.")
thetis = THETIS(port)
if thetis.connection() is True:
    version_info = thetis.get_version()
    
    
    
    qct_log.write("{}, WLP-00{} connected on port {}\n".format(get_time(),version_info[0],port))
    directory = "qct"
    thetis.make_directory(directory)
    thetis.change_directory(directory)
    qct_log.write("{}, Profiler Test Directory: {}\n".format(get_time(),directory()))
    
    thetis.logging("ON")
    qct_log.write("{},Profiler logging on".format(get_time()))

    #Sensors
    print("Sensors will now power up and sample for 60 seconds. The pump will remain on for 10 seconds and then shut off.")
    print("Please observe components such as wipers.")
    input("To power up sensors, hit enter to continue.")
    thetis.power_sensors("ON")
    qct_log.write("{}, Sensors on".format(get_time()))
    time.sleep(10)
    thetis.power_pump("OFF")
    pmp = input("Did the pump shut off? [Y/N]")
    if pmp.upper() == "Y":
        qct_log.write("{},Pump off".format(get_time()))
    print("Next, test the CTD pressure sensor response.")
    print("After hitting enter, use canned air to supply pressure to the sensor.")
    print("The value will be printed to the screen for 10 seconds. Hit enter to continue.")
    i = 0
    while i < 10:
        depth = thetis.get_ctd_depth()
        print("CTD Depth: {}".format(depth))
        qct_log.write("{},CTD Depth: {}".format(get_time(),depth))
        time.sleep(1)
        i = i + 1
    ctd_d = input("Did the CTD depth change when canned air was used? [Y/N]")
    time.sleep(30)
    thetis.power_sensors("OFF")
    print("Sensors should now be off.")
    qct_log.write("{}, Sensors off".format(get_time()))

    
    par_op = input("Did the PAR wiper open and close? [Y/N]")
    suna_op = input("Did the SUNA wiper cycle? [Y/N]") 
    trip_op = input("Did the Triplet wiper cycle? [Y/N]")
    bio_op= input("Did the bioshutter open and close? [Y/N/NA]")
    
   
    #PSW
    surface_state = thetis.get_surface_switch_status()
    input("Apply pressure to the surface pressure switch. Hit enter while supplying pressure.")
    submerged_state = thetis.get_surface_switch_status()
    
    #Winch
    thetis.power_winch("ON")
    qct_log.write("{},Profiler winch on".format(get_time()))

    
    
    thetis.logging("OFF")
    qct_log.write("{},Profiler logging off".format(get_time()))
    time.sleep(60)
    
    
    
    qct_log.close()


if thetis.connection() is True:
    thetis.power_sensors("ON")
    
    

