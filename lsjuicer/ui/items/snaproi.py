from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.static.constants import Constants
from lsjuicer.util.helpers import SenderObject
from lsjuicer.util.helpers import floor_point_x,floor_rect_x

class SnapROIItem(QW.QGraphicsRectItem):

    def __init__(self, selection_type, number, size = None, update_on_release = False, parent = None):
        super(SnapROIItem, self).__init__(parent)
        self.active = False
        self.pen = selection_type.appearance.pen
        self.sender = SenderObject()
#        self.pen= QG.QPen(QC.Qt.SolidLine)
#        self.pen.setWidth(4)
        #self.pen.setColor(QC.Qt.white)
#        self.pen_color = QG.QColor(selection_type.colorname)
#        self.pen.setColor(self.pen_color)

 #       self.pen.setCosmetic(True)
 #       self.pen.setJoinStyle(QC.Qt.MiterJoin)
        self.active_pen = selection_type.appearance.active_pen
        self.state_colors=selection_type.appearance.state_colors
        self.setPen(self.pen)
#        self.setBrush(QC.Qt.white)
      #  self.setAcceptHoverEvents(True)
        #self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(2)
        self.state = Constants.move
        self.maxResizeDistance = 50
        self.initialized = False
        self.editable = True
        self.counter = 0
        self.resizable = True
        self.update_on_release = update_on_release
        self.emit = False

        if size:
            self.resizable = False

    def setEditable(self, editable):
        self.setAcceptHoverEvents(editable)
        self.editable = editable

    def setBuilder(self,builder):
        self.builder = builder

    def setColor(self, colorname):
        self.color = colorname
        try:
            self.pen.setColor(QG.QColor(colorname))
            self.setPen(self.pen)
        except:
            print 'invalid colorname'
    def set_state(self, state):
        self.setColor(self.state_colors[state])

    def mouseReleaseEvent(self,event):
        self.setPen(self.pen)
        self.setEditable(True)
        self.initialized = True
        if self.update_on_release:
            self.sender.selection_changed.emit()

    def mousePressEvent(self,event):
        self.cursorPositionBasedStyling(event)

    def mouseMoveEvent(self,event):
        #self.prepareGeometryChange()
        if self.editable:
            r = self.rect()
            pos  = event.scenePos()
            floor_point_x(pos)
            if self.resizable:
                if self.state == Constants.resize_br or not self.initialized:
                    r.setBottomRight(pos)
                elif self.state == Constants.resize_bl:
                    r.setBottomLeft(pos)
                elif self.state == Constants.resize_tr:
                    r.setTopRight(pos)
                elif self.state == Constants.resize_tl:
                    r.setTopLeft(pos)
                else:
                    new_pos = pos-event.lastScenePos()
                    r.translate(new_pos)
            else:
                new_pos = pos - event.lastScenePos()
                floor_point_x(new_pos)
                r.translate(new_pos)
            rn = r.normalized()

            if self.scene().sceneRect().contains(rn):
                if self.rect() != rn:
                    self.emit = True
                else:
                    self.emit = False
                self.setRect(rn)
                if self.emit and not self.update_on_release:
                    self.sender.selection_changed.emit()

        #QW.QGraphicsRectItem.mouseMoveEvent(self,event)

    def hoverMoveEvent(self, event):
        self.cursorPositionBasedStyling(event)

    def hoverLeaveEvent(self, event):
        if self.initialized:
            #hoverRect = QC.QRectF(self.bottomRight()-QC.QPoint(20,20),self.bottomRight())
            self.make_look_active(False)
            #self.pen.setStyle(QC.Qt.SolidLine)
            #self.setPen(self.pen)
        self.unsetCursor()
        QW.QGraphicsRectItem.hoverEnterEvent(self,event)

    def resizeDistance(self):
        if self.rect().width() / 2. > self.maxResizeDistance and self.rect().height()/2. > self.maxResizeDistance:
            return self.maxResizeDistance
        else:
            return min(self.rect().width() / 2., self.rect().height()/2.)

    def cursorPositionBasedStyling(self,event):
        #don't calculate at every mouse event
        if not self.counter%50:
            if self.initialized and self.editable:
            #if self.editable:
            #if 1:
                if self.resizable:
                    pos  = event.pos()
                    d_br = (pos - self.rect().bottomRight()).manhattanLength()
                    d_bl = (pos - self.rect().bottomLeft()).manhattanLength()
                    d_tr = (pos - self.rect().topRight()).manhattanLength()
                    d_tl = (pos - self.rect().topLeft()).manhattanLength()
                    if d_br < self.resizeDistance():
                        self.setCursor(QC.Qt.SizeFDiagCursor)
                        self.state  = Constants.resize_br
                    elif d_bl < self.resizeDistance():
                        self.setCursor(QC.Qt.SizeBDiagCursor)
                        self.state  = Constants.resize_bl
                    elif d_tr < self.resizeDistance():
                        self.setCursor(QC.Qt.SizeBDiagCursor)
                        self.state  = Constants.resize_tr
                    elif d_tl < self.resizeDistance():
                        self.setCursor(QC.Qt.SizeFDiagCursor)
                        self.state  = Constants.resize_tl
                       # self.setFlag(QGraphicsItem.ItemIsMovable,False)
                    else:
                        self.setCursor(QC.Qt.SizeAllCursor)
                        self.state = Constants.move
                else:
                    self.setCursor(QC.Qt.SizeAllCursor)
                    self.state = Constants.move
                   # self.setFlag(QGraphicsItem.ItemIsMovable)
                #self.pen.setStyle(QC.Qt.DotLine)
                #self.setPen(self.pen)
                self.make_look_active(True)
        self.counter +=1

    def make_look_active(self, active):
        self.active = active
        if active:
            self.setPen(self.active_pen)
        else:
            self.setPen(self.pen)


    def hoverEnterEvent(self, event):
        self.counter = 0
        self.cursorPositionBasedStyling(event)
        #hoverRect = QC.QRectF(self.bottomRight()-QC.QPoint(20,20),self.bottomRight())
        return QW.QGraphicsRectItem.hoverEnterEvent(self,event)
