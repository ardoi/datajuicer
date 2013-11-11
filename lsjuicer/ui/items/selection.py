from collections import defaultdict

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from roi import ROIItem
from boundary import BoundaryItem
from line import LineItem
from snaproi import SnapROIItem

from lsjuicer.util.helpers import round_point

class PickledSelection:
    def __init__(self, name, color):
        self.name = name
        self.color = color
    def get_selection(self):
        selection_appearance =  SelectionAppearance()
        selection_appearance.set_line_params('black',1)
        selection_appearance.set_active_line_params('red')
        selection_appearance.set_fill_params(self.color, is_gradient=True)
        selection_appearance.set_active_fill_params('orange')
        selection_type = SelectionType(self.name, selection_appearance, 1)
        return selection_type

class SelectionAppearance:
    def __init__(self):
        self.linecolor = None
        self.linestyle = None
        self.linewidth = None
        self.active_linecolor = None
        self.active_linestyle = None
        self.fillcolor = None
        self.is_gradient = False
        self.brush = None
        self.active_brush = None
        self.pen = None
        self.active_pen = None
        self.state_colors = {}
        self.state = 'normal'

    def set_line_params(self, colorname, linewidth, linestyle=QC.Qt.SolidLine):
        self.state_colors['normal']=colorname
        self.linecolor = QG.QColor(colorname)
        self.linestyle = linestyle
        self.linewidth = linewidth
        if colorname:
            self.pen = QG.QPen(self.linestyle)
            self.pen.setWidth(self.linewidth)
            self.pen.setColor(self.linecolor)
            self.pen.setCosmetic(True)
            self.pen.setJoinStyle(QC.Qt.MiterJoin)
        else:
            self.pen = QG.QPen(QC.Qt.NoPen)

    def set_active_line_params(self, colorname=None, linestyle=QC.Qt.DotLine):
        if colorname:
            self.active_linecolor = QG.QColor(colorname)
        else:
            self.active_linecolor = self.linecolor
        self.state_colors['active']=colorname
        self.active_linestyle = linestyle
        self.active_pen = QG.QPen(self.active_linestyle)
        self.active_pen.setWidth(self.linewidth)
        self.active_pen.setColor(self.active_linecolor)
        self.active_pen.setCosmetic(True)
        self.active_pen.setJoinStyle(QC.Qt.MiterJoin)

    def add_state_color(self, state, colorname):
        self.state_colors[state] = colorname

    def set_fill_params(self, fillcolorname, is_gradient=False, alpha = 1.0):
        self.fillcolor = QG.QColor(fillcolorname)
        self.fillcolor.setAlphaF(alpha)
        self.is_gradient = is_gradient

    def set_active_fill_params(self, active_fillcolorname, alpha = 1.0):
        self.active_fillcolor = QG.QColor(active_fillcolorname)
        self.active_fillcolor.setAlphaF(alpha)

    def get_brush(self, rect):
        if not self.brush:
            if self.is_gradient:
                brushColor =QG.QColor(self.fillcolor)
                brushColor.setAlphaF(0.4)
                brushColor2 =QG.QColor(self.fillcolor)
                brushColor2.setAlphaF(0.15)
                start =rect.topLeft()
                stop = rect.bottomLeft()
                gradient = QG.QLinearGradient(start, stop)
                gradient.setColorAt(0,brushColor)
                gradient.setColorAt(.25,brushColor2)
                gradient.setColorAt(.75,brushColor2)
                gradient.setColorAt(1,brushColor)
                #gradient.setSpread(QG.QGradient.ReflectSpread)
                self.brush = QG.QBrush(gradient)
            else:
                self.brush = QG.QBrush(self.fillcolor)
        return self.brush

    def get_active_brush(self, rect):
        if not self.active_brush:
            if self.is_gradient:
                brushColor =QG.QColor(self.active_fillcolor)
                brushColor.setAlphaF(0.4)
                brushColor2 =QG.QColor(self.active_fillcolor)
                brushColor2.setAlphaF(0.15)
                start =rect.topLeft()
                stop = rect.bottomLeft()
                gradient = QG.QLinearGradient(start, stop)
                gradient.setColorAt(0,brushColor)
                gradient.setColorAt(.25,brushColor2)
                gradient.setColorAt(.75,brushColor2)
                gradient.setColorAt(1,brushColor)
                #gradient.setSpread(QG.QGradient.ReflectSpread)
                self.active_brush = QG.QBrush(gradient)
            else:
                self.active_brush = QG.QBrush(self.active_fillcolor)
        return self.active_brush

