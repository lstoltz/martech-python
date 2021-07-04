from martech.sercom import SERCOM
import os
import re
import sys
import time

def main():
    port = sys.argv[0]
    baudrate = sys.argv[1]
    bf = BATTERY(port,baudrate)
    if bf.balance_test() is True:
        bf.balance_battery()
        
    else:
        bf.close_connection()


class BATTERY():    
    def __init__(self,port,baudrate=9600):
        """Instantiate a serial object on the specified port.
        @param port -- a system specific port given as a string.
        """
        self.rs485 = SERCOM()
        self.port = port
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.flowcontrol = 0
        self.timeout = 3          
        
        try:
            if self.open_connection(baudrate) is True:
                self.sn = self.get_battery_sn()
                self.model = self.get_battery_model()
                self.fw = self.get_fw_version()
                self.device_sn = self.get_device_sn()
        except:
            msg = "Unable to connect to a battery on {} at {} bps."
            raise ValueError(msg.format(port,baudrate))
    
    def open_connection(self,baudrate=9600):
        """Open a connection to the battery at a defined baudrate.
        @param baudrate -- number of bits per second, BF 1.5kWhs are hardcoded
            for 9600 bps (use 115200 if using a passthru on the Thetis)
        @return -- True if the connection was successful.
            False if the connection was not successful.
            
        NOTE: If communicating through a Thetis profiler passthru, the baudrate
            should be set to 115200.
        """
        self.baudrate = baudrate        
        connected = self.rs485.connect(self.port,self.baudrate,
                                       self.bytesize,self.parity,self.stopbits,
                                       self.flowcontrol,self.timeout)
        self.rs485.clear_buffers()
        return connected      
    
    def close_connection(self):
        """Close the serial port.
        @return -- True if the connection closed successfully.
            False if the connection did not close successfully.
        """
        disconnected = self.rs485.disconnect()
        return disconnected        

    def _format_address(self,address):
        """Formats a decimal value into a hexadecimal value that works
            with the Bluefin 1.5 kWh.
        @param address -- a decimal value ranging between 0 and 250.
        @return -- the address as a hexadecimal value if the input address
            was between 0 and 250. False if the address is outside of that 
            range.
        """
        if address >=1 and address <= 250:
           address = hex(int(address)) #Convert address if between 0-250.
           if len(address) == 3: #Take the last char and append a zero.
               address = str(address[-1]).rjust(2,'0')
           elif len(address) == 4:
               address = address[-2:] #Take the last two char.              
           return address
        elif address == 0:
            address = '00'
            return address
        else:
            return False
    
    def set_address(self,address):
        """Sets the battery address.
        @param address -- a decimal value ranging between 0 and 250
        """ 
        new_address = self._format_address(address)
        self.rs485.write_command('#00?8 {}'.format(new_address))
        self.rs485.clear_buffers()
        time.sleep(0.2)
        
    def get_address(self):
        """Get the battery address. This function only works when the battery
        is the only one connected.
        @return -- the address as a decimal value.
        """
        self.rs485.clear_buffers()
        self.rs485.write_command('#00?0')
        response = self.rs485.read_response()
        pattern = '\$.*? (.*?) \r\n'
        hexval = re.findall(pattern,response).pop()
        address = int(hexval,16)
        return address
    
    def get_summary(self,address=0):
        """Get the battery summary info of the battery at the givenn address.
        @param address -- a decimal value.
        @return -- a summary string.
        """
        address = self._format_address(address)
        self.rs485.write_command('#{}q0'.format(address),EOL='\r\n')
        response = self.rs485.read_until_byte_string('\r\n')
        return response
    
    def get_battery_state(self,address=0):
        """Get the battery state and print a message.
        @param address -- a decimal value.
        @return -- a character indicating the battery state. See BF manual.
        """
        response = self.get_summary(address)
        pattern = '\$.... (.). .*?  .*? .*? .*? .*? . .*?  .*? . . . .*?\r\n'
        state = re.findall(pattern,response).pop()
        if state == 'f':
            msg = 'OFF'
        elif state == 'd':
            msg = 'DISCHARGING.'
        elif state == 'c':
            msg = 'CHARGING.'
        elif state == 'b':
            msg = 'BALANCING.'
        return state,msg
    
    def get_error_state(self,address=0):
        """Get the battery error state and print a message.
        @param address -- a decimal value.
        @return -- a character indicating the error state. See BF manual.
        """
        response = self.get_summary(address)
        pattern = '\$.... .(.) .*?  .*? .*? .*? .*? . .*?  .*? . . . .*?\r\n'
        error = re.findall(pattern,response).pop()
        if error == '-':
            msg = 'No Error'
        elif error == 'V':
            msg = 'Battery over voltage'
        elif error == 'v':
            msg = 'Battery under voltage'
        elif error == 'I':
            msg = 'Battery over current'
        elif error == 'C':
            msg = 'Battery max cell over voltage'
        elif error == 'c':
            msg = 'Battery min cell under voltage'
        elif error == 'x':
            msg = 'Battery min cell under fault voltage (2.0V)'
        elif error == 'T':
            msg = 'Battery over temperature'
        elif error == 'W':
            msg = 'Battery moisture intrusion detected by H2O sensors'
        elif error == 'H' or error == 'h':
            msg = 'Battery internal hardware fault'
        elif error == 'm':
            msg = 'Battery watchdog timeout'
        return error,msg
    
    def get_voltage(self,address=0):
        """Get the battery voltage
        @param address -- a decimal value.
        @return -- a float value representing the overall battery voltage.
        """
        response = self.get_summary(address)
        pattern = '\$.... .. (.*?)  .*? .*? .*? .*? . .*?  .*? . . . .*?\r\n'
        voltage = float(re.findall(pattern,response).pop())
        return voltage
        
    def get_current(self,address=0):
        """Get the battery current.
        @param address -- a decimal value.
        @return -- a float value representing the battery current.
        """
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  (.*?) .*? .*? .*? . .*?  .*? . . . .*?\r\n'
        current = float(re.findall(pattern,response).pop())
        return current

    def get_temperature(self,address=0):
        """Get the battery oil temperature.
        @param address -- a decimal value.
        @return -- a float value representing the temperature of the oil.
        """
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  .*? (.*?) .*? .*? . .*?  .*? . . . .*?\r\n'
        temperature = float(re.findall(pattern,response).pop())
        return temperature
    
    def get_min_cell_voltage(self,address=0):
        """Get the minimum cell voltage.
        @param address -- a decimal value.
        @return -- the minimum cell voltage as a float value.
        """
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  .*? .*? (.*?) .*? . .*?  .*? . . . .*?\r\n'
        minv = float(re.findall(pattern,response).pop())
        return minv
    
    def get_max_cell_voltage(self,address=0):
        """Get the maximum cell voltage.
        @param address -- a decimal value.
        @return -- the maximum cell voltage as a float value.
        """        
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  .*? .*? .*? (.*?) . .*?  .*? . . . .*?\r\n'
        maxv = float(re.findall(pattern,response).pop())
        return maxv        
        
    def water_detected(self,address=0):
        """Get the water intrusion detection state.
        @param address -- a decimal value.
        @return -- True if water intrusion is detected. False if not water
            intrusion is detected.
        """
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  .*? .*? .*? .*? (.) .*?  .*? . . . .*?\r\n'
        water = int(re.findall(pattern,response).pop())
        if water == 0:
            return False
        elif water == 1:
            return True 
         
    def get_wattage(self,address=0):
        """Get the battery wattage.
        @param address -- a decimal value between 0-250.
        @return -- the wattage as a float value.
        """
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  .*? .*? .*? .*? . (.*?)  .*? . . . .*?\r\n'
        watts = float(re.findall(pattern,response).pop())        
        return watts
    
    def get_runtime(self,address=0):
        """Get the amount of time the battery has been enabled.
        @param address -- a decimal value.
        @return -- a three element list of strings consisting 
            of [hours, minutes,seconds].
        """
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  .*? .*? .*? .*? . .*?  (.*?) . . . .*?\r\n'
        runtime = re.findall(pattern,response).pop()  
        hms = runtime.split(':')
        msg = 'Battery has been enabled for {}h, {}m, and {}s.'
        print(msg.format(hms[0],hms[1],hms[2]))
        return hms
    
    def get_sleep_timer(self,address=0):
        '''Get the number of seconds until the battery goes to sleep.
        @param address -- a decimal value between 0-250.
        @return -- the number of seconds until the battery goes to sleep.
        '''
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  .*? .*? .*? .*? . .*?  .*? . . .( .*?)\r\n'
        timer = int(re.findall(pattern,response).pop())        
        if timer == 0:
            print('Sleep timer is disabled.')
        else:
            print('Battery will go to sleep in {} seconds.'.format(timer))
        return timer
        
    def get_version_summary(self,address=0):
        '''Get the battery info summary.
        @param address -- a decimal value between 0-250.
        @return -- the version summary as an unparsed string.
        '''
        address = self._format_address(address)  
        self.rs485.write_command('#{}z0'.format(address),EOL= '\r\n')
        response = self.rs485.read_response()
        return response
    
    def get_battery_sn(self,address=0):
        '''Get the battery serial number.
        @param address -- a decimal value between 0-250.
        @return -- the serial number as an integer.
        '''
        response = self.get_version_summary(address)
        pattern = '\$.*? .*? .*? .*? (.*?) .*? .*? .*? .*? \r\n' 
        battery_number = int(re.findall(pattern, response).pop())
        return battery_number
    
    def get_fw_version(self,address=0):
        """Get the firmware version.
        @param address -- a decimal value between 0-250
        @return -- the firmware as a string
        """
        response = self.get_version_summary(address)
        pattern = '\$.*? .*? .*? .*? .*? .*? .*? .*? (.*?) \r\n' 
        fw_version = re.findall(pattern,response).pop()
        return fw_version

    def get_battery_model(self,address=0):
        """Get the battery board device model.
        @param address -- a decimal value
        @return -- the model as a string
        """
        response = self.get_version_summary(address)
        pattern = '\$.*? .*? .*? .*? .*? .*? .*? (.*?) .*? \r\n' 
        model = re.findall(pattern,response).pop()
        return model
    
    def get_voltage_rating(self,address=0):
        """Get the battery's voltage rating.
        @param address -- a decimal value
        @return -- the voltage rating as an integer
        """
        response = self.get_version_summary(address)
        pattern = '\$.*? .*? .*? .*? .*? (.*?) .*? .*? .*? \r\n' 
        rating = int(re.findall(pattern,response).pop())
        return rating
    
    def get_current_rating(self,address=0):
        """Get the battery's current rating.
        @param address -- a decimal value
        @return -- the current rating as an integer
        """
        response = self.get_version_summary(address)
        pattern = '\$.*? .*? .*? .*? .*? .*? (.*?) .*? .*? \r\n' 
        rating = int(re.findall(pattern,response).pop())
        return rating    
    
    def get_mode(self,address=0):
        """Get the battery mode.
        @param address -- a decimal value between 0-250
        @return -- the battery mode as a single character string (m or s)
        """
        response = self.get_version_summary(address)
        pattern = '\$.*? .*? (.*?) .*? .*? .*? .*? .*? .*? \r\n' 
        mode = re.findall(pattern,response).pop()
        return mode  
    
    def get_device_sn(self,address=0):
        """Get the board serial number.
        @param address -- a decimal value between 0-250.
        @return -- the device serial number as an integer.
        """
        response = self.get_version_summary(address)
        pattern = '\$.*? .*? .*? (.*?) .*? .*? .*? .*? .*? \r\n' 
        mcu_sn = int(re.findall(pattern,response).pop())
        return mcu_sn          
    
    def sleep(self,address=0,length=10):
        """Put the battery to sleep.
        @param address -- a decimal value
        @param length -- the number of seconds to wait before going to sleep.
        """
        address = self._format_address(address)
        self.rs485.write_command('#{}bs {}'.format(address,address),EOL='\r\n')    
    
    def output_off(self,address=0):
        """Turn off the battery output.
        This resets any existing errors.
        @param address -- a decimal value.
        """
        address = self._format_address(address)
        self.rs485.write_command('#{}bf'.format(address),EOL='\r\n')
        time.sleep(1)
     
    def discharge_mode(self,address=0):
        """Put the battery in discharge mode. A load must be applied to the
            battery before issuing this command.
        @param address -- a decimal value.
        """
        user_response = input("Is the battery under load? [Y/N] :")
        if user_response.upper() != 'Y':
            msg = 'Exiting discharge mode attempt because the battery is not under load.'
            raise ValueError(msg)
        else:
            address = self._format_address(address)
            self.rs485.write_command('#{}bd'.format(address),EOL='\r\n')                          
                     
    def discharge_cell(self,cell,address=0):
        address = self._format_address(address)
        self.rs485.write_command('#{}b{}'.format(address,cell),EOL='/r/n')
        response = self.rs485.read_response()
        if '1' in response:
            return True
        elif '0' in response:
            return False

    def get_cell_voltages(self,address=0):
        address = self._format_address(address)
        self.rs485.write_command('#{}q1'.format(address),EOL='/r/n')
        response = self.rs485.read_response()     
        #Need to figure out pattern.
        
        
