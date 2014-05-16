
from PyQt5 import QtCore as QC

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

import numpy as n

from lsjuicer.ui.widgets.plot_with_axes_widget import TracePlotWidget
from lsjuicer.ui.scenes import FDisplay
from lsjuicer.ui.items.selection import BoundaryManager, SelectionDataModel

from lsjuicer.data.models.datamodels import TransientDataModel
from lsjuicer.ui.views.dataviews import CopyTableView
from lsjuicer.static import selection_types
from lsjuicer.data.data import Fl_Data
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN

import lsjuicer.data.analysis.transient_find as tf


class AutoFitTransientTab(QW.QTabWidget):

    @property
    def fl_ds(self):
        return self.channel_fl_datas[self.channel]

    def __init__(self, rois, imagedata, pipechain, parent = None):
    #def __init__(self, parent = None):
        super(AutoFitTransientTab, self).__init__(parent)
        self.imagedata = imagedata
        self.channel_fl_datas = {}
        print 'ROIS are', rois
        if ISTN.ROI not in rois:
            r_r = [0,self.imagedata.x_points]
        else:
            r = rois[ISTN.ROI][0].graphic_item.rect()
            r_r = [min(int(r.x()),
                int(r.x() + r.width())),
                max(int(r.x()), int(r.x() + r.width())),\
                min(int(r.y()), int(r.y() + r.height())),\
                max(int(r.y()),int(r.y() + r.height()))]

        if ISTN.F0 not in rois:
            bgr = None
            bgr_r = None
        else:
            bgr = rois[ISTN.F0][0].graphic_item.rect()
            bgr_r = [min(int(bgr.x()),
                     int(bgr.x() + bgr.width())),
                     max(int(bgr.x()), int(bgr.x() + bgr.width())),
                     min(int(bgr.y()), int(bgr.y() + bgr.height())),
                     max(int(bgr.y()), int(bgr.y() + bgr.height()))]
        pc_data = pipechain.get_result_data()
        for channel in range(self.imagedata.channels):
            #channel_data = self.imagedata.all_image_data[channel]
            channel_data = pc_data[channel]
            fds = Fl_Data(channel_data,
                          self.imagedata.timestamps[r_r[0]:r_r[1]],
                          r_r, bgr_r, True)
            #FIXME
            #fds.set_events(self.imagedata.event_times)
            #fds.set_gaps(self.imagedata.gaps)
            self.channel_fl_datas[channel] = fds

        self.setup_ui()
        self.filename = None
        self.channel = 0
        self.parent = parent
        self.new_transients = None
        self.approved_transients = None
        self.toggling_buttons = False
        window=QW.QApplication.activeWindow()
        self.status = window.statusBar()
        QC.QTimer.singleShot(50, lambda :self.initialPlots())



    def initialPlots(self):
        def color_yield():
            colors = ['red','blue','green','orange','yellow','black','brown']
            for color in colors:
                yield QG.QColor(color)

        c = color_yield()
        for channel in self.channel_fl_datas:
            channel_fl_data = self.channel_fl_datas[channel]
            color = c.next()
            #color_lighter = QG.QColor(color)
            #color_lighter.setAlpha(100)
            #print channel, min(channel_fl_data.fl.data),max(channel_fl_data.fl.data)
            self.fplot.addPlot('Fluorescence {}'.format(channel),
                               #channel_fl_data.physical_x_axis_values.data,
                               n.arange(channel_fl_data.fl.data.size),
                               channel_fl_data.fl.data,
                               {'color': color, 'size': 1})
            #channel_fl_data.smooth(times=2, wl=[5, 5])
            #self.fplot.addPlot('Smoothed %i'%channel,
            #                   #channel_fl_data.physical_x_axis_values.data,
            #                   n.arange(channel_fl_data.smoothed.data.size),
            #                   channel_fl_data.smoothed.data,
            #                   {'color': color_lighter, 'size': 2})
        #self.fplot.fitView(0)
        print 'fplot',self.fplot.size()

    def channel_visibility(self, state):
        for i,cb in enumerate(self.channel_checkboxes):
            state = cb.isChecked()
            self.fplot.toggle_plot("Fluorescence %i"%i, state)
            self.fplot.toggle_plot("Smoothed %i"%i, state)


    def setup_ui(self):
        main_layout = QW.QGridLayout()
        self.setLayout(main_layout)
        #closeIcon = QG.QIcon(":/cancel.png")
        #self.closePB = QG.QPushButton(closeIcon, 'Close tabs')
        #self.setCornerWidget(self.closePB)
        #self.closePB.setEnabled(False)

        self.fplot = TracePlotWidget(sceneClass = FDisplay, antialias = True, parent = None)
        #self.plotAndZoomLayout = QG.QVBoxLayout()
        #self.zoomButtonLayout  = QG.QHBoxLayout()
        #self.plotAndZoomLayout.addWidget(self.fplot)
        #self.plotAndZoomLayout.addLayout(self.zoomButtonLayout)
        main_layout.addWidget(self.fplot,0,0)

        #Widget for transient group selection


        main_layout.setSpacing(2)

        #main layout for right hand buttons and widgets
        tool_layout = QW.QVBoxLayout()
        tool_layout.setContentsMargins(2, 2,2, 2)
        channel_box = QW.QGroupBox("Channels")
        channel_main_layout = QW.QVBoxLayout()
        channel_layout=QW.QVBoxLayout()
        channel_box.setLayout(channel_main_layout)
        channel_main_layout.addLayout(channel_layout)
        self.channel_checkboxes=[]
        for channel in self.channel_fl_datas:
            checkbox = QW.QCheckBox("Channel %i"%channel)
            channel_layout.addWidget(checkbox)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self.channel_visibility)
            self.channel_checkboxes.append(checkbox)


        save_data_icon = QG.QIcon(':/report_disk.png')
        save_pb = QW.QPushButton(save_data_icon, "Save traces")
        save_layout = QW.QHBoxLayout()
        save_layout.addWidget(save_pb)
        channel_main_layout.addLayout(save_layout)
        self.save_label = QW.QLabel()
        save_layout.addWidget(self.save_label)


        detection_box = QW.QGroupBox('Detection')
        detection_layout = QW.QVBoxLayout()
        detection_box.setLayout(detection_layout)


        #detection_layout.addWidget(self.pb_manual)

        auto_icon = QG.QIcon(":/wand.png")
        self.pb_auto  = QW.QPushButton(auto_icon, 'Fit' )
        detection_layout.addWidget(self.pb_auto)
        self.pb_auto.clicked.connect(self.find_transients)


        tool_layout.addWidget(channel_box)
        tool_layout.addWidget(detection_box)
        #main_layout.addWidget(self.fButtonWidget)


        ####
        #smoothing
        #
        self.smooth_widget = QW.QWidget()
        smooth_widget_layout = QW.QVBoxLayout()
        smooth_widget_layout.setContentsMargins(0,0,0,0)
        self.smooth_widget.setLayout(smooth_widget_layout)
        initval = 1
