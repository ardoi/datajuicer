import numpy

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.data.pipes.tools import PipeChain

from lsjuicer.ui.widgets.plot_with_axes_widget import PixmapPlotWidget
from lsjuicer.ui.plot.pixmapmaker import PixmapMaker
from lsjuicer.ui.widgets.smallwidgets import VisualizationOptionsWidget

class BasicPixmapPlotWidget(QW.QWidget):
    def __init__(self, parent=None):
        super(BasicPixmapPlotWidget, self).__init__(parent)
        pc = PipeChain(pixel_size=numpy.array((0.25, 0.25)))
        #pc.pipe_state_changed.connect(self.force_new_pixmap)
        self.pipechain = pc
        pixmaker = PixmapMaker(pc)
        self.pixmaker = pixmaker

        self.plot_widget = PixmapPlotWidget(parent=self,antialias=False)
        self.scene = self.plot_widget.fscene
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.plot_widget)
        self.image_shown = False
        vis_options_pb = QW.QPushButton("Visualization properties")
        vis_options_pb.clicked.connect(self.show_vis_options_dialog)
        vis_options_pb.setIcon(QG.QIcon('://color_wheel.png'))
        layout.addWidget(vis_options_pb)
    def force_new_pixmap(self, v = None):
        self.make_new_pixmap(force = True)

    def make_new_pixmap(self, settings = {}, force = False):
        pixmaker = self.pixmaker
        QC.QTimer.singleShot(10, lambda :
                pixmaker.makeImage(image_settings = settings, force = force))
        if self.image_shown:
            QC.QTimer.singleShot(15, lambda :
                    self.plot_widget.replacePixmap(pixmaker.pixmap))
        else:
            print 'showing image with tstamps'
            QC.QTimer.singleShot(20, lambda :
                    self.plot_widget.addPixmap(pixmaker.pixmap,
                        self.xvals, self.yvals))
            self.image_shown = True
        QC.QTimer.singleShot(25, lambda :self.plot_widget.fitView())

    def set_data(self, data):
        if data.ndim == 2:
            data = data.copy()
            data.shape = (1,1,data.shape[0],data.shape[1])
        self.pipechain.set_source_data(data)
        self.xvals = numpy.arange(data.shape[3])
        self.yvals = numpy.arange(data.shape[2])
        self.make_new_pixmap(force=True)

    def change_pixmap_settings(self, settings):
        self.make_new_pixmap(settings)

    def show_vis_options_dialog(self):
        dialog = QW.QDialog(self)
        layout = QW.QHBoxLayout()
        dialog.setLayout(layout)
        widget = VisualizationOptionsWidget(self.pipechain, parent=dialog)
        widget.settings_changed.connect(self.change_pixmap_settings)
        widget.close.connect(dialog.accept)
        layout.addWidget(widget)
        self.vis_widget = widget
        dialog.setModal(False)
        dialog.show()
        dialog.resize(400, 400)
        widget.do_histogram()
