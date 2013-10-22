import copy
import datetime

from PyQt5 import QtCore, QtWidgets

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

import numpy as n

from lsjuicer.ui.widgets.plot_with_axes_widget import TracePlotWidget
from lsjuicer.ui.scenes import FDisplay
from lsjuicer.ui.items.transient import VisualTransientCollection
from lsjuicer.ui.items.selection import BoundaryManager, SelectionDataModel
from lsjuicer.static.constants import TransientTabState as TS

from lsjuicer.data.models.datamodels import TransientDataModel
from lsjuicer.ui.views.dataviews import CopyTableView
from lsjuicer.static import selection_types
from lsjuicer.static.constants import TransientBoundarySelectionTypeNames as TBSTN
from lsjuicer.data.data import Fl_Data
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN

class SaveTracesDialog(QW.QDialog):
    def __init__(self, parent = None):
        super(SaveTracesDialog, self).__init__(parent)
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        location_layout = QW.QHBoxLayout()
        location_layout.addWidget(QW.QLabel("Saving to:"))
        #try:
        #    self.save_folder_name = Config.get_property('save_folder_name')
        #except KeyError:
        self.save_file_name = None
        self.location_label = QW.QLabel()
        location_layout.addWidget(self.location_label)
        location_change_pb = QW.QPushButton("Choose file")
        location_layout.addWidget(location_change_pb)
        layout.addLayout(location_layout)
        location_change_pb.clicked.connect(self.choose_file)

        exp_type_layout = QW.QHBoxLayout()
        exp_type_layout.addWidget(QW.QLabel('Experiment type:'))
        self.exp_type_combo = QW.QComboBox()
        #key = 'experiment.types'
        #if shelf_db.has_key(key):
        #    types = shelf_db[key]
        #else:
        #    types = []
        #exp_types = types
        #for exp_type in exp_types:
        #    self.exp_type_combo.addItem(exp_type)
        #try:
        #    key ='exp_type'
        #    exp_type = Config.get_property(key)
        #    index = exp_types.index(exp_type)
        #    self.exp_type_combo.setCurrentIndex(index)
        #except KeyError:
        #    pass


        exp_type_layout.addWidget(self.exp_type_combo)

        layout.addLayout(exp_type_layout)

        button_layout = QW.QHBoxLayout()
        self.save_pb = QW.QPushButton("Save")
        cancel_pb = QW.QPushButton("Cancel")
        button_layout.addWidget(self.save_pb)
        button_layout.addWidget(cancel_pb)
        self.save_pb.clicked.connect(self.accept)
        self.save_pb.setEnabled(False)
        cancel_pb.clicked.connect(self.reject)

        #fname_layout = QG.QHBoxLayout()
        #fname_layout.addWidget(QG.QLabel("File name"))
        #self.fname_box = QG.QLineEdit()
        #fname_layout.addWidget(self.fname_box)
        #layout.addLayout(fname_layout)

        comment_layout = QW.QHBoxLayout()
        comment_layout.addWidget(QW.QLabel("Comment"))
        self.comment_box = QW.QLineEdit()
        #self.comment_box.editingFinished.connect(self.ready)

        comment_layout.addWidget(self.comment_box)
        layout.addLayout(comment_layout)
        layout.addLayout(button_layout)

        self.set_location_label()

    def choose_file(self):
        filename = self.choose_file_dialog()
        self.save_file_name = filename
        self.set_location_label()

    def choose_file_dialog(self):
        save_file_name = str(QW.QFileDialog.getSaveFileName(self)[0])
        #Config.set_property('save_folder_name', save_folder_name)
        return save_file_name

    def set_location_label(self):
        if self.save_file_name:
            if ".csv" not in self.save_file_name:
                self.save_file_name+=".csv"
            self.location_label.setText(self.save_file_name)
            self.save_pb.setEnabled(True)
        else:
            self.location_label.setText("---")
            self.save_pb.setEnabled(False)



    def accept(self):
        self.exp_type = self.exp_type_combo.currentText()
        self.comment = self.comment_box.text()
        #Config.set_property('comment', self.comment)
        return QW.QDialog.accept(self)


def setAll(indices):
    if True in [isinstance(el, list) for el in indices]:
        outs = copy.deepcopy(indices)
        for el in outs:
            if isinstance(el, list):
                elindex = outs.index(el)
                cc = copy.deepcopy(outs)
                cc.remove(el)
                outs = []
                for ell in el:
                    ccc = copy.deepcopy(cc)
                    ccc.insert(elindex, ell)
                    outs.extend(setAll(ccc))
                return outs
    else:
        return indices

def outmake(inlist):
    out = []
    try:
        for el in inlist:
            for ell in el:
                out.append(ell)
        return out
    except TypeError:
        return inlist

def set_indices(indices, value, array):
    all_indices = n.array(setAll(indices))
    print len(array.shape)
    print all_indices,all_indices.shape,len(indices)
    all_indices.shape = (all_indices.shape[0]/len(array.shape),len(array.shape))
    #all_indices = tuple(n.array(setAll(indices),shape=(len(indices),3)).T)
    print all_indices,tuple(all_indices.T)
    array[tuple(all_indices.T)] = value

