import os
import traceback
import logging

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.util import helpers
from lsjuicer.static.constants import Constants
from lsjuicer.ui.widgets.analysiswidget import AnalysisWidget
from lsjuicer.ui.widgets.smallwidgets import Tasker
from lsjuicer.data.models.datamodels import MyFileSystemModel, RandomDataModel, MyProxyModel, MyFileIconProvider
from lsjuicer.ui.views.dataviews import CopyTableView

from lsjuicer.data.imagedata import ImageDataMaker

from lsjuicer.ui.widgets.fileinfowidget import ExpInfoWidget, ReferencePlot, AnalysesInfoWidget

class MainUI(QW.QMainWindow):

    newsignal = QC.pyqtSignal(QC.QModelIndex)

    def __init__(self, parent=None):
        super(MainUI, self).__init__(parent)
        self.version = 0.2
        #ch.start(8080)
        self.mode = Constants.SPARK_TYPE
        #self.setAttribute(QC.Qt.WA_DeleteOnClose)
        self.setupUi()
        #self.mode = None
        #versionCheck = VersionChecker(self.version)
        #versionCheck.checkVersion()

    def closeEvent(self, event):
        print "close"
        #self.rmodel.__del__()
        #print self.rmodel
        #print self.children()
        self.rmodel.deleteLater()
        from lsjuicer.inout.db.sqlbase import dbmaster
        dbmaster.end_session()

        QW.QMainWindow.closeEvent(self, event)

    def change_filetype(self, ftype):
        print 'setting ftype',ftype
        self.ftype = str(ftype).lower()
        self.fmodel.set_filetype(self.ftype)
        #Config.set_property('filetype', self.ftype)
        if self.ftype == "lsm":
            self.filetype_combo.setCurrentIndex(0)
        elif self.ftype == "tif":
            self.filetype_combo.setCurrentIndex(1)
        elif self.ftype == "oib":
            self.filetype_combo.setCurrentIndex(2)
        else:
            raise ValueError("wrong filetype %s"%self.ftype)
        index = self.fview.currentIndex()
        self.newsignal.emit(index)

    #def destroyed(self, obj):
    #    print 'destroy main', obj
    def destroy(self, a,b):
        print 'dd',a,b

    def setupUi(self):
