#acquisition stuff
from pycromanager import Acquisition, Bridge
from skimage import io 
import json
import time
from datetime import datetime

#try multiprocessing
from multiprocessing import Process, Queue, Value

import acquisitionDialog

class run_acquisition:

    """running acqusition using pycromanager as with real-time segmentation
    
    input: events - list of events as defined in pycromanager documentation

    TODO-update documentation
    """

    def __init__(self, events = None, save_path = '', q = None):
        self.events = events
        self.save_path = save_path
        self.check_abort = Value('b',False) # <- shared between processes
        self.check_segmentation_completed = Value('b',False)

        #initialise shared queue
        self.q = Queue()
        
        #initialise pytorch .. pick up from here

    def _image_process_fn(self, image, metadata, bridge, event_queue):
       #image acquisition hook for pycromanager - saves file and metadata
        
        real_snap_time = int(time.time()*1000)
        
        im_num = (metadata['Axes']['counter'])

        #add to multiprocessing queue
        
        self.q.put((image, self.events[im_num]['save_location']))    

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
            self.q.put((None,None)) # <- signal to kill the segmentation
            print('acq finished')
            while not self.check_segmentation_completed.value:
                time.sleep(0.1)

        elif self.check_abort.value:
            event_queue.put(None)            
            print('acq aborted') # <- signal to kill the segmentation
            self.q.put((None,None))
            while not self.check_segmentation_completed.value:
                time.sleep(0.1)

        else:
            # print(im_num)
            event_queue.put(self.events[im_num+1])
        
        return image,metadata

    def _post_hardware_hook(self,event,bridge,event_queue):
        #hook before image acquisition - wait for focus here
        core = bridge.get_core()
        z_stage_name = core.get_focus_device() #should be PFSOffset
        core.wait_for_device(z_stage_name)
        # print('post_hardware_hook')
        return event

    def _pre_hardware_hook(self,event):
        #placeholder
        return event

    def abort_acquisition(self,signal):
        #wait for a signal form GUI window
        self.check_abort.value = signal
    
    def segment_realTime(self):
        #construct real time acquisition function that checks for queue
        import torch
        from utils.UnetPlusPlus2 import UNet
        import numpy as np
        from skimage import io, measure, morphology

        net = UNet(num_classes=1)
        saved_model = 'C:\\Users\\kubus\\Documents\\trained_models\\Unet_mixed_brightnessAdj_Adam_HybridLoss_512px_cellsUnweighted.pth' #01.06.2021
        saved_net = torch.load(saved_model)
        net.load_state_dict(saved_net['model_state_dict'])

        net.cuda()

        #this is function called by other process
        #is this possible to run the pytorch here?
        # import torch etc
        counter = 0
        while True:
            #segmentation core
            im, save_path = self.q.get()

            if im is None: #'poision pill'
                self.check_segmentation_completed.value = True
                break
            
            print(save_path)
            path_chunks = save_path.split('/')
            # path_chunks[-2] += 'segment'
            path_chunks[-1] = f"seg{path_chunks[-1]}"
            save_path = '//'.join(path_chunks) 

            im = im.astype('float32')

            #pad image to 16
            sz = im.shape
            pad_with = np.ceil(np.array(sz)/16)*16 - sz
            pad_with = pad_with.astype('int')
            im = np.pad(im, pad_width=((0,pad_with[0]),(0,pad_with[1])),mode='constant')

            dtype = torch.FloatTensor
            im = torch.from_numpy(im).unsqueeze(0).unsqueeze(0).type(dtype)
            im = (im - torch.mean(im)) / torch.std(im)

            net.eval()
            im = im.cuda()
            pred = net(im)

            pred = torch.sigmoid(pred)
            pred = pred.to('cpu').detach().numpy().squeeze(0).squeeze(0)
            pred = pred[0:sz[0], 0:sz[1]]
            thresh = 0.5
            pred = pred > thresh
            pred = morphology.remove_small_objects(pred,100)
            pred_labels = measure.label(pred).astype('uint16')
            io.imsave(save_path,pred_labels,compress=6,check_contrast=False)
            
    def _runAcq(self):
        #here acquisition needs to be stopped by adding 'None' to event_queue 
        acq = Acquisition(image_process_fn = self._image_process_fn, post_hardware_hook_fn = self._post_hardware_hook)
        acq.acquire(self.events[0])

    def _run(self):
        
        p = Process(target=self._runAcq, args=())
        p.start()

        p2 = Process(target=self.segment_realTime, args=())
        p2.start()

        #open GUI showing progress and adding aborting functionality        
        total_time = max([t['min_start_time'] for t in self.events])
        self.acquisitionDialog = acquisitionDialog.acquisitionDialog(total_time = total_time)
        self.acquisitionDialog.abort_acq.connect(self.abort_acquisition)

def main():
    acq = run_acquisition()
    acq._run()

if __name__ == '__main__':
    main()