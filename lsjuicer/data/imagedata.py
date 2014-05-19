import os
import numpy as n

from lsjuicer.util import helpers
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
from lsjuicer.inout.db import sqla as sa

class ImageDataMaker(object):
    @staticmethod
    def from_microscopeimage(mimage):
        mimage_data = mimage.image_data("Pixels")["ImageData"]
        print mimage_data.shape
        if mimage_data.shape[1]>1:
            id_class = ImageDataFrameScan
        else:
            id_class = ImageDataLineScan
        print "id class =",id_class
        imagedata = id_class(mimage)

        if mimage.timestamps is not None:
            ts = mimage.timestamps
            timestamps = [el - ts[0] for el in ts]
            imagedata.timestamps = timestamps
        #if mimage.event_times is not None:
        #    event_times = [el - mimage.timestamps[0] for el in mimage.event_times]
        #else:
        #    event_times = []
        #imagedata.event_times = event_times
        ImageDataMaker._data_from_mimage_data(mimage_data, imagedata)
        print 'dims: x={} y={}'.format(imagedata.x_points,imagedata.y_points)
        return imagedata

    @staticmethod
    def from_pixelfitimage(image):
        image_data = image.image_data()
        if image_data.shape[1]>1:
            id_class = ImageDataFrameScan
        else:
            id_class = ImageDataLineScan
        imagedata = id_class(image)
        ImageDataMaker._data_from_mimage_data(image_data, imagedata)
        return imagedata


    @staticmethod
    def from_db_image(image):
        if isinstance(image, sa.MicroscopeImage):
            return ImageDataMaker.from_microscopeimage(image)
        elif isinstance(image, sa.PixelFittedSyntheticImage):
            return ImageDataMaker.from_pixelfitimage(image)
        else:
            raise ValueError()

    @staticmethod
    def from_imagedata(existing, cut = ()):
        if cut:
            l, r, b, t = cut
        im_class = existing.__class__
        imagedata = im_class(existing.mimage)
        if existing.timestamps is not None:
            if cut:
                imagedata.timestamps = existing.timestamps[l:r]
            else:
                imagedata.timestamps = existing.timestamps
        if existing.event_times is not None:
            if cut:
                imagedata.event_times = existing.event_times[l:r]
            else:
                imagedata.event_times = existing.event_times
        ImageDataMaker._data_from_imagedata(imagedata, existing, cut)
        return imagedata

    def linescan_from_framescan(self, existing, linescan_data):
        imagedata = ImageDataLineScan(existing.mimage)
        #print existing, existing.delta_time,linescan_data.shape
        imagedata.timestamps = existing.delta_time*n.arange(linescan_data.shape[3])
        imagedata.all_image_data = linescan_data
        #print imagedata.timestamps,imagedata.timestamps.shape
        return imagedata



    @staticmethod
    def _data_from_imagedata(imagedata, existing, cut = ()):
        if cut:
            raise NotImplementedError
            l,r,b,t = cut
            for c in existing.channels:
                imagedata.all_image_data.update({c:existing.all_image_data[c][b:t, l:r]})
            imagedata.space_origin = existing.yvals[b]
        else:
            #for c in existing.channels:
            #    imagedata.all_image_data.update({c:existing.all_image_data[c].copy()})
            imagedata.all_image_data = existing.all_image_data.copy()
            imagedata.space_origin = existing.space_origin

    @staticmethod
    def _data_from_mimage_data(mimage_data, imagedata):
        print 'data is',mimage_data.shape,mimage_data
        imagedata.all_image_data = mimage_data
        imagedata.space_origin = 0.0
        imagedata.time_origin = 0.0