class SelectionType:
    def __init__(self, selection_type_name, appearance, count):
        self.selection_type_name = selection_type_name
        self.name = self.selection_type_name
        self.appearance = appearance
        self.count = count

def make_icon(color):
    pixmap = QG.QPixmap(20,20)
    pixmap.fill(color)
    return QG.QIcon(pixmap)
class NewExperimentTypeWidget(QW.QWidget):

    cancel = QC.pyqtSignal()
    accept = QC.pyqtSignal()
    def __init__(self, model, parent = None):
        super(NewExperimentTypeWidget, self).__init__(parent)
        self.model = model
        self.valid_name = None
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        groupbox_new = QW.QGroupBox('Create new experiment type')
        new_layout = QW.QVBoxLayout()
        new_gb_layout = QW.QGridLayout()
        groupbox_new.setLayout(new_layout)
        layout.addWidget(groupbox_new)
        new_layout.addLayout(new_gb_layout)
        new_gb_layout.addWidget(QW.QLabel('Name:'), 0, 0)

        self.new_selection_name_lineedit = QW.QLineEdit()
        self.new_selection_name_lineedit.textChanged.connect(self.validate_new_selection)
        new_gb_layout.addWidget(self.new_selection_name_lineedit, 0, 1)

        self.status_label = QW.QLabel('<strong> Enter name for group</strong>')

        new_gb_layout.addWidget(self.status_label, 1, 1, QC.Qt.AlignRight)
        new_gb_layout.setSpacing(0)

        self.accept_pb = QW.QPushButton('Accept')
        self.accept_pb.clicked.connect(self.add_new_selection_type)
        self.accept_pb.setEnabled(False)
        self.accept_pb.setSizePolicy(QW.QSizePolicy.Maximum, QW.QSizePolicy.Maximum)

        self.cancel_pb = QW.QPushButton('Cancel')
        self.cancel_pb.clicked.connect(self.cancel_pb_clicked)

        button_layout = QW.QHBoxLayout()
        new_layout.addLayout(button_layout)
        button_layout.addWidget(self.accept_pb)
        button_layout.addWidget(self.cancel_pb)
        new_layout.setSpacing(0)

    def cancel_pb_clicked(self):
        print 'cancel'
        self.cancel.emit()

    def validate_new_selection(self, selection_name):
        if not selection_name:
            self.status_label.setText(' Please type in name')
            self.accept_pb.setEnabled(False)
            self.valid_name = False
            return
        if self.model.does_name_exist(selection_name):
            self.status_label.setText('<strong style="color:red;"> Name already exists!</strong>')
            self.accept_pb.setEnabled(False)
            self.valid_name = False
        else:
            self.status_label.setText('<strong style="color:green;"> OK</strong>')
            self.valid_name = selection_name
            self.accept_pb.setEnabled(True)


    def add_new_selection_type(self):
        self.model.add_new(self.valid_name)
        self.accept.emit()

