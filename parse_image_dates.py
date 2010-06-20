import datetime

# open the file of ids and datetime-filenames
f = open('id_map.txt', 'rt')
for l in f:
    # split into id and filename
    comma = l.find(',')
    id = int(l[:comma])
    file_name = l[comma+1:]
    # check we're dealing with the filename we expect
    pattern = 'TheSkiffCam_'
    assert file_name.startswith(pattern)
    dt = file_name[len(pattern):-5]
    year = int(dt[0:4])
    month = int(dt[5:7])
    day = int(dt[8:10])
    hour = int(dt[11:13])
    minute = int(dt[14:16])
    file_date = datetime.datetime(year, month, day, hour, minute)
    # now we have:
    # int id
    # datetime.datetime for file based on its filename
    print '%d,%s' % (id, file_date)

f.close()
