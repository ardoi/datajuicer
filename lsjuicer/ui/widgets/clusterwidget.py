from itertools import cycle

import numpy

from sklearn.cluster import DBSCAN

from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC

from lsjuicer.inout.db.sqla import dbmaster
import lsjuicer.data.analysis.transient_find as tf
from lsjuicer.ui.widgets.plot_with_axes_widget import TracePlotWidget

def normify(a):
    #you can use preprocessing.scale instead
    #b=10.0
    res = (a-a.mean())/a.std()
    #left = ss.scoreatpercentile(res,b)
    #right = ss.scoreatpercentile(res,100-b)
    #r2=res.clip(left,right)
    return res

class ClusterWidget(QG.QWidget):
    clusters_ready = QC.pyqtSignal(dict)
    def __init__(self, cluster_data, plot_pairs, key, settings, parent = None, reference_data = None):
        super(ClusterWidget, self).__init__(parent)

        self.cluster_data = cluster_data
        if reference_data is None:
            self.reference_data = self.cluster_data
        else:
            self.reference_data = reference_data

        widget_layout = QG.QVBoxLayout()
        self.plot_layout = QG.QGridLayout()
        self.setLayout(widget_layout)
        widget_layout.addLayout(self.plot_layout)
        self.rows = len(plot_pairs.keys())
        #self.columns = max([len(el) for el in plot_pairs.values()])
        self.plotwidgets = {}
        self.plot_pairs = plot_pairs
        self.make_plot_widgets()
        self.key = key
        setting_layout = QG.QHBoxLayout()
        do_pb = QG.QPushButton('Do')
        do_pb.clicked.connect(self.do)
        setting_layout.addWidget(do_pb)
        widget_layout.addLayout(setting_layout)
        self.settings = settings

        button_layout = QG.QVBoxLayout()
        setting_layout.addLayout(button_layout)
        ms_layout = QG.QHBoxLayout()
        button_layout.addLayout(ms_layout)
        min_sample_label  = QG.QLabel("Minimum core samples:",parent=self)
        min_sample_spinbox = QG.QSpinBox(self)
        ms_layout.addWidget(min_sample_label)
        ms_layout.addWidget(min_sample_spinbox)
        eps_layout = QG.QHBoxLayout()
        button_layout.addLayout(eps_layout)
        eps_label  = QG.QLabel("Eps:",parent=self)
        eps_spinbox = QG.QDoubleSpinBox(self)
        eps_layout.addWidget(eps_label)
        eps_layout.addWidget(eps_spinbox)
        eps_spinbox.setMinimum(0.1)
        eps_spinbox.setMaximum(25.0)
        eps_spinbox.setSingleStep(0.1)
        eps_spinbox.setValue(settings['eps'])
        min_sample_spinbox.setMinimum(1)
        min_sample_spinbox.setMaximum(200)
        min_sample_spinbox.setSingleStep(1)
        min_sample_spinbox.setValue(settings['min_samples'])

        self.eps_spinbox = eps_spinbox
        self.min_sample_spinbox = min_sample_spinbox

    def do(self):
        eps = self.eps_spinbox.value()
        min_samples = self.min_sample_spinbox.value()
        self.do_cluster(eps, min_samples)
        self.do_plots()

    def do_cluster(self, eps, min_samples):
        self.clusters = Clusterer.cluster_elements(Clusterer.cluster(self.cluster_data,
            eps = eps, min_samples = min_samples), self.reference_data)
        print 'clusterkeys',self.clusters.keys()

    def make_plot_widgets(self):
        if self.plotwidgets:
            return
        for i, kind in enumerate(self.plot_pairs.keys()):
            for j, spp in enumerate(self.plot_pairs[kind]):
                print kind, spp
                x = spp[0]
                y = spp[1]
                plotwidget = TracePlotWidget(self, antialias=False,
                    xlabel = x, ylabel = y)
                self.plotwidgets[spp] = plotwidget
                if self.rows > 1:
                    self.plot_layout.addWidget(plotwidget, i, j)
                else:
                    self.plot_layout.addWidget(plotwidget, j, 0)
        print self.plotwidgets
        QG.QApplication.processEvents()

    def do_plots(self):
        colornames = cycle(['red', 'green', 'blue', 'yellow', 'orange', 'teal', 'magenta', 'lime', 'navy', 'brown'])
        for spp, plotwidget in self.plotwidgets.iteritems():
            plotwidget.clear()
        for cluster, elements  in  self.clusters.iteritems():
            group_name = "Group %i"%cluster
            if cluster != -1:
                color = colornames.next()
            else:
                color = 'black'
            style={'style':'circles', 'color':color, 'alpha':0.50}
            if cluster == -1:
                style.update({'size':0.5, 'alpha':0.5})
            for i, kind in enumerate(self.plot_pairs.keys()):
                for j, spp in enumerate(self.plot_pairs[kind]):
                    x = self.key[spp[0]]
                    y = self.key[spp[1]]
                    plotwidget = self.plotwidgets[spp]
                    plotwidget.addPlot(group_name, elements[:,x], elements[:,y],
                            plotstyle = style, hold_update = True)
        for spp, plotwidget in self.plotwidgets.iteritems():
            plotwidget.updatePlots()
            plotwidget.fitView()
        self.clusters_ready.emit(self.clusters)

