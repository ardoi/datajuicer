import time

import PyQt4.QtGui as QG
import PyQt4.QtCore as QC

import numpy as n

from lsjuicer.inout.db.sqlbase import dbmaster
from lsjuicer.resources import cm


class FramePlayer(QG.QWidget):
    def __init__(self, frame_get_func, frame_set_func, frame_max_func, parent = None):
        super(FramePlayer, self).__init__(parent)
        self.frame_get_func = frame_get_func
        self.frame_set_func = frame_set_func
        self.frame_max_func = frame_max_func
        layout = QG.QHBoxLayout()
        self.setLayout(layout)
        play_pb = QG.QPushButton("Play")
        play_pb.setCheckable(True)
        self.play_pb = play_pb
        stop_pb = QG.QPushButton("Stop")
        stop_pb.setEnabled(False)
        self.stop_pb = stop_pb
        layout.addWidget(play_pb)
        layout.addWidget(stop_pb)
        play_pb.clicked.connect(self.play_frames)
        stop_pb.clicked.connect(self.stop_play)

        hlayout = QG.QHBoxLayout()
        hlayout.addWidget(QG.QLabel("FPS"))
        fps_selector = QG.QComboBox(self)
        fps_selector.setInputMethodHints(QC.Qt.ImhDigitsOnly)
        fps_selector.setEditable(True)
        self.fps_selector=fps_selector
        fpss = [5, 10, 25, 50, 100, 150]
        for fps in fpss:
            fps_selector.addItem(str(fps))
        fps_selector.setCurrentIndex(2)
        fps_selector.currentIndexChanged.connect(self.change_fps)
        hlayout.addWidget(fps_selector)
        layout.addLayout(hlayout)

        self.last_frame_time = None
        self.skipped_frames = 0


    @property
    def fps(self):
        return int(self.fps_selector.currentText())

    @property
    def playing(self):
        return not self.play_pb.isEnabled()

    def play_frames(self):
        if self.frame_get_func() == self.frame_max_func():
            self.frame_set_func(0)
        self.last_frame_time = None
        self.timer = QC.QTimer(self)
        self.timer.timeout.connect(self.increase_frame)
        self.timer.start(1./self.fps*1000) #in msec
        self.stop_pb.setEnabled(True)
        self.play_pb.setEnabled(False)

    def change_fps(self, new_fps):
        if self.playing:
            self.stop_pb.click()
            self.play_pb.click()
        else:
            return

    def increase_frame(self):
        max_real_fps = 25.0
        min_frame_dt = 1./max_real_fps
        if self.frame_get_func() == self.frame_max_func():
            self.stop_play()
            self.play_pb.setChecked(False)
        if self.last_frame_time is None or \
                time.time() - self.last_frame_time > 1./max_real_fps:
            if self.last_frame_time is None:
                skipped = 1
            else:
                skipped = max(1,round((time.time()-self.last_frame_time)*self.fps))
            self.frame_set_func(self.frame_get_func() + int(skipped))
            self.last_frame_time = time.time()
        else:
            self.skipped_frames += 1

    def stop_play(self):
        self.timer.stop()
        self.stop_pb.setEnabled(False)
        self.play_pb.setEnabled(True)
        self.play_pb.setChecked(False)

class Tasker(QG.QWidget):
    def __init__(self, parent = None):
        super(Tasker, self).__init__(parent)
        self.setLayout( QG.QHBoxLayout())
        self.filesButton = QG.QPushButton('Files')
        self.filesButton.setCheckable(True)
        self.filesButton.setChecked(True)
        self.analysisButton = QG.QPushButton('Analysis')
        self.analysisButton.setCheckable(True)
        self.analysisButton.setEnabled(False)
        self.confButton = QG.QPushButton('Configuration')
        self.confButton.setCheckable(True)
        bg = QG.QButtonGroup(self)
        bg.addButton(self.filesButton)
        bg.addButton(self.analysisButton)
        bg.addButton(self.confButton)

        self.layout().addWidget(self.filesButton)
        self.layout().addWidget(self.analysisButton)
        self.layout().addWidget(self.confButton)

