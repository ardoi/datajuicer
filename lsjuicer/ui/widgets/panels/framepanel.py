from PyQt5 import QtCore as QC
from PyQt5 import QtWidgets as QW

from actionpanel import ActionPanel
from lsjuicer.ui.widgets.smallwidgets import FramePlayer
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
import lsjuicer.inout.db.sqla as sa

class FramePanel(ActionPanel):
    __doc__ = """Choose channels and play frames for xyt scans"""
    __shortname__ = "Channels/Frames"

    channel_changed = QC.pyqtSignal(int)
    frame_changed = QC.pyqtSignal(int)

    def setup_ui(self):
        self.channel_combobox = QW.QComboBox()
        self.selection_slider = QW.QSlider(QC.Qt.Horizontal)
        self.selection_spinbox = QW.QSpinBox()

        vlayout = QW.QVBoxLayout()
        self.setLayout(vlayout)
        layout = QW.QHBoxLayout()
        layout.addWidget(QW.QLabel("Channel:"))
        layout.addWidget(self.channel_combobox)
        vlayout.addLayout(layout)
        layout = QW.QHBoxLayout()
        layout.addWidget(QW.QLabel("Frame:"))
        layout.addWidget(self.selection_slider)
        layout.addWidget(self.selection_spinbox)
        vlayout.addLayout(layout)

        layout = QW.QHBoxLayout()
        set_start_pb = QW.QPushButton("Set start")
        set_end_pb = QW.QPushButton("Set end")
        clear_pb = QW.QPushButton("Clear")
        layout.addWidget(set_start_pb)
        layout.addWidget(set_end_pb)
        layout.addWidget(clear_pb)
        range_label = QW.QLabel("<p style='border:red;'>Start: -<br/>End: -<br/>Duration: -</p>")
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

    def provide_range(self):
        selection = {}
        selection[ISTN.TIMERANGE] = {'start':self.time_range_start, 'end':self.time_range_end}
        return selection

    def set_region(self, fitregion):
        if isinstance(fitregion, sa.PixelByPixelFitRegion):
            self.selection_slider.setValue(fitregion.start_frame)
            self.set_time_range_start()
            self.selection_slider.setValue(fitregion.end_frame)
            self.set_time_range_end()



