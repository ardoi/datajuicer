from PyQt4 import QtGui as QG
import lsjuicer.inout.db.sqla as sa
import lsjuicer.ui.widgets.clusterwidget as cw
cc=sa.EventCategoryLocationType
app=QG.QApplication([])
wid=cw.EventCategoryWidget(cc)
wid.show()
app.exec_()