class TransientTab(QW.QTabWidget):

    @property
    def fl_ds(self):
        return self.channel_fl_datas[self.channel]

    def __init__(self, rois, imagedata, pipechains, parent = None):
    #def __init__(self, parent = None):
        super(TransientTab, self).__init__(parent)
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
                max(int(r.y()),int(r.y()+r.height()))]

        if ISTN.F0 not in rois:
            bgr = None
            bgr_r = None
        else:
            bgr = rois[ISTN.F0][0].graphic_item.rect()
            bgr_r = [min(int(bgr.x()),
                int(bgr.x() + bgr.width())),
                max(int(bgr.x()), int(bgr.x() + bgr.width())),\
                min(int(bgr.y()), int(bgr.y() + bgr.height())),
                max(int(bgr.y()), int(bgr.y()+bgr.height()))]

        for channel in range(self.imagedata.channels):
            #channel_data = self.imagedata.all_image_data[channel]
            channel_data = pipechains[channel].get_result_data()
            fds =  Fl_Data(channel_data,
                    self.imagedata.timestamps[r_r[0]:r_r[1]],
                    r_r, bgr_r, True)
            #FIXME
            #fds.set_events(self.imagedata.event_times)
            #fds.set_gaps(self.imagedata.gaps)
            self.channel_fl_datas[channel] = fds

        self.state_matrix = {}
        self.state = [0, 0, 0]
        self.state[TS.TRANSIENTS] = TS.TRANSIENTS_NONE
        self.state[TS.SELECTIONMODE] = TS.SELECTIONMODE_NONE
        self.state[TS.SELECTION] = TS.SELECTION_NONE
        self.tabs_present = []
        self.setup_ui()
        self.filename = None
        self.channel = 0
        self.parent = parent
        self.new_transients = None
        self.approved_transients = None
        self.toggling_buttons = False
        self.toggle_buttons()
        QtCore.QTimer.singleShot(50, lambda :self.initialPlots())

    def setName(self,name):
        self.filename = name

    def activeView(self):
        activeIndex = self.currentIndex()
        if activeIndex == 0:
            widget = self.fplot
        else:
            widget = self.widget(activeIndex)
        return widget.fV, self.tabText(activeIndex)

    def getAllViews(self):
        views = []
        for tabno in range(self.count()):
            if tabno == 0:
                widget = self.fplot
            else:
                widget = self.widget(tabno)
            views.append([widget.fV, self.tabText(tabno)])
        return views

    def setStatus(self, status):
        self.status = status

    def initialPlots(self):
        def color_yield():
            colors = ['red','blue','green','orange','yellow','black','brown']
            for color in colors:
                yield QG.QColor(color)

        c = color_yield()
        for channel in self.channel_fl_datas:
            channel_fl_data = self.channel_fl_datas[channel]
            color = c.next()
            color_lighter = QG.QColor(color)
            color_lighter.setAlpha(100)
            #print channel, min(channel_fl_data.fl.data),max(channel_fl_data.fl.data)
            self.fplot.addPlot('Fluorescence %i'%channel, channel_fl_data.fl.data,
                    channel_fl_data.physical_x_axis_values.data, color = color_lighter,
                    size=1,visibility=True, physical = False)
            channel_fl_data.smooth(times = 2, wl = [5,5])
            self.fplot.addPlot('Smoothed %i'%channel, channel_fl_data.smoothed.data,
                    channel_fl_data.physical_x_axis_values.data, color = color,
                        size=2, physical = False)
        #self.set_smooth()
        #self.fplot.addHLines(self.ds.events,Constants.EVENTS,'navy')
        #self.fplot.addHLines(self.ds.gaps,Constants.GAPS, 'orange')
        self.fplot.fitView(0)
        print 'fplot',self.fplot.size()

    def channel_visibility(self, state):
        for i,cb in enumerate(self.channel_checkboxes):
            state = cb.isChecked()
            self.fplot.toggle_plot("Fluorescence %i"%i, state)
            self.fplot.toggle_plot("Smoothed %i"%i, state)

    def save_traces(self):
        dialog = SaveTracesDialog(parent=self)
        if dialog.exec_():
            #save_folder_name = str(dialog.save_folder_name)
            fullfname = str(dialog.save_file_name)
            exp_type = str(dialog.exp_type)
            comment = str(dialog.comment)
            print 'fullfname',fullfname
            f = open(fullfname,'w')
            f.write("#Saved on: %s\n"%str(datetime.datetime.now()))
            f.write("#Comment: %s\n"%comment)
            f.write("#Experiment type: %s\n"%exp_type)
            f.write("#Image: %s\n"%self.imagedata.name)
            header = "#\n#Column names follow ->\n"
            cnames=["#Time"]
            for channel in self.channel_fl_datas:
                cnames.append("Fluorescence ch %i"%channel)
                cnames.append("Smooth ch %i"%channel)
            header+=", ".join(cnames)
            header += "\n"
            f.write(header)
            time_data = self.fl_ds.physical_x_axis_values.data
            rows = []
            for i in range(len(time_data)):
                rowdata = ["%.5f"%time_data[i]]
                for channel in self.channel_fl_datas:
                    ch_data = self.channel_fl_datas[channel]
                    rowdata.append("%.5f"%ch_data.fl.data[i])
                    rowdata.append("%.5f"%ch_data.smoothed.data[i])
                row = ", ".join(rowdata)
                row += "\n"
                rows.append(row)
            for row in rows:
                f.write(row)
            f.close()
            QW.QMessageBox.information(self,'Done',"%i rows saved to %s"%(len(rows),fullfname))
            self.save_label.setText("Saved")






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
        save_pb.clicked.connect(self.save_traces)
        save_layout = QW.QHBoxLayout()
        save_layout.addWidget(save_pb)
        channel_main_layout.addLayout(save_layout)
        self.save_label = QW.QLabel()
        save_layout.addWidget(self.save_label)


        detection_box = QW.QGroupBox('Detection')
        detection_layout = QW.QVBoxLayout()
        detection_box.setLayout(detection_layout)

        manual_icon = QG.QIcon(":/user.png")
        self.pb_manual = QW.QPushButton(manual_icon,'Manual')
        self.pb_manual.setObjectName('Manual PB')
        #self.pb_manual.setEnabled(False)
        self.pb_manual.setCheckable(True)

        d = n.zeros((3,3,2), dtype=bool)
        settings = [[TS.TRANSIENTS_HIDDEN,TS.TRANSIENTS_NONE],
                [TS.SELECTIONMODE_NONE,TS.SELECTIONMODE_MANUAL],
                TS.SELECTION_ALL]
        set_indices(settings, True, d)
        self.state_matrix.update({self.pb_manual:d})
        detection_layout.addWidget(self.pb_manual)

        auto_icon = QG.QIcon(":/wand.png")
        self.pb_auto  = QW.QPushButton(auto_icon, 'Automatic' )
        self.pb_auto.setObjectName('Auto PB')
        self.pb_auto.setCheckable(True)
        d = n.zeros((3,3,2),dtype=bool)
        settings = [[TS.TRANSIENTS_HIDDEN,TS.TRANSIENTS_NONE],
                [TS.SELECTIONMODE_NONE,TS.SELECTIONMODE_AUTO], TS.SELECTION_ALL]
        set_indices(settings, True, d)
        self.state_matrix.update({self.pb_auto:d})
        detection_layout.addWidget(self.pb_auto)

        find_icon = QG.QIcon(":/find.png")
        self.pb_find = QW.QPushButton(find_icon, 'Find')
        self.pb_find.setObjectName('Find PB')
        d = n.zeros((3,3,2),dtype=bool)
        settings = [[TS.TRANSIENTS_HIDDEN,TS.TRANSIENTS_NONE],
                [TS.SELECTIONMODE_MANUAL,TS.SELECTIONMODE_AUTO], TS.SELECTION_PRESENT]
        set_indices(settings, True, d)
        self.state_matrix.update({self.pb_find:d})