#-----------------------------Auto Balance----------------------------------#   
    def balance_battery(self,address=0,timeout=86400):
        address = self._format_address(address)
        start = int(time.time())
        
        
        
        
        
        
        


                                 
#-----------------------------GDMS-BF Tests----------------------------------#   
    def balance_test(self,address=0):
        """Compare the min and max cell voltages. If the delta between values
        exceeds 0.1V, it is recommended that the battery be balanced.
        @param address -- a decimal value
        @return -- a string message
        """
        mincell = self.get_min_cell_voltage(address)
        maxcell = self.get_max_cell_voltage(address)
        if abs(maxcell-mincell) > 0.1:
            msg = 'Recommend balancing battery.'
            print(msg)
            return True
        else:
            msg = 'Battery does not need to be balanced.'
            print(msg)
            return False

    def sleep_test(self,address=0,length=10):
        """Test the sleep functionality of the battery.
        @param address -- a decimal value
        @param length -- number of seconds to delay sleep
        @return -- True if the battery went to sleep and returned to OFF. False
            if the battery is in a state other than OFF.
        """
        print("A load must be placed on the battery before running this test.")
        load = input("Is a minimum of a 10 amp load in place? [Y/N] ")
        if load.upper() == 'Y':
            self.output_off(address)
            v = self.get_voltage(address)
            if isinstance(v,float):
                self.discharge_mode(address)
                self.sleep(address,length)
                time.sleep(1) #Buffer
                state,state_msg = self.get_battery_state(address)
                error,error_msg = self.get_error_state(address)
                if state == 'f' and error == '-':
                    return True
                else:
                    return False
        else:
            print('Apply load before proceeding.')
            exit
            
    def discharge_test(self,address=0):
        """Test the discharge functionality of the battery.
        @param address -- a decimal value
        @return -- True if the battery the measured current value exceeds zero
            at some point during the test. False if it does not exceed zero or
            if the battery does not enter the discharge state.
        """
        print("A load must be placed on the battery before running this test.")      
        self.output_off(address)
        load = input("Is a minimum of a 10 amp load in place? [Y/N] ")
        if load.upper() == 'Y':  
            self.discharge_mode(address)
            state,state_msg = self.get_battery_state(address)
            if state == 'd':
                cs=[]
                for i in range(60):
                    time.sleep(10)
                    c = self.get_current(address)
                    print("Output current: {}".format(c))
                    cs.append(c)
                self.output_off(address)
                for c in cs:
                    if c > 0:
                        return True
                return False
            else:
                return False
        else:
            print("Apply load before proceeding.")
            exit
    
#----------------------SBS Thetis Profiler Only------------------------------#
    def exit_passthru(self): 
        """This is a SBS Thetis Profiler specific command. Tells the profiler
            to exit the passthru and return back to the host program.
        """
        self.rs485.write_command('$PWETQ',EOL='')
        response = self.rs485.read_response()
        if "PWETA" in response:
            return True
        else:
            return False      


#-------------------------Under Development----------------------------------#
    def get_discharge_status(self,address=0):
        response = self.get_summary(address)
        pattern = '\$.... .. .*?  .*? .*? .*? .*? . .*?  .*? . (. .) .*?\r\n'
        statuses = re.findall(pattern,response).pop()
        status1 = statuses.split(' ')[0]
        status2 = statuses.split(' ')[1]
        for s in [status1,status2]:
            if s == '0':
                print('Discharge Status: No load or fault.')
            elif s == '1':
                print('Discharge Status: Battery is discharging normally.')
        return [status1,status2]          