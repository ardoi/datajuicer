from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC



class CopyTableView(QW.QTableView):
    """QTableView that allows to copy data.
    Copied data in clipboard will be separated by newlines and commas"""
    items_selected = QC.pyqtSignal(bool)
    def copy(self):
        selected = self.selectedIndexes()
        out = {}
        for s in selected:
            if s.row() not in out.keys():
                out[s.row()]={}
            out[s.row()].update({s.column():str(s.data().toString())})
        keys = out.keys()
        print keys
        keys.sort()
        copyLines = []
        for k in keys:
            linekeys = out[k].keys()
            linekeys.sort()
            line = []
            for l in linekeys:
                line.append(out[k][l])
            copyLines.append(', '.join(line))
        #Add header names if 1st line in selection
        if 0 in keys:
            header_model = self.model()
            column_names = []
            column_count = header_model.columnCount(selected[0])
            for i in range(column_count):
                column_names.append(str(header_model.headerData(i, QC.Qt.Horizontal, QC.Qt.DisplayRole).toString()))
            copyLines.insert(0, ', '.join(column_names))
        outTxt = '\n'.join(copyLines)
        #print outTxt
        QW.QApplication.clipboard().setText(outTxt)
        #print QG.QApplication.clipboard().text()
        return

    def keyPressEvent(self, event):
        if bool(event.modifiers() & QC.Qt.ControlModifier) and event.key() == QC.Qt.Key_C:
            self.copy()
            return
        else:
            return QW.QTableView.keyPressEvent(self,event)

    def mousePressEvent(self, event):
        self.repaint()
        return QW.QTableView.mousePressEvent(self,event)

    def mouseReleaseEvent(self, event):
        self.repaint()
        res = QW.QTableView.mouseReleaseEvent(self, event)
        if self.selectedIndexes():
            self.items_selected.emit(True)
        else:
            self.items_selected.emit(False)
        return res
