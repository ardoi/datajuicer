from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC
#import lsjuicer.inout.db.sqla as sa
#import lsjuicer.ui.widgets.clusterwidget as cw
#cc=sa.EventCategoryLocationType
#from lsjuicer import resources
from lsjuicer.ui.tabs.imagetabs import ControlWidget



if __name__=="__main__":

    app=QG.QApplication([])
    app.setAttribute(QC.Qt.AA_DontShowIconsInMenus, on = False)
    #wid=cw.EventCategoryWidget(cc)
    wid = ControlWidget()
    #wid.setFixedWidth(300)
    wid.show()
    wid.raise_()
    app.exec_()
