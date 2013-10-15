from collections import defaultdict
from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC

from lsjuicer.ui.scenes import LSMDisplay
from lsjuicer.static.constants import Constants
from lsjuicer.ui.widgets.plot_with_axes_widget import PixmapPlotWidget
from lsjuicer.data.pipes.tools import PipeChain
from lsjuicer.ui.plot.pixmapmaker import PixmapMaker

from lsjuicer.ui.widgets.panels  import PipeChainPanel, VisualizationPanel, FramePanel, AnalysisPanel, EventPanel
from lsjuicer.ui.widgets.panels  import ActionPanel

import lsjuicer.inout.db.sqla as sa

class Panels(object):
    def __init__(self):
        self.panel_dict = {}
        self.panels_by_name = {}

    def add_type(self, name):
        if not name in self.panel_dict:
            self.panel_dict[name] = []
        else:
            raise ValueError("Type {} already exists".format(name))

    def add_panel(self, type_name, panel):
        if panel.__base__ != ActionPanel:
            raise ValueError("Panel has to be a subclass of ActionPanel")
        if not type_name in self.panel_dict:
            self.add_type(type_name)
        self.panel_dict[type_name].append(panel)
        self.panels_by_name[panel.__shortname__] = panel

    def get_panel_by_name(self, name):
        if name in self.panels_by_name:
            return self.panels_by_name[name]
        else:
            return None

class Events(object):
    def __init__(self):
        self.types = []
        self.event_dict = defaultdict(list)
        self.status_dict = defaultdict(list)

    def add_event(self, event):
        event_type = event.category.category_type.name
        self.event_dict[event_type].append(event)
        self.status_dict[event_type].append(False)

    def change(self, event_type, row, status):
        self.status_dict[event_type][row]=status
        print self.status_dict

class EventClickTree(QG.QWidget):
    visibility_toggled = QC.pyqtSignal(str, int)

    def __init__(self, parent = None):
        super(EventClickTree, self).__init__(parent)
        layout  = QG.QVBoxLayout()
        self.setLayout(layout)
        view = QG.QTreeView(self)
        model = QG.QStandardItemModel()
        self.model = model
        self.items_by_name = {}
        model.setHorizontalHeaderLabels(["Event"])
        view.setIndentation(10)
        view.header().setResizeMode(0, QG.QHeaderView.ResizeToContents)
        view.header().setResizeMode(1, QG.QHeaderView.ResizeToContents)
        view.setModel(model)
        view.setEditTriggers(QG.QAbstractItemView.NoEditTriggers)
        view.expanded.connect(lambda: view.resizeColumnToContents(0))
        view.collapsed.connect(lambda: view.resizeColumnToContents(0))
        view.clicked.connect(self.clicked)
        layout.addWidget(view)

    def set_events(self, events):
        self.events = events
        root = self.model.invisibleRootItem()
        for typename, event_list in events.event_dict.iteritems():
            type_item = QG.QStandardItem(typename)
            root.appendRow(type_item)
            for i,ei in enumerate(event_list):
                event_item = QG.QStandardItem("{} id={}".format(i, ei.id))
                event_item.setCheckable(True)
                type_item.appendRow([event_item] )

    def toggle(self, name, state):
        print 'toggle',name
        name = str(name)

        print [type(el) for el in self.items_by_name], type(name)
        if name in self.items_by_name:
            item = self.items_by_name[name]
            print name, item
            item.setCheckState(QC.Qt.Checked)

    def clicked(self, modelindex):
        print '\nccc'
        row = modelindex.row()
        parent = modelindex.parent()
        event_type = str(parent.data().toString())
        state = modelindex.data(10).toBool()
        print row,event_type,state
        if event_type:
            self.events.change(event_type, row, state)

