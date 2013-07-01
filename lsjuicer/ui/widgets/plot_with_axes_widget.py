import PyQt4.QtCore as QC
import PyQt4.QtGui as QG
from scipy.interpolate import interp1d
import numpy as n

from lsjuicer.ui.scenes import PlotDisplay
from lsjuicer.ui.views import ZoomView
from lsjuicer.ui.widgets.axiswidget import VerticalAxisWidget, HorizontalAxisWidget
from lsjuicer.ui.plot.plotteddata import PlottedData
from lsjuicer.static.constants import Constants


class SparkScene(QG.QGraphicsScene):
    mouseclicked = QC.pyqtSignal(int, int)

    def mouseReleaseEvent(self, event):
        pos = event.scenePos()
        self.mouseclicked.emit(pos.x(), pos.y())


class PlotWidget(QG.QWidget):
    hlinemoved = QC.pyqtSignal(int)
    vlinemoved = QC.pyqtSignal(int)

    def __init__(self,  parent=None):
        super(PlotWidget, self).__init__(parent)
        self.F0_left = None
        self.F0_right = None
        self.F0_box = None
        self.pixmap_item = None
        self.pixmap = None
        self.v_box = None
        self.h_box = None
        self.vline = None
        self.hline = None
        self.ggroup = None
        self.accept_mouse_clicks = True
        self.view_fit_mode = 0
        layout = QG.QVBoxLayout()
        self.setLayout(layout)
        self.fV = QG.QGraphicsView(self)
        self.fV.setRenderHint(QG.QPainter.Antialiasing)
        self.fV.setVerticalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        # self.fV.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        self.fV.setFrameStyle(QG.QFrame.NoFrame)
        self.fV.setViewportUpdateMode(0)
        layout.addWidget(self.fV)
        self.fscene = SparkScene(self)
        self.fV.setScene(self.fscene)
        # self.setSizePolicy(QG.QSizePolicy.Minimum, QG.QSizePolicy.Minimum)
#        self.fV.show()
        print 'size init', self.size(), self.fV.isVisible(), self.fV.sizeHint()

    def accept_input(self, state):
        self.accept_mouse_clicks = state

    def add_pixmap(self, pixmap, h_span, v_span):
        self.pixmap = pixmap
        if self.pixmap_item:
            self.fscene.removeItem(self.pixmap_item)
            self.fscene.removeItem(self.v_box)
            self.fscene.removeItem(self.h_box)
            self.fscene.removeItem(self.vline)
            self.fscene.removeItem(self.hline)
            self.fscene.removeItem(self.ggroup)

        self.pixmap_item = self.fscene.addPixmap(pixmap)
        self.ggroup = self.fscene.addRect(0, 0, pixmap.width(),
                                          pixmap.height(), QG.QPen(QG.QColor('red')))
        self.fscene.setSceneRect(self.ggroup.boundingRect())
#        v_pen = QG.QPen(QG.QColor('magenta'))
        v_pen = QG.QPen(QG.QColor('magenta'))
        v_pen.setCosmetic(True)
        v_pen.setWidth(1)
#        h_pen = QG.QPen(QG.QColor('cyan'))
        h_pen = QG.QPen(QG.QColor('cyan'))
        h_pen.setCosmetic(True)
        h_pen.setCosmetic(1)

        self.h_loc = int(pixmap.width()/2.)
        self.v_loc = int(pixmap.height()/2.)
        self.h_span = h_span
        self.v_span = v_span

        v_brush_color_a = QG.QColor('magenta')
        v_brush_color_a.setAlphaF(0.15)
        v_brush_a = QG.QBrush(v_brush_color_a)
        top_left = QC.QPointF(self.h_loc - self.h_span, self.pixmap.height())
        bottom_right = QC.QPointF(self.h_loc + self.h_span+1, 0)
        rect = QC.QRectF(top_left, bottom_right)
        self.v_box = self.fscene.addRect(rect, v_pen, v_brush_a)

        v_brush_color = QG.QColor('magenta')
        v_brush_color.setAlphaF(0.5)
        v_brush = QG.QBrush(v_brush_color)
        top_left = QC.QPointF(self.h_loc, self.pixmap.height())
        bottom_right = QC.QPointF(self.h_loc + 1, 0)
        rect = QC.QRectF(top_left, bottom_right)
        # self.vline = self.fscene.addRect(rect, v_pen,
        # QG.QBrush(QC.Qt.NoBrush))
        self.vline = self.fscene.addRect(rect, QG.QPen(QC.Qt.NoPen), v_brush)

        # self.hline = self.fscene.addLine(0,self.v_loc,
        #        pixmap.width(),self.v_loc,h_pen)

        h_brush_color_a = QG.QColor('cyan')
        h_brush_color_a.setAlphaF(0.15)
        h_brush_a = QG.QBrush(h_brush_color_a)
        top_left = QC.QPointF(0.0, self.v_loc-self.v_span)
        bottom_right = QC.QPointF(
            self.pixmap.width(), self.v_loc + 1+self.v_span)
        rect = QC.QRectF(top_left, bottom_right)
        self.h_box = self.fscene.addRect(rect, h_pen, h_brush_a)

        h_brush_color = QG.QColor('cyan')
        h_brush_color.setAlphaF(0.5)
        h_brush = QG.QBrush(h_brush_color)
        top_left = QC.QPointF(0.0, self.v_loc)
        bottom_right = QC.QPointF(self.pixmap.width(), self.v_loc + 1)
        rect = QC.QRectF(top_left, bottom_right)
        self.hline = self.fscene.addRect(rect, QG.QPen(QC.Qt.NoPen), h_brush)
        # self.hline = self.fscene.addRect(rect,
        # h_pen,QG.QBrush(QC.Qt.NoBrush))

