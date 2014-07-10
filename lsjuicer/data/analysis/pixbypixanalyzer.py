import traceback
import datetime

from PyQt5 import QtCore as QC

from lsjuicer.data.imagedata import  ImageDataLineScan
from lsjuicer.util.threader import Threader
from lsjuicer.inout.db.sqla import PixelEvent, PixelByPixelAnalysis
from lsjuicer.inout.db.sqla import dbmaster
from lsjuicer.inout.db.sqla import FittedPixel, PixelByPixelFitRegion, PixelByPixelRegionFitResult

class PixelByPixelAnalyzer(object):

    @property
    def x0(self):
        if self.coords:
            return int(self.coords.left())
        else:
            return 0

    @property
    def y0(self):
        if self.coords:
            return int(self.coords.top())
        else:
            return 0
    @property
    def data_width(self):
        if isinstance(self.imagedata, ImageDataLineScan):
            return 1
        else:
            if self.coords:
                x = int(self.coords.width())
            else:
                x = self.imagedata.x_points
            return x

    @property
    def data_height(self):
        if self.coords:
            y = int(self.coords.height())
        else:
            y = self.imagedata.y_points
        return y

    def __init__(self, imagedata, analysis, coords=None):
        self.imagedata = imagedata
        self.analysis = analysis
        if coords == None:
            #use all image
            self.coords = None
        else:
            if isinstance(coords, list):
                #coords are list of [left,right, top, bottom]
                self.coords = QC.QRectF(coords[0], coords[2],
                        coords[1]-coords[0],coords[3]-coords[2])
            self.coords = coords

        print 'coords', self.coords
        if isinstance(imagedata, ImageDataLineScan):
            self.start_frame = self.x0
            if self.coords:
                self.end_frame = int(self.coords.right())
            else:
                self.end_frame = self.x0 + self.imagedata.x_points
        else:
            pass
            #FIXME
            #time_range = selections[ISTN.TIMERANGE]
            #self.start_frame = time_range['start']
            #self.end_frame = time_range['end']
        self.acquisitions = self.end_frame - self.start_frame
        #FIXME
        self.dx = 0
        self.dy = 1

    @property
    def trace_count(self):
        x = self.data_width
        y = self.data_height
        #change this if you want to use selections later
        traces = (x - 2*self.dx)*(y - 2*self.dy)
        return traces

    @property
    def region_parameters(self):
        region_parameters = {'x0':self.dx+self.x0, 'y0':self.dy + self.y0,
                             'x1':self.x0+self.data_width - self.dx,
                             'y1':self.y0+self.data_height - self.dy,
                             'dx':self.dx, 'dy':self.dy,
                             't0':self.start_frame, 't1':self.end_frame}
        return region_parameters

    def extract_pixels(self):
        params = self.imagedata.get_traces(self.region_parameters)
        settings = {'width':self.data_width, 'height':self.data_height,
                    'dx':self.dx, 'dy':self.dy}
        self.threader = Threader()
        self.threader.do(params, settings)

    def fit(self):
        self.threader.run()

    def make_result(self):
        print "threader done. saving results"
        if not self.analysis:
            self.analysis = PixelByPixelAnalysis()
        self.analysis.imagefile = self.imagedata.mimage
        self.analysis.date = datetime.datetime.now()
        session = dbmaster.get_session()
        region = PixelByPixelFitRegion()
        region.analysis = self.analysis
        region_coords = (self.x0, self.x0+self.data_width,
                self.y0, self.y0+self.data_height)
        region.start_frame = self.start_frame
        region.end_frame = self.end_frame
        region.set_coords(region_coords)
        fit_result = PixelByPixelRegionFitResult()
        fit_result.fit_settings = {"padding":self.dx}
        self.fit_result  = fit_result
        self.fit_result.region = region
        for xy, res in self.threader.results.iteritems():
            try:
                fitted_pixel = FittedPixel()
                fitted_pixel.result = fit_result
                fitted_pixel.x = xy[0]
                fitted_pixel.y = xy[1]
                if res:
                    fitted_pixel.baseline = res['baseline']
                    #fitted_pixel.event_count = len(res['transients'])
                    for c,transient in res['transients'].iteritems():
                        pixel_event = PixelEvent()
                        pixel_event.pixel = fitted_pixel
                        pixel_event.parameters = transient
            except:
                traceback.print_exc()
                continue
        session.commit()
        print 'saving done'


