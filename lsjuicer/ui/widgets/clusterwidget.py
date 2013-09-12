from itertools import cycle

import numpy

from sklearn.cluster import DBSCAN

from PyQt4 import QtGui as QG
from PyQt4 import QtCore as QC

from lsjuicer.inout.db.sqla import dbmaster
import lsjuicer.inout.db.sqla as sa
import lsjuicer.data.analysis.transient_find as tf
from lsjuicer.ui.widgets.plot_with_axes_widget import TracePlotWidget
from lsjuicer.ui.widgets.fileinfowidget import DBComboAddBox, MyFormLikeLayout, FocusLineEdit

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

    def __init__(self, data, parameter_names, plot_pairs, key, category_class, normalize = False,
                 parent = None):
        """
        Arguments
        ---------
        data : entire data array (possibly containing more columns than needed for clustering)
        parameter_names : the names of the parameters clustering is to be performed for
        plot_pairs : pairs parameter names plots are desired for
        key : dictionary mapping parameter name to its index in data
        normalize : whether to normalize data or not

        """
        super(ClusterWidget, self).__init__(parent)
        self.data = data
        self.category_class = category_class
        indices = [key[el] for el in parameter_names]
        self.cluster_data = data[:, indices]
        if normalize:
            self.cluster_data = numpy.apply_along_axis(normify, 0, self.cluster_data)
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
        do_pb = QG.QPushButton('Do clustering')
        if self.category_class == sa.EventCategoryShapeType:
            action_pb = QG.QPushButton("Cluster by Location")
            action_pb.clicked.connect(self.emit_ready)
        elif self.category_class == sa.EventCategoryLocationType:
            action_pb = QG.QPushButton("Save clusters")
            action_pb.clicked.connect(self.save_clusters)
        self.action_pb = action_pb
        self.category_widget = EventCategoryWidget(self.category_class)
        setting_layout.addWidget(self.category_widget)
        setting_layout.addWidget(do_pb)
        setting_layout.addWidget(action_pb)
        do_pb.clicked.connect(self.do)
        widget_layout.addLayout(setting_layout)
        QC.QTimer.singleShot(50, lambda:self.do())


    def do(self):
        eps = self.category_widget.eps
        min_samples = self.category_widget.samples
        self.do_cluster(eps, min_samples)
        self.do_plots()

    def do_cluster(self, eps, min_samples):
        print 'do_cluster', eps, min_samples
        self.clusters = Clusterer.cluster_elements(Clusterer.cluster(self.cluster_data,
            eps = eps, min_samples = min_samples), self.data)
        #print 'clusterkeys',self.clusters.keys()

    def make_plot_widgets(self):
        if self.plotwidgets:
            return
        for i, kind in enumerate(self.plot_pairs.keys()):
            for j, spp in enumerate(self.plot_pairs[kind]):
                x = spp[0]
                y = spp[1]
                plotwidget = TracePlotWidget(self, antialias=False,
                    xlabel = x, ylabel = y)
                self.plotwidgets[spp] = plotwidget
                if self.rows > 1:
                    self.plot_layout.addWidget(plotwidget, i, j)
                else:
                    self.plot_layout.addWidget(plotwidget, j, 0)
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

    def emit_ready(self):
        print 'ready', self.clusters[0.0][0]
        self.clusters_ready.emit(self.clusters)

    def save_clusters(self):
        #print 'save', self.clusters
        #print self.clusters
        #TODO remove existing events
        self.action_pb.setEnabled(False)
        QG.QApplication.setOverrideCursor(QG.QCursor(QC.Qt.BusyCursor))
        sess = dbmaster.get_session()

        def get_pixelevent_by_id(event_id):
            event_id = int(event_id)
            result = sess.query(sa.PixelEvent).filter(sa.PixelEvent.id == event_id).one()
            return result

        category = self.category_widget.category
        stats = []
        for event_no in self.clusters:
            if event_no == -1:
                continue
            event = sa.Event()
            event.category = category
            stats.append(self.clusters[event_no].shape[0])
            for pixel_event_line in self.clusters[event_no]:
                pe_id = pixel_event_line[-1]
                pixel_event = get_pixelevent_by_id(pe_id)
                result = pixel_event.pixel.result
                event.result = result
                pixel_event.event = event
        save_string = "<strong>Saved events:</strong><br><br>"+"<br>".join(["{}: {} pixels".format(i+1, el) for i,el in enumerate(stats)])
        print save_string
        sess.commit()
        sess.close()
        self.action_pb.setEnabled(True)
        QG.QApplication.restoreOverrideCursor()
        QG.QMessageBox.information(self, "", save_string)


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
        #print 'clustering', eps, min_samples
        #print data.shape, data[0]
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(data)
        #core_samples = db.core_sample_indices_
        labels = db.labels_
        #print set(labels)
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
        self.do_pb = do_pb

    def sizeHint(self):
        return QC.QSize(1300,1000)

    def stats(self):
        an = self.analysis
        session = dbmaster.object_to_session(an)
        #FIXME bad bad
        pixels=an.fitregions[0].results[0].pixels
        el=tf.do_event_list(pixels)

        #TODO these should not be hardcoded
        shape_params = ['A','tau2','d2','d']
        loc_params = ['m2','x','y']
        id_param = 'id'
        params = shape_params[:]
        params.extend(loc_params)
        params.append(id_param)
        #dictionary of parameter names and their indices
        ics = dict(zip(params, range(len(params))))
        self.shape_params = shape_params
        self.loc_params = loc_params
        self.ics = ics


        event_array = tf.do_event_array(el, params)
        self.event_array = event_array
        #for shape parameters a normalized array is needed too
        #ea_shape0 = tf.do_event_array(el,shape_params)
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
        #shape_cluster_tab = ClusterWidget(ea_shape, plot_pairs, ics, sa.EventCategoryShapeType,
        #        parent= tabs, reference_data = event_array)
        shape_cluster_tab = ClusterWidget(event_array, shape_params, plot_pairs, ics, sa.EventCategoryShapeType,
                                          normalize = True, parent= tabs)
        shape_cluster_tab.clusters_ready.connect(self.add_loc_clusters)
        tabs.addTab(shape_cluster_tab, 'Clusters by shape')
        self.do_pb.setVisible(False)


    def add_loc_clusters(self, cluster_data):
        """Add a tab for each shape cluster to be analyzed based on location"""
        print 'add_loc', cluster_data
        if self.tabs.count()>1:
            for i in range(1, self.tabs.count())[::-1]:
                w = self.tabs.widget(i)
                w.deleteLater()
                self.tabs.removeTab(i)
        for cluster, elements in cluster_data.iteritems():
            print 'cluster',elements
            if cluster != -1:
                #data = elements[:,[self.ics[e] for e in self.loc_params]]
                #loc_ics = dict(zip(self.loc_params, range(len(self.loc_params))))
                plot_pairs={'location':self.loc_plot_pairs}
                tab = ClusterWidget(elements, self.loc_params, plot_pairs, self.ics,
                                    sa.EventCategoryLocationType, parent=self.tabs)
                index = self.tabs.addTab(tab,'Type %i'%cluster)
            self.tabs.setCurrentIndex(index)

