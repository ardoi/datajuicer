from collections import defaultdict

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC

class Events(object):
    def __init__(self):
        self.types = []
        self.event_dict = defaultdict(list)
        self.status_dict = defaultdict(list)

    def add_event(self, event):
        event_type = event.category.category_type.name
        self.event_dict[event_type].append(event)
        self.status_dict[event_type].append(False)

    def change(self, event_type, row, status):
        #print event_type, row, status, len(self.status_dict[event_type])
        if row is not None:
            self.status_dict[event_type][row]=status
        else:
            for k in range(len(self.status_dict[event_type])):
                self.status_dict[event_type][k] = status
        #print self.status_dict

class EventClickTree(QW.QWidget):
    visibility_toggled = QC.pyqtSignal(str, int)

    def __init__(self, parent = None):
        super(EventClickTree, self).__init__(parent)
        layout  = QW.QVBoxLayout()
        self.setLayout(layout)
        view = QW.QTreeView(self)
        model = QG.QStandardItemModel()
        self.model = model
        self.items_by_name = defaultdict(list)
        view.setIndentation(10)
        #view.header().setSectionResizeMode(0, QW.QHeaderView.ResizeToContents)
        #view.header().setSectionResizeMode(1, QW.QHeaderView.ResizeToContents)
        view.setModel(model)
        view.setEditTriggers(QW.QAbstractItemView.NoEditTriggers)
        view.expanded.connect(lambda: view.resizeColumnToContents(0))
        view.collapsed.connect(lambda: view.resizeColumnToContents(0))
        view.clicked.connect(self.clicked)
        layout.addWidget(view)

    def set_events(self, events):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Event"])
        self.events = events
        root = self.model.invisibleRootItem()
        for typename, event_list in events.event_dict.iteritems():
            type_item = QG.QStandardItem(typename)
            type_item.setCheckable(True)
            root.appendRow(type_item)
            for i,ei in enumerate(event_list):
                event_item = QG.QStandardItem("{} id:{} s:{} loc:{},{}".\
                            format(i, ei.id, len(ei.pixel_events),
                                   int(ei.pixel_events[0].parameters['m2']),
                                   ei.pixel_events[0].pixel.y))
                self.items_by_name[typename].append(event_item)
                event_item.setCheckable(True)
                type_item.appendRow([event_item] )

    def toggle(self, name, state):
        name = str(name)
        if state:
            sstate = QC.Qt.Checked
        else:
            sstate = QC.Qt.Unchecked
        if name in self.items_by_name:
            items = self.items_by_name[name]
            for item in items:
                item.setCheckState(sstate)

    def clicked(self, modelindex):
        row = modelindex.row()
        parent = modelindex.parent()
        event_type = parent.data()#.toString())
        state = bool(modelindex.data(10))
        if event_type:
            self.events.change(event_type, row, state)
        else:
            #Toggle all events if the eventype has been toggled
            itemname = str(modelindex.data())#.toString())
            if itemname in self.items_by_name:
                self.events.change(itemname, None, state)
                self.toggle(itemname, state)
