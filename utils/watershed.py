import numpy as np
from skimage import io, segmentation, morphology, measure, feature
from scipy import ndimage as ndi

def watershed(im_binary):

    """ apply wathershed segmentation to binary image"""

    #for explanatin of watershed segmentation see:
    #1)https://scikit-image.org/docs/dev/auto_examples/segmentation/plot_watershed.html
    #2)https://blogs.mathworks.com/steve/2013/11/19/watershed-transform-question-from-tech-support/
    distance = ndi.distance_transform_edt(im_binary)
    #define connectivity kernel for 2d image

    #connectivity size impacts some artifacts.
    conn = np.ones((5,5))

    h = 2 # h for h minimatransform
    #use morphological reconstruction, simillar to the matlab example
    distance2 = morphology.reconstruction(distance-h,distance)
    local_maxi = feature.peak_local_max(distance2, indices=False, footprint=conn)
    markers = measure.label(local_maxi)
    watershed_labels = segmentation.watershed(-distance, markers, mask=im_binary, watershed_line=True)
    watershed_labels = watershed_labels.astype('uint16') #if I convert to binary, is this important?
    
    wathershed_image = watershed_labels > 0 #change back to binary from labels
    
    return wathershed_image