class NewBoundaryWidget(QW.QWidget):

    cancel = QC.pyqtSignal()
    accept = QC.pyqtSignal()
    def __init__(self, model, parent = None):
        super(NewBoundaryWidget, self).__init__(parent)
        self.model = model
        self.new_color = None
        self.valid_name = None
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        groupbox_new = QW.QGroupBox('Create new group')
        new_layout = QW.QVBoxLayout()
        new_gb_layout = QW.QGridLayout()
        groupbox_new.setLayout(new_layout)
        layout.addWidget(groupbox_new)
        new_layout.addLayout(new_gb_layout)
        new_gb_layout.addWidget(QW.QLabel('Name:'), 0, 0)

        self.new_selection_name_lineedit = QW.QLineEdit()
        self.new_selection_name_lineedit.textChanged.connect(self.validate_new_selection)
        new_gb_layout.addWidget(self.new_selection_name_lineedit, 0, 1)

        self.status_label = QW.QLabel('<strong> Enter name for group</strong>')

        new_gb_layout.addWidget(QW.QLabel('Color:'), 2, 0)

        self.color_pb = QW.QToolButton()
        self.color_pb.setIcon(QG.QIcon('://color_wheel.png'))
        self.color_pb.clicked.connect(self.show_color_dialog)

        new_gb_layout.addWidget(self.color_pb, 2, 1)
        new_gb_layout.addWidget(self.status_label, 1, 1, QC.Qt.AlignRight)
        new_gb_layout.setSpacing(0)

        self.accept_pb = QW.QPushButton('Accept')
        self.accept_pb.clicked.connect(self.add_new_selection_type)
        self.accept_pb.setEnabled(False)
        self.accept_pb.setSizePolicy(QW.QSizePolicy.Maximum, QW.QSizePolicy.Maximum)

        self.cancel_pb = QW.QPushButton('Cancel')
        self.cancel_pb.clicked.connect(self.cancel_pb_clicked)

        button_layout = QW.QHBoxLayout()
        new_layout.addLayout(button_layout)
        button_layout.addWidget(self.accept_pb)
        button_layout.addWidget(self.cancel_pb)
        new_layout.setSpacing(0)

    def cancel_pb_clicked(self):
        print 'cancel'
        self.cancel.emit()

    def validate_new_selection(self, selection_name):
        if not selection_name:
            self.status_label.setText(' Please type in name')
            self.accept_pb.setEnabled(False)
            self.valid_name = False
            return
        if self.model.does_name_exist(selection_name):
            self.status_label.setText('<strong style="color:red;"> Name already exists!</strong>')
            self.accept_pb.setEnabled(False)
            self.valid_name = False
        else:
            self.status_label.setText('<strong style="color:green;"> OK</strong>')
            self.valid_name = selection_name
            if self.new_color:
                self.accept_pb.setEnabled(True)

    def show_color_dialog(self):
        #dialog = QG.QColorDialog()
        #dialog.open()
        color = QW.QColorDialog.getColor(parent=self)
        print color
        pixmap = QG.QPixmap(20,20)
        pixmap.fill(color)
        icon = QG.QIcon(pixmap)
        self.color_pb.setIcon(icon)
        self.new_color = color
        if self.valid_name:
            self.accept_pb.setEnabled(True)

    def add_new_selection_type(self):
        pickled_selection = PickledSelection(self.valid_name, self.new_color)
        selection_type = pickled_selection.get_selection()
        self.model.add_new(selection_type)
        self.accept.emit()


