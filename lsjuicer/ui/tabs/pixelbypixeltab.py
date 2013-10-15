import datetime
import traceback
#from collections import defaultdict

import numpy

from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC

from lsjuicer.inout.db.sqla import FittedPixel, PixelByPixelFitRegion, PixelByPixelRegionFitResult
from lsjuicer.inout.db.sqla import dbmaster
from lsjuicer.inout.db.sqla import PixelEvent
from lsjuicer.ui.widgets.clusterwidget import ClusterDialog
from lsjuicer.ui.widgets.basicpixmapplotwidget import BasicPixmapPlotWidget
from lsjuicer.ui.widgets.pixeltracesplotwidget import PixelTracesPlotWidget
import lsjuicer.data.analysis.transient_find as tf
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
from lsjuicer.inout.db import sqla as sa
from lsjuicer.data.imagedata import ImageDataMaker

class PixelByPixelTab(QG.QTabWidget):
    @property
    def settings_text(self):
        out_image = "<strong>Image:</strong> <br>Width: %i<br>Height: %i<br>Pixels in frame: %i<br>Frames: %i"\
                %(self.imagedata.x_points, self.imagedata.y_points, \
                self.imagedata.x_points*self.imagedata.y_points, self.imagedata.frames)

        if self.coords:
            out_selection = "<strong>Selection:</strong><br>Top left: x=%i y=%i<br>Width: %i<br>Height: %i<br>Pixels: %i<br/>Frames: %i"\
                    %(self.coords.left(), self.coords.top(), self.coords.width(),\
                    self.coords.height(), self.coords.width()*self.coords.height(),
                    self.acquisitions)
        else:
            out_selection = ""
        out_settings = "<strong>Fit settings:</strong> <br>Traces to fit: %i"\
                %(self.trace_count)
        return "<br><br>".join((out_image, out_selection, out_settings))

    @property
    def data_width(self):
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

    @property
    def status(self):
        #self.makefits()
        return "A"

    def makefits(self):
        from lsjuicer.util.threader import FitDialog
        #t0 = time.time()
        #out = []
        params = []
        #if self.limit_checkbox.isChecked():
        #    stdlimit = int(self.limit_spinbox.value())
        #else:
        #    stdlimit = None
        for x in range(self.dx, self.data_width-self.dx):
            for y in range(self.dy, self.data_height-self.dy):
                data = self.imagedata.trace_in_time(x + self.x0, y+self.y0,
                        self.dx, self.dy, self.start_frame, self.end_frame)
                try:
                    assert True not in numpy.isnan(data)
                except:
                    print "NAN", (x + self.x0, y+self.y0, self.dx, self.dy)
                    print x,self.x0, y, self.y0
                #numpy.savetxt("out_%i_%i.dat"%(x+self.x0, y+self.y0), data)
                params.append({'data':data, 'coords':(x - self.dx, y-self.dy)})
        settings = {'width':self.data_width, 'height':self.data_height, 'dx':self.dx, 'dy':self.dy}
        fit_dialog = FitDialog(params, settings, parent = self)
        fit_dialog.progress_map_update.connect(self.set_progress_map_data)
        self.threader = fit_dialog.d
        #self.threader.finished.connect(self.threader_finished)
        res = fit_dialog.exec_()
        #print 'res=',res
        if res:
            self.threader_finished()
            self.get_res()
        #print 'input=',params
        #self.threader.do(params)
        #print "total time for pool size %i and %i fits: %i seconds, %.2f seconds per fit"%(pool_size, self.trace_count, time.time()-t0, (time.time()-t0)/(self.trace_count))
        #return "<br>".join(out)
    def set_progress_map_data(self, data):
        self.progress_map_data = data
        self.plot_widget.set_data(data)

    def threader_finished(self):
        from lsjuicer.inout.db import sqlb2
        print "threader done. saving results"
        #analysis  = PixelByPixelAnalysis()
        self.analysis.imagefile = self.imagedata.mimage
        self.analysis.date = datetime.datetime.now()
        session = dbmaster.get_session()
        #print self.analysis, session
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
        #session.add(fit_result)
        session2 = sqlb2.dbmaster.get_session()
        job_res = session2.query(sqlb2.Job).all()
        for job in job_res:
            try:
                fitted_pixel = FittedPixel()
                fitted_pixel.result = fit_result
                #session.add(fitted_pixel)
                res = job.result
                params = job.params
                xy = params['coords']
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
                #fitted_pixel.event_parameters = res['transients']
        session2.close()
        #print self.analysis, session
        session.commit()
        print 'saving done'

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
    def dx(self):
        return self.padding_spinbox.value()

    @property
    def dy(self):
        return self.dx

    @property
    def trace_count(self):
        x = self.data_width
        y = self.data_height
        #change this if you want to use selections later
        traces = (x - 2*self.dx)*(y - 2*self.dy)
        return traces

    def set_info_text(self):
        text = self.settings_text + "<br><br>" + self.status
        self.info_widget.setHtml(text)


    def __init__(self, imagedata, selections, analysis, parent = None):
        super(PixelByPixelTab, self).__init__(parent)
        self.imagedata = imagedata
        self.parent = parent
        print "PBPT", parent
        self.coords = None
        self.fit = False
        self.analysis  = analysis
        roi = selections[ISTN.ROI][0]
        time_range = selections[ISTN.TIMERANGE]
        self.start_frame = time_range['start']
        self.end_frame = time_range['end']
        self.acquisitions = self.end_frame - self.start_frame

        self.coords = roi.graphic_item.rect()
        #self.coords = QC.QRectF(167, 38, 148, 22)
        #self.coords = QC.QRectF(190, 44, 60, 9)
        #self.coords = QC.QRectF(211,22,121,15)
        #self.coords = QC.QRectF(121,29, 115, 31)
        #self.coords = QC.QRectF(202, 43, 276-202, 61-43)
        layout = QG.QVBoxLayout()
        self.setLayout(layout)
        settings_box = QG.QGroupBox('Fit settings')
        settings_layout = QG.QVBoxLayout()
        settings_box.setLayout(settings_layout)
        layout.addWidget(settings_box)

        padding_layout = QG.QHBoxLayout()
        padding_label = QG.QLabel("Element padding")
        padding_layout.addWidget(padding_label)
        padding_spinbox = QG.QSpinBox(self)
        padding_layout.addWidget(padding_spinbox)
        padding_spinbox.setMinimum(0)
        padding_spinbox.setValue(1)
        self.padding_spinbox = padding_spinbox
        padding_spinbox.setMaximum(20)
        settings_layout.addLayout(padding_layout)
        padding_spinbox.valueChanged.connect(self.set_info_text)

        limit_layout = QG.QHBoxLayout()
        limit_checkbox = QG.QCheckBox("Ignore transients less than x stds")
        self.limit_checkbox = limit_checkbox
        limit_layout.addWidget(limit_checkbox)
        limit_spinbox = QG.QSpinBox(self)
        self.limit_spinbox = limit_spinbox
        limit_layout.addWidget(limit_spinbox)
        limit_checkbox.toggled.connect(limit_spinbox.setEnabled)
        limit_spinbox.setEnabled(False)
        limit_spinbox.setMinimum(1)
        limit_spinbox.setMaximum(10)
        settings_layout.addLayout(limit_layout)

        info_widget = QG.QTextEdit(self)
        info_widget.setReadOnly(True)
        self.info_widget = info_widget
        self.set_info_text()
        settings_layout.addWidget(info_widget)
        fit_pb = QG.QPushButton("Do fit")
        #previous_pb = QG.QPushButton("Show previous")
        settings_layout.addWidget(fit_pb)
        #settings_layout.addWidget(previous_pb)
        fit_pb.clicked.connect(self.makefits)
        #previous_pb.clicked.connect(self.get_res)
        self.plot_widget = BasicPixmapPlotWidget(self)
        self.pixel_trace_widget = PixelTracesPlotWidget(self.plot_widget.scene,
                self, parent=self)
        plots_layout = QG.QHBoxLayout()
        plots_layout.addWidget(self.plot_widget)
        plots_layout.addWidget(self.pixel_trace_widget)
        layout.addLayout(plots_layout)
        self.load_analysis()

    def load_analysis(self):
        if self.analysis.fitregions:
            self.fit_result = self.analysis.fitregions[0].results[0]
            self.get_res()

    def get_res(self):
        results = {}
        #session = dbmaster.get_session()
        fitted_pixels = self.fit_result.pixels
        #print "get res", self.fit_result.region.width, self.fit_result.region.height
        results['width'] = self.fit_result.region.width - 2*self.fit_result.fit_settings['padding']
        results['height'] = self.fit_result.region.height - 2*self.fit_result.fit_settings['padding']
        #FIXME
        #results['frames'] = self.fit_result.region.analysis.imagefile.image_frames
        results['frames'] = self.acquisitions
        results['dx'] = self.fit_result.fit_settings['padding']
        results['dy'] = self.fit_result.fit_settings['padding']
        results['x0'] = self.fit_result.region.x0
        results['y0'] = self.fit_result.region.y0
        results['fits'] = fitted_pixels
        self.res = results
        param_combo = QG.QComboBox()
        events = tf.data_events(self.res)
        #convert numpy.int64 to python int so that sqlalchemy can
        #understand it
        max_n = int(events.max())
        #max_index = [int(el) for el in
        #        numpy.unravel_index(events.argmax(), events.shape)]
        #+1 because in results the indices are skewed by one
        #print self.fit_result.id, max_index
        #sample_pixel = self.fit_result.get_fitted_pixel(max_index[1], max_index[0])
        #FIXME Bad bad bad
        parameters=['A','m2', 'tau2', 'd', 'd2', 's']
        #for key in sample_pixel.pixel_events[0].parameters:
        for key in parameters:
            param_combo.addItem(key)
        param_combo.addItem('Events')
        param_combo.currentIndexChanged[QC.QString].connect(self.param_combo_changed)

        n_combo = QG.QComboBox()
        for i in range(max_n):
            n_combo.addItem("%i"%i)
        n_combo.currentIndexChanged.connect(self.n_combo_changed)

        hlayout = QG.QHBoxLayout()
        hlayout.addWidget(param_combo)
        hlayout.addWidget(n_combo)
        self.layout().addLayout(hlayout)
        self.t_number = 0
        self.param = "A"
        pb_do_clustering  = QG.QPushButton("Do clustering")
        pb_do_clustering.setCheckable(True)
        pb_do_clustering.clicked.connect(self.do_clustering)
        pb_make_new_stack = QG.QPushButton("New stack from fit")
        pb_make_new_stack.clicked.connect(self.make_new_stack)
        hlayout.addWidget(pb_do_clustering)
        hlayout.addWidget(pb_make_new_stack)
        self.show_res()

    def make_new_stack(self):
        #session = dbmaster.get_session()
        from lsjuicer.ui.tabs.imagetabs import AnalysisImageTab
        synthetic_image = sa.PixelFittedSyntheticImage(self.fit_result)
        next_tab = AnalysisImageTab(parent=self,analysis=self.analysis)
        im_data = ImageDataMaker.from_db_image(synthetic_image)
        next_tab.showData(im_data)
        next_tab.setAW(self.parent)
        print self.parent
        next_icon = QG.QIcon(':/chart_curve.png')
        self.parent.add_tab(next_tab, next_icon, "Fitted data")

    def param_combo_changed(self, param):
        self.param = str(param)
        self.show_res()

    def n_combo_changed(self, t_number):
        self.t_number = t_number
        self.show_res()

    def show_res(self):
        if self.param == "Events":
            data = tf.data_events(self.res)
        else:
            data = tf.make_data_by_size(self.res, self.param, self.t_number)
        self.plot_widget.set_data(data)

    def do_clustering(self, checked):
        dialog = ClusterDialog(self.analysis, self)
        dialog.show()
        #self.pixel_trace_widget.setVisible(checked)


