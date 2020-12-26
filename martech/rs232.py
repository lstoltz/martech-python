'''A base class for communicating with oceanographic sensors over RS232.

Initial Commit: Ian Black, 2020-12-13
'''


import serial
import time

class RS232():
    def __init__(self):
        self.rs232 = serial.Serial()
                
    def connect(self,port,baudrate,
                bytesize,parity,stopbits,
                flowcontrol,timeout=1):
        self.rs232.port = port
        self.rs232.baudrate = baudrate
        self.rs232.timeout = timeout
        self.rs232.bytesize = bytesize
        self.rs232.stopbits = stopbits
        self.rs232.parity = parity
        self.rs232.xonxoff = flowcontrol
        try:
            self.rs232.open()
            print('Connected!')
            return True
        except:
            print('Unable to connect!')
            return False

    def disconnect(self):
        try:
            self.rs232.close()
            print('Disconnected!')
            return True
        except:
            print('Unable to disconnect!')
            return False

    def clear_buffers(self):
        self.rs232.reset_input_buffer()
        self.rs232.reset_output_buffer()              

    def write_command(self,command,EOL='\r'):
        cmd = str.encode(command + EOL)
        self.rs232.write(cmd)
    
    def read_bytes(self):
        self._buffer_check()
        data = self.rs232.read(self._buffer_length)
        return data
    
    def read_response(self):
        data = self.read_bytes()
        response = data.decode()
        return response
    
    def _buffer_check(self):
        buffer = self.rs232.in_waiting
        start = time.monotonic()
        time.sleep(0.1)
        while True:
            end = time.monotonic()
            incoming = self.rs232.in_waiting
            if buffer == incoming:
                self._buffer_length = buffer
                break
            else:
                if (end-start) > 30:
                    break
                buffer = incoming
                time.sleep(0.1)    

    def read_until_byte_string(self,byte_string):
        incoming = self.rs232.read_until(byte_string).decode()
        return incoming
    
