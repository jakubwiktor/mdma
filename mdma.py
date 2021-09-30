from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QTableWidgetItem,QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, Signal, Slot

import copy

import sys
import os
from pycromanager import Bridge
import json

import add_configuration

import acquisitionDialog
from utils import acquisition, rt_acquisition, get_positions

#needed packages: conda/pip
#pip install opencv-python
#pip install pycromanager
#pip install PySide6
#pip install scikit-image
#pytorch

#TODO - add functionality to change / update the positions only for selected channel - change: QListWidget_configs -> selectionMode -> extendedSelection

class mdma(QtWidgets.QMainWindow):
    """
    Main GUI for the mdma app.

    """
    def __init__(self, parent=None):
        super(mdma, self).__init__(parent)
                
        loader = QUiLoader()
        self.ui = loader.load("mdma.ui") #if there is no ('mdma.ui', self) then it works with subwindows
        
        self.ui.show()

        self.ui.bridge = Bridge()
        self.ui.core = self.ui.bridge.get_core()
        self.ui.mm_studio = self.ui.bridge.get_studio()

        #preload a config for development
        self.ui.selected_preset = -1
        self.ui.configurations = []
        self.ui.neural_net_configuration = ''

        #for development purposes
        # self.initalProgram  = OVERWRITE
        # self.ui.configurations = self.initalProgram
        
        #populate the list
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(self.print_configuration(conf))  

        #initialise buttons connections
        self.ui.pushButton_addConfiguration.clicked.connect(self.add_configuration_call)
        # self.ui.pushButton_editConfiguration.clicked.connect(self.edit_configuration_call)
        self.ui.listWidget_configs.itemDoubleClicked.connect(self.edit_configuration_call)
        self.ui.listWidget_configs.installEventFilter(self)

        # self.ui.pushButton_deleteConfiguration.clicked.connect(self.delete_configuration)
        self.ui.pushButton_clearConfiguration.clicked.connect(self.clear_configuration)
        self.ui.pushButton_load.clicked.connect(self.load_settings)
        self.ui.pushButton_preview.clicked.connect(self.preview)
        self.ui.pushButton_run.clicked.connect(self.RUN)
        self.ui.pushButton_save.clicked.connect(self.save_setting)
        self.ui.pushButton_updatePositions.clicked.connect(self.update_positions)
        self.ui.pushButton_changePositions.clicked.connect(self.change_positions)

    def add_configuration_call(self):
        #open a configuration window and grab the signal, put in into the imaging configuration list
        self.conf_window = add_configuration.add_configuration()
        #connect to the slot
        self.conf_window.config_to_emit.connect(self.send_configuration)

    def edit_configuration_call(self):
        #edit selected preset
        self.ui.selected_preset = self.ui.listWidget_configs.currentRow() #store which preset was selected - otherwise the it could be changed by accident
        if  self.ui.selected_preset == -1:
            return
        self.conf_window = add_configuration.add_configuration(preset=self.ui.configurations[self.ui.selected_preset], window_mode='EDIT') #open in editing mode
        self.conf_window.config_to_emit.connect(self.edit_configuration)

    @QtCore.Slot(dict)
    def send_configuration(self, message):
        #here we get the signal emited by 'add' button of the add_configuration gui
        self.ui.listWidget_configs.addItem(self.print_configuration(message))
        self.ui.configurations.append(copy.deepcopy(message)) # i dont know how to avoid deepcopy!

        #add the model to remember
        if len(message['naural_net_path']) > 0:
            self.ui.neural_net_configuration = message['naural_net_path']

    @QtCore.Slot(dict)
    def edit_configuration(self, message):
        #here we get the signal emited by 'add' button of the add_configuration gui in the EDITING mode
        self.ui.configurations[self.ui.selected_preset] = copy.deepcopy(message)
        #repring the list
        self.ui.listWidget_configs.clear()
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(self.print_configuration(conf))

        #eventually change the model path
        if len(message['naural_net_path']) > 0:
            self.ui.neural_net_configuration = message['naural_net_path']

    def print_configuration(self,single_configuration):
        #TODO - handle case when many channels are selected (spell the channels?
        # [x['Preset'] for x in conf['channels']])?
        nchans = ', '.join([x['Preset'] for x in single_configuration['channels']])
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

    def duplicate_configuration(self):
        selected_preset = self.ui.listWidget_configs.currentRow()
        if  selected_preset == -1:
            return
        self.ui.configurations.append(copy.deepcopy(self.ui.configurations[selected_preset]))
        self.ui.listWidget_configs.addItem(self.print_configuration(self.ui.configurations[selected_preset]))

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
            self.ui.preview_list.addItem(f"time: {ev['min_start_time']}s, position: {ev['pos_label']} , channel: {ev['channel']['config']}, segmentation: {ev['segmentation']['do']}, No: {fnum}")
        
        self.ui.preview_list.show()

    def RUN(self):
        #TODO - !!! break the acquisiton when the window is closed !!!
        #TODO - open a progress window

        #select/create a folder to save the acquisition and run
        save_dir_name = QFileDialog.getExistingDirectory(self, "Select Directory")
         
        #overwrite for easier testing
        # save_dir_name = 'C:/Users/kubus/Documents/test'

        #if cancel was pressed
        if save_dir_name == '': 
            return

        run_events = self.compile_experiment(save_root=save_dir_name)
        #get dirs name and create folders at desired location
        save_paths = [os.path.dirname(x['save_location']) for x in run_events]
        save_paths = list(set(save_paths))
        
        #add segmentation folder - this is hack-fix
        seg_flag = False
        for ev in run_events:
            if ev['segmentation']['do'] == 1:
                seg_flag = True
                which_channel = ev['save_location'].split('/')[-2]
                break

        if seg_flag:
            for p in save_paths:
                if p.split('/')[-1] == which_channel:
                    save_paths.append(p.replace(which_channel,f"{which_channel}_segmented"))
            
        for savedir in save_paths:
            #if the directory already exitsts start overwriting it
            if not(os.path.exists(savedir)):
                os.makedirs(savedir)

        #TODO - check and delete medatata textfile if it exists - maye better way is to create an empty file and then add line at desired index?
        metadata_location = f"{save_dir_name}/metadata.txt"
        if os.path.isfile(metadata_location):
            os.remove(metadata_location)
            print('deleting metadata')

        # self.ui.acq = acquisition.run_acquisition(events = run_events, save_path = save_dir_name)
        self.ui.acq = rt_acquisition.run_acquisition(events = run_events, save_path = save_dir_name, model_path = self.ui.neural_net_configuration)
        self.ui.acq._run()

    def update_positions(self):
        #loop the configurations and check match the position in the current positions in micromanager
        #if the position exists in configuration and micromanager, change the configuration to the 
        #position in micromanager. 
        #TODO - is this safe, what if some positions are removed in settings before acquisition?
        positions = get_positions.get_positions(mm_studio=self.ui.mm_studio)

        for conf in self.ui.configurations:
            for i, this_pos in enumerate(conf['positions']):
                #find if 'this_pos' exists in 'positions'
                for that_pos in positions:
                    if this_pos['Position Label'] == that_pos['Position Label']:
                        conf['positions'][i] = that_pos

        # self.ui.listWidget_configs.addItem(self.print_configuration(conf)) 
        #loop the channels and match the positions and update when necessary

    def change_positions(self):
        #get the list of positions and then change the self.configurations to the new positions, retype the listWidget
        #!IMPORTANT - this will change all positions to the current position list in micromanager, complicated position arrangements may be loast
        #TODO - maybe its better to change/update the positision only for selected configuration
        
        self.ui.listWidget_configs.clear()
        positions = get_positions.get_positions(mm_studio=self.ui.mm_studio)
        for conf in self.ui.configurations:
            conf['positions'] = positions
            self.ui.listWidget_configs.addItem(self.print_configuration(conf)) 
        
        self.print_configuration(conf)

    def save_setting(self):
        #select a file to save the parameters of the acquision: how to store them? 
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Config. File",
                                                      "C:\Documents\\",
                                                      "configuration file, '.txt")

        if file_name[0] == '': #if cancel was pressed
            return
        
        file_name = file_name+'.txt'
        with open(file_name, 'w') as f:
            for conf in self.ui.configurations:
                f.write(json.dumps(conf, separators =(',',':')))
                f.write('\n')
        
    def load_settings(self):
        #load saved configuration from txt file - json file
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(parent=self, 
                                                            caption='select model',
                                                            filter = "*.txt")
        
        with open(fileName) as f:
            #TODO - check if the configuration is in correct format - improve this section
            for l in f:
                #check if the configuration contains  necessary fields
                try:
                    test_cast = json.loads(l)
                    test_cast['channels']
                except:
                    print('incorrect configuration file')
                    return
                # l['Segmentation']
                # l['positions']
                # l['frames']

        with open(fileName) as f:
            self.ui.configurations =  [json.loads(l) for l in f]
        
        self.ui.listWidget_configs.clear()
        for conf in self.ui.configurations:
            self.ui.listWidget_configs.addItem(self.print_configuration(conf)) 
    
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
        for config in self.ui.configurations:
            for time_counter, time_value in enumerate(config['frames']):
                for position_index, position in enumerate(config['positions']):
                    for channel in config['channels']:
                        
                        save_path = f"{save_root}/{position['Position Label']}/{channel['Preset']}/img_{time_counter:09d}.tiff"
                        pnumber = int(''.join(filter(str.isdigit, position['Position Label']))) # cuts the 'Pos' part of 'PosXXX' naming and uses only integer for sorting

                        event = {'axes':{'position': pnumber},
                                'channel': {'group': channel['Group'], 'config': channel['Preset']},
                                'segmentation':{'do':channel['Segmentation']['Do'], 'save_frames':channel['Segmentation']['Save_frames']},
                                'exposure': int(channel['Exposure']),
                                'z': position['Z'],
                                'min_start_time': time_value,
                                'x': position['X'],
                                'y': position['Y'],
                                'pos_label': position['Position Label'],
                                'save_location': save_path
                                }
                        
                        events.append(event)

        sorted_events = sorted(events, key = lambda i: (i['min_start_time'], i['axes']['position'])) #wont work because position sits withing dictinary 'axes'
        
        return sorted_events

    def eventFilter(self,source,event):
        #filetring events, i can catch the closing event here too
        #check if over a preset - how to add action to click on menu?
        if event.type() == QtCore.QEvent.Type.ContextMenu:
            if source.itemAt(event.pos()) is not None:
                menu = QtWidgets.QMenu()
                menu.addAction(QtGui.QAction("Edit",   self, triggered=self.edit_configuration_call))
                menu.addAction(QtGui.QAction("Delete", self, triggered=self.delete_configuration))
                menu.addAction(QtGui.QAction("Duplicate", self, triggered=self.duplicate_configuration))
                
                menu.exec(event.globalPos())
                
                return True

        return super().eventFilter(source,event) #i dont know what this does? return False could work too

def main():
    # configs = get_configs(core) #dictionary to store the MM configurations
    app = QtWidgets.QApplication(sys.argv)
    window = mdma() 
    sys.exit(app.exec())
 
if __name__ == '__main__':
    main()