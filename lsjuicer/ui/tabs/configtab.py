from PyQt5 import QtCore as QC

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW


from lsjuicer.ui.items.selection import NewBoundaryWidget,\
        NewExperimentTypeWidget,PickledSelection

from resources import cm

class ConfigTab(QW.QTabWidget):
    def __init__(self, parent = None):
        super(ConfigTab, self).__init__(parent)
        self.options_changed = {}

        envelop_layout = QW.QVBoxLayout()
        self.setLayout(envelop_layout)
        main_layout = QW.QGridLayout()
        #self.setLayout(main_layout)
        envelop_layout.addLayout(main_layout)
        self.save_pb = QW.QPushButton('Save')
        self.save_pb.setSizePolicy(QW.QSizePolicy.Maximum, QW.QSizePolicy.Maximum)
        self.save_pb.clicked.connect(self.save_settings)
        self.save_pb.setEnabled(False)
        envelop_layout.addWidget(self.save_pb)
        envelop_layout.addStretch()
        #conf_widget = QG.QWidget(self)
        #self.addTab(fl_conf_widget, 'Fluorescence calculation')
        #shelf_db = Config.get_property('shelf_db')

        #groups
        group_conf_groupbox = QW.QGroupBox('Transient groups')
        main_layout.addWidget(group_conf_groupbox,0,0)
        layout = QW.QHBoxLayout()
        group_conf_groupbox.setLayout(layout)
        self.boundary_listview = QW.QListView(group_conf_groupbox)
        layout.addWidget(self.boundary_listview)
        self.boundary_model = BoundaryDataModel(shelf_db)
        self.boundary_listview.setModel(self.boundary_model)
        buttonlayout = QW.QVBoxLayout()
        layout.addLayout(buttonlayout)
        layout.addStretch()
        edit_pb = QW.QPushButton('Edit',group_conf_groupbox)
        new_pb = QW.QPushButton('New', group_conf_groupbox)
        delete_pb = QW.QPushButton('Delete', group_conf_groupbox)
        delete_pb.clicked.connect(self.delete_item)
        new_pb.clicked.connect(self.add_item)
        buttonlayout.addWidget(edit_pb)
        buttonlayout.addWidget(new_pb)
        buttonlayout.addWidget(delete_pb)
        buttonlayout.addStretch()

        #Experiment types
        type_conf_typebox = QW.QGroupBox('Experiment types')
        main_layout.addWidget(type_conf_typebox,1,0)
        layout = QW.QHBoxLayout()
        type_conf_typebox.setLayout(layout)
        self.type_listview = QW.QListView(type_conf_typebox)
        layout.addWidget(self.type_listview)
        self.type_model = ExperimentTypeDataModel(shelf_db)
        self.type_listview.setModel(self.type_model)
        buttonlayout = QW.QVBoxLayout()
        layout.addLayout(buttonlayout)
        layout.addStretch()
        edit_pb = QW.QPushButton('Edit',type_conf_typebox)
        new_pb = QW.QPushButton('New', type_conf_typebox)
        delete_pb = QW.QPushButton('Delete', type_conf_typebox)
        delete_pb.clicked.connect(self.delete_type_item)
        new_pb.clicked.connect(self.add_type_item)
        buttonlayout.addWidget(edit_pb)
        buttonlayout.addWidget(new_pb)
        buttonlayout.addWidget(delete_pb)
        buttonlayout.addStretch()
        #visualization preferences

        #data from shelf
        vis_key = 'visualization'
        self.vis_conf = shelf_db[vis_key]

        vis_conf_groupbox = QW.QGroupBox('Default visualization settings')
        main_layout.addWidget(vis_conf_groupbox)
        layout = QW.QFormLayout()
        self.blur_spinbox = QW.QSpinBox(vis_conf_groupbox)
        self.blur_spinbox.setMaximum(10)
        self.blur_spinbox.setMinimum(0)
        self.blur_spinbox.setValue(self.vis_conf['blur'])
        self.blur_spinbox.valueChanged.connect(
                self.visualization_controls_moved)
        vis_conf_groupbox.setLayout(layout)
        layout.addRow('&Blur amount',self.blur_spinbox)

        self.saturation_spinbox = QW.QSpinBox(vis_conf_groupbox)
        self.saturation_spinbox.setMaximum(100)
        self.saturation_spinbox.setSingleStep(5)
        self.saturation_spinbox.setMinimum(1)
        self.saturation_spinbox.setValue(self.vis_conf['saturation'])
        self.saturation_spinbox.valueChanged.connect(
                self.visualization_controls_moved)
        layout.addRow('&Saturation',self.saturation_spinbox)

        self.colormap_combobox = QW.QComboBox(vis_conf_groupbox)
        self.colormaps = [name for name in cm.datad if not name.endswith("_r")]
        self.colormaps.sort()
        self.colormap_combobox.setIconSize(QC.QSize(100,20))
        for cm_name in self.colormaps:
            icon = QG.QIcon(QG.QPixmap(":/colormap_%s.png"%cm_name))
            self.colormap_combobox.addItem(icon, cm_name)
        self.colormap_combobox.setCurrentIndex(\
                self.colormaps.index(self.vis_conf['colormap']))
        self.colormap_combobox.currentIndexChanged.connect(
                self.visualization_controls_moved)
        layout.addRow('&Colormap',self.colormap_combobox)

        self.colormap_reverse_checkbox = QW.QCheckBox(vis_conf_groupbox)
        self.colormap_reverse_checkbox.setChecked(self.vis_conf['colormap_reverse'])
        self.colormap_reverse_checkbox.stateChanged.connect(
                self.visualization_controls_moved)
        layout.addRow('&Reverse colormap', self.colormap_reverse_checkbox)

        main_layout.setRowStretch(1,1)
        main_layout.setColumnStretch(2,1)

    def have_visualization_option_changed(self):
        """
        Check if visualization options are
        different from saved options
        """
        new_vis_conf = {'blur':self.blur_spinbox.value(),
                'saturation':self.saturation_spinbox.value(),
            'colormap':self.colormaps[self.colormap_combobox.currentIndex()],
            'colormap_reverse':self.colormap_reverse_checkbox.isChecked()}
        for key in self.vis_conf:
            if self.vis_conf[key] != new_vis_conf[key]:
                return True
        return False

    def visualization_controls_moved(self):
        """
        When a visualization control settings have changed
        initiate SAVE button state change
        """
        vis_key = 'visualization'
        self.options_changed[vis_key] = self.have_visualization_option_changed()
        self.save_pb_control()

    def save_pb_control(self):
        """
        Cycle through all config settings and enable
        save button if one or more settings have changed
        """
        print 'save_pb',self.options_changed
        for key in self.options_changed:
            if self.options_changed[key]:
                self.save_pb.setEnabled(True)
                return
        self.save_pb.setEnabled(False)

    def save_settings(self):
        vis_key = 'visualization'
        conf = {'blur':self.blur_spinbox.value(),
                'saturation':self.saturation_spinbox.value(),
            'colormap':self.colormaps[self.colormap_combobox.currentIndex()],
            'colormap_reverse':self.colormap_reverse_checkbox.isChecked()}
        #shelf_db = Config.get_property('shelf_db')
        #shelf_db[vis_key] = conf
        self.save_pb.setEnabled(False)


    def delete_item(self):
        self.boundary_model.removeRows(self.boundary_listview.selectedIndexes())

    def add_item(self):
        dialog = QW.QDialog(self)
        layout = QW.QHBoxLayout()
        dialog.setLayout(layout)
        new_boundary_widget = NewBoundaryWidget(self.boundary_model, dialog)
        layout.addWidget(new_boundary_widget)
        new_boundary_widget.accept.connect(dialog.accept)
        new_boundary_widget.cancel.connect(dialog.reject)
        dialog.setModal(True)
        dialog.show()

    def delete_type_item(self):
        self.type_model.removeRows(self.type_listview.selectedIndexes())

    def add_type_item(self):
        dialog = QW.QDialog(self)
        layout = QW.QHBoxLayout()
        dialog.setLayout(layout)
        new_et_widget = NewExperimentTypeWidget(self.type_model, dialog)
        layout.addWidget(new_et_widget)
        new_et_widget.accept.connect(dialog.accept)
        new_et_widget.cancel.connect(dialog.reject)
        dialog.setModal(True)
        dialog.show()

