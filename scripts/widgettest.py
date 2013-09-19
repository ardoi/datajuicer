from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC
#import lsjuicer.inout.db.sqla as sa
#import lsjuicer.ui.widgets.clusterwidget as cw
#cc=sa.EventCategoryLocationType
from lsjuicer import resources


class ClickTree(QG.QWidget):
    def __init__(self, parent = None):
        super(ClickTree, self).__init__(parent)
        layout  = QG.QVBoxLayout()
        self.setLayout(layout)
        view = QG.QTreeView(self)
        model = QG.QStandardItemModel()
        #model.setHorizontalHeaderItem(0, QG.QStandardItem("Name"))
        #model.setHorizontalHeaderItem(1, QG.QStandardItem("Description"))
        model.setHorizontalHeaderLabels(["Name", "Info"])
        root = model.invisibleRootItem()
        for i in range(1,4):
            type_item = QG.QStandardItem("Type {}".format(i))
            root.appendRow(type_item)
            for j in range(i*3):
                panel_item = QG.QStandardItem("Panel {}".format(j))
                panel_item.setCheckable(True)
                desc_item = QG.QStandardItem(QG.QIcon(QG.QPixmap(":/information.png")),"Info")
                type_item.appendRow([panel_item, desc_item] )
        view.setWordWrap(True)
        view.setIndentation(10)
        view.header().setResizeMode(0, QG.QHeaderView.ResizeToContents)
        view.header().setResizeMode(1, QG.QHeaderView.ResizeToContents)
        view.setModel(model)
        print resources
        view.setEditTriggers(QG.QAbstractItemView.NoEditTriggers)
        view.expanded.connect(lambda: view.resizeColumnToContents(0))
        view.collapsed.connect(lambda: view.resizeColumnToContents(0))
        view.clicked.connect(self.clicked)
        layout.addWidget(view)

    def clicked(self, modelindex):
        print modelindex, modelindex.row(), modelindex.column()
        if modelindex.column() == 1:
            QG.QMessageBox.information(self, "info", "this is type {} panel {}".format(modelindex.row(), modelindex.column()))


if __name__=="__main__":

    app=QG.QApplication([])
    app.setAttribute(QC.Qt.AA_DontShowIconsInMenus, on = False)
    #wid=cw.EventCategoryWidget(cc)
    wid = ClickTree()
    #wid.setFixedWidth(300)
    wid.show()
    wid.raise_()
    app.exec_()
