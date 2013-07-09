import PyQt4.QtCore as QC
import PyQt4.QtGui as QG
from scipy.interpolate import interp1d
import numpy as n

from lsjuicer.ui.scenes import PlotDisplay
from lsjuicer.ui.views import ZoomView
from lsjuicer.ui.widgets.axiswidget import VerticalAxisWidget, HorizontalAxisWidget
from lsjuicer.ui.plot.plotteddata import PlottedData
from lsjuicer.static.constants import Constants


class PlotWithAxesWidget(QG.QWidget):
    updateLocation = QC.pyqtSignal(float, float, float, float)

    def __init__(self,  parent=None, sceneClass=None, antialias=True, xlabel = None, ylabel = None):
        super(PlotWithAxesWidget, self).__init__(parent)
        # self.plot_sp = 250.
        self.plot_datas = {}
        self.antialias = antialias
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.setupUI(sceneClass)
        self.plot_index = 0
        self.scene_rect = None
        self.scene2data_xvals = None
        self.scene2data_yvals = None
        self.ymax = None
        self.ymin = None
        self.xmax = None
        self.xmin = None
        self.zeroline = 1
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

    def addPixmap(self, pixmap, xvals=None, yvals=None):
        if xvals is not None:
            self.checkAndSetXvals(xvals)
#        self.scene2data_xvals = xvals
        if yvals is not None:
            self.scene2data_yvals = yvals
        brush = QG.QBrush(QG.QColor('black'))
        self.fscene.setBackgroundBrush(brush)
        self.gpix = self.fscene.addPixmap(pixmap)
        rect = QC.QRectF(0, 0, pixmap.width(), pixmap.height())
        if self.scene_rect == rect:
            return
        self.scene_rect = rect  # path.boundingRect()
        self.reframe()
        self.fitView()

    def replacePixmap(self, pixmap):
        if self.gpix:
            self.fscene.removeItem(self.gpix)
        self.addPixmap(pixmap, None, None)

    def center_graphicsitem(self, item):
        self.fV.centerOn(item)

    def fitView(self, value=None):
        if value is not None:
            self.aspect_ratio = value
        self.fV.fitInView(self.scene_rect, self.aspect_ratio)  # value)
        self.fV.determine_axes_span()

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
        self.fV = ZoomView()
        self.fV.setTransformationAnchor(QG.QGraphicsView.AnchorUnderMouse)
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
        self.h_axis = HorizontalAxisWidget(parent=self, label = self.xlabel)

        self.v_axis = VerticalAxisWidget(parent=self, label = self.ylabel)
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
        action_toolbutton.setMaximumHeight(20)
        action_toolbutton.setMaximumWidth(40)
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
        zoomlevel_widget.setMaximumWidth(40)
        zoomlevel_widget.setMaximumHeight(20)
        zoomlevel_widget.setToolTip('Zoom levels - horizontal : vertical')
        fLayout.addWidget(zoomlevel_widget, 2, 0, QC.Qt.AlignHCenter)

        self.fV.show()

        if sceneClass is None:
            self.fscene = PlotDisplay()
        else:
            self.fscene = sceneClass()

        self.fV.setScene(self.fscene)
        if self.antialias:
            self.fV.setRenderHint(QG.QPainter.Antialiasing)