class SelectionSelectDialog(QW.QDialog):
    comboindex_set = QC.pyqtSignal(int)
    def comboindex_set_call(self, index):
        print 'call for index',index
        self.comboindex_set.emit(index)
    def __init__(self, selection_model, parent = None):
        super(SelectionSelectDialog, self).__init__(parent)
        self.model = selection_model
        self.new_color = None
        self.valid_name = False
        dialog_layout = QW.QVBoxLayout()
        self.setLayout(dialog_layout)
        self.combobox = QW.QComboBox()
        self.combobox.currentIndexChanged.connect(self.comboindex_set_call)
        self.groupbox_old = QW.QGroupBox('Choose existing group')
        groupbox_layout = QW.QHBoxLayout()
        dialog_layout.addLayout(groupbox_layout)
        groupbox_layout.addWidget(self.groupbox_old)
        old_gb_layout = QW.QVBoxLayout()
        old_gb_layout.addWidget(self.combobox)
        self.groupbox_old.setLayout(old_gb_layout)
        for selection_type in self.model.selection_manager.selection_types:
            if isinstance(self.model.selection_manager, ROIManager):
                icon = make_icon(selection_type.appearance.linecolor)
            elif isinstance(self.model.selection_manager, BoundaryManager):
                icon = make_icon(selection_type.appearance.fillcolor)
            else:
                icon = QG.QIcon()
            self.combobox.addItem(icon, selection_type.name)
        self.groupbox_new = QW.QGroupBox('Create new group')
        self.groupbox_new.setVisible(False)
        groupbox_layout.addWidget(self.groupbox_new)
        new_layout = QW.QVBoxLayout()

        new_gb_layout = QW.QGridLayout()
        self.groupbox_new.setLayout(new_layout)
        new_layout.addLayout(new_gb_layout)
        #new_b1_layout = QG.QHBoxLayout()
        #new_b2_layout = QG.QGridLayout()
        new_gb_layout.addWidget(QW.QLabel('Name:'),0,0)
        self.new_selection_name_lineedit = QW.QLineEdit()
        self.status_label = QW.QLabel('<strong> Enter name for group</strong>')

        #self.validator = NameValidator()
        #self.new_selection_name_lineedit.setValidator(self.validator)
        new_gb_layout.addWidget(self.new_selection_name_lineedit,0,1)
        #new_b1_layout.addWidget(self.status_label)
        new_gb_layout.addWidget(QW.QLabel('Color:'),2,0)
        self.color_pb = QW.QToolButton()
        self.color_pb.clicked.connect(self.show_color_dialog)
        #new_gb_layout.setAlignment(QC.Qt.AlignLeft)
        #self.color_pb.resize(20, 20)
        new_gb_layout.addWidget(self.color_pb,2,1)
        #new_gb_layout.addLayout(new_b1_layout)
        new_gb_layout.addWidget(self.status_label, 1, 1, QC.Qt.AlignRight)
        #new_gb_layout.setContentsMargins(0,0,0,0)
        new_gb_layout.setSpacing(0)
#        new_gb_layout.addLayout(new_b2_layout)
        self.accept_pb = QW.QPushButton('Accept')
        self.accept_pb.setEnabled(False)
        self.accept_pb.setSizePolicy(QW.QSizePolicy.Maximum, QW.QSizePolicy.Maximum)
#        self.new_selection_name_lineedit.editingFinished.connect(lambda:accept_pb.setEnabled(True))
        self.new_selection_name_lineedit.textChanged.connect(self.validate_new_selection)
        button_layout = QW.QHBoxLayout()
        new_layout.addLayout(button_layout)
        button_layout.addWidget(self.accept_pb)
        #button_layout.setAlignment(QC.Qt.AlignCenter)
        #button_layout.setContentsMargins(0,0,0,0)
        new_layout.setSpacing(0)
        #new_layout.setContentsMargins(0,0,0,0)
        self.accept_pb.clicked.connect(self.add_new_selection_type)

        self.button_box = QW.QDialogButtonBox(QW.QDialogButtonBox.Ok |
                QW.QDialogButtonBox.Cancel)
        new_type_pb = QW.QPushButton('Create new type')
        self.button_box.addButton(new_type_pb,
                QW.QDialogButtonBox.ActionRole)
        new_type_pb.clicked.connect(self.show_make_new)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        dialog_layout.addWidget(self.button_box)

    def accept(self):
        self.comboindex_set.emit(self.combobox.currentIndex())
        return QW.QDialog.accept(self)

    def add_new_selection_type(self):
        pickled_selection = PickledSelection(self.valid_name, self.new_color)
        selection_type = pickled_selection.get_selection()
        self.model.selection_manager.selection_types.append(selection_type)
        self.update_combo()
        self.show_old()
        #shelf_db = Config.get_property('shelf_db')
        #key = 'transienttab.groups'
        #if shelf_db.has_key(key):
        #    shelf_db[key].append(pickled_selection)
        #else:
        #    shelf_db[key] = [pickled_selection]

    def update_combo(self):
        self.combobox.clear()
        for selection_type in self.model.selection_manager.selection_types:
            if isinstance(self.model.selection_manager, ROIManager):
                icon = make_icon(selection_type.appearance.linecolor)
            elif isinstance(self.model.selection_manager, BoundaryManager):
                icon = make_icon(selection_type.appearance.fillcolor)
            else:
                icon = QG.QIcon()
            self.combobox.addItem(icon, selection_type.name)


    def show_make_new(self):
        self.groupbox_new.setVisible(True)
        self.button_box.setVisible(False)
        self.groupbox_old.setVisible(False)

    def show_old(self):
        self.groupbox_new.setVisible(False)
        self.button_box.setVisible(True)
        self.groupbox_old.setVisible(True)
        self.new_selection_name_lineedit.clear()
        self.new_color=None
        self.valid_name=None
        print 'selectedd',self.combobox.currentIndex()