#        self.fPB2.setEnabled(False)

        detection_layout.addWidget(self.pb_find)
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

        self.slider_smoothing = QW.QSlider(QtCore.Qt.Horizontal)
        self.slider_smoothing.setSizePolicy(QW.QSizePolicy.Minimum, QW.QSizePolicy.Minimum)
        self.slider_smoothing.setSingleStep(1)
        self.slider_smoothing.setValue(initval)
        self.slider_smoothing.setRange(0, 40)
        d = n.zeros((3,3,2),dtype=bool)
        settings = [TS.TRANSIENTS_NONE, TS.SELECTIONMODE_ALL, TS.SELECTION_ALL]
        set_indices(settings, True, d)
        self.smooth_widget.setObjectName('Smooth widget')
        self.state_matrix.update({self.smooth_widget:d})
        smooth_widget_layout.addWidget(self.slider_smoothing)
        self.slider_smoothing.valueChanged[int].connect(\lambda x: self.label_smoothing_value.setText("Smoothing: %i"%x))
        self.slider_smoothing.sliderReleased.connect(self.set_smooth)
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


        self.slider_detection = QW.QSlider(QtCore.Qt.Horizontal)
        self.slider_detection.setSizePolicy(QW.QSizePolicy.Minimum, QW.QSizePolicy.Minimum)
        self.slider_detection.setSingleStep(10)
        self.slider_detection.setValue(initval)
        self.slider_detection.setRange(1, 200)
        detection_widget_layout.addWidget(self.slider_detection)
        d = n.zeros((3,3,2),dtype=bool)
        settings = [TS.TRANSIENTS_ALL,
                TS.SELECTIONMODE_AUTO, TS.SELECTION_PRESENT]
        set_indices(settings, True, d)
        self.slider_detection.setObjectName('Detection slider')
        detection_layout.addWidget(self.detection_widget)
        self.state_matrix.update({self.detection_widget:d})
        self.slider_detection.valueChanged[int].connect(\lambda x: self.label_detection_value.setText("Detection: %i"%x))
        self.slider_detection.sliderReleased.connect(self.find_transients)
        #
        ####


        ####
        #
        #Plotting
        plot_box = QW.QGroupBox('Plotting')
        plot_layout = QW.QVBoxLayout()
        plot_box.setLayout(plot_layout)
        self.pb_show_transients = QW.QPushButton('Show transients')
        d = n.zeros((3,3,2),dtype=bool)
        settings = [TS.TRANSIENTS_HIDDEN, TS.SELECTIONMODE_NONE, TS.SELECTION_NONE]
        set_indices(settings, True, d)
        self.pb_show_transients.setObjectName('Show PB')
        self.state_matrix.update({self.pb_show_transients:d})
        tool_layout.addWidget(self.pb_show_transients)
        self.pb_show_transients.setCheckable(True)
        plot_layout.addWidget(self.pb_show_transients)

        accept_icon = QG.QIcon(":/accept.png")
        self.pb_accept_transients = QW.QPushButton(accept_icon,'Accept')
        self.pb_accept_transients.setVisible(False)
        plot_layout.addWidget(self.pb_accept_transients)

        reject_icon = QG.QIcon(":/cancel.png")
        self.pb_reject_transients = QW.QPushButton(reject_icon,'Reject')
        self.pb_reject_transients.setVisible(False)
        plot_layout.addWidget(self.pb_reject_transients)

        tool_layout.addWidget(plot_box)
        #
        ####

        ####
        #
        #Analysis
        do_analysis_layout = QW.QVBoxLayout()
        analyze_icon = QG.QIcon(":/calculator.png")
        self.pb_analyze = QW.QPushButton(analyze_icon, 'Analyze')

        d = n.zeros((3, 3, 2),dtype=bool)
        settings = [[TS.TRANSIENTS_HIDDEN,TS.TRANSIENTS_VISIBLE],
                TS.SELECTIONMODE_NONE, TS.SELECTION_NONE]
        set_indices(settings, True, d)
        self.pb_analyze.setObjectName('Analyze PB')
        self.state_matrix.update({self.pb_analyze:d})
        do_analysis_layout.addWidget(self.pb_analyze)
        tool_layout.addLayout(do_analysis_layout)
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
        self.transient_tableview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.transient_tableview.setSelectionBehavior(QW.QAbstractItemView.SelectRows)
        self.transient_tableview.setSelectionMode(QW.QAbstractItemView.ExtendedSelection)
        transient_action_layout.addWidget(self.transient_tableview)
        transient_action_toolbar = QW.QToolBar('Action')
        self.transient_tableview.items_selected.connect(transient_action_toolbar.setEnabled)
        transient_action_toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        transient_show_action = transient_action_toolbar.addAction(
                QG.QIcon(':/eye.png'), 'Show')
        #transient_show_action.setCheckable(True)
        transient_action_toolbar.setEnabled(False)
        transient_edit_on_action = transient_action_toolbar.addAction(
                QG.QIcon(':/pencil.png'), 'Edit')
        #transient_edit_on_action.setCheckable(True)
        transient_delete_action = transient_action_toolbar.addAction(
                QG.QIcon(':/delete.png'), 'Delete')
        transient_show_action.triggered.connect(self.transient_show_action_triggered)
        transient_edit_on_action.triggered.connect(self.transient_edit_on_action_triggered)
        transient_delete_action.triggered.connect(self.transient_delete_action_triggered)
        transient_action_layout.addWidget(transient_action_toolbar)
        transient_action_toolbar.setContentsMargins(0,0,0,0)
        transient_action_layout.setAlignment(transient_action_toolbar, QtCore.Qt.AlignCenter)

        d = n.zeros((3,3,2),dtype = bool)
        settings = [[TS.TRANSIENTS_HIDDEN, TS.TRANSIENTS_VISIBLE],
                TS.SELECTIONMODE_ALL, TS.SELECTION_ALL]
        set_indices(settings, True, d)
        self.transient_tableview.setObjectName('Transient TableView')
        for ci in range(3,8+1):
            self.transient_tableview.hideColumn(ci)
        self.state_matrix.update({self.transient_tableview:d})
        tool_layout.addWidget(self.transient_action_widget)
        #
        ####


        ####
        #
        # Group widget
        #groupW = QG.QWidget()
        #groupW.setLayout(QG.QHBoxLayout())
        #group_selection_widget = SelectionWidget(user_can_add_types=True, parent=self)
        #group_selection_widget.setSizePolicy(QG.QSizePolicy.Maximum,
        #        QG.QSizePolicy.Maximum)
        #key = 'transienttab.groups'
        #if shelf_db.has_key(key):
        #    selectiontypes = shelf_db[key]
        #else:
        #    selectiontypes = []

        #FIXME group selections
        #self.group_manager = BoundaryManager(self.fplot.fscene,
        #        defaults.selection_types.data['transienttab.groups'])
        #self.group_manager = BoundaryManager(self.fplot.fscene, selectiontypes)
        #group_datamodel = SelectionDataModel()
        #group_datamodel.set_selection_manager(self.group_manager)
        #group_selection_widget.set_model(group_datamodel)
        #groupW.layout().addWidget(group_selection_widget)
        #tool_layout.addWidget(groupW)

        #pb.setSizePolicy(QG.QSizePolicy.Minimum, QG.QSizePolicy.Minimum)
        #groupWidget.setSizePolicy(QG.QSizePolicy.Minimum, QG.QSizePolicy.Minimum)
        #self.fplot.extendControlArea(groupW)
        #
        ####

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
        self.pb_manual.toggled[bool].connect(self.pb_manual_toggled)
        self.pb_auto.toggled[bool].connect(self.pb_auto_toggled)
        self.roi_manager.ROI_available.connect(lambda: self.enable_find(True))
        self.fplot.updateLocation.connect(self.updateCoords)
        self.pb_find.clicked[()].connect(self.find_transients)
        self.pb_show_transients.toggled[bool].connect(self.toggleTransients)
        self.pb_accept_transients.clicked[()].connect(self.acceptKeyPressed)
        self.pb_reject_transients.clicked[()].connect(self.rejectPBPressed)
        self.pb_analyze.clicked[()].connect(self.analyze)

    def transient_show_action_triggered(self):
        selected = self.transient_tableview.selectedIndexes()
        if selected:
            self.transient_datamodel.set_transients_visible(selected)
            pass
        else:
            return
