from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QApplication, QTableWidgetItem, QDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, Signal, Slot


import sys
import select_model

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

        # #initialise tableWidge_channels -> before they are updated by loading the presets
        # for _ in range(3):
        #     self.ui.tableWidget_channels.insertColumn(_)
        # #fill columns headers
        # self.ui.tableWidget_channels.setHorizontalHeaderLabels(['Group','Preset','Exposure'])
        
        # #stretch to fill
        header = self.ui.tableWidget_channels.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        
        #set custom context menu for channel table <- i guess that is not needed anymore - 2021.sep.08
        # self.ui.tableWidget_channels.setContextMenuPolicy(QtCore.Qt.CustomContextMenu) 

        #allow for multiple selection in the QListWidget
        self.ui.listWidget_positionList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)   
        
        #positions buttons
        self.ui.pushButton_addPos.clicked.connect(self.add_positions_list)
        self.ui.pushButton_clearPos.clicked.connect(self.clear_position_list)
        self.ui.pushButton_removePos.clicked.connect(self.remove_position_from_list)
      
        #allow for multiple selection in the QListWidget
        self.ui.listWidget_timePoints.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)   

        #timelapse
        self.ui.pushButton_addTime.clicked.connect(self.add_timelapse)
        self.ui.pushButton_clearTime.clicked.connect(self.clear_timelapse)
        self.ui.pushButton_removeTime.clicked.connect(self.remove_timepoint_from_list)

        #channels
        # self.ui.comboBox_selectGroup.currentIndexChanged.connect(self.change_group_config)
        self.ui.pushButton_addPreset.clicked.connect(self.add_channel_preset)
        self.ui.pushButton_removePreset.clicked.connect(self.remove_channel_preset)
        self.ui.pushButton_segmentation.clicked.connect(self.add_segmentation_parameters)
        self.ui.pushButton_detectBarcode.clicked.connect(self.add_barcode_detection)

        #define QTableWidget column indexes for channels - important for channels functions
        self.check_column = 0
        self.group_column = 1
        self.preset_column = 2 
        self.exposure_column = 3

        #closing behaviour
        self.ui.pushButton_addConfiguration.clicked.connect(self.emit_configuration)
        self.ui.pushButton_cancelConfiguration.clicked.connect(self.cancel_configuration_do_nothing)

        # modify the 'ADD' button to 'add' and 'edit' mode
        if windowMode == 'edit':
            self.ui.pushButton_addConfiguration.setText('Edit')
       
        #enable loading and editing the presets
        if preset is not None:
            
            #TODO - add check mark if the channel is selected for segmentation, read the segmentation

            #here the channel configurations are stored
            self.ui.frames = preset['frames']
            self.ui.positions = preset['positions']
            self.ui.channels = preset['channels']

            for ch_index, ch in enumerate(self.ui.channels):
                n = self.ui.tableWidget_channels.rowCount()
                self.ui.tableWidget_channels.setRowCount(n + 1)
            
                #to populate comboboxes
                this_config_name = ch['Group']

                #check box column
                check_box = QtWidgets.QCheckBox()
                check_box.setStyleSheet("margin-left:50%; margin-right:50%;") #this centers the box, not very well tho
                self.ui.tableWidget_channels.setCellWidget(n,self.check_column,check_box)

                cb_group = QtWidgets.QComboBox()
                for _ in list(self.ui.configs.keys()):
                    cb_group.addItem(_)    
                self.ui.tableWidget_channels.setCellWidget(n,self.group_column,cb_group)
                
                #select the correct Group to display
                current_group_index = list(self.ui.configs.keys()).index(this_config_name)
                self.ui.tableWidget_channels.cellWidget(ch_index,self.group_column).setCurrentIndex(current_group_index)
                
                #add callback after creation not to invoke the callback on creation
                cb_group.currentIndexChanged.connect(self.change_group_combobox)
                
                cb_preset = QtWidgets.QComboBox()
                for _ in self.ui.configs[this_config_name]:
                    cb_preset.addItem(_)
                self.ui.tableWidget_channels.setCellWidget(n,self.preset_column,cb_preset)

                #display the correct Preset
                current_preset_index = self.ui.configs[this_config_name].index(ch['Preset'])
                self.ui.tableWidget_channels.cellWidget(ch_index,self.preset_column).setCurrentIndex(current_preset_index)

                #add callback
                cb_preset.currentIndexChanged.connect(self.change_preset_combobox)

                exposure_widget = QtWidgets.QLineEdit()
                exposure_widget.textChanged.connect(self.change_preset_exposure)
                exposure_widget.setText(str(ch['Exposure']))
                self.ui.tableWidget_channels.setCellWidget(n,self.exposure_column,exposure_widget)
    
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

    #channel callbacks
    def add_channel_preset(self):
        #tableWidge_channels callbacks - working with comboBoxes

        n = self.ui.tableWidget_channels.rowCount()
        self.ui.tableWidget_channels.setRowCount(n + 1)
       
        #to populate comboboxes
        first_config_name = list(self.ui.configs.keys())[0]

        #check box column
        check_box = QtWidgets.QCheckBox()
        check_box.setStyleSheet("margin-left:50%; margin-right:50%;") #this centers the box, not very well tho
        self.ui.tableWidget_channels.setCellWidget(n,self.check_column,check_box)

        #group column
        cb_group = QtWidgets.QComboBox()
        for this_group in list(self.ui.configs.keys()):
            cb_group.addItem(this_group)    
        self.ui.tableWidget_channels.setCellWidget(n,self.group_column,cb_group)
        #add calback after creation not to invoke the callback on creation
        cb_group.currentIndexChanged.connect(self.change_group_combobox)
        
        #preset column
        cb_preset = QtWidgets.QComboBox()
        for this_preset in self.ui.configs[first_config_name]:
            cb_preset.addItem(this_preset)
        self.ui.tableWidget_channels.setCellWidget(n,self.preset_column,cb_preset)
        cb_preset.currentIndexChanged.connect(self.change_preset_combobox)

        #exposure column
        exposure_widget = QtWidgets.QLineEdit()
        exposure_widget.textChanged.connect(self.change_preset_exposure)
        exposure_widget.setText('100')
        self.ui.tableWidget_channels.setCellWidget(n,self.exposure_column,exposure_widget)

        #update channel list
        self.ui.channels.append({'Group':first_config_name, 
                                 'Preset':self.ui.configs[first_config_name][0], 
                                 'Segmentation':{'Do':0,'Save_frames':None},
                                 'Exposure': 100})

    def change_group_combobox(self, event):
        #detect the change in the *channel* combo box and update the channels
        #event -> is the index of the combo box

        combo_box_index = event

        this_row = self.ui.tableWidget_channels.currentRow()
        
        #this is reference to the combo box
        this_item = self.ui.tableWidget_channels.cellWidget(this_row,self.group_column)

        #check if there is already a channel added
        if this_item is None:
            return

        #update the stored channel in preset, update the cb_preset
        selected_config_gruop = this_item.itemText(combo_box_index)
        
        #check if any change was actually made to the selection
        if selected_config_gruop == self.ui.channels[this_row]['Group']:
            return

        self.ui.tableWidget_channels.cellWidget(this_row,self.group_column).setCurrentIndex(event)

        cb_preset = QtWidgets.QComboBox()
        for _ in self.ui.configs[selected_config_gruop]:
            cb_preset.addItem(_)
        self.ui.tableWidget_channels.setCellWidget(this_row,self.preset_column,cb_preset)
        cb_preset.currentIndexChanged.connect(self.change_preset_combobox)

        self.ui.channels[this_row] = ({'Group':selected_config_gruop, 
                                       'Preset':self.ui.configs[selected_config_gruop][0], 
                                       'Segmentation':self.ui.channels[this_row]['Segmentation'],
                                       'Exposure': self.ui.channels[this_row]['Exposure']})

    def change_preset_combobox(self,event):
        #detect and change *preset* combobox
       
        combo_box_index = event
       
        this_row = self.ui.tableWidget_channels.currentRow()
       
        this_item = self.ui.tableWidget_channels.cellWidget(this_row,self.preset_column)
        
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
        #remove preset from the channels tableWidget - handles multiple selections

        #check which channels are selected by the user
        selected_channels = []
        for this_row in range(self.ui.tableWidget_channels.rowCount()):
            #get the cellWidget, it is not the 'item'
            check_box = self.ui.tableWidget_channels.cellWidget(this_row,self.check_column)
            if check_box.checkState() == QtCore.Qt.CheckState.Checked:
                selected_channels.append(this_row)
        
        if len(selected_channels) == 0:
            return

        self.ui.channels = [chan for x,chan in enumerate(self.ui.channels) if x not in selected_channels]
        print(self.ui.channels)
        #update table widget
        for ch in reversed(selected_channels):
            self.ui.tableWidget_channels.removeRow(ch)

    def add_segmentation_parameters(self):
        #add segmentation parameters
        #TODO - add 'detect barcode' checkbox

        selected_channels = []
        for this_row in range(self.ui.tableWidget_channels.rowCount()):
            #get the cellWidget, it is not the 'item'
            check_box = self.ui.tableWidget_channels.cellWidget(this_row,self.check_column)
            if check_box.checkState() == QtCore.Qt.CheckState.Checked:
                selected_channels.append(this_row)
        
        if len(selected_channels) == 0:
            print('no channel is selected')
            return
        elif len(selected_channels) > 1:
            print('only one channel can be selected')
            return

        this_row = selected_channels[0]
        this_preset = self.ui.channels[this_row] 
        #all channels share same timelapse and position parameters
        self.ui.add_model_window = select_model.select_model(preset = this_preset, timelapse = self.ui.frames)
        self.ui.add_model_window.send_model.connect(self.test)

    def test(self,message):
        #receive signal from select_model window
        print(message)

    def add_barcode_detection(self):
        #select if a channel will be used for barcode detection
        selected_channels = []
        for this_row in range(self.ui.tableWidget_channels.rowCount()):
            #get the cellWidget, it is not the 'item'
            check_box = self.ui.tableWidget_channels.cellWidget(this_row,0)
            if check_box.checkState() == QtCore.Qt.CheckState.Checked:
                selected_channels.append(this_row)
        
        if len(selected_channels) == 0:
            print('no channel is selected')
            return
        elif len(selected_channels) > 1:
            print('only one channel can be selected')
            return
        
        this_chan = self.ui.channels[selected_channels[0]]['Preset']
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText("Barcode detection only works on phase contrast.")
        msgBox.setInformativeText(f"Add barcode detection to >{this_chan}< channel")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        m = msgBox.exec()
        if m == QtWidgets.QMessageBox.Yes:
            #add barcode detection to the given channel
            print(f"adding barcode detection to >{this_chan}< channel")
            pass
        

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
        #working with selection of multiple events 
        
        position_presets_selected = self.ui.listWidget_positionList.currentRow()
        if  position_presets_selected == -1: #if none selected then it returns -1
            return
        
        selected_items = self.ui.listWidget_positionList.selectedIndexes()
        rows_to_delete = []
        for item in selected_items:
            rows_to_delete.append(item.row())
        
        #remake list, 'del' won't work on a mutliple selection - list is modified and poitners dont match
        self.ui.positions = [pos for x,pos in enumerate(self.ui.positions) if x not in rows_to_delete]
        
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

        selected_items = self.ui.listWidget_timePoints.selectedIndexes()
        rows_to_delete = []
        for item in selected_items:
            rows_to_delete.append(item.row())

        #remake list, 'del' won't work on a mutliple selection - list is modified and poitners dont match
        self.ui.frames = [data for x, data in enumerate(self.ui.frames) if x not in rows_to_delete]

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
        # print(self.ui.channels)
        print(self.ui.channels)
        self.config_to_emit.emit({'channels':self.ui.channels, 'positions':self.ui.positions, 'frames':self.ui.frames})
        self.ui.close()

def main():

    app = QtWidgets.QApplication(sys.argv)
    window = add_configuration() 
    app.exec()

if __name__ == '__main__':
    main()