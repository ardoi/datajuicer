from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC
#import lsjuicer.inout.db.sqla as sa
#import lsjuicer.ui.widgets.clusterwidget as cw
#cc=sa.EventCategoryLocationType
#from lsjuicer import resources
import numpy
from lsjuicer.ui.tabs.imagetabs import ControlWidget, Panels
from lsjuicer.ui.widgets.panels  import PipeChainPanel, VisualizationPanel, FramePanel, AnalysisPanel

from lsjuicer.data.pipes.tools import PipeChain

if __name__=="__main__":

    app=QtGui.QApplication([])
    app.setAttribute(QtCore.Qt.AA_DontShowIconsInMenus, on = False)
    panels = Panels()
    panels.add_type("Default")
    panels.add_panel("Default", PipeChainPanel)
    panels.add_panel("Default", VisualizationPanel)
    panels.add_panel("Default22", FramePanel)
    panels.add_panel("Default22", AnalysisPanel)
    #wid=cw.EventCategoryWidget(cc)
    a=numpy.arange(1000)
    a.shape = (10,10,10)
    pc = PipeChain(None, None)
    pc.set_source_data(a)
    wid = ControlWidget(panels)
    class idata:
        pass
    ida = idata()
    ida.channels = 3
    ida.acquisitions = 10
    wid.init_panel(PipeChainPanel, pipechain=pc, imagedata=ida)
    wid.init_panel(VisualizationPanel, pipechain=pc, imagedata=ida)
    #wid.setFixedWidth(300)
    wid.show()
    wid.raise_()
    app.exec_()