#        self.fV.fitInView(ggroup, QC.Qt.IgnoreAspectRatio)
        self.fitView(0)
        self.fscene.mouseclicked.connect(self.click_on_scene)
        print 'size pix', self.size()
        # self.internal_location_change = False

    def click_on_scene(self, hor, ver):
        if self.accept_mouse_clicks:
            self.move_vline(hor)
            self.move_hline(self.pixmap.height()-ver)
            self.vlinemoved.emit(hor)
            self.hlinemoved.emit(self.pixmap.height()-ver)

    def F0_changed(self, left, right):
        white = QG.QColor('white')
        white.setAlphaF(0.15)
        white_brush = QG.QBrush(white)
        if left is not None:
            self.F0_left = left
        if right is not None:
            self.F0_right = right
        if self.F0_left is not None and self.F0_right is not None:
            top_left = QC.QPointF(self.F0_left, 0)
            bottom_right = QC.QPointF(self.F0_right, self.pixmap.height())
            rect = QC.QRectF(top_left, bottom_right)
            if self.F0_box:
                self.F0_box.setRect(rect)
            else:
                self.F0_box = self.fscene.addRect(rect,
                                                  QG.QPen(QG.QColor('white')), white_brush)

    def move_hbox(self, span):
        # print 'move h',span
        self.v_span = span
        top_left = QC.QPointF(0.0, self.pixmap.height()-self.v_loc-span)
        bottom_right = QC.QPointF(self.pixmap.width(),
                                  self.pixmap.height()-self.v_loc + 1.0+span)
        # print top_left,bottom_right
        rect = QC.QRectF(top_left, bottom_right)
        self.h_box.setRect(rect)

    def move_vbox(self, span):
        # print 'move v',span
        self.h_span = span
        top_left = QC.QPointF(self.h_loc-span, self.pixmap.height())
        bottom_right = QC.QPointF(self.h_loc + 1.0+span, 0)
        rect = QC.QRectF(top_left, bottom_right)
        self.v_box.setRect(rect)

    def move_vline(self, loc):
        if self.pixmap:
            self.h_loc = loc
            top_left = QC.QPointF(self.h_loc, self.pixmap.height())
            bottom_right = QC.QPointF(self.h_loc + 1.0, 0)
            rect = QC.QRectF(top_left, bottom_right)
            self.vline.setRect(rect)
            self.move_vbox(self.h_span)
            # self.fV.repaint()
            # self.fV.update()

    def move_hline(self, loc):
        if self.pixmap:
            self.v_loc = loc
            top_left = QC.QPointF(0.0, self.pixmap.height()-self.v_loc)
            bottom_right = QC.QPointF(self.pixmap.width(),
                                      self.pixmap.height() - self.v_loc + 1.0)
            rect = QC.QRectF(top_left, bottom_right)
            self.hline.setRect(rect)
            self.move_hbox(self.v_span)
            # self.fV.repaint()
            # self.fV.update()

    def fitView(self, value=None):
        r = self.fscene.sceneRect()
        # r=self.fscene.limitItem.boundingRect()
        # print value
        m = self.fV.transform()
        if not value:
            value = self.view_fit_mode
        if value == 0:
            # ignore aspect ratio
            arh = float(self.fV.width())/r.width()
            height = r.height()
            if height == 0:
                height = 1.0
            arw = float(self.fV.height())/height
        # elif value == 1:
        # fit in screen keeping aspect ratio
        #    arw = float(self.fV.width())/r.width()
        #    arh = arw

        elif value == 1:
            # expand but keep aspect ratio
            arh = float(self.fV.height())/r.height()
            arw = arh
        m.setMatrix(arh, 0.0, 0.0, 0.0, arw, 0.0, 0.0, 0.0, 1.0)
        # m2 = self.fV.transform()
        # m2.setMatrix(arh, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        # m3 = self.fV.transform()
        # m3.setMatrix(1, 0.0, 0.0, 0.0, arw, 0.0, 0.0, 0.0, 1.0)

        # self.arh = arh
        # self.arw = arw
        self.fV.setTransform(m)
        # self.haxView.setTransform(m2)
        # self.vaxView.setTransform(m3)
        # self.haw.paint(arh)
        # self.vaw.paint(arw)
        # if value==2:
        #    self.fV.horizontalScrollBar().setSliderPosition(0)
        # self.updatePlots()


class PlotWithAxesWidget(QG.QWidget):
    updateLocation = QC.pyqtSignal(float, float, float, float)

    def __init__(self,  parent=None, sceneClass=None, antialias=True):
        super(PlotWithAxesWidget, self).__init__(parent)
        # self.plot_sp = 250.
        self.plot_datas = {}
        self.antialias = antialias
        self.setupUI(sceneClass)
        self.plot_index = 0
        self.scene_rect = None
        self.scene2data_xvals = None
        self.scene2data_yvals = None
        self.ymax = None
        self.ymin = None
        self.xmax = None
        self.xmin = None
        self.zeroline = None
        self.gpix = None
        # fill view by default
        self.aspect_ratio = QC.Qt.IgnoreAspectRatio
        self.Hlines = {Constants.EVENTS: [], Constants.GAPS: []}

    def addHLines(self, locs, linetype, color='lime'):
        # check if there is anything to add first
        if locs:
            for loc in locs:
                # try:
                if 1:
                    self.Hlines[linetype].append(self.makeHLine(loc, color))
                # except:
                #    print 'failed to add event: ', loc
            # checkBox = None
            # if linetype == Constants.EVENTS:
            #    checkBox = self.showEventsCB
            # elif linetype == Constants.GAPS:
            #    checkBox = self.showGapsCB
            # else:
            #    pass
            # if checkBox:
            #    checkBox.setEnabled(True)
            #    checkBox.setChecked(True)

    def addPixmap(self, pixmap, xvals=None, yvals=None):
        if xvals is not None:
            self.checkAndSetXvals(xvals)
