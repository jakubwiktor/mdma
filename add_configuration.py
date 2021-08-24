from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QApplication, QTableWidgetItem, QDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, Signal, Slot


import sys
# import add_configuration

from pycromanager import Bridge
import math
import time

#TODO read the exposure form the preset and set it: current_exposure = self.ui.lineEdit_setExposure.text()

#TODO add timelapse parameters with a button -> send a signal to the main GUI?

#TODO add functionality to load predefined settings, as if this function was used to edit a configuration from the main window

#TODO find out a way to pass the core property from mdma.py main window, so it wont open connections each time window is called

# def makeEvents(channels, positions, frames):
#     """create dictionary of events for acquisition"""
#     #parse 1-
#     #        time
#     #           |
#     #           > positions
#     #                     |
#     #                     > channels
#     #loop over timepoints, then positionis, and then each channel
    
#     if len(channels) == 0 or len(positions) == 0 or len(frames) == 0:
#         return []

#     events = []
#     for tCount, tValue in enumerate(frames):
#         for p in positions:
#             pos_name = list(p.keys())[0]
#             for c in channels:
#                 temp = {
#                         'axis':{'time':tCount},
#                         'min_start_time':tValue,
#                         'pos_name':pos_name,
#                         'x':p[pos_name]['x'],
#                         'y':p[pos_name]['x'],
#                         'z':p[pos_name]['x'],
#                         'channel':c,
#                         'save_path':'empty',
#                         }
#                 events.append(temp)

#     return events 

class add_configuration(QtWidgets.QDialog):
    
    config_to_emit = QtCore.Signal(dict)

    def __init__(self, parent=None, preset=None, presetNumber=0):
        super(add_configuration, self).__init__(parent)

        # uic.loadUi("add_configuration.ui", self)
        # self.ui.show()

        loader = QUiLoader()
        self.ui = loader.load("add_configuration.ui")
        self.ui.show()

        self.ui.bridge = Bridge()                  #
        self.ui.core = self.ui.bridge.get_core()      # these can be passed from the main window?
        self.ui.mmStudio = self.ui.bridge.get_studio()#
        self.ui.configs = self.get_configs()
        self.ui.result = []

        #enable loading and editing the presets
        if preset is not None:

            self.ui.frames = preset['frames']
            self.ui.positions = preset['positions']
            self.ui.channels = preset['channels']
            
            for ch in self.ui.channels:
                out_string = f"{ch['Group']}, {ch['preset']}, {ch['Exposure']} ms"
                self.ui.listWidget_channels.addItem(out_string)
            
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
        current_config = self.ui.comboBox_selectGroup.currentText()
        for ch in self.ui.configs[current_config]: #CONFIG 
            self.ui.comboBox_selectPreset.addItem(ch)
        
        #TODO!!
        #update the exposure block
        self.ui.lineEdit_setExposure.setText('10')  
        
        #positions
        self.ui.pushButton_addPos.clicked.connect(self.add_positions_list)
        self.ui.pushButton_clearPos.clicked.connect(self.clear_position_list)
        self.ui.pushButton_removePos.clicked.connect(self.remove_position_from_list)
        #timelapse
        self.ui.pushButton_addTime.clicked.connect(self.add_timelapse)
        self.ui.pushButton_clearTime.clicked.connect(self.clear_timelapse)
        self.ui.pushButton_removeTime.clicked.connect(self.remove_timepoint_from_list)

        #channels
        self.ui.comboBox_selectGroup.currentIndexChanged.connect(self.change_group_config)
        self.ui.pushButton_addPreset.clicked.connect(self.add_channel_preset)
        self.ui.pushButton_removePreset.clicked.connect(self.remove_channel_preset)
        
        #closing behaviour
        self.ui.pushButton_addConfiguration.clicked.connect(self.emit_configuration)
        self.ui.pushButton_cancelConfiguration.clicked.connect(self.cancel_configuration_do_nothing)

        # eventualy change to table widget
        # self.ui.tableWidget_channels.setColumnCount(3)
        # self.ui.tableWidget_channels.setHorizontalHeaderLabels(['Group','preset','Exposure'])
        # self.ui.tableWidget_channels.itemDoubleClicked.connect(self.update_channel_table)
       
    #channel callbacks

    #not working
    # def closeEvent(self, event):
    #     reply = self.ui.QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?', 
    #                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    #     if reply == QDialog.QMessageBox.Yes:
    #         event.accept()
    #         print('Window closed')
    #     else:
    #         event.ignore()
            
    def change_group_config(self):
        #select micromanager channel group setting
        self.ui.comboBox_selectPreset.clear()
        current_config = self.ui.comboBox_selectGroup.currentText()
        if current_config is not None:
            for ch in self.ui.configs[current_config]:
                self.ui.comboBox_selectPreset.addItem(ch)
    

    def add_channel_preset(self):
        current_group = self.ui.comboBox_selectGroup.currentText()
        current_preset = self.ui.comboBox_selectPreset.currentText()
        current_exposure = self.ui.lineEdit_setExposure.text()
        
        #update the list
        self.ui.channels.append({'Group':current_group, 
                              'preset':current_preset, 
                              'Exposure': current_exposure})

        #update list widget
        ch = (self.ui.channels[-1])
        out_string = f"{ch['Group']}, {ch['preset']}, {ch['Exposure']} ms"
        self.ui.listWidget_channels.addItem(out_string)

        # row = self.ui.tableWidget_channels.rowCount()
        # self.ui.tableWidget_channels.insertRow(row)
        
        # for column_num in range(3):
        #     chans_parameters = list(self.ui.channels[-1].keys())
        #     self.ui.tableWidget_channels.setItem(row,
        #                                       column_num, 
        #                                       QTableWidgetItem(self.ui.channels[-1][chans_parameters[column_num]]))

    def remove_channel_preset(self): 
        #remove one channel from the list, took me ages to write!
        channel_presets_selected = self.ui.listWidget_channels.currentRow()
        if  channel_presets_selected == -1:
            return

        del self.ui.channels[channel_presets_selected]
        
        #update list widget
        self.ui.listWidget_channels.clear()
        for ch in self.ui.channels:
            out_string = f"{ch['Group']}, {ch['preset']}, {ch['Exposure']} ms"
            self.ui.listWidget_channels.addItem(out_string)
        
    # def update_channel_table(self):
    #     #TODO
    #     #signals when the cell in the table was double clicked: means its ready to update
    #     out  = self.ui.tableWidget_channels.selectedItems() 
    #     row = out[0].row()
    #     column = out[0].column()
        
    #     self.ui.tableWidget_channels.setItem(row,column,QTableWidgetItem(str_out))
    #     #update self.ui.channels
    #     self.ui.channels[row]['Exposure'] = self.ui.tableWidget_channels.item(row,column).text()
    #     print(self.ui.channels)
                             

    #position callbacks

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
        
        #get current positions from mmStudio 

        positionListManager = self.ui.mmStudio.get_position_list_manager() 
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
        self.config_to_emit.emit({'channels':self.ui.channels, 'positions':self.ui.positions, 'frames':self.ui.frames})
        
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = add_configuration() 
    app.exec()

if __name__ == '__main__':
    main()