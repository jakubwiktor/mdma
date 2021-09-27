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
    TODO-connect segmentation and non-segmentation version together with segmentation and barcode flags
    Kuba
    """

    def __init__(self, events = None, save_path = '', q = None, model_path = ''):
        self.events = events
        self.tot_images = len(events)
        self.save_path = save_path
        self.model_path = model_path
        
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
        if self.events[im_num]['segmentation']['do']:
            
            #
            #detect barcode - if first image store the image
            #
            # TODO enclose this in a fucntion and move outside of the main code here

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
            
            barcode_save_path = self.events[im_num]['save_location'].replace(self.events[im_num]['channel']['config'],'barcode')
            
            #TODO - fix this ugly shit
            if not(os.path.exists(os.path.split(barcode_save_path)[0])):
                os.makedirs(os.path.split(barcode_save_path)[0])
            
            io.imsave(barcode_save_path, b_image, check_contrast=0)

            barcode_loc = dict()
            barcode_loc['file'] = barcode_save_path
            barcode_loc['pos'] = top_left
            
            with open(f"{self.save_path}/barcode_locations.txt", 'a') as f:
                f.write(json.dumps(barcode_loc, separators=(',',':')))
                f.write('\n')
            #
            #end of barcode testing
            #

            seg_save_path = self.events[im_num]['save_location'].replace(self.events[im_num]['channel']['config'], self.events[im_num]['channel']['config']+'_segmented')
            print(seg_save_path)

            self.q.put((image, seg_save_path))    

            #take number portion of the save file and check which image it is
            which_image = self.events[im_num]['save_location']
            which_image = int(''.join(x for x in which_image.split('/')[-1] if x.isdigit())) + 1 #plus 1 because names start from 0

            if which_image % int(self.events[im_num]['segmentation']['save_frames']) == 0: #save if mod of image and save frames is 0
                io.imsave(self.events[im_num]['save_location'], image, check_contrast=0)
                # cv.imwrite(self.events[im_num]['save_location'], image) #flag is IMWRITE_TIFF_COMPRESSION + number - refer to libtiff for integer constants for compression
        else:
            pass
            # io.imsave(self.events[im_num]['save_location'], image, check_contrast=False)
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
            # print(self.events[im_num+1])
            event_queue.put(self.events[im_num+1])
        
        # return image,metadata

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
    
    def segment_realTime(self):
        """
        
        update documentation
        
        """
        #construct real time acquisition function that checks for queue
        import torch
        from utils.UnetPlusPlus2 import UNet
        import numpy as np
        from skimage import io, measure, morphology

        net = UNet(num_classes=1)
        # saved_model = 'F:\\Jakub\\mdma-main\\Unet_mixed_brightnessAdj_Adam_HybridLoss_512px_cellsUnweighted.pth' #01.06.2021
        # saved_model = 'C:\\Users\\kubus\\Documents\\trained_models\\Unet_mixed_brightnessAdj_Adam_HybridLoss_512px_cellsUnweighted.pth' #01.06.2021
        
        #load specified model
        saved_model = self.model_path

        try:
            saved_net = torch.load(saved_model)
        except OSError as e:
            print(e)
            return

        net.load_state_dict(saved_net['model_state_dict'])

        net.cuda()

        while True:
            #segmentation core
            im, save_path = self.q.get()
            
            if im is None: #'poision pill'
                self.check_segmentation_completed.value = True
                print('segmentation completed')
                break

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
            io.imsave(save_path,pred_labels,compress=6,check_contrast=0)
            # cv.imwrite(save_path,pred_labels)

    def _runAcq(self):
        #here acquisition needs to be stopped by adding 'None' to event_queue 
        acq = Acquisition(image_process_fn = self._image_process_fn, post_hardware_hook_fn = self._post_hardware_hook)
        acq.acquire(self.events[0])

    def _run(self):
        p1 = Process(target=self._runAcq, args=())
        p1.start()

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