class SparkResultWidget(QG.QFrame):
    def __init__(self, parent = None):
        super(SparkResultWidget, self).__init__(parent)
        self.setFrameShape(QG.QFrame.StyledPanel)
        stats_layout = QG.QGridLayout()
        stats_layout.addWidget(QG.QLabel('<b>Amplitude:</b>'),1,0,QC.Qt.AlignRight)
        #stats_layout.addWidget(QG.QLabel('<b>dF/F0:</b>'),1,0,QC.Qt.AlignRight)
        stats_layout.addWidget(QG.QLabel('<b>FWHM:</b>'),3,0,QC.Qt.AlignRight)
        stats_layout.addWidget(QG.QLabel('<b>FDHM:</b>'),4,0,QC.Qt.AlignRight)
        stats_layout.addWidget(QG.QLabel('<b>Decay rate:</b>'),5,0,QC.Qt.AlignRight)
        stats_layout.addWidget(QG.QLabel('<b>Rise time:</b>'),6,0,QC.Qt.AlignRight)
        stats_layout.addWidget(QG.QLabel('<b>Time @ max:</b>'),7,0,QC.Qt.AlignRight)
        stats_layout.addWidget(QG.QLabel('<b>Location @ max:</b>'),8,0,QC.Qt.AlignRight)
        stats_layout.addWidget(QG.QLabel('<b>Baseline:</b>'),9,0,QC.Qt.AlignRight)
        stats_layout.setSpacing(0)
        self.setLayout(stats_layout)
        self.amp_label = QG.QLabel('0')
        self.risetime_label = QG.QLabel('0')
        self.FWHM_label = QG.QLabel('0')
        self.FDHM_label = QG.QLabel('0')
        self.decay_label = QG.QLabel('0')
        self.time_at_max_label = QG.QLabel('0')
        self.location_at_max_label = QG.QLabel('0')
        self.baseline_label = QG.QLabel('0')
        self.spark_name_label = QG.QLabel('')
        self.spark_name_label.setStyleSheet("""
        QLabel{
        background-color:black;
        color:white;
        font-weight:bold;
        }
        """)
        self.spark_name_label.setAlignment(QC.Qt.AlignCenter)
        stats_layout.addWidget(self.spark_name_label,0,0,1,2)
        stats_layout.addWidget(self.amp_label, 1,1)
        #stats_layout.addWidget(self.dFF0_label, 1,1)
        stats_layout.addWidget(self.FWHM_label, 3,1)
        stats_layout.addWidget(self.FDHM_label, 4,1)
        stats_layout.addWidget(self.decay_label, 5,1)
        stats_layout.addWidget(self.risetime_label, 6,1)
        stats_layout.addWidget(self.time_at_max_label, 7,1)
        stats_layout.addWidget(self.location_at_max_label, 8,1)
        stats_layout.addWidget(self.baseline_label, 9,1)
        self.setStyleSheet("""SparkResultWidget { background-color: white; }""")
        self.setVisible(False)

