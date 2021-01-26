''' A module for communicated with the SBS Thetis Profiler and its peripherals
over RS232.

Author(s): Ian Black

2020-12-25: Initial commit.
2021-01-24: Updated to use sercom module.
'''

import datetime
from martech.sercom import SERCOM
import os
import re
import time 

class THETIS():
    def __init__(self,port):
        self.rs232 = SERCOM()
        self.port = port
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.flowcontrol = 0
        self.timeout = 3  
        
        #Flags for determining if things are on or off.
        #By default, the CTD, winch, and instruments should be OFF on startup.
        #If they aren't, you should send the control can back to SBS.
        self.ctd_flag = 0
        self.winch_flag = 0
        self.insp_flag = 0
        self.pump_flag = 0
        
        #If file sizes are below these values, then there is no data in them.
        self.SNA_header_len = 75
        self.SND_header_len = 10
        self.ACS_header_len = 75
        self.ACD_header_len = 10
        self.PPB_header_len = 75
        self.PPD_header_len = 10
        self.DBG_header_len = 75
        
    def open_connection(self,baudrate=115200):
        self.baudrate = baudrate        
        connected = self.rs232.connect(self.port,self.baudrate,
                                       self.bytesize,self.parity,self.stopbits,
                                       self.flowcontrol,self.timeout)
        return connected      
    
    def close_connection(self):
        disconnected = self.rs232.disconnect()
        return disconnected    

    def set_datetime(self,tzo=0):
        now = datetime.datetime.now(datetime.timezone.utc)
        now = now.replace(microsecond=0)
        now_str = datetime.datetime.strftime(now,'%Y%m%d%H%M%S')
        d = datetime.datetime.strftime(now,'%m/%d/%Y') 
        t = datetime.datetime.strftime(now,'%H:%M:%S')
        tzo = int(tzo)
        self.rs232.write_command('$PWETC,PC,,,,DATE,3,{},{},{}*'.format(d,t,tzo))
        response = self.rs232.read_response()
        dpattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?),.*?,.*?\*'
        d = re.findall(dpattern,response).pop()
        tpattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,.*?,(.*?),.*?\*'
        t = re.findall(tpattern,response).pop()
        dt_pro = d + 'T' + t
        dt_pro = datetime.datetime.strptime(dt_pro,'%m/%d/%YT%H:%M:%S')
        dt_pro_str = datetime.datetime.strftime(dt_pro,'%Y%m%d%H%M%S')
        if dt_pro_str == now_str:
            return True
        else:
            return False

    def get_version(self):
        info = {}
        self.rs232.write_command('$PWETC,PC,,,,VER*0F',EOL='\n')
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,(.*?)\*'
        data = re.findall(pattern,response).pop()
        data = data.split(',')
        info['profiler_id'] = data[0]
        info['cf_sn'] = data[3]
        info['pico'] = data[4]
        info['bios'] = data[5]
        info['firmware'] = data[6]
        info['firmware_date'] = data[7]
        return info

    def change_to_root_directory(self,listener='PC'):
        while True:
            self.rs232.write_command('$PWETC,{},,,,CD,1,..*'.format(listener))
            response = self.rs232.read_response()            
            if 'CD,1,*' in response:
                return True
            else:
                time.sleep(1)
                continue

    def make_directory(self,directory_id,listener='PC'):
        if len(str(directory_id)) > 8:
            print('Subdirectories must be 8 alphanumeric characters or less.')
            return False
        self.rs232.write_command('$PWETC,{},,,,MKD,1,.\{}*'.format(listener,directory_id))
        response = self.rs232.read_response()
        if 'MKD*' in response:
            msg='New directory located at {}/{}.'.format(listener,directory_id)
            print(msg)
        elif 'NAK,2,MKD' in response:
            msg = 'Directory already exists!'
            print(msg)
            return 
        else:
            return False

    def change_directory(self,directory_id,listener='PC'):
        self.rs232.write_command('$PWETC,{},,,,CD,1,.\{}*'.format(listener,directory_id))
        time.sleep(0.5)
        response = self.rs232.read_response()
        if 'CD,1,\{}*'.format(directory_id) in response or 'CD,1,*' in response:
            msg = 'Moving to {}/{}.'.format(listener,directory_id)
            print(msg)        
            return directory_id
        elif 'NAK,2,CD,C' in response:
            print('No subdirectory found.')
            return False
        else:
            return False    

    def set_winch_power(self,state):
        if state == 'ON':
            self.rs232.write_command('$PWETC,PC,,,,WP,1,1*',EOL = '\n')
        elif state == 'OFF':
            self.rs232.write_command('$PWETC,PC,,,,WP,1,0,*',EOL = '\n')
        response = self.rs232.read_response()
        if "ON" in response:
            print('Winch is now on!')
            time.sleep(5)
        elif "OFF" in response:
            print('Winch is now off!')    

    def set_breakaway_depth(self,value=0.70):
        value = float(value)
        self.bd = value
        self.rs232.write_command('$PWETC,PC,,,,BD,1,{}*'.format(value))       
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        returned_val = float(re.findall(pattern,response).pop())
        if returned_val == value:
            return True
        else:
            return False        
        
    def turn_off_wave_height_estimator(self):
        self.whs = 'OFF'
        self.rs232.write_command('$PWETC,PC,,,,WHS,1,0*03')
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?),.*?,.*?,.*?\*'
        state = int(re.findall(pattern,response).pop())
        if state == 0:
            return True
        else: 
            return False

    def set_hld(self,mode=1):
        self.hld = mode
        if int(mode) == 1:
            self.rs232.write_command('$PWETC,PC,,,,HLD,1,1*0E')
        elif int(mode) == 0:
            self.rs232.write_command('$PWETC,PC,,,,HLD,1,0*0F')
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        val = int(re.findall(pattern,response).pop())
        if val == mode:
            return True
        else:
            return False       
    
    def set_parking_depth(self,value):
        value = float(value)
        self.pkd = value
        self.rs232.write_command('$PWETC,PC,,,,PKD,1,{}*'.format(value))
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        returned_val = float(re.findall(pattern,response).pop())
        if returned_val == value:
            return True
        else:
            return False    
    
    def set_sta(self,value=0.7):
        self.sta = 0.7
        self.rs232.write_command('$PWETC,WC,,,,STA,1,{}*'.format(value))
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        if 'WC OFF' in response:
            self.set_winch_power("ON")
            self.rs232.write_command('$PWETC,WC,,,,STA,1,{}*'.format(value))
            response = self.rs232.read_response()
            amps = float(re.findall(pattern,response).pop())
            self.set_winch_power("OFF")
        else:
            amps = float(re.findall(pattern,response).pop())
        if amps < value - 0.01:
            return False
        elif amps == value or amps + 0.01 == value:
            return True    

    def set_profile_number(self,value=0):
        value = int(value)
        self.num = value
        self.rs232.write_command('$PWETC,PC,,,,num,1,{}*'.format(int(value)))
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        returned_val = int(re.findall(pattern,response).pop())
        if returned_val == value:
            return True
        else:
            return False        

    def set_scooch(self,interval=250,max_delta=5000,travel=150000,
                            min_delta=2500):
        self.scs = '{},{},{},{}'.format(interval,max_delta,travel,min_delta)
        self.rs232.write_command('$PWETC,PC,,,,SCS,4,{},{},{},{}*'.format(interval,
                           max_delta,travel,min_delta))
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        settings = re.findall(pattern,response).pop()
        pro_set = settings.split(',')
        pro_set = list(map(float,pro_set))
        user_set = [interval,max_delta,travel,min_delta]
        user_set = list(map(float,user_set))        
        if pro_set == user_set:
            return True
        else:
            return False
        
    def set_slsf(self,value=1.45):
        value = float(value)
        self.slsf = value
        self.rs232.write_command('$PWETC,WC,,,,SLSF,1,1.45*')
        response = self.rs232.read_response()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        if 'WC OFF' in response:
            self.set_winch_power("ON")
            self.rs232.write_command('$PWETC,WC,,,,SLSF,1,1.45*')
            response = self.rs232.read_response()
            returned_val = float(re.findall(pattern,response).pop())
            self.set_winch_power("OFF")
        else:
            returned_val = float(re.findall(pattern,response).pop())
        if returned_val == value:
            return True
        else:
            return False   
        
    def set_battery_thresholds(self,primary=28.5,secondary=28.5):
        primary = float(primary)
        secondary = float(secondary)
        self.bt1 = primary
        self.bt2 = secondary
        self.rs232.write_command('$PWETC,PC,,,,BLV,2,{},{}*'.format(primary,secondary))
        response = self.rs232.read_response()
        if str(primary) in response and str(secondary) in response:
            return True
        else:
            return False
        
    def set_depth_offset(self,value=0.6):
        value = float(value)
        self.do = value
        self.rs232.write_command('$PWETC,WC,,,,DO,1,{}*'.format(value))
        response = self.rs232.read_response()
        if 'DO,1,{}'.format(value) in response:
            return True
        else:
            return False
        
    def set_gps_acquistion_after_profile(self,state="OFF"):
        self.ggf = state
        if state == "OFF":
            self.rs232.write_command('$PWETC,PC,,,,GGF,1,0*')
        elif state == "ON":
            self.rs232.write_command('$PWETC,PC,,,,GGF,1,1*')
        response = self.rs232.read_response()
        if 'GGF,1,0' in response and state == "OFF":
            return True
        elif 'GGF,1,1' in response and state == "ON":
            return True
        else:
            return False
        if 'OFF' in response:
            return True
        else: 
            return False
    
    def set_gps_power(self,state="OFF"):
        self.gpsp = state
        if state == "OFF":
            self.rs232.write_command('$PWETC,PC,,,,GPSP,1,0*')
        elif state == "ON":
            self.rs232.write_command('$PWETC,PC,,,,GPSP,1,1*')
        response = self.rs232.read_response()
        if 'GPSP,1,1' in response and state == "ON":
            return True
        elif 'GPSP,1,0' in response and state == "OFF":
            return True
        else:
            return False
    
    
    def get_battery_status(self,address): 
        status = {}
        self.rs232.write_command('$PWETC,PC,,,,BFS,1,{}*'.format(int(address)))
        time.sleep(2)
        response = self.rs232.read_response()
        if "LOCKED" in response:
            print('Battery at this address does not exist.')
            return False     
        pweta_pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        info = re.findall(pweta_pattern,response).pop()
        info = [i for i in info.split(' ') if i]        
        status['position'] = info[0][1:3]
        if 'f' in info[1]:
            status['state'] = 'OFF'
        elif 'd' in info[1]:
            status['state'] = 'DISCHARGING'
        elif 'c' in info[1]:
            status['state'] = 'CHARGING'
        elif 'b' in info[1]:
            status['state'] = 'BALANCING'   
        status['voltage'] = float(info[2])
        status['current'] = float(info[3])
        status['temperature'] = float(info[4])
        status['min_cell'] = float(info[5])
        status['max_cell'] = float(info[6])
        if info[7] == '0':
            status['leak_detect'] = 'NO_LEAK'
        elif info[7] == '1':
            status['leak_detect'] = 'WATER_DETECTED'
        return status
            
    
    def set_radio_depth(self,value=1.0):
        value = float(value)
        self.rd = value
        self.rs232.write_command('$PWETC,PC,,,,RD,1,{}*'.format(value))
        response = self.rs232.read_response()
        if 'RD,1,{}'.format(value) in response:
            return True
        else:
            return False
            
        
    def host2pico(self,via='Q'):
        if via == 'Q':
            self.rs232.write_command('$PWETC,PC,,,,Q*')
        elif via == 'E':
            self.rs232.write_command('$PWETC,PC,,,,EXIT')
        time.sleep(3)    
        self.rs232.write_command('\r',EOL='')
        
    
    def get_pkg_settings(self):
        self.rs232.clear_buffers()
        time.sleep(1)
        self.rs232.write_command('SET',EOL='\r')
        response = self.rs232.read_response()
        if 'SET' in response:    
            self.rs232.write_command('\r',EOL='')
            return response
    
    def get_acsb(self):
        self.rs232.write_command('SET PKG.ACSB',EOL='\r')
        time.sleep(1)
        response = self.rs232.read_response()
        if 'PKG.ACSB' in response:
            pattern = 'ACSB=(.*?)\r\n'
            num_wavelengths = int(re.findall(pattern,response).pop())
            self.rs232.write_command('\r',EOL='')
            return num_wavelengths
        
    def set_acsb(self,output_wavelengths):
        self.rs232.clear_buffers()
        self.rs232.write_command('SET PKG.ACSB={}'.format(int(output_wavelengths)),EOL='\r')
        time.sleep(1)
        response = self.rs232.read_response()
        print(response)
        if str(output_wavelengths) in response:
            return True
        else:
            return False
        
    def pico2host(self):
        self.rs232.write_command('\r',EOL='')
        self.rs232.clear_buffers()
        self.rs232.write_command('APP',EOL='\r')
        time.sleep(3)
        self.rs232.clear_buffers()
        
    def set_buf(self,value=512):
        value = int(value)
        self.rs232.write_command('$PWETC,PC,,,,BUF,1,{}*'.format(value))
        response = self.rs232.read_response()
        if 'BUF,1,{}'.format(value) in response:
            return True
        else:
            return False

    def get_memory(self,listener='PC'):
        self.rs232.write_command('$PWETC,{},,,,FREE*'.format(listener))        
        response = self.rs232.read_response()
        fpattern = 'FREE,1,(.*?)\*'
        free = (int(re.findall(fpattern,response).pop()))/1000
        time.sleep(1)
        self.rs232.write_command('$PWETC,{},,,,TOTAL*'.format(listener))
        response = self.rs232.read_response()
        tpattern =  'TOTAL,1,(.*?)\*'
        total = (int(re.findall(tpattern,response).pop()))/1000          
        used = total - free       
        return total,used,free
    
    def send_break(self):
        self.rs232.write_command('$PWETC,PC,,,,BREAK*')
        time.sleep(0.05) #Wait for 50 milliseconds.
        self.rs232.clear_buffers()   
    
    def turn_off_power_to_acoustic_modem(self):
        self.rs232.write_command('$PWETC,PC,,,,ATMP,1,0*')  
        response = self.rs232.read_response()
        if "OFF" in response:
            return True
        else:
            return False

    def logging(self,state,listener='PC'):
        if state == "ON":
            self.rs232.write_command('$PWETC,{},,,,LOG,1,1*'.format(listener))
        elif state == "OFF":
            self.rs232.write_command('$PWETC,{},,,,LOG,1,0*'.format(listener))
        time.sleep(1)
        response = self.rs232.read_response()
        if 'LOG,1,1' in response and state == "ON":
            return True
        elif 'LOG,1,0' in response and state == "OFF":
            return True
        else:
            return False

    def set_ctd_power(self,state):
        if state == "ON":
            self.rs232.write_command('$PWETC,PC,,,,CTDP,1,1*')
            self.ctd_flag = 1
        elif state == "OFF":
            self.rs232.write_command('$PWETC,PC,,,,CTDP,1,0*')     
            self.ctd_flag = 0
        response = self.rs232.read_response()
        if 'ON' in response and state == "ON":
            return True
        if 'OFF' in response and state == "OFF":
            return True
        else:
            return False
    
    def set_insts_power(self,state):
        if state == "ON":
            self.rs232.write_command('$PWETC,PC,,,,INSP,1,1*')
            self.insp_flag = 1
        elif state == "OFF":
            self.rs232.write_command('$PWETC,PC,,,,INSP,1,0*')       
            self.insp_flag = 0
        response = self.rs232.read_response()
        if 'ON' in response and state == "ON":
            return True
        if 'OFF' in response and state == "OFF":
            return True
        else:
            return False
    
    def set_sensors_power(self,state):
        if state == "ON":
            ctd_bool = self.set_ctd_power("ON")
            time.sleep(1)
            insp_bool = self.set_insts_power("ON")
        elif state == "OFF":
            while True:
                ctd_bool = self.set_ctd_power("OFF")
                time.sleep(1)
                insp_bool = self.set_insts_power("OFF")
                time.sleep(1)
                if ctd_bool is True and insp_bool is True:
                    break
                else:
                    time.sleep(1)
                    continue
        if ctd_bool is True and insp_bool is True:
            time.sleep(3)
            return True
        else:
            return False
        
    def set_pump_power(self,state):
        if state == 'ON':
            self.rs232.write_command('$PWETC,PC,,,,PWR,2,PMP,1*')
            response = self.rs232.read_response()
            if "ON" in response and state == "ON":
                self.pump_flag = 1
                return True
        elif state == 'OFF':
            while True:
                self.rs232.write_command('$PWETC,PC,,,,PWR,2,PMP,0*')
                response = self.rs232.read_response()
                if "OFF" in response and state == "OFF":
                    self.pump_flag = 0
                    return True
                else:
                    time.sleep(1)
                    continue
        else:
            return False
            
        
    def get_ctd_depth(self):
        if self.ctd_flag == 0:
            self.set_ctd_power("ON")
            self.rs232.write_command('$PWETC,PC,,,,D*')
            response = self.rs232.read_response()
            pattern = 'D,1,(.*?)\*'
            depth = float(re.findall(pattern,response).pop())
            time.sleep(0.25)
            self.set_ctd_power("OFF")
        elif self.ctd_flag == 1:
            self.rs232.write_command('$PWETC,PC,,,,D*')
            response = self.rs232.read_response()
            pattern = 'D,1,(.*?)\*'
            depth = float(re.findall(pattern,response).pop())         
        return depth
    
    def get_psw_state(self):
        self.rs232.write_command('$PWETC,PC,,,,PSW*')
        response = self.rs232.read_response()
        if 'SUBMERGED' in response:
            state = 'SUBMERGED'
        elif 'SURFACE' in response:
            state = 'SURFACE'
        else:
            state = 'UNKNOWN'
        return state         
    
    def passthru(self,port):
        self.rs232.write_command('$PWETC,PC,,,,pas,1,{}*'.format(port))
        time.sleep(1)
    
    def get_working_directory(self,listener):
        self.rs232.write_command('$PWETC,{},,,,PWD*'.format(listener))
        response = self.rs232.read_response()
        pattern = 'PWD,1,(.*?)\*'   
        directory = re.findall(pattern,response).pop()
        if directory == '':
            directory = listener + '/root'
        return directory

    def list_subdirectories(self,listener='PC'):
        self.rs232.write_command('$PWETC,{},,,,DIR*'.format(listener))
        response = self.rs232.read_response()
        pattern = 'DIR,1,\\\\(.*?)\*'
        subs = re.findall(pattern,response)
        keeps = []
        for sub in subs:
            if '\.' not in sub:
                keeps.append(sub)
        if len(keeps) == 1:
            keeps = keeps.pop()
        elif len(keeps) == 0:
            return None
        return keeps
    
    def list_files(self,listener):
        self.rs232.write_command('$PWETC,{},,,,DIR,1,#.#*'.format(listener))
        time.sleep(3)
        response = self.rs232.read_response()
        pattern = 'DIR,2,.*?\\\\([0-9]*\.[A-Z]*),(.*?)\*' #Search for PDDDFFFF.ext and file sizes.
        files = re.findall(pattern,response)
        if len(files) == 0:
            return None
        return files

    def delete_file(self,filename,listener):
        if not isinstance(filename,list):
            filename = [filename]
        for f in filename:
            self.rs232.write_command('$PWETC,{},,,,DEL,1,{}*'.format(listener,f))
            time.sleep(1)
    
    def remove_directory(self,directory_id,listener):
        self.rs232.write_command('$PWETC,{},,,,RMD,1,.\{}*'.format(listener,directory_id))
        response = self.rs232.read_response()
        if 'RMD*' in response:
            return True
        elif 'NAK' in response:
            return False
        else:
            return False

    def set_winch_brake(self,state):
        if state == 'OFF':
            self.rs232.write_command('$PWETC,WC,,,,B,1,0*0A')
        elif state == 'ON':
            self.rs232.write_command('$PWETC,WC,,,,B,1,1*0B')       
        time.sleep(0.25)
        response = self.rs232.read_response()
        if 'B,1,1' in response and state == "ON":
            return True
        elif 'B,1,0' in response and state == "OFF":
            return True
        else:
            return False  

    def _send_ack(self,listener='PC'):
        self.rs232.write_command('$PWETA,{},,,,ACK*'.format(listener))  

    def offload_files(self,filenames,directory,handshake=0.1):
        if not isinstance(filenames,list):
            filenames = [filenames]     
        for filename in filenames:
            print('\nStarting offload of {}.'.format(filename))
            if '.PPD' in filename:
                full = filename.replace(filename[-1],'B')
                handshake = 0.25
                self.rs232.write_command('$PWETC,PC,,,,GDF,1,{}*'.format(full))
            elif '.SND' in filename:
                full = filename.replace(filename[-1],'A')
                handshake = 0.25
                self.rs232.write_command('$PWETC,PC,,,,GDF,1,{}*'.format(full))                
            elif '.ACD' in filename:
                full = filename.replace(filename[-1],'S')
                handshake = 0.25
                self.rs232.write_command('$PWETC,PC,,,,GDF,1,{}*'.format(full))  
            else:
                full = filename
                self.rs232.write_command('$PWETC,PC,,,,GET,1,{}*'.format(full))
            time.sleep(0.5)
            raw = []
            pattern = rb".*\$PWETB,.*?,.*?,.*?,.*?,.*?,.*?,(.*)"
            while True:
                print('.',end='')
                incoming = self.rs232.sercom.in_waiting
                time.sleep(handshake)
                if incoming == 0:
                    print('\n')
                    break
                else:
                    received = self.rs232.sercom.read(incoming)
                try:
                    msg = received.decode()
                    if "DONE" in msg or "ACK" in msg:
                        print('\n')
                        break
                    else:
                        drop_lead = re.findall(pattern,received,re.DOTALL)[0]
                        drop_checksum = drop_lead[:-5]
                        raw.append(drop_checksum)
                        self._send_ack()
                        time.sleep(handshake)
                except:
                    drop_lead = re.findall(pattern,received,re.DOTALL)[0]
                    drop_checksum = drop_lead[:-5]
                    raw.append(drop_checksum)      
                    self._send_ack()
                    time.sleep(handshake)
            filepath = os.path.join(directory,filename)        
            with open(filepath,'wb') as f:
                for item in raw:
                    f.write(item)
            print('Offloaded: {}'.format(filename))
            time.sleep(1)
            self.rs232.clear_buffers()
            time.sleep(1)

       
#Still need to test.        
#----------------------------------------------------------------------------#

         
    def transfer_winch_file(self,filename):
        if not isinstance(filename,list):
            filename = [filename]
        if self.winch_flag != 1:
            self.set_winch_power("ON")
            for wf in filename:
                self.rs232.write_command('$PWETC,WC,,,,GWF,1{}*'.format(wf))
                time.sleep(1)
                response = self.rs232.read_until_byte_string('\n')
                if "DONE" in response:
                    self.set_winch_power("OFF")
                    time.sleep(1)
                    return True
                else:
                    return False
        else:
            for wf in filename:
                self.rs232.write_command('$PWETC,WC,,,,GWF,1{}*'.format(wf))
                time.sleep(1)
                response = self.rs232.read_until_byte_string('\n')
                if "DONE" in response:
                    time.sleep(1)
                    return True
                else:
                    return False           
