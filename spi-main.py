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
import urllib2
import urllib
import json
import re
import datetime

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

def parse_date(date):
    year, mon, day = date.split('-')
    return datetime.date(int(year), int(mon), int(day))

def extract_date(date):
    return re.sub(r'(\d{4}-\d\d-\d\d).*', r'\1', date)

def create_date_range(date):
    date = extract_date(date)
    date = parse_date(date)
    following = date + datetime.timedelta(days=1)
    return date, following

def read_images(cursor, has_faces=None, diff_gt=None, id=None, not_diffed=None, not_detected=None, dates=None):
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
    
    if not_detected:
        filters.append('face_count < 0')
    
    if dates:
        date_filters = []
        if not isinstance(dates, list):
            dates = [dates]
        for date in dates:
            date, following = create_date_range(date)
            date_filters.append('(date >= ? and date < ?)')
            args.append(date)
            args.append(following)
        filters.append('(%s)' % (' or '.join(date_filters)))
    
    if id is not None:
        filters.append('id = ?')
        args.append(id)
    
    if filters:
        sql += ' where '
        sql += (' and '.join(filters))
    
    sql += ' order by id asc'
    
    print sql
    print args
    
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
    date = request.GET.get('date', None)
    
    if diff_gt.strip() == '':
        diff_gt = None
    
    per_page = 30
    images = list(read_images(cursor, has_faces=has_faces, diff_gt=diff_gt, dates=date));
    pages = [(i+1) for i in range(len(images)/per_page)]
    images = images[(page-1)*per_page:page*per_page]
    
    if not isinstance(date, list):
        date = [date]
    
    return dict(images=images, pages=pages, current_page=page, has_faces=has_faces, diff_gt=diff_gt, date=date)

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
    print "examining %d images for faces" % len(images)
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
    return list(read_images(cursor, not_detected=True, diff_gt=diff_gt))

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

def read_checkins(cursor):
    for url, created, name, image_url in cursor.execute('select url, created, name, image_url from checkins order by created asc'):
        yield {'url': url, 'created': created, 'name': name, 'image_url': image_url, 'possible': 0}

@with_db_cursor
def find_possible_face_count(cursor, checkins):
    possible = {}
    for date, count in cursor.execute('select date(date), count(*) from spi_image where face_count > 0 group by date(date)'):
        possible[date] = count
    
    for checkin in checkins:
        date = extract_date(checkin['created'])
        count = possible.get(date, 0)
        checkin['possible'] = count

@route('/checkins')
@view('checkins')
@with_db_cursor
def checkins(cursor):
    checkins = list(read_checkins(cursor))
    
    find_possible_face_count(checkins)
    
    return dict(checkins=checkins)

@route('/people')
@view('people')
@with_db_cursor
def people(cursor):
    checkins = list(read_checkins(cursor))
    
    all_dates = {}
    for checkin in checkins:
        name = checkin['name']
        dates = all_dates.get(name, [])
        dates.append(checkin['created'])
        all_dates[name] = dates
    
    people = []
    for name in sorted(all_dates.keys()):
        url_parts = ['has_faces=on']
        for date in all_dates[name]:
            url_parts.append('date=%s' % urllib.quote(date))
        url = '/?%s' % ('&'.join(url_parts))
        person = { 'name': name, 'url': url }
        people.append(person)
    
    return dict(people=people)

@route('/checkins/fetch')
@with_db_cursor
def checkins_fetch(cursor):
    GOWALLA_SPOT_ID = 32096
    GOWALLA_API_KEY = 'fa574894bddc43aa96c556eb457b4009'
    
    url = 'http://api.gowalla.com/checkins?spot_id=%d' % GOWALLA_SPOT_ID
    
    checkins = urllib2.Request(url)
    checkins.add_header('Accept', 'application/json')
    checkins.add_header('X-Gowalla-API-Key', GOWALLA_API_KEY)
    
    json_checkins = json.loads(urllib2.urlopen(checkins).read())
    
    existing = set()
    for row in cursor.execute('select url from checkins'):
        existing.add(row[0])
    
    checkins = []
    
    for json_checkin in json_checkins['events']:
        url = json_checkin['url']
        if url not in existing:
            created = json_checkin['created_at']
            user = json_checkin['user']
            name = '%s %s' % (user['first_name'], user['last_name'])
            image_url = user['image_url']
            
            created = re.sub(r'^(\d{4}-\d\d-\d\d)T(\d\d:\d\d:\d\d).*$', r'\1 \2', created)
            
            checkins.append((url, created, name, image_url))
    
    if checkins:
        cursor.executemany('insert into checkins (url, created, name, image_url) values(?,?,?,?)', checkins)
    
    redirect("/checkins")

def create_db(cursor):
    statements = [
        'create table if not exists spi_image (id integer primary key, filename text unique, date text, face_count integer, diff real)',
        'create index if not exists spi_image_filename_index on spi_image (filename)',
        'create index if not exists spi_image_date_index on spi_image (date)',
        'create index if not exists spi_image_face_count_index on spi_image (face_count)',
        'create index if not exists spi_image_diff_index on spi_image (diff)',
        'create table if not exists checkins (id integer primary key, url text unique, name text, image_url text, created text)',
        'create index if not exists checkins_name on checkins (name)',
        'create index if not exists checkins_created on checkins (created)',
    ]
    for stmt in statements:
        cursor.execute(stmt)

def read_image_dates(existing):
    images = open('image_dates.csv', 'r')
    for line in images:
        line = line.strip()
        cols = line.split(',')
        if len(cols) == 2:
            id, date = cols
            filename = '%s.jpg' % id
            if filename not in existing:
                full_path = os.path.join(CAM_IMAGES_PATH, filename)
                if os.path.exists(full_path):
                    yield filename, date

@route('/init')
@with_db_cursor
def init(cursor):
    create_db(cursor)
    existing = set()
    for row in cursor.execute('select filename from spi_image'):
        existing.add(row[0])
    print "made db"
    images = list(read_image_dates(existing));
    if images:
        images = [(filename, date, -1, 0.0) for (filename, date) in images]
        print "prepared images"
        res = cursor.executemany('insert into spi_image (filename, date, face_count, diff) values(?,?,?,?)', images)
        print "inserted"
    redirect("/")

if __name__ == '__main__':
    debug(True)
    run(reloader=True)