#        self.fV.setRenderHint(QG.QPainter.HighQualityAntialiasing)
        self.fV.setVerticalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        self.fV.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)

        self.fscene.setLocation.connect(self.updateCoords)
        QG.QApplication.processEvents()

    def zoom_level_changed(self, h_zoom, v_zoom):
        #t= self.fV.transform()
        #print 'transform', t.m11(), t.m12(), t.m13(),t.m21(),t.m22(),t.m23(),t.m31(),t.m32(),t.m33()
        #print 'zoom', t.m11()/self.base_transform.m11(), t.m22()/self.base_transform.m22()
        #print 'zf', h_zoom, v_zoom
        self.reset_zoom_action.setEnabled(h_zoom > 1 or v_zoom > 1)
        self.zoom_h_label.setText('%.1f' % h_zoom)
        self.zoom_v_label.setText('%.1f' % v_zoom)
        self.scale_aspect(h_zoom, v_zoom)

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
        if isinstance(spoint, QC.QPointF):
            sx = spoint.x()
            sy = - spoint.y()
        else:
            sx = spoint[0]
            sy = spoint[1]
        #try:
        if 1:
            #x_out = self.scene2data_xfunc(sx)
            x_out = sx
            y_out = - sy  # the value from scene is also data value
            #if self.scene2data_yvals is None:
            #    y_out = - sy  # the value from scene is also data value
            #else:
            #    y_out = self.scene2data_yvals[int(sy)]

            return QC.QPointF(x_out, y_out)
        #except:
        #    return spoint

    def data2scene(self, dpoint):
        dx = dpoint[0]
        dy = dpoint[1]
        #ret = QC.QPointF(self.data2scene_xfunc(dx), -dy)
        ret = QC.QPointF(dx, -dy)
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

    def makeHLine(self, loc, color):
        eventPen = QG.QPen(QC.Qt.SolidLine)
        eventPen.setWidth(2)
        eventPen.setColor(QG.QColor(color))
        eventPen.setCosmetic(True)
        x_loc = self.data2scene((loc, 0)).x()
        x0 = QC.QPointF(x_loc, self.fscene.sceneRect().top())
        x1 = QC.QPointF(x_loc, self.fscene.sceneRect().bottom())
        line = self.fscene.addLine(QC.QLineF(x0, x1), eventPen)
        line.setZValue(1000.)
        return line

    def reframe(self):
        QG.QApplication.processEvents()
        print 'setting scene rect', self.scene_rect
        #self.fscene.addRect(self.scene_rect)
        self.fscene.setSceneRect(self.scene_rect)
        #self.fV.setViewportMargins(-2, -2, -2, -2)
        self.ranges_changed()
        QG.QApplication.processEvents()

    def updatePlots(self):
        #QG.QApplication.processEvents()
        self.plot_index = 0
        #rects = []
        #for plot in self.plot_datas:
        #    # because cosmetic pens still have width that gets taken into
        #    # account when making bounding boxes (QT feature), then we have to
        #    # manually change the sceneRect to the maximum bounding box of
        #    # paths without the pen width.
        #    plotd = self.plot_datas[plot]
        #    r = plotd.boundingrect
        #    rects.append(r)
        #    # print 'bounding',r,r.top(),r.bottom()
        #    # set values if they do not exist
        #    # if not (xmin and xmax and ymin and ymax):
        #    #    if xmin is None:
        #    #        xmin = r.left()
        #    #    if xmax is None:
        #    #        xmax = r.right()
        #    #    if ymin is None:
        #    #        ymin = r.bottom()
        #    #    if ymax is None:
        #    #        ymax = r.top()
        #    # else:
        #    #    if r.left() < xmin:
        #    #        xmin = r.left()
        #    #    if r.right() > xmax:
        #    #        xmax = r.right()
        #    #    if r.top() < ymax:
        #    # ymax is actually negative because qt axes are:
        #    # -------------> x
        #    # |
        #    # |
        #    # |
        #    # |
        #    # |
        #    # v y
        #    #        ymax = r.top()
        #    #    if r.bottom() > ymin:
        #    #        ymin = r.bottom()
        #srect = rects[0]
        #for rect in rects:
        #    srect = srect.united(rect)

        xmin = min([pd.x_min for pd in self.plot_datas.values()])
        xmax = max([pd.x_max for pd in self.plot_datas.values()])
        ymin = min([pd.y_min for pd in self.plot_datas.values()])
        ymax = max([pd.y_max for pd in self.plot_datas.values()])
        print 'extents', xmin, xmax, ymin, ymax
        self.scene_rect = QC.QRectF(xmin,-ymax, xmax-xmin, ymax-ymin)
        #self.scene_rect = self.scene.sceneRect()

        #if dont_shrink_in_y:
        #    if self.ymax and self.ymax < srect.top():
        #        srect.setTop(self.ymax)
        #    else:
        #        self.ymax = srect.top()
        #else:
        #    self.ymax = srect.top()
        #self.ymin = srect.bottom()
        #self.xmin = srect.left()
        #self.xmax = srect.right()
        #print 'update srect',srect
        self.reframe()
        self.fitView()
        for pd in self.plot_datas.values():
            if pd.style == 'lineV':
                self.makePath(pd)
            elif pd.style == 'circles':
                self.makeCircles(pd)
        self.base_transform = self.fV.transform()

    def addPlot(self, name, x_vals, y_vals, plotstyle, hold_update=False):
        while name in self.plot_datas.keys():
            name += 'i'
        print 'addplot',name, min(x_vals), max(x_vals), min(y_vals),max(y_vals)
        pd = PlottedData(x_vals, y_vals, self.plot_index + 1, name, **plotstyle)
        self.plot_datas[name] = pd
        if not hold_update:
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
        QG.QApplication.processEvents()
        scaledData = [self.data2scene((x, dy)) for x, dy in
                      zip(plotd.phys_xvalues, plotd.data)]
        group = QG.QGraphicsItemGroup()
        print 'scene is', self.fscene.sceneRect()
