import re
import traceback

import PyQt4.QtCore as QC
import PyQt4.QtGui as QG

import numpy as n

import scipy.signal as ss
from scipy import poly1d, polyfit
from scipy import ndimage as sn
import scipy.interpolate as si

from lsjuicer.util import helpers
from lsjuicer.static import selection_types
from lsjuicer.ui.items.selection import BoundaryManager, SelectionDataModel
from lsjuicer.static.constants import TransientBoundarySelectionTypeNames as TBSTN

class Pipe(QC.QObject):
    pipe_toggled = QC.pyqtSignal()
    new_data_out = QC.pyqtSignal()
    def _set_data_in(self, data_in):
        self._data_in = data_in
        #print self.name,' set data in', data_in.shape
        self.process()


    def process(self):
        pass

    def set_chain(self, chain):
        self.chain=chain

    def _get_data_in(self):
        #print self.name,' get data in', self._data_in,self
        return self._data_in

    data_in = property(fset = _set_data_in, fget = _get_data_in)

    @property
    def data_out(self):
        #print self.name,' get data out', self._data_out,self
        #print self.name,' sending data out', self._data_out.shape
        return self._data_out

    @data_out.setter
    def data_out(self, data_out):
        self._data_out = data_out
        #print self.name, "new data out set"
        #print self.name,' set data out', self._data_out,self
        self.new_data_out.emit()

    #data_out = property(fset = _set_data_out, fget = _get_data_out)

    def __init__(self, name=None):
        super(Pipe, self).__init__()
        self.name = name
        self.chain = None
        self.enabled = True
        self.up_pipe = None
        self.processed = False
        self._data_in = None
        self._data_out = None
        self.needs_ROI = False
        self.options = {}
        self.values = {}
        self.pixel_size = None

    def set_enabled(self, enabled):
        #print 'enabled ', self.name
        self.enabled = enabled
        self.processed = True
        self.pipe_toggled.emit()
        self.process()
        self.new_data_out.emit()

    def new_values(self):
        #print 'new values ', self.name
        self.processed = True
        #print 'nv p',self.name
        self.process()
        #print 'nv ndo',self.name
        #self.new_data_out.emit()
        #print 'nv pt',self.name
        self.pipe_toggled.emit()

    def set_pixelsize(self, pixelsize):
        self.pixel_size = pixelsize

    def set_up_pipe(self, pipe):
        #pipe that is before this one in the chain
        #print 'set up',self.name
        if not self.up_pipe:
            #print 'no up pipe'
            pass
        elif self.up_pipe is pipe:
            #'connection exists',self.name,pipe.name
            return
        else:
            #print 'disconnect', self.name, self.up_pipe.name
            self.up_pipe.new_data_out.disconnect(self.new_data_in)
        #print 'make connection', self.name, pipe.name
        self.up_pipe = pipe
        self.up_pipe.new_data_out.connect(self.new_data_in)

    def new_data_in(self):
        #print self.name,' new data in'
        self.data_in = self.up_pipe.data_out

class PassPipe(Pipe):
    """Pipe that simply passes input to output"""
    def _set_data_in(self, data_in):
        self._data_in = data_in
    def process(self):
        #print 'process',self.name
        self.data_out = self.data_in

class ProcessPipe(Pipe):

    def process(self):
        pass

    def extra_ui(self):
        #pipes that needs extra ui elements can return these by this method
        return None

    def update_options(self):
        for option in self.option_names:
            self.options[option].setValue(self.values[option])

class SingleChannelProcessPipe(ProcessPipe):
    """Pipe that works on data from each channel separately"""
    def process(self):
        #print 'process',self.name
        if self.enabled and self.processed:
            q = n.zeros_like(self.data_in)
            for channel in range(q.shape[0]):
                q[channel] = self.do_processing(channel)
            self.data_out = q
        else:
            self.data_out = self.data_in

    def do_processing(self, channel_no):
        pass

class MultiChannelProcessPipe(ProcessPipe):
    """Pipe that works on data from all channel concurrently"""
    def process(self):
        #print 'process',self.name
        if self.enabled and self.processed:
            print 'process ', self.enabled, self.processed
            q = self.do_processing()
            self.data_out = q
        else:
            print 'process ', self.enabled, self.processed
            self.data_out = self.data_in

    def do_processing(self):
        pass

