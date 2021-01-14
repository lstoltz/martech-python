#TODO
#$met
#$ave
#$pkt
#$rls
#$rfd
#Implement catch for "unrecognized command".

import datetime
from martech.sercom import SERCOM 
import re
import time

class TRIPLETW():
    def __init__(self,port):
        self.rs232 = SERCOM()
        self.port = port
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.flowcontrol = 0
        self.timeout = 3  
        
    def open_connection(self,baudrate=19200):
        self.baudrate = baudrate        
        connected = self.rs232.connect(self.port,self.baudrate,
                                       self.bytesize,self.parity,self.stopbits,
                                       self.flowcontrol,self.timeout)
        return connected    
    
    def close_connection(self):
        disconnected = self.rs232.disconnect()
        return disconnected

    def stop_sampling(self):
        self.rs232.write_command('!!!!',EOL='')
        response = self.rs232.read_until_byte_string('Mem'.encode())
        if 'Ver' in response:
            time.sleep(1)
            self.rs232.clear_buffers()
            print('Sensor has stopped auto-sampling.')
            return True
        else:
            return False
        
    def start_sampling(self):
        self.rs232.write_command('$run',EOL='\r')
        
    
    def wiper(self):
        self.rs232.write_command('$mvs',EOL='\r')
        response = self.rs232.read_until_byte_string('\n')
        if 'mvs' in response:
            return True
        else:
            return False
    
    def set_time(self):
        HHMMSS=datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')
        self.rs232.write_command('$clk {}'.format(HHMMSS),EOL='\r')
        time.sleep(0.25)
        self.HHMMSS = datetime.datetime.strptime(HHMMSS,'%H%M%S')

    def set_date(self):
        mmddyy=datetime.datetime.now(datetime.timezone.utc).strftime('%m%d%y')
        self.rs232.write_command('$date {}'.format(mmddyy),EOL='\r')
        time.sleep(0.25)
        self.mmddyy = datetime.datetime.strptime(mmddyy,'%m%d%y')
        
    def set_datetime(self):
        self.set_date()
        self.rs232.clear_buffers()
        self.set_time()
        response = self.rs232.read_response()
        dat_pattern = r"Dat (.*?)\r"
        clk_pattern = r"Clk (.*?)\r" 
        d = re.findall(dat_pattern,response).pop()
        d = datetime.datetime.strptime(d,'%m/%d/%y')
        t = re.findall(clk_pattern,response).pop()
        t = datetime.datetime.strptime(t,'%H:%M:%S')
        if d == self.mmddyy & t == self.HHMMSS:
            print('Date and time set to system time in UTC.')
            return True
        else:
            print('Date and time not set correctly.')
            return False

    def store_settings(self):
        self.rs232.write_command('$sto')
        response = self.rs232.read_response()
        if "done" in response:
            print('Settings now stored.')
            return True
        else:
            return False
        
    def _get_info(self):
        self.rs232.write_command('$mnu')     
        time.sleep(0.2)
        info = self.rs232.read_response()
        dat_pattern = "Dat (.*?)\r"
        clk_pattern = "Clk (.*?)\r"
        mem_pattern = "Mem (.*?)\r"
        ser_pattern = "Ser (.*?)\r"
        ver_pattern = "Ver (.*?)\r"
        m1d_pattern = "M1d (.*?)\r"
        m2d_pattern = "M2d (.*?)\r"
        m3d_pattern = "M3d (.*?)\r"
        m1s_pattern = "M1s (.*?)\r"
        m2s_pattern = "M2s (.*?)\r"
        m3s_pattern = "M3s (.*?)\r"        
        self.d = re.findall(dat_pattern,info).pop()
        self.t = re.findall(clk_pattern,info).pop()
        self.memory = re.findall(mem_pattern,info).pop()
        self.version = re.findall(ver_pattern,info).pop()
        self.sn = re.findall(ser_pattern,info).pop()
        self.m1d = re.findall(m1d_pattern,info).pop()
        self.m2d = re.findall(m2d_pattern,info).pop()
        self.m3d = re.findall(m3d_pattern,info).pop()
        self.m1s = re.findall(m1s_pattern,info).pop()
        self.m2s = re.findall(m2s_pattern,info).pop()
        self.m3s = re.findall(m3s_pattern,info).pop()
        
    
    def get_serial_number(self):
        self._get_info()
        return self.sn

    def get_memory(self):
        self._get_info()
        return self.memory

    def get_firmware_version(self):
        self._get_info()
        return self.version
    