class SelectionWidget(QW.QWidget):
    item_clicked = QC.pyqtSignal(QC.QModelIndex)
    def view_item_clicked(self, index):
        self.item_clicked.emit(index)
    def __init__(self, user_can_add_types = False, parent = None):
        super(SelectionWidget, self).__init__(parent)
        layout = QW.QVBoxLayout()
        self.user_can_add_types = user_can_add_types
        self.view = QW.QListView()
        self.view.setIconSize(QC.QSize(12,12))
        ff=self.view.font()
        #print '\n\n\nFONT',ff.family(), ff.bold(), ff.pixelSize(), ff.pointSize()
        #font = QG.QFont()
        #font.setFamily('sans')
        #font.setPointSize(10)
        #self.view.setFont(font)
        #ff=self.view.font()
        #print '\n\n\nFONT',ff.family(), ff.bold(), ff.pixelSize(), ff.pointSize()
        self.view.setSizePolicy(QW.QSizePolicy.Maximum, QW.QSizePolicy.Maximum)
        show_rows = 4
        row_height = 12
        gap = 3
        #self.view.setFixedHeight(show_rows*row_height+(show_rows-1)*gap)
        self.view.clicked.connect(self.view_item_clicked)
        #self.view.setSelectionMode(QG.QAbstractItemView.MultiSelection)
        self.setLayout(layout)
        layout.addWidget(self.view)
        toolbar = QW.QToolBar(self)
        self.add_action = toolbar.addAction(QG.QIcon(':/add.png'),'Add')
        delete_action = toolbar.addAction(QG.QIcon(':/delete.png'),'Delete')
        deselect_action = toolbar.addAction(QG.QIcon(':/shape_align_bottom.png'),'Deselect')
        button_layout = QW.QHBoxLayout()
        layout.addLayout(button_layout)
        self.add_action.setCheckable(True)
        self.add_action.triggered.connect(self.add_selection)
        delete_action.triggered.connect(self.remove_selection)
        #deselect_action.triggered.connect(self.view.clearSelection)
        deselect_action.triggered.connect(self.deselect)
        self.add_menu = QW.QMenu(toolbar)
        if not self.user_can_add_types:
            self.pb = QW.QComboBox(self)
            button_layout.addWidget(self.pb)
        else:
            self.pb = None
        button_layout.addWidget(toolbar)
        button_layout.setContentsMargins(0,0,0,0)
        self.layout().setContentsMargins(0,0,0,0)
        button_layout.setSpacing(0)
        toolbar.layout().setSpacing(0)
        toolbar.layout().setContentsMargins(0,0,0,0)
        self.model = None

    def deselect(self):
        self.view.setCurrentIndex(QC.QModelIndex())
        self.model.active_look(QC.QModelIndex())

    def set_model(self, model):
        if self.model is not None:
            self.view.clicked.disconnect(self.model.active_look)
        self.model = model
        self.view.setModel(model)
        if self.model.selection_manager:
            for selection_type in self.model.selection_manager.selection_types:
                if isinstance(self.model.selection_manager, ROIManager):
                    icon = make_icon(selection_type.appearance.linecolor)
                elif isinstance(self.model.selection_manager, BoundaryManager):
                    icon = make_icon(selection_type.appearance.fillcolor)
                else:
                    icon = QG.QIcon()
                if not self.user_can_add_types:
                    self.pb.addItem(icon, selection_type.name)
            self.model.selection_manager.ROI_available.connect(self.selection_selected)
        self.view.clicked.connect(self.model.active_look)
        if not self.user_can_add_types:
            self.pb.currentIndexChanged.connect(
                    lambda x:self.model.selection_manager.disable_builder())
        #self.layout().addWidget(SelectionSelectWidget(self.model))

    def selection_selected(self):
        self.add_action.setChecked(False)
        self.model.selection_manager.disable_builder()

    def remove_selection(self):
        selection = self.view.selectedIndexes()
        if selection:
            self.model.removeRows(selection)
        self.view.clearSelection()
        self.model.selection_manager.disable_builder()

    def activate_comboindex(self, index):
        print 'saving comboindex',index
        self.model.selection_manager.activate_builder(index)

    def add_selection(self):
        if self.user_can_add_types:
            self.dialog = SelectionSelectDialog(self.model, self)
            self.dialog.comboindex_set.connect(self.activate_comboindex)
            self.dialog.setModal(True)
            self.dialog.show()
 #           selection_index = self.comboindex
 #           print 'selected',selection_index
        else:
            selection_index = self.pb.currentIndex()
            self.activate_comboindex(selection_index)
