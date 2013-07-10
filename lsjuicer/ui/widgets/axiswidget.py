import PyQt4.QtCore as QC
import PyQt4.QtGui as QG


class AxisWidget(QG.QWidget):

    def __init__(self, label = None, parent=None):
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
        self.label = label
        #if self.label:
        #    self.min_limit += 20
        self.my_init()
        super(AxisWidget, self).__init__(parent)
    @property
    def label_space(self):
        if self.label:
            return 20
        else:
            return 0

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
        range_size = self.active_dimension_length
        if self.minval is not None:
            tick_count = int(
                self.active_dimension_length/self.min_tick_distance)
            tick_gap_pix = range_size/float(tick_count)
            self.tick_positions = []
            self.tick_labels = []
            start_pos = self.pixels_shifted % tick_gap_pix
            val = start_pos + self.start_offset
            #+1 to avoid rounding errors resulting in the last tick not being made
            while val <= self.start_offset + range_size + 1:
                self.tick_positions.append(val)
                label_val_on_scene = self.minval + (
                    val-self.start_offset)*self.pixel_size
                if self.relative_to_start:
                    label_val_on_scene -= self.minval
                # print 'value',val, label_val_on_scene, self.minval, self.pixel_size
                # try:
                if 1:
                    if isinstance(self, HorizontalAxisWidget):
                        label_val = self.parent().scene2data(
                            [label_val_on_scene, 0]).x()
                    elif isinstance(self, VerticalAxisWidget):
                        label_val = self.parent().scene2data(
                            [0, label_val_on_scene]).y()
                # except (ValueError, IndexError, AttributeError):
                #    print 'error'
                #    pass
                #label_val = label_val_on_scene
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

    def minimumSizeHint(self):
        return QC.QSize(self.min_limit*2, self.min_limit + self.label_space)

    def paintEvent(self, event=None):
        self.calculate_ticks()
        if self.tick_positions:
            p = QG.QPainter(self)
            p.fillRect(QC.QRect(0, 0, self.width(), 20 + self.label_space),
                       self.palette().brush(QG.QPalette.Midlight))
            self.painterStyle(p)
            p.drawLine(QC.QLineF(0, 0, self.width(), 0))
            for pos, label in zip(self.tick_positions, self.tick_labels):
                p.drawLine(QC.QLineF(pos, 1, pos, 10))
                p.drawText(pos+5, 15, label)
            if self.label:
                font = p.font()
                font.setBold(True)
                p.setFont(font)
                p.drawText(self.width()/2, 15+self.label_space, self.label)
                font.setBold(False)
                p.setFont(font)

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
        #print 'active vertical'
        if self.span:
            #print 'span', self.span
            return self.span
        else:
            #print 'height',self.height()
            return self.height()

    def minimumSizeHint(self):
        return QC.QSize(self.min_limit*2+self.label_space, self.min_limit)

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
            p.fillRect(QC.QRect(0, 0, 40+self.label_space, self.height()),
                       # QC.Qt.magenta)
                       # p.fillRect(QC.QRect(0, 0, self.width(), 20),
                       # QG.QBrush(QG.QColor('yellow')))
                       self.palette().brush(QG.QPalette.Midlight))
            self.painterStyle(p)
            # p.drawLine(QC.QLineF(0,0,self.width(),0))
            p.drawLine(QC.QLineF(39+self.label_space, 0, 39+self.label_space, self.height()))
            count = 0
            for pos, label in zip(self.tick_positions, self.tick_labels):
                p.drawLine(QC.QLineF(39+self.label_space, pos, 30+self.label_space, pos))
                if count == 0:
                    p.drawText(self.label_space, pos + 15, label)
                else:
                    # p.drawText(0, pos - 5, label)
                    p.drawText(self.label_space, pos + 15, label)

                count += 1
            if self.label:
                font = p.font()
                font.setBold(True)
                p.setFont(font)
                p.drawText(self.width()/2, 15+self.label_space, self.label)
                p.save()
                p.translate(self.label_space/2, self.height()/2.)
                p.rotate(-90)
                p.drawText(0,0, self.label)
                p.restore()
                font.setBold(False)
                p.setFont(font)
