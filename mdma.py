from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QTableWidgetItem,QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, Signal, Slot

import copy

import sys
import os
from pycromanager import Bridge

import add_configuration
from utils import acquisition

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
        self.initalProgram = [{'channels': [{'Group': 'Channel', 'preset': 'DAPI', 'Exposure': '10'}], 'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]}, 
                              {'channels': [{'Group': 'Channel', 'preset': 'Cy5', 'Exposure': '10'}],  'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]}, 
                              {'channels': [{'Group': 'Channel', 'preset': 'FITC', 'Exposure': '10'}], 'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30]}]
        self.ui.configurations = self.initalProgram
        #populate the list
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(self.print_configuration(conf))  

        #initialise buttons connections
        self.ui.pushButton_addConfiguration.clicked.connect(self.add_configuration_call)
        self.ui.pushButton_editConfiguration.clicked.connect(self.edit_configuration_call)
        self.ui.listWidget_configs.itemDoubleClicked.connect(self.edit_configuration_call)
        self.ui.listWidget_configs.installEventFilter(self)

        self.ui.pushButton_deleteConfiguration.clicked.connect(self.delete_configuration)
        self.ui.pushButton_clearConfiguration.clicked.connect(self.clear_configuration)
        self.ui.pushButton_load.clicked.connect(self.load_settings)
        self.ui.pushButton_preview.clicked.connect(self.preview)
        self.ui.pushButton_run.clicked.connect(self.RUN)
        self.ui.pushButton_save.clicked.connect(self.save_setting)
        self.ui.pushButton_updatePositions.clicked.connect(self.update_positions)
        self.ui.pushButton_changePositions.clicked.connect(self.change_positions)
        
    def add_configuration_call(self):
        #open a configuration window and grab the signal, put in into the imaging configuration list
        self.conf_window = add_configuration.add_configuration(bridge = self.ui.bridge)
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
        self.ui.listWidget_configs.addItem(self.print_configuration(message))
        self.ui.configurations.append(copy.deepcopy(message)) # i dont know how to avoid deepcopy!

    @QtCore.Slot(dict)
    def edit_configuration(self, message):
        #here we get the signal emited by 'add' button of the add_configuration gui in the EDITING mode
        self.ui.configurations[self.ui.selected_preset] = copy.deepcopy(message)
        #repring the list
        self.ui.listWidget_configs.clear()
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(self.print_configuration(conf))

    def print_configuration(self,single_configuration):
        #TODO - handle case when many channels are selected (spell the channels?
        # [x['preset'] for x in conf['channels']])?
        nchans = ', '.join([x['preset'] for x in single_configuration['channels']])
        npos = len(single_configuration['positions'])
        nframes = len(single_configuration['frames'])

        return f"channels: {nchans} , positions: {npos} , frames: {nframes}"

    def delete_configuration(self):
        #delete highlighted preset
        selected_preset = self.ui.listWidget_configs.currentRow()
        if  selected_preset == -1:
            return
        del self.ui.configurations[selected_preset]
        self.ui.listWidget_configs.clear()
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(self.print_configuration(conf))

    def clear_configuration(self):
        #clear ALL configuratins
        #TODO open dialog window to ask if you really want to clear all configuratins
        self.ui.configurations = []
        self.ui.listWidget_configs.clear()

    def preview(self):
        #preview the events in a new window
        self.ui.preview_list = QtWidgets.QListWidget()
        self.ui.preview_list.resize(640, 480)
        self.ui.preview_list.setWindowTitle('Preview')

        #TODO write it in some decent format - position - channel - time > maybe best in a table?
        for fnum, ev in enumerate(self.compile_experiment()):
            self.ui.preview_list.addItem(f"{fnum}, position: {ev['pos_label']} , channel: {ev['channel']['config']} , time: {ev['min_start_time']}s")

        self.ui.preview_list.show()

    def RUN(self):

        #TODO - !!! break the acquisiton when the window is closed !!!

        #select/create a folder to save the acquisition and run
        save_dir_name = QFileDialog.getExistingDirectory(self, "Select Directory")

        #if cancel was pressed
        if save_dir_name == '': 
            return

        run_events = self.compile_experiment(save_root=save_dir_name)

        #get dirs name and create folders at desired location
        # save_paths = [os.path.dirname(x['save_location']) for x in run_events]
        # save_paths = list(set(save_paths))
        # for savedir in save_paths:
        #     os.makedirs(savedir)
        
        self.ui.acq = acquisition.RunAcquisition(events = run_events)
        self.ui.acq._run()

        #start the acquisition
        
    def update_positions(self):
        #I guess loop through every position in the self.configurations and change the x,y,.. to what is new,
        #First check if the positions match, otherwise bail out!
        pass

    def change_positions(self):
        #easier than update - just grab the lost of positions and then change the self.configurations to the new positions
        pass

    def save_setting(self):
        #select a file to save the parameters of the acquision: how to store them? 
        file_name = QFileDialog.getSaveFileName(self, "Save Config. File",
                                                "C:\Documents\\",
                                                 "configuration file, '.txt")

        if file_name[0] == '': #if cancel was pressed
            return
        
        #TODO finish this part
        pass

    def load_settings(self):
        #figure out first how to store the configurations
        print('load')

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
        # 'exposure: seconds,
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
        counter = 0
        for config in self.ui.configurations:
            for time_counter, time_value in enumerate(config['frames']):
                for position_index, position in enumerate(config['positions']):
                    for channel in config['channels']:
                        
                        save_path = f"{save_root}/{position['Position Label']}/{channel['preset']}/img_{time_counter:09d}.tiff"
                        
                        event = {'axes':{'position': position_index},
                                'channel': {'group': channel['Group'], 'config': channel['preset']},
                                'exposure': int(channel['Exposure']),
                                'z': position['Z'],
                                'min_start_time': time_value,
                                'x': position['X'],
                                'y': position['Y'],
                                'pos_label': position['Position Label'],
                                'save_location': save_path
                                }
                        
                        counter += 1
                        
                        events.append(event)

        sorted_events = sorted(events, key = lambda i: (i['min_start_time'], i['axes']['position'])) #imgetter wont work because position sits withing dictinary 'axes'

        for ie, _ in enumerate(sorted_events):
            sorted_events[ie]['axes']['counter'] = ie

        return(sorted_events)

    def eventFilter(self,source,event):
        
        #check if over a preset - how to add action to click on menu?

        if event.type() == QtCore.QEvent.Type.ContextMenu:
            if source.itemAt(event.pos()) is not None:
                menu = QtWidgets.QMenu()
                menu.addAction(QtGui.QAction("edit",   self, triggered=self.edit_configuration_call))
                menu.addAction(QtGui.QAction("remove", self, triggered=self.delete_configuration))
                menu.exec(event.globalPos())
                
                # item = source.itemAt(event.pos())
                # print(item.text()) - acces the item in qlistwidget
                return True

        return super().eventFilter(source,event) #i dont know what this does? return False could work too

    def editThis(self):
        print('edit')
    
    def deleteThis(self):
        print('edit')

def main():
    # configs = get_configs(core) #dictionary to store the MM configurations
    app = QtWidgets.QApplication(sys.argv)
    window = mdma() 
    sys.exit(app.exec())
 
if __name__ == '__main__':
    main()