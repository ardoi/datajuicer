import PyQt4.QtCore as QC
import PyQt4.QtGui as QG
import numpy as n
import scipy.interpolate as si
import scipy.optimize as so

from lsjuicer.util import helpers
from lsjuicer.data.transient import SparkTransient, SparkSpatialProfile

class SparkData(QC.QObject):

    def _temporal_smoothing_set(self, value):
        self._temporal_smoothing = int(value)
        self.set_temporal_data()
    def _temporal_smoothing_get(self):
        return self._temporal_smoothing

    def _spatial_smoothing_set(self, value):
        self._spatial_smoothing = int(value)
        self.set_spatial_data()
    def _spatial_smoothing_get(self):
        return self._spatial_smoothing

    def _F0_left_get(self):
        return self._F0_left
    def _F0_left_set(self, value):
        self._F0_left = value

    def _F0_right_get(self):
        return self._F0_right
    def _F0_right_set(self, value):
        self._F0_right = value

    def _v_loc_get(self):
        return self._v_loc
    def _v_loc_set(self, value):
        self._v_loc = value
        self.set_temporal_data()

    def _v_halfspan_get(self):
        return self._v_halfspan
    def _v_halfspan_set(self, value):
        self._v_halfspan = value
        self.set_temporal_data()

    def _h_loc_get(self):
        return self._h_loc
    def _h_loc_set(self, value):
        self._h_loc = value
        print 'setting hloc to', value
        self.set_spatial_data()

    def _h_halfspan_get(self):
        return self._h_halfspan

    def _h_halfspan_set(self, value):
        self._h_halfspan = value
        self.set_spatial_data()

    def _F0_get(self):
        #return 1.0
        return self.av_mean
        F0_settings = (self.F0_left, self.F0_right, self.v_loc, self.v_halfspan)
        if F0_settings == self.F0_settings:
            #nothing has to be done. Old F0 value will be returned
            pass
        else:
            self.F0_settings = F0_settings
            if self.v_halfspan > 0:
                data_slice = self.data[
                        self.v_loc - self.v_halfspan - 1: self.v_loc + self.v_halfspan, :]
                data = data_slice.sum(axis = 0)/(1. + 2*self.v_halfspan)
            else:
                data_slice = n.zeros(1)
                data = self.data[self.v_loc, :]
            self._F0 = data[self.F0_left : self.F0_right].mean()
        return self._F0


    F0_left = property(fget = _F0_left_get, fset = _F0_left_set)
    F0_right = property(fget = _F0_right_get, fset = _F0_right_set)
    v_loc = property(fget = _v_loc_get, fset = _v_loc_set)
    h_loc = property(fget = _h_loc_get, fset = _h_loc_set)
    v_halfspan = property(fget = _v_halfspan_get, fset = _v_halfspan_set)
    h_halfspan = property(fget = _h_halfspan_get, fset = _h_halfspan_set)
    F0 = property(fget = _F0_get)
    temporal_smoothing = property(fget = _temporal_smoothing_get, fset = _temporal_smoothing_set)
    spatial_smoothing = property(fget = _spatial_smoothing_get, fset = _spatial_smoothing_set)

    def __init__(self, imagedata, roi, bg_roi = None, im_mean = None,
                 new_image=None, max_roi = None, max_mask=None,
                 dilated_mask=None, raw_data=None):
        super(SparkData, self).__init__(None)
        self.coords = roi
        self.max_coords = max_roi
        self.av_mean = im_mean
        self.imagedata = imagedata
        self.time_interval = imagedata.delta_time
        self.pixel_size = imagedata.delta_space
        channels = imagedata.channels
        if new_image is None:
            imagearray = imagedata.all_image_data[channels[0]]
        else:
            imagearray = new_image
        self.data  = imagearray[self.coords[2]:self.coords[3],
                self.coords[0]:self.coords[1]].astype('float')
        #print raw_data, self.coords
        self.raw_data  = raw_data[self.coords[2]:self.coords[3],
                self.coords[0]:self.coords[1]].astype('float')
        if self.max_coords:
            self.max_data  = imagearray[self.max_coords[2]:self.max_coords[3],
                self.max_coords[0]:self.max_coords[1]].astype('float')
            #print self.max_data.shape, self.data.shape
        else:
            self.max_data = None
        #print 'shapes:',new_image.shape, dilated_mask.shape, max_mask.shape
        #get the mask id from the max mask
        self.max_mask = max_mask[self.max_coords[2]:self.max_coords[3],
                self.max_coords[0]:self.max_coords[1]]
        count = n.bincount(self.max_mask.flatten())
        count[0] = 0
        spark_no_in_mask = count.argmax()
        #print 'mask id',spark_no_in_mask
        self.dilated_mask =( dilated_mask[self.coords[2]:self.coords[3],
                self.coords[0]:self.coords[1]]==spark_no_in_mask).astype(float)

        phys = imagedata.timestamps[roi[0]:roi[1]]
        self.phys = n.array(phys) #in ms

        if bg_roi is not None and self.av_mean is None:
            #print 'av is list',bg_roi
            if sum(bg_roi[3:4])>0:
                av_data  = n.array[bg_roi[2]:bg_roi[3],
                        bg_roi[0]:bg_roi[1]]
                #print '2d',av_data
                self.av_mean = n.mean(av_data)
                if bg_roi[3]==bg_roi[2] and bg_roi[0]==bg_roi[1]:
                    #if no av roi
                    print 'faulty bgroi'
                    self.av_mean = 1
        self.x_axis_physical_values = imagedata.xvals[self.coords[0]:self.coords[1]] # show and fit in milliseconds
        self.y_axis_physical_values = imagedata.yvals[self.coords[2]:self.coords[3]]

        self._F0_left = 0
        self._F0_right = self.data.shape[1]-1
        self.F0_settings = None
        self._v_loc = int(self.data.shape[0]/2.)
        self._h_loc = int(self.data.shape[1]/2.)
        self._v_halfspan = 1
        self._h_halfspan = 1
        self._temporal_smoothing = 1
        self._spatial_smoothing = 1
        self.name = 'Spark ROI'
        self.approved = False

        self.make_icon()

    def set_approved(self, state):
        self.approved = state
        self.make_icon()

    def make_icon(self):
        if self.approved:
            colorname = 'green'
        else:
            colorname = 'red'
        iconpixmap = QG.QPixmap(20,20)
        iconpixmap.fill(QG.QColor(colorname))
        self.icon = QG.QIcon(iconpixmap)

    def set_name_from_number(self, n):
        self.name = "Spark ROI %i"%n

    def estimate_temporal_span(self, span_needed = 10.0):
        #span in TIME used to calculate the spatial profile
        interval = self.time_interval
        print 'inteval', self.time_interval,span_needed
        #span_needed = 10.0 #ms
        n = int(round((span_needed / interval -1.)/2.))
        print 'temporal span=', n
        return n

    def estimate_spatial_span(self, span_needed = 1.8):
        #span in SPACE used to calculate the temporal profile
        pixelsize = self.pixel_size
        #span_needed = 1.0 #um
        n = int(round((span_needed / pixelsize -1.)/2.))
        print 'spatial span',n
        return n

    def find_max_loc(self):
        if self.max_data is not None:
            ind = n.unravel_index(self.max_data.argmax(), self.max_data.shape)
            ind = (ind[0] + self.max_coords[2]-self.coords[2],
                    ind[1]+self.max_coords[0]-self.coords[0])
        else:
            ind = n.unravel_index(self.data.argmax(), self.data.shape)
        return ind

    def get_max_loc(self):
        return self.find_max_loc()
        halfspan = self.v_halfspan
        rows = self.data.shape[0]
        max_val = 0.0
        max_index = None
        max_index_horizontal = None
        for vloc in range(halfspan+1,rows-halfspan+1):
            data_slice = self.data[vloc-halfspan-1:vloc+halfspan, :]
            data = data_slice.sum(axis=0)/(1.+2*halfspan)
            if data.max() > max_val:
                max_index = vloc
                max_val = data.max()
                max_index_horizontal = data.argmax()

        return rows-max_index, max_index_horizontal

    def estimate_sparkyness(self):
        return (0,0)
        halfspan = self.v_halfspan
        rows = self.data.shape[0]
        row_means = []
        for vloc in range(halfspan+1,rows-halfspan+1):
            data_slice = self.data[vloc-halfspan-1:vloc+halfspan, :]
            data = data_slice.sum(axis=0)/(1.+2*halfspan)
            row_means.append(data.mean())
        #print 'row means', row_means
        row_means = n.array(row_means)
        #print row_means.mean(), row_means.std()
        return row_means.mean(), row_means.std()



    def set_temporal_data(self):
        alldata=self.data
        if self.v_halfspan > 0:
            data_slice = alldata[
                    self.v_loc-self.v_halfspan-1:self.v_loc + self.v_halfspan, :]
            mask_slice = self.dilated_mask[
                    self.v_loc-self.v_halfspan-1:self.v_loc + self.v_halfspan, :]
            #data = data_slice.sum(axis=0)/(1.+2*self.v_halfspan)
            data, valid_slice  = helpers.masked_mean(data_slice, mask_slice, axis = 0)
        elif self.v_halfspan == 0:
            data_slice = n.zeros(1)
            data, valid_slice = helpers.masked_mean(alldata[self.v_loc, :],
                    self.dilated_mask[self.v_loc,:], axis=0)
        else:
            data, valid_slice = helpers.masked_mean(alldata, self.dilated_mask, axis=0)

        #self.temporal_data = data
        self.temporal_data = (data - 0*self.F0) / self.F0
        self.valid_t_slice = valid_slice
        #self.temporal_data = (data - self.F0) / self.F0 + 1.0
        if self.temporal_smoothing:
            self.temporal_smooth_data = helpers.smooth_times(self.temporal_data, times=self.temporal_smoothing)
        else:
            self.temporal_smooth_data = self.temporal_data
        #set time data for transient generation
        #self.temporal_axis_data = n.arange(self.data.shape[1])*\
        #        self.spark_data.time_interval#*1000

        #print self.spark_data.phys.tolist()
        #self.find_halfmax_span()
        #self.find_FDHM()

    def set_spatial_data(self):
        #self.h_loc = center_value
        #self.h_halfspan = halfspan
        #alldata=self.raw_data
        alldata=self.data
        if self.h_halfspan >0:
            data_slice = alldata[:,
                    self.h_loc - self.h_halfspan-1: self.h_loc + self.h_halfspan]
            #data = data_slice.sum(axis=1)/(1.+2*self.h_halfspan)
            mask_slice = self.dilated_mask[:,
                    self.h_loc - self.h_halfspan-1: self.h_loc + self.h_halfspan]
            #print self.data.shape, self.dilated_mask.shape, data_slice.shape, mask_slice.shape
            try:
                data,valid_slice = helpers.masked_mean(data_slice, mask_slice, axis = 1)
            except ValueError:
                #print 'set spatial error', data_slice, mask_slice, self.h_loc, self.h_halfspan,self.h_loc - self.h_halfspan-1, self.h_loc + self.h_halfspan
                #print alldata.shape, self.dilated_mask.shape
                #print alldata.tolist()
                #print self.dilated_mask.tolist()
                raise ValueError
        elif self.h_halfspan == 0:
            data_slice = n.zeros(1)
            data = alldata[:, self.h_loc]
            data,valid_slice = helpers.masked_mean(alldata[:,self.h_loc],
                    self.dilated_mask[:,self.h_loc], axis=1)
        else:
            data,valid_slice = helpers.masked_mean(alldata, self.dilated_mask, axis=1)
        try:
            self.spatial_data = (data - 0*self.F0) / self.F0
        except:
            import pdb
            pdb.set_trace()
        self.valid_s_slice = valid_slice
        if self.spatial_smoothing:
            self.spatial_smooth_data = helpers.smooth_times(self.spatial_data, times=self.spatial_smoothing)
        else:
            self.spatial_smooth_data = self.spatial_data
        #self.find_FWHM()


    def find_phys_index(self,val):
        try:
            ind = self.x_axis_physical_values.index(val)
            return ind
        except:
            for i in range(len(self.x_axis_physical_values)-1):
                if self.x_axis_physical_values[i+1]>val and self.x_axis_physical_values[i]<=val:
                    return i

    def make_spark(self, start_x_phys=None, end_x_phys=None):
        if start_x_phys:
            start_x = self.find_phys_index(start_x_phys)
        else:
            start_x = 0
        if end_x_phys:
            end_x = self.find_phys_index(end_x_phys)
        else:
            end_x = self.data.shape[1]
        #print 'make transient',(start_x, start_x_phys), (end_x, end_x_phys)
        #spark = Spark(self.spatial_smooth_data, self.spatial_axis_data, self.temporal_smooth_data[start_x: end_x], self.physical_x_axis_values.data[start_x:end_x], self)
        spark = Spark(self.spatial_smooth_data, self.y_axis_physical_values[self.valid_s_slice], self.temporal_smooth_data, self.x_axis_physical_values[self.valid_t_slice], self)
        return spark

