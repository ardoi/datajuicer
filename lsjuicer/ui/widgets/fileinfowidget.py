from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.ui.plot.pixmapmaker import PixmapMaker
from lsjuicer.data.pipes.tools import PipeChain
from lsjuicer.ui.views import ZoomView
from lsjuicer.ui.widgets.smallwidgets import VisualizationOptionsWidget

from lsjuicer.inout.db.sqlbase import dbmaster
from lsjuicer.util import helpers
from lsjuicer.inout.db.sqla import MicroscopeImage, ExperimentalInfo
from lsjuicer.inout.db import sqla

from lsjuicer.ui.views.dataviews import CopyTableView


class FocusLineEdit(QW.QLineEdit):
    """QLineEdit extension that displays default text that is removed when user starts editing."""
    def focusInEvent(self, event):
        if str(self.text()) == self.default_text:
            self.setText("")
        QW.QLineEdit.focusInEvent(self, event)

    def focusOutEvent(self, event):
        if str(self.text()) == self.default_text or len(self.text())==0:
            self.set_default_text()
        QW.QLineEdit.focusOutEvent(self, event)

    def set_default_text(self, text=None):
        if text:
            self.default_text = text
        if self.default_text:
            self.setText(self.default_text)

    def get_text(self):
        if str(self.text()) == self.default_text:
            return ''
        else:
            return str(self.text())

    def set_text(self, text):
        self.set_default_text()
        if text:
            self.setText(text)


class AddSQLPropertyDialog(QW.QDialog):
    def __init__(self, db_class, parent = None):
        super(AddSQLPropertyDialog, self).__init__(parent)
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle("Add new %s type"%db_class.__name__)
        widget = AddSQLPropertyWidget(db_class, parent=self)
        layout.addWidget(widget)
        button_layout = QW.QHBoxLayout()
        close_pb = QW.QPushButton("Close")
        close_pb.clicked.connect(self.accept)
        button_layout.addWidget(close_pb)
        layout.addLayout(button_layout)


class AddSQLPropertyWidget(QW.QWidget):
    def __init__(self, db_class, parent = None):
        super(AddSQLPropertyWidget, self).__init__(parent)
        add_layout = QW.QVBoxLayout()
        self.setLayout(add_layout)
        self.db_class = db_class
        add_formlayout = QW.QFormLayout()
        name_lineedit = FocusLineEdit()
        name_lineedit.set_default_text("Name of %s"%self.db_class.__name__)
        self.name_lineedit = name_lineedit
        add_formlayout.addRow("Name:", name_lineedit)
        descr_lineedit = QW.QTextEdit()
        self.descr_lineedit = descr_lineedit
        #descr_lineedit.set
        add_formlayout.addRow("Description:", descr_lineedit)
        add_layout.addLayout(add_formlayout)
        status_label = QW.QLabel()
        add_layout.addWidget(status_label)
        self.status_label = status_label
        button_layout = QW.QHBoxLayout()
        add_layout.addLayout(button_layout)
        ok_pb = QW.QPushButton("Add")
        #cancel_pb = QG.QPushButton("Close")
        button_layout.addWidget(ok_pb)
        #button_layout.addWidget(cancel_pb)
        ok_pb.clicked.connect(self.add_item)

    def add_item(self):
        name = str(self.name_lineedit.get_text())
        description = str(self.descr_lineedit.toPlainText())
        if name:
            session = dbmaster.get_session()
            new_item = self.db_class()
            new_item.name = name
            if description:
                new_item.description = description
            session.add(new_item)
            self.status_label.setVisible(True)
            if dbmaster.commit_session():
                self.status_label.setText('<strong style="color:green;">OK:</strong> %s added'%name)
            else:
                self.status_label.setText('<strong style="color:red;"> Error:</strong> \
                        <span style="color:navy">%s</span> already exists'%name)
        else:
            self.status_label.setText('<strong style="color:red;">A name is required</strong>')

    def hide_status(self, state):
        self.status_label.setVisible(False)


