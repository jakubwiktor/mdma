from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QTableWidgetItem,QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, Signal, Slot

import copy

import sys
import add_configuration
from pycromanager import Bridge

class mdma(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(mdma, self).__init__(parent)
                
        loader = QUiLoader()
        self.ui = loader.load("mdma.ui") #if there is no ('mdma.ui', self) then it works with subwindows
        
        self.ui.show()
        self.ui.bridge = Bridge()
        self.ui.core = self.ui.bridge.get_core()
        self.ui.studio = self.ui.bridge.get_studio()
                
        #preload a config for development
        self.ui.selected_preset = -1
        self.ui.configurations = []
        self.ui.counter = 0
        self.initConf = {'channels': [{'Group': 'Camera', 'preset': 'HighRes', 'Exposure': '10'}], 'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 60, 120]}

        self.ui.pushButton_addConfiguration.clicked.connect(self.add_configuration_call)
        self.ui.pushButton_editConfiguration.clicked.connect(self.edit_configuration_call)
        self.ui.pushButton_deleteConfiguration.clicked.connect(self.delete_configuration)
        self.ui.pushButton_clearConfiguration.clicked.connect(self.clear_configuration)
        self.ui.pushButton_load.clicked.connect(self.load_settings)
        self.ui.pushButton_preview.clicked.connect(self.preview)
        self.ui.pushButton_run.clicked.connect(self.RUN)
        self.ui.pushButton_save.clicked.connect(self.save_setting)
        
    def add_configuration_call(self):
        #open a configuration window and grab the signal, put in into the imaging configuration list
        self.conf_window = add_configuration.add_configuration(preset=self.initConf)
        #connect to the slot
        self.conf_window.config_to_emit.connect(self.send_configuration)

    def edit_configuration_call(self):
        self.ui.selected_preset = self.ui.listWidget_configs.currentRow()
        if  self.ui.selected_preset == -1:
            return
        print(self.ui.configurations[self.ui.selected_preset])
        self.conf_window = add_configuration.add_configuration(preset=self.ui.configurations[self.ui.selected_preset])
        self.conf_window.config_to_emit.connect(self.edit_configuration)

    @QtCore.Slot(dict)
    def send_configuration(self, message):
        #here we get the signal emited by 'add' button of the add_configuration gui
        self.ui.listWidget_configs.addItem(str(message))
        self.ui.configurations.append(copy.deepcopy(message)) # i dont know how to avoid deepcopy!
        for ch in self.ui.configurations:
            print(ch)

    @QtCore.Slot(dict)
    def edit_configuration(self, message):
        #here we get the signal emited by 'add' button of the add_configuration gui in the EDITING mode
        self.ui.configurations[self.ui.selected_preset] = copy.deepcopy(message)
        #repring the list
        self.ui.listWidget_configs.clear()
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(str(conf))

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