class EventCategoryWidget(QG.QWidget):
    def __init__(self, category_class, parent = None):
        super(EventCategoryWidget, self).__init__(parent)
        self.category_class = category_class
        self.cat_type = None
        self.category = None
        layout = QG.QVBoxLayout()
        self.setLayout(layout)
        gbox = QG.QGroupBox("Clustering settings")
        settings_layout = MyFormLikeLayout()
        gbox.setLayout(settings_layout)
        layout.addWidget(gbox)
        combo = DBComboAddBox(category_class, show_None = False)
        self.combo=combo
        combo.combo.currentIndexChanged[QC.QString].connect(self.update_settings)
        settings_layout.add_row("Type", combo)
        settings_combo = QG.QComboBox()
        settings_combo.currentIndexChanged.connect(self.update_spinboxes)
        settings_layout.add_row("Parameters", settings_combo)
        self.settings_combo =settings_combo
        self.settings_combo.setMinimumWidth(250)

        edit_checkbox = QG.QCheckBox(self)
        min_sample_spinbox = QG.QSpinBox(self)
        eps_spinbox = QG.QDoubleSpinBox(self)
        eps_spinbox.setMinimum(0.1)
        eps_spinbox.setMaximum(25.0)
        eps_spinbox.setSingleStep(0.05)
        min_sample_spinbox.setMinimum(2)
        min_sample_spinbox.setMaximum(200)
        min_sample_spinbox.setSingleStep(1)
        desc_edit = FocusLineEdit()
        desc_edit.set_default_text("optional")
        self.desc_edit = desc_edit
        settings_layout.add_row("Edit settings", edit_checkbox)
        settings_layout.add_row("Description", desc_edit)
        settings_layout.add_row("Minimum core samples", min_sample_spinbox)
        settings_layout.add_row("EPS", eps_spinbox)
        save_pb = QG.QPushButton("Save")
        settings_layout.add_row("", save_pb)

        self.min_sample_spinbox = min_sample_spinbox
        self.eps_spinbox = eps_spinbox
        self.save_pb = save_pb
        edit_checkbox.toggled.connect(self.toggle_edit)
        self.edit_checkbox = edit_checkbox
        self.toggle_edit(False)
        self.save_pb.clicked.connect(self.save)
        self.activate()

    def activate(self):
        name = self.combo.get_value()
        if name:
            self.update_settings(name)
            self.edit_checkbox.setEnabled(True)
        else:
            self.edit_checkbox.setEnabled(False)

    @property
    def eps(self):
        return self.eps_spinbox.value()

    @property
    def samples(self):
        samples = self.min_sample_spinbox.value()
        return samples

    def save(self):
        sess = dbmaster.get_session()
        temp_cat_type= self.category_class()
        samples = self.samples
        name = self.combo.get_value()
        eps = self.eps
        desc = self.desc_edit.get_text()



        #TODO only make new category if the saved one has events associated with it
        #(we dont want to change the settings for used categories)
        make_new = False

        if self.category:
            sess.add(self.category)
            if not self.category.events:
                #no events so category can be updated
                print 'category update'
                self.category.eps = eps
                self.category.min_samples = samples
                self.category.description = desc
                self.category_type = self.cat_type
                #self.reload_settings()
                sess.commit()
                self.activate()
            else:
                print 'description update'
                #events exist but only description is different. update description
                if self.category.eps == eps and self.category.min_samples == samples and \
                        self.category.description != desc:
                    self.category.description = desc
                    self.reload_settings()
                else:
                    make_new = True
            sess.commit()
            #sess.expunge(self.category)
        else:
            make_new = True

        if make_new:
            #build a query to find matching categories
            query = sess.query(sa.EventCategory).join(sa.EventCategoryType).\
                    filter(sa.EventCategoryType.category_type == temp_cat_type.category_type).\
                    filter(sa.EventCategoryType.name == name).\
                    filter(sa.EventCategory.eps == eps).\
                    filter(sa.EventCategory.min_samples == samples)
            #categories which are exactly the same
            existing = query.filter(sa.EventCategory.description == desc).first()
            #categories with different description
            different_desc = query.filter(sa.EventCategory.description != desc).first()
            #we don't want categories with same settings but different descriptions
            if existing:
                print "settings alread exist",(samples, eps)
                QG.QMessageBox.information(self, "Category exists",
                        """<p style='font-weight:normal;'>A <strong
                        style='color:navy;'>{}</strong> category with parameters
                        <br><strong style='color:navy'>{}</strong> already exists</p>"""
                        .format(temp_cat_type.category_type, str(existing[0])))
            elif different_desc:
                ec = different_desc
                ec.description = desc
                sess.commit()
                self.reload_settings()
                #self.activate()
            else:
                ec = sa.EventCategory()
                ec.eps = eps
                ec.min_samples = samples
                ec.description = desc
                ec.category_type = self.cat_type
                sess.add(ec)
                sess.commit()
                self.activate()
                self.settings_combo.setCurrentIndex(self.settings_combo.count() - 1)
        self.toggle_edit(True)
        sess.close()

    def toggle_edit(self, state):
        self.min_sample_spinbox.setEnabled(state)
        self.eps_spinbox.setEnabled(state)
        self.save_pb.setEnabled(state)
        self.desc_edit.setEnabled(state)
        self.edit_checkbox.setChecked(state)

    def get_category_type_by_name(self, name):
        sess = dbmaster.get_session()
        temp = self.category_class()
        cat_type = sess.query(sa.EventCategoryType).\
                filter(sa.EventCategoryType.name == str(name)).\
                filter(sa.EventCategoryType.category_type == temp.category_type).one()
        sess.close()
        del temp
        return cat_type

    def reload_settings(self):
        name = self.combo.get_value()
        sess = dbmaster.get_session()
        temp = self.category_class()
        self.settings = sess.query(sa.EventCategory).join(sa.EventCategoryType).\
                filter(sa.EventCategoryType.category_type == temp.category_type).\
                filter(sa.EventCategoryType.name == str(name)).all()
        del temp
        sess.close()

    def update_settings(self, name):
        """Update categorytype"""
        if not name:
            #DBComboBox updates stuff internally and can remove entries
            #To keep this function from crashing such calls are ignored here
            return
        self.reload_settings()
        self.cat_type = self.get_category_type_by_name(name)
        self.settings_combo.clear()
        if not self.settings:
            self.edit_checkbox.setEnabled(True)
            self.edit_checkbox.setChecked(True)
            self.category = None
        else:
            #print self.settings
            for s in self.settings:
                self.settings_combo.addItem(str(s))
            self.category = self.settings[0]
        #sess.close()

    def update_spinboxes(self, index):
        """Update category settings"""
        try:
            setting = self.settings[index]
            self.category = setting
            self.min_sample_spinbox.setValue(setting.min_samples)
            self.eps_spinbox.setValue(setting.eps)
            self.desc_edit.set_text(setting.description)
            #self.toggle_edit(False)
            #self.edit_checkbox
        except IndexError:
            self.min_sample_spinbox.setValue(0)
            self.eps_spinbox.setValue(0)
            self.desc_edit.set_text("")