class DBComboAddBox(QW.QWidget):
    """Combo box with an 'Add' button to add options"""
    def show_add_dialog(self):
        add_dialog = AddSQLPropertyDialog(self.db_class, parent = self)
        if add_dialog.exec_():
            self.combo.clear()
            self.populate_combobox()
            self.add_pb.setChecked(False)

    def __init__(self, db_class, show_None = True, parent = None):
        super(DBComboAddBox, self).__init__(parent)
        layout = QW.QVBoxLayout()
        field_layout = QW.QHBoxLayout()
        field_layout.setContentsMargins(0,0,0,0)
        layout.setContentsMargins(0,0,0,0)
        layout.addLayout(field_layout)
        self.setLayout(layout)
        self.db_class = db_class
        self.show_None = show_None

        combo = QW.QComboBox()
        add_pb = QW.QToolButton()
        add_pb.setIcon(QG.QIcon(':/add.png'))
        add_pb.setCheckable(True)
        add_pb.setAutoRaise(True)
        add_pb.setToolTip("Add a new %s type"%db_class.__name__)
        add_pb.clicked.connect(self.show_add_dialog)
        info_label = QW.QLabel()
        info_label.setPixmap(QG.QPixmap(":/information.png"))
        info_label.setToolTip(db_class.__doc__)
        info_label.setSizePolicy(QW.QSizePolicy.Maximum, QW.QSizePolicy.Maximum)

        self.add_pb = add_pb
        field_layout.addWidget(combo)
        field_layout.addWidget(info_label)
        field_layout.addWidget(add_pb)
        self.combo = combo
        self.populate_combobox()

    def populate_combobox(self):
        session = dbmaster.get_session()
        items = session.query(self.db_class).all()
        if self.show_None:
            self.combo.addItem("None")
        for item in items:
            self.combo.addItem(item.name)
        dbmaster.commit_session()

    def set_value(self, value):
        if value:
            text = value.name
        else:
            text = 'None'
        ind = self.combo.findText(text)
        if ind>-1:
            self.combo.setCurrentIndex(ind)

    def get_value(self):
        return str(self.combo.currentText())

class DBAttributeSpinBox(QW.QWidget):
    def __init__(self, attr, parent = None):
        super(QW.QWidget, self).__init__(parent)
        layout = QW.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        #field_layout = QG.QHBoxLayout()
        #layout.addLayout(field_layout)
        self.setLayout(layout)
        self.spin = QW.QSpinBox(self)
        self.spin.setMinimum(0)
        self.spin.setMaximum(500)
        self.spin.setSingleStep(1)
        layout.addWidget(self.spin)
        info_label = QW.QLabel()
        info_label.setPixmap(QG.QPixmap(":/information.png"))
        info_label.setToolTip(attr.__doc__)
        layout.addWidget(info_label)
        self.attr = attr

    def set_value(self, val):
        if val is None:
            val = 0
        self.spin.setValue(val)


    def get_value(self):
        val = self.spin.value()
        if val == 0:
            return None
        else:
            return val

class DBAttributeLineEdit(QW.QWidget):
    def __init__(self, attr, parent = None):
        super(QW.QWidget, self).__init__(parent)
        layout = QW.QHBoxLayout()
        #field_layout = QG.QHBoxLayout()
        #layout.addLayout(field_layout)
        self.setLayout(layout)
        self.lineedit = QW.QTextEdit(self)
        layout.addWidget(self.lineedit)
        info_label = QW.QLabel()
        info_label.setPixmap(QG.QPixmap(":/information.png"))
        info_label.setToolTip(attr.__doc__)
        layout.addWidget(info_label)
        self.attr = attr
        print 'str',str(attr),str(attr).split("."),dir(attr),attr.setter

    def set_value(self, val):
        if val is None:
            val = ""
        self.lineedit.setText(val)

    def get_value(self):
        return str(self.lineedit.toPlainText())


