from time import process_time
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtUiTools import QUiLoader


import sys

class select_model(QtWidgets.QDialog):
    
    send_model = QtCore.Signal(dict)

    def __init__(self, parent=None, preset = None, timelapse = None):
        super(select_model, self).__init__(parent)

        loader = QUiLoader()
        self.ui = loader.load("select_model.ui") #if there is no ('mdma.ui', self) then it works with subwindows

        self.ui.show()

        self.ui.model_path = ''
        self.ui.skip_frames = []
        self.ui.preset = preset
        self.ui.timelapse = timelapse

        self.ui.textBrowser_preset.setText(f"{self.ui.preset}, {self.ui.timelapse}")

        self.ui.pushButton_loadModel.clicked.connect(self.load_model)
        self.ui.pushButton_confirm.clicked.connect(self.confirm_model)

    def load_model(self):
        #browse to find the model to use and emit it to the add_configurtion gui
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(parent=self, 
                                                            caption='select model',
                                                            selectedFilter = "")
        
        self.ui.textBrowser_modelPath.setText(fileName)
        self.ui.model_path = fileName

    def confirm_model(self):
        #send model path to add_configuration gui
        #TODO - REDO THE CHANNEL CONFIGURATION HERE - save one with segmentation flag, the other with nomal channel with changed timelapse
        if self.ui.model_path != '':
            self.send_model.emit(self.ui.model_path)
            self.ui.close()

def main():
    # configs = get_configs(core) #dictionary to store the MM configurations
    app = QtWidgets.QApplication(sys.argv)
    window = select_model() 
    sys.exit(app.exec())
 
if __name__ == '__main__':
    main()