#    def transient_hide_action_triggered(self):
#        selected = self.transient_tableview.selectedIndexes()
#        if selected:
#            self.transient_datamodel.set_transients_visible(selected, False)
#            pass
#        else:
#            return
    def transient_edit_on_action_triggered(self):
        selected = self.transient_tableview.selectedIndexes()
        if selected:
            self.transient_datamodel.set_transients_visible(selected)
            self.transient_datamodel.set_transients_editable(selected)
            pass
        else:
            return
#    def transient_edit_off_action_triggered(self):
#        selected = self.transient_tableview.selectedIndexes()
#        if selected:
#            self.transient_datamodel.set_transients_visible(selected, False)
#            self.transient_datamodel.set_transients_editable(selected, False)
#        else:
#            return
    def transient_delete_action_triggered(self):
        selected = self.transient_tableview.selectedIndexes()
        if selected:
            self.transient_datamodel.remove_transients(selected)

    def enable_find(self, toggle):
        print 'enable find',toggle
        if toggle:
            self.state[TS.SELECTION]=TS.SELECTION_PRESENT
        else:
            self.state[TS.SELECTION]=TS.SELECTION_NONE

        self.toggle_buttons()

    def pb_auto_toggled(self, toggle):
        if not self.toggling_buttons:
            #self.roi_manager.setAutomaticROIActive(toggle)
            self.roi_manager.activate_builder_by_type_name(TBSTN.AUTO)
            if toggle:
                self.state[TS.SELECTIONMODE] = TS.SELECTIONMODE_AUTO
            else:
                self.state[TS.SELECTIONMODE] = TS.SELECTIONMODE_NONE
            self.toggle_buttons()

    def pb_manual_toggled(self, toggle):
        if not self.toggling_buttons:
            #self.roi_manager.setManualROIActive(toggle)
            self.roi_manager.activate_builder_by_type_name(TBSTN.MANUAL)
            if toggle:
                self.state[TS.SELECTIONMODE] = TS.SELECTIONMODE_MANUAL
            else:
                self.state[TS.SELECTIONMODE] = TS.SELECTIONMODE_NONE
            self.toggle_buttons()

    #def showOptions(self, show):
    #    print 'show', show
    #    if show:
    #        self.OptionFrame.show()
    #    else:
    #        self.OptionFrame.hide()

    def acceptKeyPressed(self):
        #self.roi_manager.activeBuilder.clear()
        self.accept_transients()

    def accept_transients(self):
        print 'ACCEPT'
        print 'keys1',self.new_transients.transients.keys()
        channel_fl_data = self.fl_ds
        channel_fl_data.addTransientGroup(self.new_transients)
        print 'b'
        self.temp_transients.hideAll()
        print 'keys2',self.new_transients.transients.keys()
        if self.approved_transients is None:
            color = QG.QColor(140, 0, 250, 128)
            self.approved_transients = VisualTransientCollection(self.new_transients, self.fplot, color)
            self.approved_transients.maxUpdate.connect(self.update_maxima)
        self.approved_transients.showAll()
        self.approved_transients.hideAll()
        print 'approved transients0',self.approved_transients.visual_transients.keys()
        self.showNewTransients(False)
        #self.transients = self.new_transients
        self.new_transients = None
        print 'approved transients1',self.approved_transients.visual_transients.keys()
        self.transient_datamodel.set_visual_transient_collection(self.approved_transients)
        self.roi_manager.remove_selections()
        self.roi_manager.disable_builder()
        #self.pb_show_transients.setChecked(False)
        #self.roi_manager.setAutomaticROIActive(False)

    def rejectPBPressed(self):