class ResultDataModel(QC.QAbstractTableModel):
    def __init__(self, parent=None):
        super(ResultDataModel, self).__init__(parent)
        self.columns = 9
        self.session = None
        self.results = None
        self.microscope_image = None

    def set_mimage(self, mimage):
        self.microscope_image = mimage
        self.update_results()

    def update_results(self):
        if self.microscope_image:
            #if self.session:
            #    dbmaster.end_session(self.session)
            #self.session = dbmaster.get_session()
            self.session = dbmaster.get_session()
            results = self.session.query(ExperimentalInfo).\
                    join(MicroscopeImage).filter(MicroscopeImage.id == self.microscope_image.id).all()
            print 'in rdm', results
            self.results = results
            self.data_update()

    def data_update(self):
        self.modelAboutToBeReset.emit()
        self.layoutAboutToBeChanged.emit((),0)
        self.modelReset.emit()
        self.layoutChanged.emit((),0)

    def rowCount(self, parent):
        if self.results:
            return len(self.results)
        else:
            return 0

    def columnCount(self, parent):
        return self.columns

    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section == 0:
                    return "Id"
                elif section == 1:
                    return "Project"
                elif section == 2:
                    return "Preparation"
                elif section==3:
                    return "Solution"
                elif section== 4:
                    return "Protocol"
                elif section == 5:
                    return "Sample"
                elif section==6:
                    return "Cell"
                elif section==7:
                    return "Analyses"
                elif section==8:
                    return "Comment"
            else:
                return section+1
        else:
            return QC.QVariant()

    def data(self, index, role):
        if role == QC.Qt.DisplayRole:
            col = index.column()
            row = index.row()
            res = self.results[row]
            na_string = "-"
            def ifname(val):
                if val:
                    return getattr(val, 'name')
                else:
                    return na_string
            def ifattr(name):
                val = getattr(res, name)
                if val:
                    return val
                else:
                    return na_string
            if col == 0:
                return res.id
            elif col == 1:
                return ifname(res.project)
            elif col == 2:
                return ifname(res.preparation)
            elif col == 3:
                return ifname(res.solution)
            elif col == 4:
                return ifname(res.protocol)
            elif col ==5:
                return ifattr("sample")
            elif col ==6:
                return ifattr("cell")
            elif col ==8:
                return " ".join(ifattr("comment").split('\n'))
        elif role==QC.Qt.TextAlignmentRole:
            return QC.Qt.AlignCenter
        else:
            return QC.QVariant()


    def get_selected(self, indexlist):
        print 'restable', indexlist
        ind = indexlist
        return self.results[ind.row()]

class AnalysesDataModel(QC.QAbstractTableModel):
    def __init__(self, parent=None):
        super(AnalysesDataModel, self).__init__(parent)
        self.columns = 4
        self.analyses = None

    def rowCount(self, parent):
        if self.analyses:
            return len(self.analyses)
        else:
            return 0

    def columnCount(self, parent):
        return self.columns

    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section == 0:
                    return "Type"
                elif section == 1:
                    return "Info"
                elif section == 2:
                    return "ID"
                elif section == 3:
                    return "Data"
            else:
                return section+1
        else:
            return QC.QVariant()

    def data(self, index, role):
        if role == QC.Qt.DisplayRole:
            col = index.column()
            row = index.row()
            res = self.analyses[row]
            #na_string = "-"
            if col == 0:
                return str(res.__class__.__tablename__)
            elif col == 1:
                return str(res)
            elif col == 2:
                return str(res.id)
            elif col == 3:
                fmt = '%Y-%m-%d %H:%M:%S'
                if res.date:
                    return res.date.strftime(fmt)
                else:
                    return QC.QVariant()
        elif role==QC.Qt.TextAlignmentRole:
            return QC.Qt.AlignCenter
        else:
            return QC.QVariant()

    def set_mimage(self, mimage):
        self.microscope_image = mimage
        self.update_results()

    def update_results(self):
        if self.microscope_image:
            self.analyses = self.microscope_image.analyses
            self.data_update()

    def clear(self):
        print "\n\nClearing!!"
        self.analyses = None
        self.data_update()

    def data_update(self):
        self.modelAboutToBeReset.emit()
        self.layoutAboutToBeChanged.emit((),0)
        self.modelReset.emit()
        self.layoutChanged.emit((),0)

    def get_selected(self, indexlist):
        ind = indexlist[0]
        print 'indices', ind
        return self.analyses[ind.row()]

