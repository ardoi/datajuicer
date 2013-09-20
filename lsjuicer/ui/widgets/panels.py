from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC

from collections import defaultdict
from lsjuicer.data.pipes.tools import PipeChain
from lsjuicer.data.data import ImageDataMaker
from lsjuicer.data.pipes.tools import pipe_classes, PipeModel, PipeWidget
from lsjuicer.ui.widgets.smallwidgets import VisualizationOptionsWidget
from lsjuicer.ui.widgets.smallwidgets import FramePlayer
from lsjuicer.inout.db.sqla import SparkAnalysis, PixelByPixelAnalysis
from lsjuicer.static import selection_types
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
from lsjuicer.ui.tabs.transienttab import FluorescenceTab

from lsjuicer.ui.items.selection import ROIManager, SelectionDataModel, SelectionWidget, LineManager, SnapROIManager

class ActionPanel(QG.QWidget):
    def __init__(self, parent = None):
        super(ActionPanel, self).__init__(parent)
        self.imagedata = parent.imagedata
        self.pipechain = parent.pipechain
        self.analysis = parent.analysis
        self.parentwidget = parent
        self.setup_ui()


class PipeChainPanel(ActionPanel):
    __doc__ = """Panel for editing pipes for the image"""
    __shortname__ = "Pipes"

    def setup_ui(self):
        self.settings_widgets={}

        layout = QG.QHBoxLayout()
        self.setLayout(layout)
        self.types = pipe_classes
        self.typecombo = QG.QComboBox()
        for t in self.types:
            self.typecombo.addItem(t)
        add_layout = QG.QVBoxLayout()
        add_layout.addWidget(self.typecombo)
        add_pb = QG.QPushButton('Add')
        add_layout.addWidget(add_pb)
        add_pb.clicked.connect(self.add_pipe)

        pipelist = QG.QListView()
        self.pipemodel = PipeModel()
        pipelist.setModel(self.pipemodel)

        self.setting_stack = QG.QStackedWidget()

        self.pipechain.pipe_state_changed.connect(self.update_model)

        layout.addLayout(add_layout)
        layout.addWidget(pipelist)
        layout.addWidget(self.setting_stack)

        pipelist.clicked.connect(self.show_pipe_settings)
        self.setSizePolicy(QG.QSizePolicy.Maximum, QG.QSizePolicy.Maximum)

    def update_model(self):
        self.pipemodel.pipes_updated()

    def show_pipe_settings(self, index):
        pipe_number = index.row()
        #print 'show', pipe_number
        pipe = self.pipechain.imagepipes[pipe_number]
        if pipe in self.settings_widgets:
            sw, pos = self.settings_widgets[pipe]
            #print 'activate', sw,pos
        else:
            sw = PipeWidget(pipe)
            pos = self.setting_stack.addWidget(sw)
            self.settings_widgets[pipe] = (sw, pos)
            #print 'new', sw,pos
        self.setting_stack.setCurrentIndex(pos)

    def add_pipe(self):
        pipetypename = str(self.typecombo.currentText())
        pipetype = self.types[pipetypename]
        pipe = pipetype(pipetypename)
        self.pipechain.add_pipe(pipe)
        self.pipemodel.pipedata = self.pipechain.imagepipes

class VisualizationPanel(ActionPanel):
    __doc__ = """Change visualization settings"""
    __shortname__ = "Visualization"
    settings_changed = QC.pyqtSignal(dict)
    def setup_ui(self):
        vis_layout = QG.QStackedLayout()
        self.setLayout(vis_layout)
        channels = self.imagedata.channels
        for channel in range(channels):
            vis_options = VisualizationOptionsWidget(self.pipechain, self, channel)
            vis_layout.addWidget(vis_options)
            vis_options.settings_changed.connect(self.settings_changed)
        vis_layout.setCurrentIndex(0)

    def channel_change(self, channel):
        self.layout().setCurrentIndex(channel)

