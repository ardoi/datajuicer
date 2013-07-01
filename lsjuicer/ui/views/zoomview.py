import PyQt4.QtCore as QC
import PyQt4.QtGui as QG


class ZoomView(QG.QGraphicsView):
    hor_zoom_changed = QC.pyqtSignal(float, float)
    hor_range_changed = QC.pyqtSignal(float, float)
    ver_zoom_changed = QC.pyqtSignal(float, float)
    ver_range_changed = QC.pyqtSignal(float, float)
    zoom_level = QC.pyqtSignal(float, float)
    v_axis_param = QC.pyqtSignal(int, int)
    #scaleSignal = QC.pyqtSignal(float)
    #centerSignal = QC.pyqtSignal(float)
    #visibleRectSignal = QC.pyqtSignal(QC.QRectF)
    def __init__(self, parent=None, locked = False):
        super(ZoomView, self).__init__(parent)
        #full_view is False if the scene does not take up the entire view.
        #For example in cases when fitview keeps the aspect ratio of the scene
        self.full_view = False
        self.zoom_count_hor = 0
        self.zoom_count_ver = 0
        self.zooming_hor = False
        self.zooming_ver = False
        #lock horizontal and vertical zoom
        self.locked = locked

    def alert_horizontal_zoom_change(self):
        left, right = self.visible_horizontal_range()
        self.hor_zoom_changed.emit(left,right)
        self.zooming_hor = False

    def alert_vertical_zoom_change(self):
        top, bottom = self.visible_vertical_range()
        self.ver_zoom_changed.emit(top, bottom)
        self.zooming_ver = False

    def alert_horizontal_range_change(self):
        #print 'hor range change'
        if not self.zooming_hor:
            left, right = self.visible_horizontal_range()
            self.hor_range_changed.emit(left, right)

    def alert_vertical_range_change(self):
        #print 'ver range change'
        if not self.zooming_ver:
            top, bottom = self.visible_vertical_range()
            #print 'top bot', top, bottom
            self.ver_range_changed.emit(top, bottom)

    def visible_horizontal_range(self):
        if self.zoom_count_hor:
            rect = self.mapToScene(self.viewport().geometry()).boundingRect()
        else:
            #for some reason the view shows more of the scene than it should. In other cases this is fine, but with 0 zoom level this effect causes the axis ticks to go wrong. To prevent that we use the know scene rectangle
            rect = self.scene().sceneRect()
        return (rect.left(), rect.right())

    def visible_vertical_range(self):
        if 0:#self.zoom_count_ver:
            rect = self.mapToScene(self.viewport().geometry()).boundingRect()
            print rect
        else:
            pass
            #for some reason the view shows more of the scene than it should. In other cases this is fine, but with 0 zoom level this effect causes the axis ticks to go wrong. To prevent that we use the known scene rectangle
            #rect = self.scene().sceneRect()
        rect = self.mapToScene(self.viewport().geometry()).boundingRect()
        scene_rect = self.sceneRect()
        #print rect, scene_rect
        return (max(scene_rect.top(),rect.top() ), min(scene_rect.bottom(),rect.bottom()))

    def reset_zoom(self):
        self.zooming_ver = True
        self.zooming_hor = True
        hor_factor = 1/(1.25**self.zoom_count_hor)
        ver_factor = 1/(1.25**self.zoom_count_ver)
        self.zoom_count_hor = 0
        self.zoom_count_ver = 0
        self.scale_view(hor_factor, ver_factor)
        self.alert_horizontal_zoom_change()
        self.alert_vertical_zoom_change()
        self.setDragMode(QG.QGraphicsView.NoDrag)


    def wheelEvent(self,event):
        """Overridden to catch mouse scroll events and apply appropriate zoom transform"""
        #if not hasattr(self, 'originalZoom'):
        #    self.resetZoom()
        #    #print 'original',self.originalZoom
        event.ignore()
