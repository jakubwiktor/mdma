#acquisition stuff
from pycromanager import Acquisition, Bridge
from skimage import io 
import json

# import matplotlib.pyplot as plt

#TODO: write a metadata file
class RunAcquisition:

    def __init__(self, events = None, save_path = ''):
        self.events = events
        self.save_path = save_path
        
    def _image_process_fn(self,image,metadata):
       #image acquisition hook for pycromanager - saves file and metadata

        in_num = (metadata['Axes']['counter'])
       
        #find back the correct frame!
        print(self.events[in_num]['save_location'], self.events[in_num]['min_start_time'])
        
        io.imsave(self.events[in_num]['save_location'], image)
        
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

        tmp = self.events[in_num]
        metadata_line = {
                         'position':tmp['pos_label'],
                         'acquire_time':tmp['min_start_time'],
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

        return image,metadata

    def _post_hardware_hook(self,event,bridge,event_queue):
        #hook needs 1 or 3 parameters (plus 'self' because it's a class?)

        #wait for focus here?
        # with Bridge() as bridge:
        core = bridge.get_core()
        
        z_stage_name = core.get_focus_device()
        core.wait_for_device(z_stage_name)
        print('post_hardware_hook')
        return event

    def _pre_hardware_hook(self,event):
        print('pre_hardware_hook')
        return event

    def _run(self):
        
        acq =  Acquisition(image_process_fn = self._image_process_fn, 
                         post_hardware_hook_fn = self._post_hardware_hook)
        # acq =  Acquisition(image_process_fn = self._image_process_fn)
        acq.acquire(self.events)

def main():
    acq = RunAcquisition()
    acq._run()

if __name__ == '__main__':
    main()