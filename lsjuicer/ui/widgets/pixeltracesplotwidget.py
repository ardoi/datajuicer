import numpy

from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC
from lsjuicer.inout.db.sqla import SyntheticData

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
        self.save_trace_checkbox = QW.QCheckBox("Save trace")
        tables_layout.addWidget(self.save_trace_checkbox)
        tables_layout.setStretch(0,2)
        tables_layout.setStretch(1,3)
        tables_layout.setStretch(2,1)
        layout.setStretch(0, 2)
        layout.setStretch(1, 1)

        self.plot_made = False
        self.plotnames = {}
        self.plotted = 0

    def get_time_trace_fit(self, selection):
        roiitem = selection.graphic_item
        rect = roiitem.rect()
        y = int(rect.top())
        x = int(rect.left())

        trace = self.pixpixw.imagedata.get_trace(self.pixpixw.coords,
                                                 self.pixpixw.dx, self.pixpixw.dy,
                                                 x, y)
        time_4_fit = numpy.arange(len(trace))
        res_4_fit = self.pixpixw.fit_result.get_fitted_pixel(x, y)
        syn_data = SyntheticData()
        syn_data.times = time_4_fit
        fit = syn_data.func_all(res_4_fit)
        if self.save_trace_checkbox.isChecked():
            import cPickle
            with open("trace_x{}_y{}.dat".format(x,y),'w') as fout:
                for item in (time_4_fit, trace, fit, x, y, res_4_fit):
                    cPickle.dump(item, fout)
        return time_4_fit, trace, fit, x, y, res_4_fit

    def trace_plot_update(self, selection):
        if self.plot_made:
            time_4_fit, trace, fit, x, y, res = self.get_time_trace_fit(selection)
            plot_number = self.plotnames[selection]
            self.plot_widget.updatePlot('data %i'% plot_number, trace,
                   time_4_fit, hold_update=True)
            self.plot_widget.updatePlot('fit %i'% plot_number, fit,
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
                self.plot_widget.addPlot('data %i'% self.plotted,
                       time_4_fit, trace, style)
                style={'color':'red','size':3}
                self.plot_widget.addPlot('fit %i'% self.plotted,
                       time_4_fit,fit, style)

                self.plotnames[roi] = self.plotted
                self.plotted += 1
                self.events_model.set_events(res)
            self.plot_made = True

        #self.plot_widget.fitView()