class VisualizationOptionsWidget(QG.QWidget):

    settings_changed = QC.pyqtSignal(dict)
    close = QC.pyqtSignal()
    def __init__(self, pipechain, parent = None, channel=0):
        super(VisualizationOptionsWidget, self).__init__(parent)
        #data from shelf
        vis_key = 'visualization_options_reference'

        vis_conf = dbmaster.get_config_setting_value(vis_key)
        main_layout = QG.QVBoxLayout()
        layout = QG.QFormLayout()
        self.setLayout(main_layout)
        self.channel = channel
        main_layout.addLayout(layout)
        self.blur_spinbox = QG.QDoubleSpinBox(self)
        self.blur_spinbox.setMaximum(5)
        self.blur_spinbox.setSingleStep(.05)
        self.blur_spinbox.setMinimum(0)
        self.blur_spinbox.setValue(vis_conf['blur'])
        self.blur_spinbox.valueChanged.connect(
                self.visualization_controls_moved)
        self.blur_spinbox.setKeyboardTracking(False)
        layout.addRow(QG.QLabel('<html>Blur kernel &sigma; [&mu;m]</html>:'),self.blur_spinbox)

        self.saturation_spinbox = QG.QDoubleSpinBox(self)
        self.saturation_spinbox.setMaximum(99)
        self.saturation_spinbox.setSingleStep(.1)
        self.saturation_spinbox.setMinimum(0)
        self.saturation_spinbox.setValue(vis_conf['saturation'])
        self.saturation_spinbox.valueChanged.connect(
                self.visualization_controls_moved)
        self.saturation_spinbox.setKeyboardTracking(False)
        layout.addRow('Saturation:',self.saturation_spinbox)

        self.colormap_combobox = QG.QComboBox(self)

        self.colormaps = [name for name in cm.datad if not name.endswith("_r")]
        self.colormaps.sort()
        self.colormap_combobox.setIconSize(QC.QSize(100,20))
        for cm_name in self.colormaps:
            icon = QG.QIcon(QG.QPixmap(":/colormap_%s.png"%cm_name))
            self.colormap_combobox.addItem(icon, cm_name)
        self.colormap_combobox.setCurrentIndex(\
                self.colormaps.index(vis_conf['colormap']))
        self.colormap_combobox.currentIndexChanged.connect(
                self.visualization_controls_moved)
        layout.addRow('Colormap:',self.colormap_combobox)

        self.colormap_reverse_checkbox = QG.QCheckBox(self)
        self.colormap_reverse_checkbox.setChecked(vis_conf['colormap_reverse'])
        self.colormap_reverse_checkbox.stateChanged.connect(
                self.visualization_controls_moved)
        layout.addRow('Reverse colormap', self.colormap_reverse_checkbox)

        self.hist_plot = HistogramPlot( self)
        self.hist_plot.saturation_changed.connect(self.saturation_spinbox.setValue)
        main_layout.addWidget(self.hist_plot)
        close_pb =QG.QPushButton("Close")
        #close_pb.setSizePolicy(QG.QSizePolicy.Maximum, QG.QSizePolicy.Maximum)
        main_layout.addWidget(close_pb, QC.Qt.AlignRight)
        close_pb.clicked.connect(self.close)
        #self.pipechain = pipechain
        self.update_pipechain(pipechain)
       # self.do_histogram()

    def update_pipechain(self, pipechain):
        self.pipechain = pipechain
        pipechain.new_histogram.connect(self.update_hdata)
        self.update_hdata()

    def update_hdata(self):
        self.hist_plot.update_hdata(self.pipechain)
        self.do_histogram()

    #@helpers.timeIt
    def do_histogram(self):
        self.hist_plot.set_histogram(self.saturation_spinbox.value())

    def visualization_controls_moved(self):
        saturate = self.saturation_spinbox.value()
        cmap_name = str(self.colormap_combobox.currentText())
        cmap_r= self.colormap_reverse_checkbox.isChecked()
        blur = self.blur_spinbox.value()
        settings = {'saturation':saturate, 'colormap':cmap_name,
                'colormap_reverse':cmap_r, 'blur':blur}
        self.settings_changed.emit(settings)
        self.do_histogram()