class ExperimentTypeDataModel(QC.QAbstractListModel):
    @property
    def experimenttypes(self):
        if self.shelf_db.has_key(self.key):
            types = self.shelf_db[self.key]
        else:
            types = []
        return types

    @experimenttypes.setter
    def experimenttypes(self, sts):
        self.shelf_db[self.key] = sts

    def __init__(self, shelf_db, parent=None):
        super(ExperimentTypeDataModel, self).__init__(parent)
        self.shelf_db = shelf_db
        self.key = 'experiment.types'

    def rowCount(self, parent):
        rows = len(self.experimenttypes)
        return rows

    def removeRows(self, index):
        self.layoutAboutToBeChanged.emit()
        ets = self.experimenttypes
        ets.remove(ets[index[0].row()])
        self.experimenttypes = ets
        self.layoutChanged.emit()

    def add_new(self, et):
        self.layoutAboutToBeChanged.emit()
        ets = self.experimenttypes
        ets.append(et)
        self.experimenttypes = ets
        self.layoutChanged.emit()

    def data(self, index, role):
        ets = self.experimenttypes
        if role == QC.Qt.DisplayRole:
            try:
                return ets[index.row()]
            except IndexError:
                print 'error @',index.row()
                return QC.QVariant()
        #elif role == QC.Qt.DecorationRole:
        #    return selections[index.row()].appearance.fillcolor
        else:
            return QC.QVariant()

    def does_name_exist(self, name):
       for sel in self.experimenttypes:
           if name == sel:
               return True
       else:
            return False