#        self.h = hpy()
#        self.h.setrelheap()
        self.setWindowTitle('LSJuicer')

        #actions & menus
        self.menu = self.menuBar()
        self.setWindowIcon(QG.QIcon(QG.QPixmap(":/juicerlogo_icon.png")))

        #actionIcon = QG.QIcon(':/film_go.png')
        #self.actionNew = QG.QAction(actionIcon,'New',self)

        analysisToolbar = self.addToolBar('Analysis')
        analysisToolbar.setVisible(False)
        fileToolbar = self.addToolBar('File')
        confToolbar = self.addToolBar('Configuration')
        focusToolbar = self.addToolBar('Focus')
        analysisToolbar.setMovable(False)
        fileToolbar.setMovable(False)
        focusToolbar.setMovable(False)
        confToolbar.setMovable(False)
        focusToolbar.setContextMenuPolicy(QC.Qt.PreventContextMenu)
        fileToolbar.setContextMenuPolicy(QC.Qt.PreventContextMenu)
        analysisToolbar.setContextMenuPolicy(QC.Qt.PreventContextMenu)

        analysisToolbar.setToolButtonStyle(QC.Qt.ToolButtonTextBesideIcon)
        fileToolbar.setToolButtonStyle(QC.Qt.ToolButtonTextBesideIcon)

        #fileToolbar.addAction(self.actionNew)

        #actionAppendIcon = QG.QIcon(':/film_add.png')
        #self.actionAppend = QG.QAction(actionAppendIcon,'Append',self)
        #fileToolbar.addAction(self.actionAppend)
        #self.actionAppend.setEnabled(False)

        #actionSaveIcon = QG.QIcon(':/picture_save.png')
        #self.actionSave = QG.QAction(actionSaveIcon,'Save image',self)
        #analysisToolbar.addAction(self.actionSave)
        #self.actionSave.setEnabled(False)
        actionSaveDataIcon = QG.QIcon(':/report_disk.png')
        self.actionSaveData = QW.QAction(actionSaveDataIcon,'Save data',self)
        #analysisToolbar.addAction(self.actionSaveData)
        self.actionSaveData.setEnabled(False)

        #actionSaveAllIcon = QG.QIcon(':/disk_multiple.png')
        #self.actionSaveAll = QG.QAction(actionSaveAllIcon,'Save all',self)
        #analysisToolbar.addAction(self.actionSaveAll)
        #self.actionSaveAll.setEnabled(False)

        #actionInfoIcon = QG.QIcon(':/report.png')
        #self.actionInfo = QG.QAction(actionInfoIcon,'LSM info',self)
        #analysisToolbar.addAction(self.actionInfo)
        #self.actionInfo.setEnabled(False)

        actionHelpIcon = QG.QIcon(':/help.png')
        self.actionHelp = QW.QAction(actionHelpIcon,'Help',self)
        analysisToolbar.addAction(self.actionHelp)

        actionLogIcon = QG.QIcon(':/book_open.png')
        self.actionLog = QW.QAction(actionLogIcon,'Log',self)
        fileToolbar.addAction(self.actionLog)

        #spacer1 = QG.QWidget()
        #spacer1.setSizePolicy(QG.QSizePolicy.Expanding, QG.QSizePolicy.Expanding)
        spacer2 = QW.QWidget()
        spacer2.setSizePolicy(QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding)
        #analysisToolbar.addWidget(spacer1)
        self.tasker = Tasker()
        focusToolbar.addWidget(spacer2)
        focusToolbar.addWidget(self.tasker)
        self.tasker.analysisButton.toggled[bool].connect(analysisToolbar.setVisible)
        self.tasker.filesButton.toggled[bool].connect(fileToolbar.setVisible)
        self.tasker.confButton.toggled[bool].connect(confToolbar.setVisible)
        #focusFiles = QG.QAction('Files',self)
        #focusAnalysis = QG.QAction('Analysis',self)
        #focusConf = QG.QAction('Configuration',self)
        #focusFiles.setCheckable(True)
        #focusAnalysis.setCheckable(True)
        #focusConf.setCheckable(True)
        #focusGroup = QG.QActionGroup(self)
        #focusGroup.setExclusive(True)
        #focusGroup.addAction(focusFiles)
        #focusGroup.addAction(focusAnalysis)
        #focusGroup.addAction(focusConf)
        #testToolbar.addAction(focusFiles)
        #testToolbar.addAction(focusAnalysis)
        #testToolbar.addAction(focusConf)

        self.status = self.statusBar()
        #status_widget = QG.QWidget()
        #layout=QG.QHBoxLayout()
        #status_label = QG.QLabel("<b>QQ</b>")

        #layout.addWidget(status_label)
        #layout.addStretch()
        #status_widget.setLayout(layout)
        #self.status.addPermanentWidget(status_widget)
        #self.status.addPermanentWidget(QG.QSpacerItem(10,10))
        #Config.set_property('status_bar', self.status)
        self.status.showMessage('ok')

        self.mainStack = QW.QStackedWidget()
        self.setCentralWidget(self.mainStack)

        ####
        #tabs
        self.tabs = QW.QTabWidget()
        #self.tabs.setTabPosition(QG.QTabWidget.North)
        self.nameLabel = QW.QLabel()
        self.nameLabel.setEnabled(False)
        self.tabs.setCornerWidget(self.nameLabel)


        ###
        #folder/file picking tab
        self.filePickerTab = QW.QTabWidget()
        #self.filePickerTab.setTabPosition(QG.QTabWidget.North)
        #self.filePickerTab.setStyleSheet("""
        #QTabWidget::tab-bar{
        #    alignment: right;
        #}
        #""")

        ##
        #folder pick
        self.fmodel = MyFileSystemModel(self)
        icon_provider = MyFileIconProvider()
        self.fmodel.setIconProvider(icon_provider)
        #self.fview = QG.QColumnView()
        self.fview = QW.QTreeView(self)
        self.fview.setModel(self.fmodel)
        self.fview.setSelectionMode(QW.QAbstractItemView.SingleSelection)
        self.fview.setSelectionBehavior(QW.QAbstractItemView.SelectRows)
        self.fview.header().setSectionResizeMode(0, QW.QHeaderView.ResizeToContents)
        fselectLayout = QW.QHBoxLayout()
        fselectLayout.addWidget(self.fview)

        #
        #inspection progress and button
        inspect_layout = QW.QVBoxLayout()
        inspect_layout.addWidget(QW.QLabel('<b>File type:</b>'))
        filetype_combo = QW.QComboBox(self)
        inspect_layout.addWidget(filetype_combo)
        filetype_combo.addItem('LSM')
        #filetype_combo.addItem('CSV')
        filetype_combo.addItem('TIF')
        filetype_combo.addItem('OIB')
        filetype_combo.currentIndexChanged[str].connect(self.change_filetype)
        self.filetype_combo = filetype_combo
        frame = QW.QFrame(self)
        frame.setFrameStyle(QW.QFrame.HLine)
        frame.setFrameShadow(QW.QFrame.Sunken)
        inspect_layout.addWidget(frame)
        self.inspect_pb = QW.QPushButton('Inspect')
        inspect_layout.setAlignment(self.inspect_pb, QC.Qt.AlignCenter)
        self.inspect_pb.setSizePolicy(QW.QSizePolicy.Maximum,QW.QSizePolicy.Maximum)
        self.inspect_pb.setEnabled(False)
        inspect_layout.addWidget(self.inspect_pb)
        inspect_layout.addStretch()
        if 1:
            self.inspect_progressbar = QW.QProgressBar()
            self.inspect_progressbar.setFormat("%p% - %v out of %m files done")
            self.inspect_progressbar.setVisible(False)
            inspect_layout.addWidget(self.inspect_progressbar)

        fselectLayout.addLayout(inspect_layout)
        fselectWidget = QW.QWidget()
        fselectWidget.setLayout(fselectLayout)
        self.filePickerTab.addTab(fselectWidget,QG.QIcon(':/folder_table.png'),'Folder selection')

        #
        #file pick
        #splitter = QG.QSplitter(QC.Qt.Vertical)
        file_pick_widget = QW.QWidget()
        file_pick_layout = QW.QVBoxLayout()
        #file_pick_layout.setContentsMargins(0,0,0,0)
        file_pick_widget.setLayout(file_pick_layout)
        file_action_layout = QW.QVBoxLayout()
        file_action_layout.setContentsMargins(0,0,0,0)
        convert_progress_widget = QW.QWidget()
        convert_progress_layout = QW.QVBoxLayout()
        convert_progress_layout.setContentsMargins(0,0,0,0)
        convert_progress_widget.setLayout(convert_progress_layout)
        self.convert_progressbar = QW.QProgressBar()
        self.convert_progressbar.setFormat("%p% - %v out of %m files done")
        self.convert_progressbar.setMinimum(0)
        busy_bar = QW.QProgressBar()
        busy_bar.setMinimum(0)
        busy_bar.setMaximum(0)
        convert_progress_layout.addWidget(self.convert_progressbar)
        convert_progress_layout.addWidget(busy_bar)
        self.file_in_progress_label = QW.QLabel()
        convert_progress_layout.addWidget(self.file_in_progress_label)
        file_action_layout.addWidget(convert_progress_widget)
        convert_progress_widget.setVisible(False)

        pb_widget = QW.QWidget()
        pb_layout = QW.QHBoxLayout()
        pb_layout.setContentsMargins(0,0,0,0)
        pb_widget.setLayout(pb_layout)
        self.convert_pb = QW.QPushButton('Convert')
        self.convert_pb.setVisible(False)
        recheck_pb = QW.QPushButton("Recheck files")
        pb_layout.addStretch()
        pb_layout.addWidget(self.convert_pb)
        pb_layout.addWidget(recheck_pb)
        recheck_pb.clicked.connect(self.recheck_from_files)
        pb_widget.setSizePolicy(QW.QSizePolicy.Maximum,QW.QSizePolicy.Maximum)
        file_action_layout.addWidget(pb_widget)
        file_action_layout.setAlignment(pb_widget, QC.Qt.AlignCenter)

        location_layout = QW.QHBoxLayout()
        location_layout.setContentsMargins(0,0,0,0)
        self.location_label = QW.QLabel("Location: None")
        self.location_icon = QW.QLabel()
        location_layout.addWidget(self.location_icon)
        location_layout.addWidget(self.location_label)
        turn_left_icon = QG.QPixmap(":/arrow_turn_left.png")
        rotate_transform = QG.QTransform().rotate(90)
        turn_left_icon_rotated = turn_left_icon.transformed(rotate_transform)
        self.location_icon.setPixmap(turn_left_icon_rotated)
        self.location_label.setVisible(True)
        location_layout.addStretch()
        file_action_layout.addLayout(location_layout)

        #if os.name =="posix":
        #    username = os.environ['USER']
        #    rootdir = '/home/%s'%username
        #else:
        #    rootdir = "C:"
        rootdir = os.getenv('HOME')
        self.fmodel.setRootPath(rootdir)
        #fmodel.setNameFilters(strList([str("*.lsm"),str("*.ome")]))
        #self.fmodel.setNameFilters(strList([str("*.lsm")]))
        #ftype = Config.get_property('filetype')
        ftype ="tif"
        print 'ftype is %s'%ftype
        self.change_filetype(ftype)
        #self.fmodel.setNameFilters(strList([str("*.%s"%ftype)]))
