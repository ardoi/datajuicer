from PyQt5 import QtWidgets as QW
import lsjuicer.inout.db.sqla as sa

class MergeWidget(QW.QWidget):
    def __init__(self, event_ids, parent = None):
        super(MergeWidget, self).__init__(parent)
        self.merged=False
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        groupb = QW.QGroupBox("Events to merge")
        event_layout = QW.QVBoxLayout()
        groupb.setLayout(event_layout)
        self.groupb = groupb
        layout.addWidget(groupb)
        self.buttongroup = QW.QButtonGroup()
        self.event_ids = event_ids

        self.session = sa.dbmaster.get_session()
        self.events = self.session.query(sa.Event).\
                filter(sa.Event.id.in_(self.event_ids)).all()

        for event in self.events:
            text = "{}: {} , size: {} px".format(event.category.category_type.name,
                    event.id, len(event.pixel_events))
            radiob = QW.QRadioButton(text)
            self.buttongroup.addButton(radiob)
            self.buttongroup.setId(radiob, event.id)
            event_layout.addWidget(radiob)
        info_label = QW.QLabel("Events will be merged to the selected event")
        layout.addWidget(info_label)
        self.info_label = info_label
        button_layout = QW.QHBoxLayout()
        button_layout.addStretch()
        close_pb = QW.QPushButton("Close")
        close_pb.clicked.connect(self.close)
        button_layout.addWidget(close_pb)
        do_pb = QW.QPushButton("Merge")
        do_pb.clicked.connect(self.merge)
        self.do_pb = do_pb
        button_layout.addWidget(do_pb)
        layout.addLayout(button_layout)

    def merge(self):
        parent_event_id = self.buttongroup.checkedId()
        if parent_event_id == -1:
            self.info_label.setText("Select the event to merge into")
            return
        parent_event = [ev for ev in self.events if \
                ev.id == parent_event_id][0]
        for event in self.events:
            if event.id == parent_event_id:
                continue
            else:
                pixel_events = event.pixel_events
                for pe in pixel_events:
                    pe.event = parent_event
                self.session.delete(event)
        self.session.commit()
        self.groupb.setEnabled(False)
        self.do_pb.setEnabled(False)
        self.info_label.setText("Merge successful!")
        self.merged = True


    def closeEvent(self, event):
        self.session = None
        self.events = None
        self.event_ids = None
        if self.merged:
            self.parent().accept()
        else:
            self.parent().reject()
        QW.QWidget.closeEvent(self, event)


class MergeDialog(QW.QDialog):
    def __init__(self, events, parent=None):
        super(MergeDialog, self).__init__(parent)
        layout = QW.QHBoxLayout()
        self.setLayout(layout)
        merge_widget =  MergeWidget(events, self)
        layout.addWidget(merge_widget)

