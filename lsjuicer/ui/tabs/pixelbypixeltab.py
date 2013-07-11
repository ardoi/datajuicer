import datetime
from itertools import cycle
#from collections import defaultdict

import numpy

from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC

from sklearn.cluster import DBSCAN

from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
from lsjuicer.util.threader import FitDialog
from lsjuicer.inout.db import sqlb2
from lsjuicer.inout.db.sqla import dbmaster
from lsjuicer.ui.widgets.plot_with_axes_widget import DiscontinousPlotWidget
from lsjuicer.ui.widgets.plot_with_axes_widget import ContinousPlotWidget
from lsjuicer.data.pipes.tools import PipeChain
from lsjuicer.ui.plot.pixmapmaker import PixmapMaker
import lsjuicer.data.analysis.transient_find as tf
from lsjuicer.ui.widgets.smallwidgets import VisualizationOptionsWidget
from lsjuicer.ui.views.dataviews import CopyTableView
from lsjuicer.ui.items.selection import SelectionDataModel, SelectionWidget, FixedSizeSnapROIManager
from lsjuicer.static import selection_types
from lsjuicer.inout.db.sqla import FittedPixel, PixelByPixelFitRegion, PixelByPixelRegionFitResult

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
        print "threader done. saving results"
        #analysis  = PixelByPixelAnalysis()
        self.analysis.imagefile = self.imagedata.mimage
        self.analysis.date = datetime.datetime.now()
        session = dbmaster.object_session(self.analysis)
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
                fitted_pixel.event_count = len(res['transients'])
                fitted_pixel.event_parameters = res['transients']
            else:
                fitted_pixel.event_count = 0
        session2.close()
        print self.analysis, session
        session.commit()
        session.close()
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
        self.coords = QC.QRectF(121,29, 115, 31)
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
        session = dbmaster.object_session(self.fit_result)
        if not session:
            session = dbmaster.get_session()
            session.add(self.fit_result)
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
        max_n = int(events.max())
        #convert numpy.int64 to python int so that sqlalchemy can
        #understand it
        max_index = [int(el) for el in
                numpy.unravel_index(events.argmax(), events.shape)]
        #+1 because in results the indices are skewed by one
        #print self.fit_result.id, max_index
        sample_pixel = self.fit_result.get_fitted_pixel(max_index[1], max_index[0])
        for key in sample_pixel.event_parameters[0]:
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
        pb_show_pixel_traces  = QG.QPushButton("Show pixel data")
        pb_show_pixel_traces.setCheckable(True)
        pb_show_pixel_traces.clicked.connect(self.show_pixel_traces)
        pb_make_new_stack = QG.QPushButton("New stack from fit")
        pb_make_new_stack.clicked.connect(self.make_new_stack)
        hlayout.addWidget(pb_show_pixel_traces)
        hlayout.addWidget(pb_make_new_stack)
        self.show_res()
        session.close()

    def make_new_stack(self):
        new_data = tf.clean_plot_data(self.res)
        bl = tf.clean_plot_data(self.res, only_bl = True)
        print new_data
        print bl
        pass

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

    def show_pixel_traces(self, checked):
        dialog = ClusterDialog(self.analysis, self)
        dialog.show()
        #self.pixel_trace_widget.setVisible(checked)

