from PyQt5 import QtCore

import numpy as n

class OffsetPixmap:
    def __init__(self, pixmap, dx, dy):
        self.pixmap = pixmap
        self.dx = dx
        self.dy = dy

class SplitPixmap:

    def __init__(self, pixmap):
        self.pixmap = pixmap
        self.splits = []

    def getSplits(self):
        s_x = 500
        s_y = 300 
        w = self.pixmap.width()
        h = self.pixmap.height()
        if w%s_x != 0:
            addtox = 1
        if h%s_y != 0:
            addtoy = 1

        dxs = (n.arange(w/s_x + addtox)*s_x).tolist()
        dys = (n.arange(h/s_y + addtoy)*s_y).tolist()
        if addtox:
            dxs.append(dxs[-1]+w%s_x)
        else:
            dxs.append(dxs[-1]+s_x)
        if addtoy:
            dys.append(dys[-1]+h%s_y)
        else:
            dxs.append(dxs[-1]+s_y)
        for i in range(len(dxs)-1):
            for j in range(len(dys)-1):
                cut = [dxs[i], dxs[i+1] - 1, dys[j], dys[j+1] - 1]
                rec = QC.QRect(QC.QPoint(cut[0],cut[2]),QC.QPoint(cut[1],cut[3]))
                copyp = self.pixmap.copy(rec)
                self.splits.append(OffsetPixmap(copyp, dxs[i], dys[j]))
        return self.splits
