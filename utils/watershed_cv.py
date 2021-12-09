import os
from utils.unet import UNet, UNet_deep

from skimage import io, measure, morphology, feature, color, transform, segmentation
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi
import time

import cv2 as cv

# def watershed_k(im_binary):

imname = 'segmented.tiff'
im_binary = io.imread(imname)

# img = cv.cvtColor(img, cv.COLOR_BGR2GRAY) #otherwise it breaks in the distanceTransfor - openCV formats...

#https://docs.opencv.org/4.x/d3/db4/tutorial_py_watershed.html

# t1 = time.time()

# img = cv.cvtColor(im_binary, cv.COLOR_BGR2GRAY) #otherwise it breaks in the distanceTransfor - openCV formats...
kernel = np.ones((3,3),np.uint8)
opening = cv.morphologyEx(im_binary,cv.MORPH_OPEN, kernel, iterations = 2)

sure_bg = cv.dilate(opening,kernel,iterations=3)

dist_transform = cv.distanceTransform(opening,cv.DIST_L2,5)

# ret, sure_fg = cv.threshold(dist_transform,0.5*dist_transform.max(),255,0)

#here is the part where Im supposed to 'impose minima', however, I don now know of this is working at all...
sure_fg = cv.erode(dist_transform, kernel, iterations = 3)
sure_fg = cv.erode(sure_fg, np.ones((3,1),np.uint8), iterations = 1) #WARNING - THIS EXTRA STEP WORKS ONLY FOR LONG CELLS THAT ARE VERTICAL - removes pixels along long axis of a cell!
sure_fg = sure_fg > 0

# Finding unknown region
sure_fg = np.uint8(sure_fg)
unknown = cv.subtract(sure_bg,sure_fg)

ret, markers = cv.connectedComponents(sure_fg)
markers = markers+1
markers[unknown==255] = 0

im2watershed = cv.cvtColor(im_binary, cv.COLOR_GRAY2RGB)

watersheded = cv.watershed(im2watershed, markers)

# return (watersheded>1)

# t2 = time.time()
# im2watershed = np.uint8(im2watershed[:,:,0])>0
im2watershed[watersheded==-1] = [255,0,0]

# print(f"{t2-t1} sec")

fig = plt.figure()
plt.imshow(im2watershed)
plt.show()
