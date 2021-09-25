#acquisition stuff
from pycromanager import Acquisition, Bridge
from skimage import io 
import cv2 as cv
import json
import time
import os
import numpy as np

from multiprocessing import Process, Queue, Value

import acquisitionDialog
from utils.barcode_code import find_barcode_region, match_barcode

class run_acquisition:
    """
    running acqusition using pycromanager as with real-time segmentation
    
    input: events - list of events as defined in pycromanager documentation

    TODO-update documentation
    TODO-error handling
    Kuba
    """

    def __init__(self, events = None, save_path = '', q = None):
        self.events = events
        self.tot_images = len(events)
        self.save_path = save_path
        
        #initialise shared values
        self.check_abort = Value('b',False) # <- shared between processes
        self.check_segmentation_completed = Value('b',False)
        
        #initialise shared queue
        self.q = Queue()

        #initialise event counter
        self.counter = 0
        
        #initialise barcode image dictionary - populate the dictionary with None
        position_names = set([x['pos_label'] for x in events])
        self.barcodes = dict()
        for p in position_names:
            self.barcodes[p] = None

    def _image_process_fn(self, image, metadata, bridge, event_queue):
        """
        update documentation
        TODO: check if the images are acquired as expected - check if im_num and self.counter
        interact as intended
        """
        #image acquisition hook for pycromanager - saves file and metadata
        
        real_snap_time = int(time.time()*1000)

        #update image counter
        im_num = self.counter
        self.counter+=1
        
        #seems the function will be called even if event_queue is None. It was throwing an error before
        if im_num+1 < len(self.events): 
            print(self.events[im_num+1])

        #add to multiprocessing queue phase image
        if self.events[im_num]['channel']['config'] == 'aphase':
            #TODO - rework this part
            #
            #detect barcode - if first image store the image
            #
            
            if self.barcodes[self.events[im_num]['pos_label']] is None:
                barcode_img = find_barcode_region(image)
                self.barcodes[self.events[im_num]['pos_label']] = barcode_img
            
            barcode_img = self.barcodes[self.events[im_num]['pos_label']]
            if barcode_img is None:
                top_left = None
                bottom_right = None
                b_image = np.zeros((100,100))
            else:
                top_left, bottom_right = match_barcode(image, barcode_img)

                #for debugging
                b_image = image[top_left[1]:bottom_right[1],top_left[0]:bottom_right[0]]
                # #save barcode image 
            
            barcode_save_path = self.events[im_num]['save_location'].replace('aphase', 'barcode')
                
            #TODO - fix this ugly shit
            if not(os.path.exists(os.path.split(barcode_save_path)[0])):
                os.makedirs(os.path.split(barcode_save_path)[0])
            
            io.imwrite(barcode_save_path, b_image)

            barcode_loc = dict()
            barcode_loc['file'] = barcode_save_path
            barcode_loc['pos'] = top_left
            
            with open(f"{self.save_path}/barcode_locations.txt", 'a') as f:
                f.write(json.dumps(barcode_loc, separators=(',',':')))
                f.write('\n')
            #
            #end of barcode testing
            #

        cv.imwrite(self.events[im_num]['save_location'], image) #i think by defalt it uses compression. 
        
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

        elif self.check_abort.value:
            event_queue.put(None)            
            print('acq aborted') # <- signal to kill the segmentation

        else:
            # print(self.events[im_num+1])
            event_queue.put(self.events[im_num+1])

    def _post_hardware_hook(self,event,bridge,event_queue):
        #hook before image acquisition - wait for focus here
        core = bridge.get_core()
        core.full_focus() #should be PFSOffset
        return event

    def _pre_hardware_hook(self,event):
        #placeholder
        return event

    def abort_acquisition(self,signal):
        #wait for a signal form GUI window
        self.check_abort.value = signal
    

    def _runAcq(self):
        #here acquisition needs to be stopped by adding 'None' to event_queue 
        acq = Acquisition(image_process_fn = self._image_process_fn, post_hardware_hook_fn = self._post_hardware_hook)
        acq.acquire(self.events[0])

    def _run(self):
        
        self._runAcq()
        
        #open GUI showing progress and adding aborting functionality        
        total_time = max([t['min_start_time'] for t in self.events])
        self.acquisitionDialog = acquisitionDialog.acquisitionDialog(total_time = total_time)
        self.acquisitionDialog.abort_acq.connect(self.abort_acquisition)

def main():
    acq = run_acquisition()
    acq._run()

if __name__ == '__main__':
    main()