class AnalysesInfoWidget(QW.QGroupBox):
    new_analysis = QC.pyqtSignal()
    load_analysis = QC.pyqtSignal(sqla.Analysis)

    def __init__(self, parent=None):
        super(AnalysesInfoWidget, self).__init__(parent)
        self.ui_setup()

    def ui_setup(self):
        layout = QW.QHBoxLayout()
        table_layout = QW.QVBoxLayout()
        layout.addLayout(table_layout)
        self.setLayout(layout)
        analyses_table = CopyTableView(self)
        analyses_model = AnalysesDataModel(self)
        analyses_table.setSelectionMode(QW.QAbstractItemView.SingleSelection)
        analyses_table.setSelectionBehavior(QW.QAbstractItemView.SelectRows)
        self.analyses_model = analyses_model
        self.analyses_table = analyses_table
        analyses_table.setModel(analyses_model)
        table_layout.addWidget(analyses_table)
        self.setTitle("Analyses")
        self.setSizePolicy(QW.QSizePolicy.Minimum, QW.QSizePolicy.Expanding)

        plot_pb = QW.QPushButton(QG.QIcon("://chart_curve_edit.png"),"New Analysis")
        load_pb = QW.QPushButton("Load")
        delete_pb = QW.QPushButton("Delete")
        #self.plot_pb.setVisible(False)
        plot_pb.setStyleSheet("""
            QPushButton {
                color: crimson;
                font-weight:bold;
            }""" )
        table_layout.addWidget(load_pb)
        table_layout.addWidget(delete_pb)
        table_layout.addWidget(plot_pb)
        load_pb.clicked.connect(self.get_analysis)
        delete_pb.clicked.connect(self.delete_analysis)
        plot_pb.clicked.connect(self.new_analysis)

    def get_analysis(self):
        ind = self.analyses_table.selectedIndexes()
        if ind:
            analysis = self.analyses_model.get_selected(ind)
            print "analysis to load", analysis
            self.load_analysis.emit(analysis)

    def delete_analysis(self):
        ind = self.analyses_table.selectedIndexes()
        if ind:
            analysis = self.analyses_model.get_selected(ind)
            session = dbmaster.get_session()
            print "analysis to delete", analysis
            regions = analysis.searchregions
            spark_count = 0
            region_count = 0
            for r in regions:
                sparks = r.sparks
                for spark in sparks:
                    session.delete(spark)
                    spark_count+=1
                region_count+=1
                session.delete(r)
            session.delete(analysis)
            message = "Are you sure you want to delete this analysis?\n%i regions with %i sparks will be removed"%(region_count, spark_count)
            res = QW.QMessageBox.question(self,'Confirm delete', message,
                    QW.QMessageBox.Yes|QW.QMessageBox.No)
            if res == QW.QMessageBox.Yes:
                print 'deleting'
                session.commit()
            else:
                session.rollback()
                print 'not deleting'

    def set_image(self, image):
        self.mimage = image
        self.analyses_model.set_mimage(image)

    def clear(self):
        self.analyses_model.clear()

class MyFormLikeLayout(QW.QVBoxLayout):
    def add_row(self, name, widget):
        row=QW.QHBoxLayout()
        #row.setContentsMargins(0,0,0,0)
        row.addWidget(QW.QLabel(name))
        if isinstance(widget, QW.QWidget):
            row.addWidget(widget)
        else:
            row.addLayout(widget)
        self.addLayout(row)

