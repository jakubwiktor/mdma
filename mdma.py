from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QTableWidgetItem,QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice


import sys
import add_configuration
from pycromanager import Bridge

def add_configuration_call(parent):
    # config_app = QtWidgets.QDialog()
    window_conf = add_configuration.add_configuration() 
    # window_conf.show()

class mdma(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(mdma, self).__init__(parent)
                
        loader = QUiLoader()
        self.ui = loader.load("mdma.ui") #if there is no ('mdma.ui', self) then it works with subwindows
        
        self.ui.show()
        self.ui.bridge = Bridge()
        self.ui.core = self.ui.bridge.get_core()
        self.ui.studio = self.ui.bridge.get_studio()
                
        self.ui.configurations = []
        self.ui.pushButton_addConfiguration.clicked.connect(self.add_configuration_call)
        self.ui.pushButton_deleteConfiguration.clicked.connect(self.delete_configuration)
        self.ui.pushButton_clearConfiguration.clicked.connect(self.clear_configuration)
        self.ui.pushButton_load.clicked.connect(self.load_settings)
        self.ui.pushButton_preview.clicked.connect(self.preview)
        self.ui.pushButton_run.clicked.connect(self.RUN)
        self.ui.pushButton_save.clicked.connect(self.save_setting)

    #here we call add_cofiguration window and add a binding to 'ADD' button
    def add_configuration_call(self):
        self.conf_window = add_configuration.add_configuration()
        self.conf_window.ui.pushButton_addConfiguration.clicked.connect(self.push_configuration_to_main)

    #here we define 'ADD' button response, it reads the parameters of the conf. window
    def push_configuration_to_main(self):
        #get a configuration window and grab a configuration 

        #TODO - think how to pass the configurations. It only makes sense to construct the events 
        # as the very last step once the folders are knbown and all channels are added.
        
        #there must be a smarter way to do this, right?
        self.ui.config_parameters = self.conf_window.ui.result #result from configuraton window 
        
        #check if all parameters are filled
        if len(self.ui.config_parameters['channels']) == 0 or len(self.ui.config_parameters['positions']) == 0 or len(self.ui.config_parameters['frames']) == 0:
            return
       
        out = []
        out.append([x['Preset'] for x in self.ui.config_parameters['channels']]) #chans
        out.append([list(x.keys())[0] for x in self.ui.config_parameters['positions']]) #pos
        out.append(len(self.ui.config_parameters['frames'])) #num of frames

        out_string = f"{out[0]}, {out[1]}, num. frames: {out[2]}"
        self.ui.listWidget_configs.addItem(out_string)

    def delete_configuration(self):
        print('delete')
    

    def clear_configuration(self):
        print('clear')


    def load_settings(self):
        print('load')


    def preview(self):
        print('preview')

    def RUN(self):
        #select/create a folder to save the acquisition and run
        save_dir_name = QFileDialog.getExistingDirectory(self, "Select Directory")
        print(save_dir_name)

        #TODO: finish the running logic: make the event list and call pycromanager


    def save_setting(self):
        #select a file to save the parameters of the acquision: how to store them? 
        file_name = QFileDialog.getSaveFileName(self, "Save Config. File",
                                                "C:\\",
                                                 "configuration file, '.txt")
        #fileName = ('C:/Users/kubus/Desktop/save', "configuration file, '.mdma")
        print(file_name)


def main():
    # configs = get_configs(core) #dictionary to store the MM configurations
    app = QtWidgets.QApplication(sys.argv)
    window = mdma() 
    sys.exit(app.exec())
 
if __name__ == '__main__':
    main()