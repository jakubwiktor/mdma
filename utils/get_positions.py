def get_positions(mm_studio=None):
        #get current positions from mm_studio 
        
        if not mm_studio:
            return None
        
        positionListManager = mm_studio.get_position_list_manager() 
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

def main():
    get_positions()

if __name__ == "__main__":
    main()