#    def get_output_format(self):
#        self.rs232.write_command('$met')
#        time.sleep(2)
#        response = self.rs232.read_response()
#        delim_pattern = "0,Delimiter(.*?)1,"
#        date_pattern = "1,DATE,(.*?)2,"
#        time_pattern = "2,TIME,(.*?)3,"
#        ref1_pattern = "(Ref_1.*?)5,"
#        ref2_pattern = "(Ref_2.*?)7,"
#        ref3_pattern = "(Ref_3.*?)9,"
#        
#        
#        
#        
#        
#        response = self.read_response()
#        fmt = response.replace('\r','')
#        return fmt        
    
    
#    
#    def get_sensor_datetime(self):
#        self._get_info()
#        d = self.d
#        t = self.t
#        
#        
#    def get_calibration_coefficients(self):
#        self._get_info()
        


    def erase_memory(self):
        self.rs232.write_command('$emc')
        time.sleep(0.1)
        response = self.read_response()
        if 'retype' in response:
            self.rs232.clear_buffers()
            self.rs232.write_command('$emc')
            response = self.read_until_character('Mem')
            if 'Ver' in response:
                print('Memory erased!')
                return True
            else:
                print('Failure to erase memory.')
                return False



#    def log_data(self,state="ON"):
#        if state == "ON":
#            val = 1
#            self.write_command('$rec 1')
#        elif state == "OFF":
#            val = 0
#            self.write_command('$rec 0')     
#        time.sleep(self.wait)
#        response = self.read_response()
#        response = re.findall(r"Rec (.*?)\r",response)[0]
#        return state
#
#    
#
#
#    def set_packet_size(self,value=0):       
#        if value < 0 or value > 65535:
#            print('Packet size out of bounds. Please set between 0-65535.')
#            return None
#        self.write_command('$Pkt {}'.format(value))
#        time.sleep(self.wait)
#        response = self.read_response()
#        packet = re.findall(r"Pkt (.*?)\r",response)[0]
#        self.store_settings()
#        print('Pkt set to {}'.format(packet))
#        return packet
#
#
#    def set_rows(self,value=0):
#        if value < 0 or value > 65535:
#            print('Row size out of bounds. Please set between 0-65535.')
#            return None
#        self.write_command('$Set {}'.format(value))
#        time.sleep(self.wait)
#        response = self.read_response()
#        set_val = re.findall(r"Set (.*?)\r",response)[0]
#        self.store_settings()
#        print('Set set to {}'.format(set_val))
#        return set_val
# 
#
#            
#    def get_output_format(self):
#        self.write_command('$met')
#        time.sleep(self.wait)
#        response = self.read_response()
#        fmt = response.replace('\r','')
#        return fmt    
#    
#    
#    def get_calibration_coefficients(self):
#        '''Get sensor cal coeffs that should be shown on vendor documentation.
#        return -- The dark counts and scale factors for each channel on the sensor.
#        You will need to determine the connection to a specific wavelength by looking
#        at the output data and the metadata.
#        '''
#        self.write_command('$mnu')
#        time.sleep(self.wait)
#        response = self.read_response()        
#        m1d = re.findall(r"M1d (.*?)\r",response)[0]
#        m2d = re.findall(r"M2d (.*?)\r",response)[0]
#        m3d = re.findall(r"M3d (.*?)\r",response)[0]
#        m1sf = re.findall(r"M1s (.*?)\r",response)[0]
#        m2sf = re.findall(r"M2s (.*?)\r",response)[0]
#        m3sf = re.findall(r"M3s (.*?)\r",response)[0]
#        WL1 = ['WL1',m1d,m1sf]
#        WL2 = ['WL2',m2d,m2sf]
#        WL3 = ['WL3',m3d,m3sf]
#        return WL1,WL2,WL3
#
#    
#    def collect_data(self,seconds=30):
#        '''Collects data for X number of seconds.
#        seconds -- number of seconds to collect data
#        return -- an array of arrays of strings. Each array within the main array
#            is a line of data output.
#        '''
#        self.start()
#        time.sleep(self.wait + 3 + seconds) #Add 2 seconds for wiper operation.
#        response = self.read_response()
#        self.stop()
#        response = response.replace('\r','')
#        lines = response.split('\n')
#        lines = [line for line in lines if 'mvs' not in line] #Drop mvs lines.
#        lines = list(filter(None,lines)) #Drop empty lines.
#        data_array = []
#        for line in lines:
#            data = line.split('\t')
#            data_array.append(data)
#        return data_array
#
