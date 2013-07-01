import numpy as n

import PyQt4.QtGui as QG
import PyQt4.QtCore as QC


class PlottedData(QC.QObject):

    def __init__(self, data, x_vals, color, size, zvalue, type='line',
                 movable=False, visibility=True, physical=True):

        super(PlottedData, self).__init__(None)
        self.update_data(data, x_vals)
        self.type = type
        self.movable = movable
        self.drawn = False
        self.visibility = visibility
        self.graphic_item = None
        self.physical_x_data = physical  # i.e. x data is time and not pixels
        if len(data) > 1:
            self.data_x_max = float(self.xvalues[- 1])
            self.data_x_min = float(self.xvalues[0])
            self.data_y_max = float(n.max(data))  # + 0.1 * n.mean(self.data)
            self.data_y_min = float(n.min(data))  # - 0.1 * n.mean(self.data)
        else:
            self.data_x_max = float(self.xvalues[0]) * 1.1
            self.data_x_min = float(self.xvalues[0]) * .9
            print data
            print data[0]
            self.data_y_max = float(data[0]) * 1.1
            self.data_y_min = float(data[0]) * .9

        self.pen = QG.QPen(QC.Qt.SolidLine)
        self.size = size
        if type == 'line':
            self.pen.setColor(QG.QColor(color))
            self.pen.setWidth(self.size)
            self.pen.setCosmetic(True)
        else:
            self.pen.setColor(QG.QColor('black'))

        # self.pen.setJoinStyle(QC.Qt.RoundJoin)
        self.brush = QG.QBrush(QG.QColor(color))
        self.Z = zvalue

    def update_data(self, y_vals, x_vals):
        self.xvalues = n.arange(len(x_vals))
        self.phys_xvalues = x_vals
        self.data = y_vals
