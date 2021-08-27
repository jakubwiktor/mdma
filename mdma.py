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

        #for development purposes
        self.initConf = {'channels': [{'Group': 'Camera', 'preset': 'HighRes', 'Exposure': '10'}], 'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 60, 120]}
        self.initalProgram = [{'channels': [{'Group': 'Camera', 'preset': 'HighRes', 'Exposure': '10'}], 'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]}, {'channels': [{'Group': 'Camera', 'preset': 'LowRes', 'Exposure': '10'}], 'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58]}, {'channels': [{'Group': 'Camera', 'preset': 'MedRes', 'Exposure': '10'}], 'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 3, 6, 9, 12, 15, 
                            18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57]}]
        self.ui.configurations = self.initalProgram
        #populate the list
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(str(conf))  

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
        self.conf_window = add_configuration.add_configuration(preset=self.initConf, bridge = self.ui.bridge)
        #connect to the slot
        self.conf_window.config_to_emit.connect(self.send_configuration)

    def edit_configuration_call(self):
        #edit selected preset
        self.ui.selected_preset = self.ui.listWidget_configs.currentRow() #store which preset was selected - otherwise the it could be changed by accident
        if  self.ui.selected_preset == -1:
            return
        self.conf_window = add_configuration.add_configuration(preset=self.ui.configurations[self.ui.selected_preset], windowMode='edit', bridge = self.ui.bridge) #open in editing mode
        self.conf_window.config_to_emit.connect(self.edit_configuration)

    @QtCore.Slot(dict)
    def send_configuration(self, message):
        #here we get the signal emited by 'add' button of the add_configuration gui
        self.ui.listWidget_configs.addItem(str(message))
        self.ui.configurations.append(copy.deepcopy(message)) # i dont know how to avoid deepcopy!

    @QtCore.Slot(dict)
    def edit_configuration(self, message):
        #here we get the signal emited by 'add' button of the add_configuration gui in the EDITING mode
        self.ui.configurations[self.ui.selected_preset] = copy.deepcopy(message)
        #repring the list
        self.ui.listWidget_configs.clear()
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(str(conf))

    def delete_configuration(self):
        #delete highlighted preset
        selected_preset = self.ui.listWidget_configs.currentRow()
        if  selected_preset == -1:
            return
        del self.ui.configurations[selected_preset]
        self.ui.listWidget_configs.clear()
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(str(conf))

    def clear_configuration(self):
        #clear ALL configuratins
        self.ui.configurations = []
        self.ui.listWidget_configs.clear()

    def load_settings(self):
        #figure out first how to store the configurations
        print('load')

    def preview(self):
        for ev in self.compile_experiment():
            print(ev)

    def RUN(self):
        #select/create a folder to save the acquisition and run
        save_dir_name = QFileDialog.getExistingDirectory(self, "Select Directory")
        run_events = self.compile_experiment(save_root=save_dir_name)
        for ev in run_events:
            print(ev)

        #TODO: prepare the folders to put the images in, call the pycromanager logic from here.

    def save_setting(self):
        #select a file to save the parameters of the acquision: how to store them? 
        file_name = QFileDialog.getSaveFileName(self, "Save Config. File",
                                                "C:\\",
                                                 "configuration file, '.txt")
        #fileName = ('C:/Users/kubus/Desktop/save', "configuration file, '.mdma")
        print(file_name)

    def compile_experiment(self, save_root=None):
        #parse 1-
        #        time
        #           |
        #           > positions
        #                     |
        #                     > channels
        #loop over timepoints, then positionis, and then each channel
        #
        #   {
        # 'axes':{name}, 
        # 'channel': {'group':name, 'config':name},
        # 'exposure:  number,
        # 'z': number,
        # 'min_start_time': time_in_s
        # 'x': x_position_in_µm,
        #  'y': y_position_in_µm,
        # 'keep_shutter_open': False, <- what is defalut?
        # 'properties': [['DeviceName', 'PropertyName', 'PropertyValue'],
        #               ['OtherDeviceName', 'OtherPropertyName', 'OtherPropertyValue']],
        #   }

        events = []
        save_pathway = None
        for config in self.ui.configurations:
            for time_counter, time_value in enumerate(config['frames']):
                for position in config['positions']:
                    for channel in config['channels']:
                        
                        save_path = f"{save_root}/{position['Position Label']}/{channel['preset']}/img_{time_counter:09d}.tiff"
                        
                        event = {'axes':{'position': position['Position Label']},
                                'channel': {'group':channel['Group'], 'config':channel['preset']},
                                'exposure': channel['Exposure'],
                                'z':position['Z'],
                                'min_start_time':time_value,
                                'x':position['X'],
                                'y':position['Y'],
                                'save_location':save_path
                                }
                        
                        events.append(event)
        
        sorted_events = sorted(events, key = lambda i: (i['min_start_time'], i['axes']['position'])) #imgetter wont work because position sits withing dictinary 'axes'
        
        return(sorted_events)

def main():
    # configs = get_configs(core) #dictionary to store the MM configurations
    app = QtWidgets.QApplication(sys.argv)
    window = mdma() 
    sys.exit(app.exec())
 
if __name__ == '__main__':
    main()