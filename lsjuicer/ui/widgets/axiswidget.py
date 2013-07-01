import PyQt4.QtCore as QC
import PyQt4.QtGui as QG


class AxisWidget(QG.QWidget):

    def __init__(self, parent=None):
        self.max_limit = 2000
        self.vmax = self.max_limit
        self.hmax = self.max_limit
        self.min_limit = 20

        # shifting due to dragging the scene
        self.pixels_shifted = 0.0
        # shifting due to the scene not fillling the entire view
        self.start_offset = 0
        self.span = None
        self.tick_positions = []
        self.minval = None
        self.base_min = None
        self.relative_to_start = False
        self.my_init()
        super(AxisWidget, self).__init__(parent)

    def my_init(self):
        pass

    def paintEvent(self, event=None):
        pass

    def param_changed(self, start, span):
        # print 'param changed', start,span
        # for case when image is not filing the view and
        # axis needs to be drawn only on a portion of the available spacee
        self.start_offset = start
        self.span = span

    def minimumSizeHint(self):
        return QC.QSize(self.min_limit*2, self.min_limit)

    def painterStyle(self, painter):
        bigpen = QG.QPen(QG.QBrush(QC.Qt.black), 1)
        painter.setPen(bigpen)
        painter.setRenderHint(QG.QPainter.HighQualityAntialiasing)

    def set_range(self, minimum, maximum):
        # print 'set_range', minimum, maximum
        self.minval = minimum
        self.maxval = maximum
        pixels_per_full_range = self.active_dimension_length
        if self.base_min is not None:
            self.pixels_shifted = -(minimum - self.base_min)/self.pixel_size
        self.repaint()

    @property
    def pixel_size(self):
        return (self.maxval-self.minval)/float(self.active_dimension_length)

    def zoom_changed(self, minimum, maximum):
        # print 'zoom change',minimum, maximum, self
        self.base_min = minimum
        self.base_max = maximum
        self.set_range(minimum, maximum)

    def calculate_ticks_for_range(self):
        """
        range_size: width for horizontal plot and height for vertical
        pixel_value: size of pixel (either in time or space depending on direction)
        """
        # print '\n\ncalc ticks',self
        range_size = self.active_dimension_length
        if self.minval is not None:
            tick_count = int(
                self.active_dimension_length/self.min_tick_distance)
            tick_gap_pix = range_size/float(tick_count)
            self.tick_positions = []
            self.tick_labels = []
            start_pos = self.pixels_shifted % tick_gap_pix
            val = start_pos + self.start_offset
            # print start_pos, self.start_offset, range_size, val, self.pixel_size
            # print self.minval, self.maxval, self.pixel_size
            #+1 to avoid rounding errors resulting in the last tick not being made
            while val <= self.start_offset + range_size + 1:
                self.tick_positions.append(val)
                label_val_on_scene = self.minval + (
                    val-self.start_offset)*self.pixel_size
                if self.relative_to_start:
                    label_val_on_scene -= self.minval
                # print 'value',val, label_val_on_scene, self.minval, self.pixel_size
                # try:
                if 0:
                    if isinstance(self, HorizontalAxisWidget):
                        label_val = self.parent().scene2data(
                            [label_val_on_scene, 0]).x()
                    elif isinstance(self, VerticalAxisWidget):
                        label_val = self.parent().scene2data(
                            [0, label_val_on_scene]).y()
                # except (ValueError, IndexError, AttributeError):
                #    print 'error'
                #    pass
                label_val = label_val_on_scene
                # print "lv",label_val
                self.tick_labels.append("%.2f" % label_val)
                val += tick_gap_pix
                # print val,label_val,
            # print 'start/end',start_pos
            # print 'pos', self.tick_positions
            # print 'label', self.tick_labels
        else:
            self.tick_positions = []