class PixelTracesPlotWidget(QG.QWidget):
    def __init__(self, scene, pixpixw, parent=None):
        super(PixelTracesPlotWidget, self).__init__(parent)
        self.plot_widget = DiscontinousPlotWidget(parent=self)
        layout = QG.QVBoxLayout()
        #original image
        self.pixpixw = pixpixw
        self.setLayout(layout)
        layout.addWidget(self.plot_widget)
        tables_layout = QG.QHBoxLayout()

        layout.addLayout(tables_layout)

        self.selection_widget = SelectionWidget()
        self.selection_datamodel = SelectionDataModel()
        key = 'pixelbypixeltab'
        self.roi_manager = FixedSizeSnapROIManager(scene, selection_types.data[key])
        self.roi_manager.ROI_available.connect(self.plot_traces)
        self.roi_manager.selection_changed.connect(self.trace_plot_update)
        self.selection_datamodel.set_selection_manager(self.roi_manager)
        self.selection_widget.set_model(self.selection_datamodel)

        self.events_view = CopyTableView()
        self.events_model = EventFitParametersDataModel()
        self.events_view.setModel(self.events_model)
        tables_layout.addWidget(self.selection_widget)
        tables_layout.addWidget(self.events_view)
        layout.setStretch(0, 2)
        layout.setStretch(1, 1)
        self.plot_made = False
        self.plotnames = {}
        self.plotted = 0

    def get_time_trace_fit(self, selection):
        roiitem = selection.graphic_item
        rect = roiitem.rect()
        y = rect.top()
        x = rect.left()
        #trace = self.pixpixw.imagedata.trace_in_time(x+ self.pixpixw.x0, y + self.pixpixw.y0, 1, 1)
        trace = self.pixpixw.imagedata.trace_in_time(x + self.pixpixw.x0 + self.pixpixw.dx,
                y + self.pixpixw.y0 + self.pixpixw.dy, self.pixpixw.dx, self.pixpixw.dy,
                self.pixpixw.start_frame, self.pixpixw.end_frame)
        #print '\n',x,y,trace
        time_4_fit = numpy.arange(len(trace))
        res_4_fit = self.pixpixw.fit_result.get_fitted_pixel(x, y)
        #res_4_fit = self.pixpixw.res['fits'][(int(x)+1, int(y)+1)]
        fit = tf.full_res(time_4_fit, res_4_fit)
        return time_4_fit, trace, fit, x, y, res_4_fit

    def trace_plot_update(self, selection):
        if self.plot_made:
            time_4_fit, trace, fit, x, y,res = self.get_time_trace_fit(selection)
            plot_number = self.plotnames[selection]
            self.plot_widget.updatePlot('data %i'%(plot_number), trace, \
                   time_4_fit)
            self.plot_widget.updatePlot('fit %i'%(plot_number), fit, \
                   time_4_fit)
            self.plot_widget.fitView()
            self.events_model.set_events(res)
        else:
            self.plot_traces()

    def plot_traces(self):
        #print "plot traces"
        selections= self.roi_manager.selections_by_type
        rois = selections[ISTN.ROI]
        for roi in rois:
            if roi not in self.plotnames:
                time_4_fit, trace, fit,x,y,res = self.get_time_trace_fit(roi)
                self.plot_widget.addPlot('data %i'%(self.plotted), trace, \
                       time_4_fit,size=1, color='gray',physical=False)

                self.plot_widget.addPlot('fit %i'%(self.plotted), fit, \
                       time_4_fit,size=3,color='red', physical=False)

                self.plotnames[roi] = self.plotted
                self.plotted += 1
                self.events_model.set_events(res)
            self.plot_made = True

        self.plot_widget.fitView()


class EventFitParametersDataModel(QC.QAbstractTableModel):
    def __init__(self, parent=None):
        super(EventFitParametersDataModel, self).__init__(parent)
        self.rows = 0
        self.keys = ['A','d','tau2','s','m2','d2']
        self.columns = len(self.keys)
        self.events = []

    def set_events(self, res):
        self.emit(QC.SIGNAL('modelAboutToBeReset()'))
        self.events = res.event_parameters
        self.rows = res.event_count
        #print 'events', self.events, self.columns
        self.emit(QC.SIGNAL('modelReset()'))
        self.emit(QC.SIGNAL('layoutChanged()'))

    def rowCount(self, parent):
        return self.rows

    def columnCount(self, parent):
        return self.columns

    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section<6:
                    return self.keys[section]
                else:
                    return QC.QVariant()

            else:
                return section+1
        else:
            return QC.QVariant()

    def data(self, index, role):
        if role == QC.Qt.DisplayRole:
            row = index.row()
            event = self.events[row]
            col = index.column()
            #print event[self.keys[col]], self.keys[col]
            return "%.3f"%(event[self.keys[col]])
        else:
            return QC.QVariant()

def normify(a):
    #you can use preprocessing.scale instead
    #b=10.0
    res = (a-a.mean())/a.std()
    #left = ss.scoreatpercentile(res,b)
    #right = ss.scoreatpercentile(res,100-b)
    #r2=res.clip(left,right)
    return res