class FramePanel(ActionPanel):
    __doc__ = """Choose channels and play frames for xyt scans"""
    __shortname__ = "Channels/Frames"

    channel_changed = QC.pyqtSignal(int)
    frame_changed = QC.pyqtSignal(int)

    def setup_ui(self):
        self.channel_combobox = QG.QComboBox()
        self.selection_slider = QG.QSlider(QC.Qt.Horizontal)
        self.selection_spinbox = QG.QSpinBox()

        vlayout = QG.QVBoxLayout()
        self.setLayout(vlayout)
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
        self.selection_slider.setMinimum(0)
        acquisitions = self.imagedata.acquisitions
        self.selection_slider.setMaximum(acquisitions-1)
        self.selection_slider.valueChanged.connect(self.frame_changed)
        self.time_range_start = 0
        self.time_range_end = acquisitions - 1
        self.update_time_range_label(0)
        self.selection_spinbox.setMinimum(0)
        self.selection_spinbox.setMaximum(acquisitions-1)
        self.selection_spinbox.valueChanged.connect(self.selection_slider.setValue)
        self.selection_slider.valueChanged.connect(self.selection_spinbox.setValue)
        self.selection_slider.valueChanged.connect(self.update_time_range_label)

        self.channel_combobox.setCurrentIndex(0)


        #FIXME
        #self.channel_combobox.currentIndexChanged.connect(vis_layout.setCurrentIndex)

        self.channel_combobox.currentIndexChanged.connect(self.channel_changed)

        channel_names = self.imagedata.channel_names
        for channel, name in channel_names.iteritems():
            ch_str = 'ch{}: {}'.format(channel, name)
            print ch_str
            self.channel_combobox.addItem(ch_str)

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
        if current>=self.time_range_start and current<=self.time_range_end:
            color = "green"
        else:
            color = "red"
        width = self.time_range_end - self.time_range_start
        region_text = "<p>Start: %i<br/>End: %i<br/>Duration:%i</p>"%(self.time_range_start,
                self.time_range_end, width)
        self.range_label.setText(region_text)
        self.set_range_label_color(color)

    def clear_time_range(self):
        self.time_range_start = 0
        self.time_range_end = self.imagedata.acquisitions
        self.update_time_range_label(0)

    def set_range_label_color(self, color=None):
        if color == None:
            color='transparent'
        self.range_label.setStyleSheet(" QLabel{ border: 3px solid %s;}"%color)

class AnalysisPanel(ActionPanel):
    __doc__ = """Choose analysis mode"""
    __shortname__ = "Analysis"
    def setup_ui(self):
        analysistype_layout = QG.QVBoxLayout()
        self.setLayout(analysistype_layout)
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

        plotIcon=QG.QIcon(":/chart_curve_go.png")
        plotFluorescencePB  = QG.QPushButton(plotIcon,'Next')
        plotFluorescencePB.setEnabled(False)
        plotFluorescencePB.clicked.connect(self.on_next_PB_clicked)
        self.plotFluorescencePB = plotFluorescencePB
        analysistype_layout.addWidget(plotFluorescencePB)

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
            self.roi_manager = LineManager(self.parentwidget.image_plot.fscene,
                        selection_types.data[key])
        elif key == 'imagetab.timeaverage':
            self.roi_manager = SnapROIManager(self.parentwidget.image_plot.fscene,
                        selection_types.data[key])
            if not self.analysis:
                self.analysis  = PixelByPixelAnalysis()
                self.analysis.imagefile = self.imagedata.mimage
        else:
            self.roi_manager = ROIManager(self.parentwidget.image_plot.fscene,
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
            pass
            #fltab = SparkTab(selections_by_type_name, self.imagedata, self)

        elif self.analysis_mode == "SparkDetect":
            pass
            #idata = ImageDataMaker.from_imagedata(self.imagedata)
            #idata.replace_channel(self.pipechain.get_result_data())
            #next_tab = SparkRegionsTab(selections_by_type_name, idata, self.analysis, self)
        elif self.analysis_mode == "PseudoLineScan":
            from lsjuicer.ui.tabs.imagetabs import AnalysisImageTab
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
                pc = PipeChain(new_data.pixel_size, self.parentwidget.image_plot.fscene)
                pc.set_source_data(new_data.all_image_data[channel])
                pcs[channel] = pc
            selections_by_type = defaultdict(list)
            next_tab = FluorescenceTab(selections_by_type, new_data, pcs, self.aw)
        #self.setCurrentIndex(1)
        #if self.analysis_mode != "PseudoLineScan":
        if 1:
            next_icon = QG.QIcon(':/chart_curve.png')
        self.aw.add_tab(next_tab, next_icon, self.analysis_mode)