class ExpInfoWidget(QW.QGroupBox):
    update_results = QC.pyqtSignal()
    close = QC.pyqtSignal()
    #this is for quickly reusing the settings of the previous file
    exp_info_previous = None
    def __init__(self,  parent=None):
        super(ExpInfoWidget, self).__init__(parent)
        self.microscope_image = None
        self.exp_info = None
        self.ui_setup()

    def start_edit(self):
        self.setEnabled(True)
        self.exp_info = self.microscope_image.exp_info
        for combo in self.combos:
            prop_name = combo.db_class.__name__.lower()
            val = getattr(self.exp_info, prop_name)
            combo.set_value(val)

        for attr in self.spins + self.lines:
            val = attr.attr.fget(self.exp_info)
            attr.set_value(val)

    def reuse(self):
        print "reuse",ExpInfoWidget.exp_info_previous
        if ExpInfoWidget.exp_info_previous:
            for combo in self.combos:
                prop_name = combo.db_class.__name__.lower()
                val = getattr(self.exp_info_previous, prop_name)
                combo.set_value(val)

            for attr in self.spins + self.lines:
                val = attr.attr.fget(self.exp_info_previous)
                attr.set_value(val)

    def ui_setup(self):
        prop_layout = QW.QVBoxLayout()
        self.setLayout(prop_layout)
        form_layout = MyFormLikeLayout()
        form_layout.setSpacing(1)
        form_layout.setContentsMargins(0,0,0,0)
        prop_layout.addLayout(form_layout)
        self.setSizePolicy(QW.QSizePolicy.Maximum, QW.QSizePolicy.Maximum)


        button_layout = QW.QHBoxLayout()
        update_pb = QW.QPushButton(QG.QIcon('://database_go.png'),"Apply")
        reuse_pb = QW.QPushButton("Copy from last")
        close_pb = QW.QPushButton("Close")
        status_label = QW.QLabel('<html style="background:red;">Not saved</html>')
        self.status_label = status_label
        button_layout.addWidget(status_label)
        button_layout.addWidget(update_pb)
        button_layout.addWidget(reuse_pb)
        button_layout.addWidget(close_pb)
        prop_layout.addLayout(button_layout)
        update_pb.clicked.connect(self.save_exp_info)
        close_pb.clicked.connect(self.close)
        reuse_pb.clicked.connect(self.reuse)


        self.combos = []
        def add_dbprop_row(dbclass):
            combo = DBComboAddBox(dbclass)
            form_layout.add_row("%s:"%dbclass.__name__, combo)
            #form_layout.addWidget(combo)
            self.combos.append(combo)

        add_dbprop_row(sqla.Project)
        add_dbprop_row(sqla.Preparation)
        add_dbprop_row(sqla.Solution)
        add_dbprop_row(sqla.Protocol)

        self.spins = []
        spin1 = DBAttributeSpinBox(ExperimentalInfo.sample)
        form_layout.add_row("Sample:", spin1)
        #form_layout.addWidget(spin1)
        self.spins.append(spin1)
        spin2 = DBAttributeSpinBox(ExperimentalInfo.cell)
        form_layout.add_row("Cell:", spin2)
        #form_layout.addWidget(spin2)
        self.spins.append(spin2)

        self.lines = []
        line = DBAttributeLineEdit(ExperimentalInfo.comment)
        form_layout.add_row("Comment:",line)
        #orm_layout.addWidget(line)
        self.lines.append(line)
        self.setEnabled(False)
        self.setTitle("Experiment info")


    def save_exp_info(self):
        print '\nsave'
        if self.exp_info:
            session = dbmaster.get_session()
            for combo in self.combos:
                prop_name = combo.db_class.__name__.lower()
                val = combo.get_value()
                if val == 'None':
                    setattr(self.exp_info, prop_name, None)
                else:
                    prop_obj = session.query(combo.db_class).\
                            filter_by(name = val).one()
                    print '\n setting',self.exp_info, prop_name, prop_obj
                    setattr(self.exp_info, prop_name, prop_obj)
                    print 'prop', self.exp_info.project, self.exp_info._project
            #print self.spins, self.lines,self.spins+self.lines
            for attr in self.spins + self.lines:
                val = attr.get_value()
                print attr, val
                attr.attr.fset(self.exp_info, val)

            session.commit()
            self.status_label.setText('<html style="background:lime;">Saved</html>')
            ExpInfoWidget.exp_info_previous  = self.exp_info
            self.update_results.emit()



    #def add_new_exp_info(self):
    #    if self.microscope_image:
    #        session = dbmaster.object_session(self.microscope_image)
    #        exp_info = ExperimentalResult()
    #        exp_info._image = self.microscope_image
    #        session.add(exp_info)
    #        session.commit()
    #        self.res_model.update_results()
    #        self.exp_info = exp_info

    def set_image(self, microscope_image):
        print 'setting image', microscope_image
        self.microscope_image = microscope_image
        #self.res_model.set_mimage(microscope_image)

        self.start_edit()



