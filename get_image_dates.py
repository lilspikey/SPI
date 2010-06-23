from threading import Thread
import urllib2
import re
import time
import socket


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


class testit(Thread):
   def __init__ (self,id):
      Thread.__init__(self)
      self.id = id
      self.status = -1
      self.url = None
   def run(self):
      #global d 

      cam_id = self.id
      cam_url = """http://cam.theskiff.org/latest-from-the-skiff-cam-%d""" % \
          (cam_id)
      #print cam_url    
      # get the jpg's url by parsing the page's html
      try:
        cam_jpg_url = get_jpg_url(cam_url)
        #if cam_id == 1:
        #  raise urllib2.URLError('ian')
        self.url = cam_jpg_url
        #last_slash = cam_jpg_url.rfind('/')
        
      except urllib2.URLError:
        pass
        #print "URLError"
      except urllib2.HTTPError:
        pass
        #print "HTTPError"
      except socket.timeout:
        pass
        #print "socket.timeout"
      

ids_urls = {}
id_range = range(start_id, end_id)

iterations = 0
while True:
    ids_we_have = set(ids_urls.keys())
    ids_we_need = set()
    # get a set of ids in small groups so we don't have too many threads
    for id in id_range:
        if id not in ids_we_have:
            # search for max 200 items at once
            if len(ids_we_need) < 200:
                ids_we_need.add(id)
            else:
                break

    if len(ids_we_need) == 0:
        break    

    #print "WE NEED:", ids_we_need

    testits = []
    for id in ids_we_need:
        t = testit(id)
        t.start()
        testits.append(t)

    while True:
        nbr_alive = 0
        for t in testits:
            if t.is_alive():
                # if we've had too many iterations then maybe
                # a thread has hung, we break and start again
                if iterations == 5:
                    print "KILLING threads"
                    break
                else:
                    nbr_alive += 1
        print "Alive", nbr_alive, ", iterations", iterations
        if nbr_alive == 0:
            iterations = 0
            break
        else:
            time.sleep(10)
            iterations += 1

    # now everything has finished...
    for t in testits:
        if t.url != None:
            ids_urls[t.id] = t.url
    got_keys = ids_urls.keys()    
    got_keys.sort()
    print "GOT:", got_keys[:5], '...', got_keys[-5:], 'of ', len(got_keys)

print 
print "Final results"
print ids_urls.keys()

ids_file = file('id_map.txt', 'w')
for cam_id in id_range:
    cam_jpg_url = ids_urls[cam_id]
    last_slash = cam_jpg_url.rfind('/')
    file_name = cam_jpg_url[last_slash+1:]
    
    ids_file.write('%d,%s\n' % (cam_id, file_name))
ids_file.close()    