class BlurPipe(SingleChannelProcessPipe):
    def __init__(self, *args, **kwargs):
        super(BlurPipe, self).__init__(*args, **kwargs)

        init_value = 0.6
        option_2 = QG.QDoubleSpinBox()
        option_2.setMaximum(20)
        option_2.setMinimum(0)
        option_2.setSingleStep(0.1)
        option_2.setValue(init_value)
        self.options['Amount x'] = option_2
        self.values['Amount x'] = init_value

        init_value = 0.6
        option_3 = QG.QDoubleSpinBox()
        option_3.setMaximum(200)
        option_3.setMinimum(0)
        option_3.setSingleStep(0.1)
        option_3.setValue(init_value)
        self.options['Amount y'] = option_3
        self.values['Amount y'] = init_value

        option_1 = QG.QComboBox()
        option_1.addItem("Gaussian")
        option_1.addItem("Uniform")
        option_1.addItem("Median")
        self.options['Type'] = option_1
        init_value = "Uniform"
        index = option_1.findText(init_value)
        option_1.setCurrentIndex(index)
        self.values['Type'] = init_value

    def do_processing(self, channel):
        #q = helpers.blur_image(self.data_in, self.values['Amount'])
        #return q
        data = self.data_in[channel]
        blur_type = self.values['Type']
        level_x = self.values['Amount x']
        level_y = self.values['Amount y']
        blur_x = level_x/(self.pixel_size[0])
        blur_y = level_y/(self.pixel_size[1])
        level = (blur_y, blur_x)
        print "\n\nDoing blur",blur_type, level, self.pixel_size
        if blur_type == "Median":
            blurred_data = sn.median_filter(data, level)
        elif blur_type == "Uniform":
            blurred_data = sn.uniform_filter(data, level)
        elif blur_type =="Gaussian":
            blurred_data = sn.gaussian_filter(data, level)
        return blurred_data

class ShearPipe(MultiChannelProcessPipe):
    align_indices = None
    def __init__(self, *args, **kwargs):
        super(ShearPipe, self).__init__(*args, **kwargs)

        self.align_indices = None
        init_value = 100
        option_1 = QG.QSpinBox()
        option_1.setMaximum(20000)
        option_1.setMinimum(1)
        option_1.setValue(init_value)
        self.options['Lines'] = option_1
        self.values['Lines'] = init_value

        init_value = 0
        option_2 = QG.QSpinBox()
        option_2.setMaximum(50000)
        option_2.setMinimum(0)
        option_2.setValue(init_value)
        self.options['Start'] = option_2
        self.values['Start'] = init_value

        init_value = 0
        option_3 = QG.QSpinBox()
        option_3.setMaximum(50)
        option_3.setMinimum(0)
        option_3.setValue(init_value)
        self.options['Order'] = option_3
        self.values['Order'] = init_value

        init_value = False
        option_4 = QG.QCheckBox("Reuse other channel")
        option_4.setChecked(init_value)
        self.options['Reuse'] = option_4
        self.values['Reuse'] = option_4

        init_value = 1
        option_5 = QG.QSpinBox()
        option_5.setMaximum(10)
        option_5.setMinimum(1)
        option_5.setValue(init_value)
        self.options['Times'] = option_5
        self.values['Times'] = init_value

        self.selection = None
        self.needs_ROI = True
        self.option_names = ['Lines', 'Start']

    def do_processing(self):
        #q = helpers.blur_image(self.data_in, 8)
        d=self.data_in.copy()
#        align_indices = wave.argmax(axis=1)
        if self.values['Reuse']:
            if ShearPipe.align_indices is not None:
                #print 'using indices'
                align_indices = ShearPipe.align_indices
                d=self.align_image(d, align_indices)
            else:
                pass
                #print 'nothing to use'
        else:
            wave = d[:,self.values['Start']:self.values['Start']+self.values['Lines']]
            d, ShearPipe.align_indices = self.align(d, wave,times=self.values['Times'])

