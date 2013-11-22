from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC


from lsjuicer.ui.scenes import LSMDisplay
from lsjuicer.static.constants import Constants
from lsjuicer.ui.widgets.plot_with_axes_widget import PixmapPlotWidget
from lsjuicer.data.pipes.tools import PipeChain
from lsjuicer.ui.plot.pixmapmaker import PixmapMaker

from lsjuicer.ui.widgets.panels import PipeChainPanel
from lsjuicer.ui.widgets.panels import VisualizationPanel
from lsjuicer.ui.widgets.panels import FramePanel
from lsjuicer.ui.widgets.panels import AnalysisPanel
from lsjuicer.ui.widgets.panels import EventPanel
import lsjuicer.inout.db.sqla as sa

from lsjuicer.ui.widgets.clicktrees import PanelClickTree, Panels



class ControlWidget(QW.QWidget):
    def  __init__(self, panels, parent = None):
        super(ControlWidget, self).__init__(parent)
        layout = QW.QHBoxLayout()
        layout.setAlignment(QC.Qt.AlignLeft)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.groupboxes = {}
        self.panels = panels
        chooser = PanelClickTree(panels)
        self.chooser = chooser
        chooser.visibility_toggled.connect(self.toggle)
        self.add_grouping(chooser, "Panels")

    def add_grouping(self, widget, name):
        groupbox = QW.QGroupBox(name)
        layout = QW.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        groupbox.setSizePolicy(QW.QSizePolicy.Maximum,QW.QSizePolicy.Minimum)
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


class AnalysisImageTab(QW.QWidget):
    """Tab containing image to analyze"""
    positionTXT = QC.pyqtSignal(str)
    def  __init__(self, analysis = None, parent = None):
        super(AnalysisImageTab, self).__init__(parent)
        self.image_shown = False
        self.analysis = analysis
        self.sess = sa.dbmaster.get_session()
        layout = QW.QVBoxLayout()
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
        return self.frame_widget.active_channel

    @property
    def active_frame(self):
        return self.frame_widget.active_frame

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
                self.event_widget.active_events_changed.connect(self.force_new_pixmap)
                self.frame_widget.set_region(self.analysis.fitregions[0])

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
        self.positionTXT.emit('x: %.3f [s], y: %.1f [um], sx: %i, sy: %i'%(x, y, xx, yy))

    def makePlotArea(self):
        return PixmapPlotWidget(sceneClass=LSMDisplay, parent=self)

    def show_events(self,event_times):
        self.image_plot.addHLines(event_times,Constants.EVENTS, 'cyan')

    def show_gaps(self,gap_times):
        self.image_plot.addHLines(gap_times,Constants.GAPS,'yellow')

