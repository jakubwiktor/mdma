import cv2 as cv
import numpy as np
# import time
# from matplotlib import pyplot as plt

def find_barcode_region(img):
    """
    Function detects the most central barcode image in the image of mother machine chip. 
    Returns a cropped image of the barcode. 
    NOTE! Image has to be in horizontal orientation, function will not handle vertical image.

    input: 
        img : 16 bit numpy array with phase contrast image of the mother machine (100x objective)
    output:
        barcode_im : 16 bit numpy array with the barcode image
        if the detection failed functino returns None
    Kuba
    """

    #first use iterative finding of the circles - find potential barcodes - shrink image if nothing was found
    counter = 0
    output = img.copy()
    while True:
        output = (img/256).astype('uint8')
        param1 = 200
        circles = cv.HoughCircles(output, 
                                cv.HOUGH_GRADIENT, 
                                dp=1.5, minDist=1,
                                param1=param1,
                                param2=10,
                                minRadius=5,
                                maxRadius=10)
        if circles is not None or counter > 2:
            break
        else:
            # print('shrinking')
            output = cv.resize(output,
                    dsize=(int(np.ceil(output.shape[1]/2)),int(np.ceil(output.shape[0]/2))))
            counter += 1
    
    if counter > 0:
        output = cv.resize(output,
                    dsize=(int(np.ceil(img.shape[1])),int(np.ceil(img.shape[0]))))

    #convert circles to recntangles to use cv.groupRectangles function
    rectangles = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            rectangles.append([x-r,y-r,2*r,2*r])
    else:
        print('find_barcode_region: No circles detected on the image - line 61')
        return None

    #filter detections at the edges of the image
    im_height = int(np.floor(img.shape[0])) #'y' coordinates
    im_width = int(np.floor(img.shape[1])) #'x' coordinates
    keep_rectangles = []
    for (x,y,w,h) in rectangles:
            if y > im_height*0.2 and y < im_height*0.8 and x > im_width*0.05 and x < im_width*0.95:
                keep_rectangles.append(np.array([x,y,w/2,h/2])) #needed for cv2.groupRectangles. Shrinking rectangles helps too.
                keep_rectangles.append(np.array([x,y,w/2,h/2])) #and for some reason it needs to be doubled

    #group rectangles with cv.groupRectangles
    rectangles,_ = cv.groupRectangles(keep_rectangles, 1, 2)
    #select only bright regions
    pixel_values = []
    for (x,y,w,h) in rectangles:
        im_slice = img[y-h*2:y+h*2,x-w*2:x+w*2]
        if im_slice.any():
            pixel_values.append(np.max(im_slice)) #brightest pixel - usually barcode
            #pixel_values.append(sum(sum(im_slice)))

    threshold_multiplier = 10
    while True:
        bright_regions = np.where(pixel_values > np.median(img)*threshold_multiplier)
        # print(bright_regions)
        if bright_regions[0].shape[0] != 0:
            break
        if threshold_multiplier == 0:
            print('thresholding of cicles failed')
            return None
            # break
        threshold_multiplier = threshold_multiplier-1
    rectangles = rectangles[bright_regions]

    # optupt2 = output.copy()
    # for x,y,w,h in rectangles:
    #     cv.rectangle(output,(x,y),(x+w,y+h),(255,255,255),1)
    # cv.imshow('output', output)
    # cv.waitKey(0)
    # return None
    
    #find regularities in circle locations
    #TODO - this part needs to be improved for robust detection - it shoudl look for a strongest signal, not only one that is closest to the middle
    pk_pos = []
    pk_size = []
    bin_edges = [x for x in range(0,img.shape[1],50)] # 20px spaced bins
    
    for edge_ind,_ in enumerate(bin_edges[:-1]):
        rect_indexes = (rectangles[:,0] > bin_edges[edge_ind]) & (rectangles[:,0] < bin_edges[edge_ind+1])
        current_rectangles = rectangles[rect_indexes]
        if current_rectangles.size > 2: #filet for more than 2 detections
            pk_pos.append(np.mean(current_rectangles[:,0])) #save mean x position
            pk_size.append(len(current_rectangles))

    # print(pk_pos)
    # print(pk_size) # <- maybe get 3 biggest peaks

    #use the strongest peak 
    #TODO - also find the most center one
    main_pk = int(pk_pos[np.argmax(pk_size)])
    barcode_loc = [main_pk-20,main_pk+30,int(np.floor(img.shape[0]*0.2)),int(np.floor(img.shape[0]*0.8))] #somehowh main_pk is moved to the left
    barcode_im = img[barcode_loc[2]:barcode_loc[3],barcode_loc[0]:barcode_loc[1]]
    
    return barcode_im

def match_barcode(img, barcode_img):
    """
    function locates barcode on the image using a image seed. Image seed
    has to be a cropped image of barcode, ideally from the same position 
    but from time=0, but it should also work for a generalized image of barcode.
    There is no guarantee that it will return the middle barcode.
    
    -runs for about 30-40 ms on SONA image (800px x 2048px)
    -may not work with very large drifft

    input:
        img : 16-bit phase contrast image of the mother machine chip (100x objective)
        barcode_img : 16-bit cropped image of barcode region to match
    output:
        top_left - tuple, coordinates of top left corner of matched rectangle (x,y)
        bottom_right - tuple, coordinates of bottorm right corner of matched rectangle (x,y)
        
    TODO - how to handle error when nothing is detected?
    Kuba
    """
    #available methods - output of some in MINUMUM, not MAXIMUM!
    # methods = ['cv.TM_CCOEFF', 'cv.TM_CCOEFF_NORMED', 'cv.TM_CCORR',
    #             'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED']
    method = cv.TM_CCOEFF

    #convert to 8-bit for cv2.matchTemplate
    img = (img/256).astype('uint8')
    barcode_img = (barcode_img/256).astype('uint8')
    w, h = barcode_img.shape[::-1]

    res = cv.matchTemplate(img,barcode_img,method) #accepts 8 or 32 bit images
    
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    cv.rectangle(img,top_left, bottom_right, color=(255,0,0), thickness=10)
    
    return top_left, bottom_right

def main():
    #testing on some images
    plist = [f"Pos{x}" for x in range(20)]
    
    for p in plist:
        image_name = 'C:\\Users\\kubus\\Documents\\EXP-21-BV3242 liveRuns\\exp6\\' + p + '\\aphase\\img_000000000.tiff'
        print(image_name)
        # image_name = 'C:\\Users\\kubus\\Documents\\test_unet\\img_000000003.tiff'

        img = cv.imread(image_name,cv.IMREAD_ANYDEPTH)
        barcode_img = find_barcode_region(img)
    
        if barcode_img is not None:
            top_left, bottom_right = match_barcode(img, barcode_img)
            b_image = img[top_left[1]:bottom_right[1],top_left[0]:bottom_right[0]]
            output = img.copy()
            output = (output/256).astype('uint8')
            output = cv.rectangle(output,top_left,bottom_right,(255,255,255), 5)
            cv.imshow('barcode',output)
            cv.waitKey(0)

if __name__ == '__main__':
    main()