class SparkResult(object):
    def __init__(self, spark):
        data = {}
        data['FWHM'] = spark.FWHM
        data['FDHM'] = spark.FDHM
        data['max_val'] = spark.max_val
        data['max_time'] = spark.max_time
        #data['FDHM_max_location'] = spark.FDHM_max_location
        #data['FWHM_max_location'] = spark.FWHM_max_location
        data['baseline'] = spark.baseline
        data['decay_constant'] = spark.decay_constant
        data['risetime'] = spark.risetime
        #data['spatial'] = spark.spatial_smooth_data
        #data['temporal'] = spark.temporal_smooth_data
        #data['spatial_axis'] = spark.spatial_axis_data
        #data['temporal_axis'] = spark.temporal_x_phys
        data['time_profile'] = spark.transient
        data['spatial_profile'] = spark.spatial_profile
        data['number'] = spark.number
        data['roi'] = spark.roi
        #data['image_data'] = spark.data
        #data['raw_data'] = spark.raw_data
        data['coordinates'] = spark.coords
        data['tfit_params'] = spark.transient.params
        data['sfit_params'] = spark.spatial_profile.params
        self.data = data

def spark_from_sparkresult(sparkresult):
    class SpDa:
        def __init__(self, pixel_size, interval, data, coords):
            self.pixel_size = pixel_size
            self.time_interval = interval
            self.data = data
            self.coords = coords
    d=sparkresult.data
    #sparkdata = SpDa(d[' ')

