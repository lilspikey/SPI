import cv
import os.path
from optparse import OptionParser

def create_diff(file1, file2):
    im1 = cv.LoadImage(file1, cv.CV_LOAD_IMAGE_GRAYSCALE)
    im2 = cv.LoadImage(file2, cv.CV_LOAD_IMAGE_GRAYSCALE)
    
    diff = cv.CreateImage((im1.width,im1.height), im1.depth, im1.nChannels)
    
    cv.AbsDiff(im1, im2, diff)
    
    cv.Erode(diff, diff, iterations=2)
    
    return diff


def calc_diff(file1, file2, output, out_index):
    diff = create_diff(file1, file2)
    if output:
        cv.SaveImage(os.path.join('diffed', '%s.jpg' % out_index), diff)
    avg, sd = cv.AvgSdv(diff)
    return sd[0]


def main(start, end, output):
    if output and not os.path.exists('diffed'):
        os.mkdir('diffed')
        
    prev = None
    for i in range(start, end+1):
        current = os.path.join('cam_images', '%d.jpg' % i)
        if prev is not None:
            try:
                print current, calc_diff(prev, current, output, i)
            except IOError:
                pass
        prev = current
    
    #cv.SaveImage('out.jpg', diff)

if __name__ == '__main__':
    parser = OptionParser(usage = "usage: %prog [options]")
    parser.add_option("--start", action="store", dest="start", type="int",
                      help="Start image index", default = 1)
    parser.add_option("--end", action="store", dest="end", type="int",
                      help="End image index", default = 1)
    parser.add_option("-o", "--output", action="store_true", dest="output", 
                      help="output diff images to diffed directory", default=False)
    (options, args) = parser.parse_args()
    main(options.start, options.end, options.output)