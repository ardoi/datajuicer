from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.static.constants import Constants
from lsjuicer.util.helpers import SenderObject


class BoundaryItem(QW.QGraphicsRectItem):
    # changed = QC.pyqtSignal()

    def __init__(self, selection_type, boundary, parent=None):
        super(BoundaryItem, self).__init__(parent)
        # QC.QObject.__init__(self)
        # QG.QGraphicsRectItem.__init__(self)
        print 'parent', parent, boundary
        self.sender = SenderObject()
        self.boundary = boundary
        self.active = False
        self.pen = selection_type.appearance.pen
        self.active_pen = selection_type.appearance.active_pen
        self.brush = selection_type.appearance.get_brush(parent)
        # self.boundary = parent
        # self.active_brush =
        # selection_type.appearance.get_active_brush(parent.rectf)
        self.active_brush = selection_type.appearance.get_active_brush(parent)
        self.setPen(self.pen)
        self.setBrush(self.brush)
        self.setAcceptHoverEvents(True)
        # self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
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
            self.setBrush(self.active_brush)
        else:
            self.setPen(self.pen)
            self.setBrush(self.brush)

    def setEditable(self, editable):
        self.setAcceptHoverEvents(editable)
        self.editable = editable
        # self.make_look_active(editable)

    def mouseReleaseEvent(self, event):
        # self.setPen(self.pen)
        # if not self.initialized:
        #    self.setEditable(False)
        #    self.initialized = True
        print 'release'
        self.setPen(self.pen)
        self.setEditable(True)
        self.initialized = True

    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        # self.prepareGeometryChange()
        # print self.editable,self.state,event.scenePos()
        if self.editable:
            r = self.rect()
            pos = event.scenePos().x()
            if self.state == Constants.resize_r or not self.initialized:
                r.setRight(pos)
            elif self.state == Constants.resize_l:
                r.setLeft(pos)
            else:
                r.translate((event.scenePos()-event.lastScenePos()).x(), 0)
            rn = r.normalized()
            self.setRect(rn)
            self.boundary.update_rect()

    def hoverMoveEvent(self, event):
        self.cursorPositionBasedStyling(event)
        # pos  = event.pos()
        # d = (pos - self.rect().bottomRight()).manhattanLength()
        # if d < 20:
        #    self.setCursor(QC.Qt.SizeFDiagCursor)
        # self.setFlag(QGraphicsItem.ItemIsMovable,False)
        # else:
        #    self.setCursor(QC.Qt.SizeAllCursor)
        return QW.QGraphicsRectItem.hoverMoveEvent(self, event)

    def hoverLeaveEvent(self, event):
        self.hovering = False
        # if self.initialized:
        # self.pen.setStyle(QC.Qt.SolidLine)
        #    self.setPen(self.pen)
        self.make_look_active(False)
        self.unsetCursor()
        return QW.QGraphicsRectItem.hoverLeaveEvent(self, event)

    def resizeDistance(self):
        return self.rect().width()/4.

    def cursorPositionBasedStyling(self, event):
        if not self.counter % 10:
            if self.initialized and self.editable:
                pos = event.pos()
                d_r = abs(pos.x() - self.rect().right())
                d_l = abs(pos.x() - self.rect().left())
                if d_r < self.resizeDistance():
                    self.setCursor(QC.Qt.SizeHorCursor)
                    self.state = Constants.resize_r
                elif d_l < self.resizeDistance():
                    self.setCursor(QC.Qt.SizeHorCursor)
                    self.state = Constants.resize_l
                else:
                    self.setCursor(QC.Qt.SizeAllCursor)
                    self.state = Constants.move
                self.make_look_active(True)
        self.counter += 1

    def hoverEnterEvent(self, event):
        self.hovering = True
        self.counter = 0
        self.cursorPositionBasedStyling(event)
        return QW.QGraphicsRectItem.hoverEnterEvent(self, event)