#        initval=5
        self.label_smoothing_value = QW.QLabel("Smoothing: " + str(initval))
        self.label_smoothing_value.setToolTip('Amount of smoothing to be done \non fluorescence signal')
        smooth_widget_layout.addWidget(self.label_smoothing_value)
        detection_layout.addWidget(self.smooth_widget)

        self.slider_smoothing = QW.QSlider(QC.Qt.Horizontal)
        self.slider_smoothing.setSizePolicy(QW.QSizePolicy.Minimum, QW.QSizePolicy.Minimum)
        self.slider_smoothing.setSingleStep(1)
        self.slider_smoothing.setValue(initval)
        self.slider_smoothing.setRange(0, 40)
        smooth_widget_layout.addWidget(self.slider_smoothing)
        self.slider_smoothing.valueChanged[int].connect(
            lambda x: self.label_smoothing_value.setText("Smoothing: %i"%x))
        #
        ####

        ####
        #
        #Detection
        detection_widget_layout = QW.QVBoxLayout()
        detection_widget_layout.setContentsMargins(0,0,0,0)
        self.detection_widget = QW.QWidget()
        self.detection_widget.setLayout(detection_widget_layout)
        initval = 15
        self.label_detection_value = QW.QLabel("Detection: "+str(initval))
        self.label_detection_value.setToolTip('Amount of smoothing to be done \ non fluorescence signal')
        detection_widget_layout.addWidget(self.label_detection_value)
        detection_layout.addWidget(self.detection_widget)


        self.slider_detection = QW.QSlider(QC.Qt.Horizontal)
        self.slider_detection.setSizePolicy(QW.QSizePolicy.Minimum, QW.QSizePolicy.Minimum)
        self.slider_detection.setSingleStep(10)
        self.slider_detection.setValue(initval)
        self.slider_detection.setRange(1, 200)
        detection_widget_layout.addWidget(self.slider_detection)
        self.slider_detection.setObjectName('Detection slider')
        detection_layout.addWidget(self.detection_widget)
        self.slider_detection.valueChanged[int].connect(
            lambda x: self.label_detection_value.setText("Detection: %i"%x))
        #
        ####




        ####
        #
        # Transient edit widget
        self.transient_action_widget = QW.QWidget()
        transient_action_layout = QW.QVBoxLayout()
        self.transient_action_widget.setLayout(transient_action_layout)
        self.transient_tableview = CopyTableView()
        self.transient_datamodel = TransientDataModel()
        #boxdelegate = CheckBoxDelegate()
        self.transient_tableview.setModel(self.transient_datamodel)
        #self.transient_tableview.setItemDelegateForColumn(9, boxdelegate)
        #transient_tableview.horizontalHeader().setSectionResizeMode(0, QG.QHeaderView.ResizeToContents)
        #transient_tableview.horizontalHeader().setSectionResizeMode(1, QG.QHeaderView.ResizeToContents)
        #transient_tableview.horizontalHeader().setSectionResizeMode(2, QG.QHeaderView.ResizeToContents)
        self.transient_tableview.horizontalHeader().setSectionResizeMode(
                QW.QHeaderView.ResizeToContents)
        self.transient_tableview.horizontalHeader().setStretchLastSection(True)
        self.transient_tableview.verticalHeader().setSectionResizeMode(QW.QHeaderView.Fixed)
        self.transient_tableview.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        self.transient_tableview.setSelectionBehavior(QW.QAbstractItemView.SelectRows)
        self.transient_tableview.setSelectionMode(QW.QAbstractItemView.ExtendedSelection)
        transient_action_layout.addWidget(self.transient_tableview)
        transient_action_toolbar = QW.QToolBar('Action')
        transient_action_toolbar.setToolButtonStyle(QC.Qt.ToolButtonTextUnderIcon)
        #transient_show_action.setCheckable(True)
        transient_action_toolbar.setEnabled(False)
        #transient_edit_on_action.setCheckable(True)
        transient_action_layout.addWidget(transient_action_toolbar)
        transient_action_toolbar.setContentsMargins(0,0,0,0)
        transient_action_layout.setAlignment(transient_action_toolbar, QC.Qt.AlignCenter)

        self.transient_tableview.setObjectName('Transient TableView')
        for ci in range(3,8+1):
            self.transient_tableview.hideColumn(ci)
        tool_layout.addWidget(self.transient_action_widget)


        tool_layout.addStretch()


        main_layout.addLayout(tool_layout,0,1,2,1)
        main_layout.setRowStretch(0,10)
        main_layout.setRowStretch(1,1)
        main_layout.setColumnStretch(0,5)
        main_layout.setColumnStretch(1,1)
        self.roi_manager = BoundaryManager(self.fplot.fscene, selection_types.data['transienttab'])
        #selection_widget = SelectionWidget()
        self.selection_datamodel = SelectionDataModel()
        self.selection_datamodel.set_selection_manager(self.roi_manager)
        #selection_widget.set_model(selection_datamodel)
        #self.lsmButtonLayout.addWidget(selection_widget)
        self.fplot.updateLocation.connect(self.updateCoords)



    def find_transients(self):
        print 'find transient'
        channel_fl_data = self.channel_fl_datas[0]
        xvals = n.arange(channel_fl_data.fl.data.size),
        yvals = channel_fl_data.fl.data
        #res = tf.fit_2_stage(yvals)
        n.savetxt("linefit.dat",yvals)

        print res

    def updateCoords(self, xv, yv, xs, ys):
        self.status.showMessage('x: %.3f, y: %.2f, sx: %i, sy: %i'%(xv, yv, xs, ys))