#        self.scene2data_xvals = xvals
        if yvals is not None:
            self.scene2data_yvals = yvals
        # assert len(self.scene2data_xvals) == pixmap.width() and \
        #        len(self.scene2data_yvals) == pixmap.height(), 'Wrong size for x an y phys values'
        # self.fscene.clear()
        brush = QG.QBrush(QG.QColor('black'))
        self.fscene.setBackgroundBrush(brush)
        self.gpix = self.fscene.addPixmap(pixmap)
        # splitPix = SplitPixmap(pixmap)
        # t0 = time.time()
        # splits = splitPix.getSplits()
        # ggroup = QG.QGraphicsItemGroup()
        # for sp in splits:
        #    gg = QG.QGraphicsPixmapItem(sp.pixmap, ggroup)
        #    gg.setCacheMode(QG.QGraphicsItem.ItemCoordinateCache,QC.QSize(sp.pixmap.width(),sp.pixmap.height()))
        #    gg.setOffset(sp.dx,sp.dy)
        #    ggroup.addToGroup(gg)
        # self.fscene.addItem(ggroup)
        # print 'pix w/h',pixmap.width(),pixmap.height()
        rect = QC.QRectF(0, 0, pixmap.width(), pixmap.height())
        # path = QG.QPainterPath(QC.QPointF(0,0))
        # path.addRect(rect)
        # self.border = self.fscene.addPath(path,QG.QPen(QG.QColor('black')))
        # self.scene_rect=ggroup.boundingRect()
        # self.scene_rect=self.gpix.boundingRect()
        if self.scene_rect == rect:
            return
        self.scene_rect = rect  # path.boundingRect()
        # fix QT 2 pix boundary
        # self.scene_rect.adjust(-2,-2,2,2)
        # self.scene_rect.adjust(0,0,-0,-0)
        # self.h_axis.set_range(rect.left(), rect.right())
        # print self.scene_rect
        # self.fscene.setSceneRect(ggroup.boundingRect())
        self.reframe()
        # self.fV.determine_axes_span()
        self.fitView()
        # self.emit(QC.SIGNAL('pixmapW(int)'),ggroup.boundingRect().width())

    def replacePixmap(self, pixmap):
        if self.gpix:
            # print 'removing',self.gpix
            self.fscene.removeItem(self.gpix)
            # self.fscene.removeItem(self.border)
        self.addPixmap(pixmap, None, None)

    def center_graphicsitem(self, item):
        self.fV.centerOn(item)

    def fitView(self, value=None):
        if value is not None:
            self.aspect_ratio = value
        self.fV.fitInView(self.scene_rect, self.aspect_ratio)  # value)
        # print 'fitview',self.scene_rect, self.fV.sceneRect()
        self.fV.determine_axes_span()
        # poly = self.fV.mapFromScene(self.scene_rect)
        # for i in range(poly.count()):
        #    point = poly.point(i)
        #    print point

        # r=self.fscene.sceneRect()
        # r=self.scene_rect
        # r=self.fscene.limitItem.boundingRect()
        # print 'scenerect', r
        # print self.fscene.items()
        # for item in self.fscene.items():
        # print item, item.boundingRect()
        # print self.fscene.itemsBoundingRect()
        # m=self.fV.transform()
        # if value == 0:
        # ignore aspect ratio
        #    arh = float(self.fV.width())/r.width()
        #    height = r.height()
        #    if height == 0:
        #        height = 1.0
        #    arw = float(self.fV.height())/height
        # elif value == 1:
        # fit in screen keeping aspect ratio
        # arw = float(self.fV.width())/r.width()
        # arh = arw
        #
        # elif value == 1:
        # expand but keep aspect ratio
        #    arh = float(self.fV.height())/r.height()
        #    arw = arh
        # m.setMatrix(arh, 0.0, 0.0, 0.0, arw, 0.0 ,0.0, 0.0, 1.0)
        # m2 = self.fV.transform()
        # m2.setMatrix(arh, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        # m3 = self.fV.transform()
        # m3.setMatrix(1, 0.0, 0.0, 0.0, arw, 0.0, 0.0, 0.0, 1.0)

        # self.arh = arh
        # self.arw = arw
        # self.fV.setTransform(m)
        # self.haxView.setTransform(m2)
        # self.vaxView.setTransform(m3)
        # self.haw.paint(arh)
        # self.vaw.paint(arw)
        # if value==2:
        #    self.fV.horizontalScrollBar().setSliderPosition(0)
        # self.updatePlots()

    def removeItem(self, item):
        if item.scene() == self.fscene:
            self.fscene.removeItem(item)
        else:
            print 'no point in removing item ', item
            pass
        return

    def toggle_plot(self, plot_name, state):
        if plot_name in self.plot_datas:
            path = self.plot_datas[plot_name].graphic_item
            self.plot_datas[plot_name].visibility = state
            path.setVisible(state)

    def setupUI(self, sceneClass):
        plotLayout = QG.QVBoxLayout()
        plotLayout.setContentsMargins(0, 0, 0, 0)
        plotLayout.setSpacing(0)
        self.setLayout(plotLayout)
        self.my_init()
        # GLW  = QGL.QGLWidget(self)
        self.fV = ZoomView()
        self.fV.setTransformationAnchor(QG.QGraphicsView.AnchorUnderMouse)
        # self.fV.setViewport(GLW)
        # self.fV.setViewportUpdateMode(2)
        self.fV.setFrameStyle(QG.QFrame.NoFrame)
        # TODO try disable:
        self.fV.setCacheMode(QG.QGraphicsView.CacheNone)
        self.fV.setMouseTracking(True)
        fLayout = QG.QGridLayout()
        plotLayout.addLayout(fLayout)
        self.setLayout(plotLayout)
        # horizontal scroll bar
        hscroll_widget = QG.QWidget()
        hscroll_widget.setLayout(QG.QVBoxLayout())
        hscroll_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.horizontal_scrollbar = self.fV.horizontalScrollBar()
        hscroll_widget.setMinimumSize(self.horizontal_scrollbar.size())
        self.horizontal_scrollbar.rangeChanged.connect(self.hor_scroll_range)
        self.horizontal_scrollbar.setVisible(False)
        hscroll_widget.layout().addWidget(self.horizontal_scrollbar)
        self.horizontal_scrollbar.valueChanged.connect(self.h_scroll_changed)

        # vertical scroll bar
        vscroll_widget = QG.QWidget()
        vscroll_widget.setLayout(QG.QVBoxLayout())
        vscroll_widget.layout().setContentsMargins(0, 0, 0, 0)
        self.vertical_scrollbar = self.fV.verticalScrollBar()
        self.vertical_scrollbar.rangeChanged.connect(self.ver_scroll_range)
        self.vertical_scrollbar.setVisible(False)
        vscroll_widget.layout().addWidget(self.vertical_scrollbar)
        self.vertical_scrollbar.valueChanged.connect(self.v_scroll_changed)

        # axis widgets
        self.h_axis = HorizontalAxisWidget(self)

        self.v_axis = VerticalAxisWidget(self)
        fLayout.setContentsMargins(0, 0, 0, 0)
        fLayout.setSpacing(0)

        fLayout.addWidget(self.v_axis, 0, 0)
        fLayout.addWidget(self.fV, 0, 1)
        fLayout.addWidget(vscroll_widget, 0, 2)

        fLayout.addWidget(self.h_axis, 1, 1)

        fLayout.addWidget(hscroll_widget, 2, 1)

        self.fV.hor_zoom_changed.connect(self.h_axis.zoom_changed)
        self.fV.hor_range_changed.connect(self.h_axis.set_range)
        self.fV.ver_zoom_changed.connect(self.v_axis.zoom_changed)
        self.fV.ver_range_changed.connect(self.v_axis.set_range)
        self.fV.zoom_level.connect(self.zoom_level_changed)
        self.fV.v_axis_param.connect(self.v_axis.param_changed)

        action_toolbutton = QG.QToolButton(self)
        action_toolbutton.setIcon(QG.QIcon(QG.QPixmap("://lightbulb.png")))
        action_toolbutton.setToolTip("Actions")
        action_toolbutton.setPopupMode
        menu = QG.QMenu()
        reset_zoom_action = menu.addAction(QG.QIcon(
            QG.QPixmap("://bomb.png")), "Reset zoom levels")
        fit_menu = menu.addMenu(QG.QIcon(QG.QPixmap(
            "://monitor_edit.png")), "Change fit")
        fit_in_view_action = fit_menu.addAction(
            QG.QIcon("://arrow_out.png"), "Fit in view")
        fit_width_action = fit_menu.addAction(
            QG.QIcon("://arrow_right.png"), "Fit width")
        fit_height_action = fit_menu.addAction(
            QG.QIcon("://arrow_up.png"), "Fit height")
        help_action = menu.addAction(QG.QIcon("://help.png"), "Help")
        action_toolbutton.setMenu(menu)

        reset_zoom_action.triggered.connect(self.fV.reset_zoom)
        reset_zoom_action.setEnabled(False)
        self.reset_zoom_action = reset_zoom_action

        fit_width_action.triggered.connect(
            lambda: self.fitView(QC.Qt.KeepAspectRatio))
        fit_height_action.triggered.connect(
            lambda: self.fitView(QC.Qt.KeepAspectRatioByExpanding))
        fit_in_view_action.triggered.connect(
            lambda: self.fitView(QC.Qt.IgnoreAspectRatio))
        action_text = """<h3>Zooming</h3>
        Using the mouse wheel it is possible to zoom in into the image
        <ul>
        <li>To zoom only in the
        vertical direction, hold <strong>Shift</strong> button while scrolling </li>
        <li>For horizontal direction only, hold <strong>Ctrl</strong> key (&#8984; on Mac)</li>
        <li>To reset the view click on the <strong>Reset zoom level</strong> button in
        this menu</li>
        </ul>
        <h3>Panning</h3>
        While zoomed in, you can drag and move the image
        <h3>Fitting the image in the window</h3>
        There are three options for the positioning the image in the view:
        <dl>
        <dt><strong>Fit in view</strong></dt>
        <dd>Stretches the image to fit all available space, ignoring the aspect ratio
        (i.e., pixels will not be squares)</dd>
        <dt><strong>Fit width<strong></dt>
        <dd>Stretches the image in the horizontal direction, keeping the aspect ratio</dd>
        <dt><strong>Fit height</strong></dt>
        <dd>Stretches the image in the vertical direction and expands the horizontal
        direction to maintain the aspect ratio<dd>
        </dl>
        """
        help_action.triggered.connect(lambda: QG.QMessageBox.information(
            self, "Plot window actions", action_text))

        style = """
            QToolButton
            {
                 border: none;
            }
                """
        action_toolbutton.setStyleSheet(style)
        action_toolbutton.setPopupMode(QG.QToolButton.InstantPopup)
        # change_fit_toolbutton.setStyleSheet(style)
        # reset_zoom_toolbutton = toolbar.widgetForAction(reset_zoom_action)
        # reset_zoom_toolbutton.setStyleSheet(style)
        # toolbar.setStyleSheet(style)
        action_toolbutton.setMaximumHeight(20)
        action_toolbutton.setMaximumWidth(40)
        #:wfit_toolbutton.setAutoRaise(True)
        # toolbar.setMaximumHeight(20)
        # toolbar.setMaximumWidth(40)
        # fLayout.addWidget(self.piclabel,1,0)
        fLayout.addWidget(action_toolbutton, 1, 0)

        zoomlevel_widget = QG.QWidget(self)
        zoom_labels_layout = QG.QHBoxLayout()
        zoomlevel_widget.setLayout(zoom_labels_layout)

        self.zoom_h_label = QG.QLabel('1.0')
        small_text_style = """
        QLabel{
        font-size:10px;
        }
        """
        self.zoom_h_label.setStyleSheet(small_text_style)
        self.zoom_v_label = QG.QLabel('1.0')
        self.zoom_v_label.setStyleSheet(small_text_style)
        zoom_middle_label = QG.QLabel(':')
        zoom_middle_label.setStyleSheet(small_text_style)
        zoom_labels_layout.addWidget(self.zoom_h_label)
        zoom_labels_layout.addWidget(zoom_middle_label)
        zoom_labels_layout.addWidget(self.zoom_v_label)
        zoom_labels_layout.setContentsMargins(0, 0, 0, 0)
        zoom_labels_layout.setSpacing(0)
        # zoomlevel_label = QG.QLabel('\
        #        <p style="font-size:small;text-align:justify">1:1</p>')
        # zoomlevel_widget.setSizePolicy(QG.QSizePolicy.Minimum,
        #        QG.QSizePolicy.Minimum)
        zoomlevel_widget.setMaximumWidth(40)
        zoomlevel_widget.setMaximumHeight(20)
        zoomlevel_widget.setToolTip('Zoom levels - horizontal : vertical')
        fLayout.addWidget(zoomlevel_widget, 2, 0, QC.Qt.AlignHCenter)

        # self.line_prop_pb=QG.QPushButton('Data properties')
        # self.piclabel.setIcon(QG.QIcon(QG.QPixmap("://bomb.png")))
        # self.line_prop_pb.setSizePolicy(QG.QSizePolicy.Minimum,QG.QSizePolicy.Minimum)
        # self.line_prop_pb.setFlat(True)
        # self.line_prop_pb.setEnabled(False)
        # self.line_prop_pb.setToolTip('Change properties of plotted data')
        # self.line_prop_pb.setMaximumWidth(40)
        # self.line_prop_pb.setMaximumHeight(20)
        # self.line_prop_pb.clicked.connect(self.show_line_props)

        self.fV.show()

        if sceneClass is None:
            self.fscene = PlotDisplay()
        else:
            self.fscene = sceneClass()

        self.fV.setScene(self.fscene)
        # self.haw.setPlotScene(self.fscene)
        # self.vaw.setPlotScene(self.fscene)
        # print 'antialias',self.antialias
        if self.antialias:
        #    print 'setting aa',self.antialias
            self.fV.setRenderHint(QG.QPainter.Antialiasing)
