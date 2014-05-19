from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.static.constants import Constants
from lsjuicer.util.helpers import SenderObject


class MeasureLineItem(QW.QGraphicsLineItem):
    #changed = QC.pyqtSignal()
    def __init__(self, selection_type, boundary, parent = None):
        print 'parent is',parent,boundary
        super(MeasureLineItem, self).__init__(parent)
        self.sender = SenderObject()
        self.boundary = boundary
        self.active = False
        self.pen = selection_type.appearance.pen
        self.active_pen = selection_type.appearance.active_pen
        self.setPen(self.pen)
        self.setAcceptHoverEvents(True)
        #self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(200)
        self.state = Constants.move
        self.maxResizeDistance = 50
        self.initialized = False
        self.editable = True
        self.counter = 0
        self.hovering = False
        self.info_box = None
        self.info_text = None
        self.fm = None

    def make_look_active(self, active):
        self.active = active
        if active:
            self.setPen(self.active_pen)
        else:
            self.setPen(self.pen)

    def setEditable(self, editable):
        self.setAcceptHoverEvents(editable)
        self.editable = editable
        #self.make_look_active(editable)


    def mouseReleaseEvent(self, event):
        self.setPen(self.pen)
        self.setEditable(True)
        self.initialized = True

    def mousePressEvent(self,event):
        pass

    def mouseMoveEvent(self,event):
        pos  = event.scenePos()
        scene_r = self.scene().sceneRect()
        if scene_r.contains(pos) and self.editable:
            r = self.line()
            if self.state == Constants.resize_t or not self.initialized:
                r.setP1(pos)
            elif self.state == Constants.resize_b:
                r.setP2(pos)
            else:
                r.translate(pos-event.lastScenePos())
                if not (scene_r.contains(r.p1()) and scene_r.contains(r.p2())):
                    return
            if self.line() != r:
                emit = True
            else:
                emit = False
            self.setLine(r)

            #draw info box
            loc = r.p1()
            #add some space between line and box
            view = self.scene().views()[0]
            pad_rec = view.mapToScene(QC.QRect(0, 0, 10, 10)).boundingRect()
            loc += QC.QPoint(pad_rec.width(), pad_rec.height())
            #calculate size of info box on scene based on font size
            if self.fm:
                line_height = self.fm.lineSpacing()
            else:
                line_height = 20
            lines = 3
            extra_padding = 0.5
            multiplier = lines + extra_padding
            rec = view.mapToScene(QC.QRect(0, 0, 200, multiplier * line_height)).boundingRect()
            #make sure info box does not go out of the scene
            if loc.x() + rec.width() > scene_r.right():
                over = loc.x() + rec.width() - scene_r.right()
                loc.setX(loc.x() - over)
            if loc.y() + rec.height() > scene_r.bottom():
                over = loc.y() + rec.height() - scene_r.bottom()
                loc.setY(loc.y() - over)

            info_box_rect = QC.QRectF(loc, QC.QSizeF(rec.width(), rec.height()))

            if not self.info_box:
                self.info_box = QW.QGraphicsRectItem(self)
                color = QG.QColor('greenyellow')
                color.setAlphaF(0.7)
                self.info_box.setBrush(QG.QBrush(color))
                pen = QG.QPen(QG.QColor('black'))
                pen.setCosmetic(True)
                self.info_box.setPen(pen)
            self.info_box.setRect(info_box_rect)

            if not self.info_text:
                self.info_text = QW.QGraphicsTextItem(self)
                self.info_text.setDefaultTextColor(QG.QColor('black'))
                self.info_text.setFlag(QW.QGraphicsItem.ItemIgnoresTransformations)
                #self.info_text.setPos(QC.QPointF(0,0))
                font = self.info_text.font()
                font.setFamily('Courier')
                font.setStyleHint(QG.QFont.TypeWriter)
                font.setBold(True)
                font.setPointSize(15)
                self.fm = QG.QFontMetrics(font)
                self.info_text.setFont(font)
            self.info_text.setPos(loc)
            format_string = """<p>
            x<sub>1</sub>:{:.4g}, y<sub>1</sub>:{:.4g}<br>
            x<sub>2</sub>:{:.4g}, y<sub>2</sub>:{:.4g}<br>
            &Delta;x:{:.4g}, &Delta;y:{:.4g}<br></p>
            """
            p1 = r.p1()
            p2 = r.p2()
            info_string = format_string.format(p1.x(), p1.y(),
                                               p2.x(), p2.y(),
                                               - (p2.x() - p1.x()),
                                               p2.y() - p1.y())
            self.info_text.setHtml(info_string)
            if emit:
                self.sender.selection_changed.emit()
        QW.QGraphicsLineItem.mouseMoveEvent(self,event)

    def hoverMoveEvent(self, event):
        self.cursorPositionBasedStyling(event)
        return QW.QGraphicsRectItem.hoverMoveEvent(self,event)

    def hoverLeaveEvent(self, event):
        self.hovering = False
        #if self.initialized:
        #    #self.pen.setStyle(QC.Qt.SolidLine)
        #    self.setPen(self.pen)
        self.make_look_active(False)
        self.unsetCursor()
        return QW.QGraphicsRectItem.hoverLeaveEvent(self,event)

    def resizeDistance(self):
        return self.line().length()/4.

    def cursorPositionBasedStyling(self,event):
        if not self.counter%10:
            if self.initialized and self.editable:
                pos  = event.pos()
                d_t = (pos - self.line().p1()).manhattanLength()
                d_b = (pos - self.line().p2()).manhattanLength()
                if d_t < self.resizeDistance():
                    self.setCursor(QC.Qt.CrossCursor)
                    self.state  = Constants.resize_t
                elif d_b < self.resizeDistance():
                    self.setCursor(QC.Qt.CrossCursor)
                    self.state  = Constants.resize_b
                else:
                    self.setCursor(QC.Qt.SizeAllCursor)
                    self.state = Constants.move
                self.make_look_active(True)
        self.counter +=1

    def hoverEnterEvent(self, event):
        self.hovering = True
        self.counter = 0
        self.cursorPositionBasedStyling(event)
        return QW.QGraphicsLineItem.hoverEnterEvent(self,event)