#        if self.roi_manager.isManualROIActive():
#            rois = self.roi_manager.getROIs()[Constants.MANUAL]
#
#        roi=self.roi_manager.getROIs()[Constants.AUTOMATIC][0]
        self.roi_manager.activeBuilder.clear()
        self.reject_transients()

    def reject_transients(self):
        print 'reject'
        if self.approved_transients:
            print 'approved',self.approved_transients.transient_group
        self.new_transients = None
        self.showNewTransients(False)
        self.temp_transients.hideAll()
        #self.pb_show_transients.setChecked(False)
        self.pb_accept_transients.setVisible(False)
        self.pb_reject_transients.setVisible(False)

    def update_maxima(self):
        print 'update max'
        #?self.removeMaxs()
        if self.new_transients:
            tG = self.new_transients
        else:
            if self.approved_transients:
                tG = self.approved_transients.transient_group
            else:
                self.fplot.removePlotByName('Maxima')
                return
        print tG
        if not tG:
            return
        maxima, times= tG.get_amps()
        if not hasattr(self,'maxplot_d'):
            print 'plot'
            self.maxplot_d = self.fplot.addPlot('Maxima', maxima, times, size = 10, type = 'circles')
        else:
            print 'update'
            self.maxplot_d = self.fplot.updatePlot('Maxima', maxima, times)
        self.fplot.fscene.update(self.fplot.fscene.sceneRect())
#        self.fplot.fV.update()

    def close_tabs(self):
        #self.closePB.setEnabled(False)
        while self.count() > 1:
            self.removeTab(self.count() - 1)
        for tab in self.tabs_present:
            delattr(self, tab)
        self.tabs_present = []

    #def compareBase(self, save = False):
    #    #self.closePB.setEnabled(True)
    #    if not hasattr(self, 'compareTab'):
    #        self.comparecount= 0
    #        self.comparePlot = PathPlotWidget()
    #        #self.connect(self.comparePlot, QC.SIGNAL('updateLocation(float, float, float, float)'), self.updateCoords)
    #        self.compareTab = self.addTab(self.comparePlot, 'Comparison')
    #        self.presentTabs.append('compareTab')
    #    if self.fplot.fscene.manual:
    #        edges = []
    #        for tb in self.fplot.fscene.transientBoundaries:
    #            x1 = tb[0].shape().elementAt(1).x
    #            x2 = tb[1].shape().elementAt(1).x
    #            start = self.fplot.scene2data((min(x1, x2), 0)).x()
    #            end = self.fplot.scene2data((max(x1, x2), 0)).x()
    #            edges.append((start, end))
    #        #print edges
    #    if save:
    #        #creationtime = datetime.datetime.now()
    #        #im_id = creationtime.strftime('%m-%d_%H-%M-%S')
    #        #filename = "transients_%s.dat"%im_id
    #        while True:
    #            name,ok = QG.QInputDialog.getText(self,'info','Please give file name to save',QG.QLineEdit.Normal,self.fname+".dat")
    #            if not os.path.isfile("res/"+name):
    #                break
    #        file = open("res/"+name,'w')
    #        if not ok:
    #            save = False
    #    for edge in edges:
    #        self.comparecount += 1
    #        tr = self.ds.make_transient(edge, True)
    #        xcoords = n.array(tr.phys_x) - tr.phys_x0
