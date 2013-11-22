from PyQt5 import QtWidgets as QW

class ActionPanel(QW.QWidget):
    def __init__(self, parent = None):
        super(ActionPanel, self).__init__(parent)
        self.imagedata = parent.imagedata
        self.pipechain = parent.pipechain
        self.analysis = parent.analysis
        self.parentwidget = parent
        self.setup_ui()

    def provide_range(self):
        return None