class ClusterWidget(QG.QWidget):
    clusters_ready = QC.pyqtSignal(dict)
    def __init__(self, cluster_data, plot_pairs, key, settings, parent = None, reference_data = None):
        super(ClusterWidget, self).__init__(parent)

        self.cluster_data = cluster_data
        if reference_data is None:
            self.reference_data = self.cluster_data
        else:
            self.reference_data = reference_data

        widget_layout = QG.QVBoxLayout()
        self.plot_layout = QG.QGridLayout()
        self.setLayout(widget_layout)
        widget_layout.addLayout(self.plot_layout)
        self.rows = len(plot_pairs.keys())
        #self.columns = max([len(el) for el in plot_pairs.values()])
        self.plotwidgets = {}
        self.plot_pairs = plot_pairs
        self.make_plot_widgets()
        self.key = key
        do_pb = QG.QPushButton('Do')
        do_pb.clicked.connect(self.do)
        widget_layout.addWidget(do_pb)
        self.settings = settings

    def do(self):
        eps = self.settings['eps']
        min_samples = self.settings['min_samples']
        self.do_cluster(eps, min_samples)
        self.do_plots()

    def do_cluster(self, eps, min_samples):
        self.clusters = Clusterer.cluster_elements(Clusterer.cluster(self.cluster_data,
            eps = eps, min_samples = min_samples), self.reference_data)
        print 'clusterkeys',self.clusters.keys()

    def make_plot_widgets(self):
        if self.plotwidgets:
            return
        for i, kind in enumerate(self.plot_pairs.keys()):
            for j, spp in enumerate(self.plot_pairs[kind]):
                print kind, spp
                x = spp[0]
                y = spp[1]
                plotwidget = ContinousPlotWidget(self, antialias=False,
                    xlabel = x, ylabel = y)
                self.plotwidgets[spp] = plotwidget
                if self.rows > 1:
                    self.plot_layout.addWidget(plotwidget, i, j)
                else:
                    self.plot_layout.addWidget(plotwidget, j, 0)
        print self.plotwidgets
        QG.QApplication.processEvents()

    def do_plots(self):
        colornames = cycle(['red', 'green', 'blue', 'yellow', 'orange', 'teal', 'magenta', 'lime', 'navy', 'brown'])
        for cluster, elements  in  self.clusters.iteritems():
            group_name = "Group %i"%cluster
            if cluster != -1:
                color = colornames.next()
            else:
                color = 'black'
            style={'style':'circles', 'color':color, 'alpha':0.50}
            if cluster == -1:
                style.update({'size':0.5, 'alpha':0.5})
            for i, kind in enumerate(self.plot_pairs.keys()):
                for j, spp in enumerate(self.plot_pairs[kind]):
                    x = self.key[spp[0]]
                    y = self.key[spp[1]]
                    plotwidget = self.plotwidgets[spp]
                    plotwidget.addPlot(group_name, elements[:,x], elements[:,y], plotstyle = style, hold_update = True)
        for spp, plotwidget in self.plotwidgets.iteritems():
            plotwidget.updatePlots()
            plotwidget.fitView()
        self.clusters_ready.emit(self.clusters)

class ClusterDialog(QG.QDialog):
    def __init__(self, analysis, parent=None):
        super(ClusterDialog, self).__init__(parent)
        layout = QG.QHBoxLayout()
        self.analysis = analysis
        self.setLayout(layout)
        do_pb = QG.QPushButton("Get clusters")
        layout.addWidget(do_pb)
        do_pb.clicked.connect(self.stats)

    def sizeHint(self):
        return QC.QSize(1300,1000)

    def stats(self):
        an = self.analysis
        session = dbmaster.object_to_session(an)
        pixels=an.fitregions[0].results[0].pixels
        el=tf.do_event_list(pixels)

        shape_params = ['A','tau2','d2','d']
        loc_params = ['m2','x','y']
        params = shape_params[:]
        params.extend(loc_params)
        #dictionary of parameter names and their indices
        ics = dict(zip(params, range(len(params))))
        self.shape_params = shape_params
        self.loc_params = loc_params
        self.ics = ics


        event_array = tf.do_event_array(el, params)
        #for shape parameters a normalized array is needed too
        ea_shape0 = tf.do_event_array(el,shape_params)
        ea_shape = numpy.apply_along_axis(normify, 0, ea_shape0)
        #ea_shape = ea_shape0
        #ea_loc = tf.do_event_array(el,['m2','x','y'])
        session.close()
        tabs = QG.QTabWidget(self)
        self.layout().addWidget(tabs)
        self.tabs = tabs

        shape_plot_pairs = [('d', 'tau2'),('tau2','A'),('A', 'd')]
        loc_plot_pairs = [('m2','x'),('x','y'),('m2','y')]
        self.loc_plot_pairs = loc_plot_pairs
        plot_pairs = {'shape':shape_plot_pairs, 'location':loc_plot_pairs}
        try:
            shape_cluster_tab = ClusterWidget(ea_shape, plot_pairs, ics,{'eps':2.0, 'min_samples':50},
                    parent= tabs, reference_data = event_array)
            #shape_cluster_tab.do()
            shape_cluster_tab.clusters_ready.connect(self.add_loc_clusters)
        except:
            from IPython.frontend.terminal.embed import InteractiveShellEmbed
            #from IPython import embed_kernel
            QC.pyqtRemoveInputHook()
            ipshell=InteractiveShellEmbed()
            ipshell()
            #embed_kernel()
        tabs.addTab(shape_cluster_tab, 'Clusters by shape')

    def add_loc_clusters(self, cluster_data):
        for cluster, elements in cluster_data.iteritems():
            if cluster!=-1:
                data = elements[:,[self.ics[e] for e in self.loc_params]]
                loc_ics = dict(zip(self.loc_params, range(len(self.loc_params))))
                plot_pairs={'location':self.loc_plot_pairs}
                print 'loc ics',loc_ics,data.shape
                tab = ClusterWidget(data, plot_pairs, loc_ics, {'eps':2.5, 'min_samples':15},parent=self.tabs)
                index = self.tabs.addTab(tab,'Type %i'%cluster)


        #        for spp in loc_plot_pairs:
        #            x=spp[0]
        #            y=spp[1]
        #            plotwidget = ContinousPlotWidget(self, antialias=False,
        #                xlabel = x, ylabel = y)
        #            plotwidgets[cluster][spp] = plotwidget
        #            plot_layout.addWidget(plotwidgets[cluster][spp])
        #        for type_cluster, elements  in  clusters.iteritems():
        #            group_name = "Group %i"%cluster
        #            if type_cluster != -1:
        #                color = colornames.next()
        #            else:
        #                color = 'black'
        #            style={'style':'circles', 'color':color, 'alpha':0.25}
        #            if type_cluster == -1:
        #                style.update({'size':0.5,'alpha':0.75})

        #            for spp in loc_plot_pairs:
        #                x=loc_ics[spp[0]]
        #                y=loc_ics[spp[1]]
        #                plotwidget = plotwidgets[cluster][spp]
        #                plotwidget.addPlot(group_name, elements[:,x], elements[:,y], plotstyle = style, hold_update = True)

            self.tabs.setCurrentIndex(index)
        #    for spp, plotwidget in plotwidgets[cluster].iteritems():
        #        plotwidget.updatePlots()
        #        plotwidget.fitView()