class ImageData(object):
    """Intermediate class between MicroscopeImage and Pixmap"""
    @property
    def acquisitions(self):
        """The number of frames in a framescan or lines in a linescan"""
        if self.frames == 1:
            #if we have a linescan, return the
            return self.x_points
        else:
            return self.frames
    @property
    def x_points(self):
        return self.all_image_data.shape[3]
    @property
    def y_points(self):
        return self.all_image_data.shape[2]
    @property
    def pixels(self):
        return self.x_points*self.y_points
    @property
    def channels(self):
        return self.all_image_data.shape[0]
    @property
    def channel_names(self):
        return self.mimage.channel_names
    @property
    def frames(self):
        return self.all_image_data.shape[1]
    @property
    def delta_space(self):
        return self.mimage.delta_space
    @property
    def delta_time(self):
        if self._delta_time:
            return self._delta_time
        else:
            return self.mimage.delta_time
    @property
    def info_txt(self):
        return self.mimage.description
    @property
    def notes(self):
        return self.mimage.notes
    @property
    def filedir(self):
        return os.path.dirname(self.mimage.file_name)
    @property
    def name(self):
        return os.path.splitext(self.mimage.file_name)[0]
    @property
    def ome_sha1(self):
        return self.mimage.file_hash
    @property
    def pixel_size(self):
        print "\n\n\n\nGetting pixel data"
        print self.mimage.get_pixel_size("Pixels")
        return self.mimage.get_pixel_size("Pixels")
    @property
    def all_image_data(self):
        return self._all_image_data

    @all_image_data.setter
    def all_image_data(self, data):
        self._all_image_data = None
        if  data.shape[3] < data.shape[2]:
            #have to transpose frames because we want the ImageData frame to be longer in the
            #horizontal axis than in vertical (for display purposes)
            print 'Transposing'
            channels = data.shape[0]
            frames = data.shape[1]
            width = data.shape[2]
            height = data.shape[3]
            self._all_image_data = n.zeros_like(data)
            self._all_image_data.shape = (channels, frames, height, width)
            print 'old shape {}\t new shape {}'.format(data.shape, self._all_image_data.shape)
            for channel in range(channels):
                for frame in range(frames):
                    self._all_image_data[channel][frame]=data[channel][frame].transpose()
        else:
            self._all_image_data = data

    def __init__(self, mimage):
        self.mimage = mimage
        self.timestamps = None
        self.event_times = None
        self.space_origin = 0.0
        self.time_origin = 0.0
        self._all_image_data = None
        self._delta_time = None

    def replace_channels(self, new_image):
        self.all_image_data = new_image.copy()
    def replace_channel(self, new_image, channel=0):
        #self.all_image_data={channel:new_image.copy()}
        self.all_image_data[channel]=new_image

class ImageDataLineScan(ImageData):
    def __init__(self, mimage):
        super(ImageDataLineScan, self).__init__(mimage)
        #self.check_for_gaps()

    #@property
    #def x_points(self):
    #    return 1
    @property
    def xvals(self):
        return self.timestamps
    @property
    def yvals(self):
        return n.arange(self.y_points)*self.delta_space + self.space_origin
    def check_for_gaps(self):
        print '::Name::',self.name,self.filedir,self.ome_sha1
        diffs = n.diff(self.timestamps)
        gaps,mean = helpers.find_outliers(diffs)
        self.timestamps, gaps, removed = helpers.remove_bad_gaps(self.timestamps, gaps, mean)
        print 'rem', removed
        #if removed:
        #    QG.QMessageBox.warning(None, 'Alert', '%i line intervals have been corrected in the file'%removed)
        self.gaps = [self.timestamps[gap] for gap in gaps.keys()]
        self.interval = mean  #make interval in msec
        self._delta_time = self.interval

    def get_traces(self, kwargs):
        out = []
        y0 = kwargs['y0']
        y1 = kwargs['y1']
        dy = kwargs['dy']
        #in a linescan the time is given on the x axis
        t0 = kwargs['t0']
        t1 = kwargs['t1']
        for y in range(y0, y1):
            data = self.trace_in_time(y, dy, t0, t1)
            out.append({'data':data, 'coords':(0, y - y0)})
        return out

    def get_trace(self, kwargs):
        y = kwargs['y']
        dy = kwargs['dy']
        #in a linescan the time is given on the x axis
        t0 = kwargs['t0']
        t1 = kwargs['t1']
        trace = self.trace_in_time( y, dy, t0, t1)
        return trace

    def trace_in_time(self, center_y, height, start, end):
        """give a slice through time for give coordinates"""
        #to accommodate n slicing we have to fix the indices
        if height:
            bottom = center_y - height
            top = center_y + height + 1
        else:
            bottom = center_y
            top = bottom + 1
        dd = self.all_image_data[0, 0, bottom:top, start:end]
        if height == 1:
            #weigh the central pixel equally to all surrounding ones
            w = n.ones(shape=3)*1/2.
            w[1] = 1
            data = n.average(dd, axis=0, weights=w)
        else:
            raise ValueError('wrong height %i'%height)
            #data = dd.mean(axis=1).mean(axis=1)
        return data