class HorizontalAxisWidget(AxisWidget):
    active_dimension_length = property(QG.QWidget.width)

    def my_init(self):
        self.min_tick_distance = 100.0  # pixels

    def calculate_ticks(self):
        self.calculate_ticks_for_range()

    def maximumSizeHint(self):
        return QC.QSize(self.hmax, self.min_limit)

    def paintEvent(self, event=None):
        self.calculate_ticks()
        if self.tick_positions:
            p = QG.QPainter(self)
            p.fillRect(QC.QRect(0, 0, self.width(), 20),
                       #                    QG.QBrush(QG.QColor('yellow')))
                       self.palette().brush(QG.QPalette.Midlight))
            self.painterStyle(p)
            p.drawLine(QC.QLineF(0, 0, self.width(), 0))
        #    print self.width()
            for pos, label in zip(self.tick_positions, self.tick_labels):
                p.drawLine(QC.QLineF(pos, 1, pos, 10))
                p.drawText(pos+5, 15, label)

    def mouseReleaseEvent(self, event):
        self.relative_to_start = not self.relative_to_start
        self.calculate_ticks()
        self.repaint()
    # def setHmax(self, h):
    #    self.hmax = int(h)
    #    self.updateGeometry()
    # def resetHmax(self):
    #    self.hmax = self.max_limit
    #    self.updateGeometry()


class VerticalAxisWidget(AxisWidget):
    # active_dimension_length = 569-260#property(QG.QWidget.height)
    # active_dimension_length = property(QG.QWidget.height)

    @property
    def active_dimension_length(self):
        if self.span:
            return self.span
        else:
            return self.height()

    def my_init(self):
        self.min_tick_distance = 70.0  # pixels
    # def setVmax(self, v):
    #    self.vmax = int(v)
    #    self.updateGeometry()
    # def resetVmax(self):
    #    self.vmax = self.max_limit
    #    self.updateGeometry()
    # def maximumSizeHint(self):
    #    print 'sh',self.vmax
    #    return QC.QSize(self.min_limit,self.vmax)

    def calculate_ticks(self):
        self.calculate_ticks_for_range()

    def paintEvent(self, event=None):
        self.calculate_ticks()
        if self.tick_positions:
            p = QG.QPainter(self)
            p.fillRect(QC.QRect(0, 0, 40, self.height()),
                       # QC.Qt.magenta)
                       # p.fillRect(QC.QRect(0, 0, self.width(), 20),
                       # QG.QBrush(QG.QColor('yellow')))
                       self.palette().brush(QG.QPalette.Midlight))
            self.painterStyle(p)
            # p.drawLine(QC.QLineF(0,0,self.width(),0))
            p.drawLine(QC.QLineF(39, 0, 39, self.height()))
            count = 0
            for pos, label in zip(self.tick_positions, self.tick_labels):
                p.drawLine(QC.QLineF(39, pos, 30, pos))
                if count == 0:
                    p.drawText(0, pos + 15, label)
                else:
                    # p.drawText(0, pos - 5, label)
                    p.drawText(0, pos + 15, label)

                count += 1