class Spark(QC.QObject):

    result_update = QC.pyqtSignal()
    def set_number(self,  number):
        self.number = number
        self.roi = 0
        self.name = 'Spark %i:%i'%(self.roi, number)

    def __init__(self, spatial_smooth_data, spatial_axis_data, temporal_smooth_data,
            temporal_x_phys, spark_data):
        super(Spark, self).__init__(None)
        #self.spark_data = spark_data
        self.pixel_size = spark_data.pixel_size
        self.time_interval = spark_data.time_interval
        #print spatial_smooth_data.tolist(), spatial_axis_data.tolist()
        #print temporal_smooth_data.tolist(), temporal_x_phys.tolist()

        #full width half max
        self.FWHM = None
        #full duration half max
        self.FDHM = None
        self.data = spark_data.data
        self.raw_data = spark_data.raw_data
        self.coords = spark_data.coords
        #decay time
        self.decay_constant = None
        self.risetime = None
        self.max_val = None
        self.max_location = None
        self.FDHM_location = None
        self.FWHM_left_location = None
        self.FWHM_right_location = None
        self.FDHM_max_location = None
        self.FWHM_max_location = None
        self.baseline = None
        self.spatial_smooth_data = n.copy(spatial_smooth_data)
        self.spatial_axis_data = spatial_axis_data
        self.temporal_smooth_data = n.copy(temporal_smooth_data)
        self.temporal_x_phys = n.copy(temporal_x_phys)
        self.transient = SparkTransient(
                self.temporal_smooth_data,
                self.temporal_x_phys)
        self.spatial_profile = SparkSpatialProfile(
                self.spatial_smooth_data,
                self.spatial_axis_data)


    def set_spatial_data(self, data):
        self.spatial_smooth_data = data
    def set_temporal_data(self, data):
        self.temporal_smooth_data = data



    def get_delta_f(self):
        print 'delta',self.transient.fit_max_value, self.transient.bl_left,self.transient.fit_max_value - self.transient.bl_left
        return self.transient.fit_max_value - self.transient.bl_left

    def analyze(self):
        #try:
        #    self.find_FDHM()
        #except:
        #    pass
        #try:
        if 1:
            #self.find_FWHM()
            self.FWHM = self.spatial_profile.FWHM
            self.FWHM_left_location = self.spatial_profile.params['mu']-self.FWHM/2.
            self.FWHM_right_location = self.spatial_profile.params['mu']+self.FWHM/2.
            f = self.spatial_profile.fit_function
            p = self.spatial_profile.params
            self.FWHM_left_val = f(arg=self.FWHM_left_location, **p)
            self.FWHM_right_val = f(arg=self.FWHM_right_location, **p)
            self.FWHM_max_location = p['mu']
            self.max_location = self.FWHM_max_location
        #except:
        #    pass
        #try:
        if 1:
            #self.max_val = self.transient.max_y
            self.max_val = self.transient.fit_max_value
            #rise = self.transient.max - self.transient.bl_loc
            rise = self.transient.rise
            #self.max_time = self.temporal_x_pahys[rise]
            self.max_time = self.transient.fit_max_loc
            self.baseline = self.transient.bl_left
            self.FDHM_location = self.transient.FDHM_loc
            self.FDHM_val = self.transient.FDHM_value
            self.FDHM = self.transient.FDHM
        #except:
        #    pass
        #nprint '\n\n TIME',self.max_time
        self.risetime = rise#*self.time_interval*1000
        #self.transient.fit_decay()
        #self.decay_constant = self.transient.decay
        self.decay_constant = self.transient.params['tau2']
        self.result_update.emit()