#        self.fV.setRenderHint(QG.QPainter.HighQualityAntialiasing)
        self.fV.setVerticalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        self.fV.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)

        # self.connect(self.fscene, QC.SIGNAL('setLocation(float, float)'),
        # self.updateCoords)
        self.fscene.setLocation.connect(self.updateCoords)

    def zoom_level_changed(self, h_zoom, v_zoom):
        self.reset_zoom_action.setEnabled(h_zoom > 1 or v_zoom > 1)
        self.zoom_h_label.setText('%.1f' % h_zoom)
        self.zoom_v_label.setText('%.1f' % v_zoom)

    def ranges_changed(self):
        # call this so that haxis is initialized to the right left/right values
        self.h_scroll_changed()
        self.v_scroll_changed()

    def h_scroll_changed(self, value=None):
        self.fV.alert_horizontal_range_change()

    def v_scroll_changed(self, value=None):
        self.fV.alert_vertical_range_change()

    def hor_scroll_range(self, minv, maxv):
        self.horizontal_scrollbar.setVisible(minv != maxv)

    def ver_scroll_range(self, minv, maxv):
        self.vertical_scrollbar.setVisible(minv != maxv)

    def showHLines(self, state, hlines):
        if state == QC.Qt.Checked:
            visible = True
        else:
            visible = False
        for line in hlines:
            line.setVisible(visible)

    def scene2data(self, spoint):
        # print 's2d in',spoint
        if isinstance(spoint, QC.QPointF):
            sx = spoint.x()
            sy = - spoint.y()
        else:
            sx = spoint[0]
            sy = spoint[1]
        try:
        # if 1:
            x_out = self.scene2data_xfunc(sx)
            if self.scene2data_yvals is None:
                y_out = -sy  # the value from scene is also data value
            else:
                # print len(self.scene2data_yvals),sy,int(sy)
                y_out = self.scene2data_yvals[int(sy)]

            # print 's2d out',(x_out,y_out)
            return QC.QPointF(x_out, y_out)
        except:
        #    print 'error getting corresponding values for',spoint
            return spoint

    def data2scene(self, dpoint):
        dx = dpoint[0]
        dy = dpoint[1]
