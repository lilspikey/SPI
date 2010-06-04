#!/usr/bin/env python

from bottle import route, send_file, request, response,\
                   json_dumps, run, debug, view, validate
import os.path
import os
from fnmatch import fnmatch
from itertools import islice
import cv

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
CAM_IMAGES_PATH = os.path.join(ROOT_PATH, 'cam_images')

@route('/cam_images/(?P<filename>.*)')
def cam_images(filename):
    send_file(filename, root=CAM_IMAGES_PATH)

def all_images():
    image_files = os.listdir(CAM_IMAGES_PATH)
    image_files.sort(key=lambda name: (len(name), name))
    image_index = 0
    for image_file in image_files:
        if fnmatch(image_file, '*.jpg'):
            image_index += 1
            url = '/'.join(['', 'cam_images', image_file])
            yield dict(index=image_index, url=url, name=image_file)

def get_image(index):
    for image in all_images():
        if image['index'] == index:
            return image
        elif image['index'] > index:
            break
    return None

@route('/image/:index')
@validate(index=int)
@view('image')
def image(index):
    prev, current, next = get_image(index-1), get_image(index), get_image(index+1)
    return dict(prev=prev, current=current, next=next)

@route('/')
@view('index')
def index():
    page = int(request.GET.get('page', 1))
    per_page = 100
    images = list(all_images());
    pages = [(i+1) for i in range(len(images)/per_page)]
    images = images[(page-1)*per_page:page*per_page]
    return dict(images=images, pages=pages)

def _load_cv_image_gray(index):
    image = get_image(index)
    return cv.LoadImage(os.path.join(CAM_IMAGES_PATH, image['name']),
                        cv.CV_LOAD_IMAGE_GRAYSCALE)

def encode_img(img):
    request.content_type='image/jpeg'
    encoded = cv.EncodeImage('.jpg', img)
    return encoded.tostring()

@route('/faces/:index')
@validate(index=int)
def faces(index):
    img = _load_cv_image_gray(index)
    
    min_size = (20, 20)
    image_scale = 2
    haar_scale = 1.2
    min_neighbors = 2
    haar_flags = 0
    cascade_file = os.path.join(ROOT_PATH, 'haarcascades', 'haarcascade_frontalface_alt.xml')
    cascade = cv.Load(cascade_file)
    
    faces = cv.HaarDetectObjects(img, cascade, cv.CreateMemStorage(0),
                                 haar_scale, min_neighbors, haar_flags, min_size)
    for ((x, y, w, h), n) in faces:
         pt1 = (int(x), int(y))
         pt2 = (int(x + w), int(y + h))
         cv.Rectangle(img, pt1, pt2, cv.RGB(255, 0, 0), 3, 8, 0)

    return encode_img(img)

@route('/diff/:first/:second')
@validate(first=int, second=int)
def diff(first, second):
    im1 = _load_cv_image_gray(first)
    im2 = _load_cv_image_gray(second)
    
    diff = cv.CreateImage((im1.width,im1.height), im1.depth, im1.nChannels)
    
    cv.AbsDiff(im1, im2, diff)
    
    cv.Erode(diff, diff, iterations=2)
    
    return encode_img(diff)

if __name__ == '__main__':
    debug(True)
    run(reloader=True)