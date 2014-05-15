from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC

from collections import defaultdict

from actionpanel import ActionPanel
from lsjuicer.ui.items.selection import ROIManager, SelectionDataModel
from lsjuicer.ui.items.selection import SelectionWidget, LineManager, SnapROIManager
from lsjuicer.inout.db.sqla import SparkAnalysis, PixelByPixelAnalysis
from lsjuicer.static import selection_types
from lsjuicer.data.imagedata import ImageDataLineScan
from lsjuicer.ui.tabs.transienttab import FluorescenceTab
from lsjuicer.data.imagedata import ImageDataMaker
from lsjuicer.data.pipes.tools import PipeChain

class AnalysisPanel(ActionPanel):
    __doc__ = """Choose analysis mode"""
    __shortname__ = "Analysis"
    def setup_ui(self):
        analysistype_layout = QW.QVBoxLayout()
        self.setLayout(analysistype_layout)
        self.analysistype_combo = QW.QComboBox()
        analysistype_layout.addWidget(self.analysistype_combo)
        self.analysistype_combo.addItem('Transients')
        self.analysistype_combo.addItem('Sparks')
        self.analysistype_combo.addItem('SparkDetect')
        self.analysistype_combo.addItem('PseudoLineScan')
        self.analysistype_combo.addItem('TimeAverage')
        self.analysistype_combo.addItem('PixelByPixel')
        self.analysistype_combo.setCurrentIndex(5)
        analysistype_use_pb = QW.QPushButton("Use")
        analysistype_layout.addWidget(analysistype_use_pb)
        analysistype_use_pb.clicked.connect(self.analysis_type_set)
        self.analysistype_combo.currentIndexChanged[str].connect(
                self.analysis_combo_changed)

        plotIcon=QG.QIcon(":/chart_curve_go.png")
        plotFluorescencePB  = QW.QPushButton(plotIcon,'Next')
        plotFluorescencePB.setEnabled(False)
        plotFluorescencePB.clicked.connect(self.on_next_PB_clicked)
        self.plotFluorescencePB = plotFluorescencePB
        analysistype_layout.addWidget(plotFluorescencePB)
        if self.analysis:
            self.analysis_type_set()

    def analysis_type_set(self):
        layout = self.layout()
        if hasattr(self,'selection_widget'):
            layout.removeWidget(self.selection_widget)
            del(self.selection_widget)
            del(self.selection_datamodel)

        self.selection_widget = SelectionWidget()
        self.selection_datamodel = SelectionDataModel()
        layout.addWidget(self.selection_widget)
        #if not self.analysis_mode:
        #    #FIXME: Wrong!
        self.makeButtons()
        if self.analysis:
            if isinstance(self.analysis, PixelByPixelAnalysis):
                self.analysis_mode = "PixelByPixel"
        else:
            self.analysis_mode = self.analysistype_combo.currentText()
        #print "set analysis mode", self.analysis_,mode, self.analysis
        self.analysis_mode_changed(self.analysis_mode)

    def analysis_mode_changed(self, analysis_mode):
        print 'analysis mode',analysis_mode
        if analysis_mode == "Sparks":
            key = 'imagetab.sparks'
        elif analysis_mode == "Transients":
            key = 'imagetab.transients'
        elif analysis_mode == "SparkDetect":
            key = 'imagetab.sparkdetect'
            #creating analysis
            if not self.analysis:
                self.analysis  = SparkAnalysis()
                self.analysis.imagefile = self.imagedata.mimage
        elif analysis_mode == "PseudoLineScan":
            key = 'imagetab.pseudolinescan'
        elif analysis_mode == "TimeAverage":
            key = 'imagetab.timeaverage'
        elif analysis_mode == "PixelByPixel":
            key = 'imagetab.timeaverage'
        if key == 'imagetab.pseudolinescan':
            self.roi_manager = LineManager(self.parentwidget.image_plot.fscene,
                        selection_types.data[key])
        elif key == 'imagetab.timeaverage':
            self.roi_manager = SnapROIManager(self.parentwidget.image_plot.fscene,
                        selection_types.data[key])
            if not self.analysis:
                self.analysis  = PixelByPixelAnalysis()
                self.analysis.imagefile = self.imagedata.mimage
        else:
            self.roi_manager = SnapROIManager(self.parentwidget.image_plot.fscene,
                        selection_types.data[key])
        self.selection_datamodel.set_selection_manager(self.roi_manager)
        self.selection_widget.set_model(self.selection_datamodel)
        #if self.analysis:
        #    try:
        #        if self.analysis.searchregions:
        #            self.roi_manager.activate_builder_by_type_name("ROI")
        #            builder = self.roi_manager.builder
        #            for region in self.analysis.searchregions:
        #                #print "region",region
        #                topleft = QC.QPointF(region._x0, region._y0)
        #                bottomright = QC.QPointF(region._x1, region._y1)
        #                #print topleft, bottomright
        #                builder.make_selection_rect(None, QC.QRectF(topleft, bottomright))
        #    except:
        #        pass
        if self.analysis:
            if isinstance(self.analysis, PixelByPixelAnalysis):
                self.roi_manager.activate_builder_by_type_name("ROI")
                builder = self.roi_manager.builder
                for region in self.analysis.fitregions:
                    print region
                    if isinstance(self.imagedata, ImageDataLineScan):
                        x0 = region.start_frame
                        x1 = region.end_frame
                    else:
                        x0 = region.x0
                        x1 = region.x1
                    topleft = QC.QPointF(x0, region.y0)
                    bottomright = QC.QPointF(x1, region.y1)
                    builder.make_selection_rect(None, QC.QRectF(topleft, bottomright))
                #self.time_range_start = 100
                #self.selection_slider.setValue(500)
                #self.set_time_range_end()
                #self.selection_slider.setValue(100)
                #self.set_time_range_start()

        return

    def analysis_combo_changed(self, analysis_mode):
        if hasattr(self,'selection_widget'):
            self.selection_widget.setEnabled(
                    self.analysis_mode == analysis_mode)

    def makeButtons(self):
        self.plotFluorescencePB.setEnabled(True)

    def on_next_PB_clicked(self):
        selections_by_type = self.roi_manager.selections_by_type
        #FIXME find better way to do this
        selections_by_type.update(self.parentwidget.frame_widget.provide_range())
        self.make_next_tab(selections_by_type)

    def make_next_tab(self, selections_by_type_name):
        #if self.count() > 1:
        #    while self.count() != 1:
        #        w = self.widget(self.count() - 1)
        #        self.removeTab(self.count() - 1)
        #        del(w)
        if self.analysis_mode == "Transients":
            next_tab =FluorescenceTab(selections_by_type_name, self.imagedata, self.pipechain, self.parentwidget.aw)
            #next_tab.setName(self.data.name)
            #self.connect(self.fltab,QC.SIGNAL('positionTXT(QString)'),
            #        self.emitStatusTXT)
        elif self.analysis_mode == "Sparks":
            pass
            #fltab = SparkTab(selections_by_type_name, self.imagedata, self)

        elif self.analysis_mode == "SparkDetect":
            pass
            #idata = ImageDataMaker.from_imagedata(self.imagedata)
            #idata.replace_channel(self.pipechain.get_result_data())
            #next_tab = SparkRegionsTab(selections_by_type_name, idata, self.analysis, self)
        elif self.analysis_mode == "PseudoLineScan":
            from lsjuicer.ui.tabs.imagetabs import AnalysisImageTab
            next_tab = AnalysisImageTab(parent=self.parentwidget.aw)
            next_tab.setAW(self.parentwidget.aw)
            if self.pipechain.active:
                print "pipe active. making new image"
                idata = ImageDataMaker.from_imagedata(self.imagedata)
                idata.replace_channels(self.pipechain.get_result_data())
            else:
                print "pipe inactive. using existing image"
                idata = self.imagedata
            linescan_image = idata.get_pseudo_linescan(selections_by_type_name)
            next_tab.showData(linescan_image)
        elif self.analysis_mode == "PixelByPixel":
            from lsjuicer.ui.tabs.pixelbypixeltab import PixelByPixelTab
            idata = ImageDataMaker.from_imagedata(self.imagedata)
            idata.replace_channels(self.pipechain.get_result_data())
            next_tab = PixelByPixelTab(idata, selections_by_type_name, self.analysis, parent = self.parentwidget.aw)

        if self.analysis_mode == "TimeAverage":
            new_data = self.imagedata.get_time_average_linescan(selections_by_type_name)
            #need to make fake pipechains :(
            pcs={}
            for channel in range(self.imagedata.channels):
                pc = PipeChain(new_data.pixel_size, self.parentwidget.image_plot.fscene)
                pc.set_source_data(new_data.all_image_data[channel])
                pcs[channel] = pc
            selections_by_type = defaultdict(list)
            next_tab = FluorescenceTab(selections_by_type, new_data, pcs, self.parentwidget.aw)
        #self.setCurrentIndex(1)
        #if self.analysis_mode != "PseudoLineScan":
        if 1:
            next_icon = QG.QIcon(':/chart_curve.png')
        self.parentwidget.aw.add_tab(next_tab, next_icon, self.analysis_mode)
