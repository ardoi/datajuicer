from PyQt5 import QtCore as QC

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW


from lsjuicer.util.helpers import SenderObject
from lsjuicer.static.constants import Constants
class TransientGraphicItem(QW.QGraphicsItemGroup):
    def __init__(self, parent = None):
        self.transient_rect = None
        self.sender = SenderObject()
        self.fit_line = None
        self.visible_color = QG.QColor('purple')
        self.selected_color = QG.QColor('yellow')
        self.hidden_color = QG.QColor('white')
        self.hidden_color.setAlpha(0)
        self.color = self.hidden_color
        self.group_color = QG.QColor('navy')
        self.visible = False
        self.editable = False
        super(TransientGraphicItem, self).__init__(parent)

    def set_transient_rect(self, transient_rect):
        self.transient_rect = transient_rect
        self.addToGroup(transient_rect)
        #self.transient_rect.setZValue(200)
        self.transient_rect.appearanceSelected(False)

    def set_fit_line(self, fit_pd):
        self.fit_line = fit_pd
        self.addToGroup(fit_pd.graphic_item)
        #normal_pen = QG.QPen(QC.Qt.black)
        #normal_pen.setWidth(2)
        #normal_pen.setCosmetic(True)
        #self.fit_line.setPen(normal_pen)
        #self.fit_line.setZValue(205)
        #blur=QG.QGraphicsBlurEffect()
        #blur.setBlurRadius(2)
        #self.fit_line.setGraphicsEffect(blur)
    def mousePressEvent(self,event):
        self.transient_rect.mousePressEvent(event)
    def mouseReleaseEvent(self,event):
        self.transient_rect.mouseReleaseEvent(event)
    def mouseMoveEvent(self,event):
        self.transient_rect.mouseMoveEvent(event)
    def hoverMoveEvent(self, event):
        self.transient_rect.hoverMoveEvent(event)
    def hoverLeaveEvent(self, event):
        self.transient_rect.hoverLeaveEvent(event)
    def hoverEnterEvent(self, event):
        self.transient_rect.hoverEnterEvent(event)
    def set_visible(self, visible):
        if visible and self.fit_line is None and self.transient_rect.transient.analyzed:
            transient_data = self.transient_rect.transient
            if transient_data.decay_y is not None:
                plot_data = self.transient_rect.collection.plot_widget.\
                        addPlot('Fit_%s'%self.transient_rect.key,
                                transient_data.decay_y,transient_data.decay_x,color='black',size=2)
                self.set_fit_line(plot_data)
                self.setToolTip(u'\u03c4:%.3f\nr:%.3f'%(transient_data.decay,transient_data.relaxation_bl))
            else:
                pass
        #print self.transient_rect,self.transient_rect.rect()
        if visible:
            if self.editable:
                self.color = self.selected_color
            else:
                self.color = self.visible_color
        else:
            self.color = self.hidden_color
        print 'vis', self.color, self.editable, self.visible
        self.visible = visible
        self.setVisible(self.visible or self.editable)

    def set_editable(self, editable):
        self.transient_rect.setSelected(editable)
        self.editable = editable
        print 'set edit',editable
        if editable:
            self.color = self.selected_color
        else:
            if self.visible:
                self.color = self.visible_color
            else:
                self.color = self.hidden_color
        self.setVisible(self.editable or self.visible)
#        if self.transient_rect.selected:



class TransientRect(QW.QGraphicsRectItem):
    def __init__(self, rect, transient, collection, key, normalbrushcolor):
        self.selected = False
        self.moved=False
        self.key=key
        self.transient = transient
        self.state = Constants.move
        self.selected_pen =QG.QPen()
        self.selected_pen.setStyle(QC.Qt.SolidLine)
        self.selected_pen.setColor(QC.Qt.red)
        self.selected_pen.setWidth(1)
        self.selected_pen.setCosmetic(True)
        self.normal_pen = QG.QPen(QC.Qt.black)
        self.normal_pen.setWidth(1)
        self.normal_pen.setCosmetic(True)
        self.collection = collection
        self.maxResizeDistance = 25
        super(TransientRect, self).__init__(rect)
        self.normal_brush = QG.QBrush(self.makeGradient(QG.QColor(normalbrushcolor)))
        self.selected_brush = QG.QBrush(self.makeGradient(QG.QColor('orange')))

    def makeGradient(self, color):
        brushColor =QG.QColor(color)
        brushColor.setAlphaF(0.4)
        brushColor2 =QG.QColor(color)
        brushColor2.setAlphaF(0.15)
        start = self.rect().topLeft()
        stop = self.rect().bottomLeft()
        #start.setY(start.y()+self.rect().height()/4.)
        #stop.setY(stop.y()-self.rect().height()/4.)
        gradient = QG.QLinearGradient(start,stop)
        gradient.setColorAt(0,brushColor)
        gradient.setColorAt(.25,brushColor2)
        gradient.setColorAt(.75,brushColor2)
        gradient.setColorAt(1,brushColor)
        return gradient