#        return QC.QPointF((dx - self.data_x_min) / (self.data_x_max - self.data_x_min) * self.plot_w, - (dy - self.data_y_min) / (self.data_y_max - self.data_y_min) * self.plot_h)
        # print dpoint
        ret = QC.QPointF(self.data2scene_xfunc(dx), -dy)
        return ret

    def addText(self, loc, height, label):
        font = QG.QFont()
        font.setPointSize(14)
        font.setBold(True)
        location = self.data2scene((loc, height))
        gt = self.fscene.addText(str(label), font)
        gt.setPos(location)
        gt.setZValue(100)
        return gt

    def addVLine(self, start, end, height):
        pen = QG.QPen()
        pen.setWidth(6)
        pen.setColor(QG.QColor('navy'))
        start = self.data2scene((start, height))
        end = self.data2scene((end, height))
        gl = self.fscene.addLine(QC.QLineF(start, end), pen)
        gl.setZValue(500)
        return gl

    def removeHlines(self):
        for line in self.Hlines:
            self.removeItem(line)
        self.Hlines = []

    def updateCoords(self, x, y):
        # if self.scene2data_xvals is not None:
        if 1:
            p = self.scene2data((x, y))
            # self.emit(QC.SIGNAL('updateLocation(float, float, float, float)'), \
            #    p.x(),p.y(),x,y)
            try:
                self.updateLocation.emit(p.x(), p.y(), x, y)
            except:
                pass

    def my_init(self):
        """init for per type stuff"""
        self.max_data_len = 0
        self.scene2data_xvals = None

    # def makeHLine(self, loc):
    #    rec = self.fV.sceneRect()
    #    eventPen = QG.QPen(QC.Qt.SolidLine)
    #    eventPen.setWidth(10)
    #    eventPen.setColor(QC.Qt.green)
    # x = self.data2scene((loc, self.data_y_min)).x()
    #    x = loc
    # print loc, x, self.data_x_max, self.data_x_min
    # line = self.fscene.addLine(x, rec.y(), x, rec.height()/10., eventPen)
    # line.setZValue(10.)
    def makeHLine(self, loc, color):
        # rec = self.fV.sceneRect()
        print 'line', loc
        eventPen = QG.QPen(QC.Qt.SolidLine)
