import re
import urllib2
import urllib
import os
import random

# run this to get all the Skiff cam images
# from http://cam.theskiff.org/
# set the start_id and end_id numbers below
# get end_id from the url permalink next to the topmost image
# at cam.theskiff.org, it'll look like:
# http://cam.theskiff.org/latest-from-the-skiff-cam-26542
# this script will make an './images/' directory and 
# download jpgs off all the full size pictures
start_id = 1
end_id = 29063#26542

def get_jpg_url(cam_url):
    urlhandle = urllib2.urlopen(cam_url)
    lines = urlhandle.readlines()
    lines = "".join(lines)

    # this is a what the html for this url looks like
    # http://cam.theskiff.org/latest-from-the-skiff-cam-26540
    #"""class="posterousGalleryMainDiv"><a href='http://posterous.com/getfile/files.posterous.com/theskiffcam/HCLBwI3Cy11OrduOMp9KYdhKpfIirB85o7pByex6Uf4WO5dwQC4iTvApeqcy/TheSkiffCam_2009-07-08_14-29-5.jpg'>""
    
    # look for the full sized image url
    regexp = re.compile("""class="posterousGalleryMainDiv"><a href='(.*)'""")
    # return just the url
    return regexp.findall(lines)[0]

# if no './images/' directory then make it
cam_images_dir = 'cam_images'
if not os.path.exists(cam_images_dir):
    os.mkdir(cam_images_dir)

# loop over all ids and download a jpg if
# we don't already have it
ids = range(start_id, end_id)
#random.shuffle(ids) # mix into random order
for cam_id in ids:
    cam_filename =  '%s/%d.jpg' % (cam_images_dir, cam_id)
    if True:#os.path.exists(cam_filename):
        print "Downloading %d" % (cam_id),
        cam_url = """http://cam.theskiff.org/latest-from-the-skiff-cam-%d""" % \
            (cam_id)
        # get the jpg's url by parsing the page's html
        cam_jpg_url = get_jpg_url(cam_url) 
        #print cam_jpg_url
        last_slash = cam_jpg_url.rfind('/')
        file_name = cam_jpg_url[last_slash+1:]
        print file_name
        ids_file = file('id_map.txt', 'at')
        ids_file.write('%d,%s\n' % (cam_id, file_name))
        ids_file.close()
        # download the jpg image directly to disk
        #urllib.urlretrieve(cam_jpg_url, cam_filename)