#        if self.xmin is not None:
        if 1:#self.plot_datas:
            p1 = self.fV.mapToScene(QC.QPoint(0, 0))
            p2 = self.fV.mapToScene(QC.QPoint(10, 10))
            p = p2-p1
            xsize = p.x()
            ysize = p.y()

        #else:
        #    print 'optionb'
#       #     xspan = plotd.data_x_max-plotd.data_x_min
        #    xspan = plotd.phys_xvalues[-1]-plotd.phys_xvalues[0]
        #    yspan = abs(plotd.data_y_max-plotd.data_y_min)
        #    screensize = 10.  # pixels
        #    # print self.fV.height(),self.fV.width()
        #    xpixelsize = xspan*1 / float(self.fV.width())
        #    ypixelsize = yspan*1.1 / float(
        #        self.fV.height())  # add a bit for margin too
        #    xsize = screensize*xpixelsize
        #    ysize = screensize*ypixelsize

        for i, p in enumerate(scaledData):
            e = self.fscene.addEllipse(p.x()-xsize/2., p.y()-ysize/2.,
                                       xsize, ysize, plotd.pen, plotd.brush)
            #e.setFlag(QG.QGraphicsItem.ItemIgnoresTransformations)
            e.setZValue(plotd.Z)
            e.setToolTip("%f, %f" % (plotd.phys_xvalues[i], plotd.data[i]))
            group.addToGroup(e)
        plotd.drawn = True
        self.fscene.addItem(group)
        plotd.boundingrect = group.boundingRect()
        group.setZValue(plotd.Z)
        self.plot_index += 1
        if not plotd.visibility:
            group.setVisible(False)
        plotd.graphic_item = group
        plotd.base_size = (xsize, ysize)
        print 'base size', plotd.base_size
        return group

    def scale_aspect(self, h_scale, v_scale):
        """Scale any circle plots so that they would look like
        circles under any scaling"""
        #if h_scale == v_scale:
        #    return
        #else:
        #    new_h_scale = 1.0
        #    new_v_scale = 1.0
        #    if h_scale > v_scale:
        #        new_h_scale = h_scale/v_scale
        #    elif h_scale<v_scale:
        #        new_v_scale = v_scale/h_scale
        if 1:
            if len(self.plot_datas.keys()) > 0:
                for plotd in self.plot_datas.values():
                    if plotd.drawn:
                        children = plotd.graphic_item.childItems()
                        p1 = self.fV.mapToScene(QC.QPoint(0, 0))
                        p2 = self.fV.mapToScene(QC.QPoint(10, 10))
                        p = p2-p1
                        xsize = p.x()
                        ysize = p.y()
                        for c in children:
                            x=c.rect().center().x()
                            y=c.rect().center().y()
                            c.setTransform(QG.QTransform().translate(x, y).
                                    scale(1/(plotd.base_size[0]/xsize),1/( plotd.base_size[1]/ysize)).translate(-x, -y))
                            #old_x = c.rect().center().x()
                            #old_y = c.rect().center().y()
                            #new_width = plotd.base_size[0]/h_scale
                            #new_height = plotd.base_size[1]/v_scale

                            #new_x = old_x - new_width/2.
                            #new_y = old_y - new_height/2.
                            #new_x = old_x - xsize/2.
                            #new_y = old_y - ysize/2.
                            #c.setRect(new_x, new_y, new_width, new_height)
                            #c.setRect(new_x, new_y, xsize, ysize)


class ContinousPlotWidget(PlotWithAxesWidget):

    def convert_data(self, plotd):
        plot_data = [self.data2scene((x, dy)) for x, dy in
                     zip(plotd.phys_xvalues, plotd.data)]
        return plot_data

    #def checkAndSetXvals(self, x_vals):
    #    self.data2scene_xfunc = lambda x: x
    #    self.scene2data_xfunc = lambda x: x


class DiscontinousPlotWidget(PlotWithAxesWidget):
    # For plotting data from a linescan image, i.e, the averaged fluorescence
    # signal. As the recording can have gaps, we have to take care of
    # discontinuities. This is done by plotting by pixel count and then
    # associating a count with a time through the data2scene function.

    def convert_data(self, plotd):
        if not plotd.physical_x_data:
            # pixel vs data. fluorescence data from image
            plot_data = [QC.QPointF(x,dy) for x, dy in
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