class Clusterer(object):
    @staticmethod
    def cluster_elements(labels, data):
        groups = {}
        for k in set(labels):
            members = numpy.argwhere(labels == k).flatten()
            groups[k] = data[members]
        return groups

    @staticmethod
    def cluster(data, eps, min_samples):
        #D = metrics.euclidean_distances(data)
        #S = 1 - (D / numpy.max(D))
        print 'clustering', eps, min_samples
        print data.shape, data[0]
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(data)
        #core_samples = db.core_sample_indices_
        labels = db.labels_
        print set(labels)
        # Number of clusters in labels, ignoring noise if present.
        #n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        return labels


class ClusterDialog(QG.QDialog):
    def __init__(self, analysis, parent=None):
        super(ClusterDialog, self).__init__(parent)
        layout = QG.QHBoxLayout()
        self.analysis = analysis
        self.setLayout(layout)
        do_pb = QG.QPushButton("Get clusters")
        layout.addWidget(do_pb)
        do_pb.clicked.connect(self.stats)

    def sizeHint(self):
        return QC.QSize(1300,1000)

    def stats(self):
        an = self.analysis
        session = dbmaster.object_to_session(an)
        pixels=an.fitregions[0].results[0].pixels
        el=tf.do_event_list(pixels)

        shape_params = ['A','tau2','d2','d']
        loc_params = ['m2','x','y']
        params = shape_params[:]
        params.extend(loc_params)
        #dictionary of parameter names and their indices
        ics = dict(zip(params, range(len(params))))
        self.shape_params = shape_params
        self.loc_params = loc_params
        self.ics = ics


        event_array = tf.do_event_array(el, params)
        #for shape parameters a normalized array is needed too
        ea_shape0 = tf.do_event_array(el,shape_params)
        ea_shape = numpy.apply_along_axis(normify, 0, ea_shape0)
        #ea_shape = ea_shape0
        #ea_loc = tf.do_event_array(el,['m2','x','y'])
        session.close()
        tabs = QG.QTabWidget(self)
        self.layout().addWidget(tabs)
        self.tabs = tabs

        shape_plot_pairs = [('d', 'tau2'),('tau2','A'),('A', 'd')]
        loc_plot_pairs = [('m2','x'),('x','y'),('m2','y')]
        self.loc_plot_pairs = loc_plot_pairs
        plot_pairs = {'shape':shape_plot_pairs, 'location':loc_plot_pairs}
        try:
            shape_cluster_tab = ClusterWidget(ea_shape, plot_pairs, ics,{'eps':2.0, 'min_samples':50},
                    parent= tabs, reference_data = event_array)
            #shape_cluster_tab.do()
            shape_cluster_tab.clusters_ready.connect(self.add_loc_clusters)
        except:
            from IPython.frontend.terminal.embed import InteractiveShellEmbed
            #from IPython import embed_kernel
            QC.pyqtRemoveInputHook()
            ipshell=InteractiveShellEmbed()
            ipshell()
            #embed_kernel()
        tabs.addTab(shape_cluster_tab, 'Clusters by shape')

    def add_loc_clusters(self, cluster_data):
        #TODO remove existing tabs when making new
        for cluster, elements in cluster_data.iteritems():
            if cluster!=-1:
                data = elements[:,[self.ics[e] for e in self.loc_params]]
                loc_ics = dict(zip(self.loc_params, range(len(self.loc_params))))
                plot_pairs={'location':self.loc_plot_pairs}
                print 'loc ics',loc_ics,data.shape
                tab = ClusterWidget(data, plot_pairs, loc_ics, {'eps':2.5, 'min_samples':15},parent=self.tabs)
                index = self.tabs.addTab(tab,'Type %i'%cluster)


        #        for spp in loc_plot_pairs:
        #            x=spp[0]
        #            y=spp[1]
        #            plotwidget = ContinousPlotWidget(self, antialias=False,
        #                xlabel = x, ylabel = y)
        #            plotwidgets[cluster][spp] = plotwidget
        #            plot_layout.addWidget(plotwidgets[cluster][spp])
        #        for type_cluster, elements  in  clusters.iteritems():
        #            group_name = "Group %i"%cluster
        #            if type_cluster != -1:
        #                color = colornames.next()
        #            else:
        #                color = 'black'
        #            style={'style':'circles', 'color':color, 'alpha':0.25}
        #            if type_cluster == -1:
        #                style.update({'size':0.5,'alpha':0.75})

        #            for spp in loc_plot_pairs:
        #                x=loc_ics[spp[0]]
        #                y=loc_ics[spp[1]]
        #                plotwidget = plotwidgets[cluster][spp]
        #                plotwidget.addPlot(group_name, elements[:,x], elements[:,y], plotstyle = style, hold_update = True)

            self.tabs.setCurrentIndex(index)
        #    for spp, plotwidget in plotwidgets[cluster].iteritems():
        #        plotwidget.updatePlots()
        #        plotwidget.fitView()


