from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC

from actionpanel import ActionPanel
from lsjuicer.ui.widgets.smallwidgets import VisualizationOptionsWidget

class VisualizationPanel(ActionPanel):
    __doc__ = """Change visualization settings"""
    __shortname__ = "Visualization"
    settings_changed = QC.pyqtSignal(dict)
    def setup_ui(self):
        vis_layout = QW.QStackedLayout()
        self.setLayout(vis_layout)
        channels = self.imagedata.channels
        for channel in range(channels):
            vis_options = VisualizationOptionsWidget(self.pipechain, self, channel)
            vis_layout.addWidget(vis_options)
            vis_options.settings_changed.connect(self.settings_changed)
        vis_layout.setCurrentIndex(0)

    def channel_change(self, channel):
        self.layout().setCurrentIndex(channel)


