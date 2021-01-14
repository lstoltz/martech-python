from martech.sercom import SERCOM
import time

class OCR():
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
            self.rs232.write_command("etx",EOL='\r\n')
            self.rs232.write_command("",EOL='\r\n')
            self.rs232.write_command("",EOL='\r\n')
            response = self.rs232.read_response()
            if "SUNA" in response:
                self.rs232.write_command("",EOL='\r\n')
                self.rs232.write_command("",EOL='\r\n')
                self.rs232.clear_buffers()
                return True
            else:
                continue







#-------------------------Thetis Profiler Only-------------------------------#
    def exit_passthru(self): 
        """This is a SBS Thetis Profiler specific command."""
        self.rs232.write_command('$PWETQ',EOL='')
        response = self.rs232.read_response()
        if "PWETA" in response:
            return True
        else:
            return False