#        first = align_indices[0]
        self.selection=None
        self.roi_manager.remove_selections()
        self.roi_manager.disable_builder()
        return d

    def align(self, image, wave, times=1):
        cumulative_align_indices = None
        image_0 = image.copy()
        for i in range(times):
            align_indices = self.get_align_indices(wave)
            if cumulative_align_indices is not None:
                cumulative_align_indices += align_indices
            else:
                cumulative_align_indices = align_indices
            #cumulative_align_indices = self.fit_indices(cumulative_align_indices)
            image = self.align_image(image, align_indices)
        cumulative_align_indices = self.fit_indices(cumulative_align_indices)
        image = self.align_image(image_0, cumulative_align_indices)
        return image, cumulative_align_indices


    def align_image(self, data, align_indices):
        d=data
        for i in range(1,d.shape[0]):
            d[i] = n.roll(d[i],align_indices[i])
        return d

    def fit_indices(self, indices):
        order = self.values['Order']
        if order:
            if order == -1:
                import fitfun
                def fitf(arg, y0,y1,y2,x1):
                    n=len(indices)
                    x=arg
                    ya = (y1-y0)/x1*x + y0
                    yb = (y2-y1)/(n-x1)*(x-x1)+y1
                    return ya*(x<x1)+yb*(x>=x1)
                xx = n.arange(len(indices))
                oo=fitfun.Optimizer(xx, indices)
                oo.set_function(fitf)
                oo.set_parameter_range('y0', min(indices),max(indices),0)
                oo.set_parameter_range('y1', min(indices),max(indices),0)
                oo.set_parameter_range('y2', min(indices),max(indices),0)
                oo.set_parameter_range('x1', 2.0, len(indices)-2.,len(indices)/2.)
                oo.optimize()
                #print oo.solutions
                #print 'old',indices.tolist()
                indices=fitf(arg=xx, **oo.solutions).astype('int')
                #print 'new',indices.tolist()
            else:
                #print 'old i', indices.tolist()
                x = range(len(indices))
                fit_f= poly1d( polyfit( x,indices, self.values['Order']) )
                indices = fit_f(x).round().astype('int')
                #print 'new i', indices.tolist()
        else:
            pass
        return indices

    def get_align_indices(self, wave):
        #wave = helpers.blur_image(wave.astype('float'),1)
        wave = sn.uniform_filter(wave.astype('float'), (3,3))
        indices = []
        w_base = wave.mean(axis=0)
        w_base_n = (w_base-w_base.min())/(w_base.max()-w_base.min())
        pad_left = n.ones(wave.shape[1]/2.)*w_base_n[0:10].mean()
        pad_right = n.ones(wave.shape[1]/2.)*w_base_n[-10:].mean()
        ww0=n.hstack((pad_left,w_base_n,pad_right))
        flatten = 3
        for i in range(wave.shape[0]):
            if 0:
                indices.append(0)
            else:
                ww = wave[max(0,i-flatten):min(wave.shape[0], i+flatten)]
                w_i = ww.mean(axis=0)
                w_i2 = helpers.smooth(wave[i])
                w_i = helpers.smooth(w_i)
                w_i_n = (w_i-w_i.min())/(w_i.max()-w_i.min())
                w_i_n2 = (w_i2-w_i2.min())/(w_i2.max()-w_i2.min())
                cc = ss.correlate(ww0, w_i_n, mode='valid')
                indices.append(cc.argmax()-wave.shape[1]/2.)
        #make a nice polynomial fit for the indices
        indices = n.array(indices).astype('int')
        return indices

    def set_scene(self, scene):
        self.scene = scene
        self.roi_manager = BoundaryManager(self.scene, selection_types.data['pipes.singleboundary'])
        self.selection_model = SelectionDataModel()
        self.selection_model.set_selection_manager(self.roi_manager)
        self.roi_manager.selection_added.connect(self.boundary_selected)

    def boundary_selected(self):
        self.selection = self.roi_manager.selections[0]
        self.selection.changed.connect(self.boundary_changed)

    def boundary_changed(self):
        #print self.selection.rectf
        left = self.selection.rectf.left()
        width = self.selection.rectf.width()
        self.values['Start']=left
        self.values['Lines']=width
        self.update_options()


    def extra_ui(self):
        button = QG.QPushButton('Select')
        button.clicked.connect(lambda:self.roi_manager.activate_builder_by_type_name(TBSTN.MANUAL))
        return button

