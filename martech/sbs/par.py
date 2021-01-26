'''A module for driving the Sea-Bird Scientific ECO PAR.
'''
#TODO
#Implement catch for "unrecognized command".

import datetime
from martech.sercom import SERCOM 
import re
import time

class PAR():
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
        self.rs232.write_command('!!!!!',EOL='')
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
        
    def open_wiper(self):
        self.rs232.write_command('$mvs 1',EOL='\r')
        response = self.rs232.read_until_byte_string('\n')
        if 'mvs' in response:
            return True
        else:
            return False
    
    def close_wiper(self):
        self.rs232.write_command('$mvs 0',EOL='\r')
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
        if d == self.mmddyy and t == self.HHMMSS:
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
        pkt_pattern = "Pkt (.*?)\r"
        ave_pattern = "Ave (.*?)\r"
        asv_pattern = "Asv (.*?)\r"
        set_pattern = "Set (.*?)\r"
        rec_pattern = "Rec (.*?)\r"
        int_pattern = "Int (.*?)\r"
        self.d = re.findall(dat_pattern,info).pop()
        self.t = re.findall(clk_pattern,info).pop()
        self.memory = re.findall(mem_pattern,info).pop()
        self.version = re.findall(ver_pattern,info).pop()
        self.sn = re.findall(ser_pattern,info).pop()
        self.ave = re.findall(ave_pattern,info).pop()
        self.pkt = re.findall(pkt_pattern,info).pop()
        self.set = re.findall(set_pattern,info).pop()
        self.rec = re.findall(rec_pattern,info).pop()
        self.asv = re.findall(asv_pattern,info).pop()
        self.int = re.findall(int_pattern,info).pop()
        
    def get_serial_number(self):
        self._get_info()
        return self.sn

    def get_memory(self):
        self._get_info()
        return int(self.memory)

    def get_firmware_version(self):
        self._get_info()
        return self.version
   
    def get_sensor_datetime(self):
        self._get_info()
        d = datetime.datetime.strptime(self.d,'%m/%d/%y')
        t = datetime.datetime.strptime(self.t,'%H:%M:%S')
        d_iso = datetime.datetime.strftime(d,'%Y-%m-%d')
        t_iso = datetime.datetime.strftime(t,'%H:%M:%S')
        dt_iso = d_iso + 'T' + t_iso
        return dt_iso
             
    def print_settings_from_flash(self):
        self.rs232.write_command('$rls')
        info = self.rs232.read_response()
        print(info)

    def erase_memory(self):
        self.rs232.write_command('$emc')
        while True:
            response = self.rs232.read_response()
            if 'Mem' in response:
                break
        mem_pattern = "Mem (.*?)\r"
        mem_val = int(re.findall(mem_pattern,response).pop())
        if mem_val == 0:
            print('Memory erased!')
            return True
        else:
            print('Failure to erase memory!')
            return False
         
    def log_data(self,state="ON"):
        if state == "ON":
            val = 1
            self.rs232.write_command('$rec 1')
        elif state == "OFF":
            val = 0
            self.rs232.write_command('$rec 0')     
        response = self.rs232.read_response()
        status = re.findall(r"Rec (.*?)\r",response).pop()
        if int(status) == val == 1:
            print('Internal memory logging on.')
        elif int(status) == val == 0:
            print('Internal memory logging off.')

    def set_row_collection_between_times(self,value=0):       
        if value < 0 or value > 65535:
            print('Packet size out of bounds. Please set between 0-65535.')
            return None
        self.rs232.write_command('$Pkt {}'.format(value))
        response = self.rs232.read_response()
        packet = re.findall(r"Pkt (.*?)\r",response)[0]
        print('Pkt set to {}'.format(packet))
        self.store_settings()
        return packet

    def set_row_collection_between_low_power(self,value=0):
        if value < 0 or value > 65535:
            print('Row size out of bounds. Please set between 0-65535.')
            return None
        self.rs232.write_command('$Set {}'.format(value))
        response = self.rs232.read_response()
        set_val = re.findall(r"Set (.*?)\r",response)[0]
        print('Set set to {}'.format(set_val))
        self.store_settings()
        return set_val
  
    def collect_data(self,seconds=30):

        self.start_sampling()
        time.sleep(1 + seconds) #Add 1 second for wiper operation.
        response = self.rs232.read_response()
        self.stop_sampling()
        response = response.replace('\r','')
        lines = response.split('\n')
        lines = [line for line in lines if 'mvs' not in line] #Drop mvs lines.
        lines = list(filter(None,lines)) #Drop empty lines.
        data_array = []
        for line in lines:
            data = line.split('\t')
            data_array.append(data)
        self.rs232.clear_buffers()
        return data_array
    
    def get_data(self):
        self.rs232.write_command('$get')
        response = self.rs232.read_response()
        if 'etx' in response:
            print(response)
        return response