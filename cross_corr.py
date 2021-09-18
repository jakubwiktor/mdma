#testing barcode detection using different methods
# -pip install opencv-python-
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

    #compute mean brightness of each circle
    circle_vals = []
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")

        #limit the circles to be present only in 20% to 80% of the image - edges of the chip tend to be bright
        lower_bound = int(np.floor(img.shape[0]*0.2)) #'y' coordinates
        upper_bound =  int(np.ceil(img.shape[0]*0.8))
        circles = circles[(circles[:,1] > lower_bound) & (circles[:,1] < upper_bound)]

        for (x, y, r) in circles:
            # r=int(np.ceil(r)/2)
            r = 3
            vals = img[y-r:y+r,x-r:x+r]
            circle_vals.append(np.mean(vals))
    else:
        print('find_barcode_region: No circles detected on the image - line 61')
        return None

    #select brightest circles only
    threshold_multiplier = 5
    while True:
        bright_circles = np.where(circle_vals > np.median(img)*threshold_multiplier)
        if bright_circles[0].shape[0] != 0:
            break
        if threshold_multiplier == 0:
            print('thresholding of cicles failed')
            return None
            # break
        threshold_multiplier = threshold_multiplier-1
    circles = circles[bright_circles]

    #find regularities in circle locations
    pk_pos = []
    bin_edges =[x for x in range(0,img.shape[1],20)] # 20px spaced bins
    for edge_ind,_ in enumerate(bin_edges[:-1]):
        circ_indexes = (circles[:,0] > bin_edges[edge_ind]) & (circles[:,0] < bin_edges[edge_ind+1])
        current_circles = circles[circ_indexes]
        if current_circles.size > 2: #filet for more than 2 detections
            pk_pos.append(np.mean(current_circles[:,0]))

    dist_from_cntr = [abs(x-(img.shape[1]/2)) for x in pk_pos]
    middle_pk = dist_from_cntr.index(min(dist_from_cntr))

    middle_pk = dist_from_cntr.index(min(dist_from_cntr))
    middle_pos = int(pk_pos[middle_pk])

    barcode_loc = [ middle_pos-30, 
                    middle_pos+30, 
                    int(np.floor(img.shape[0]*0.1)), 
                    int(np.ceil(img.shape[0]*0.9))] #x,x,y,y

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
    image_name = 'C:\\Users\\kubus\\Documents\\test_unet\\img_000000003.tiff'
    img = cv.imread(image_name,cv.IMREAD_ANYDEPTH)

    barcode_img = find_barcode_region(img)

    top_left, bottom_right = match_barcode(img, barcode_img)
    
    b_image = img[top_left[1]:bottom_right[1],top_left[0]:bottom_right[0]]
  
    cv.imshow('barcode',b_image)
    cv.waitKey(0)

if __name__ == '__main__':
    main()