#   #         n.savetxt(filename, n.array([xcoords,tr.data]))
    #        if save:
    #            pickle.dump([xcoords,tr.data],file)
    #        self.comparePlot.addPlot('Compare', tr.data, xcoords, color = self.comparecolors[self.comparecount - 1], append = True, movable = True)

    #def compareSave(self):
    #    self.compareBase(save = True)

    #def compare(self):
    #    self.compareBase()


#    def manualmode(self, mode):
#        pass
#        ##self.fplot.fscene.toggleManualSelection(mode)
#        #if mode:
#        #    #self.removeMaxs()
#        #    self.fPB3.setChecked(False)
#        #    self.fPB2.setEnabled(False)
#        #    #self.qsettingsB.setVisible(False)
#        #    self.fPB1.setEnabled(False)
#        #    self.fPB4.setEnabled(False)
#        #    self.CBBox.setEnabled(False)
#        #    self.comparePB.setEnabled(False)
#        #    self.compareSavePB.setEnabled(False)
#        #else:
#        #    self.fPB1.setEnabled(True)
#        #    if self.fplot.fscene.transientBoundaries:
#        #        self.comparePB.setEnabled(True)
#        #        self.compareSavePB.setEnabled(True)
#        #        self.fPB2.setEnabled(True)
#        #        self.CBBox.setEnabled(True)
#
#    #def setDSmooth(self):
#    #    #smooth_val = self.qds.value()
#    #    #edges = []
#    #    self.fPB3.setChecked(False)
#    #    x1 = self.fplot.fscene.bline1.shape().elementAt(1).x
#    #    x2 = self.fplot.fscene.bline2.shape().elementAt(1).x
#    #    if x1 < 0:
#    #        x1 = 1
#    #    if x2 > 1200:
#    #        x2 = 1200 - 1
#    #    #start_x = self.fplot.scene2data((min(x1, x2), 0)).x()
#    #    #end_x = self.fplot.scene2data((max(x1, x2), 0)).x()
#    #    #self.ds.find_maximums(start_treshold, stop_treshold, min_time, start_x, end_x)
#    #    self.find_transients()
#    #    #self.ds.find_transients(start_x, end_x, smooth_val)
#    #    #self.removeMaxs()
#    #    #print 'm', self.ds.my
#    #    #self.maxplot_d = self.fplot.addPlot('Maxima', self.ds.my, self.ds.pmx, size = 10, type = 'circles')
#    #    #self.fPB4.setEnabled(True)
#

    def set_smooth(self):
        smooth_val = self.slider_smoothing.value()
        for channel in self.channel_fl_datas:
            channel_fl_data = self.channel_fl_datas[channel]
            channel_fl_data.smooth(times = 2, wl = [smooth_val,smooth_val])
        #self.ds.smooth(times = 2, wl = [5, smooth_val])
        #self.smoothed_plot = self.fplot.updatePlot('Smoothed', self.ds.smoothed.data, self.ds.physical_x_axis_values.data, color = 'red', size = 2)
            self.smoothed_plot = self.fplot.updatePlot('Smoothed %i'%channel, channel_fl_data.smoothed.data, channel_fl_data.physical_x_axis_values.data)

    #def toggleEvents(self, show):
    #    if show:
    #        self.fplot.addHLines(self.ds.events,'navy')
    #        self.fplot.addHLines(self.ds.gaps,'orange')
    #    else:
    #        self.fplot.removeHlines()


#    def baselinePlotUpdate(self):
#        self.removeBaselines()
#        if self.new_transients:
#            tG = self.new_transients
#        else:
#            tG = self.ds.transientGroup
#        transients = tG.transients.values()
#        for tr in transients:
#            bl = self.fplot.addVLine(tr.start_phys,tr.bl_end_phys,tr.bl)
#            self.baselines.append(bl)