#        eventPen.setWidth(1.5)
        eventPen.setWidth(2)
        eventPen.setColor(QG.QColor(color))
        eventPen.setCosmetic(True)
        x_loc = self.data2scene((loc, 0)).x()
        # x1 = self.data2scene((loc, -100))
        # print x0,x1
        x0 = QC.QPointF(x_loc, self.fscene.sceneRect().top())
        x1 = QC.QPointF(x_loc, self.fscene.sceneRect().bottom())
        print x0, x1
        line = self.fscene.addLine(QC.QLineF(x0, x1), eventPen)
        line.setZValue(1000.)
        return line

    def reframe(self):
        # print 'reframe',self.scene_rect, self.size(), self.fV.size()
        self.fscene.setSceneRect(self.scene_rect)
        self.fV.setViewportMargins(-2, -2, -2, -2)
        # self.fV.determine_axes_span()
        self.ranges_changed()

    def updatePlots(self, only_grow_in_y=False):
        self.plot_index = 0
        self.sceneheight = 0
        #xmin = None
        #xmax = None
        #ymin = None
        #ymax = None
        # if not only_grow_in_y:
            # self.ymin = None
            # self.ymax = None
        dont_shrink_in_y = True
        rects = []
        for plot in self.plot_datas:
            # print 'Updating:',plotd

            # because cosmetic pens still have width that gets taken into
            # account when making bounding boxes (QT feature), then we have to
            # manually change the sceneRect to the maximum bounding box of
            # paths without the pen width.
            plotd = self.plot_datas[plot]
            r = plotd.boundingrect
            rects.append(r)
            # print 'bounding',r,r.top(),r.bottom()
            # set values if they do not exist
            # if not (xmin and xmax and ymin and ymax):
            #    if xmin is None:
            #        xmin = r.left()
            #    if xmax is None:
            #        xmax = r.right()
            #    if ymin is None:
            #        ymin = r.bottom()
            #    if ymax is None:
            #        ymax = r.top()
            # else:
            #    if r.left() < xmin:
            #        xmin = r.left()
            #    if r.right() > xmax:
            #        xmax = r.right()
            #    if r.top() < ymax:
            # ymax is actually negative because qt axes are:
            # -------------> x
            # |
            # |
            # |
            # |
            # |
            # v y
            #        ymax = r.top()
            #    if r.bottom() > ymin:
            #        ymin = r.bottom()
        # if only_grow_in_y:
        #    if not self.ymin:
        #        self.ymin = ymin
        #    else:
        #        if ymin > self.ymin:
        #            self.ymin = ymin
        #    if not self.ymax:
        #        self.ymax = ymax
        #    else:
        #        if ymax < self.ymax:
        #            self.ymax = ymax
        # else:
        #    self.ymax = ymax
        #    self.ymin = ymin
        # self.xmin = xmin
        # self.xmax = xmax
        # y_span = abs(self.ymax - self.ymin)
        # margin = 0.00
        # self.y_margin = margin*y_span
        # print 'scene',self.xmin, self.xmax, self.ymin, self.ymax
        srect = rects[0]
        for rect in rects:
            srect = srect.united(rect)

        if self.scene_rect is None:
            # self.scene_rect = QC.QRectF(
            # QC.QPointF(self.xmin, self.ymax -
            # margin*y_span),QC.QPointF(self.xmax,self.ymin + margin*y_span))
            self.scene_rect = srect
        else:
            # self.scene_rect.setCoords(self.xmin, self.ymax - margin*y_span
            # ,self.xmax,self.ymin + margin*y_span)
            self.scene_rect = srect

        if dont_shrink_in_y:
            if self.ymax and self.ymax < srect.top():
                srect.setTop(self.ymax)
            else:
                self.ymax = srect.top()
        else:
            self.ymax = srect.top()
        self.ymin = srect.bottom()
        self.xmin = srect.left()
        self.xmax = srect.right()
        if not self.zeroline:
            self.zeroline = self.fscene.addLine(self.xmin, 1, self.xmax, 1)
        else:
            self.zeroline.setLine(self.xmin, 1, self.xmax, 1)
        self.reframe()

    def addPlot(self, name, data, x_vals, color='black',
                size=1, type='line', append=True,
                movable=False,  visibility=True, physical=True):
        # if x_vals == None:
            # FIXME line time should come automatically
        #    x_vals = n.arange(len(data))*10e-3
        # print 'adding plot',name,visibility
        pd = PlottedData(data, x_vals, color, size,
                         self.plot_index + 1, type, movable, visibility, physical)
        self.checkAndSetXvals(x_vals)
        while name in self.plot_datas.keys():
            name += 'i'
        if pd.type == 'line':
            self.makePath(pd)
        elif pd.type == 'circles':
            self.makeCircles(pd)
        self.plot_datas[name] = pd
        self.updatePlots()
        return pd

    def removePlotByName(self, name):
        for pd_name in self.plot_datas:
            if pd_name == name:
                self.removePlotData(self.plot_datas[pd_name])

    def removePlotData(self, plotd):
        if hasattr(plotd, 'group'):
            self.removeItem(plotd.group)
        else:
            self.removeItem(plotd.gpath)

    def updatePlot(self, name, data, x_vals, only_grow=False):
        plotd = self.plot_datas[name]
        # self.removePlotData(plotd)
        plotd.update_data(data, x_vals)
        # self.checkAndSetXvals(x_vals)
        self.redraw(plotd)
