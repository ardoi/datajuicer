import numpy
from abstractreader import AbstractReader

class CSVReader(AbstractReader):
    def read(self):
        f=None
        try:
            f = open(self.filename, 'r')
        except IOError:
            print 'file %s does not exist'%self.filename
        lines = f.readlines()
        timeindex = 0
        dataindex = 1
        time = []
        data = []
        #start_comment = "CORRECTED ABSORBANCES"
        #data_reached = False
        for line in lines:
            #if start_comment in line:
            #    data_reached = True
            #    continue
            #if not data_reached:
            #    continue
            #else:
            try:
                ldata = line.split(',')
                #print ldata
                time.append(float(ldata[timeindex].strip()))
                data.append(float(ldata[dataindex].strip()))
            except ValueError:
                pass
        self.image_in = True
        self.image_step_y = 1.0
        self.image_width = len(time)
        #so that pixmap showing would work. otherwise we'd have an 1xn pixmap
        self.image_height = int(self.image_width*0.6)
        self.interval = time[1]-time[0]
        self.timestamps = numpy.array(time)
        array_data = numpy.array(data)
        self.im_data = numpy.vstack((array_data,)*self.image_height)
        #print self.im_data
        #if self.im_data.min()<0:
        #    self.im_data = self.im_data + 2 * abs(self.im_data.min())
        self.im_data.shape=(self.image_height,self.image_width)
        self.data_loaded = True
        self.converted = True