class ReferencePlot(QW.QWidget):
    def __init__(self, parent = None):
        super(ReferencePlot, self).__init__(parent)
        layout = QW.QVBoxLayout()
        self.setLayout(layout)
        self.scene = QW.QGraphicsScene(self)
        #self.scene.addRect(QC.QRectF(0,0,100,100))
        self.view = ZoomView(self, locked = True)
        self.view.setScene(self.scene)
        self.pc = PipeChain()
        self.pixmaker = PixmapMaker(self.pc)
        self.image_shown = False
        self.vis_widget = None
        screen_rect = QW.QApplication.instance().desktop().screenGeometry()
        screen_width = screen_rect.width()
        if screen_width > 1500:
            self.view.setFixedSize(512, 512)
        else:
            self.view.setFixedSize(256, 256)
        layout.addWidget(self.view, QC.Qt.AlignTop)

        vis_options_pb = QW.QPushButton("Visualization properties")
        vis_options_pb.clicked.connect(self.show_vis_options_dialog)
        vis_options_pb.setIcon(QG.QIcon('://color_wheel.png'))
        layout.addWidget(vis_options_pb)
        layout.addStretch(5)

        self.g_pixmap = None
        self.g_roiline = None
        gt = self.scene.addText("No file selected")
        self.view.centerOn(gt)
        self.view.setFrameStyle(QW.QFrame.NoFrame)
        self.view.setRenderHint(QG.QPainter.Antialiasing)
        self.view.setTransformationAnchor(QW.QGraphicsView.AnchorUnderMouse)
        self.view.setMouseTracking(True)
        self.roi_pen = QG.QPen(QG.QColor('lime'))
        self.roi_pen.setCosmetic(True)
        self.roi_pen.setWidth(3)
        self.setSizePolicy(QW.QSizePolicy.Maximum, QW.QSizePolicy.Minimum)


    def set_pixmap(self, pixmap, view_reset):
        if view_reset:
            self.view.reset_zoom()
        if self.g_pixmap:
            self.scene.removeItem(self.g_pixmap)
        self.g_pixmap = self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(self.g_pixmap.boundingRect())
        #print self.g_pixmap.boundingRect()
        self.g_pixmap.setZValue(1)
        if view_reset:
            self.view.fitInView(self.g_pixmap)
        #self.view.fitInView(self.scene.sceneRect())

    def show_roi(self, roiline):
        print 'shwo roi', roiline
        self.clear_roi()
        self.g_roiline = self.scene.addLine(roiline, self.roi_pen)
        self.g_roiline.setZValue(2)

    def clear_roi(self):
        if self.g_roiline:
            self.scene.removeItem(self.g_roiline)

    @helpers.timeIt
    def make_new_pixmap(self, settings={}, viewreset=True, force=False):
        pixmaker = self.pixmaker
        QC.QTimer.singleShot(50,lambda :
                pixmaker.makeImage(force = force, image_settings=settings))
        QC.QTimer.singleShot(100,lambda :
                #self.image_widget.addPixmap(pixmaker.image, range(self.xvals),range(self.yvals))
                self.set_pixmap(pixmaker.pixmap, viewreset)
                )
        if self.roi_data:
            roi_data = self.roi_data
            #x and y and swapped from microscope
            roiline = QC.QLineF(roi_data["y1"],roi_data["x1"],
                roi_data["y2"], roi_data["x2"])
            QC.QTimer.singleShot(105,lambda : self.show_roi(roiline))
        else:
            self.clear_roi()
        self.image_shown = True

    def change_pixmap_settings(self, settings):
        self.make_new_pixmap(settings, viewreset = False)


    def set_image(self, microscope_image):
        reference_data = microscope_image.image_data("Reference")
        if reference_data is not None:
            try:
                reference_imdata = reference_data["ImageData"]
                roi_data = reference_data["ROI"]
                self.xvals,self.yvals = reference_imdata[0][0].shape
                self.pc.set_source_data(reference_imdata)
                self.pc.update_pixel_size(microscope_image.get_pixel_size("Reference"))
                if self.vis_widget:
                    self.vis_widget.update_pipechain(self.pc)
                    #self.vis_widget.do_histogram(self.pc)
                self.roi_data = roi_data
                self.make_new_pixmap(force=True)
            except:
                import traceback
                traceback.print_exc()
                pass

    def show_vis_options_dialog(self):
        dialog = QW.QDialog(self)
        layout = QW.QHBoxLayout()
        dialog.setLayout(layout)
        widget = VisualizationOptionsWidget(self.pc, parent=dialog)
        widget.settings_changed.connect(self.change_pixmap_settings)
        widget.close.connect(dialog.accept)
        layout.addWidget(widget)
        self.vis_widget = widget
        dialog.setModal(False)
        dialog.show()
        dialog.resize(400, 400)
        widget.do_histogram()