#    def setColors(self):
    def setSelected(self, state):
        print 'setselect',state
        self.selected=state
        self.setAcceptHoverEvents(state)
        self.appearanceSelected(state)
        #self.notifyScene(state)

    def appearanceSelected(self,bool):
        if bool:
            self.setPen(self.selected_pen)
            self.setBrush(self.selected_brush)
        else:
            self.setPen(self.normal_pen)
            self.setBrush(self.normal_brush)

    def toggleSelected(self):
        if self.selected:
            print 'unset'
            print self.cursor()
            self.unsetCursor()
            print self.cursor()
        self.setAcceptHoverEvents(not self.selected)
        self.setSelected(not self.selected)

    def updateRR(self,x):
        r = self.rect()
        r.setRight(x)
        self.setRect(r)
        print 'right edge',r.right(),x
        self.key=self.collection.update(self.key,r)

    def updateRL(self,x):
        r = self.rect()
        r.setLeft(x)
        self.setRect(r)
        self.key=self.collection.update(self.key,r)

    #def notifyScene(self,adjust):
    #    print 'notify',adjust
    ##self.scene().start_transient_adjust(self, adjust)
    #    if adjust:
    #        self.scene().selected_transients.append(self)
    #    else:
    #        try:
    #            self.scene().selected_transients.remove(self)
    #        #self.remove(self)
    #        except:
    #            pass
    def remove(self):
        self.collection.remove_transient(self.key)

    def mousePressEvent(self,event):
        print 'pext',event
        self.moved = False
        #self.toggleSelected()
        #return QG.QGraphicsRectItem.mousePressEvent(self,event)

    def mouseReleaseEvent(self,event):
        print 'rext',event
        #if not self.moved:
            #dont change selected state if roi has been moved
        #    self.toggleSelected()
        #return QG.QGraphicsRectItem.mouseReleaseEvent(self,event)

    def mouseMoveEvent(self,event):
        if self.selected:
            self.moved = True
            r = self.rect()
            pos  = event.scenePos()
            #only move in x
            if self.state == Constants.resize_r:
                r.setRight(pos.x())
            elif self.state == Constants.resize_l:
                r.setLeft(pos.x())
            else:
                r.translate(pos.x()-event.lastScenePos().x(),0.0)
            rn = r.normalized()
            self.setRect(rn)
            #self.update()
            #QG.QGraphicsRectItem.mouseMoveEvent(self,event)
            #self.key=self.collection.update(self.key,self.rect())
            self.collection.update(self.key,self.rect())
        return QW.QGraphicsRectItem.mouseMoveEvent(self,event)

    def resizeDistance(self):
        if self.rect().width() / 2. > self.maxResizeDistance:
            return self.maxResizeDistance
        else:
            #return min(self.rect().width() / 2., self.rect().height()/2.)
            return self.rect().width() / 2.

    def cursorPositionBasedStyling(self,event):
        #don't calculate at every mouse event
        if not self.counter%10:
            if self.selected:
                pos  = event.pos()
                d_r = abs(pos.x() - self.rect().right())
                d_l = abs(pos.x() - self.rect().left())
                if d_r < self.resizeDistance():
                    self.setCursor(QC.Qt.SizeHorCursor)
                    self.state  = Constants.resize_r
                elif d_l < self.resizeDistance():
                    self.setCursor(QC.Qt.SizeHorCursor)
                    self.state  = Constants.resize_l
                else:
                    self.setCursor(QC.Qt.SizeAllCursor)
                    self.state = Constants.move
        self.counter +=1

    def hoverMoveEvent(self, event):
        if self.selected:
            self.cursorPositionBasedStyling(event)
        #return QG.QGraphicsRectItem.hoverMoveEvent(self,event)
    def hoverLeaveEvent(self, event):
        print 'hover leave'
        if self.selected:
            self.unsetCursor()
        #return QG.QGraphicsRectItem.hoverEnterEvent(self,event)
    def hoverEnterEvent(self, event):
        print 'hover in',self.selected
        if self.selected:
            self.counter = 0
            self.cursorPositionBasedStyling(event)
            #hoverRect = QC.QRectF(self.bottomRight()-QC.QPoint(20,20),self.bottomRight())
        #return QG.QGraphicsRectItem.hoverEnterEvent(self,event)
    def contextMenuEvent(self, event):
        print 'context'
        menu = QW.QMenu()
        menu.addAction("Remove")
        menu.addAction("Mark")
        menu._exec()