class ImageMathPipe(MultiChannelProcessPipe):
    def __init__(self, *args, **kwargs):
        super(ImageMathPipe, self).__init__(*args, **kwargs)
        self.needs_ROI = False
        self.option_names = ['Expression']
        option_1 = QG.QLineEdit()
        self.options['Expression'] = option_1
        self.values['Expression'] = ""

    def do_processing(self):
        """Process the expression. We expect it to contain channels as ch[0-9]
        which will be replaced with channel[[0-9]]"""
        expr = self.values['Expression']
        def repl_f(match):
            return "channels[%s]"%(match.group(1))
        print 'expression is', expr, type(expr)
        if expr:
            channels = self.data_in.astype('float')
            valid_expr = "res=%s"%(re.sub('ch([0-9])', repl_f, expr))
            print valid_expr
            import_statement = "from numpy import cos,log,sqrt,sin"
            exec_statement = "\n".join([import_statement, valid_expr])
            try:
                exec(exec_statement)
            #resize the result to the expected shape and dimension
                res.shape = (1,res.shape[0], res.shape[1], res.shape[2])
            #print channels[0].mean(), channels[0].min(), channels[0].max()
            #print channels[1].mean(), channels[1].min(), channels[1].max()
            #print res.mean(), res.min(), res.max()
                return n.vstack((res,)*self.data_in.shape[0])
            except Exception,e:
                QG.QMessageBox.critical(None, "Error with expression!",
                        "Error:\n"+traceback.format_exception_only(type(e),e)[0])
        return self.data_in





class SelfRatioPipe(SingleChannelProcessPipe):
    def __init__(self, *args, **kwargs):
        super(SelfRatioPipe, self).__init__(*args, **kwargs)
        self.needs_ROI = True

        self.option_names = ['Lines', 'Start']
        init_value = 100
        option_1 = QG.QSpinBox()
        option_1.setMaximum(10000)
        option_1.setMinimum(1)
        option_1.setValue(init_value)
        self.options['Lines'] = option_1
        self.values['Lines'] = init_value
        init_value = 0
        option_2 = QG.QSpinBox()
        option_2.setMaximum(50000)
        option_2.setMinimum(0)
        option_2.setValue(init_value)
        self.options['Start'] = option_2
        self.values['Start'] = init_value

        self.selection = None

    def set_scene(self, scene):
        self.scene = scene
        self.roi_manager = BoundaryManager(self.scene, selection_types.data['pipes.singleboundary'])
        self.selection_model = SelectionDataModel()
        self.selection_model.set_selection_manager(self.roi_manager)
        self.roi_manager.selection_added.connect(self.boundary_selected)

    def boundary_selected(self):
        self.selection = self.roi_manager.selections[0]
        self.selection.changed.connect(self.boundary_changed)

    def boundary_changed(self):
        print self.selection.rectf
        left = self.selection.rectf.left()
        width = self.selection.rectf.width()
        self.values['Start']=left
        self.values['Lines']=width
        self.update_options()

    def do_processing(self,channel):
        d = self.data_in[channel]
        array_for_mean = d[:,
                self.values['Start']:self.values['Start']+self.values['Lines']]
        means = array_for_mean.mean(axis=1)
        means_array = n.column_stack((means,)*d.shape[1])
        q = self.data_in/means_array
        self.selection=None
        self.roi_manager.remove_selections()
        self.roi_manager.disable_builder()
        return q

    def extra_ui(self):
        button = QG.QPushButton('Select')
        button.clicked.connect(lambda:self.roi_manager.activate_builder_by_type_name(TBSTN.MANUAL))
        return button