#        self.model.selection_manager.activate_builder(selection_index)

    def set_index(self, index):
        self.view.setCurrentIndex(index)

class Selection(QC.QObject):
    """Generic selection"""
    selection_changed = QC.pyqtSignal()
    def set_name(self, name):
        self.name = name
    def __del__(self):
        print 'removing',self
        scene = self.graphic_item.scene()
        scene.removeItem(self.graphic_item)
        if hasattr(self, 'graphic_item'):
            del(self.graphic_item)
    def update_number(self, number):
        self.number = number
        self.graphic_item.number = number
    def set_state(self, state):
        self.graphic_item.set_state(state)

class Line(Selection):
    @property
    def name(self):
        r = self.graphic_item.line()
        n = self._name+": dx=%i dy=%i length=%i"%(abs(r.dx()), abs(r.dy()),r.length())
        return n
    def __init__(self, start_point, scene_rect, selection_type, number):
        super(Line, self).__init__(None)
        print 'making Line with', start_point, scene_rect
        end_point = start_point + QC.QPointF(1, 1)
        self.linef = QC.QLineF(start_point, end_point)
        self.selection_type = selection_type
        self.graphic_item  = LineItem(selection_type, number, parent=self.linef)
        self.graphic_item.sender.selection_changed.connect(self.selection_changed)
        #self.name = selection_type.name
        self._name = "Line"
        self.number = number

class ROI(Selection):
    """Selection with size in x and y"""
    def __init__(self, start_point, scene_rect, selection_type, number):
        print 'making ROI with', start_point, scene_rect
        super(ROI, self).__init__(None)
        if not start_point:
            self.rectf = scene_rect
        else:
            end_point = start_point + QC.QPointF(1, 1)
            self.rectf = QC.QRectF(start_point, end_point)
        self.selection_type=selection_type
        self.graphic_item  = ROIItem(selection_type, number, parent=self.rectf)
        self.graphic_item.sender.selection_changed.connect(self.selection_changed)
        self.name = selection_type.name
        self.number = number


class SnapROI(Selection):
    @property
    def name(self):
        r = self.graphic_item.rect()
        return self._name+": h=%i w=%i"%(r.height(), r.width())

    """Selection with size in x and y"""
    def __init__(self, start_point, scene_rect, selection_type, number, size=None):
        print 'making SnapROI with', start_point, scene_rect

        super(SnapROI, self).__init__(None)
        if not start_point:
            self.rectf = scene_rect
        else:
            round_point(start_point)
            end_point = start_point + QC.QPointF(1, 1)
            self.rectf = QC.QRectF(start_point, end_point)
        self.selection_type = selection_type
        self.graphic_item  = SnapROIItem(selection_type, number, parent=self.rectf,size=size)
        self.graphic_item.sender.selection_changed.connect(self.selection_changed)
        #self.name = selection_type.name
        #self.number = number
        self._name = "ROI"

class FixedSizeSnapROI(Selection):
    @property
    def name(self):
        r = self.graphic_item.rect()
        return self._name+": x=%i y=%i"%(r.left(), r.top())

    def __init__(self, start_point, scene_rect, selection_type, number):
        super(FixedSizeSnapROI, self).__init__(None)
        size = 1
        if not start_point:
            self.rectf = scene_rect
        else:
            round_point(start_point)
            end_point = start_point + QC.QPointF(size, size)
            self.rectf = QC.QRectF(start_point, end_point)
        self.selection_type = selection_type
        self.graphic_item  = SnapROIItem(selection_type, number, parent=self.rectf,size=size, update_on_release = True)
        self.graphic_item.sender.selection_changed.connect(self.selection_changed)
        self._name = "Pixel"


