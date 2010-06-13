#!/usr/bin/env python

from bottle import route, send_file, request, response,\
                   json_dumps, run, debug, view, validate, redirect,\
                   BreakTheBottle
import sqlite3 as db
import os.path
import os
from fnmatch import fnmatch
from itertools import islice
import cv

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
CAM_IMAGES_PATH = os.path.join(ROOT_PATH, 'cam_images')

DB_FILE = os.path.join(ROOT_PATH, 'spi.db')

def with_db_cursor(fn):
    def _decorated(*arg, **kw):
        committed = False
        conn = db.connect(DB_FILE)
        try:
            cursor = conn.cursor()
            val = fn(cursor, *arg, **kw)
            committed = True
            conn.commit()
            return val
        except BreakTheBottle:
            committed = True
            conn.commit()
            raise
        finally:
            if not committed:
                conn.rollback()
            conn.close()
    return _decorated

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

def read_images(cursor, has_faces=None, diff_gt=None, id=None, not_diffed=None):
    sql = 'select id, filename from spi_image'
    filters = []
    args = []
    
    if has_faces is not None:
        filters.append('face_count > 0')
    
    if diff_gt is not None:
        filters.append('diff > ?')
        args.append(diff_gt)
    
    if not_diffed is not None:
        filters.append('diff = 0')
    
    if id is not None:
        filters.append('id = ?')
        args.append(id)
    
    if filters:
        sql += ' where '
        sql += (' and '.join(filters))
    
    sql += ' order by id asc'
    
    try:
        images = cursor.execute(sql, args)
        for id, filename in images:
            url = '/'.join(['', 'cam_images', filename])
            yield dict(index=id, url=url, name=filename)
    except db.OperationalError:
        pass

def get_image(cursor, index):
    for image in read_images(cursor, id=index):
        return image
    return None

@route('/image/:index')
@validate(index=int)
@view('image')
@with_db_cursor
def image(cursor, index):
    if index == 1:
        second = index + 1
    else:
        second = index - 1
    diff = image_diff_sd(cursor, index, second)
    prev, current, next = get_image(cursor, index-1), get_image(cursor, index), get_image(cursor, index+1)
    return dict(prev=prev, current=current, next=next, diff=diff)

@route('/')
@view('index')
@with_db_cursor
def index(cursor):
    page = int(request.GET.get('page', 1))
    has_faces = request.GET.get('has_faces', None)
    diff_gt = request.GET.get('diff_gt', '')
    if diff_gt.strip() == '':
        diff_gt = None
    
    per_page = 30
    images = list(read_images(cursor, has_faces=has_faces, diff_gt=diff_gt));
    pages = [(i+1) for i in range(len(images)/per_page)]
    images = images[(page-1)*per_page:page*per_page]
    return dict(images=images, pages=pages, current_page=page, has_faces=has_faces, diff_gt=diff_gt)

def _load_cv_image_gray(cursor, index):
    image = get_image(cursor, index)
    return cv.LoadImage(os.path.join(CAM_IMAGES_PATH, image['name']),
                        cv.CV_LOAD_IMAGE_GRAYSCALE)

def encode_img(img):
    request.content_type='image/jpeg'
    encoded = cv.EncodeImage('.jpg', img)
    return encoded.tostring()

@route('/faces/:index')
@validate(index=int)
@with_db_cursor
def faces(cursor, index):
    img = _load_cv_image_gray(cursor, index)
    faces = find_faces(img)
    
    for ((x, y, w, h), n) in faces:
         pt1 = (int(x), int(y))
         pt2 = (int(x + w), int(y + h))
         cv.Rectangle(img, pt1, pt2, cv.RGB(255, 0, 0), 3, 8, 0)

    return encode_img(img)

def find_faces(img):
    min_size = (20, 20)
    image_scale = 2
    haar_scale = 1.2
    min_neighbors = 2
    haar_flags = 0
    cascade_file = os.path.join(ROOT_PATH, 'haarcascades', 'haarcascade_frontalface_alt.xml')
    cascade = cv.Load(cascade_file)
    
    faces = cv.HaarDetectObjects(img, cascade, cv.CreateMemStorage(0),
                                 haar_scale, min_neighbors, haar_flags, min_size)
    return faces

@route('/faces/detect')
def detect_faces():
    diff_gt = request.GET.get('diff_gt', '')
    if diff_gt.strip() == '':
        diff_gt = None
    
    images = get_images_for_detect(diff_gt)
    for image in images:
        index = image['index']
        
        print "detect", index
        
        save_detect(image)
    redirect("/")

@with_db_cursor
def save_detect(cursor, image):
    id = image['index']
    
    img = _load_cv_image_gray(cursor, id)
    faces = find_faces(img)
    
    count = len(faces)
    
    cursor.execute('update spi_image set face_count = ? where id = ?', (count, id))

@with_db_cursor
def get_images_for_detect(cursor, diff_gt):
    return list(read_images(cursor, diff_gt=diff_gt))

@route('/diff/:first/:second')
@validate(first=int, second=int)
@with_db_cursor
def diff(cursor, first, second):
    im1 = _load_cv_image_gray(cursor, first)
    im2 = _load_cv_image_gray(cursor, second)
    
    diff = diff_image(im1, im2)
    
    return encode_img(diff)

def pre_smooth(im):
    cv.EqualizeHist(im, im)

def diff_image(im1, im2):
    pre_smooth(im1)
    pre_smooth(im2)
    
    diff = cv.CreateImage((im1.width,im1.height), im1.depth, im1.nChannels)
    
    cv.AbsDiff(im1, im2, diff)
    
    cv.Erode(diff, diff, iterations=5)
    
    return diff

def image_diff_sd(cursor, id1, id2):
    im1 = _load_cv_image_gray(cursor, id1)
    im2 = _load_cv_image_gray(cursor, id2)
    
    diff = diff_image(im1, im2)
    
    avg, sd = cv.AvgSdv(diff)
    
    return sd[0]

@with_db_cursor
def get_images_for_diff(cursor):
    return list(read_images(cursor, not_diffed=True))

@with_db_cursor
def save_diff(cursor, id1, id2):
    sd = image_diff_sd(cursor, id1, id2)
    
    cursor.execute('update spi_image set diff = ? where id = ?', (sd, id1))

@route('/diff/calc')
def diff_calc():
    images = get_images_for_diff()
    for image in images:
        index = image['index']
        
        print "diff", index
        
        if index == 1:
            second = index +1
        else:
            second = index -1
        
        save_diff(index, second)
    redirect("/")

def create_db(cursor):
    statements = [
        'create table if not exists spi_image (id integer primary key, filename text unique, face_count integer, diff real)',
        'create index if not exists spi_image_filename_index on spi_image (filename)',
        'create index if not exists spi_image_face_count_index on spi_image (face_count)',
        'create index if not exists spi_image_diff_index on spi_image (diff)',
    ]
    for stmt in statements:
        cursor.execute(stmt)

@route('/init')
@with_db_cursor
def init(cursor):
    create_db(cursor)
    print "made db"
    images = list(all_images());
    images = [(i+1, image['name'], 0, 0.0) for (i,image) in enumerate(images)]
    print "prepared images"
    res = cursor.executemany('insert or replace into spi_image (id, filename, face_count, diff) values(?,?,?,?)', images)
    print "inserted"
    redirect("/")

if __name__ == '__main__':
    debug(True)
    run(reloader=True)