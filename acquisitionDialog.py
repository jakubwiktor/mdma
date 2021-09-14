from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtUiTools import QUiLoader

import sys
import time
import math

class acquisitionDialog(QtWidgets.QMainWindow):

    abort_acq = QtCore.Signal(bool)

    def __init__(self, parent=None,  total_time=40):
        super(acquisitionDialog, self).__init__(parent)
                
        loader = QUiLoader()
        self.ui = loader.load("acquisitionDialog.ui") #if there is no ('mdma.ui', self) then it works with subwindows
        self.ui.show()

        self.ui.total_time = total_time
        self.ui.worker = Worker(total_time=self.ui.total_time)
        self.ui.worker.updateProgress.connect(self.setProgress)
        self.ui.worker.start()

        self.ui.pushButton_abort.clicked.connect(self.close_abort)
        # self.ui.pushButton_abort.clicked.connect(self.closeEvent)

        self.ui.time_counter = 0

        #set time labels
        self.ui.total_time = total_time
        ty_res = time.gmtime(total_time)
        total_time_hms = time.strftime("%H:%M:%S",ty_res)

        self.ui.label_time_expected.setText(total_time_hms)

        #method within the gui - problem is that when it sleeps it blocks the window - grab the progress from somewhere?
        # for i in range(0, self.ui.total_time+1):
        #     time_element = (100/self.ui.total_time)*i
        #     self.ui.progressBar.setValue(time_element)
        #     ty_res = time.gmtime(self.ui.time_counter)
        #     total_time_hms = time.strftime("%H:%M:%S",ty_res)
        #     self.ui.label_time_passed.setText(total_time_hms)
        #     self.ui.time_counter += 1
        #     QtCore.QCoreApplication.processEvents()
        #     time.sleep(1)

    def setProgress(self, progress):
        self.ui.progressBar.setValue(progress)
        
        #update label
        ty_res = time.gmtime(self.ui.time_counter)
        total_time_hms = time.strftime("%H:%M:%S",ty_res)
        self.ui.label_time_passed.setText(total_time_hms)
        self.ui.time_counter += 1

    def close_abort(self):
        self.abort_acq.emit(True)
        self.ui.close()
        # bridge = Bridge()
        # bridge.close()
    
    # def closeEvent(self):
    #     self.abort_acq.emit(1)
        

class Worker(QtCore.QThread):

    #This is the signal that will be emitted during the processing.
    #By including int as an argument, it lets the signal know to expect
    #an integer argument when emitting.
    updateProgress = QtCore.Signal(int)

    #You can do any extra things in this init you need, but for this example
    #nothing else needs to be done expect call the super's init
    def __init__(self, total_time=60):
        QtCore.QThread.__init__(self)
        total_time = math.ceil(total_time) #<- prepare in case of fraction seconds
        self.total_time = total_time
        self.update_time = total_time/101
    
    #A QThread is run by calling it's start() function, which calls this run()
    #function in it's own "thread". 
    def run(self):
        # print(self.total_time)
        
        #Notice this is the same thing you were doing in your progress() function
        for i in range(0, self.total_time+1):
            #Emit the signal so it can be received on the UI side.
            time_element = (100/self.total_time)*i
            self.updateProgress.emit(time_element)
            time.sleep(1)

def main():

    app = QtWidgets.QApplication(sys.argv)
    window = acquisitionDialog() 
    app.exec()

if __name__ == '__main__':
    main()