#    def removeBaselines(self):
#        if hasattr(self,'baselines'):
#            for b in self.baselines:
#                self.fplot.removeItem(b)
#        self.baselines = []

    def showNewTransients(self,show):
        print 'show new'
        if show:
            self.pb_reject_transients.setVisible(True)
            self.pb_accept_transients.setVisible(True)
            color = QG.QColor(140, 0, 150,128)
            self.temp_transients = VisualTransientCollection(self.new_transients, self.fplot, color)
            self.temp_transients.showAll()
            self.state[TS.TRANSIENTS] = TS.TRANSIENTS_VISIBLE
            print 'setting tempttrs',self.state
        else:
            self.pb_reject_transients.setVisible(False)
            self.pb_accept_transients.setVisible(False)
            self.temp_transients.hideAll()
            if self.approved_transients:
                self.state[TS.TRANSIENTS] = TS.TRANSIENTS_HIDDEN
            else:
                self.state[TS.TRANSIENTS] = TS.TRANSIENTS_NONE
            self.state[TS.SELECTIONMODE] = TS.SELECTIONMODE_NONE
            self.state[TS.SELECTION] = TS.SELECTION_NONE
        #print self.state
        self.toggle_buttons()
        self.update_maxima()
        self.fplot.reframe()


    def toggleTransients(self, show):
        if show:
            self.approved_transients.showAll()
            self.update_maxima()
        else:
            self.approved_transients.hideAll()

    def analyze(self):
        self.parent.makeResTab()
        groups = []
        #rois=self.group_manager.getROIs()[Constants.GROUP]
        #rois = self.group_manager.selections
        #print rois
        #print dir(rois[0])
        #for roi in rois:
        #    x1 = roi.graphic_item.rect().left()
        #    x2 = roi.graphic_item.rect().right()
        #    start_x = self.fplot.scene2data((min(x1, x2), 0)).x()
        #    end_x = self.fplot.scene2data((max(x1, x2), 0)).x()
        #    groups.append([roi,[start_x,end_x]])

        decays, times = self.fl_ds.transientGroup.get_decays()
        self.parent.addResPlot('Decays', decays, times, groups,
                size= 15, plottype = 'circles', color = 'green', append = True)

        maxfun = self.maxFunction()
        print '\ngetting amps'
        amps, times = maxfun()
        print 'using', amps, times
        self.parent.addResPlot('Amplitudes_MBL', amps,
                times, groups, size= 15, plottype = 'circles',
                color = 'blue', append = True)

        #maxfun = self.maxFunction2()
        #amps, times = maxfun()
        #self.parent.addResPlot('Amplitudes_RBL', amps,
        #        times,groups, size= 15, plottype = 'circles',
        #        color = 'blue', append = True)

        maxfun = self.maxFunction3()
        amps, times = maxfun()
        self.parent.addResPlot('Amplitudes_ABS', amps,
                times,groups, size= 15, plottype = 'circles',
                color = 'orange', append = True)

        #delays, times = self.ds.transientGroup.get_delays()
        #out = helpers.find_outliers(delays)[0]

        #print 'outliers',out
        #for k in out.keys():
        #    print k,delays[k]
        #    q = delays.index(out[k])
        #    delays.remove(out[k])
        #    times.pop(q)

        #self.parent.addResPlot('Delays', delays, times,groups, size= 15, plottype = 'circles', color = 'red', append = True)


        #halftimes, times = self.ds.transientGroup.get_halftimes()
        #self.parent.addResPlot('Halftimes', halftimes, times, size= 15, plottype = 'circles', color = 'orange', append = True)

        relbls, times = self.fl_ds.transientGroup.get_relaxation_baselines()
        self.parent.addResPlot('Relaxation', relbls,
                times,groups, size= 15, plottype = 'circles',
                color = 'orange', append = True)

        residuals, times = self.fl_ds.transientGroup.get_decay_residuals()
        self.parent.addResPlot('Residuals', residuals,
                times,groups, size= 15, plottype = 'circles',
                color = 'brown', append = True)

        starts, times = self.fl_ds.transientGroup.get_baselines()
        self.parent.addResPlot('Baselines', starts, times,groups,
                size= 15, plottype = 'circles', color = 'brown', append = True)

#        self.parent.addResPlot('Fluorescence', self.ds.fl.data, self.ds.phys_x_new, color = 'pink')

        self.additionalAnalysis()
        transient_data_view = CopyTableView()
        transient_data_view.setModel(self.transient_datamodel)
#        transient_data_view.hideColumn(2)
#        transient_data_view.hideColumn(3)
#        transient_data_view.hideColumn(4)
        self.parent.addTab(transient_data_view, 'Transient data')
        #self.parent.setCurrentIndex(1)


    def try_state_change(self, button, state):
#        try:
        if 1:
            state_m= self.state_matrix[button]
            #print 'ns',new_state,state,repr(new_state),repr(state)
