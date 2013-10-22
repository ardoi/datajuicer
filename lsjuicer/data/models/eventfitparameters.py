from PyQt5 import QtCore as QC


class EventFitParametersDataModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super(EventFitParametersDataModel, self).__init__(parent)
        self.rows = 0
        self.keys = ['A','d','tau2','s','m2','d2']
        self.columns = len(self.keys)
        self.events = []

    def set_events(self, res):
        self.emit(QC.SIGNAL('modelAboutToBeReset()'))
        self.events = res.pixel_events
        self.rows = res.event_count
        self.emit(QC.SIGNAL('modelReset()'))
        self.emit(QC.SIGNAL('layoutChanged()'))

    def rowCount(self, parent):
        return self.rows

    def columnCount(self, parent):
        return self.columns

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section<6:
                    return self.keys[section]
                else:
                    return QtCore.QVariant()

            else:
                return section+1
        else:
            return QtCore.QVariant()

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            event = self.events[row]
            col = index.column()
            #print event[self.keys[col]], self.keys[col]
            return "%.3f"%(event.parameters[self.keys[col]])
        else:
            return QtCore.QVariant()

