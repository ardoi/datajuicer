import os

import numpy as n

from scipy import diff
from scipy.interpolate import interp1d

from lsjuicer.util import helpers
from lsjuicer.data.transient import TransientGroup, Transient
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
        if mimage.event_times is not None:
            event_times = [el - mimage.timestamps[0] for el in mimage.event_times]
        else:
            event_times = []
        #imagedata.timestamps = timestamps
        #imagedata.event_times = event_times
        ImageDataMaker._data_from_mimage_data(mimage_data, imagedata)
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
        print linescan_data
        return imagedata



    @staticmethod
    def _data_from_imagedata(imagedata, existing, cut = ()):
        imagedata.all_image_data = {}
        #FIXME
        if cut:
            l,r,b,t = cut
            print 'cutting', l,r,b,t
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
        #print 'data is',mimage_data.shape,mimage_data
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


    def __init__(self, mimage):
        self.mimage = mimage
        self.timestamps = None
        self.event_times = None
        self.space_origin = 0.0
        self.time_origin = 0.0
        self.all_image_data = None
        self._delta_time = None

    def replace_channels(self, new_image):
        self.all_image_data = new_image.copy()
    def replace_channel(self, new_image, channel=0):
        self.all_image_data={channel:new_image.copy()}

class ImageDataLineScan(ImageData):
    def __init__(self, mimage):
        super(ImageDataLineScan, self).__init__(mimage)
        #self.check_for_gaps()

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

class ImageDataFrameScan(ImageData):
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


class Fl_Data:
    def __init__(self, array, phys, coords, av = [], bl_per_transient = False):
        self.coords = coords
        self.av_mean = 1
        self.calculate_bl = False

        if len(coords) == 0:
            #use whole image
            self.coords = [0,array.shape[1]-1,0,array.shape[0]-1]

        #take slice of array
        print 'coords',self.coords
        print 'darray', array
        if len(self.coords)==2:
            self.data = array
        elif self.coords[2] == 0 and self.coords[3]==0:
            self.data = array[:,self.coords[0]:self.coords[1]]
        else:
            self.data  = array[self.coords[2]:self.coords[3],self.coords[0]:self.coords[1]]
        if isinstance(av,list):
            print 'av is list',av
            if len(av) == 4:
                if sum(av[3:4])>0:
                    av_data  = array[av[2]:av[3],av[0]:av[1]]
                    print '2d',av_data
                    self.av_mean = n.mean(av_data)
                    if av[3]==av[2] and av[0]==av[1]:
                        #if no av roi
                        self.av_mean = 1
                else:
                    #1d case
                    av_data = array[:,av[0]:av[1]]
                    print array
                    print '1d',av_data
                    self.av_mean = n.mean(av_data)
                    if av[3]==av[2] and av[0]==av[1]:
                        #if no av roi
                        self.av_mean = 1
        elif av==None:
            print 'calculate'
