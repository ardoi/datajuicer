from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.static.constants import Constants
from lsjuicer.util.helpers import SenderObject


class ROIDataModel(QC.QAbstractListModel):
    def __init__(self, parent=None):
        super(ROIDataModel, self).__init__(parent)
        self.builders = []
        self.rois={}
        self.keys = []
        self.sender = SenderObject()

    def updateData(self):
        self.layoutAboutToBeChanged.emit()
        self.rois = {}
        for b in self.builders:
            for i,r in enumerate(b.rois):
                self.rois["%s %i"%(b.name,i+1)] = {'roi':r,'builder':b}
        self.keys = self.rois.keys()
        self.keys.sort()
        self.layoutChanged.emit()

    def rowCount(self,parent):
        return len(self.rois)

    def delete(self,indices):
        print 'del'
        for i in indices:
            el = self.rois[self.keys[i.row()]]
            el['builder'].delete(el['roi'])
        self.updateData()

    def watchBuilder(self, builder):
        self.builders.append(builder)

    def data(self, index, role):
        if role == QC.Qt.DisplayRole:
            return self.keys[index.row()]
        elif role == QC.Qt.DecorationRole:
            return QG.QColor(self.rois[self.keys[index.row()]]['roi'].color)


class ROIManager(QC.QObject):
    def __init__(self, parent = None):
        super(ROIManager, self).__init__(parent)
        self.dataModel = ROIDataModel()
        self.setup()
        self.active = False
    def setup(self):
        self.roiBuilder = ROIBuilder('ROI', 'blue', 1)
        self.bgRoiBuilder = ROIBuilder('Background', 'lime', 1)
        self.builders = {Constants.ROI:self.roiBuilder, Constants.BGROI:self.bgRoiBuilder}
        #self.types = [Constants.ROI, Constants.BGROI]
        self.activeBuilder = None
        self.dataModel.watchBuilder(self.roiBuilder)
        self.dataModel.watchBuilder(self.bgRoiBuilder)
        self.roiBuilder.ROIDone.connect(lambda:self.setActive(Constants.ROI)
        self.bgRoiBuilder.ROIDone.connect(lambda:self.setActive(Constants.BGROI)

    def roisSelected(self):
        return any([b.roiSelected() for b in self.builders.values()])

    def getROIs(self):
        out = {}
        for k in self.builders.keys():
            out[k] = self.builders[k].rois
        return out

    def setROIActive(self, state):
        self.setActive(Constants.ROI, state)
    def setBgROIActive(self, state):
        self.setActive(Constants.BGROI, state)
    def enableEditing(self, enable):
        for b in self.builders.values():
            b.makeROIsEditable(enable)
    def findAndInitialize(self, roi):
        print 'findand init'
        self.activeBuilder.endInit(roi)

    def setActive(self, rtype,state):
        self.active = state
        if state:
            if rtype == Constants.ROI:
                self.activeBuilder = self.roiBuilder
            elif rtype == Constants.BGROI:
                self.activeBuilder = self.bgRoiBuilder
            self.enableEditing(False)
            self.ROIView.viewport().setCursor(QC.Qt.CrossCursor)
        else:
            if rtype == Constants.ROI:
                self.ROIButtonUncheck.emit()
            elif rtype == Constants.BGROI:
                self.BgROIButtonUncheck.emit()
            self.activeBuilder = None
            self.enableEditing(True)
            self.ROIView.viewport().setCursor(QC.Qt.ArrowCursor)

    def delete(self,indices):
        self.dataModel.delete(indices)
    #def getROI(self, rect):
    #    print 'get',rect,self.activeBuilder
    #    if self.activeBuilder:
    #        r = self.activeBuilder.getROI(rect)
    #        if r:
    #            self.dataModel.updateData()
    #        return r
    #    else:
    #        return None

class GroupManager(ROIManager):

    def setGroupActive(self, state):
        print 'group',state
        self.setActive(Constants.GROUP, state)

    def setup(self):
        self.roiBuilder = ROIBuilder('Group', ['black','orange','green','magenta','red','blue']*3,10)
        self.activeBuilder = None
        self.builders = {Constants.GROUP:self.roiBuilder}
        self.dataModel.watchBuilder(self.roiBuilder)
        self.roiBuilder.ROIDone.connect(lambda:self.setActive(Constants.GROUP)

    def setActive(self, rtype,state):
        print 'setactive'
        self.active = state
        if state:
            if rtype == Constants.GROUP:
                self.activeBuilder = self.roiBuilder
            self.enableEditing(False)
            self.ROIView.viewport().setCursor(QC.Qt.CrossCursor)
        else:
            if rtype == Constants.GROUP:
                self.GroupButtonUncheck.emit()
            self.activeBuilder = None
            self.enableEditing(True)
            self.ROIView.viewport().setCursor(QC.Qt.ArrowCursor)

class GroupManagerWidget(QW.QWidget):

    def __init__(self, roimanager, parent = None):
        super(GroupManagerWidget, self).__init__(parent)
        self.manager = roimanager
        layout = QW.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.view = QW.QListView()
        self.view.setSizePolicy(QW.QSizePolicy.Minimum, QW.QSizePolicy.Maximum)
        self.view.setMaximumWidth(200)
        self.view.setMaximumHeight(100)
        self.view.setModel(self.manager.dataModel)
        buttonLayout = QW.QVBoxLayout()
        layout.addLayout(buttonLayout)
        addRB = QW.QPushButton('Add Group')
        delB = QW.QPushButton('Delete')
        #bg =QG.QButtonGroup(self)
        addRB.setCheckable(True)
        #bg.addButton(addRB)
        #bg.addButton(addBgRB)
        buttonLayout.addWidget(addRB)
        buttonLayout.addWidget(delB)
        layout.addWidget(self.view)
        addRB.toggled[bool].connect(self.manager.setGroupActive)
        delB.clicked[()].connect(lambda:self.manager.delete(self.view.selectedIndexes()))
        self.manager.GroupButtonUncheck.connect(lambda:addRB.setChecked(False))

class ROIManagerWidget(QW.QWidget):

    def __init__(self, roimanager, parent = None):
        super(ROIManagerWidget, self).__init__(parent)
        self.manager = roimanager
        layout = QW.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.view =  QW.QListView()
        self.view.setSizePolicy(QW.QSizePolicy.Minimum, QW.QSizePolicy.Maximum)
        self.view.setMaximumWidth(200)
        self.view.setMaximumHeight(100)
        self.view.setModel(self.manager.dataModel)
        buttonLayout = QW.QVBoxLayout()
        layout.addLayout(buttonLayout)
        addRB = QW.QPushButton('Add ROI')
        addBgRB = QW.QPushButton('Add BgROI')
        delB = QW.QPushButton('Delete')
        #bg =QG.QButtonGroup(self)
        addRB.setCheckable(True)
        addBgRB.setCheckable(True)
        #bg.addButton(addRB)
        #bg.addButton(addBgRB)
        buttonLayout.addWidget(addRB)
        buttonLayout.addWidget(addBgRB)
        buttonLayout.addWidget(delB)
        layout.addWidget(self.view)
        addRB.toggled[bool].connect(self.manager.setROIActive)
        addBgRB.toggled[bool].connect(self.manager.setBgROIActive)
        delB.clicked[()].connect(lambda:self.manager.delete(self.view.selectedIndexes()))
        self.manager.ROIButtonUncheck.connect(lambda:addRB.setChecked(False))
        self.manager.BgROIButtonUncheck.connect(lambda:addBgRB.setChecked(False))

class ROIBuilder(QC.QObject):

    def __init__(self, name, colornames, maximum):
        super(ROIBuilder, self).__init__(None)
        self.roi_count = 0
        self.rois = []
        self.name = name
        self.maximum = maximum
        self.singleColor = True
        if isinstance(colornames,list):
            self.colorname = colornames[0]
            self.singleColor = False
            self.colors = colornames
            self.colorindex = 0
        else:
            self.colorname = colornames

    def delete(self, roi):
        self.rois.remove(roi)
        self.roi_count -= 1
        s = roi.scene()
        s.removeItem(roi)

    def makeROIsEditable(self, editable):
        print 'make editable',self.rois
        for roi in self.rois:
            roi.setEditable(editable)

    def endInit(self, roi):
        print 'end init',roi
        roi.initialized = True
        self.done()

    def roiSelected(self):
        print 'roi query',self, self.roi_count
        return self.roi_count>0

    def done(self):
        #if self.roi_count >= self.maximum:
        self.makeROIsEditable(True)
        self.ROIDone.emit()

    #def getROI(self, rect):
    #    print 'in builder',rect
    #    if self.roi_count >= self.maximum :
    #        return None
    #    else:
    #        self.roi_count += 1
    #        print 'roi count',self.roi_count
    #        roi  = ROIItem(rect)
    #        roi.setColor(self.colorname)
    #        if not self.singleColor:
    #            self.colorindex += 1
    #            self.colorname = self.colors[self.colorindex]
    #        roi.setBuilder(self)
    #        self.rois.append(roi)
    #    #    self.connect(roi, QC.SIGNAL('ROI_Initialized()'),self.done)
    #        return roi

#class SelectionGraphicItem(QG.QGraphicsRectItem):
#    pass

class ROIItem(QW.QGraphicsRectItem):
    def _set_number(self, number):
        self._number = number
        if self.text_item:
            self.text_item.setPlainText("%s"%number)
        return
    def _get_number(self):
        return self._number
    number = property(fget=_get_number, fset=_set_number)

    def _get_text_height_on_scene(self):
        if self.text_item:
            return self.text_item.mapToScene(self.text_item.boundingRect()).boundingRect().height()
        else:
            return None

    def _get_rect_height_on_scene(self):
        return self.mapToScene(self.rect()).boundingRect().height()

    def _get_text_width_on_scene(self):
        if self.text_item:
            return self.text_item.mapToScene(self.text_item.boundingRect()).boundingRect().width()
        else:
            return None

    def _get_rect_width_on_scene(self):
        return self.mapToScene(self.rect()).boundingRect().width()

    text_height_on_scene = property(_get_text_height_on_scene)
    rect_height_on_scene = property(_get_rect_height_on_scene)
    text_width_on_scene = property(_get_text_width_on_scene)
    rect_width_on_scene = property(_get_rect_width_on_scene)

    def __init__(self, selection_type, number, parent = None):
        super(ROIItem, self).__init__(parent)
        self.active = False
        self.pen = selection_type.appearance.pen
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
        self.text_item = None
        self.number = number

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
        #self.pen.setColor(QC.Qt.white)
        self.setPen(self.pen)
        self.setEditable(True)
        self.initialized = True
        #self.builder.endInit(self)
        #self.setCursor(QC.Qt.ArrowCursor)
        #self.initialized = True
        #self.emit(QC.QIGNAL('ROI_Initialized()'))

    def font_resize(self):
        #fm = QG.QFontMetrics(self.font)
        #fm.height()
        #text_height_on_scene = self.text_item.mapToScene(self.text_item.boundingRect()).boundingRect().height()
        #rect_height_on_scene = self.mapToScene(self.rect()).boundingRect().height()
        pointsize = self.font.pointSize()
        max_pointsize = 20
        min_pointsize = 2

        if self.text_height_on_scene > self.rect_height_on_scene * 0.75 \
               or self.text_width_on_scene > self.rect_width_on_scene * 0.5:
            #need to reduce
            while self.text_height_on_scene > self.rect_height_on_scene * 0.75 \
               or self.text_width_on_scene > self.rect_width_on_scene * 0.5:
                pointsize -= 1
                pointsize = max(pointsize, min_pointsize)
                self.font.setPointSize(pointsize)
                self.text_item.setFont(self.font)
                if pointsize == min_pointsize:
                    break
        else:
            #need to make bigger
            while self.text_height_on_scene <= self.rect_height_on_scene * 0.5 \
                           and self.text_width_on_scene <= self.rect_width_on_scene * 0.35:
                pointsize += 1
                pointsize = min(pointsize, max_pointsize)
                self.font.setPointSize(pointsize)
                self.text_item.setFont(self.font)
                if pointsize == max_pointsize:
                    break




    def mousePressEvent(self,event):
        print 'press',self
        self.cursorPositionBasedStyling(event)
        #pos  = event.pos()
        #d = (pos - self.rect().bottomRight()).manhattanLength()
        #if d < self.resizeDistance:
        #    self.state  = Constants.resize
        #else:
        #    self.state = Constants.move
        #self.setPen(self.pen)
    #def boundingRect(self):
    #    r = self.rect()
    #    return QC.QRectF(r.x()-0.5*r.width()-0.5*r.height(),r.y()-0.5*r.width()-0.5*r.height(),2*r.width(),2*r.height())

    def mouseMoveEvent(self,event):
        #self.prepareGeometryChange()
        if self.editable:
            r = self.rect()
            pos  = event.scenePos()
            if self.state == Constants.resize_br or not self.initialized:
                r.setBottomRight(pos)
            elif self.state == Constants.resize_bl:
                r.setBottomLeft(pos)
            elif self.state == Constants.resize_tr:
                r.setTopRight(pos)
            elif self.state == Constants.resize_tl:
                r.setTopLeft(pos)
            else:
                r.translate(pos-event.lastScenePos())
            rn = r.normalized()
            self.setRect(rn)
            if self.text_item:
                self.text_item.setPos(self.rect().topLeft())
                self.font_resize()
        #self.update()
        if not self.text_item:
#            self.text_item = QG.QGraphicsTextItem("<p style='background:red;'>%i</p>"%self.number, self)
            self.text_item = QW.QGraphicsTextItem(self)
            self.text_item.setHtml('<p style="background-color:rgba(255,255,255,80);">%i</p>'%self.number)
            self.text_item.setDefaultTextColor(self.pen.color())
            self.text_item.setPos(self.rect().topLeft())
            self.text_item.setFlag(QW.QGraphicsItem.ItemIgnoresTransformations)
            self.font = self.text_item.font()
            self.font.setFamily('Sans')
            self.font.setBold(True)
            self.font.setPointSize(2)
            self.text_item.setFont(self.font)
        QW.QGraphicsRectItem.mouseMoveEvent(self,event)

    def hoverMoveEvent(self, event):
        self.cursorPositionBasedStyling(event)
        #pos  = event.pos()
        #d = (pos - self.rect().bottomRight()).manhattanLength()
        #if d < 20:
        #    self.setCursor(QC.Qt.SizeFDiagCursor)
        #   # self.setFlag(QGraphicsItem.ItemIsMovable,False)
        #else:
        #    self.setCursor(QC.Qt.SizeAllCursor)
        #QGraphicsRectItem.hoverMoveEvent(self,event)

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
        print 'hover in'
        self.counter = 0
        self.cursorPositionBasedStyling(event)
        #hoverRect = QC.QRectF(self.bottomRight()-QC.QPoint(20,20),self.bottomRight())
        return QW.QGraphicsRectItem.hoverEnterEvent(self,event)
