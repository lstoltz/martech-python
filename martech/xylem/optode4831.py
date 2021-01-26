from martech.sercom import SERCOM
import time

class OPTODE4831():
    def __init__(self,port):
        self.rs232 = SERCOM()
        self.port = port
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.flowcontrol = True
        self.timeout = 1     
    
    def open_connection(self,baudrate=115200):
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
            self.rs232.write_command("STOP",EOL='\r\n')
            self.rs232.write_command("",EOL='\r\n')
            response = self.rs232.read_response()
            if "#" in response:
                self._force_new_command_prompt()
                self.rs232.read_response()
                self.rs232.clear_buffers()
                return True
            else:
                continue
    
    def get_settings(self):
        while True:
            self.rs232.write_command('get\sall',EOL='\n')
            response = self.rs232.read_response()
            if 'ERROR' in response:
                continue
            else:
                return response

    def exit_passthru(self): 
        """This is a SBS Thetis Profiler specific command."""
        self.rs232.write_command('$PWETQ',EOL='')
        response = self.rs232.read_response()
        if "PWETA" in response:
            return True
        else:
            return False
    
    def get_cal_date(self):
        self.rs232.write_command('get\slast\scalibration')
        while True:
            response = self.rs232.read_response()
            if 'ERROR' in response:
                continue
            else:
                return response
    
    def _force_new_command_prompt(self):
        for i in range(3):
            self.rs232.write_command("",EOL='\r\n')