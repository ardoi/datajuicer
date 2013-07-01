from PyQt4 import QtCore as QC
from PyQt4 import QtGui as QG


class PlotDisplay(QG.QGraphicsScene):
    setLocation = QC.pyqtSignal(float, float)

    def __init__(self, parent=None):
        super(PlotDisplay, self).__init__(parent)
        self.selection_builder = None

    def mouseMoveEvent(self, event):
        # if self.r.contains(event.scenePos()):
        toScene = event.scenePos()
        self.setLocation.emit(toScene.x(), toScene.y())
        return QG.QGraphicsScene.mouseMoveEvent(self, event)

    def set_selection_builder(self, builder):
        self.selection_builder = builder

    def mousePressEvent(self, event):
        if self.selection_builder:
            item = self.itemAt(event.scenePos())
            # make sure there is no selection item at the current mouse
            # position
            if not isinstance(item, QG.QGraphicsRectItem):
                selection_start = event.scenePos()
                self.selection_builder.make_selection_rect(
                    selection_start, self.sceneRect())
        return QG.QGraphicsScene.mousePressEvent(self, event)


class FDisplay(PlotDisplay):
    pass


class LSMDisplay(PlotDisplay):
    pass