#            print 'nns',new_state[zip(state)][0]
            new_state = state_m[zip(state)][0]
            #.get(tuple(state))
            print 'button',button,state,new_state
            button.setEnabled(new_state)
            if isinstance(button, QW.QPushButton):
                print button.text()
                if new_state == False and button.isChecked():
                    button.setChecked(new_state)
                    print 'disable check'
            return 1
        #except KeyError:
        #    for p in state.parents:
        #        if p:
        #            if self.try_state_change(button, p):
        #                break

    def toggle_buttons(self):
        print '\n\ntoggle'
        self.toggling_buttons = True
        for button in self.state_matrix:
            print '\nchanging',button.objectName(), self.state
            self.try_state_change(button, self.state)
        self.toggling_buttons = False
        print 'toggle done'


    #def removeMaxs(self):
    #    if hasattr(self, 'maxplot_d'):
    #        self.fplot.removePlot('Maxima')
    #        self.maxplot_d = None

    def find_transients(self):
        print 'find transient'
        try:
            self.temp_transients.hideAll()
        except:
            pass
        #self.pb_show_transients.setEnabled(True)
        #self.pb_show_transients.setChecked(False)
        #assume that only 1 type of selections in roi_manager
        selections = self.roi_manager.selections
        #assume all selections are of the same type
        try:
            selection_type_name = selections[0].selection_type.selection_type_name
        except IndexError:
            selection_type_name = None
        print 'stn',selection_type_name
        ch_data = self.fl_ds
        if selection_type_name == TBSTN.MANUAL:
            edges = []
            for selection in selections:
                x1 = selection.graphic_item.rect().left()
                x2 = selection.graphic_item.rect().right()
                start_x = self.fplot.scene2data((min(x1, x2), 0)).x()
                end_x = self.fplot.scene2data((max(x1, x2), 0)).x()
                edges.append((start_x, end_x))
            self.new_transients = ch_data.make_transients(edges, True)
        elif selection_type_name== TBSTN.AUTO:
            #if self.new_transients:
            #    self.rejectTransients()
            selection = selections[0]
            smooth_val = self.slider_detection.value()
            print 'find with', smooth_val
            #roi=self.roi_manager.getROIs()[Constants.AUTOMATIC][0]
            x1 = selection.graphic_item.rect().left()
            x2 = selection.graphic_item.rect().right()
            start_x = self.fplot.scene2data((min(x1, x2), 0)).x()
            end_x = self.fplot.scene2data((max(x1, x2), 0)).x()
            print 'roi dim',start_x,end_x
            self.new_transients = ch_data.find_transients(start_x, end_x, smooth_val)
        else:
            print 'should not be possible'

        #self.pb_analyze.setEnabled(True)
        #self.roi_manager.remove_selections()
        if selection_type_name == TBSTN.MANUAL:
            self.roi_manager.remove_selections()
            self.roi_manager.disable_builder()
        elif selection_type_name== TBSTN.AUTO:
            self.roi_manager.hide_selections()
        #self.roi_manager.disable_builder()
        self.showNewTransients(True)


    #def updateCoords(self, x,y):
    #    point = self.fplot.scene2data((x, - y))
    #    print emit
    #    self.emit(QC.SIGNAL('updateLocation(float, float, float, float)'), point.x(), point.y(), x, - y)

    def updateCoords(self, xv, yv, xs, ys):
        #self.status.showMessage('x: %.3f, y: %.3f, sx: %i, sy: %i'%(xv, yv, xs, ys))
        self.positionTXT.emit('x: %.3f, y: %.2f, sx: %i, sy: %i'%(xv, yv, xs, ys)


class FluorescenceTab(TransientTab):
    def maxFunction(self):
        return self.fl_ds.transientGroup.get_amps_minus_bl
#        return self.ds.transientGroup.get_amps_minus_relbl
    def maxFunction2(self):
#        return self.ds.transientGroup.get_amps_minus_bl
        return self.fl_ds.transientGroup.get_amps_minus_relbl
    def maxFunction3(self):
#        return self.fl_ds.transientGroup.get_amps_minus_bl
        return self.fl_ds.transientGroup.get_amps
    def additionalAnalysis(self):
        pass
    def additionalUISetup(self):
        pass
        #self.fPB5 = QG.QPushButton('Show events')
        #if len(self.ds.events) > 0:
        #    self.fPB5.setEnabled(True)
        #else:
        #    self.fPB5.setEnabled(False)
        #self.fPB5.setCheckable(True)
        #self.plotLayout.addWidget(self.fPB5)
        #self.connect(self.fPB5, QC.SIGNAL('toggled(bool)'), self.toggleEvents)

#class SparkFlTab(TransientTab):
#    def maxFunction(self):
##        return self.ds.transientGroup.get_amps_minus_bl
#        return self.ds.transientGroup.get_amps
#
#    def additionalUISetup(self):
#        detection_widget_layout = QG.QHBoxLayout()
#        initval = 200
#        qls4 = QG.QLabel('Min delay:')
#        self.qls5 = QG.QLabel(str(initval))
#        self.qls5.setToolTip('Minimum delay between sparks to\ninclude themin A1 / A2 calculations')
#        detection_widget_layout.addWidget(qls4)
#        detection_widget_layout.addWidget(self.qls5)
#        self.detectionLayout.addLayout(detection_widget_layout)
#        self.qms = QG.QSlider(QtCore.Qt.Horizontal)
#        self.qms.setSizePolicy(QG.QSizePolicy.Minimum, QG.QSizePolicy.Minimum)
#        self.qms.setRange(50, 300)
#        self.qms.setSingleStep(25)
#        self.qms.setValue(initval)
#        self.detectionLayout.addWidget(self.qms)
#
#        self.connect(self.qms, QC.SIGNAL('valueChanged(int)'), self.qls5, QC.SLOT('setNum(int)'))
#
#
#        self.CB5 = QG.QCheckBox('A1 / A2')
#        self.CB5.setChecked(True)
#        self.ABLayout.addWidget(self.CB5)
#
#    def additionalAnalysis(self):
#        if self.CB5.isChecked():
#            ratios = self.ds.transientGroup.get_A2A1(self.qms.value() * 1e-3)
#            self.ds.a1a2info = ''
#            sparklabels={}
#            blLines = {}
#            self.sparkTexts=[]
#            for ratio in ratios:
#                sparkindex0 = ratio[0][0]
#                sparkindex1 = ratio[0][1]
#                self.ds.a1a2info += 'Sparks %i and %i'%(sparkindex0, sparkindex1) + ', Ratio: %f'%ratio[1] + ' , Delay: %f'%ratio[2] + "\n"
#                if not sparkindex0 in sparklabels.keys():
#                    sparklabels[sparkindex0] = (self.ds.transientGroup.times[sparkindex0],self.ds.transientGroup.amps[sparkindex0])
#                    tr = self.ds.transientGroup.get_transient(sparkindex0)
#                    blLines[sparkindex0] = (tr.bl_end_phys,tr.start_phys,tr.bl)
#                if not sparkindex1 in sparklabels.keys():
#                    sparklabels[sparkindex1] = (self.ds.transientGroup.times[sparkindex1],self.ds.transientGroup.amps[sparkindex1])
#                    tr = self.ds.transientGroup.get_transient(sparkindex1)
#                    blLines[sparkindex1] = (tr.bl_end_phys,tr.start_phys,tr.bl)
#            for label in sparklabels.keys():
#                loc = sparklabels[label][0] - 0.03
#                height = sparklabels[label][1] + 0.1
#                g=self.fplot.addText(loc,height,label)
#                self.sparkTexts.append(g)
#                bl = blLines[label]
#                self.fplot.addVLine(bl[1],bl[0],bl[2])
#            self.mb = QG.QMessageBox(QG.QMessageBox.Information, 'Pairs', self.ds.a1a2info)
#            self.mb.show()
#            self.connect(self.mb, QC.SIGNAL('finished(int)'), self.clearSparkLabels)
#    def clearSparkLabels(self):
#        for l in self.sparkTexts:
#            self.fplot.removeItem(l)
#            del(l)
#        self.sparkTexts=[]
#        self.fplot.updatePlots()
#        self.fplot.makeAxes(7,7)