class BoundaryDataModel(QC.QAbstractListModel):

    def _get_selectiontypes(self):
        if self.shelf_db.has_key(self.key):
            types = [el.get_selection() for el in self.shelf_db[self.key]]
        else:
            types = []
        return types

    def _set_selectiontypes(self, sts):
        selections_to_pickle = []
        for sel in sts:
            pickled_selection = PickledSelection(sel.selection_type_name,
                    sel.appearance.fillcolor)
            selections_to_pickle.append(pickled_selection)
        self.shelf_db[self.key] = selections_to_pickle

    selectiontypes = property(fget = _get_selectiontypes,
            fset = _set_selectiontypes )

    def __init__(self, shelf_db, parent=None):
        super(BoundaryDataModel, self).__init__(parent)
        #self.shelf_db = shelf_db
        self.key = 'transienttab.groups'

    def rowCount(self, parent):
        rows = len(self.selectiontypes)
        return rows

    def removeRows(self, index):
        self.layoutAboutToBeChanged.emit()
        selections = self.selectiontypes
        print 'remove row',index[0].row()
        selections.remove(selections[index[0].row()])
        self.selectiontypes = selections
        self.layoutChanged.emit()

    def add_new(self, selection):
        self.layoutAboutToBeChanged.emit()
        selections = self.selectiontypes
        selections.append(selection)
        self.selectiontypes = selections
        self.layoutChanged.emit()


    def data(self, index, role):
        selections = self.selectiontypes
        if role == QC.Qt.DisplayRole:
            try:
                return selections[index.row()].name
            except IndexError:
                print 'error @',index.row()
                return QC.QVariant()
        elif role == QC.Qt.DecorationRole:
            return selections[index.row()].appearance.fillcolor
        else:
            return QC.QVariant()

    def does_name_exist(self, name):
       for sel in self.selectiontypes:
           if name == sel.name:
               return True
       else:
            return False
