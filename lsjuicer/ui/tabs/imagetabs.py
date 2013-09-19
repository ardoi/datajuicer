from collections import defaultdict

from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC

from lsjuicer.ui.scenes import LSMDisplay
from lsjuicer.ui.items.selection import ROIManager, SelectionDataModel, SelectionWidget, LineManager, SnapROIManager
from lsjuicer.static.constants import Constants
from lsjuicer.static import selection_types
from lsjuicer.ui.widgets.plot_with_axes_widget import PixmapPlotWidget
from lsjuicer.data.pipes.tools import PipeChain, PipeChainWidget
from lsjuicer.data.data import ImageDataMaker
from lsjuicer.ui.plot.pixmapmaker import PixmapMaker
from lsjuicer.ui.widgets.smallwidgets import VisualizationOptionsWidget
from lsjuicer.ui.widgets.smallwidgets import FramePlayer
from lsjuicer.inout.db.sqla import SparkAnalysis, PixelByPixelAnalysis
from lsjuicer.ui.tabs.transienttab import FluorescenceTab
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
class ControlWidget(QG.QWidget):
    def  __init__(self, parent = None):
        super(ControlWidget, self).__init__(parent)

class AnalysisImageTab(QG.QWidget):
    """Tab containing image to analyze"""
    def  __init__(self, analysis = None, parent = None):
        super(AnalysisImageTab, self).__init__(parent)
        self.image_shown = False
        self.time_range_start = None
        self.time_range_end = None
        self.analysis = analysis
        layout = QG.QVBoxLayout()
        self.setLayout(layout)
        self.lsmPlot =self.makePlotArea()
        self.lsmPlot.updateLocation.connect(self.updateCoords)
        layout.addWidget(self.lsmPlot)
        self.controlWidget = QG.QWidget()
        self.control_layout = QG.QHBoxLayout()
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.controlWidget.setLayout(self.control_layout)
        layout.addWidget(self.controlWidget)
        layout.setStretchFactor(self.lsmPlot, 5)
        layout.setStretchFactor(self.controlWidget, 1)

    def clear_overlays(self):
        pass

    def setAW(self,widget):
        self.aw = widget

    @property
    def active_channel(self):
        return self.channel_combobox.currentIndex()
    @property
    def active_frame(self):
        return self.selection_slider.value()

    def force_new_pixmap(self, v = None):
        self.make_new_pixmap(force = True)

    def change_pixmap_settings(self, settings):
        self.make_new_pixmap(settings, viewreset = False)

    #@helpers.timeIt
    def make_new_pixmap(self, settings={}, viewreset = True, force=False):
        #print 'making new pix', force,settings
        #qmb=QG.QMessageBox(QG.QMessageBox.Information,
        #        '','Please wait...\nAdjusting image',QG.QMessageBox.Ok)
        #b=qmb.buttons()
        #qmb.removeButton(b[0])
        #qmb.show()
        channel = self.active_channel
        frame = self.active_frame
        pixmaker = self.pixmaker
        QC.QTimer.singleShot(0,lambda:
                pixmaker.makeImage(channel=channel,frame = frame, image_settings=settings, force=force))
                #self.data.makeImage(saturate/100.,cmap_name,0))
        if self.image_shown:
            QC.QTimer.singleShot(0,lambda:
                    self.lsmPlot.replacePixmap(pixmaker.pixmap))
        else:
            QC.QTimer.singleShot(0,lambda:
                    self.lsmPlot.addPixmap(pixmaker.pixmap,
                        self.imagedata.xvals, self.imagedata.yvals)
                    )
        #pixmaker.makeImage(image_settings=settings, force=force)
        #self.lsmPlot.replacePixmap(pixmaker.pixmap)
        #self.lsmPlot.addPixmap(pixmaker.pixmap,
        #    self.imagedata.xvals, self.imagedata.yvals)
        self.image_shown = True
        #QC.QTimer.singleShot(150,lambda :qmb.hide())

    def showData(self, data):
        self.imagedata = data
        channels = self.imagedata.channels
        acquisitions = self.imagedata.acquisitions
        #self.active_channel = 0
        self.pipechain = None
        self.pixmaker = None
        self.analysis_mode = None
        pipegroupbox = QG.QGroupBox("Processing")
        #pipegroupbox.setLayout(QG.QStackedLayout())
        pipegroupbox.setLayout(QG.QVBoxLayout())
        pipegroupbox.setSizePolicy(QG.QSizePolicy.Maximum,QG.QSizePolicy.Minimum)
        layout = pipegroupbox.layout()

        vis_opt_groupbox = QG.QGroupBox("Visualization options")
        vis_opt_groupbox.setLayout(QG.QStackedLayout())
        #vis_opt_groupbox.setLayout(QG.QVBoxLayout())
        vis_opt_groupbox.setSizePolicy(QG.QSizePolicy.Maximum,QG.QSizePolicy.Minimum)
        vis_layout = vis_opt_groupbox.layout()

        self.channel_combobox = QG.QComboBox()
        self.selection_slider = QG.QSlider(QC.Qt.Horizontal)
        self.selection_spinbox = QG.QSpinBox()

        pc = PipeChain(data.pixel_size, self.lsmPlot.fscene)
        pc.set_source_data(self.imagedata.all_image_data)
        pc.pipe_state_changed.connect(self.force_new_pixmap)
        self.pipechain = pc

        pipechainwidget = PipeChainWidget(pc)

        layout.addWidget(pipechainwidget)

        pixmaker = PixmapMaker(pc)
        self.pixmaker = pixmaker

        for channel in range(channels):
            vis_options = VisualizationOptionsWidget(pc, self, channel)
            vis_layout.addWidget(vis_options)
            vis_options.settings_changed.connect(self.make_new_pixmap)
        channel_names = self.imagedata.channel_names
        for channel, name in channel_names.iteritems():
            ch_str = 'ch{}: {}'.format(channel, name)
            print ch_str
            self.channel_combobox.addItem(ch_str)


        self.control_layout.addWidget(pipegroupbox)
        self.control_layout.addWidget(vis_opt_groupbox)
        channel_selection_groupbox = QG.QGroupBox("Displayed image")
        vlayout = QG.QVBoxLayout()
        channel_selection_groupbox.setLayout(vlayout)
        layout = QG.QHBoxLayout()
        layout.addWidget(QG.QLabel("Channel:"))
        layout.addWidget(self.channel_combobox)
        vlayout.addLayout(layout)
        layout = QG.QHBoxLayout()
        layout.addWidget(QG.QLabel("Frame:"))
        layout.addWidget(self.selection_slider)
        layout.addWidget(self.selection_spinbox)
        vlayout.addLayout(layout)

        layout = QG.QHBoxLayout()
        set_start_pb = QG.QPushButton("Set start")
        set_end_pb = QG.QPushButton("Set end")
        clear_pb = QG.QPushButton("Clear")
        layout.addWidget(set_start_pb)
        layout.addWidget(set_end_pb)
        layout.addWidget(clear_pb)
        range_label = QG.QLabel("<p style='border:red;'>Start: -<br/>End: -<br/>Duration: -</p>")
        #range_label.setEnabled(False)
        self.range_label = range_label
        self.set_range_label_color()
        layout.addWidget(range_label)
        layout.setContentsMargins(0,0,0,0)
        vlayout.addLayout(layout)
        vlayout.addStretch()
        set_start_pb.clicked.connect(self.set_time_range_start)
        set_end_pb.clicked.connect(self.set_time_range_end)
        clear_pb.clicked.connect(self.clear_time_range)

        frame_player = FramePlayer(self.selection_slider.value,
                self.selection_slider.setValue, self.selection_slider.maximum, self)
        vlayout.addWidget(frame_player)
        self.control_layout.addWidget(channel_selection_groupbox)
        self.selection_slider.setMinimum(0)
        self.selection_slider.setMaximum(acquisitions-1)
        self.selection_slider.valueChanged.connect(self.change_frame)
        self.time_range_start = 0
        self.time_range_end = acquisitions - 1
        self.update_time_range_label(0)
        self.selection_spinbox.setMinimum(0)
        self.selection_spinbox.setMaximum(acquisitions-1)
        self.selection_spinbox.valueChanged.connect(self.selection_slider.setValue)
        self.selection_slider.valueChanged.connect(self.selection_spinbox.setValue)
        self.selection_slider.valueChanged.connect(self.update_time_range_label)

        self.channel_combobox.setCurrentIndex(0)

        vis_layout.setCurrentIndex(0)

        self.channel_combobox.currentIndexChanged.connect(self.change_channel)
        #self.channel_combobox.currentIndexChanged.connect(pipegroupbox.layout().setCurrentIndex)
        self.channel_combobox.currentIndexChanged.connect(vis_layout.setCurrentIndex)
        self.analysistype_groupbox = QG.QGroupBox("Analysis")
        self.analysistype_groupbox.setLayout(QG.QHBoxLayout())
        analysistype_layout = QG.QVBoxLayout()
        self.analysistype_combo = QG.QComboBox()
        analysistype_layout.addWidget(self.analysistype_combo)
        self.analysistype_combo.addItem('Transients')
        self.analysistype_combo.addItem('Sparks')
        self.analysistype_combo.addItem('SparkDetect')
        self.analysistype_combo.addItem('PseudoLineScan')
        self.analysistype_combo.addItem('TimeAverage')
        self.analysistype_combo.addItem('PixelByPixel')
        self.analysistype_combo.setCurrentIndex(5)
        analysistype_use_pb = QG.QPushButton("Use")
        analysistype_layout.addWidget(analysistype_use_pb)
        analysistype_use_pb.clicked.connect(self.analysis_type_set)
        self.analysistype_combo.currentIndexChanged[QC.QString].connect(
                self.analysis_combo_changed)
        self.analysistype_groupbox.layout().addLayout(analysistype_layout)
        self.control_layout.addWidget(self.analysistype_groupbox)

        plotIcon=QG.QIcon(":/chart_curve_go.png")
        plotFluorescencePB  = QG.QPushButton(plotIcon,'Next')
        plotFluorescencePB.setEnabled(False)
        plotFluorescencePB.clicked.connect(self.on_next_PB_clicked)
        self.control_layout.addWidget(plotFluorescencePB)
        self.control_layout.addStretch()
        self.plotFluorescencePB = plotFluorescencePB
        #make sure other widgets are drawn before making pixmap
        QC.QTimer.singleShot(0,lambda: self.make_new_pixmap())
        if self.analysis:
            self.analysis_type_set()
        #QC.QTimer.singleShot(310,lambda :self.show_events(data.event_times))
        #QC.QTimer.singleShot(320,lambda :self.show_gaps(data.gaps))

    def change_channel(self, channel):
        self.force_new_pixmap()

    def set_time_range_start(self):
        self.time_range_start = self.selection_slider.value()
        if self.time_range_start >= self.time_range_end:
            self.time_range_end = self.imagedata.acquisitions
        self.update_time_range_label(self.time_range_start)

    def set_time_range_end(self):
        self.time_range_end = self.selection_slider.value()
        if self.time_range_end <= self.time_range_start:
            self.time_range_start = 0
        self.update_time_range_label(self.time_range_end)

    def update_time_range_label(self, current):
        #if self.start_frame is None and self.end_frame is None:
        #    region_text = "<p>Start: -<br/>End: -<br/>Duration: -</p>"
        #    self.range_label.setText(region_text)
        #    self.set_range_label_color(None)
        #    self.range_label.setEnabled(False)
        #else:
        #if self.start_frame !=0 and self.end_frame is not None:
        if current>=self.time_range_start and current<=self.time_range_end:
            color = "green"
        else:
            color = "red"
        width = self.time_range_end - self.time_range_start
        region_text = "<p>Start: %i<br/>End: %i<br/>Duration:%i</p>"%(self.time_range_start,
                self.time_range_end, width)
        #else:
        #    color='blue'
        #    region_text = "<p>Start: %s<br/>End: %s<br/>Duration: -</p>"%(str(self.start_frame) if self.start_frame is not None else "-", str(self.end_frame) if self.end_frame is not None else "-")
        self.range_label.setText(region_text)
        self.set_range_label_color(color)
        #self.range_label.setEnabled(True)

    def clear_time_range(self):
        self.time_range_start = 0
        self.time_range_end = self.imagedata.acquisitions
        self.update_time_range_label(0)

    def set_range_label_color(self, color=None):
        if color == None:
            color='transparent'
        self.range_label.setStyleSheet(" QLabel{ border: 3px solid %s;}"%color)

    def change_frame(self, frame):
        #pc = self.pipechain
        #pc.set_frame(frame)
        self.force_new_pixmap()

    def analysis_type_set(self):
        layout = self.analysistype_groupbox.layout()
        if hasattr(self,'selection_widget'):
            layout.removeWidget(self.selection_widget)
            del(self.selection_widget)
            del(self.selection_datamodel)

        self.selection_widget = SelectionWidget()
        self.selection_datamodel = SelectionDataModel()
        layout.addWidget(self.selection_widget)
        if not self.analysis_mode:
            #FIXME: Wrong!
            self.makeButtons()
        if self.analysis:
            if isinstance(self.analysis, PixelByPixelAnalysis):
                self.analysis_mode = "PixelByPixel"
        else:
            self.analysis_mode = self.analysistype_combo.currentText()
        print "set analysis mode", self.analysis_mode, self.analysis
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
            self.roi_manager = LineManager(self.lsmPlot.fscene,
                        selection_types.data[key])
        elif key == 'imagetab.timeaverage':
            self.roi_manager = SnapROIManager(self.lsmPlot.fscene,
                        selection_types.data[key])
            if not self.analysis:
                self.analysis  = PixelByPixelAnalysis()
                self.analysis.imagefile = self.imagedata.mimage
        else:
            self.roi_manager = ROIManager(self.lsmPlot.fscene,
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
                    topleft = QC.QPointF(region.x0, region.y0)
                    bottomright = QC.QPointF(region.x1, region.y1)
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

    def updateCoords(self,x,y,xx,yy):
        self.emit(QC.SIGNAL('positionTXT(QString)'),
                'x: %.3f [s], y: %.1f [um], sx: %i, sy: %i'%(x,y,xx,yy))

    def makeButtons(self):
        self.plotFluorescencePB.setEnabled(True)

    def on_next_PB_clicked(self):
        selections_by_type = self.roi_manager.selections_by_type
        selections_by_type[ISTN.TIMERANGE] = {'start':self.time_range_start, 'end':self.time_range_end}
        self.make_next_tab(selections_by_type)

    def make_next_tab(self, selections_by_type_name):
        #if self.count() > 1:
        #    while self.count() != 1:
        #        w = self.widget(self.count() - 1)
        #        self.removeTab(self.count() - 1)
        #        del(w)
        if self.analysis_mode == "Transients":
            next_tab =FluorescenceTab(selections_by_type_name, self.imagedata, self.pipechain, self.aw)
            #next_tab.setName(self.data.name)
            #self.connect(self.fltab,QC.SIGNAL('positionTXT(QString)'),
            #        self.emitStatusTXT)
        elif self.analysis_mode == "Sparks":
            fltab = SparkTab(selections_by_type_name, self.imagedata, self)

        elif self.analysis_mode == "SparkDetect":
            idata = ImageDataMaker.from_imagedata(self.imagedata)
            idata.replace_channel(self.pipechain.get_result_data())
            next_tab = SparkRegionsTab(selections_by_type_name, idata, self.analysis, self)
        elif self.analysis_mode == "PseudoLineScan":
            next_tab = AnalysisImageTab(parent=self.aw)
            next_tab.setAW(self.aw)
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
            next_tab = PixelByPixelTab(idata, selections_by_type_name, self.analysis, parent = self.aw)

        if self.analysis_mode == "TimeAverage":
            new_data = self.imagedata.get_time_average_linescan(selections_by_type_name)
            #need to make fake pipechains :(
            pcs={}
            for channel in range(self.imagedata.channels):
                pc = PipeChain(new_data.pixel_size, self.lsmPlot.fscene)
                pc.set_source_data(new_data.all_image_data[channel])
                pcs[channel] = pc
            selections_by_type = defaultdict(list)
            next_tab = FluorescenceTab(selections_by_type, new_data, pcs, self.aw)
        #self.setCurrentIndex(1)
        #if self.analysis_mode != "PseudoLineScan":
        if 1:
            next_icon = QG.QIcon(':/chart_curve.png')
        self.aw.add_tab(next_tab, next_icon, self.analysis_mode)

    def makePlotArea(self):
        return PixmapPlotWidget(sceneClass=LSMDisplay, parent=self)

    def show_events(self,event_times):
        self.lsmPlot.addHLines(event_times,Constants.EVENTS, 'cyan')

    def show_gaps(self,gap_times):
        self.lsmPlot.addHLines(gap_times,Constants.GAPS,'yellow')