class Clusterer(object):
    @staticmethod
    def cluster_elements(labels, data):
        groups = {}
        for k in set(labels):
            members = numpy.argwhere(labels == k).flatten()
            groups[k] = data[members]
        return groups

    @staticmethod
    def cluster(data, eps, min_samples):
        #D = metrics.euclidean_distances(data)
        #S = 1 - (D / numpy.max(D))
        print 'clustering', eps, min_samples
        print data.shape, data[0]
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(data)
        #core_samples = db.core_sample_indices_
        labels = db.labels_
        print set(labels)
        # Number of clusters in labels, ignoring noise if present.
        #n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        return labels


class BasicPixmapPlotWidget(QG.QWidget):
    def __init__(self, parent=None):
        super(BasicPixmapPlotWidget, self).__init__(parent)
        pc = PipeChain(pixel_size=numpy.array((0.25, 0.25)))
        #pc.pipe_state_changed.connect(self.force_new_pixmap)
        self.pipechain = pc
        pixmaker = PixmapMaker(pc)
        self.pixmaker = pixmaker

        self.plot_widget = DiscontinousPlotWidget(parent=self)
        self.scene = self.plot_widget.fscene
        layout = QG.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.plot_widget)
        self.image_shown = False
        vis_options_pb = QG.QPushButton("Visualization properties")
        vis_options_pb.clicked.connect(self.show_vis_options_dialog)
        vis_options_pb.setIcon(QG.QIcon('://color_wheel.png'))
        layout.addWidget(vis_options_pb)
    def force_new_pixmap(self, v = None):
        self.make_new_pixmap(force = True)

    def make_new_pixmap(self, settings = {}, force = False):
        pixmaker = self.pixmaker
        QC.QTimer.singleShot(10, lambda :
                pixmaker.makeImage(image_settings = settings, force = force))
        if self.image_shown:
            QC.QTimer.singleShot(15, lambda :
                    self.plot_widget.replacePixmap(pixmaker.pixmap))
        else:
            print 'showing image with tstamps'
            QC.QTimer.singleShot(20, lambda :
                    self.plot_widget.addPixmap(pixmaker.pixmap,
                        self.xvals, self.yvals))
            self.image_shown = True
        QC.QTimer.singleShot(25, lambda :self.plot_widget.fitView())

    def set_data(self, data):
        if data.ndim == 2:
            data = data.copy()
            data.shape = (1,1,data.shape[0],data.shape[1])
        self.pipechain.set_source_data(data)
        self.xvals = numpy.arange(data.shape[3])
        self.yvals = numpy.arange(data.shape[2])
        self.make_new_pixmap(force=True)

    def change_pixmap_settings(self, settings):
        self.make_new_pixmap(settings)

    def show_vis_options_dialog(self):
        dialog = QG.QDialog(self)
        layout = QG.QHBoxLayout()
        dialog.setLayout(layout)
        widget = VisualizationOptionsWidget(self.pipechain, parent=dialog)
        widget.settings_changed.connect(self.change_pixmap_settings)
        widget.close.connect(dialog.accept)
        layout.addWidget(widget)
        self.vis_widget = widget
        dialog.setModal(False)
        dialog.show()
        dialog.resize(400, 400)
        widget.do_histogram()
