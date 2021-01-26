'''Profiler must have files in the working directory. You must have also
offloaded files via JProfilerHost for comparison.
'''

from martech.sbs.thetis import THETIS
import os

directory = 'C:/Users/Ian/Documents/GitHub/martech-python/examples/thetis/offload_test'
py_dir = os.path.join(directory,'python_offload')
jpro_dir = os.path.join(directory,'jprofiler_offload')

port = 'COM3'
thetis = THETIS(port)
if thetis.open_connection(115200) is True:
    info = thetis.get_version()
    print('Connected to {}.'.format(info['profiler_id']))

    files = thetis.list_files('PC')
    filenames = []
    sizes = []
    for file in files:
        filenames.append(file[0])
        sizes.append(file[1])
    
    ppds = [f for f in filenames if 'PPD' in f]
    snds = [f for f in filenames if 'SND' in f]
    acds = [f for f in filenames if 'ACD' in f]
    ppbs = [f for f in filenames if 'PPB' in f]
    snas = [f for f in filenames if 'SNA' in f]
    acss = [f for f in filenames if 'ACS' in f]
    dbgs = [f for f in filenames if 'DBG' in f]
    
    #Must offload decimated files before full files.
    thetis.offload_files(snds,py_dir)
    thetis.offload_files(snas,py_dir)
    thetis.offload_files(ppds,py_dir)
    thetis.offload_files(ppbs,py_dir)
    thetis.offload_files(acds,py_dir)
    thetis.offload_files(acss,py_dir)
    thetis.offload_files(dbgs,py_dir)
    
    thetis.close_connection()
    
py_files = os.listdir(py_dir)
jpro_files = os.listdir(jpro_dir)

#Check if there are the same number and types of files.
if py_files == jpro_files:
    print('Folder contents match!')
    for file in py_files:
        py = open(os.path.join(py_dir,file),'rb')
        py_contents = py.read()
        py.close()
        jpro = open(os.path.join(jpro_dir,file),'rb')
        jpro_contents = jpro.read()
        jpro.close()
        if py_contents == jpro_contents:
            print('{} matches!'.format(file))
        else:
            print('{} does not match!'.format(file))           



