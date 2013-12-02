from PyQt5 import QtWidgets as QW
import lsjuicer.inout.db.sqla as sa

class DeleteWidget(QW.QWidget):
    def __init__(self, event_ids, parent = None):
        super(DeleteWidget, self).__init__(parent)
        self.deleted=False
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        groupb = QW.QGroupBox("Events to delete")
        event_layout = QW.QVBoxLayout()
        groupb.setLayout(event_layout)
        self.groupb = groupb
        layout.addWidget(groupb)
        #self.buttongroup = QW.QButtonGroup()
        self.event_ids = event_ids

        self.session = sa.dbmaster.get_session()
        self.events = self.session.query(sa.Event).\
                filter(sa.Event.id.in_(self.event_ids)).all()

        for event in self.events:
            text = "{}: {} , size: {} px".format(event.category.category_type.name,
                    event.id, len(event.pixel_events))
            label = QW.QLabel(text)
            event_layout.addWidget(label)
        info_label = QW.QLabel("Events shown will be deleted!")
        layout.addWidget(info_label)
        self.info_label = info_label
        button_layout = QW.QHBoxLayout()
        button_layout.addStretch()
        close_pb = QW.QPushButton("Cancel")
        close_pb.clicked.connect(self.close)
        button_layout.addWidget(close_pb)
        do_pb = QW.QPushButton("Delete")
        do_pb.clicked.connect(self.delete)
        self.do_pb = do_pb
        button_layout.addWidget(do_pb)
        layout.addLayout(button_layout)

    def delete(self):
        for event in self.events:
            self.session.delete(event)
        self.session.commit()
        self.do_pb.setEnabled(False)
        self.info_label.setText("Delete successful!")
        self.deleted = True
        self.close()


    def closeEvent(self, event):
        self.session = None
        self.events = None
        self.event_ids = None
        if self.deleted:
            self.parent().accept()
        else:
            self.parent().reject()
        QW.QWidget.closeEvent(self, event)


class DeleteDialog(QW.QDialog):
    def __init__(self, events, parent=None):
        super(DeleteDialog, self).__init__(parent)
        layout = QW.QHBoxLayout()
        self.setLayout(layout)
        delete_widget =  DeleteWidget(events, self)
        layout.addWidget(delete_widget)

