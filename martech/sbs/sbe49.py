from martech.sercom import SERCOM
import time

class SBE49():
    def __init__(self,port):
        self.rs232 = SERCOM()
        self.port = port
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.flowcontrol = 0
        self.timeout = 3          
    
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
        self.rs232.write_command("STOP")
        self._force_new_command_prompt()
        time.sleep(1)
        response = self.rs232.read_response()
        self.rs232.clear_buffers()
        if "S>" in response:
            return True
        else:
            return False

    def get_status(self):
        self.rs232.write_command("DS")
        response = self.rs232.read_response()
        return response
    
    def get_calibration_coeffs(self):
        self.rs232.write_command("DCAL")
        response = self.rs232.read_response()
        return response

    def exit_passthru(self): 
        """This is a SBS Thetis Profiler specific command."""
        self.rs232.write_command('$PWETQ',EOL='')
        response = self.rs232.read_response()
        if "PWETA" in response:
            return True
        else:
            return False        

    def _force_new_command_prompt(self):
        for i in range(3):
            self.rs232.write_command("",EOL='\r\n')