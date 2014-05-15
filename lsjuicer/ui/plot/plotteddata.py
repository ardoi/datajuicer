import numpy as n

from PyQt5 import QtGui as QG

from PyQt5 import QtCore as QC



class PlottedData(QC.QObject):
    def __init__(self, x_vals, y_vals, zvalue, name,
            style='line', alpha=1.0, color = 'black', size = 1):
        super(PlottedData, self).__init__(None)
        self.style = style
        self.drawn = False
        self.graphic_item = None
        self.name = name
        self.update_data(y_vals, x_vals)
        self.visibility  =True
        #print y_vals.tolist()
        #print x_vals.tolist()

        self.pen = QG.QPen(QC.Qt.SolidLine)
        self.pen.setCosmetic(True)
        self.size = size
        if style == 'line':
            self.pen.setColor(QG.QColor(color))
            self.pen.setWidth(self.size)
        else:
            self.pen.setStyle(QC.Qt.NoPen)
        # self.pen.setJoinStyle(QC.Qt.RoundJoin)
        brush_color = QG.QColor(color)
        brush_color.setAlphaF(alpha)
        self.brush = QG.QBrush(brush_color)
        self.Z = zvalue

    def update_data(self, y_vals, x_vals):
        self.xvalues = n.arange(len(x_vals))
        self.phys_xvalues = x_vals
        self.data = y_vals
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

