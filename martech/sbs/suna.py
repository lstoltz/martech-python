import datetime
from martech.sercom import SERCOM
import re
import time
from xml.etree import ElementTree as ET
from xmodem import XMODEM

class SUNA():
    def __init__(self,port):
        self.rs232 = SERCOM()
        self.port = port
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.flowcontrol = 0
        self.timeout = 3          
    
    def open_connection(self,baudrate=57600):
        self.baudrate = baudrate        
        connected = self.rs232.connect(self.port,self.baudrate,
                                       self.bytesize,self.parity,self.stopbits,
                                       self.flowcontrol,self.timeout)
        self.rs232.clear_buffers()
        return connected      
    
    def close_connection(self):
        disconnected = self.rs232.disconnect()
        return disconnected        
    
    def stop_sampling(self):
        while True:
            self.rs232.write_command("$$$$$",EOL='\r')
            self.rs232.write_command("",EOL='\r')
            self.rs232.write_command("",EOL='\r')
            response = self.rs232.read_response()
            if "SUNA" in response:
                self.rs232.write_command("",EOL='\r')
                self.rs232.write_command("",EOL='\r')
                self.rs232.clear_buffers()
                return True
            else:
                continue
            
    def start_sampling(self):
        self.rs232.write_command('exit')
        time.sleep(1)
        
    def get_disk_free(self):
        self.rs232.write_command('get --diskfree')
        response = self.rs232.read_response()
        disk_free = int(re.findall(r"Ok (.*?)\r",response).pop())/1000000
        return disk_free 
    
    def get_disk_total(self):
        self.rs232.write_command('get --disktotal')
        response = self.rs232.read_response()
        disk_total = int(re.findall(r"Ok (.*?)\r",response).pop())/1000000
        return disk_total
    
    def get_clock(self):
        self.rs232.write_command('get clock')
        response = self.rs232.read_response()
        dt = str(re.findall(r"Ok (.*?)\r",response).pop())
        return dt    

    def set_clock(self):
        fmt = '%Y/%m/%d %H:%M:%S'
        now = datetime.datetime.now(datetime.timezone.utc).strftime(fmt)
        self.rs232.write_command('set clock {}'.format(now))
        response = self.rs232.read_response()
        if 'Ok' in response:
            return True
        else:
            return False
    
    def get_active_calfile_name(self):
        self.rs232.write_command('get activecalfile')
        response = self.rs232.read_response()
        filename = re.findall(r"Ok (.*?)\r",response).pop()
        return filename    

    def _getc(self,size,timeout=1):
        '''XMODEM output'''
        return self.rs232.read(size)

    def _putc(self,data,timeout=1):
        '''XMODEM input'''
        return self.rs232.write(data)
    
    def transfer_calfile(self,filename):
        filename = filename.upper() 
        self.rs232.write_command('send cal {}'.format(filename))
        self.rs232.read_bytes() #Read send command response to clear buffers.
        modem = XMODEM(self._getc,self._putc)
        stream = open(filename,'wb')
        modem.recv(stream)
        if os.path.getsize(filename) > 1000:
            print('Downloaded {}.'.format(filename)
            return True
        else:
            print('There was an issue downloading {}.'.format(filename)
            return False      

    def transfer_xml_zip(self):
        '''Downloads a zip file which contains a XML file that has everything 
        you need to know about the SUNA you are using.
        return -- True if the file contains some information.
                False if the file doesn't contain anything.
        '''
        sn = self.get_sn()
        if len(sn)) == 3:
            self.sn = str('0') + str(sn)
        self.write_command('send Pkg SNA{}.ZIP'.format(str(sn)))
        self.read_bytes() #Read send command response to clear buffers.
        print('XMODEM transfer of SNA{}.ZIP initiated.'.format(sn))
        modem = XMODEM(self._getc,self._putc)
        filename = 'SNA' + str(sn) + '.ZIP'
        stream = open(filename,'wb')
        modem.recv(stream)
        if os.path.getsize(filename) > 1:
            print('Downloaded {}.'.format(filename)
            return True
        else:
            print('There was an issue downloading {}.'.format(filename)
            return False  

        
    def extract_xml(self):
        '''Extract the xml file from the zip.
        return -- the filename of the extracted xml file.
        '''
        for root, dirs, files in os.walk('./'):
            for file in files:  #Search for a zip folder and extract it.
                if 'ZIP' in file:
                    print('Extracting {}.'.format(file)
                    zipfile.ZipFile(file,'r').extractall()
                    print('{} extracted.'.format(file)
                    break

        for root, dirs, files in os.walk('./'):
            for file in files:  #Search for an xml file.
                if '.xml' in file:
                    print('{} extracted from zip.'.format(file)
                    return file
        
        
    def transfer_syslog(self):
        '''Downloads the syslog file from the SUNA.'''
        self.write_command('send LOG SYSLOG.LOG')
        self.read_bytes() #Read send command response to clear buffers.
        print('XMODEM transfer of SYSLOG initiated.')
        modem = XMODEM(self._getc,self._putc)
        stream = open('SYSLOG.LOG','wb')
        modem.recv(stream)
        print('XMODEM transfer of SYSLOG complete.)
        if os.path.getsize('SYSLOG.LOG') > 1:
            print('Downloaded SYSLOG.LOG.')
            return True
        else:
            print('There was an issue downloading SYSLOG.LOG.')
            return False  

    def transfer_lamplog(self):
        '''Downloads the LAMPUSE file from the SUNA. WILL TAKE FOREVER.'''
        self.write_command('send LOG LAMPUSE.LOG')
        time.sleep(self.wait)
        self.read_bytes() #Read send command response to clear buffers.
        modem = XMODEM(self._getc,self._putc)
        stream = open('LAMPUSE.LOG','wb')
        modem.recv(stream) 
        if os.path.getsize(filename) > 1:
            print('Downloaded LAMPUSE.LOG.')
            return True
        else:
            print('There was an issue downloading LAMPUSE.LOG.')
            return False   
    
    def perform_selftest(self):
        self.rs232.write_command("selftest",EOL='\r\n')
        time.sleep(25)
        response = self.rs232.read_response()
        return response



    def get_sn(self):
        self.write_command('get serialno')
        response = self.read_response()
        sn = re.findall(r"Ok (.*?)\r",response)[0]
        print('Connected to SNA{}.'.format(sn)
        return sn


    def get_sensor_type(self):
        self.write_command('get senstype')
        response = self.read_response()
        sensor_type = str(re.findall(r"Ok (.*?)\r",response)[0])
        print('Sensor Type: {}'.format(sensor_type))
        return sensor_type


    def get_sensor_version(self):
        self.write_command('get sensvers')
        response = self.read_response()
        sensor_version = str(re.findall(r"Ok (.*?)\r",response)[0])
        print('Sensor Version: {}'.format(sensor_version))
        return sensor_version           


    def get_firmware_version(self):
        self.write_command('$Info FirmwareVersion')
        response = self.read_response()
        fw_version = str(re.findall(r"Ok (.*?)\r",response)[0])
        print('Firmware Version: {}'.format(fw_version))
        return fw_version


    def external_power_status(self):
        '''Checks if external power is connected.'''
        self.write_command('get --extpower')
        response = self.read_response()
        status = str(re.findall(r"Ok (.*?)\r",response)[0])
        if status == 'On':
            print('External power is on.')
            return True
        elif status == 'Off':
            print('External power is off. Please turn it on.')
            return False


    def get_lamp_usage(self):
        '''Returns how many hours the lamp has been run 
        and the approximate hours remaining.
        '''
        self.write_command('get lamptime')
        response = self.read_response()
        lamp_used = int(float(re.findall(r"Ok (.*?)\r",response)[0])/3600)
        return lamp_used
    
    
    def run_wiper(self):
        '''Runs the wiper. Takes ~15-20 seconds for the sensor to communicate 
        again.'''
        print('Running the wiper.')
        print('The SUNA will be back in a communcation state in 20 seconds.')
        self.write_command('special swipewiper')
        time.sleep(20)
        

    def list_calfiles(self):
        '''Returns a list of calibration files, dates, and filesizes on
        the SUNA as an array of arrays. 
        '''
        self.write_command('List Cal')
        response = self.read_response() 
        files = response.split('\n')
        calfiles = [file for file in files if '.CAL' in file]
        cal_files_info = []
        for cal in calfiles:
            split = cal.split('\t')
            size = int(split[1])
            caldate = str(split[2])
            filename = str(split[3])
            filename = filename.replace('\r','')
            file_info = [filename,caldate,size]
            cal_files_info.append(file_info)
        return cal_files_info

        
    def list_datafiles(self):
        '''Returns a list of data files, dates, and filesizes on the SUNA
        as an array of arrays.'''
        self.write_command('List Data')
        response = self.read_response()
        files = response.split('\n')
        dfiles = [file for file in files if '.CSV' in file or '.BIN' in file]
        data_files_info = []
        for d in dfiles:
            split = d.split('\t')
            size = int(split[1])
            creation_date = str(split[2])
            filename = str(split[3])
            filename = filename.replace('\r','')
            file_info = [filename,creation_date,size]
            data_files_info.append(file_info)
        return data_files_info
    
    
    def transfer_datafile(self,filename):
        '''Downloads a specified data file. May take several minutes
        to offload.'''
        filename = filename.upper()
        self.write_command('send DATA {}'.format(filename))
        self.read_bytes() #Read send command response to clear buffers.
        modem = XMODEM(self._getc,self._putc)
        stream = open(filename,'wb')
        modem.recv(stream)     
        
        
    def selftest(self):
        '''Runs the SUNA selftest.'''
        print('Running SUNA SelfTest.')
        print('This test can take up to 30 seconds.')
        self.write_command('selftest')
        time.sleep(30)
        response = self.read_response()
        st = response.replace('\r','')
        return st

    def get_config(self):
        '''Returns the configuration.'''
        self.write_command('get cfg')
        response = self.read_response()
        cfg = response.replace('\r','')
        return cfg

    def autosample(self,seconds=60):
        '''Tells the SUNA to autosample for X number of seconds
        (with a 20 second buffer for wiper operation). Numbers are converted
        to floats and strings are left as strings.'''       
        self.stop()
        self.start()
        time.sleep(20 + seconds)
        response = self.read_response()
        self.stop()
        lines = response.split('\n')
        data_lines = [line for line in lines if 'SAT' in line] #ID header.
        data = []
        for data_line in data_lines:
            drop = data_line.replace('\r','')
            delim = drop.split(',')
            data.append(delim)
        for sample in data: #Convert data to appropriate datatypes.
            for i in range(len(sample)):
                try:
                    sample[i] = float(sample[i])
                except:
                    sample[i] = str(sample[i])
        return data
 

    def reboot(self):
        '''Reboots the device firmware, simulating a power cycle.'''
        self.write_command('Reboot')    
        self.close_connection()
    

#----------------------------------------------------------------------------#
    def exit_passthru(self): 
        """This is a SBS Thetis Profiler specific command."""
        self.rs232.write_command('$PWETQ',EOL='')
        response = self.rs232.read_response()
        if "PWETA" in response:
            return True
        else:
            return False