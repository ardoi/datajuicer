from PyQt5 import QtCore as QC


class EventFitParametersDataModel(QC.QAbstractTableModel):
    def __init__(self, parent=None):
        super(EventFitParametersDataModel, self).__init__(parent)
        self.rows = 0
        self.keys = ['A','d','tau2','s','m2','d2']
        self.columns = len(self.keys)
        self.events = []

    def set_events(self, res):
        self.modelAboutToBeReset.emit()
        self.events = res.pixel_events
        self.rows = res.event_count
        self.modelReset.emit()
        self.layoutChanged.emit()

    def rowCount(self, parent):
        return self.rows

    def columnCount(self, parent):
        return self.columns

    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section<6:
                    return self.keys[section]
                else:
                    return QC.QVariant()

            else:
                return section+1
        else:
            return QC.QVariant()

    def data(self, index, role):
        if role == QC.Qt.DisplayRole:
            row = index.row()
            event = self.events[row]
            col = index.column()
            #print event[self.keys[col]], self.keys[col]
            return "%.3f"%(event.parameters[self.keys[col]])
        else:
            return QC.QVariant()