#        self.updatePlots(only_grow)
        self.updatePlots(True)

    def redraw(self, plotd):
        self.removeItem(plotd.graphic_item)
        if plotd.type == 'line':
            self.makePath(plotd)
        elif plotd.type == 'circles':
            self.makeCircles(plotd)

    def clear(self):
        print 'clearing'
        self.fscene.clear()
        # if len(self.plot_datas.keys()) > 0:

        for plotd in self.plot_datas:
            del(plotd)
        self.plot_datas = {}
        self.max_data_len = 0
        return

    def makeCircle(self, loc_x, loc_y):
        r = QC.QRectF(loc_x-2, loc_y-2, 4., 4.)
        c = self.fscene.addEllipse(r)
        return c

    def makeRect(self, qrect):
        r = self.fscene.addRect(qrect)
        return r

    def makePath(self, plotd):
        plot_data = self.convert_data(plotd)
        start = plot_data[0]
        path = QG.QPainterPath(start)
        for p in plot_data[1:]:
            path.lineTo(p)
        plotd.boundingrect = path.boundingRect()
        gpath = self.fscene.addPath(path, plotd.pen)

        gpath.setZValue(plotd.Z)

        plotd.drawn = True
        self.plot_index += 1
        # print 'visible', plotd.visibility
        if not plotd.visibility:
            gpath.setVisible(False)
        plotd.graphic_item = gpath
        # print 'makepath',
        # print 'path br', path.boundingRect()
        # print 'gitem br',gpath.boundingRect()

        return

    def makeCircles(self, plotd):
        # testpath = self.makePath(plotd)
        # print 'making circles'
        scaledData = [self.data2scene((x, dy)) for x, dy in
                      zip(plotd.phys_xvalues, plotd.data)]
        # path = []
#        start = scaledData[0]
#        path = QG.QPainterPath(start)
        group = QG.QGraphicsItemGroup()
#        if self.xmin is not None:
        if self.plot_datas:
            p1 = self.fV.mapToScene(QC.QPoint(0, 0))
            p2 = self.fV.mapToScene(QC.QPoint(10, 10))
            p = p2-p1
            # print 'POINTS',p1,p2,p2-p1
            xsize = p.x()
            ysize = p.y()
        else:
#            xspan = plotd.data_x_max-plotd.data_x_min
            xspan = plotd.phys_xvalues[-1]-plotd.phys_xvalues[0]
            yspan = abs(plotd.data_y_max-plotd.data_y_min)
            screensize = 10.  # pixels
            # print self.fV.height(),self.fV.width()
            xpixelsize = xspan*1 / float(self.fV.width())
            ypixelsize = yspan*1.1 / float(
                self.fV.height())  # add a bit for margin too
            xsize = screensize*xpixelsize
            ysize = screensize*ypixelsize

        for i, p in enumerate(scaledData):
            e = self.fscene.addEllipse(p.x()-xsize/2., p.y()-ysize/2.,
                                       xsize, ysize, plotd.pen, plotd.brush)
            e.setZValue(plotd.Z)
            e.setToolTip("%f, %f" % (plotd.phys_xvalues[i], plotd.data[i]))
            group.addToGroup(e)
        plotd.drawn = True
        # self.fscene.removeItem(testpath)
        self.fscene.addItem(group)
        plotd.boundingrect = group.boundingRect()
        group.setZValue(plotd.Z)
        self.plot_index += 1
        # plotd.group=group
        # print 'visible', plotd.visibility
        if not plotd.visibility:
            group.setVisible(False)
        plotd.graphic_item = group
        return group

    def scaleAspect(self, scale):
        """Scale any circle plots so that they would look like
        circles under any horizontal scaling"""
        if len(self.plot_datas.keys()) > 0:
            for plotd in self.plot_datas.values():
                if plotd.drawn:
                    if plotd.type == 'circles':
                        children = plotd.graphic_item.childItems()
                        for c in children:
                            old_x = c.rect().x() + c.rect().width()/2.
                            new_width = c.rect().width()/scale
                            new_height = c.rect().height()
                            new_x = old_x - new_width/2.
                            c.setRect(
                                new_x, c.rect().y(), new_width, new_height)
                    else:
                        pass
        return