class Boundary(Selection):
    changed = QC.pyqtSignal()
    """Selection with max height and size in x"""
    def __init__(self, start_point, scene_rect, selection_type, number, parent = None):
        super(Boundary, self).__init__(parent)
        self.selection_type = selection_type
        start_point.setY(scene_rect.y())
        end_point = QC.QPointF(start_point.x(), scene_rect.bottom())
        self.rectf = QC.QRectF(start_point, end_point)
        self.graphic_item  = BoundaryItem(selection_type,self, self.rectf)
        self.graphic_item.sender.selection_changed.connect(self.selection_changed)
        self.name = selection_type.name
        #self.graphic_item.changed.connect(self.update_rect)
    def update_rect(self):
        self.rectf = self.graphic_item.rect()
        self.changed.emit()
    def set_visible(self, state):
        self.graphic_item.setVisible(state)
    def set_editable(self, state):
        self.graphic_item.setEditable(state)

class SelectionManager(QC.QObject):
    """Abstract selection manager"""
    def _active(self):
        return bool(self.builder)

    def _selections(self):
        out = []
        for builder in self.builders.values():
            for i,s in enumerate(builder.selections):
                #s.set_name("%s %i"%(builder.selection_type.name,i+1))
                #print 'setting name',"%s %i"%(builder.selection_type.name,i+1)
                #s.update_number(i+1)
                out.append(s)
        return out

    @property
    def selections_by_type(self):
        selections_by_type = defaultdict(list)
        for s in self.selections:
            selections_by_type[s.selection_type.selection_type_name].append(s)
        return selections_by_type

    active = property(fget = _active)
    selections = property(fget = _selections)
    selection_changed = QC.pyqtSignal(Selection)
    selection_added = QC.pyqtSignal()
    selection_update = QC.pyqtSignal()
    ROI_available = QC.pyqtSignal()
    def __init__(self, scene, selection_types, parent=None):
        super(SelectionManager, self).__init__(parent)
        #self.selections = []
        self.new_selections = []
        if selection_types:
            if isinstance(selection_types[0], PickledSelection):
                #if loading from shelf then actual selectiontypes have to be generated from the pickle data
                self.selection_types = [el.get_selection() for el in selection_types]
            else:
                self.selection_types = selection_types
        else:
            self.selection_types = []
        self.builder = None
        self.builders = {}
        self.scene = scene
        self.sub_init()
        self.builders_from_selection_types()

    def hide_selection(self, selection):
        for builder in self.builders.values():
            if selection in builder.selections:
                #builder.selections.remove(selection)
                selection.set_visible(False)

    def remove_selection(self, selection):
        print 'removes',selection
        for builder in self.builders.values():
            if selection in builder.selections:
                builder.selections.remove(selection)
                selection.__del__()
                break
        for builder in self.builders.values():
            for i,s in enumerate(builder.selections):
                s.update_number(i+1)
        return

    def builders_from_selection_types(self):
        for selection_type in self.selection_types:
            self.new_builder(selection_type)
        print self.builders

    def new_builder(self, selection_type):
        builder = SelectionBuilder(self.selection_class, self.scene, selection_type)
        self.builders[selection_type] = builder

    def activate_builder(self, selection_index):
        print 'activate',selection_index
        selection_type_name = self.selection_types[selection_index].selection_type_name
        self.activate_builder_by_type_name(selection_type_name)

    def activate_builder_by_type_name(self, selection_type_name):
        print "activate by name", selection_type_name
        print "types", self.selection_types
        for selection_type in self.selection_types:
            print "name",selection_type.selection_type_name
            if selection_type.selection_type_name == selection_type_name:
                self.builder = self.builders[selection_type]
                self.builder.activate()
                self.builder.selection_added.connect(self.sc)
                self.builder.selection_changed.connect(self.selection_changed)
                self.builder.selection_changed.connect(self.alert_selection_change)
                print "active builder", self.builder
                return
    def alert_selection_change(self, selection):
        self.selection_update.emit()
    def remove_selections(self):
        selections = self.selections
        for selection in selections:
            self.remove_selection(selection)

    def hide_selections(self):
        selections = self.selections
        for selection in selections:
            self.hide_selection(selection)

    def disable_builder(self):
        print 'disable', self.builder
        if self.builder:
            self.builder.disable()
            self.builder = None

    def sc(self):
        self.selection_added.emit()
        self.ROI_available.emit()

    def sub_init(self):
        pass