#        rect = self.mapToScene(self.viewport().geometry()).boundingRect()
#        print 'before',rect
        hor_factor = 1.0
        ver_factor = 1.0
        self.zooming_ver = False
        self.zooming_hor = False
        if self.locked:
            self.zooming_ver = True
            self.zooming_hor = True
        else:
            if event.modifiers() & QC.Qt.ShiftModifier:
                #zoom in y
                self.zooming_ver = True
            elif event.modifiers() & QC.Qt.ControlModifier:
                self.zooming_hor = True
            else:
                self.zooming_hor = True
                self.zooming_ver = True


        #print 'zoom',self.zoom_count_hor, self.zoom_count_ver
        #print self.zooming_hor, self.zooming_ver
        if event.delta() > 0:
            if self.zooming_hor:
                self.zoom_count_hor += 1
                hor_factor = 1.25
            if self.zooming_ver:
                self.zoom_count_ver += 1
                ver_factor = 1.25

        else:
            ret = False
            if self.zooming_hor:
                if self.zoom_count_hor > 0:
                    self.zoom_count_hor -= 1
                    hor_factor= 1./1.25
                else:
                    ret = True

            if self.zooming_ver:
                if self.zoom_count_ver > 0:
                    self.zoom_count_ver -= 1
                    ver_factor= 1./1.25
                else:
                    ret = True
            if ret:
                return


        #print 'wheel bf',  factor,self.transform().m11()
        #self.centerSignal.emit(self.mapToScene(event.pos()).x())
        self.scale_view(hor_factor, ver_factor)
        #print 'wheel af',  factor,self.transform().m11()
        #if self.transform().m11()>self.originalZoom:
        #    self.setDragMode(QG.QGraphicsView.ScrollHandDrag)
        #else:
        #    self.setDragMode(QG.QGraphicsView.NoDrag)
        if self.full_view and (self.zoom_count_hor > 0 or self.zoom_count_ver > 0):
            self.setDragMode(QG.QGraphicsView.ScrollHandDrag)
        else:
            self.setDragMode(QG.QGraphicsView.NoDrag)
        #self.visibleRectSignal.emit(self.mapToScene(self.viewport().geometry()).boundingRect())
        #print self.sceneRect()
        if self.locked:
            self.alert_horizontal_zoom_change()
            self.alert_vertical_zoom_change()
        else:
            if self.zooming_hor:
                self.alert_horizontal_zoom_change()
            elif self.zooming_ver:
                self.alert_vertical_zoom_change()
        #QG.QGraphicsView.wheelEvent(self,event)

    #def resetZoom(self):
    #    self.originalZoom = self.transform().m11()

    def determine_axes_span(self):
        """Axes span is the length in pixels used by the axiswidget to draw
        the axes ticks and labels. This is different from the axes range which
        represents the range of values of the scene the axes ticks correspond to.
        To determine the axis span we need to know whether the view is showing
        the entire scene or a section of it. If it's the entire scene then the
        span is however much the scene takes up on the view (can depend on zoom
        level). This we get with mapFromScene. If the rect is smaller than the
        view rect then we use that to determine the span. Otherwise the span is
        the same as the view rect.
        """
        poly = self.mapFromScene(self.sceneRect())
        scene_rect = poly.boundingRect()
        widget_width = self.rect().width()
        widget_height = self.rect().height()
        v_axis_start_loc = max(0, scene_rect.top())
        if v_axis_start_loc == 0:
            self.full_view = True
        else:
            self.full_view = False
        v_axis_height = min(widget_height, scene_rect.height())
        self.v_axis_param.emit(v_axis_start_loc, v_axis_height)

    def scale_view(self, hor_scale_factor, ver_scale_factor ):
        self.scale( hor_scale_factor, ver_scale_factor)
        self.determine_axes_span()
        self.zoom_level.emit(1.25**self.zoom_count_hor,
                1.25**self.zoom_count_ver)
        #self.scaleSignal.emit(scaleFactor)

    def mousePressEvent(self, event):
        """Overridden to catch right click and reset original zoom"""
        #pass
        #if event.button() == QC.Qt.RightButton:
        #    factor = self.transform().m11()
        #    self.scale(self.originalZoom/factor,1)
        #    self.scaleSignal.emit(self.originalZoom/factor)
        #    #print factor
        #elif event.button() == QC.Qt.LeftButton:
        #    self.dragging = True
        #    #print 'dragging',self.dragging

        QG.QGraphicsView.mousePressEvent(self,event)

    def mouseReleaseEvent(self, event):
        #if event.button() == QC.Qt.LeftButton:
        #    self.dragging = False
        #    #print 'dragging',self.dragging

        QG.QGraphicsView.mouseReleaseEvent(self,event)

    def mouseMoveEvent(self, event):
    #    if self.dragging:
    #        print self.mapToScene(self.viewport().geometry()).boundingRect()
        QG.QGraphicsView.mouseMoveEvent(self,event)

    #def resizeEvent(self, event):
    #    print '\n\n\nresize',self.scene()
    #    self.fitInView(self.scene().itemsBoundingRect())
    #    QG.QGraphicsView.resizeEvent(self,event)
   # def resizeEvent(self, event):
   #     QG.QGraphicsView.resizeEvent(self,event)
   #     self.fitInView(self.scene().itemsBoundingRect())