class VisualTransientCollection(QC.QObject):
    def __len__(self):
        return len(self.visual_transients)

    def __getitem__(self, i):
        return self.visual_transients[i]

    def __init__(self, transient_group, plotwidget, color):
        self.visual_transients = {}
        self.transient_group = transient_group
        self.s2d = plotwidget.scene2data
        self.d2s = plotwidget.data2scene
        self.plot_widget = plotwidget
        self.scene = plotwidget.fscene
        self.color = color
        self.plotTransients()
        super(VisualTransientCollection, self).__init__()

    def plotTransients(self):
        for key in self.transient_group.transients.keys():
            print 'new',key
            t = self.transient_group.transients[key]
            rec = QC.QRectF(QC.QPointF(t.start, self.scene.sceneRect().top()),
                    QC.QPointF(t.end, self.scene.sceneRect().bottom()))
            print rec
            tr = TransientRect(rec, t, self, key, self.color)
            tg = TransientGraphicItem()

            self.visual_transients[key] = tg
            self.scene.addItem(tg)
            tg.setZValue(5)
            tg.set_transient_rect(tr)
        self.hideAll()
        print 'created',self.visual_transients.keys()
            #print 'adding',tr,self.scene,tr.scene()

    #def checkTransients(self,x,y):
    #    eventpoint = QC.QPointF(x,y)
    #    for r in self.visual_transients.values():
    #        if r.contains(eventpoint):
    #            r.toggleSelected()

    def remove_transient(self, key):
        #print 'me',self.visual_transients.keys()
        #print 'ts',self.ts.transients.keys()
        tg = self.visual_transients.pop(key)
        #tr.notifyScene(False)
        self.scene.removeItem(tg)
        #del(tr)
        self.transient_group.remove(key)
        self.maxUpdate.emit()

    def update(self,key,rect):
        #t=self.ts.transients[key]
        left = self.s2d((rect.left(),0)).x()
        right= self.s2d((rect.right(),0)).x()
        #newkey = self.ts.update(key,left,right)
        self.transient_group.update(key,left,right)
        #if newkey != key:
        #    tt = self.visual_transients.pop(key)
        #    self.visual_transients[newkey] = tt
        self.maxUpdate.emit()
        #return newkey

    def showAll(self):
        print 'showall now',len(self.transient_group.transients),len(self.visual_transients)
        if len(self.transient_group.transients) != len(self.visual_transients):
            self.plotTransients()
        for k in self.visual_transients.keys():
            self.visual_transients[k].set_visible(True)
            self.transient_group.transients[k].visible = True

    def hideAll(self):
        for k in self.visual_transients.keys():
            self.visual_transients[k].set_visible(False)
            self.transient_group.transients[k].visible = False
            #t=self.visual_transients.pop(k)
            #t.notifyScene(False)
            #self.scene.removeItem(t)
            #del(t)
        #self.visual_transients={}
    def set_visible(self, transient_keys, visible):
        if isinstance(visible, list):
            for key, state in zip(transient_keys, visible):
                self.visual_transients[key].set_visible(state)
        else:
            for key in transient_keys:
                self.visual_transients[key].set_visible(visible)

    def set_editable(self, transient_keys, editable):
        if isinstance(editable, list):
            for key, state in zip(transient_keys, editable):
                self.visual_transients[key].set_editable(state)
        else:
            for key in transient_keys:
                self.visual_transients[key].set_editable(editable)