class ClickTree(QG.QWidget):
    visibility_toggled = QC.pyqtSignal(str, int)

    def __init__(self, panels, parent = None):
        super(ClickTree, self).__init__(parent)
        layout  = QG.QVBoxLayout()
        self.panels = panels
        self.setLayout(layout)
        view = QG.QTreeView(self)
        model = QG.QStandardItemModel()
        self.model = model
        self.items_by_name = {}
        #model.setHorizontalHeaderItem(0, QG.QStandardItem("Name"))
        #model.setHorizontalHeaderItem(1, QG.QStandardItem("Description"))
        model.setHorizontalHeaderLabels(["Name", "Info"])
        root = model.invisibleRootItem()
        for typename, panel_list in panels.panel_dict.iteritems():
            type_item = QG.QStandardItem(typename)
            root.appendRow(type_item)
            for pi in panel_list:
                panel_item = QG.QStandardItem(pi.__shortname__)
                panel_item.setCheckable(True)
                desc_item = QG.QStandardItem(QG.QIcon(QG.QPixmap(":/information.png")),"Info")
                type_item.appendRow([panel_item, desc_item] )
                self.items_by_name[pi.__shortname__] = panel_item
        #view.setWordWrap(True)
        view.setIndentation(10)
        view.header().setResizeMode(0, QG.QHeaderView.ResizeToContents)
        view.header().setResizeMode(1, QG.QHeaderView.ResizeToContents)
        view.setModel(model)
        view.setEditTriggers(QG.QAbstractItemView.NoEditTriggers)
        view.expanded.connect(lambda: view.resizeColumnToContents(0))
        view.collapsed.connect(lambda: view.resizeColumnToContents(0))
        view.clicked.connect(self.clicked)
        layout.addWidget(view)

    def toggle(self, name, state):
        print 'toggle',name
        name = str(name)

        print [type(el) for el in self.items_by_name], type(name)
        if name in self.items_by_name:
            item = self.items_by_name[name]
            print name, item
            item.setCheckState(QC.Qt.Checked)

    def clicked(self, modelindex):
        print '\nccc'
        print modelindex.row(), modelindex.column(),modelindex.data().toString(),modelindex.parent()
        parent = modelindex.parent()
        name = str(self.model.data(self.model.index(modelindex.row(), 0, parent)).toString())
        state = modelindex.data(10).toBool()
        print name
        actionpanel = self.panels.get_panel_by_name(name)
        print name,state,actionpanel
        if actionpanel:
            if modelindex.column() == 1:
                QG.QMessageBox.information(self, "Panel info",
                        "<strong>{0.__shortname__}</strong><br>{0.__doc__}".format(actionpanel))
            elif modelindex.column() == 0:
                self.visibility_toggled.emit(str(name), state)



class ControlWidget(QG.QWidget):
    def  __init__(self, panels, parent = None):
        super(ControlWidget, self).__init__(parent)
        layout = QG.QHBoxLayout()
        layout.setAlignment(QC.Qt.AlignLeft)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.groupboxes = {}
        self.panels = panels
        chooser = ClickTree(panels)
        self.chooser = chooser
        chooser.visibility_toggled.connect(self.toggle)
        self.add_grouping(chooser, "Panels")

    def add_grouping(self, widget, name):
        groupbox = QG.QGroupBox(name)
        layout = QG.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        groupbox.setSizePolicy(QG.QSizePolicy.Maximum,QG.QSizePolicy.Minimum)
        groupbox.setLayout(layout)
        layout.addWidget(widget)
        self.groupboxes[name]=groupbox
        self.layout().addWidget(groupbox)

    def init_panel(self, pclass, **kwargs):
        name = str(pclass.__shortname__)
        panel_class = self.panels.get_panel_by_name(name)
        widget = panel_class(**kwargs)
        self.add_grouping(widget, str(name))
        self.chooser.toggle(name, True)
        return widget

    def toggle(self, name, state):
        name = str(name)
        if name in self.groupboxes:
            gb = self.groupboxes[str(name)]
            print gb
            gb.setVisible(state)