class ImageProcessPipe(ProcessPipe):
    def __init__(self, *args, **kwargs):
        super(ImageProcessPipe, self).__init__(*args, **kwargs)
        init_value = 2.0
        option_1 = QG.QSpinBox()
        option_1.setMaximum(10)
        option_1.setMinimum(1)
        option_1.setValue(init_value)
        self.options['Multiplier 1'] = option_1
        self.values['Multiplier 1'] = init_value
        init_value = 3.0
        option_2 = QG.QSpinBox()
        option_2.setMaximum(10)
        option_2.setMinimum(1)
        option_2.setValue(init_value)
        self.options['Multiplier 2'] = option_2
        self.values['Multiplier 2'] = init_value
        #self.value = init_value

    def do_processing(self):
        q = self.data_in**(1./self.values["Multiplier 1"])
        return q

class PipeChain(QC.QObject):
    pipe_state_changed = QC.pyqtSignal()
    new_histogram = QC.pyqtSignal()

    def set_source_data(self, source_data):
        self.source_data = source_data
        #print 'source data shape', source_data.shape
        if source_data.ndim == 3:
            pass
        elif source_data.ndim == 4:
            pass
        else:
            raise ValueError("wrong data dimension %i"%source_data.ndim)
        self.percentage_value_map = {}
        self.inpipe.data_in = self.source_data
        #self.calc_histogram()



    def calc_histogram(self):
        #ignore call if a pipe has been freshly inserted
        if self.pipe_insertion:
            self.pipe_insertion = False
            return
        for channel in range(self.source_data.shape[0]):
            #data = self.source_data[channel]
            data = self.get_result_data()[channel]
            #if nans are in the data then use only non-nan data for histogram
            nans = n.isnan(data)
            if n.any(nans):
                data = data[n.invert(n.isnan(data))]

            histogram = n.histogram(data, bins=min(64, max(5, n.sqrt(data.size))), density=True)
            counts = histogram[0]
            bins = histogram[1]
            percs = []
            cumul = (counts*n.diff(bins)).cumsum()
            percs=cumul.tolist()
            percs.insert(0,0) #add first value to avoid out of interpolation range errors
            self.perc_val_funcs[channel] = si.interp1d(n.array(percs)*100, bins)
            self.val_perc_funcs[channel] = si.interp1d(bins, n.array(percs)*100)
            self.histograms[channel] = histogram
        self.new_histogram.emit()

    def histogram(self, channel=0):
        if not self.histograms:
            self.calc_histogram()
        return self.histograms[channel]

    def percentage_value(self, percentage, channel = 0):
        if not self.perc_val_funcs:
            self.calc_histogram()
        return self.perc_val_funcs[channel](100-(percentage+0.01))

    def value_percentage(self, value, channel = 0):
        if not self.val_perc_funcs:
            self.calc_histogram()
        return self.val_perc_funcs[channel](value)

    def update_pixel_size(self, pixel_size):
        self.pixel_size = pixel_size
        for pipe in self.imagepipes:
            pipe.set_pixelsize(self.pixelsize)

    def get_result_data(self):
        return self.outpipe.data_out

    #def set_frame(self, frame=None):
    #    if frame is not None:
    #        self.frame = frame
    #    if self.frame is not None:
    #        self.inpipe.data_in = self.source_data[:,self.frame,:,:]
    #    else:
    #        self.inpipe.data_in = self.source_data
    @property
    def active(self):
        """Return True if pipechain has any active elements, False otherwise"""
        if len(self.pipes)<3:
            return False
        else:
            for p in self.process_pipes:
                if p.enabled and p.processed:
                    return True
            return False

    @property
    def process_pipes(self):
        return self.pipes[1:-1]

    def __init__(self, pixel_size=None, graphicsscene=None, parent = None):
        super(PipeChain, self).__init__(parent)
        self.pipes = []
        self.scene = graphicsscene
        self.pixel_size = pixel_size
        self.percentage_value_map = {}
        self.histograms = {}
        self.perc_val_funcs = {}
        self.val_perc_funcs = {}
        self.imagepipes = []
        #this is needed to avoid extra histogram calculation when pipe is added
        #to the chain.
        self.pipe_insertion=False
        self.inpipe = PassPipe("inpipe")
        self.inpipe.set_chain(self)
        self.outpipe = PassPipe("outpipe")
        self.outpipe.set_chain(self)
        self.outpipe.new_data_out.connect(self.calc_histogram)
        self.do_connections()

    def add_pipe(self, new_pipe):
        self.pipe_insertion = True
        self.imagepipes.append(new_pipe)
        new_pipe.set_pixelsize(self.pixel_size)
        new_pipe.set_chain(self)
        if new_pipe.needs_ROI:
            new_pipe.set_scene(self.scene)
        self.do_connections()
        new_pipe.pipe_toggled.connect(lambda:self.pipe_state_changed.emit())

    def do_connections(self):
        self.pipes = []
        self.pipes.append(self.inpipe)
        for pipe in self.imagepipes:
            self.pipes.append(pipe)
        self.pipes.append(self.outpipe)

        for i in range(len(self.pipes)-1):
            source = self.pipes[i]
            sink = self.pipes[i+1]
            sink.set_up_pipe(source)
        if self.inpipe.data_in is not None:
            self.inpipe.process()

