import numpy as n

import PyQt4.QtGui as QG
import PyQt4.QtCore as QC


class PlottedData(QC.QObject):
    def __init__(self, y_vals, x_vals, color, size, zvalue,name, style='line'):
        super(PlottedData, self).__init__(None)
        self.update_data(y_vals, x_vals)
        self.style = style
        self.drawn = False
        self.graphic_item = None
        self.name = name
        self.visibility  =True
        #print y_vals.tolist()
        #print x_vals.tolist()
        if len(y_vals) > 1:
            #self.y_vals_x_max = float(self.xvalues[-1])
            #self.y_vals_x_min = float(self.xvalues[0])
            self.x_max = float(n.max(x_vals))
            self.x_min = float(n.min(x_vals))
            self.y_max = float(n.max(y_vals))  # + 0.1 * n.mean(self.y_vals)
            self.y_min = float(n.min(y_vals))  # - 0.1 * n.mean(self.y_vals)
        else:
            self.x_max = float(self.xvalues[0]) * 1.1
            self.x_min = float(self.xvalues[0]) * .9
            self.y_max = float(y_vals[0]) * 1.1
            self.y_min = float(y_vals[0]) * .9

        self.pen = QG.QPen(QC.Qt.SolidLine)
        self.size = size
        if style == 'line':
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