class ContinousPlotWidget(PlotWithAxesWidget):

    def convert_data(self, plotd):
        plot_data = [self.data2scene((x, dy)) for x, dy in
                     zip(plotd.phys_xvalues, plotd.data)]
        return plot_data

    def checkAndSetXvals(self, x_vals):
        self.data2scene_xfunc = lambda x: x
        self.scene2data_xfunc = lambda x: x


class SparkFluorescencePlotWidget(ContinousPlotWidget):

    def __init__(self, *args, **kwargs):
        super(SparkFluorescencePlotWidget, self).__init__(*args, **kwargs)
        self.FDHM_line_left = None
        self.FDHM_line_right = None
        self.FWHM_line_left = None
        self.FWHM_line_right = None
        self.FWHM_line_center = None

    def plot_FDHM(self, spark):
        end_loc = spark.FDHM_location
        start_loc = spark.FDHM_max_location
        max_val = spark.FDHM_max_val
        FDHM_val = spark.FDHM_val
        if self.FDHM_line_left:
            self.FDHM_line_left.setLine(
                start_loc, -max_val, start_loc, self.ymin)
            self.FDHM_line_right.setLine(
                end_loc, -FDHM_val, end_loc, self.ymin)
        else:
            self.FDHM_line_left = self.fscene.addLine(QC.QLineF(
                start_loc, -max_val, start_loc, self.ymin))
            self.FDHM_line_right = self.fscene.addLine(
                QC.QLineF(end_loc, -FDHM_val, end_loc, self.ymin))

    def plot_FWHM(self, spark):
        left_loc = spark.FWHM_left_location
        right_loc = spark.FWHM_right_location
        max_val = spark.FWHM_max_val
        max_loc = spark.FWHM_max_location
        FWHM_left_val = spark.FWHM_left_val
        FWHM_right_val = spark.FWHM_right_val
        if self.FWHM_line_left:
            self.FWHM_line_left.setLine(
                left_loc, -FWHM_left_val, left_loc, self.ymin)
            self.FWHM_line_right.setLine(
                right_loc, -FWHM_right_val, right_loc, self.ymin)
            self.FWHM_line_center.setLine(
                max_loc, -max_val, max_loc, self.ymin)
        else:
            self.FWHM_line_left = self.fscene.addLine(QC.QLineF(
                left_loc, -FWHM_left_val, left_loc, self.ymin))
            self.FWHM_line_right = self.fscene.addLine(QC.QLineF(
                right_loc, -FWHM_right_val, right_loc, self.ymin))
            self.FWHM_line_center = self.fscene.addLine(
                QC.QLineF(max_loc, -max_val, max_loc, self.ymin))

    def fitView(self, value=None):
        r = self.fscene.sceneRect()
        # print value
        m = self.fV.transform()
        if value is None:
            # value = self.view_fit_mode
            value = 0
        if value == 0:
            # ignore aspect ratio
            arh = float(self.fV.width())/r.width()
            height = r.height()
            if height == 0:
                height = 1.0
            arw = float(self.fV.height())/height
        # elif value == 1:
        # fit in screen keeping aspect ratio
        #    arw = float(self.fV.width())/r.width()
        #    arh = arw

        elif value == 1:
            # expand but keep aspect ratio
            arh = float(self.fV.height())/r.height()
            arw = arh
        m.setMatrix(arh, 0.0, 0.0, 0.0, arw, 0.0, 0.0, 0.0, 1.0)
        # m2 = self.fV.transform()
        # m2.setMatrix(arh, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        # m3 = self.fV.transform()
        # m3.setMatrix(1, 0.0, 0.0, 0.0, arw, 0.0, 0.0, 0.0, 1.0)

        # self.arh = arh
        # self.arw = arw
        self.fV.setTransform(m)


class DiscontinousPlotWidget(PlotWithAxesWidget):
    # For plotting data from a linescan image, i.e, the averaged fluorescence
    # signal. As the recording can have gaps, we have to take care of
    # discontinuities. This is done by plotting by pixel count and then
    # associating a count with a time through the data2scene function.

    def convert_data(self, plotd):
        if not plotd.physical_x_data:
            # pixel vs data. fluorescence data from image
            plot_data = [QC.QPointF(x, -dy) for x, dy in
                         zip(plotd.xvalues, plotd.data)]
        else:
            # time vs data
            plot_data = [self.data2scene((x, dy)) for x, dy in
                         zip(plotd.phys_xvalues, plotd.data)]
        return plot_data

    def checkAndSetXvals(self, x_vals):
        # We assume that all data plotted on is given with the same dx
        # (because the data originally comes from a linescan with a given
        # pixelsize).
        #
        # print 'setxvals'
        if not self.max_data_len:
            self.max_data_len = len(x_vals)
            if not isinstance(x_vals, list):
                self.scene2data_xvals = x_vals.tolist()
            else:
                self.scene2data_xvals = x_vals
            self.data2scene_xfunc = interp1d(
                x_vals, n.arange(len(x_vals)))
            self.scene2data_xfunc = interp1d(
                n.arange(len(x_vals)), x_vals)
