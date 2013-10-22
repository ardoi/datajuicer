from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore, QtWidgets


from constants import Constants

class StartUI(QW.QDialog):
    mode_set = QC.pyqtSignal(int)
    """Main user interface window"""
    def __init__(self, parent = None):
        super(StartUI, self).__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.modeasker = QW.QWidget()
        modelayout = QW.QVBoxLayout()
        self.modeasker.setLayout(modelayout)
        modelayout.addWidget(QW.QLabel('Choose mode:'))
        buttonlayout = QW.QHBoxLayout()
        self.sparkpix_g = QG.QPixmap(":/sparkbutton_gray.png")
        self.sparkicon = QG.QIcon(self.sparkpix_g)
        self.sparkpix = QG.QPixmap(":/sparkbutton.png")

        self.transientpix_g = QG.QPixmap(":/transientbutton_gray.png")
        self.transienticon = QG.QIcon(self.transientpix_g)
        self.transientpix = QG.QPixmap(":/transientbutton.png")

        self.sparkb = QW.QPushButton(self.sparkicon,'')
        self.sparkb.setCheckable(True)
        self.sparkb.setIconSize(QC.QSize(140, 140))
        self.sparkb.setSizePolicy(QW.QSizePolicy.Expanding,
                QW.QSizePolicy.Expanding)


        self.transientb = QW.QPushButton(self.transienticon,'')
        self.transientb.setCheckable(True)
        self.transientb.setMouseTracking(True)
        self.transientb.setIconSize(QC.QSize(140, 140))
        self.transientb.setSizePolicy(QW.QSizePolicy.Expanding,
                QW.QSizePolicy.Expanding)
        buttonlayout.addWidget(self.sparkb)
        buttonlayout.addWidget(self.transientb)
        modelayout.addLayout(buttonlayout)
        self.gobutton = QW.QPushButton('OK')
        self.gobutton.setEnabled(False)
        modelayout.addWidget(self.gobutton)
        self.setLayout(QW.QVBoxLayout())
        self.layout().addWidget(self.modeasker)
        #self.setCentralWidget(self.modeasker)
        onsc = lambda : self.setbuttons(0)
        ontc = lambda : self.setbuttons(1)
        self.sparkb.clicked[()].connect(onsc)
        self.transientb.clicked[()].connect(ontc)
        self.gobutton.clicked[()].connect(self.go)

        #self.setWindowFlags(QC.Qt.Dialog)

    def go(self):
        if self.sparkb.isChecked():
            self.mode_set.emit(Constants.SPARK_TYPE)
        else:
            self.mode_set.emit(Constants.TRANSIENT_TYPE)
        #self.close()
        return QW.QDialog.accept(self)

    def setbuttons(self, state):
        if not self.gobutton.isEnabled():
            self.gobutton.setEnabled(True)
        if state == 0:
            self.sparkb.setChecked(True)
            self.transientb.setChecked(False)
            self.sparkicon = QG.QIcon(self.sparkpix)
            self.transienticon = QG.QIcon(self.transientpix_g)
        elif state == 1:
            self.transientb.setChecked(True)
            self.sparkb.setChecked(False)
            self.sparkicon = QG.QIcon(self.sparkpix_g)
            self.transienticon = QG.QIcon(self.transientpix)
        self.sparkb.setIcon(self.sparkicon)
        self.transientb.setIcon(self.transienticon)