class PipeWidget(QG.QFrame):
    def __init__(self, pipe, parent = None):
        super(PipeWidget, self).__init__(parent)
        layout = QG.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        self.setFrameStyle(QG.QFrame.StyledPanel)
        self.setFrameShadow(QG.QFrame.Plain)
        visible_layout = QG.QHBoxLayout()
        settings_layout = QG.QGridLayout()
        settings_layout.setContentsMargins(0,0,0,0)
        settings_layout.setSpacing(0)
        settings_frame = QG.QFrame()
        settings_frame.setLayout(settings_layout)
        layout.addLayout(visible_layout)
        layout.addWidget(settings_frame)
        name_label = QG.QLabel(pipe.name)
        on_checkbox = QG.QCheckBox("Enabled")
        on_checkbox.setChecked(True)
        on_checkbox.toggled.connect(pipe.set_enabled)
        on_checkbox.toggled.connect(settings_frame.setEnabled)
        #details_pb = QG.QPushButton('Settings')
        #details_pb.setCheckable(True)
        #details_pb.setChecked(False)
        #settings_frame.setVisible(False)
        #details_pb.toggled.connect(settings_frame.setVisible)
        visible_layout.addWidget(name_label)
        visible_layout.addWidget(on_checkbox)
        #visible_layout.addWidget(details_pb)
        count = 0
        apply_pb = QG.QPushButton("Apply")
        for option in pipe.options:
            settings_layout.addWidget(QG.QLabel(option), count, 0)
            settings_layout.addWidget(pipe.options[option], count, 1)
            if isinstance(pipe.options[option], QG.QLineEdit):
                print 'connect lineedit'
                pipe.options[option].returnPressed.connect(self.set_pipe_options)
            count +=1
        extra_ui = pipe.extra_ui()
        if extra_ui:
            settings_layout.addWidget(extra_ui, count,0,1,2)
            count +=1
        apply_pb = QG.QPushButton("Apply")
        settings_layout.addWidget(apply_pb, count, 1)
        apply_pb.clicked.connect(self.set_pipe_options)
        self.pipe = pipe

    def minimumSizeHint(self):
        return QC.QSize(100,100)

    def set_pipe_options(self):
        new = False
        for option in self.pipe.options:
            widget = self.pipe.options[option]
            if isinstance(widget, QG.QCheckBox):
                new_value = widget.isChecked()
            elif isinstance(widget, QG.QComboBox):
                new_value = str(widget.currentText())
            elif isinstance(widget, QG.QLineEdit):
                new_value = str(widget.text())
                if not test_string(new_value):
                    QG.QMessageBox.critical(self, "Bad input!",
                            "The expression %s is invalid!"%new_value)
                    new_value = ""
            else:
                new_value = self.pipe.options[option].value()
            if new_value != self.pipe.values[option]:
                self.pipe.values[option] = new_value
                new = True
            else:
                pass
        if new or not self.pipe.processed:
            self.pipe.new_values()


def test_string(s):
    allowed = ['ch', '+','/','-','+','*','sqrt','log','sin','cos','(',')','.']
    numbers = [str(el) for el in range(10)]
    allowed.extend(numbers)
    s2 = s
    for a in allowed:
        s2 = s2.replace(a,'')
    if s2:
        return False
    else:
        return True


