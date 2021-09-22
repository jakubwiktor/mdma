from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtUiTools import QUiLoader

import sys
import time
import math

class acquisitionDialog(QtWidgets.QMainWindow):

    abort_acq = QtCore.Signal(bool)

    def __init__(self, parent=None,  total_time=15):
        super(acquisitionDialog, self).__init__(parent)
                
        loader = QUiLoader()
        self.ui = loader.load("acquisitionDialog.ui") #if there is no ('mdma.ui', self) then it works with subwindows
        self.ui.show()

        self.ui.total_time = total_time
        # self.ui.worker = Worker(total_time=self.ui.total_time)
        # self.ui.worker.updateProgress.connect(self.setProgress)
        # self.ui.worker.time_finished.connect(self.closeGUI)
        # self.ui.worker.start()

        self.timer = QtCore.QTimer(self.ui)
        self.timer.timeout.connect(self.setProgress)
        self.timer.start(1000)

        self.ui.pushButton_abort.clicked.connect(self.close_abort)

        self.ui.time_counter = 1

        #set time labels
        self.ui.total_time = total_time
        ty_res = time.gmtime(total_time)
        total_time_hms = time.strftime("%H:%M:%S",ty_res)

        self.ui.label_time_expected.setText(total_time_hms)

    def setProgress(self):
        ty_res = time.gmtime(self.ui.time_counter)
        total_time_hms = time.strftime("%H:%M:%S",ty_res)
        self.ui.label_time_passed.setText(total_time_hms)
        
        #Emit the signal so it can be received on the UI side.
        time_element = (100/self.ui.total_time)*self.ui.time_counter
        self.ui.progressBar.setValue(time_element)

        self.ui.time_counter += 1

        if self.ui.time_counter == self.ui.total_time+1:
                self.timer.stop()

    def closeGUI(self, signal):
        if signal:
            self.ui.close()

    def close_abort(self):
        self.abort_acq.emit(True)
        self.ui.close()

def main():

    app = QtWidgets.QApplication(sys.argv)
    window = acquisitionDialog() 
    app.exec()

if __name__ == '__main__':
    main()