class ImageDataFrameScan(ImageData):
    def get_trace(self, kwargs):
        x = kwargs['x']
        y = kwargs['y']
        dx = kwargs['dx']
        dy = kwargs['dy']
        t0 = kwargs['t0']
        t1 = kwargs['t1']
        trace = self.trace_in_time(x, y, dx, dy, t0, t1)
        return trace

    def get_traces(self, kwargs):
        out = []
        x0 = kwargs['x0']
        x1 = kwargs['x1']
        y0 = kwargs['y0']
        y1 = kwargs['y1']
        dx = kwargs['dx']
        dy = kwargs['dy']
        t0 = kwargs['t0']
        t1 = kwargs['t1']

        for x in range(x0, x1):
            for y in range(y0, y1):
                data = self.trace_in_time(x, y, dx, dy, t0, t1)
                out.append({'data':data, 'coords':(x -x0, y -y0)})
        return out

    @property
    def xvals(self):
        try:
            return n.arange(self.x_points)*self.delta_space + self.space_origin
        except:
            return n.arange(self.x_points) + self.space_origin
    @property
    def yvals(self):
        try:
            return n.arange(self.y_points)*self.delta_space + self.space_origin
        except:
            return n.arange(self.y_points) + self.space_origin

    def get_pseudo_linescan(self, selection):
        line = selection[ISTN.LINE][0]
        timerange = selection[ISTN.TIMERANGE]
        start = timerange['start']
        end = timerange['end']
        frames = end-start
        lineitem = line.graphic_item
        #print '\nline',line
        linef = lineitem.line()
        #print '\nselection',lineitem, linef, linef.p1(), linef.p2()
        p1 = linef.p1()
        p2 = linef.p2()
        #we should only create more pixels than we have. For this the maximum number of pixels either in x or y direction is used for number of new points to be calculated
        points = int(max(abs(p1.x()-p2.x()),abs(p1.y()-p2.y())))
        print 'using %i points'%points,abs(p1.x()-p2.x()),abs(p1.y()-p2.y()),n.sqrt((p1.x()-p2.x())**2.+(p1.y()-p2.y())**2.)
        xvals = n.linspace(p1.x(), p2.x(), points).astype(int)
        yvals = n.linspace(p1.y(), p2.y(), points).astype(int)
        #print xvals, yvals
        linescan_data = n.zeros(shape=(self.channels, 1, points, frames),dtype='float32') #print 'channels', self.channels
        for channel in range(self.channels):
            for frame in range(start, end):
                fdata = self.all_image_data[channel][frame]
                new_line = fdata[yvals,xvals]
                linescan_data[channel][0][:,frame-start]=new_line
        id_maker = ImageDataMaker()
        new_image = id_maker.linescan_from_framescan(self, linescan_data)
        return new_image

    def trace_in_time(self, center_x, center_y, width, height, start, end):
        """give a slice through time for give coordinates"""
        #to accommodate n slicing we have to fix the indices
        if width:
            left = center_x - width
            right = center_x + width + 1
        else:
            left = center_x
            right = left + 1
        if height:
            bottom = center_y - height
            top = center_y + height + 1
        else:
            bottom = center_y
            top = bottom + 1
        dd = self.all_image_data[0, start:end, bottom:top, left:right]

        if width == 1 and height == 1:
            #weigh the central pixel equally to all surrounding ones
            w = n.ones(shape=(3,3))*1/8.
            w[1,1]=1
            ww = n.array((w,)*(end-start))
            ww2 = ww.sum(axis=1)
            data = n.average(n.average(dd, axis=2, weights=ww),axis=1,weights=ww2)
        else:
            data = dd.mean(axis=1).mean(axis=1)
        return data

    def get_time_average_linescan(self, selection):
        """Gives out a linescan image that will be used by FluorescenceTab for average F calculation."""
        roi = selection[ISTN.ROI][0]
        roiitem = roi.graphic_item
        rect = roiitem.rect()
        print 'roi',roi,roiitem, rect
        linescan_data = n.zeros(shape=(self.channels, 1, 1, self.frames),dtype='float32')
        for channel in range(self.channels):
            #collapse all data into 1xframes dimensional array
            data = self.all_image_data[channel,:,rect.top():rect.bottom(), rect.left():rect.right()].mean(axis=1).mean(axis=1)
            linescan_data[channel][0]=data
        id_maker = ImageDataMaker()
        new_image = id_maker.linescan_from_framescan(self, linescan_data)
        return new_image
