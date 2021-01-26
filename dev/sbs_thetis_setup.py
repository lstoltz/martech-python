#Rope Check


#CCFN
#CCM
#GPS,0
#GGF,0


from datetime import datetime,timezone
from martech.sbs.thetis import THETIS

port = 'COM3'
SS = '02' #Options: 01,02,06,07 
deployment = '20'

def main():
    opr8r = input('Operator: ')
    thetis = THETIS(port)
    if thetis.open_connection(115200) is True:
        version_info = thetis.get_version()
        dt_set = thetis.set_datetime()      
        profiler_id = "WLP-{}".format(version_info[0].rjust(3,"0"))
  
        buf_set = thetis.set_buf()
        pkd_set = thetis.set_parking_depth(depth)
        bd_set = thetis.set_breakaway_depth(0.70)
        whs_set = thetis.turn_off_wave_height_estimator()
        hld_set = thetis.set_hld(1) 
        num_set = thetis.set_profile_number(0)
        scs_set = thetis.set_scooch()
        blv_set = thetis.set_battery_thresholds(primary=28.5,secondary=28.5)
        gpsp_set = thetis.set_gps_power("OFF")
        ggf_set = thetis.set_gps_acquistion_after_profile("OFF")
        today = datetime.now(timezone.utc).strftime('%y%m%d')
        dir_name = 'QT{}'.format(today)        
        if thetis.change_to_root_directory('PC') is True: 
            pmkd = thetis.make_directory(dir_name,'PC')
            pcd = thetis.change_directory(dir_name,'PC')
            
        battery1 = thetis.get_battery_status(1)
        battery2 = thetis.get_battery_status(2)

        #Adjust winch settings.
        thetis.set_winch_power("ON")
        sta_set = thetis.set_sta(0.7)
        slsf_set = thetis.set_slsf(1.45)
        do_set = thetis.set_depth_offset(0.6)
        if thetis.change_to_root_directory(device='WC') is True:
            wmkd = thetis.make_directory(dir_name,'WC')
            wcd = thetis.change_directory(dir_name,'WC')
        thetis.set_winch_power("OFF")
        
        thetis.close_connection()
#-----------------------------------------------------------------------------#        
        
        dt = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        filename = '{}_QCT_{}.txt'.format(profiler_id,dt)
        with open(filename,'w') as file:
            file.write('{} Quality Conformance Test\n'.format(profiler_id))
            file.write('Operator: {}\n'.format(opr8r))
            file.write('Date Performed: {}\n'.format(dt))
            if pcd is not False and wcd is not False:
                file.write('Controller QCT Directory: {}\n'.format(pcd))
                file.write('Winch QCT Directory: {}\n'.format(wcd))
            if battery1 is not False:
                file.write('Battery 1 Voltage: {}\n'.format(battery1['voltage']))
                file.write('Battery 1 Min Cell: {}\n'.format(battery1['min_cell']))
                file.write('Battery 1 Max Cell: {}\n'.format(battery1['max_cell']))
                file.write('Battery 1 Leak Detect: {}\n'.format(battery1['leak_detect']))
            else:
                file.write('Battery 1: Not Found\n')
            if battery2 is not False:
                file.write('Battery 2 Voltage: {}\n'.format(battery2['voltage']))
                file.write('Battery 2 Min Cell: {}\n'.format(battery2['min_cell']))
                file.write('Battery 2 Max Cell: {}\n'.format(battery2['max_cell']))
                file.write('Battery 2 Leak Detect: {}\n'.format(battery2['leak_detect']))
            else:
                file.write('Battery 2: Not Found\n')
            if pkd_set is True:
                file.write('Parking Depth Set: {}\n'.format(thetis.pkd))
            else:
                file.write('Unable to set PKD.')
            if bd_set is True:
                file.write('Breakaway Depth Set: {}\n'.format(thetis.bd))
            else:
                file.write('Unable to set BD.')
            