from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.static.constants import Constants
from lsjuicer.util.helpers import SenderObject


class LineItem(QW.QGraphicsLineItem):
    #changed = QC.pyqtSignal()
    def __init__(self, selection_type, boundary, parent = None):
        print 'parent is',parent,boundary
        super(LineItem, self).__init__(parent)
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
        #self.setPen(self.pen)
        #if not self.initialized:
        #    self.setEditable(False)
        #    self.initialized = True
        print 'release'
        self.setPen(self.pen)
        self.setEditable(True)
        self.initialized = True

    def mousePressEvent(self,event):
        pass

    def mouseMoveEvent(self,event):
        #self.prepareGeometryChange()
        if self.editable:
            r = self.line()
            pos  = event.scenePos()
            if self.state == Constants.resize_t or not self.initialized:
                r.setP1(pos)
            elif self.state == Constants.resize_b:
                r.setP2(pos)
            else:
                r.translate(pos-event.lastScenePos())
            if self.line() != r:
                emit = True
            else:
                emit = False
            self.setLine(r)
            if emit:
                self.sender.selection_changed.emit()
            #self.changed.emit()
        QW.QGraphicsLineItem.mouseMoveEvent(self,event)

    def hoverMoveEvent(self, event):
        self.cursorPositionBasedStyling(event)
        #pos  = event.pos()
        #d = (pos - self.rect().bottomRight()).manhattanLength()
        #if d < 20:
        #    self.setCursor(QC.Qt.SizeFDiagCursor)
        #   # self.setFlag(QGraphicsItem.ItemIsMovable,False)
        #else:
        #    self.setCursor(QC.Qt.SizeAllCursor)
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
