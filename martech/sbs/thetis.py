"""A class for communicating with the Sea-Bird Scientific Thetis profiler 
controller and winch.

Tested in Spyder 3.3.3 under Python 3.7.4.

Author: Ian Black (iantimothyblack@gmail.com)
2020-10-19: Initial commit.
2020-10-20: Added functionality for offloading winch files. 
            Cleaned up and alphabetized functions.
2020-10-23: Updated descriptions.

Functions to improve...
- change_winch_directory (need to test "cd,.." and add t/f return)
- change_winch_directory
- any function that deals with file offload.
- picodos functions

Commands to add in the future...
- GPS
- GGF
- CCM
- CCFN (move to spool position using encoder counts)
- PAS (Passthrough to individual instruments, need to rebuild classes for
       those sensors.)
"""
import datetime
import re
import serial 
import time 

class Thetis():
    def __init__(self):
        '''Instantiate a blank serial object. 
        Conceivably this should allow for communication with several profilers
        at once using multiple cables/ports. Who would do that? A crazy person.
        '''
        self.rs232 = serial.Serial()
           
        
    def change_directory(self,directory_id):
        '''Change the directory to a known directory structure.
        To move up one directory, a user can supply '..' as the directory_id.
        directory_id -- a known overarching or sub directory.
        return -- true/false if the response contains the directory_id
        '''
        self.write_command('$PWETC,PC,,,,CD,1,.\{}*'.format(directory_id))
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'            
        directory = re.findall(pattern,data)[0]
        if directory_id in directory:
            return True
        elif directory == '' and directory_id == '..':
            return True
        else:
            return False    


    def change_winch_directory(self,directory_id):
        '''Move to a new winch directory.
        directory_id -- a known overarching or sub directory
        '''
        self.write_command('$PWETC,WC,,,,CD,1,\{}*'.format(directory_id))
         
        
    def clear_buffers(self):
        """Clear the input and output buffers.
        Note: Intended to be used if there are extra characters in the buffers.
        """
        self.rs232.reset_input_buffer()
        self.rs232.reset_output_buffer()    
        
    def close_connection(self):
        """Close the active port to the profiler.
        return -- true if the connection was closed successfully, false if not.
        """
        try:
            self.rs232.close()
            return True
        except:
            return False    
    
           
    def data_logging(self,state):
        '''Turn on/off the file logging capability of the controller. 
            Turning this on will create data files on the controller, but
            not the winch.
        state -- ON/OFF 
        '''
        if state == 'ON':
            self.write_command('$PWETC,PC,,,,LOG,1,1*0A')
        elif state == 'OFF':
            self.write_command('$PWETC,PC,,,,LOG,1,0*0B')
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        val = int(re.findall(pattern,data)[0])
        if val == 1:
            print('Data file logging is now on!')
        elif val == 0:
            print('Data file logging is now off!')    



    def delete_file(self,filename):
        '''Delete a known file from the controller.
        filename -- a single name or list of names.
        '''
        if not isinstance(filename,list):
            filename = [filename]
        for f in filename:
            self.write_command('$PWETC,PC,,,,DEL,1,{}*'.format(f))
            time.sleep(0.1)


    def exit2picodos(self):
        '''Move to picodos.
            The exit commands retains power to any controller 
            peripherals that are on.
        '''      
        self.write_command('$PWETC,PC,,,,EXIT*4E')
        time.sleep(3)
        
    
    def get_battery_status(self,position):
        '''Get battery information.
        position -- a string or integer with the value of 1 or 2.
        return -- an array that contains the following in this order
            1: position
            2: state
            3: voltage
            4: current
            5: temperature
            6: minimum cell voltage
            7: maximum cell voltage
            8: leak detect state
            9: watts
            10: runtime of battery
        '''      
        self.write_command('$PWETC,PC,,,,BFS,1,{}*'.format(int(position)))
        time.sleep(3)
        buffer = self.rs232.readlines()
        response = buffer[-1]
        data = response.decode()
        if "LOCKED" in data:
            print('Battery at this address does not exist.')
            return False     
        pweta_pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        info = re.findall(pweta_pattern,data)[0]
        info_split = info.split(' ')
        info_split = [i for i in info_split if i]
        position = info_split[0]
        state = info_split[1]
        #error_state = state[-1]
        voltage = float(info_split[2])
        current = float(info_split[3])
        temp = float(info_split[4])
        mincell = float(info_split[5])
        maxcell = float(info_split[6])
        leak = int(info_split[7])
        watts = float(info_split[8])
        runtime = info_split[9]
        #mode = info_split[10]
        #dis1 = int(info_split[11])
        #dis2 = int(info_split[12])
        #sleeptimer = int(info_split[13])
        info = [position,state,voltage,current,temp,mincell,maxcell,leak,watts,
                runtime]
        print('Battery voltage is {}v.'.format(voltage))
        print('Battery has been enabled for {} (HH:MM:SS).'.format(runtime))
        print('Battery max/min cell voltage is {}/{}.'.format(maxcell,mincell))
        return info


    def get_data_file(self,filename,handshake_delay=0.075):
        '''Get a file that is on the control can that is not a debug, winch,
            or decimated file.
        filename -- a file name or list of file names
        handshake_delay -- number of seconds to wait between handshakes.
        '''
        if not isinstance(filename,list):
            filename = [filename]
        for f in filename:
            self.write_command('$PWETC,PC,,,,GET,1,{}*'.format(f))
            time.sleep(0.5)
            data = []
            while True:
                time.sleep(handshake_delay) #Handshake for 512 is about 60ms.
                incoming = self.rs232.in_waiting
                print(incoming)
                if incoming == 0:
                    break
                else:
                    received = self.rs232.read(incoming)
                try:
                    msg = received.decode()
                    if 'DONE' in msg or 'ACK' in msg:
                        break
                except:
                    pattern = rb".*\$PWETB,.*?,.*?,.*?,.*?,.*?,.*?,(.*)"
                    dropped_leader = re.findall(pattern,received,re.DOTALL)[0]
                    dropped_checksum = dropped_leader[:-5]
                    data.append(dropped_checksum)
                    self._send_ack()        
            datafile = open(f,"wb")
            for item in data:
                datafile.write(item)
            datafile.close()
            self.clear_buffers()
            time.sleep(3)
    
    
    def get_debug_file(self,filename,handshake_delay=0.1):
        '''Get a debug file.
        filename -- a file name or list of file names
        handshake_delay -- number of seconds to wait between handshakes.
        '''
        if not isinstance(filename,list):
            filename = [filename]
        for f in filename:
            self.write_command('$PWETC,PC,,,,GET,1,{}*'.format(f))
            time.sleep(0.1)
            data = []
            while True:
                time.sleep(handshake_delay) #Handshake for 512 is about 60ms.
                print(self.rs232.in_waiting)
                received = self.rs232.read(self.rs232.in_waiting)
                try:
                    msg = received.decode()
                    if 'DONE' in msg or 'ACK' in msg:
                        break
                    else:
                        pattern = rb".*\$PWETB,.*?,.*?,.*?,.*?,.*?,.*?,(.*)"
                        dropped_leader = re.findall(pattern,received,re.DOTALL)[0]
                        dropped_checksum = dropped_leader[:-5]
                        data.append(dropped_checksum)
                        self._send_ack()                     
                except:
                    pattern = rb".*\$PWETB,.*?,.*?,.*?,.*?,.*?,.*?,(.*)"
                    dropped_leader = re.findall(pattern,received,re.DOTALL)[0]
                    dropped_checksum = dropped_leader[:-5]
                    data.append(dropped_checksum)
                    self._send_ack()        
            datafile = open(f,"wb")
            for item in data:
                datafile.write(item)
            datafile.close()    
            self.clear_buffers()
            time.sleep(3)


    def get_decimated_file(self,filename,handshake_delay=0.1):
        '''Get a decimeted file that is on the control can.
        filename -- a file name or list of file names
        handshake_delay -- number of seconds to wait between handshakes.
        '''
        if not isinstance(filename,list):
            filename = [filename]
        for f in filename:
            self.write_command('$PWETC,PC,,,,GDF,1,{}*'.format(f))
            time.sleep(0.5)
            data = []
            while True:
                time.sleep(handshake_delay) #Handshake for 512 is about 60ms.
                incoming = self.rs232.in_waiting
                print(incoming)
                received = self.rs232.read(incoming)
                try:
                    msg = received.decode()
                    if 'DONE' in msg or 'ACK' in msg:
                        break
                except:
                    pattern = rb".*\$PWETB,.*?,.*?,.*?,.*?,.*?,.*?,(.*)"
                    dropped_leader = re.findall(pattern,received,re.DOTALL)[0]
                    dropped_checksum = dropped_leader[:-5]
                    data.append(dropped_checksum)
                    self._send_ack()       
            deci_f_name = f.replace(f[-1],'D')
            datafile = open(deci_f_name,"wb")
            for item in data:
                datafile.write(item)
            datafile.close()
            self.clear_buffers()
            print("{} offloaded.".format(deci_f_name))
            time.sleep(3)
    

    def get_memory(self):
        '''Get the total, used, and free memory space on the control can.
        return -- total, used, and free memory (in that order).
        '''
        self.write_command('$PWETC,PC,,,,FREE*5A')        
        buffer = self.read_until_lf()
        data = buffer.decode()
        fpattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        free = int(re.findall(fpattern,data)[0])
        time.sleep(0.5)
        self.write_command('$PWETC,PC,,,,TOTAL*0C')
        buffer = self.read_until_lf()
        data = buffer.decode()
        tpattern =  '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        total = int(re.findall(tpattern,data)[0])    
        used = total - free        
        return total,used,free
    
 
    def get_surface_switch_status(self):
        '''Get the submerged/surface status of the pressure switch.
        return -- a string that says submerged or surface.
        '''
        self.write_command('$PWETC,PC,,,,PSW*1A')
        time.sleep(0.2)
        received = self.rs232.read_until()
        data = received.decode()
        if 'SUBMERGED' in data:
            state = 'SUBMERGED'
        elif 'SURFACE' in data:
            state = 'SURFACE'
        else:
            state = 'UNKNOWN'
        return state                
   
   
    def get_winch_file(self,filename,handshake_delay=0.1):
        '''Get a winch file that is on the control can.
        filename -- a file name or list of file names
        handshake_delay -- number of seconds to wait between handshakes.
        '''
        if not isinstance(filename,list):
            filename = [filename]
        for f in filename:
            self.write_command('$PWETC,PC,,,,GET,1,{}*'.format(f))
            time.sleep(0.5)
            data = []
            while True:
                time.sleep(handshake_delay) #Handshake for 512 is about 60ms.
                incoming = self.rs232.in_waiting
                print(incoming)
                if incoming == 0:
                    break
                else:
                    received = self.rs232.read(incoming)
                try:
                    msg = received.decode()
                    if 'DONE' in msg or 'ACK' in msg:
                        break
                except:
                    pattern = rb".*\$PWETB,.*?,.*?,.*?,.*?,.*?,.*?,(.*)"
                    dropped_leader = re.findall(pattern,received,re.DOTALL)[0]
                    dropped_checksum = dropped_leader[:-5]
                    data.append(dropped_checksum)
                    self._send_ack()        
            datafile = open(f,"wb")
            for item in data:
                datafile.write(item)
            datafile.close()
            self.clear_buffers()
            time.sleep(3)        
        
    
    def get_working_directory(self):
        '''Get the current working directory.
        return -- The directory structure of the current working directory.
        '''
        self.write_command('$PWETC,PC,,,,PWD*0D')
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'   
        structure = re.findall(pattern,data)[0]
        if structure == '':
            print('Working directory is at root level.')
            structure = 'root'
        return structure
    
    
    def list_files(self):
        '''List the files on the controller.
        return -- a list of filenames and a list of respective file sizes.
        '''
        self.write_command('$PWETC,PC,,,,DIR,1,#.#*0E')
        time.sleep(30)
        buffer = self.rs232.in_waiting
        received = self.rs232.read(buffer)
        data = received.decode()       
        file_list = data.split('\r\n')
        filenames = []
        sizes = []
        for pweta in file_list:
            try:
                params = int(pweta.split(',')[6])
                if params != 1:
                    size = pweta.split(',')[8]
                    size = int(re.findall('(.*?)\*',size)[0])
                    filepath = pweta.split(',')[7]
                    filename = filepath.split('\\')[-1]
                    filenames.append(filename)
                    sizes.append(size)
            except:
              time.sleep(0.010)
        self.sizes = sizes
        return filenames,sizes    

    
    def list_winch_files(self):
        '''List the files on the winch.
        return -- a list of filenames and a list of respective file sizes.
        '''        
        self.write_command('$PWETC,WC,,,,DIR,1,#.#*09')
        time.sleep(3)
        buffer = self.rs232.in_waiting
        received = self.rs232.read(buffer)
        data = received.decode()
        file_list = data.split('\r\n')
        filenames = []
        sizes = []
        for pweta in file_list:
            try:
                params = int(pweta.split(',')[6])
                if params != 1:
                    size = pweta.split(',')[8]
                    size = int(re.findall('(.*?)\*',size)[0])
                    filepath = pweta.split(',')[7]
                    filename = filepath.split('\\')[-1]
                    filenames.append(filename)
                    sizes.append(size)
            except:
              time.sleep(0.010)
        self.sizes = sizes   
        return filenames,sizes


    def make_directory(self,directory_id):
        '''Make a new directory in the current working directory on the
            controller.
        directory_id -- an 8 character "folder" name.
        return -- true/false if the directory was created.
        '''
        if len(str(directory_id)) > 8:
            print('Subdirectories must be 8 alphanumeric characters or less.')
            return False
        self.write_command('$PWETC,PC,,,,MKD,1,.\{}*'.format(directory_id))
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,(.*?)\*'
        created = re.findall(pattern,data)[0]
        if created == 'MKD':
            return True
        else:
            return False
 
        
    def make_winch_directory(self,directory_id):
        '''Make a new directory in the current working directory on the winch.
        directory_id -- an 8 character "folder" name.
        return -- true/false if the directory was created.
        '''        
        if len(str(directory_id)) > 8:
            return False
        self.write_command('$PWETC,WC,,,,MKD,1,\{}*'.format(directory_id))
              
    
    def open_connection(self,port,baudrate=115200,timeout=1):        
        """Open a RS232 connection to the profiler at the specified port.
        baudrate -- default is 115200 bps.
        timeout -- how long to wait for a connection to occur before aborting.
        return -- true if the connection was successful, false if not.
        """
        self.rs232.port = port
        self.rs232.baudrate = baudrate
        self.rs232.timeout = timeout        
        try:
            self.rs232.open()
            return True
        except:
            return False
        
    
    def power_acoustic_modem(self,state):
        '''OOI THETIS ONLY
        Cycle power to the acoustic modem.
        state -- on/off 
        '''
        if state == 'ON':
            self.write_command('$PWETC,PC,,,,ATMP,1,1*46')
        elif state == 'OFF':
            self.write_command('$PWETC,PC,,,,ATMP,1,0*47')  
        buffer = self.read_until_lf()
        data = buffer.decode()
        if "now ON" in data:
            print('Acoustic modem is now on!')
        elif "now OFF" in data:
            print('Acoustic modem is now off!')


    def power_pump(self,state):
        '''Turn on/off the ACS pump.
        state -- on/off
        '''
        if state == 'ON':
            self.write_command('$PWETC,PC,,,,PWR,2,PMP,1*79')
        elif state == 'OFF':
            self.write_command('$PWETC,PC,,,,PWR,2,PMP,0*78')
        buffer = self.read_until_lf()
        data = buffer.decode()
        if "ON" in data:
            print('ACS pump is now on!')
        elif "OFF" in data:
            print('ACS pump is now off!')            
            

    def power_sensors(self,state):
        '''Turn on/off the sensors (including CTD).
        state -- on/off
        '''        
        if state == 'ON':
            self.write_command('$PWETC,PC,,,,CTDP,1,1*4D')
            buffer = self.read_until_lf()
            ctd_d = buffer.decode()
            time.sleep(0.5)
            self.write_command('$PWETC,PC,,,,INSP,1,1*4A')
            buffer = self.read_until_lf()
            insp_d = buffer.decode()   
            if "ON" in ctd_d and "ON" in insp_d:
                print('Sensors are now on!')
        elif state == 'OFF':
            while True:  #Keep trying to turn off the sensors until successful.
                self.write_command('$PWETC,PC,,,,CTDP,1,0*4C')
                buffer = self.read_until_lf()
                ctd_d = buffer.decode()
                self.clear_buffers()
                time.sleep(0.5)
                self.write_command('$PWETC,PC,,,,INSP,1,0*4B')
                buffer = self.read_until_lf()
                insp_d = buffer.decode()      
                self.clear_buffers()
                time.sleep(0.5)
                if "OFF" not in ctd_d and "OFF" not in insp_d:
                    time.sleep(1)
                    continue
                elif "OFF" in ctd_d and "OFF" in insp_d:
                    print('Sensors are now off!')
                    break
 
    
    def power_winch(self,state):
        '''Turn on/off the winch.
        state -- on/off
        '''           
        if state == 'ON':
            self.write_command('$PWETC,PC,,,,WP,1,1*49')
        elif state == 'OFF':
            self.write_command('$PWETC,PC,,,,WP,1,0,*48')
        buffer = self.read_until_lf()
        data = buffer.decode()
        if "ON" in data:
            print('Winch is now on!')
        elif "OFF" in data:
            print('Winch is now off!')    
    
    
    def quit2picodos(self):
        '''Move to picodos.
        The quit function shuts off power to instruments before proceeding.
        '''
        self.write_command('$PWETC,PC,,,,Q*1F')
        time.sleep(3)
            
    
    def read_until_lf(self):
        """Read a response from the profiler until a linefeed character (\n)
        is received.
        return -- a sequence of byte data.
        """
        byte_data = self.rs232.read_until()
        return byte_data
    
    
    def remove_directory(self,directory_id):
        '''Remove a directory on the controller.
        directory_id -- a known subdirectory in the current working directory.
        return -- true/false if command is accepted/not accepted.
        '''
        self.write_command('$PWETC,PC,,,,RMD,1,.\{}*'.format(directory_id))
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,(.*?)\*'   
        removed = re.findall(pattern,data)[0]
        if removed == 'RMD':
            return True
        elif removed == 'NAK':
            print('Directory does not exist. Could not remove.')
            return False
        else:
            return False
        

    def send_break(self):
        '''Send a break to the control can to stop file offloads.
        The buffers are cleared after the break to ensure no garbage is carried
        over.
        '''
        self.write_command('$PWETC,PC,,,,BREAK*11')
        time.sleep(0.1)
        self.clear_buffers()


    def set_breakaway_depth(self,value=0.70):
        '''Set the profiler's breakaway depth.
        This value should be less than radio/stop depth.
        value -- breakaway depth in meters.
        return -- true/false if command is accepted/not accepted.
        '''
        value = float(value)
        self.write_command('$PWETC,PC,,,,BD,1,{}*'.format(value))       
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        returned_val = float(re.findall(pattern,data)[0])
        if returned_val == value:
            return True
        else:
            return False        
        
    def set_buf(self,value=512):
        '''Set the number of bits the control can sends for each handshake 
            during file offloads.
        value -- the number of bytes at each handshake. 
        
        WARNING: This value impacts telecommmunication transfers and 
        should be reset before deployment. (e.g. optimal for OOI iridium
        profilers is 512)
        
        WARNING: Values greater than 512 may result in incomplete data 
            transfers.
        '''
        self.write_command('$PWETC,PC,,,,BUF,1,{}*'.format(value))
        time.sleep(0.150)
        buffer = self.read_until_lf()        
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        buf = int(re.findall(pattern,data)[0])
        if buf == value:
            return True
        else:
            return False
    
    
    def set_datetime(self,tzo=0):
        '''Set the control can RTC to the current time in UTC.
        tzo -- timezone offset as an integer between 0 and 23.
        return -- true/false if the profiler reports a time that matches the 
            the time that was the command sent.
        '''
        now = datetime.datetime.utcnow()
        now = now.replace(microsecond=0)
        d = datetime.datetime.strftime(now,'%m/%d/%Y') 
        t = datetime.datetime.strftime(now,'%H:%M:%S')
        tzo = int(tzo)
        self.write_command('$PWETC,PC,,,,DATE,3,{},{},{}*'.format(d,t,tzo))
        buffer = self.read_until_lf()
        data = buffer.decode()
        dpattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?),.*?,.*?\*'
        d = re.findall(dpattern,data)[0]
        tpattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,.*?,(.*?),.*?\*'
        t = re.findall(tpattern,data)[0]
        dt_pro = d + 'T' + t
        dt_pro = datetime.datetime.strptime(dt_pro,'%m/%d/%YT%H:%M:%S')
        if dt_pro == now:
            return True
        else:
            return False


    def set_hld(self,mode=1):
        '''Set the winch hold mode.
        mode -- if mode is set to 1, the winch will operate at the surface with
            respect to the STA value (set through the STA command). If set to 
            0, the winch will not operate at the surface.
        return -- True/False if the command is accepted/not accepted.        
        '''
    
        if int(mode) == 1:
            self.write_command('$PWETC,PC,,,,HLD,1,1*0E')
        elif int(mode) == 0:
            self.write_command('$PWETC,PC,,,,HLD,1,0*0F')
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        val = int(re.findall(pattern,data)[0])
        if val == mode:
            return True
        else:
            return False
    


    def set_parking_depth(self,value):
        '''Set the parking depth in meters.
        value -- parking depth in meters
        return -- True/False if the command is accepted/not accepted.
        '''
        value = float(value)
        self.write_command('$PWETC,PC,,,,PKD,1,{}*'.format(value))
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        returned_val = float(re.findall(pattern,data)[0])
        if returned_val == value:
            return True
        else:
            return False
 

    def set_profile_number(self,value=0):
        '''Set the profiler number value. 
            If it is a new deployment, this value should be set to 0.
        value -- the profiler number
        return -- True/False if the command is accepted/not accepted.
        '''
        value = int(value)
        self.write_command('$PWETC,PC,,,,num,1,{}*'.format(int(value)))
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        returned_val = int(re.findall(pattern,data)[0])
        if returned_val == value:
            return True
        else:
            return False        


    def set_scooch(self,interval=250,max_delta=5000,travel=150000,
                            min_delta=2500):
        '''Set the scooch settings.
        interval -- minutes in between scooches
        max_delta -- maximum distance to move in encoder counts
        travel -- number of cumulative encoder counts before the profiler 
            returns to home depth
        min_delta -- minimum distance to move in encoder counts
        '''
        self.write_command('$PWETC,PC,,,,SCS,4,{},{},{},{}*'.format(interval,
                           max_delta,travel,min_delta))
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        settings = re.findall(pattern,data)[0]
        pro_set = settings.split(',')
        pro_set = list(map(float,pro_set))
        user_set = [interval,max_delta,travel,min_delta]
        user_set = list(map(float,user_set))        
        if pro_set == user_set:
            return True
        else:
            return False

        
    def set_sta(self,value=1.0):
        '''Set the stop amps for the winch while in surface hold mode.
        value -- default is 1.0 amps. positive values will spool on rope. 
            negative values spool off rope. THE MANUAL RECOMMENDS NOT USING
            NEGATIVE VALUES (pg 100).
        return -- True/False if the command was accepted/not accepted.
        '''
        self.write_command('$PWETC,WC,,,,STA,1,{}*'.format(value))
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?)\*'
        amps = float(re.findall(pattern,data)[0])
        if amps < value - 0.01:
            return False
        elif amps == value or amps + 0.01 == value:
            return True
        
    
    def transfer_winch_files(self):
        '''Transfer winch files from the winch controller to the profiler 
            controller.
        '''      
        winch_files,winch_file_sizes = self.list_winch_files()
        for winch_file in winch_files:
            self.write_command('$PWETC,WC,,,,GWF,1,{}*'.format(winch_file))
            time.sleep(1)
            received = self.read_until_lf()            
            data = received.decode()
            if "DONE" in data:
                print('Winch file transferred!')


    def turn_off_wave_height_estimator(self):
        '''Turn off the WHS function.
        return -- True/False if successful/not successful.
        '''
        self.write_command('$PWETC,PC,,,,WHS,1,0*03')
        buffer = self.read_until_lf()
        data = buffer.decode()
        pattern = '\$PWETA,.*?,.*?,.*?,.*?,.*?,.*?,(.*?),.*?,.*?,.*?\*'
        state = int(re.findall(pattern,data)[0])
        if state == 0:
            return True
        else: 
            return False
        
    
    def winch_brake(self,state):
        '''Engage or disenage the winch brake.
        state -- OFF/ON for disenage/engage
        '''
        if state == 'OFF':
            self.write_command('$PWETC,WC,,,,B,1,0*0A')
        elif state == 'ON':
            self.write_command('$PWETC,WC,,,,B,1,1*0B')       
        time.sleep(0.05)
        received = self.read_until_lf()
        data = received.decode()
        if 'B,1,1' in data:
            print('Brake is on!')
        elif 'B,1,0' in data:
            print('Brake is off!')       
          
            
    def write_command(self,command):
        """Encode and send a command to the profiler.
        command -- a PWET[A,B,C] command string.
        
        Note: Nothing is returned. This function appends a 
            newline character to each string.
        """
        cmd = str.encode(command + '\n')
        self.rs232.write(cmd)
    
    
    def _send_ack(self):
        """Send an acknowledgement to the control can (for file offloads).
        Note: If using this function, you will need to use a delay to ensure
            prevent communication issues. A delay of 100ms is appropriate.
        """
        self.write_command('$PWETA,PC,,,,ACK*05')
    
    
    def _send_nak(self):
        '''Send a no acknowledgement to the control can (for file offloads).
        '''
        self.write_command('$PWETC,PC,,,,NAK*0A')
            

#-------------------PICODOS (UNDER DEVELOPMENT)------------------------------#       
    def back2host(self):
        self.rs232.write('APP\r'.encode())
        time.sleep(3)
        
        
    def get_pkg_settings(self):
        self.clear_buffers()
        self.rs232.write('SET\r'.encode())
        time.sleep(1)
        received = self.rs232.read_until('C:\>')
        data = received.decode()
        return data
        
    
    def get_acs_output_setting(self):
        self.clear_buffers()
        self.rs232.write('SET PKG.ACSB\r'.encode())
        time.sleep(0.5)
        received = self.rs232.read_until('C:\>')
        data = received.decode()
        return data
        
    
    def set_acs_output_setting(self,output_wavelengths):
        self.clear_buffers()
        self.rs232.write('SET PKG.ACSB={}\r'.format(int(output_wavelengths)))
        time.sleep(0.5)
        received = self.rs232.read_until('C:\>')
        data = received.decode()       
        return data        
 

