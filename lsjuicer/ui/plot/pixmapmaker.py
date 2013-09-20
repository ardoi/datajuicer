import numpy as n
from scipy import ndimage as sn

import PyQt4.QtGui as QG
from skimage import exposure


from lsjuicer.resources import cm
import lsjuicer.inout.db.sqla as sa


class PixmapMaker(object):

    """Makes a Qt Pixmap object from numerical data output by pipechain"""
    @property
    def data(self):
        return self.pipechain.get_result_data()

    @property
    def colormap(self):
        cmap = self.settings["colormap"]
        if self.settings["colormap_reverse"]:
            cmap += "_r"
        return cmap

    @property
    def saturation(self):
        return self.settings["saturation"]

    @property
    def blur(self):
        return self.settings["blur"]

    def __init__(self, pipechain):
        print "\n\n\nMaking pixmaker"
        self.last_pixmap_settings = None
        self.last_channel = None
        self.last_frame = None
        self.settings = sa.dbmaster.get_config_setting_value(
            "visualization_options_reference")
        self.pipechain = pipechain
        self._pixmap = None
        self.force = False

    @property
    def pixmap(self):
        # print 'getting pixmap'

        if (not self._pixmap) or (self.settings != self.last_pixmap_settings)\
                or self.force or self.channel != self.last_channel or \
                self.frame != self.last_frame:
            # print 'make new'
            self._make_pixmap()
            self.last_pixmap_settings = self.settings.copy()
            self.last_channel = self.channel
        else:
            pass
            # print 'use old'
        # print self.data.shape, self._pixmap
        return self._pixmap

    @pixmap.setter
    def pixmap(self, value):
        self._pixmap = value

    #@helpers.timeIt
    def _make_pixmap(self):
        # print "making pixmap"
        # print self.blur
        # print self.data
        dd = self.data[self.channel][self.frame].astype('float')
        nans = n.isnan(dd)
        # if n.any(nans):
        #    print 'nans'
        # dd = n.ma.masked_array(dd,nans)
        # array of dd values that are not nan (for stats)
        allnans = n.all(nans)
        if not allnans:
            if n.any(nans):
                ddn = dd[n.invert(n.isnan(dd))]
                # array where nan has been replaced by neigbourhood average
                nan_coords = n.where(nans)
                y_nan, x_nan = nan_coords
                for y, x in zip(y_nan, x_nan):
                    dd[y, x] = nearest_average(dd, x, y)
            else:
                ddn = dd
            if self.blur:
            # if 1:
                # dd = helpers.blur_image(dd, self.blur)
                pix_size = self.pipechain.pixel_size
                blur = self.blur * n.ones(pix_size.shape) / pix_size
                # the gaussian filter takes arguments in
                # different order - [y,x] instead of [x,y]
                blur = blur[::-1]
                # use the same blur in temporal direction(x) as in spatial(y)
                blur[1] = blur[0]
                blur = self.blur * n.ones(pix_size.shape)
                # print 'blur settings',blur, pix_size, self.blur,type(blur)
                # print dd.shape
                # dd = sn.gaussian_filter(dd, blur)
                dd = sn.uniform_filter(dd, blur)

            # saturation
            cut_max = self.pipechain.percentage_value(self.saturation)
            dd = exposure.rescale_intensity(dd, in_range=(ddn.min(), cut_max),
                                            out_range=(0.0, 1.0))
        # print '\ndd',dd,cut_max
        # colormap for image
        # if n.any(nans):
        #    dd[nans] = None
            # nan_coords = n.where(nans==True)
            # y_nan, x_nan = nan_coords
            # for y,x in zip(y_nan, x_nan):
            #    dd[y,x] = None
        # print dd
        dd = n.ma.masked_array(dd, nans)
        cmap = cm.get_cmap(self.colormap)
        cmap.set_bad(color='r')
        d2 = cmap.__call__(dd, bytes=True)
        # print '\nd2',d2
        d2.shape = (dd.size, 4)
        # swap columns
        d2[:, n.array([0, 2])] = d2[:, n.array([2, 0])]
        im_data = d2.tostring()
        y_points = dd.shape[0]
        x_points = dd.shape[1]
        im = QG.QImage(im_data, x_points,
                       y_points, QG.QImage.Format_ARGB32)
        self._pixmap = QG.QPixmap.fromImage(im)
        print 'set settnings', self.settings
        sa.dbmaster.set_config_setting(
            "visualization_options_reference", self.settings)
        print 'done setting'

    def makeImage(self, channel=0, frame=0, force=False, image_settings={}):
        # print "make image",image_settings, self.last_pixmap_settings,force
        # force is needed for cases when a new image is loaded (settings don't
        # change but image generation is necessary)
        self.force = force
        self.frame = frame
        self.channel = channel
        if image_settings:
            self.settings.update(image_settings)
        # print self.settings


def nearest_average(data, x, y):
    margin = 1
    while margin<5:
        x0 = max(0, x - margin)
        x1 = min(data.shape[1], x + margin + 1)
        y0 = max(0, y - margin)
        y1 = min(data.shape[0], y + margin + 1)
        d = data[y0:y1, x0:x1]
        nans = n.isnan(d)
        nonnan = d[n.invert(nans)]
        if nonnan.size:
            return nonnan.flatten().mean()
        else:
            margin += 1
            continue
    return 0.0
