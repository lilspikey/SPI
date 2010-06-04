#!/usr/bin/env python

from bottle import route, send_file, request, response,\
                   json_dumps, run, debug, view, validate
import os.path
import os
from fnmatch import fnmatch
from itertools import islice


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
    images = list(islice(all_images(), index, index+1))
    if images:
        return images[0]
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

if __name__ == '__main__':
    debug(True)
    run(reloader=True)