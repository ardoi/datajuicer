from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC

from lsjuicer.ui.widgets.fileinfowidget import MyFormLikeLayout
from lsjuicer.ui.widgets.clicktrees import EventClickTree, Events
from actionpanel import ActionPanel
from lsjuicer.ui.widgets.mergewidget import MergeDialog
from lsjuicer.ui.widgets.deletewidget import DeleteDialog
from lsjuicer.data.analysis.transient_find import SyntheticData

class EventPanel(ActionPanel):
    __doc__ = """Event display panel"""
    __shortname__ = "Events"
    active_events_changed = QC.pyqtSignal()
    def setup_ui(self):

        layout = QW.QVBoxLayout()
        combo_layout = MyFormLikeLayout()
        layout.addLayout(combo_layout)
        self.setLayout(layout)
        self.events = None
        region_select = QW.QComboBox()
        for i,reg in enumerate(self.analysis.fitregions):
            region_select.addItem("{}".format(i))
        region_select.currentIndexChanged.connect(self.region_changed)
        combo_layout.add_row("Region:", region_select)
        result_select = QW.QComboBox()
        combo_layout.add_row("Result:", result_select)
        self.result_select = result_select
        result_select.currentIndexChanged.connect(self.result_changed)
        clicktree = EventClickTree(self)
        self.clicktree = clicktree
        layout.addWidget(clicktree)
        region_select.setCurrentIndex(0)
        self.region_changed(0)
        set_data_pb = QW.QPushButton("Set data")
        set_data_pb.clicked.connect(self.set_data)
        merge_pb = QW.QPushButton("Merge events")
        merge_pb.clicked.connect(self.merge_events)
        delete_pb = QW.QPushButton("Delete events")
        delete_pb.clicked.connect(self.delete_events)
        layout.addWidget(set_data_pb)
        layout.addWidget(merge_pb)
        layout.addWidget(delete_pb)

    def _selected_events(self):
        selected_events = []
        for event_type in self.events.event_dict:
            for i, event in enumerate(self.events.event_dict[event_type]):
                status = self.events.status_dict[event_type][i]
                if status:
                    selected_events.append(event.id)
        return selected_events

    def set_data(self):
        events_to_show = self._selected_events()
        sdata = SyntheticData(self.result)
        new = sdata.get_events(events_to_show)
        self.imagedata.replace_channel(new, 2)
        self.active_events_changed.emit()

    def merge_events(self):
        events_to_merge = self._selected_events()
        if len(events_to_merge) < 2:
            QW.QMessageBox.warning(self,'Not enough events',
                    "At least two events have to be selected for merging")
            return
        dialog = MergeDialog(events_to_merge,self)
        res = dialog.exec_()
        if res:
            self.result_changed(self.result_select.currentIndex())

    def delete_events(self):
        events_to_delete = self._selected_events()
        if len(events_to_delete) < 1:
            QW.QMessageBox.warning(self,'Not enough events',
                    "At least one event has to be selected for deletion")
            return
        dialog = DeleteDialog(events_to_delete,self)
        res = dialog.exec_()
        if res:
            self.result_changed(self.result_select.currentIndex())


    def region_changed(self, reg_no):
        print "\nREgion changed"
        self.region = self.analysis.fitregions[reg_no]
        self.result_select.clear()
        print reg_no, self.region
        for i,res in enumerate(self.region.results):
            self.result_select.addItem(str(i))

    def result_changed(self, res_no):
        print "\nResult changed"
        self.result = self.region.results[res_no]
        print res_no, self.result
        self.events = Events()
        for ev in self.result.events:
            self.events.add_event(ev)
        self.clicktree.set_events(self.events)