class LineManager(SelectionManager):
    def sub_init(self):
        self.selection_class = Line

class SnapROIManager(SelectionManager):
    def sub_init(self):
        self.selection_class = SnapROI

class FixedSizeSnapROIManager(SelectionManager):
    def sub_init(self):
        self.selection_class = FixedSizeSnapROI

class ROIManager(SelectionManager):
    def sub_init(self):
        self.selection_class = ROI

class BoundaryManager(SelectionManager):
    def sub_init(self):
        self.selection_class = Boundary

class SelectionDataModel(QC.QAbstractListModel):
    def __init__(self, parent=None):
        super(SelectionDataModel, self).__init__(parent)
        self.selection_manager = None

    def rowCount(self, parent):
        if self.selection_manager:
            rows= len(self.selection_manager.selections)
            return rows
        else:
            return 0
    def removeRows(self, index):
        self.layoutAboutToBeChanged.emit((),0)
        selections = self.selection_manager.selections
        for i in index:
            q=selections[i.row()]
            self.selection_manager.remove_selection(q)
        self.layoutChanged.emit((),0)

    def set_selection_manager(self, selection_manager):
        #self.modelAboutToBeReset.emit()
        self.beginResetModel()
        self.selection_manager = selection_manager
        self.selection_manager.selection_added.connect(self.modelReset)
        self.selection_manager.selection_update.connect(self.modelReset)
        self.endResetModel()
        #self.modelReset.emit()

    def active_look(self, index):
        print 'active look', self, index
        selections = self.selection_manager.selections
        for i,s in enumerate(selections):
            if i == index.row():
                #make item active in inactive and vice-versa
                s.graphic_item.make_look_active(not s.graphic_item.active)
            else:
                #deactivate everything else
                s.graphic_item.make_look_active(False)

    def data(self, index, role):
        selections = self.selection_manager.selections
        if role == QC.Qt.DisplayRole and self.selection_manager:
            try:
                return selections[index.row()].name
            except IndexError:
                print 'error @',index.row()
                return QC.QVariant()
        elif role == QC.Qt.DecorationRole:
            if isinstance(self.selection_manager, ROIManager):
                return selections[index.row()].selection_type.appearance.linecolor
            elif isinstance(self.selection_manager, BoundaryManager):
                try:
                    return selections[index.row()].selection_type.appearance.fillcolor
                except IndexError:
                    print index.row(), self.rowCount(None), selections
        else:
            return QC.QVariant()


class SelectionBuilder(QC.QObject):
    selection_added = QC.pyqtSignal()
    selection_changed = QC.pyqtSignal(Selection)
    def __init__(self, selection_class, graphics_scene, selection_type) :
        super(SelectionBuilder, self).__init__(None)
        self.selections = []
        self.maximum_to_select = selection_type.count
        self.selection_type = selection_type
        self.selection_class = selection_class
        self.scene = graphics_scene
        #self.activate()

    def make_selection_rect(self, start_point, scene_rect):
        if self.maximum_to_select == -1 or len(self.selections) < self.maximum_to_select:
            selection = self.selection_class(start_point, scene_rect,
                                             self.selection_type, len(self.selections)+1)
            selection.selection_changed.connect(self.send_selection_changed)
            self.scene.addItem(selection.graphic_item)
            #selection.graphic_item.setPos(selection.rectf.topLeft())
            self.selections.append(selection)
            self.selection_added.emit()

        else:
            return

    def activate(self):
        self.scene.set_selection_builder(self)

    def disable(self):
        self.scene.set_selection_builder(None)

    def send_selection_changed(self):
        sender = self.sender()
        self.selection_changed.emit(sender)


