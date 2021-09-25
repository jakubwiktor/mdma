# test = ['Pos11','Pos10','Pos0','Pos100']

# out = [''.join(filter(str.isdigit, t)) for t in test]
# out.sort(key=int)
# print(out)

class test():

    def __init__(self): 
        self.configurations = [{'channels': [{'Group': 'Channel', 'Preset': 'Cy5', 'Exposure': 100}], 'positions': [{'Position Label': 'Pos0', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos1', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos2', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos3', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos4', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos5', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos6', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos7', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos8', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos9', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos10', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos11', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 600, 1200, 1800, 2400, 
            3000]}, {'channels': [{'Group': 'Objective', 'Preset': '10X', 'Exposure': 100}], 'positions': [{'Position Label': 'Pos6', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos7', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos8', 'X': 0, 'Y': 0, 
            'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos9', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos10', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}, {'Position Label': 'Pos11', 'X': 0, 'Y': 0, 'Z': 0, 'XYStage': 'XY', 'ZStage': 'Z'}], 'frames': [0, 1800]}]      

    def printit(self):
        print(self.configurations)

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

        #TODO - compile to make the positions go in order from Pos0 - PosXX
        #test = ['Pos11','Pos10','Pos0','Pos100']
        #out = [''.join(filter(str.isdigit, t)) for t in test]
        #out.sort(key=int)
        #print(out)
        events = []
        for config in self.configurations:
            for time_counter, time_value in enumerate(config['frames']):
                for position_index, position in enumerate(config['positions']):
                    for channel in config['channels']:
                        
                        save_path = f"{save_root}/{position['Position Label']}/{channel['Preset']}/img_{time_counter:09d}.tiff"
                        
                        pnumber = int(''.join(filter(str.isdigit, position['Position Label']))) # cuts the 'Pos' part of 'PosXXX' naming and uses only integer for sorting

                        event = {'axes':{'position': pnumber},
                                'channel': {'group': channel['Group'], 'config': channel['Preset']},
                                'exposure': int(channel['Exposure']),
                                'z': position['Z'],
                                'min_start_time': time_value,
                                'x': position['X'],
                                'y': position['Y'],
                                'pos_label': position['Position Label'],
                                'save_location': save_path
                                }
                        
                        events.append(event)

        sorted_events = sorted(events, key = lambda x: (x['min_start_time'], x['axes']['position']))
        # sorted_events = events
        for fnum, ev in enumerate(sorted_events):
            print(f"{ev['axes']['position']} time: {ev['min_start_time']}, position: {ev['pos_label']} , channel: {ev['channel']['config']}, No: {fnum}")

        return sorted_events
        
def main():
    t = test()
    t.compile_experiment(save_root='TEST:')

if __name__ == "__main__":
    main()
