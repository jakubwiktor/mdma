#acquisition stuff
from pycromanager import Acquisition, Bridge
from skimage import io 
import json
import time
from datetime import datetime

import acquisitionDialog

#TODO: write a metadata file
class run_acquisition:

    """running acqusition using pycromanager as a signle thread
    
    input: events - list of events as defined in pycromanager documentation

    TODO-update documentation
    """

    def __init__(self, events = None, save_path = ''):
        self.events = events
        self.save_path = save_path
        self.check_abort = 0

    def _image_process_fn(self, image, metadata, bridge, event_queue):
        #image acquisition hook for pycromanager - saves file and metadata

        real_snap_time = int(time.time()*1000)
        im_num = (metadata['Axes']['counter'])
               
        io.imsave(self.events[im_num]['save_location'], image)
        
        #update metadata - matadata is json with a format:
        #{"position":"Pos10",
        # "acquire_time":1622229839618,
        # "exposure_time":60,
        # "PosZ":8399,
        # "PosY":-4986.6,
        # "PosX":-689.4000000000001,
        # "expected_acquire_time":1622229836398,
        # "filename":"F:\\Jakub\\EXP-21-BV3236 death\\exp3\\Pos10\\aphase\\img_000000000",
        # "channel":"aphase",
        # "channel_group":"Fluor"}

        tmp = self.events[im_num]
        metadata_line = {
                         'position':tmp['pos_label'],
                         'acquire_time':real_snap_time,
                         'exposure_time':tmp['exposure'],
                         'PosZ':tmp['z'],
                         'PosY':tmp['y'],
                         'PosX':tmp['x'],
                         'expected_acquire_time':tmp['min_start_time'],
                         'filename':tmp['save_location'],
                         'channel':tmp['channel']['group'],
                         'channel_group':tmp['channel']['config']
                        }
        metadata_line['filename'] = metadata_line['filename'].replace('/','//') #<- to match ritaaquire

        with open(f"{self.save_path}/metadata.txt", 'a') as f:
            f.write( json.dumps(metadata_line, separators =(',',':')) )
            f.write('\n')

        #add events one by one
        if im_num+1 == len(self.events):#remember that numbering starts from 0 - took me a while!
            event_queue.put(None)
            print('acq finished')
        elif self.check_abort:
            event_queue.put(None)            
            print('acq aborted')
        else:
            print(im_num)
            event_queue.put(self.events[im_num+1])
            
        return image,metadata

    def _post_hardware_hook(self,event,bridge,event_queue):
        #hook before image acquisition - wait for focus here
        core = bridge.get_core()
        z_stage_name = core.get_focus_device()
        core.wait_for_device(z_stage_name)
        # print('post_hardware_hook')
        return event

    def _pre_hardware_hook(self,event):
        #placeholder
        return event

    def abort_acquisition(self,signal):
        #wait for a signal form GUI window
        self.check_abort = signal
        
    def _run(self):
        
        #here acquisition needs to be stopped by adding 'None' to event_queue
        acq =  Acquisition(image_process_fn = self._image_process_fn, post_hardware_hook_fn = self._post_hardware_hook)
        acq.acquire(self.events[0])

        #open GUI showing progress and adding aborting functionality        
        total_time = max([t['min_start_time'] for t in self.events])
        self.acquisitionDialog = acquisitionDialog.acquisitionDialog(total_time = total_time)
        self.acquisitionDialog.abort_acq.connect(self.abort_acquisition)

def main():
    acq = run_acquisition()
    acq._run()

if __name__ == '__main__':
    main()