#acquisition stuff
from pycromanager import Acquisition

class RunAcquisition:

    def __init__(self, events = None):
        self.events = events

    def _image_process_fn(self,image,metadata):
        in_num = (metadata['Axes']['counter'])
        #find back the correct frame!
        print(self.events[in_num]['save_location'], self.events[in_num]['min_start_time'])
        return image, metadata
        
    def _run(self):
        with Acquisition(image_process_fn = self._image_process_fn) as acq:
            acq.acquire(self.events)


def main():
    acq = RunAcquisition()
    acq._run()

if __name__ == '__main__':
    main()