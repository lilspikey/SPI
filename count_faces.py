#!/usr/bin/python
"""
This program is demonstration for face and object detection using haar-like features.
The program finds faces in a camera image or video stream and displays a red box around them.

Original C implementation by:  ?
Python implementation by: Roman Stanchak, James Bowman
"""
import sys
import os
import cv
from optparse import OptionParser

# Parameters for haar detection
# From the API:
# The default parameters (scale_factor=2, min_neighbors=3, flags=0) are tuned 
# for accurate yet slow object detection. For a faster operation on real video 
# images the settings are: 
# scale_factor=1.2, min_neighbors=2, flags=CV_HAAR_DO_CANNY_PRUNING, 
# min_size=<minimum possible face size

min_size = (20, 20)
image_scale = 2
haar_scale = 1.2
min_neighbors = 2
haar_flags = 0

def detect_and_draw(img, cascade):
    # allocate temporary images
    gray = cv.CreateImage((img.width,img.height), 8, 1)
    small_img = cv.CreateImage((cv.Round(img.width / image_scale),
			       cv.Round (img.height / image_scale)), 8, 1)

    # convert color input image to grayscale
    cv.CvtColor(img, gray, cv.CV_BGR2GRAY)

    # scale input image for faster processing
    cv.Resize(gray, small_img, cv.CV_INTER_LINEAR)

    cv.EqualizeHist(small_img, small_img)

    faces = []

    if(cascade):
        t = cv.GetTickCount()
        faces = cv.HaarDetectObjects(small_img, cascade, cv.CreateMemStorage(0),
                                     haar_scale, min_neighbors, haar_flags, min_size)
        t = cv.GetTickCount() - t
        if False:#faces:
            for ((x, y, w, h), n) in faces:
                # the input to cv.HaarDetectObjects was resized, so scale the 
                # bounding box of each face and convert it to two CvPoints
                pt1 = (int(x * image_scale), int(y * image_scale))
                pt2 = (int((x + w) * image_scale), int((y + h) * image_scale))
                cv.Rectangle(img, pt1, pt2, cv.RGB(255, 0, 0), 3, 8, 0)

    return faces

#haar_dir = "../data/haarcascades/haarcascade_frontalface_alt.xml"
haar_dir = "/Users/ian/Documents/OpenCV-2.1.0/data/haarcascades/haarcascade_frontalface_alt.xml"


parser = OptionParser(usage = "usage: %prog [options] [filename|camera_index]")
parser.add_option("-c", "--cascade", action="store", dest="cascade", type="str", help="Haar cascade file, default %default", default = haar_dir)
(options, args) = parser.parse_args()

cascade = cv.Load(options.cascade)
    
capture = None

def count_faces(input_name):
    image = cv.LoadImage(input_name, 1)
    faces = detect_and_draw(image, cascade)
    return len(faces)

if __name__ == "__main__":
    faces_found = []
    cam_images_dir = "/Users/ian/Documents/SkiffCamDownloader/cam_images"
    files = os.listdir(cam_images_dir)
    print "Files:", len(files)
    for n, filename in enumerate(files):
        if n % 100 == 0:
            print "Progress: %d of %d" % (n, len(files))
        if filename.endswith('.jpg'):
            filename = os.path.join(cam_images_dir, filename)
            nbr_faces = count_faces(filename)
            if nbr_faces > 0:
                print "found faces:", nbr_faces
                faces_found.append(nbr_faces)
    print faces_found
    
