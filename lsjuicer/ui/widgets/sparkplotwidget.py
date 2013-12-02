from PyQt5 import QtCore as QC

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW


class SparkFluorescencePlotWidget(PixmapPlotWidget):

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




class SparkScene(QW.QGraphicsScene):
    mouseclicked = QC.pyqtSignal(int, int)

    def mouseReleaseEvent(self, event):
        pos = event.scenePos()
        self.mouseclicked.emit(pos.x(), pos.y())

class PlotWidget(QW.QWidget):
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
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        self.fV = QW.QGraphicsView(self)
        self.fV.setRenderHint(QG.QPainter.Antialiasing)
        self.fV.setVerticalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        # self.fV.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        self.fV.setFrameStyle(QW.QFrame.NoFrame)
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



