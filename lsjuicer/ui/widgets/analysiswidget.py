import os

from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC


from lsjuicer.ui.tabs.imagetabs import AnalysisImageTab
from lsjuicer.ui.tabs.resulttab import ResultTab

class AnalysisWidget(QW.QTabWidget):
    """Widget containing all analysis related stuff (fluorescence view, selection view)"""
    setStatusText = QC.pyqtSignal(str)
    tabs_closed = QC.pyqtSignal()

    def __init__(self, analysis=None, parent=None):
        super(AnalysisWidget, self).__init__(parent)
        self.imageTab = AnalysisImageTab(analysis)
        self.imageTab.setAW(self)
        self.addTab(self.imageTab,'Image')
        self.setStyleSheet("""
        QTabWidget::tab-bar{
            alignment: right;
        }
        """)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.imageTab.positionTXT[str].connect(self.emitStatusTXT)

    def close_tab(self, index):
        widget = self.widget(index)
        widget.deleteLater()
        self.removeTab(index)
        if self.count()==0:
            self.tabs_closed.emit()



    def emitStatusTXT(self, txt):
        self.setStatusText.emit(txt)

    def save_result_data(self):
        resdirname = os.path.join(self.data.filedir,'results')
        if not os.path.isdir(resdirname):
            os.mkdir(resdirname)
        datafilename = os.path.join(resdirname, os.path.basename(self.data.name)+".dat")
        self.resultTab.save_data(datafilename)

    def setData(self, data):
        self.imageTab.showData(data)
        self.data = data

    def add_tab(self, tab, icon, name):
        self.addTab(tab, icon, name)
        self.setCurrentIndex(self.count()-1)

    def makeResTab(self):
        #if self.count() == 3:
        #    w = self.widget(2)
        #    self.removeTab(2)
        #    del(w)
        #self.resultTab = ResultTab(self)
        self.resultTab = ResultTab()
#        self.resultTab = FluorescenceTab(self.DS1,self)
        self.addTab(self.resultTab,'Results')
        #self.setCurrentIndex(2)
        self.resultTab.positionTXT[str].connect(self.emitStatusTXT)
        #self.setCurrentIndex(2)

    def addResPlot(self,*args,**kwargs):
        self.resultTab.addResPlot(*args,**kwargs)