# class AxisMaker:
#    """Base class for deriving AxisMakers
#    :note: beware
#    :attention: oh no!
#    :bug: kills everything
#    :warning: use at own risk"""
#    def __init__(self, scene, parentplotwidget):
# actual width in pixels, visible width in pixels, physical width on scene
#        self.parentwidget = parentplotwidget
#        self.scene = scene
#        self.scale_factor = None
#        """
#        :ivar: scene where to paint axis
#        :type: C{QG.GraphicsScene}
#        """
#        self.textTransform = QG.QTransform()
#        self.setGeometry()
#
#    def setPlotScene(self, scene):
#        self.plotScene  = scene
#        """:ivar: the source scene to get actual width from
#        :type: C{QG.GraphicsScene}"""
#
#    def setGeometry(self):
#        pass
#
# class HorizontalAxisMaker(AxisMaker):
#    def setGeometry(self):
# self.width = 1000 #this needs to be set before plotting to the actual value
#        self.height = 20
# self.min_visible_distance = float(100) #in visible pixels
# self.space_from_tick_to_text = 5.0 #in visible pixels
#    def setScale(self, scale):
#        self.scale_factor *= scale
#        self.paint()
#    def paint(self, scale_factor=1):
#        if self.scale_factor == None:
#            self.scale_factor = scale_factor
# self.scene.clear() #remove previous axis
# self.width = self.plotScene.itemsBoundingRect().width() # get width from plot scene
#        x0 = self.plotScene.itemsBoundingRect().x()
#        self.scene.setSceneRect(x0,0,self.width,self.height)
#        self.scene.addLine(QC.QLineF(x0,0,x0+self.width,0))
# number_of_ticks = int(self.scale_factor*self.width / self.min_visible_distance)
#        number_of_ticks = 10
#        tickpos, d = n.linspace(x0,x0+self.width,number_of_ticks,retstep = True)
# print tickpos,d
#        self.textTransform.setMatrix(1./self.scale_factor, 0, 0, 0,1,0,0,0,1)
#        for j,i in enumerate(tickpos):
# hack to make sure the last tick is also visible
#            if j==number_of_ticks - 1:
#                self.scene.addLine(QC.QLineF( i-0.02*d, 1, i-0.02*d,10))
#            else:
#                self.scene.addLine(QC.QLineF( i, 1, i,100))
#            try:
#                lbl=self.parentwidget.scene2data((i,0)).x()
#                t=self.scene.addSimpleText('%.2f'%lbl)
#                t.setPos(i+self.space_from_tick_to_text*self.textTransform.m11(),5)
#                t.setTransform(self.textTransform)
#            except:
#                pass

# class VerticalAxisMaker(AxisMaker):
#    def setGeometry(self):
# self.height = 1000 #this needs to be set before plotting to the actual value
#        self.width = 40
# self.min_visible_distance = float(70) #in visible pixels
# self.space_from_tick_to_text = 3.0 #in visible pixels
#
#    def paint(self, scale_factor):
# self.scene.clear() #remove previous axis
# self.height = self.plotScene.itemsBoundingRect().height() # get width from plot scene
# self.height = self.plotScene.sceneRect().height() # get width from plot scene
#        y0 = self.plotScene.sceneRect().y()
#        self.scene.setSceneRect(0,y0,self.width,self.height)
#        self.scene.addLine(QC.QLineF(self.width - 1,y0,self.width - 1,y0+self.height))
#        number_of_ticks = int(scale_factor*self.height / self.min_visible_distance)
#        if self.height == 0.0:
#            height = 1.0
#        else:
#            height = self.height
# print y0,y0+height
#        tickpos, d = n.linspace(y0,y0+height,number_of_ticks,retstep = True,endpoint=False)
#
#        tickpos = tickpos.tolist()
# hack to make sure the last tick mark is also painted
#        tickpos.append(tickpos[-1]+0.98*d)
#        self.textTransform.setMatrix(1., 0, 0, 0,1./scale_factor,0,0,0,1)
# try to guess format for ticklabels
# take the middle tick as a representative
#        label_val = self.parentwidget.scene2data((0,tickpos[len(tickpos)/2])).y()
#
#
#
#        for j,i in enumerate(tickpos):
# hack to make sure the last tick is also visible
#            self.scene.addLine(QC.QLineF( self.width -1 , i, self.width - 10,i))
#            try:
#                val  = self.parentwidget.scene2data((0,i)).y()
#                if label_val > 5.0:
#                    try:
#                        label_txt = "{0:>3}".format(int(val))
#                    except:
#                        label_txt = "%i"%val
#                        label_txt = ' '*max(0,3-len(label_txt))+label_txt
#                        print 'error in string formatting, using old style'
#                else:
#                    label_txt = "%.4f"%val
#                t=self.scene.addSimpleText(label_txt)
#                t.setPos(0,i+self.space_from_tick_to_text*self.textTransform.m22())
#                t.setTransform(self.textTransform)
#            except:
#                print 'problem making vertical axis'
#                pass
#
