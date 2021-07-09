import os
import pwd

def get_uid():
    '''Get the username of the active user.'''
    uid = pwd.getpwuid(os.getuid()).pw_name
    return uid
    
    
    
