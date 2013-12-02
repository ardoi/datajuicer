from PyQt5 import QtWidgets as QW
from actionpanel import ActionPanel

from lsjuicer.data.pipes.tools import pipe_classes, PipeModel, PipeWidget

class PipeChainPanel(ActionPanel):
    __doc__ = """Panel for editing pipes for the image"""
    __shortname__ = "Pipes"

    def setup_ui(self):
        self.settings_widgets={}

        layout = QW.QHBoxLayout()
        self.setLayout(layout)
        self.types = pipe_classes
        self.typecombo = QW.QComboBox()
        for t in self.types:
            self.typecombo.addItem(t)
        add_layout = QW.QVBoxLayout()
        add_layout.addWidget(self.typecombo)
        add_pb = QW.QPushButton('Add')
        add_layout.addWidget(add_pb)
        add_pb.clicked.connect(self.add_pipe)

        pipelist = QW.QListView()
        self.pipemodel = PipeModel()
        pipelist.setModel(self.pipemodel)

        self.setting_stack = QW.QStackedWidget()

        self.pipechain.pipe_state_changed.connect(self.update_model)

        layout.addLayout(add_layout)
        layout.addWidget(pipelist)
        layout.addWidget(self.setting_stack)

        pipelist.clicked.connect(self.show_pipe_settings)
        #self.setSizePolicy(QG.QSizePolicy.Maximum, QG.QSizePolicy.Maximum)

    def update_model(self):
        self.pipemodel.pipes_updated()

    def show_pipe_settings(self, index):
        pipe_number = index.row()
        #print 'show', pipe_number
        pipe = self.pipechain.imagepipes[pipe_number]
        if pipe in self.settings_widgets:
            sw, pos = self.settings_widgets[pipe]
            #print 'activate', sw,pos
        else:
            sw = PipeWidget(pipe)
            pos = self.setting_stack.addWidget(sw)
            self.settings_widgets[pipe] = (sw, pos)
            #print 'new', sw,pos
        self.setting_stack.setCurrentIndex(pos)

    def add_pipe(self):
        pipetypename = str(self.typecombo.currentText())
        pipetype = self.types[pipetypename]
        pipe = pipetype(pipetypename)
        self.pipechain.add_pipe(pipe)
        self.pipemodel.pipedata = self.pipechain.imagepipes


