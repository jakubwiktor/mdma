from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QApplication, QTableWidgetItem, QDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, Signal, Slot


import sys
# import add_configuration

from pycromanager import Bridge
import math
import time

#TODO read the exposure form the preset and set it: current_exposure = self.ui.lineEdit_setExposure.text()
#TODO find out a way to pass the core property from mdma.py main window, so it wont open connections each time window is called

#TODO - add function to update/change the positions of all existing presets - may be tricky, may be easy

class add_configuration(QtWidgets.QDialog):
    
    config_to_emit = QtCore.Signal(dict)

    def __init__(self, parent=None, preset=None, windowMode = 'ADD'):
        super(add_configuration, self).__init__(parent)

        # uic.loadUi("add_configuration.ui", self)
        # self.ui.show()

        loader = QUiLoader()
        self.ui = loader.load("add_configuration.ui")
        self.ui.show()

        self.ui.bridge = Bridge()
        self.ui.core =  self.ui.bridge.get_core()
        self.ui.mm_studio = self.ui.bridge.get_studio()
        self.ui.configs = self.get_configs()

        self.ui.result = []

        #enable loading and editing the presets
        if preset is not None:
            
            #here the channel configurations are stored
            self.ui.frames = preset['frames']
            self.ui.positions = preset['positions']
            self.ui.channels = preset['channels']
            
            #TODO - change to handle the table
            for ch in self.ui.channels:
                print(ch)
                # out_string = f"{ch['Group']}, {ch['preset']}, {ch['Exposure']} ms"
                # self.ui.listWidget_channels.addItem(out_string)
            
            for ch in self.ui.positions:
                self.ui.listWidget_positionList.addItem(str(ch))
            self.ui.label_info_pos_val.setText(str(len(self.ui.positions)))    

            for frame_number, frame in enumerate(self.ui.frames):
                ty_res = time.gmtime(frame)
                res = time.strftime("%H:%M:%S",ty_res)
                self.ui.listWidget_timePoints.addItem(f"f: {frame_number}, t: {res}")   
            self.ui.label_info_frames_val.setText(str(len(self.ui.frames)))
            ty_res = time.gmtime(self.ui.frames[-1])
            total_time_hms = time.strftime("%H:%M:%S",ty_res)
            self.ui.label_info_duration_val.setText(total_time_hms)
        else:
            self.ui.frames = []
            self.ui.positions = []
            self.ui.channels = []

        #initialise channel selection boxes
        for c in self.ui.configs: #GROUP
            self.ui.comboBox_selectGroup.addItem(c)

        #initialise tableWidge_channels coumn names
        for _ in range(3):
            self.ui.tableWidget_channels.insertColumn(_)
        #fill columns headers
        self.ui.tableWidget_channels.setHorizontalHeaderLabels(['Group','Preset','Exposure'])
        #stretch to fill
        header = self.ui.tableWidget_channels.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.ui.tableWidget_channels.verticalHeader().setDefaultSectionSize(10)
        #set custom context menu for channel table
        self.ui.tableWidget_channels.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) 
        # self.ui.tableWidget_channels.horizontalHeader().setStretchLastSection(True) 

        #positions
        self.ui.pushButton_addPos.clicked.connect(self.add_positions_list)
        self.ui.pushButton_clearPos.clicked.connect(self.clear_position_list)
        self.ui.pushButton_removePos.clicked.connect(self.remove_position_from_list)
        #timelapse
        self.ui.pushButton_addTime.clicked.connect(self.add_timelapse)
        self.ui.pushButton_clearTime.clicked.connect(self.clear_timelapse)
        self.ui.pushButton_removeTime.clicked.connect(self.remove_timepoint_from_list)

        #channels
        # self.ui.comboBox_selectGroup.currentIndexChanged.connect(self.change_group_config)
        self.ui.pushButton_addPreset.clicked.connect(self.add_channel_preset)
        self.ui.pushButton_removePreset.clicked.connect(self.remove_channel_preset)
        
        #connect listWIdget to clicking behaviour
        # self.ui.tableWidget_channels.doubleClicked.connect(self.detect_click_table)

        #closing behaviour
        self.ui.pushButton_addConfiguration.clicked.connect(self.emit_configuration)
        self.ui.pushButton_cancelConfiguration.clicked.connect(self.cancel_configuration_do_nothing)

        # modify the 'ADD' button to 'add' and 'edit' mode
        if windowMode == 'edit':
            self.ui.pushButton_addConfiguration.setText('Edit')

        # eventualy change to table widget
        # self.ui.tableWidget_channels.setColumnCount(3)
        # self.ui.tableWidget_channels.setHorizontalHeaderLabels(['Group','preset','Exposure'])
        # self.ui.tableWidget_channels.itemDoubleClicked.connect(self.update_channel_table)
       
    #channel callbacks

    def add_channel_preset(self):
        #tableWidge_channels callbacks - working with comboBoxes

        n = self.ui.tableWidget_channels.rowCount()
        self.ui.tableWidget_channels.setRowCount(n + 1)
       
        #to populate comboboxes
        first_config_name = list(self.ui.configs.keys())[0]

        cb_group = QtWidgets.QComboBox()
        for _ in list(self.ui.configs.keys()):
            cb_group.addItem(_)    
        self.ui.tableWidget_channels.setCellWidget(n,0,cb_group)
        #add calback after creation not to invoke the callback on creation
        cb_group.currentIndexChanged.connect(self.change_group_combobox)
        
        
        cb_preset = QtWidgets.QComboBox()
        for _ in self.ui.configs[first_config_name]:
            cb_preset.addItem(_)
        self.ui.tableWidget_channels.setCellWidget(n,1,cb_preset)
        cb_preset.currentIndexChanged.connect(self.change_preset_combobox)

        # exposure_item = QTableWidgetItem()
        # self.ui.tableWidget_channels.setItem(n,2,exposure_item)
        # exposure_item.setText('100')

        exposure_widget = QtWidgets.QLineEdit()
        exposure_widget.textChanged.connect(self.change_preset_exposure)
        exposure_widget.setText('100')
        self.ui.tableWidget_channels.setCellWidget(n,2,exposure_widget)

        #update channel list
        self.ui.channels.append({'Group':first_config_name, 
                                 'Preset':self.ui.configs[first_config_name][0], 
                                 'Exposure': 100})

    def change_group_combobox(self,event):
        #detect the change in the *channel* combo box and update the channels
        #event -> is the index of the combo box

        combo_box_index = event

        this_row = self.ui.tableWidget_channels.currentRow()
        
        #this is reference to the combo box
        this_item = self.ui.tableWidget_channels.cellWidget(this_row,0)

        #check if there is already a channel added
        if this_item is None:
            return

        #update the stored channel in preset, update the cb_preset
        selected_config_gruop = this_item.itemText(combo_box_index)
        
        #check if any change was actually made to the selection
        if selected_config_gruop == self.ui.channels[this_row]['Group']:
            return

        self.ui.tableWidget_channels.cellWidget(this_row,1).setCurrentIndex(0)

        cb_preset = QtWidgets.QComboBox()
        for _ in self.ui.configs[selected_config_gruop]:
            cb_preset.addItem(_)
        self.ui.tableWidget_channels.setCellWidget(this_row,1,cb_preset)
        cb_preset.currentIndexChanged.connect(self.change_preset_combobox)

        self.ui.channels[this_row] = ({'Group':selected_config_gruop, 
                                       'Preset':self.ui.configs[selected_config_gruop][0], 
                                       'Exposure': self.ui.channels[this_row]['Preset']})

    def change_preset_combobox(self,event):
        #detect and change *preset* combobox
       
        combo_box_index = event
       
        this_row = self.ui.tableWidget_channels.currentRow()
       
        this_item = self.ui.tableWidget_channels.cellWidget(this_row,1)
        
        if this_item is None:
            return
        
        selected_preset_gruop = this_item.itemText(combo_box_index)

        self.ui.channels[this_row]['Preset'] = selected_preset_gruop

    def change_preset_exposure(self,event):
        #detec change in exposure in tableWidget
        current_exposure = event
        this_row = self.ui.tableWidget_channels.currentRow()
        if this_row == -1:
            return
        self.ui.channels[this_row]['Exposure'] = current_exposure

    def remove_channel_preset(self): 
        #remove preset from the channels tableWidget 
        this_row = self.ui.tableWidget_channels.currentRow()
        self.ui.tableWidget_channels.removeRow(this_row)
        del self.ui.channels[this_row] 

    def add_positions_list(self):
        #add positions from the MM position list
        self.ui.positions = self.getPositions()

        self.ui.listWidget_positionList.clear()
        for p in self.ui.positions:
            self.ui.listWidget_positionList.addItem(str(p))
            
        #update info label
        self.ui.label_info_pos_val.setText(str(len(self.ui.positions)))        


    def clear_position_list(self):
        #clear the position list
        self.ui.listWidget_positionList.clear()
        self.ui.positions = []

        #update info label
        self.ui.label_info_pos_val.setText('0')


    def remove_position_from_list(self):
        position_presets_selected = self.ui.listWidget_positionList.currentRow()
        if  position_presets_selected == -1: #if none selected then it returns -1
            return

        del self.ui.positions[position_presets_selected]
        
        #update list widget
        self.ui.listWidget_positionList.clear()
        for ch in self.ui.positions:
            self.ui.listWidget_positionList.addItem(str(ch))

        #update info label
        self.ui.label_info_pos_val.setText(str(len(self.ui.positions)))


    #timelapse callbacks

    def add_timelapse(self):
        #compute the timelapse from lenght and framerate 
        duration_hr  = self.ui.spinBox_tlHr.value()
        duration_min  = self.ui.spinBox_tlMin.value()
        duration_sec = self.ui.spinBox_tlSec.value()

        framerate_hr = self.ui.spinBox_frHr.value()
        framerate_min = self.ui.spinBox_frMin.value()
        framerate_sec = self.ui.spinBox_frSec.value()

        #make a timelapse in seconds from the input, display in hh:mm:ss
        total_time = duration_hr*3600  + duration_min*60  + duration_sec
        framerate  = framerate_hr*3600 + framerate_min*60 + framerate_sec

        if total_time == 0 or framerate == 0:
            return

        self.ui.frames = [frame*framerate for  frame in range(math.ceil(total_time/framerate))]
        
        #update timepoits list widget
        self.ui.listWidget_timePoints.clear()
        for frame_number, frame in enumerate(self.ui.frames):
            ty_res = time.gmtime(frame)
            res = time.strftime("%H:%M:%S",ty_res)
            self.ui.listWidget_timePoints.addItem(f"f: {frame_number}, t: {res}")
        
        #update info labels
        self.ui.label_info_frames_val.setText(str(len(self.ui.frames)))
        
        ty_res = time.gmtime(self.ui.frames[-1])
        total_time_hms = time.strftime("%H:%M:%S",ty_res)
        self.ui.label_info_duration_val.setText(total_time_hms)

    def clear_timelapse(self):
        #clear the timelapse
        self.ui.listWidget_timePoints.clear()
        self.ui.label_info_frames_val.setText('0')
        self.ui.label_info_duration_val.setText('0')
        self.ui.frames = []

    def remove_timepoint_from_list(self):
        #remove selected timepoint, is it tricky with 'self.ui.frames'?
        frame_selected = self.ui.listWidget_timePoints.currentRow()
        if  frame_selected == -1: #if none selected then it returns -1
            return

        del self.ui.frames[frame_selected]
        
        #update list widget
        self.ui.listWidget_timePoints.clear()
        for frame_number, frame in enumerate(self.ui.frames):
            ty_res = time.gmtime(frame)
            res = time.strftime("%H:%M:%S",ty_res)
            self.ui.listWidget_timePoints.addItem(f"f: {frame_number}, t: {res}")

        #update info label
        self.ui.label_info_frames_val.setText(str(len(self.ui.frames)))

        ty_res = time.gmtime(self.ui.frames[-1])
        total_time_hms = time.strftime("%H:%M:%S",ty_res)
        self.ui.label_info_duration_val.setText(total_time_hms)

    def cancel_configuration_do_nothing(self):
        #just close the window and do nothing
        self.ui.close()

    def getPositions(self):
        
        #get current positions from mm_studio 

        positionListManager = self.ui.mm_studio.get_position_list_manager() 
        positions = positionListManager.get_position_list()
        numberOfPositions = positions.get_number_of_positions()

        positionDictionary = []
        #add for Ritacquire compatibility
        #thisPosition.get_default_xy_stage()
        #thisPosition.get_default_z_stage()
        for pos in range(numberOfPositions):
            thisPosition = positions.get_position(pos)
            positionDictionary.append({
                    'Position Label':thisPosition.get_label(),
                    'X':thisPosition.get_x(),
                    'Y':thisPosition.get_y(),
                    'Z':thisPosition.get_z(),
                    'XYStage':thisPosition.get_default_xy_stage(),
                    'ZStage':thisPosition.get_default_z_stage()})

        return positionDictionary

    def get_configs(self):

        #get micromanager configurations
        
        configs = {}
        availableGroups = self.ui.core.get_available_config_groups()
        if availableGroups.is_empty():
            print('group configuration is empty, bailing out')
            return
        numGroups = availableGroups.capacity()
        for ngroup in range(numGroups):
            thisGroup = availableGroups.get(ngroup)
            #add to dictionary
            configs[thisGroup] = []
            availableConfigs = self.ui.core.get_available_configs(thisGroup)
            if availableConfigs.is_empty():
                print(thisGroup +" is empty!")
                continue
            numConfigs = availableConfigs.capacity()
            for nConfig in range(numConfigs):
                thisConfig = availableConfigs.get(nConfig)            
                configs[thisGroup].append(thisConfig) # populate the dictionary
                #acces configuration: core.get_config_data(thisGroup,thisConfig)   
        return configs

    def emit_configuration(self):
        #self explanatory
        print(self.ui.channels)
        self.config_to_emit.emit({'channels':self.ui.channels, 'positions':self.ui.positions, 'frames':self.ui.frames})
        
def main():

    app = QtWidgets.QApplication(sys.argv)
    window = add_configuration() 
    app.exec()

if __name__ == '__main__':
    main()