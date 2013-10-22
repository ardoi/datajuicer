import numpy

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.ui.widgets.plot_with_axes_widget import TracePlotWidget
from lsjuicer.ui.items.selection import SelectionDataModel, SelectionWidget, FixedSizeSnapROIManager
from lsjuicer.static import selection_types
from lsjuicer.ui.views.dataviews import CopyTableView
import lsjuicer.data.analysis.transient_find as tf
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
from lsjuicer.data.models.eventfitparameters import EventFitParametersDataModel

class PixelTracesPlotWidget(QW.QWidget):
    def __init__(self, scene, pixpixw, parent=None):
        super(PixelTracesPlotWidget, self).__init__(parent)
        self.plot_widget = TracePlotWidget(parent=self)
        layout = QW.QVBoxLayout()
        #original image
        self.pixpixw = pixpixw
        self.setLayout(layout)
        layout.addWidget(self.plot_widget)
        tables_layout = QW.QHBoxLayout()

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
        #trace = self.pixpixw.imagedata.trace_in_time(x+ so.elf.pixpixw.x0, y + self.pixpixw.y0, 1, 1)
        params = {'x':x + self.pixpixw.x0 + self.pixpixw.dx,
                  'y':y + self.pixpixw.y0 + self.pixpixw.dy,
                  'dx':self.pixpixw.dx, 'dy':self.pixpixw.dy,
                  't0':self.pixpixw.start_frame, 't1':self.pixpixw.end_frame}
        print 'get trace', params
        trace = self.pixpixw.imagedata.get_trace(params)
        print '\n',x,y,trace
        time_4_fit = numpy.arange(len(trace))
        res_4_fit = self.pixpixw.fit_result.get_fitted_pixel(x, y)
        #res_4_fit = self.pixpixw.res['fits'][(int(x)+1, int(y)+1)]
        syn_data = tf.SyntheticData(results=None)
        syn_data.times = time_4_fit
        fit = syn_data.func_all(res_4_fit)
        #fit = tf.res_all(time_4_fit, res_4_fit)
        return time_4_fit, trace, fit, x, y, res_4_fit

    def trace_plot_update(self, selection):
        if self.plot_made:
            time_4_fit, trace, fit, x, y,res = self.get_time_trace_fit(selection)
            plot_number = self.plotnames[selection]
            self.plot_widget.updatePlot('data %i'%(plot_number), trace, \
                   time_4_fit, hold_update=True)
            self.plot_widget.updatePlot('fit %i'%(plot_number), fit, \
                   time_4_fit, hold_update=True)
            #self.plot_widget.fitView()
            QC.QTimer.singleShot(5, self.plot_widget.updatePlots)
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
                style={'color':'gray'}
                self.plot_widget.addPlot('data %i'%(self.plotted),
                       time_4_fit, trace, style)
                style={'color':'red','size':3}
                self.plot_widget.addPlot('fit %i'%(self.plotted),
                       time_4_fit,fit, style)

                self.plotnames[roi] = self.plotted
                self.plotted += 1
                self.events_model.set_events(res)
            self.plot_made = True

        #self.plot_widget.fitView()