class PipeChainWidget(QG.QWidget):
    pipes_changed = QC.pyqtSignal()
    def __init__(self, pipechain, parent = None):
        super(PipeChainWidget, self).__init__(parent)
        self.pipechain = pipechain
        self.settings_widgets={}

        layout = QG.QHBoxLayout()
        self.setLayout(layout)
        self.types = {'SelfRatio':SelfRatioPipe,
                'Shear':ShearPipe, "Blur":BlurPipe,
                'Image math':ImageMathPipe}
        self.typecombo = QG.QComboBox()
        for t in self.types:
            #print t
            self.typecombo.addItem(t)
        add_layout = QG.QVBoxLayout()
        add_layout.addWidget(self.typecombo)
        add_pb = QG.QPushButton('Add')
        add_layout.addWidget(add_pb)
        add_pb.clicked.connect(self.add_pipe)

        pipelist = QG.QListView()
        self.pipemodel = PipeModel()
        pipelist.setModel(self.pipemodel)

        self.setting_stack = QG.QStackedWidget()

        self.pipechain.pipe_state_changed.connect(self.update_model)

        layout.addLayout(add_layout)
        layout.addWidget(pipelist)
        layout.addWidget(self.setting_stack)

        pipelist.clicked.connect(self.show_pipe_settings)
        #self.pipelistingarea = QG.QScrollArea()
        #self.pipelistingarea = QG.QWidget()
        #self.pipelistwidget = QG.QWidget()
        #self.pipelistwidget.setMinimumSize(100,200)
        #layout.addWidget(self.pipelistingarea)
        #layout.addWidget(self.pipelistwidget)
        #plw_layout = QG.QVBoxLayout()
        #self.pipelistwidget.setLayout(plw_layout)
        #self.pipelistingarea.setWidget(self.pipelistwidget)
        #:plw_layout.addWidget(QG.QLabel('W'))
        #self.make_widgetlist()
        self.setSizePolicy(QG.QSizePolicy.Maximum, QG.QSizePolicy.Maximum)

    def update_model(self):
        self.pipemodel.pipes_updated()
        self.pipes_changed.emit()

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
        #layout = self.pipelistwidget.layout()
        #label = QG.QLabel('ASDFS')
        #layout.addWidget(label)
        #print label.size()
        #self.pipelistwidget.setMinimumSize(100,100+self.c*label.height())
        #self.pipelistwidget.setMinimumSize(100,200+self.c*20)
        #self.pipelistingarea.setWidget(self.pipelistwidget)
        #pipewidget = PipeWidget(pipe)
        #layout.addWidget(pipewidget)
        #self.c+=1

    #def make_widgetlist(self):
    #    layout = self.pipelistwidget.layout()
    #    for imagepipe in self.pipechain.imagepipes:
    #        pipewidget = PipeWidget(imagepipe)
    #        layout.addWidget(pipewidget)

class PipeModel(QC.QAbstractListModel):
    def __init__(self, parent = None):
        super(PipeModel, self).__init__(parent)
        self._pipedata = []
    @property
    def pipedata(self):
        return self._pipedata
    @pipedata.setter
    def pipedata(self, pipes):
        #print 'new pipe'
        self.emit(QC.SIGNAL('modelAboutToBeReset()'))
        self._pipedata = pipes
        self.emit(QC.SIGNAL('modelReset()'))
        #print self._pipedata
    @property
    def rows(self):
        return len(self.pipedata)

    def rowCount(self, parent):
        return self.rows

    def data(self, index, role):
        pipe = self.pipedata[index.row()]
        if role == QC.Qt.DisplayRole:
            return pipe.name
        elif role==QC.Qt.DecorationRole:
            if pipe.enabled:
                if pipe.processed:
                    return QG.QColor('lime')
                else:
                    return QG.QColor('orange')
            else:
                return QG.QColor('red')
        else:
            return QC.QVariant()

    def pipes_updated(self):
        self.emit(QC.SIGNAL('modelAboutToBeReset()'))
        self.emit(QC.SIGNAL('layoutAboutToBeChanged()'))
        self.emit(QC.SIGNAL('modelReset()'))
        self.emit(QC.SIGNAL('layoutChanged()'))