#        fmodel.setNameFilters(str("*.lsm *.ome"))
        self.fmodel.setNameFilterDisables(False)
        self.fview.setRootIndex(self.fmodel.index(rootdir))
        #fmodel.setFilter(QC.QDir.Dirs | QC.QDir.NoDotAndDotDot | QC.QDir.AllDirs)
        #fmodel.setFilter(QC.QDir.NoDotAndDotDot | QC.QDir.AllDirs)
        #fview.setAnimated(True)
        #fview.header().hideSection(1)
        #fview.setSortingEnabled(True)

        rmodel =  RandomDataModel(self)
        self.rmodel = rmodel
        self.proxymodel = MyProxyModel(self)
        self.proxymodel.setSourceModel(rmodel)
        #self.proxymodel.setDynamicSortFilter(True)
        #inspect slot/signals
        self.fmodel.inspect_visible[bool].connect(self.inspect_pb.setEnabled)
        self.fmodel.inspect_needed[int].connect(self.set_inspectpb_text)
        rmodel.filesRead[int].connect(self.inspect_progressbar.setValue)
        rmodel.totalFiles[int].connect(self.inspect_progressbar.setMaximum)
        rmodel.progressVisible[bool].connect(self.inspect_progressbar.setVisible)
        #self.connect(rmodel, QC.SIGNAL('switchToFileSelection()'), lambda:self.filePickerTab.setTabEnabled(1,True))
        self.rmodel.switchToFileSelection.connect(self.switch_to_folder_content)
        #self.connect(sort_pb, QC.SIGNAL('clicked()'), lambda:self.dosort())


        rmodel.conversion_needed[int].connect(self.set_conversion_needed)
        self.convert_pb.clicked[()].connect(rmodel.convert)

        rmodel.omexml_maker.set_file_being_inspected_label[str].connect(self.set_file_being_inspected_label)
        rmodel.omexml_maker.filesConverted[int].connect(self.converted)
        rmodel.convert_progress_visible[bool].connect(convert_progress_widget.setVisible)
        rmodel.convert_pb_visible[bool].connect(self.convert_pb.setVisible)
        rmodel.conversion_finished.connect(lambda:convert_progress_widget.setVisible(False))

        self.fmodel.setTarget(rmodel)

        #self.tview = CopyTableView()
        self.tview = QW.QTableView()
        self.tview.setAlternatingRowColors(True)
        self.tview.setSelectionMode(QW.QAbstractItemView.SingleSelection)
        self.tview.setSelectionBehavior(QW.QAbstractItemView.SelectRows)
        self.tview.setModel(self.proxymodel)
        self.tview.horizontalHeader().setSectionResizeMode(QW.QHeaderView.ResizeToContents)
        self.tview.horizontalHeader().setSectionResizeMode(15, QW.QHeaderView.Stretch)
        #self.connect(rmodel,QC.SIGNAL('fitColumns()'),self.tview.resizeRowsToContents)
        rmodel.fitColumns.connect(self.tview.resizeRowsToContents)
        file_table_and_reference_layout = QW.QHBoxLayout()
        file_pick_layout.addLayout(file_table_and_reference_layout)
        file_table_and_reference_layout.addWidget(self.tview)
        file_pick_layout.addLayout(file_action_layout)
        #infogroup = QG.QGroupBox("Experiment Info")
        expinfo_pb = QW.QPushButton("Change info")
        expinfo_pb.clicked.connect(self.expinfo_pb_clicked)
        expinfo_pb.setEnabled(False)
        self.expinfo_pb = expinfo_pb

        analyses_widget = AnalysesInfoWidget()

        #infolayout=QG.QVBoxLayout()
        #infogroup.setLayout(infolayout)
        #infolayout.addWidget(expinfo_widget)
        reference_plot_widget = ReferencePlot(self)
        file_table_and_reference_layout.addWidget(reference_plot_widget)
        self.analyses_widget = analyses_widget
        self.reference_plot_widget = reference_plot_widget


        edit_and_analyze_layout = QW.QHBoxLayout()
        file_pick_layout.addLayout(edit_and_analyze_layout)
        edit_and_analyze_layout.addWidget(expinfo_pb)
        edit_and_analyze_layout.addWidget(analyses_widget)
        edit_and_analyze_layout.addStretch()

        #self.plot_pb = QG.QPushButton('Analyze')
        #self.plot_pb.setVisible(False)
        #edit_and_analyze_layout.addWidget(self.plot_pb)
        #splitter.setStretchFactor(0,2)
        #splitter.setStretchFactor(1,3)
        self.filePickerTab.addTab(file_pick_widget,QG.QIcon(':/application_view_list.png'), 'File selection')
        #self.filePickerTab.setTabEnabled(1,False)
        self.tview.setSortingEnabled(True)

        self.proxymodel.setView(self.tview)

        self.fview.clicked.connect(self.new_file_selection)
        self.newsignal.connect(self.fmodel.checkFiles)
        self.inspect_pb.clicked.connect(self.do_inspect)
        self.analyses_widget.new_analysis.connect(self.start_new_analysis)
        self.analyses_widget.load_analysis.connect(self.start_plot_with_analysis)
        self.tview.doubleClicked[QC.QModelIndex].connect(self.start_new_analysis)
        self.tview.clicked[QC.QModelIndex].connect(self.start_show_reference)
        #self.connect(self.tview, QC.SIGNAL('clicked(QModelIndex)'), self.enable_display_pb)
        #self.tview.items_selected.connect(self.plot_pb.setVisible)
        #self.connect(self.tview,QC.SIGNAL('pressed(QModelIndex)'), self.enable_display_pb)
        #self.connect(self.tview,QC.SIGNAL('selectionChanged(QModelIndex, QModelIndex)'), self.tview_selection_changed)
        #self.tview.itemSelectionChanged.connect(self.tview_selection_changed)
        self.proxymodel.doPlot[object].connect(rmodel.plot)
        rmodel.plotFile[object].connect(self.open_file)
        self.rmodel = rmodel
        self.tasker.analysisButton.toggled[bool].connect(lambda:self.mainStack.setCurrentIndex(1))
        self.tasker.confButton.toggled[bool].connect(lambda:self.mainStack.setCurrentIndex(2))
        self.tasker.filesButton.toggled[bool].connect(lambda:self.mainStack.setCurrentIndex(0))
        self.mainStack.addWidget(self.filePickerTab)
        self.mainStack.addWidget(AnalysisWidget(parent=self))
        self.actionSaveData.triggered[()].connect(self.on_actionSaveData_triggered)
        self.actionHelp.triggered[()].connect(self.on_actionHelp_triggered)
        self.actionLog.triggered[()].connect(self.on_actionLog_triggered)

    def recheck_from_files(self):
        self.rmodel.recheck_images()

    def switch_to_folder_content(self, folder_name):
        self.filePickerTab.setCurrentIndex(1)
        self.location_label.setText('Location: <b>%s</b>'%folder_name)
        QC.QTimer.singleShot(0,self.dosort)

    def expinfo_pb_clicked(self):
        expinfo_widget = ExpInfoWidget(self)
        expinfo_widget.update_results.connect(self.db_data_update)
        expinfo_widget.set_image(self.active_image)
        qh = QW.QDialog(self)
        expinfo_widget.close.connect(qh.accept)
        layout = QW.QHBoxLayout(qh)
        layout.addWidget(expinfo_widget)
        qh.setWindowTitle('Change experimental info')
        #qh.setFixedWidth(450)
        #qh.setFixedHeight(300)
        qh.setLayout(layout)
        #self.qh.show()
        if qh.exec_():
            expinfo_widget.update_results.disconnect(self.db_data_update)

    def new_file_selection(self, index):
        print 'new selection',index
        if self.fmodel.isDir(index):
            self.newsignal.emit(index)
            self.analyses_widget.clear()

    def db_data_update(self):
        selected = self.tview.selectedIndexes()
        row = selected[0].row()
        topleft = self.proxymodel.index(row,0, QC.QModelIndex())
        bottomright =  self.proxymodel.index(row,15, QC.QModelIndex())
        self.rmodel.data_update(topleft, bottomright)

    def tview_selection_changed(self):
        pass
        #selected = self.tview.selectedIndexes()
        #self.plot_pb.setVisible(bool(selected))

    def get_mode(self):
        if self.mode_combo.currentIndex() == 0:
            return Constants.TRANSIENT_TYPE
        elif self.mode_combo.currentIndex() == 1:
            return Constants.SPARK_TYPE
        else:
            return None

    def dosort(self):
        self.tview.sortByColumn(6,QC.Qt.AscendingOrder)
        self.tview.horizontalHeader().setSortIndicator(6, QC.Qt.AscendingOrder)

    def enable_display_pb(self, index):
        pass
        #selected = self.tview.selectedIndexes()
        #self.plot_pb.setVisible(bool(selected))


    def do_inspect(self):
        index = self.fview.currentIndex()
        self.fmodel.updateTarget(index)
        #print index,location
        #self.inspect_pb.setEnabled(False)
        #self.location_label.setVisible(True)

    def close_and_expand(self, index):
        self.fview.collapseAll()
        self.fview.expand(index)
    def set_file_being_inspected_label(self, text):
        print 'inspect',text
        self.file_in_progress_label.setText('Inspecting: <strong>%s</strong>'%text)

    def converted(self,value):
        print 'files converted',value
        self.convert_progressbar.setMinimum(0)
        self.convert_progressbar.setValue(value)

    def set_inspectpb_text(self, value):
        self.inspect_pb.setText("Inspect %i files"%value)

    def set_conversion_needed(self, value):
        if value>0:
            self.convert_pb.setVisible(True)
            self.convert_pb.setText("Convert %i files"%value)
            self.convert_progressbar.setMaximum(value)
        else:
            self.convert_pb.setVisible(False)

    def start_plot_with_analysis(self, analysis):
        print "got analysis:",analysis
        self.startPlot(analysis)

    def start_new_analysis(self):
        print "starting without analysis"
        self.startPlot()

    def startPlot(self, analysis = None):
        aw = self.mainStack.widget(1)
        if isinstance(aw, AnalysisWidget):
            aw.deleteLater()
            del aw
        analysisWidget = AnalysisWidget(analysis, self)
        analysisWidget.setStatusText[str].connect(self.showMessageplz)
        self.mainStack.insertWidget(1, analysisWidget)
        self.proxymodel.preparePlot()

    def start_show_reference(self):
        indices = self.proxymodel.prepareShowReference()
        toshow = self.rmodel.show_ref(indices)
        if toshow:
            self.reference_plot_widget.set_image(toshow[0])
            self.active_image = toshow[0]
            self.analyses_widget.set_image(toshow[0])
            self.expinfo_pb.setEnabled(True)


    def showMessageplz(self,txt):
        self.status.showMessage(txt)

    def on_actionInfo_triggered(self):
        self.tb = QW.QTextEdit()
        self.tb.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        self.tb.setText(self.mainStack.widget(1).data.info.replace('\n','<br>'))
        self.infoL = QW.QHBoxLayout()
        self.infoL.addWidget(self.tb)
        self.qd = QW.QDialog()
        self.qd.setWindowTitle('LSM file info')
        self.qd.setFixedWidth(550)
        self.qd.setFixedHeight(500)
        self.qd.setLayout(self.infoL)
        self.qd.show()
    def getLogfileName(self):
        handlers = logging.root.handlers
        if len(handlers)>0:
            fileHandler = handlers[0]
        else:
            return None
        if isinstance(fileHandler, logging.FileHandler):
            return fileHandler.baseFilename
        else:
            return None

    def on_actionLog_triggered(self):
        tb = QW.QTextEdit(self)
        tb.setReadOnly(True)
        #tb.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        log_filename = self.getLogfileName()
        if log_filename:
            text = "Log file: <b>%s</b><br/><br/>"%log_filename
            try:
                logfile = open(log_filename,'r')
                text += "".join(logfile.readlines())
                text = text.replace("\n","<br/>")
                text = text.replace("INFO","<b>INFO</b>")
                text = text.replace("DEBUG","<b>DEBUG</b>")
                text = text.replace("ERROR","<b style='color:red'>ERROR</b>")
                text = text.replace("CRITICAL","<b style='color:red'>CRITICAL</b>")
                print text
            except:
                text += "No messages in logfile"
        else:
            text = "No log file"

        tb.setHtml(text)
        qh = QW.QDialog(self)
        infoL = QW.QHBoxLayout(qh)
        infoL.addWidget(tb)
        qh.setWindowTitle('Log')
        qh.setFixedWidth(650)
        qh.setFixedHeight(300)
        qh.setLayout(infoL)
        #self.qh.show()
        res = qh.exec_()

    def on_actionHelp_triggered(self):
        tb = QW.QTextBrowser(self)
        tb.setOpenExternalLinks(True)
        tb.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
        text = 'You are using version <b>%.3f</b> of the LSJuicer program<br><br>Read the tutorial on <b>LSJuicer</b> <a href="http://code.google.com/p/lsjuicer/wiki/GettingStarted?tm=6">website</a> to get started'%self.version
        tb.setHtml(text)

        logo = QG.QPixmap(":/juicerlogo.png")
        label = QW.QLabel()
        label.setPixmap(logo.scaledToHeight(300))
        qh = QW.QDialog(self)
        infoL = QW.QHBoxLayout(qh)
        infoL.addWidget(tb)
        infoL.addWidget(label)
        qh.setWindowTitle('Help')
        qh.setFixedWidth(450)
        qh.setFixedHeight(300)
        qh.setLayout(infoL)
        #self.qh.show()
        res = qh.exec_()
        #print res

    def updateCoords(self,xv,yv,xs,ys):
        print 'up'
        self.status.showMessage('x: %.3f, y: %.3f, sx: %i, sy: %i'%(xv,yv,xs,ys))

    @helpers.timeIt
    def load_file(self, imfiles):
        try:
            d = ImageDataMaker.from_db_image(imfiles[0])
            self.tasker.analysisButton.setEnabled(True)
            self.tasker.analysisButton.click()
            #self.mainStack.widget(1).getImageTab().showData(d)
            self.mainStack.widget(1).setData(d)
        except:
            print 'Reading failed'
            self.qmb.hide()
            traceback.print_exc()
        else:
            print "in else"
            self.qmb.hide()
            del(self.qmb)
            self.actionSaveData.setEnabled(True)
            if 1:
                while self.tabs.count() > 1:
                    w=self.tabs.widget( self.tabs.count() -1)
                    self.tabs.removeTab(self.tabs.count() - 1)
                    del(w)


    def open_file(self, imfiles):
        if not hasattr(self,'dirname'):
            self.dirname = '/home/ardo/experiments'
        if 1:
            if len(imfiles) == 1:
                txt = 'Loading file'
            else:
                txt = 'Loading %i files'%len(imfiles)
            self.qmb=QW.QMessageBox(QW.QMessageBox.Information,'Loading ...',txt,QW.QMessageBox.Ok)
            #remove ok button as we are just showing 'loading' text
            b = self.qmb.buttons()
            self.qmb.removeButton(b[0])
            self.qmb.show()
            QC.QTimer.singleShot(50, lambda :self.load_file(imfiles))


    #def on_actionNew_triggered(self):
    #    self.open_file(False)

    #def on_actionSaveAll_triggered(self):
    #    if not os.path.isdir(self.pic_dirname):
    #        os.mkdir(self.pic_dirname)
    #    views = self.getAllViews()
    #    outfile = os.path.join(self.pic_dirname,self.imname.replace(' ','_') +'.dat')
    #    #TODO: fix this mess
    #    #if self.analysisWidget.write_out(outfile,self.imname):
    #    #    for v in views:
    #    #        view = v[0]
    #    #        type = v[1]
    #    #        imname = (self.imname +"_%s"%type+ '.png').replace(' ','_')
    #    #        fname = os.path.join(self.pic_dirname,imname)
    #    #        self.saveViewToImage(view,fname)
    #    #    QG.QMessageBox.information(self,'Success','Files saved')

    def on_actionSaveData_triggered(self):
        #if not os.path.isdir(self.pic_dirname):
        #    os.mkdir(self.pic_dirname)
        #outfile = os.path.join(self.pic_dirname,self.imname +'.dat')
        #print outfile
        self.mainStack.widget(1).save_result_data()
        #TODO: fix this mess
        #if self.analysisWidget.write_out(outfile,self.imname):
        #    QG.QMessageBox.information(self,'Success','Data saved')

    #def on_actionSave_triggered(self):
    #    if not os.path.isdir(self.pic_dirname):
    #        os.mkdir(self.pic_dirname)
    #    view,type = self.getActiveView()
    #    imname = self.imname.replace(' ','_')
    #    fname = os.path.join(self.pic_dirname,imname +"_%s"%type+ '.png')
    #    status = self.saveViewToImage(view,fname)
    #    if status:
    #        QG.QMessageBox.information(self,'Success','File saved to\n%s'%fname)
    #    else:
    #        QG.QMessageBox.critical(self,'Failed','Failed to save file to\n%s'%fname)

    #def getActiveView(self):
    #    active_tab = self.tabs.currentIndex()
    #    if active_tab == 0:
    #        return self.analysisWidget.lsmPlot.fV,'lsm'
    #    else:
    #        tabs = self.tabs.widget(active_tab)
    #        view,name = tabs.activeView()
    #        name = self.tabs.tabText(active_tab)+"_"+name
    #        return view,name

    #def getAllViews(self):
    #    views = []
    #    #if hasattr(self.analysisWidget.lsmPlot,'fV'):
    #    #    views.append([self.analysisWidget.lsmPlot.fV,'lsm'])
    #    for tabno in range(self.tabs.count()):
    #        if tabno == 0:
    #            views.append([self.analysisWidget.lsmPlot.fV,'lsm'])
    #        else:
    #            tab = self.tabs.widget(tabno)
    #            tabviews = tab.getAllViews()
    #            for view in tabviews:
    #                v = view[0]
    #                name = view[1]
    #                views.append([v,self.tabs.tabText(tabno)+"_"+name])
    #    return views

    #def saveViewToImage(self,view,filename):
    #    rec=view.sceneRect()
    #    x0= QC.QPoint(view.mapFromScene(rec.x(),rec.y()))
    #    x1= QC.QPoint(view.mapFromScene(rec.width(),rec.height()))
    #    #width = x1.x()-x0.x()
    #    #height = x1.y() - x0.y()
    #    rec = view.viewport().rect()
    #    self.paint_dev = QG.QImage(rec.width(),rec.height(),QG.QImage.Format_RGB32)
    #    brush = view.scene().backgroundBrush()
    #    view.scene().setBackgroundBrush(QG.QBrush(QG.QColor('white')))
    #    self.painter = QG.QPainter(self.paint_dev)
    #    self.painter.setRenderHint(QG.QPainter.Antialiasing)
    #    self.painter.setRenderHint(QG.QPainter.HighQualityAntialiasing)
    #    view.render(self.painter,QC.QRectF(0,0,0,0),view.viewport().rect())
    #    status=self.paint_dev.save(filename)
    #    view.scene().setBackgroundBrush(brush)
    #    del(self.painter)
    #    del(self.paint_dev)
    #    return status
