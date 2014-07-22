import traceback
import datetime

from lsjuicer.data.imagedata import  ImageDataLineScan, make_selection
from lsjuicer.util.threader import Threader
from lsjuicer.inout.db.sqla import PixelEvent, PixelByPixelAnalysis
from lsjuicer.inout.db.sqla import dbmaster
from lsjuicer.inout.db.sqla import FittedPixel, PixelByPixelFitRegion, PixelByPixelRegionFitResult

class PixelByPixelAnalyzer(object):


    def __init__(self, imagedata, analysis, coords=None):
        self.imagedata = imagedata
        self.analysis = analysis
        if coords == None:
            #use all image
            self.coords = make_selection(imagedata)
        else:
            if isinstance(coords, list):
                #coords are list of [left,right, top, bottom]
                #FIXME make work with new selection classes
                raise NotImplementedError()
                #self.coords = QC.QRectF(coords[0], coords[2],
                #        coords[1]-coords[0],coords[3]-coords[2])
            self.coords = coords
        #FIXME
        self.dx = 1
        if isinstance(imagedata, ImageDataLineScan):
            self.dx = 0
        self.dy = 1

    @property
    def trace_count(self):
        x = self.coords.width
        y = self.coords.height
        #change this if you want to use selections later
        traces = (x - 2*self.dx)*(y - 2*self.dy)
        return traces

    @property
    def region_parameters(self):
        region_parameters = {'selection':self.coords,
                             'dx':self.dx, 'dy':self.dy}
        return region_parameters

    def extract_pixels(self):
        params = self.imagedata.get_traces(**self.region_parameters)
        print 'pp',params[0]
        settings = {'selection':self.coords,
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
        region_coords = (self.coords.left, self.coords.right,
                self.coords.top, self.coords.bottom)
        region.start_frame = self.coords.start
        region.end_frame = self.coords.end
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