#            self.av_mean = n.mean(self.data)
            self.av_mean = 1.0
        else :
            print 'av is number'
            self.av_mean = av
        if bl_per_transient == True:
            self.calculate_bl = True
        fl_list = []
        row_len = self.data.shape[0]
        #print 'rows',row_len,self.av_mean,self.data.shape
        #print 'data',self.data
        for row in self.data.transpose():
            assert len(row)==row_len
            fl_list.append( (sum(row) / row_len - self.av_mean) / self.av_mean + 1)
        if len(self.coords)==2:
            self.x_axis_values = range(0,self.coords[1])
        else:
            self.x_axis_values  = range(self.coords[0],self.coords[1])#pixel numbers

        self.fld = fl_list
        self.offset = self.x_axis_values[0]
        self.physical_x_axis_values  = helpers.shiftList(n.array(phys), self.offset)
        #self.phys = phys
        self.fl_func = interp1d(self.physical_x_axis_values.data,helpers.smooth(n.array(fl_list),1),kind='slinear')
        if 1:
            self.fl = helpers.shiftList(self.fl_func(phys),self.offset)
        #self.mx = []
        #self.my = []
        #self.xlim = 0
        #self.ylim = 0
        self.taus = []
        self.halftimes = []

    def set_events(self,all_events):
        self.events=[]
        for event in all_events:
            if event >self.physical_x_axis_values.data[0] and event < self.physical_x_axis_values.data[-1]:
                self.events.append(event)
    def set_gaps(self, all_gaps):
        self.gaps=[]
        for gap in all_gaps:
            if gap >self.physical_x_axis_values.data[0] and gap < self.physical_x_axis_values.data[-1]:
                self.gaps.append(gap)
    def addTransientGroup(self,tg):
        if not hasattr(self,'transientGroup'):
            self.transientGroup = tg
        else:
            self.transientGroup.append(tg)
            print 'done adding transient'
    def index_2_val(self,x):
        return self.phys_coords[0]+(x - self.x_axis_values[0])*self.phys_step

    #def val_2_index_x(self,v):
    #    return int((v - self.phys_coords[0])/self.phys_step + self.x_axis_values[0])

    #def val_2_index_y(self,v):
    #    return (v - self.phys_coords[2])/self.phys_step_y + self.y_axis_values[0]



    def get_limit(self, x):
        #limit function max_limit is given in physical coordinates so pixels cant be used
        return self.max_limit(x)


    #def deriv(self,x,y):
    #    dx = n.diff(x)
    #    dy = n.diff(y)
    #    der = []
    #    for x,y in zip(dx,dy):
    #        #print x,y,y/x
    #        der.append(y/x)
    #    return n.array(der)

    def find_phys_index(self,val):
        print 'total ',len(self.physical_x_axis_values.data)
        print 'looking for',val
        try:
            print 't1'
            ind = self.physical_x_axis_values.index(val) + 0*self.offset
            return ind
        except:
            print 't2'
            for i in range(len(self.physical_x_axis_values.data)-1):
                if self.physical_x_axis_values.data[i+1]>val and self.physical_x_axis_values.data[i]<=val:
                    return i+0*self.offset
            print 'error'

    def make_transient(self,edges, phys_coords = False):
        if phys_coords:
            start = self.find_phys_index(edges[0])
            end = self.find_phys_index(edges[1])
        else:
            start = edges[0]
            end = edges[1]
        return Transient(self.smoothed.data[start:end],start,end,self.physical_x_axis_values.data[start:end],self,self.calculate_bl)

    def make_transients(self,all_edges,physical_coords = False):
        tG = TransientGroup(self)

        #max_ys = []
        #if self.calculate_bl:
        #    max_ybs = []
        #max_xs = []
        for edge in all_edges:
            transient = self.make_transient(edge, physical_coords)
            tG.addTransient(transient)
            #max_ys.append(transient.max_y)
            #max_xs.append(transient.max)
            #if self.calculate_bl:
            #    max_ybs.append(transient.max_y_bl)
        return tG
        #self.mx = max_xs
        #self.my = max_ys
        #if self.calculate_bl:
        #    self.myb = max_ybs
        #self.pmx = [self.physical_x_axis_values[x] for x in self.mx]

    def find_transients(self,start,end,smooth_val):
        data = helpers.smooth(self.smoothed.data,smooth_val)
        f = data
        d1 = diff(data)
        d2 = diff(d1)
        zeros0 = []
        last = d1[0]
        index = 0
        for d,dd in zip( d1[1:], d2):
            phys_x = self.physical_x_axis_values.data[index]
            index +=1
            if (phys_x < start or phys_x > end):
                #if phys_x out of search range continue
                continue
            if d * last < 0.0 and dd > 0:
                #if the sign of the derivative changes and second derivative is >0 then we have local minimum
                zeros0.append(index)
            last = d
        #second run
        #make sure that each zero is in actual minimum, if not then adjust

        #third run
        #determine which zero is start/end of a transient
        dm = []
        for z in range(1,len(zeros0)):
            b0 = zeros0[z-1]
            b1 = zeros0[z]
            dm.append(max(f[b0:b1])-max(f[b0],f[b1]))
        avdm = n.mean(dm)
        #zeros = []
        starts = []
        ends = []
        amnt = 0.15
        for z in range(1,len(zeros0)):
            b0 = zeros0[z-1]
            b1 = zeros0[z]
            if max(f[b0:b1]) - max(f[b0], f[b1]) > amnt * avdm :
                starts.append(b0)
                ends.append(b1)

        for i in range(len(starts)):
            z = starts[i]
            #search_range = 5
            zero_value = self.smoothed.data[z]
            k = 1
            new_z_left = z
            new_z_right = z
            left_val = zero_value
            right_val = zero_value
            while self.smoothed.data[z - k] < zero_value:
                #look left
                new_z_left = z - k
                k += 1
            if k != 1:
                #add 1 cause during while the last step is invalid
                new_z_left += 1
            left_val = self.smoothed.data[new_z_left]
            k = 1
            while self.smoothed.data[z + k] < zero_value:
                #look right
                new_z_right = z + k
                k += 1
            if k != 1:
                #subtract 1 cause during while the last step is invalid
                new_z_right -= 1
            right_val = self.smoothed.data[new_z_right]
            if new_z_left == new_z_right == z:
                #we already were at minimum
                continue
            elif left_val< right_val:
                print 'adjusted left %i,%f to %i,%f'%(z,zero_value,new_z_left,left_val)
                starts[i] = new_z_left
            else:
                print 'adjusted right %i,%f to %i,%f'%(z,zero_value,new_z_right,right_val)
                starts[i] = new_z_right

        for i in range(len(ends)):
            z = ends[i]
            #search_range = 5
            zero_value = self.smoothed.data[z]
            k = 1
            new_z_left = z
            new_z_right = z
            left_val = zero_value
            right_val = zero_value
            while self.smoothed.data[z - k] < zero_value:
                #look left
                new_z_left = z - k
                k += 1
            if k != 1:
                #add 1 cause during while the last step is invalid
                new_z_left += 1
            left_val = self.smoothed.data[new_z_left]
            k = 1
            while self.smoothed.data[z + k] < zero_value:
                #look right
                new_z_right = z + k
                k += 1
            if k != 1:
                #subtract 1 cause during while the last step is invalid
                new_z_right -= 1
            right_val = self.smoothed.data[new_z_right]
            if new_z_left == new_z_right == z:
                #we already were at minimum
                continue
            elif left_val< right_val:
                print 'adjusted left %i,%f to %i,%f'%(z,zero_value,new_z_left,left_val)
                ends[i] = new_z_left
            else:
                print 'adjusted right %i,%f to %i,%f'%(z,zero_value,new_z_right,right_val)
                ends[i] = new_z_right

        edges = []
        for s,e in zip(starts,ends):
            edges.append([s,e])
        return self.make_transients(edges)

    def get_max_index(self,start,end):
        max = -1e6
        ind = None
        phys_offseted = helpers.shiftList(self.x_axis_values,self.offset)
        for x,val in zip(phys_offseted[start:end],self.smoothed[start:end]):
            if val > max:
                max = val
                ind = x
        return max,ind


    def calc_A1A2(self,min_delay):
        self.ratios =[]
        self.A2A1_ratios = []
        self.A2A1_delays = []
        for i in range(1,len(self.pmx)):
            delay = self.pmx[i]-self.pmx[i-1]
            if i == 1:
                self.ratios.append([(i-1,i),self.myb[i]/self.myb[i-1],delay])
                self.A2A1_ratios.append(self.myb[i]/self.myb[i-1])
                self.A2A1_delays.append(delay)
            else:
                previous_delay =  self.pmx[i-1]-self.pmx[i-2]
                if previous_delay>min_delay:
                    self.ratios.append([(i-1,i),self.myb[i]/self.myb[i-1],delay])
                    self.A2A1_ratios.append(self.myb[i]/self.myb[i-1])
                    self.A2A1_delays.append(delay)


    def find_start_end(self,x,percentage):
        """Find start and end positions of transient peaking at position x."""
        #find start
        min = self.smoothed[x]
        start_index = x
        index = 0
        search_active = False
        #go back till F goes below limit and then find minimum until F goes above limit again
        while True:
            #print x,index,self.offset
            if x-index > self.offset:
                F_val = self.smoothed[x - index]
                #print F_val,x-index
                if F_val > self.max_limit(self.physical_x_axis_values[x - index]):
                    if not search_active:
                        #not yet below limit, continue
                        index += 1
                        continue
                    if search_active:
                        #went above limit during searching, meaning we have reached the other end. break
                        break
                else:
                    search_active = True
                    if F_val < min:
                        #found new minimum. store it
                        min = F_val
                        start_index = x - index
                    index += 1
            else:
                #we went too far back over the ROI window
                break
        start_val = self.smoothed[start_index]
        #find end
        end_criteria = percentage
        #end is where (F-F0)/(F_max-F0) = end_criteria. F0 = start_val
        index = 0
        end_index = x
        F_max = self.smoothed[x]
        min_val = F_max
        crossings = 0
        while True:
            if x+index < self.x_axis_values[-1] and crossings < 2:
                #make sure we are not out of ROI range nor that we have not started climbing a new transient
                F_val = self.smoothed[x + index]
                if (F_val - start_val)/(F_max-start_val) < end_criteria:
                    end_index = x+index
                    break
                if (F_val - self.max_limit(self.physical_x_axis_values[x+index]))*(self.smoothed[x + index - 1] - self.max_limit(self.physical_x_axis_values[x+index-1])) <0:
                    #val-limit would have different signs during consequtive steps if we crossed the limit line
                    crossings += 1
                if F_val < min_val:
                    min_val = F_val
                    end_index = x + index
                index += 1
            else:
                #we went too far back over the ROI window,take the last value as end point
                print 'End criteria %f not reached. Stopped at x=%i for max at x=%i with ratio %f'\
                        %(end_criteria,end_index,x,(min_val-start_val)/(F_max-start_val))
                break
        return start_index,end_index

    def find_halftimes(self):
        self.halftimes = self.transientGroup.find_halftimes()

    def fit_taus(self):
        self.taus = self.transientGroup.fit_taus()

    def smooth(self, times = 1, wl = [10], win = 'blackman'):
        self.smoothed = n.array(self.fl.data)
        for i in range(times):
            self.smoothed = helpers.smooth(self.smoothed, window_len = wl[i], window = win)
        self.smoothed = helpers.shiftList(self.smoothed,self.offset)
