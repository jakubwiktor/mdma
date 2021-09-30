from time import process_time
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtUiTools import QUiLoader

import sys

class select_model(QtWidgets.QDialog):
    """
    GUI to specify the trained neural netowrk model to be used for segmentation. Called by add_configuration.py
    input
        preset

        timelapse 
        
        row
        
        model_path

    out
       dictionary - {'preset':self.preset,'model_path':self.model_path, 'row':self.row}
    
    """
    send_model = QtCore.Signal(dict)

    def __init__(self, parent=None, preset=None, timelapse=None, row=None, model_path=''):
        super(select_model, self).__init__(parent)

        loader = QUiLoader()
        self.ui = loader.load("select_model.ui") #if there is no ('mdma.ui', self) then it works with subwindows

        self.ui.show()

        self.model_path = model_path
        self.skip_frames = 1 #save every frame by default
        self.preset = preset
        self.timelapse = timelapse
        self.row = row

        if len(self.model_path) == 0:
            self.ui.textBrowser_modelPath.setText('Select model.')
        else:
            self.ui.textBrowser_modelPath.setText(self.model_path)

        self.ui.textBrowser_preset.setText(f"{self.preset}, {self.timelapse}")
        self.ui.lineEdit_skipFrames.setText('1')

        self.ui.pushButton_loadModel.clicked.connect(self.load_model)
        self.ui.pushButton_confirm.clicked.connect(self.confirm_model)
        self.ui.lineEdit_skipFrames.textChanged.connect(self.change_skip_frames)

    def load_model(self):
        #browse to find the model to use and emit it to the add_configurtion gui
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(parent=self, 
                                                            caption='select model',
                                                            selectedFilter = "")
        
        self.ui.textBrowser_modelPath.setText(fileName)
        self.model_path = fileName
    
    def change_skip_frames(self,event):
        #detect user input
        self.skip_frames = event

    def confirm_model(self):
        #send model path to add_configuration gui
        #TODO - REDO THE CHANNEL CONFIGURATION HERE - save one with segmentation flag, the other with nomal channel with changed timelapse
        if self.model_path != '':
            # self.preset['Segmentation'] = dict()
            self.preset['Segmentation']['Do'] = 1
            self.preset['Segmentation']['Save_frames'] = self.skip_frames
            self.send_model.emit({'preset':self.preset,'model_path':self.model_path, 'row':self.row})
            self.ui.close()

def main():
    # configs = get_configs(core) #dictionary to store the MM configurations
    app = QtWidgets.QApplication(sys.argv)
    window = select_model() 
    sys.exit(app.exec())
 
if __name__ == '__main__':
    main()