from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC



class Panels(object):
    def __init__(self):
        self.panel_dict = {}
        self.panels_by_name = {}

    def add_type(self, name):
        if not name in self.panel_dict:
            self.panel_dict[name] = []
        else:
            raise ValueError("Type {} already exists".format(name))

    def add_panel(self, type_name, panel):
        from lsjuicer.ui.widgets.panels  import ActionPanel
        if panel.__base__ != ActionPanel:
            raise ValueError("Panel has to be a subclass of ActionPanel")
        if not type_name in self.panel_dict:
            self.add_type(type_name)
        self.panel_dict[type_name].append(panel)
        self.panels_by_name[panel.__shortname__] = panel

    def get_panel_by_name(self, name):
        if name in self.panels_by_name:
            return self.panels_by_name[name]
        else:
            return None


class PanelClickTree(QW.QWidget):
    visibility_toggled = QC.pyqtSignal(str, int)

    def __init__(self, panels, parent = None):
        super(PanelClickTree, self).__init__(parent)
        layout  = QW.QVBoxLayout()
        self.panels = panels
        self.setLayout(layout)
        view = QW.QTreeView(self)
        model = QG.QStandardItemModel()
        self.model = model
        self.items_by_name = {}
        #model.setHorizontalHeaderItem(0, QG.QStandardItem("Name"))
        #model.setHorizontalHeaderItem(1, QG.QStandardItem("Description"))
        model.setHorizontalHeaderLabels(["Name", "Info"])
        root = model.invisibleRootItem()
        for typename, panel_list in panels.panel_dict.iteritems():
            type_item = QG.QStandardItem(typename)
            root.appendRow(type_item)
            for pi in panel_list:
                panel_item = QG.QStandardItem(pi.__shortname__)
                panel_item.setCheckable(True)
                desc_item = QG.QStandardItem(QG.QIcon(QG.QPixmap(":/information.png")),"Info")
                type_item.appendRow([panel_item, desc_item] )
                self.items_by_name[pi.__shortname__] = panel_item
        #view.setWordWrap(True)
        view.setIndentation(10)
        #view.header().setSectionResizeMode(0, QW.QHeaderView.ResizeToContents)
        #view.header().setSectionResizeMode(1, QW.QHeaderView.ResizeToContents)
        view.setModel(model)
        view.setEditTriggers(QW.QAbstractItemView.NoEditTriggers)
        view.expanded.connect(lambda: view.resizeColumnToContents(0))
        view.collapsed.connect(lambda: view.resizeColumnToContents(0))
        view.clicked.connect(self.clicked)
        layout.addWidget(view)

    def toggle(self, name, state):
        print 'toggle',name
        name = str(name)
        #print [type(el) for el in self.items_by_name], type(name)
        if state:
            sstate = QC.Qt.Checked
        else:
            sstate = QC.Qt.Unchecked
        if name in self.items_by_name:
            item = self.items_by_name[name]
            item.setCheckState(sstate)

    def clicked(self, modelindex):
        print '\nccc'
        print modelindex.row(), modelindex.column(),modelindex.data(),modelindex.parent()
        parent = modelindex.parent()
        name = str(self.model.data(self.model.index(modelindex.row(), 0, parent)))
        state = bool(modelindex.data(10))
        print name
        actionpanel = self.panels.get_panel_by_name(name)
        print name,state,actionpanel
        if actionpanel:
            if modelindex.column() == 1:
                QW.QMessageBox.information(self, "Panel info",
                        "<strong>{0.__shortname__}</strong><br>{0.__doc__}".format(actionpanel))
            elif modelindex.column() == 0:
                self.visibility_toggled.emit(str(name), state)