class HistogramPlot(QG.QWidget):
    saturation_changed = QC.pyqtSignal(float)
    @property
    def log_scale(self):
        return self.log_checkbox.isChecked()

    def __init__(self,  parent = None):
        super(HistogramPlot, self).__init__(parent)
        layout = QG.QVBoxLayout()
        self.channel = parent.channel
        self.setLayout(layout)
        self.scene = HistogramScene(self)
        self.scene.clicked.connect(self.reverse_saturation)
        self.scene.setBackgroundBrush(QG.QBrush(QG.QColor('#1D3A3B')))
        #gr = self.scene.addRect(QC.QRectF(0,0,200,100))
        self.view = RefitView(self)
        self.view.setScene(self.scene)
        self.log_checkbox = QG.QCheckBox("Log scale histogram")
        #self.log_checkbox.stateChanged.connect(self.set_histogram)
        self.log_checkbox.stateChanged.connect(self.checkbox_changed)
        #self.setFixedSize(200, 150)
        self.gpath = None
        self.gpath_fill = None
        self.saturation_gline = None
        self.saturation_value = 0
        self.pipechain=None
        self._points = {'Normal':None, 'Log':None}
        layout.addWidget(self.view)
        layout.addWidget(self.log_checkbox)
        #self.g_pixmap = None
        #self.g_roiline = None
        #gt = self.scene.addText("No file selected")
        #self.view.centerOn(gr)
        self.view.setFrameStyle(QG.QFrame.NoFrame)
        self.view.setRenderHint(QG.QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        self.saturation_pen = QG.QPen(QG.QColor('orange'))
        #self.saturation_pen.setWidth(3)
        self.saturation_pen.setCosmetic(True)

        self.hist_line_pen = QG.QPen(QG.QColor('white'))
        #self.hist_line_pen.setWidth(2)
        self.hist_line_pen.setCosmetic(True)

    def update_hdata(self, pipechain):
        self.hdata = pipechain.histogram(self.channel)
        #reset precalculated histogram points
        self._points = {'Normal':None, 'Log':None}
        self.pipechain = pipechain

    def checkbox_changed(self, state):
        self.set_histogram()

    def scale_y(self, val, logmin=0):
        if self.log_scale:
            return 1./n.log(val+1e-12) - logmin
        else:
            return -val

    def sizeHint(self):
        return QC.QSize(200,150)

    @property
    def points(self):
        if self.log_scale:
            if not self._points["Log"]:
                self._points["Log"] = self.make_points(self.hdata)
            return self._points["Log"]
        else:
            if not self._points["Normal"]:
                self._points["Normal"] = self.make_points(self.hdata)
            return self._points["Normal"]

    #@helpers.timeIt
    def reverse_saturation(self, loc):
        #method to determine saturation value based on user click on scene
        saturation_value = self.pipechain.value_percentage(loc, self.channel)
        #self.set_histogram(100-saturation_value)
        self.saturation_changed.emit(100 - saturation_value)
        #print 'emitted', 100 - saturation_value, saturation_value

    #@helpers.timeIt
    def set_histogram(self, saturation_value=None ):
        #print '\nsat val',self.saturation_value,saturation_value
        if saturation_value:
            self.saturation_value = saturation_value
        #print 'new sat val',self.saturation_value
        if self.hdata is not None:
            cut_max = self.pipechain.percentage_value(self.saturation_value,
                    self.channel)
            points = self.points
            start = points[0]
            path = QG.QPainterPath(start)
            for p in points[1:]:
                path.lineTo(p)
            if self.gpath:
                self.scene.removeItem(self.gpath)
            self.gpath = self.scene.addPath(path,self.hist_line_pen)
            self.gpath.setZValue(2)
            #draw line of saturation percentage
            if self.saturation_gline:
                self.scene.removeItem(self.saturation_gline)
            self.saturation_gline = self.scene.addLine(cut_max, 0,
                    cut_max, self.scale_y(max(self.hdata[0][1:])),
                    self.saturation_pen)
            #make fill path till cut_max
            path_fill = QG.QPainterPath(start)
            for p in points[1:]:
                if p.x()<=cut_max:
                    path_fill.lineTo(p)
                else:
                    sl = self.saturation_gline.shape()
                    #hl = self.gpath.shape()
                    inters = path.intersected(sl)
                    if inters.elementCount() > 1:
                        el=inters.elementAt(0)
                        #print el.x, el.y
                        y_last = el.y
                        #print 'intersect'
                    else:
                        y_last = p.y()
                        #print 'no intersect'
                    #print 'yl=',y_last
                    path_fill.lineTo(cut_max, y_last)
                    path_fill.lineTo(cut_max, start.y())
                    break
            path_fill.closeSubpath()
            if self.gpath_fill:
                self.scene.removeItem(self.gpath_fill)
            self.gpath_fill = self.scene.addPath(path_fill,
                    brush=QG.QBrush(QG.QColor('cornflowerblue')))
            self.gpath_fill.setZValue(1)
            self.saturation_gline.setZValue(3)
            self.fit_view()

    def fit_view(self):
        if self.gpath:
            self.view.fitInView(self.gpath)

    #@helpers.timeIt
    def make_points(self, data):
        points = []
        #skip the first point of the histogram because it will be all black values and will make the histogram unreadable unless in log scale.
        points.append(QC.QPointF(data[1][1], 0))
        logmin = max(1/n.log(data[0][1:]+1e-12))
        for x,y in zip(data[1][1:],data[0][1:]):
            point = QC.QPointF(x, self.scale_y(y,logmin = logmin))
            points.append(point)
        points.append(QC.QPointF(data[1][-2], 0))
        return points

class HistogramScene(QG.QGraphicsScene):
    clicked = QC.pyqtSignal(float)
    def mousePressEvent(self, event):
        pos = event.scenePos()
        self.clicked.emit(pos.x())

class RefitView(QG.QGraphicsView):
    """GraphicsView extension that fits in view at every resize event"""
    def resizeEvent(self, event):
        QG.QGraphicsView.resizeEvent(self,event)
        self.fitInView(self.scene().itemsBoundingRect())