class AnalysisImageTab(QG.QWidget):
    """Tab containing image to analyze"""
    def  __init__(self, analysis = None, parent = None):
        super(AnalysisImageTab, self).__init__(parent)
        self.image_shown = False
        self.analysis = analysis
        self.sess = sa.dbmaster.get_session()
        layout = QG.QVBoxLayout()
        self.setLayout(layout)
        self.image_plot =self.makePlotArea()
        self.image_plot.updateLocation.connect(self.updateCoords)
        layout.addWidget(self.image_plot)

        panels = Panels()
        panels.add_panel("Default", PipeChainPanel)
        panels.add_panel("Default", VisualizationPanel)
        panels.add_panel("Default", FramePanel)
        panels.add_panel("Default", AnalysisPanel)
        panels.add_panel("Analysis", EventPanel)
        self.control_widget = ControlWidget(panels)
        layout.addWidget(self.control_widget)
        layout.setStretchFactor(self.image_plot, 5)
        layout.setStretchFactor(self.control_widget, 1)

    def __del__(self):
        self.sess.commit()
        #self.sess.close()

    def setAW(self,widget):
        self.aw = widget

    @property
    def active_channel(self):
        return self.frame_widget.channel_combobox.currentIndex()
    @property
    def active_frame(self):
        return self.frame_widget.selection_slider.value()

    def force_new_pixmap(self, v = None):
        self.make_new_pixmap(force = True)

    def change_pixmap_settings(self, settings):
        self.make_new_pixmap(settings, viewreset = False)

    #@helpers.timeIt
    def make_new_pixmap(self, settings={}, viewreset = True, force=False):
        #print 'making new pix', force,settings
        #qmb=QG.QMessageBox(QG.QMessageBox.Information,
        #        '','Please wait...\nAdjusting image',QG.QMessageBox.Ok)
        #b=qmb.buttons()
        #qmb.removeButton(b[0])
        #qmb.show()
        channel = self.active_channel
        frame = self.active_frame
        pixmaker = self.pixmaker
        QC.QTimer.singleShot(0,lambda:
                pixmaker.makeImage(channel=channel,frame = frame, image_settings=settings, force=force))
                #self.data.makeImage(saturate/100.,cmap_name,0))
        if self.image_shown:
            QC.QTimer.singleShot(0,lambda:
                    self.image_plot.replacePixmap(pixmaker.pixmap))
        else:
            QC.QTimer.singleShot(0,lambda:
                    self.image_plot.addPixmap(pixmaker.pixmap,
                        self.imagedata.xvals, self.imagedata.yvals))
        self.image_shown = True

    def showData(self, data):
        self.imagedata = data
        self.pipechain = None
        self.pixmaker = None
        self.analysis_mode = None

        pc = PipeChain(data.pixel_size, self.image_plot.fscene)
        pc.set_source_data(self.imagedata.all_image_data)
        pc.pipe_state_changed.connect(self.force_new_pixmap)
        self.pipechain = pc
        pixmaker = PixmapMaker(pc)
        self.pixmaker = pixmaker


        self.pipe_widget = self.control_widget.init_panel(PipeChainPanel,
                parent = self)
        self.vis_widget = self.control_widget.init_panel(VisualizationPanel,
                parent = self)
        self.frame_widget = self.control_widget.init_panel(FramePanel,
                parent = self)
        self.analysis_widget = self.control_widget.init_panel(AnalysisPanel,
                parent = self)
        if self.analysis and isinstance(self.analysis, sa.PixelByPixelAnalysis):
            if self.analysis.fitregions:
                self.event_widget = self.control_widget.init_panel(EventPanel,
                        parent = self)

        self.vis_widget.settings_changed.connect(self.make_new_pixmap)
        self.frame_widget.frame_changed.connect(self.change_frame)
        self.frame_widget.channel_changed.connect(self.change_channel)
        self.frame_widget.channel_changed.connect(self.vis_widget.channel_change)
        #make sure other widgets are drawn before making pixmap
        QC.QTimer.singleShot(0,lambda: self.make_new_pixmap())

    def change_channel(self, channel):
        self.force_new_pixmap()


    def change_frame(self, frame):
        self.force_new_pixmap()


    def updateCoords(self,x,y,xx,yy):
        self.emit(QC.SIGNAL('positionTXT(QString)'),
                'x: %.3f [s], y: %.1f [um], sx: %i, sy: %i'%(x,y,xx,yy))

    def makePlotArea(self):
        return PixmapPlotWidget(sceneClass=LSMDisplay, parent=self)

    def show_events(self,event_times):
        self.image_plot.addHLines(event_times,Constants.EVENTS, 'cyan')

    def show_gaps(self,gap_times):
        self.image_plot.addHLines(gap_times,Constants.GAPS,'yellow')

