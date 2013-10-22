from collections import defaultdict


from PyQt5 import QtCore, QtWidgets

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

import numpy as n

from lsjuicer.ui.widgets.plot_with_axes_widget import PlotWidget, SparkFluorescencePlotWidget
from lsjuicer.ui.scenes import FDisplay
from lsjuicer.ui.items.selection import BoundaryManager
from lsjuicer.static.constants import TransientBoundarySelectionTypeNames as TBSTN
from lsjuicer.ui.tabs.resulttab import SparkResultsWidget
from lsjuicer.ui.items.selection import SelectionDataModel, SelectionWidget
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
from lsjuicer.data.spark import SparkData
from lsjuicer.ui.widgets.smallwidgets import SparkResultWidget, VisualizationOptionsWidget

class LocatedSpark(QtCore.QObject):
    """Combines spark with its horizontal(temporal) location"""
    def __init__(self, spark, location_h, location_v):
        self.spark = spark
        self.location_h = location_h
        self.location_v = location_v

class SparkTab(QW.QTabWidget):
    def __init__(self, rois, imagedata, parent = None):
        super(SparkTab, self).__init__(parent)
        print '\n\n\n\n\n\ncreating sparktab'
        self.parent_tab = parent
        self.imagedata = imagedata
        self.temporal_plotted = False
        self.spatial_plotted = False
        self.old_F0_bounds = None
        self.old_F0_average = None
        self.active_roi = None #active _roispark
        self.active_spark = None
        self.spark_rois_plotted = []
        self.roi_managers = {}
        self.spark_rois = []
        self.located_sparks = {}
        self.sparks = defaultdict(dict)
        self.active_boundary_index = None
        self.temporal_smooth_data = None
        self.temporal_phys_data = None
        spark_ROIs = rois[ISTN.SPARK_ROI]
        self.analysis_settings = {}
        self.resultwidget = None
        #self.status = Config.get_property('status_bar')

        #check if a background ROI is available
        if ISTN.BACKGROUND not in rois:
            bgr_r = None
        else:
            bgr = rois[ISTN.BACKGROUND][0].graphic_item.rect()
            bgr_r = [min(int(bgr.x()),int(bgr.x()+bgr.width())),
                    max(int(bgr.x()),int(bgr.x()+bgr.width())),
                    min(int(bgr.y()),int(bgr.y()+bgr.height())),
                    max(int(bgr.y()),int(bgr.y()+bgr.height()))]
        #go through spark ROIs and create SparkData objects
        for roi in spark_ROIs:
            r = roi.graphic_item.rect()
            r_r = [min(int(r.x()), int(r.x()+r.width())),
                    max(int(r.x()), int(r.x()+r.width())),
                    min(int(r.y()), int(r.y()+r.height())),
                    max(int(r.y()), int(r.y()+r.height()))]
            sd = SparkData(self.imagedata, r_r, bgr_r)
            self.spark_rois.append(sd)
            sd.set_name_from_number(len(self.spark_rois))
        self.spark_roi = self.spark_rois[0]
        self.spark = None
        self.setup_ui()
        QtCore.QTimer.singleShot(50, lambda :self.fit_all_plots())

    def set_settings(self, settings=None):
        shape = self.spark_roi.data.shape
        self.left_F0_slider.setMinimum(0)
        self.right_F0_slider.setMinimum(1)
        self.right_F0_slider.setMaximum(shape[1])
        self.left_F0_slider.setMaximum(shape[1]/4.)
        self.ver_slider.setMaximum(shape[0]-self.temporal_slice_span_spinb.value()-1)
        self.ver_slider.setMinimum(self.temporal_slice_span_spinb.value()+1)
        self.ver_spinner.setMaximum(shape[0]-self.temporal_slice_span_spinb.value()-1)
        self.ver_spinner.setMinimum(self.temporal_slice_span_spinb.value()+1)
        self.hor_slider.setMaximum(shape[1] - self.spatial_slice_span_spinb.value()-1)
        self.hor_spinner.setMaximum(shape[1] - self.spatial_slice_span_spinb.value()-1)
        self.hor_slider.setMinimum(self.spatial_slice_span_spinb.value()+1)
        self.hor_spinner.setMinimum(self.spatial_slice_span_spinb.value()+1)

        self.accept_button.setChecked(self.spark_roi.approved)

        if settings:
            self.left_F0_slider.setValue(settings['left_F0_slider'])
            self.right_F0_slider.setValue(settings['right_F0_slider'])
            self.hor_slider.setValue(settings['hor_slider'])
            self.ver_slider.setValue(settings['ver_slider'])
            self.old_F0_bounds = settings['old_F0_bounds']
            self.old_F0_average = settings['old_F0_average']
        else:
            self.left_F0_slider.setValue(1)
            self.right_F0_slider.setValue(shape[1]/4.-1)
            self.hor_slider.setValue(shape[1]/2.)
            self.ver_slider.setValue(shape[0]/2.)
            self.old_F0_bounds = None
            self.old_F0_average = None




    def change_active_spark(self, index):
        print 'active spark', index, index.row()
        number = index.row()
        boundary = self.roi_manager.selections[number]
        self.active_boundary_index = number
        if boundary in self.located_sparks:
            print 'already there'
            loc_spark = self.located_sparks[boundary]
            self.spark = loc_spark.spark
            new_max_h = loc_spark.location_h
            new_max = loc_spark.location_v
            #self.spark_result.setVisible(True)
            self.update_resultswidget()
        else:
            print 'not yet spark'
            x1 = boundary.graphic_item.rect().left()
            x2 = boundary.graphic_item.rect().right()
            start_x = self.fplot_temporal.scene2data((min(x1, x2), 0)).x()
            end_x = self.fplot_temporal.scene2data((max(x1, x2), 0)).x()
            x1index = self.find_index(start_x)
            x2index = self.find_index(end_x)

            new_max, new_max_h = self.get_max_spatial_loc(left = x1index, right = x2index)
            #add left border as offset
            new_max_h += x1index
            self.spark_result.setVisible(False)
        #self.ver_slider.setValue(new_max)
        self.hor_slider.setValue(new_max_h)

    def change_active_spark_region(self, number):
        print 'making spark roi %i active'%number
        self.temporal_plotted = False
        self.spatial_plotted = False
        self.spark_roi = self.spark_rois[number]
        self.spark_roi_number = number
        self.sparkplot.add_pixmap(self.spark_roi.pixmap,
                                  self.spatial_slice_span_spinb.value(),
                                  self.temporal_slice_span_spinb.value())
        if self.active_roi is not None:
            settings = {}
            settings['left_F0_slider'] = self.left_F0_slider.value()
            settings['right_F0_slider'] = self.right_F0_slider.value()
            settings['hor_slider'] = self.hor_slider.value()
            settings['ver_slider'] = self.ver_slider.value()
            settings['old_F0_bounds'] = self.old_F0_bounds
            settings['old_F0_average'] = self.old_F0_average
        if number in self.analysis_settings:
            self.set_settings(self.analysis_settings[number])
        else:
            self.set_settings()
            #self.recalculate_locations()
        if self.active_roi is not None:
            self.analysis_settings[self.active_roi] = settings

        if number in self.spark_rois_plotted:
            self.fplot_temporal = self.temporal_stack.widget(number)
            self.fplot_spatial = self.spatial_stack.widget(number)
            self.temporal_plotted = True
            self.spatial_plotted = True
            self.roi_manager = self.roi_managers[number]
        else:
            self.fplot_temporal = SparkFluorescencePlotWidget(sceneClass =
                    FDisplay, antialias = True, parent = self.temporal_stack)
            self.fplot_temporal.updateLocation.connect(self.update_temporal_slice_coords)
            self.fplot_spatial = SparkFluorescencePlotWidget(sceneClass =
                    FDisplay, antialias = True, parent = self.spatial_stack)
            self.fplot_spatial.updateLocation.connect(self.update_spatial_slice_coords)

            roi_manager = BoundaryManager(self.fplot_temporal.fscene,
                    defaults.selection_types.data['sparktab'])
            roi_manager.ROI_available.connect(self.spark_roi_selected)
            self.roi_managers[number] = roi_manager
            self.roi_manager = roi_manager
            self.temporal_stack.addWidget(self.fplot_temporal)
            self.spatial_stack.addWidget(self.fplot_spatial)
            self.spark_rois_plotted.append(number)
        self.selection_datamodel.set_selection_manager(self.roi_manager)
        self.selection_widget.set_model(self.selection_datamodel)
        self.plot_spatial()
        self.plot_temporal()
        self.active_roi = number

        #toggle next/prev buttons
        next_state = False
        prev_state = False
        if number > 0 and number < len(self.spark_rois) - 1:
            #middle spark
            next_state = True
            prev_state = True
        elif number == len(self.spark_rois) - 1:
            #last spark
            next_state = False
            if len(self.spark_rois) == 1:
                prev_state = False
            else:
                prev_state = True
        elif number == 0:
            prev_state = False
            if len(self.spark_rois) == 1:
                next_state = False
            else:
                next_state = True
        self.previous_spark_pb.setEnabled(prev_state)
        self.next_spark_pb.setEnabled(next_state)
        self.fplot_temporal.h_scroll_changed()
        self.fplot_spatial.h_scroll_changed()



        self.temporal_stack.setCurrentIndex(number)
        self.spatial_stack.setCurrentIndex(number)

        QtCore.QTimer.singleShot(102, lambda:self.reset_selected_spark())


    def reset_selected_spark(self):
        rows = self.selection_datamodel.rowCount(None)
        rows = len(self.roi_manager.selections)
        if rows:
            index = self.selection_datamodel.index(0)
            self.selection_widget.set_index(index)
            self.change_active_spark(index)
        else:
            self.spark_result.setVisible(False)
            self.active_boundary_index = None


    def plot_temporal(self):
        vloc =  self.spark_roi.data.shape[0] - self.ver_slider.value()
        halfspan = self.temporal_slice_span_spinb.value()
        smoothing = self.t_smooth_spinb.value()
        self.spark_roi.v_loc = vloc
        self.spark_roi.v_halfspan = halfspan
        self.spark_roi.temporal_smoothing = smoothing
        data = self.spark_roi.temporal_data
        smooth_data = self.spark_roi.temporal_smooth_data
        axis_data = self.spark_roi.temporal_axis_data
        if not self.temporal_plotted:
            self.fplot_temporal.addPlot('Temporal', data,
                    axis_data, color = 'cyan',
                    size=1, physical = False)
            self.fplot_temporal.addPlot('Temporal_smooth', smooth_data,
                    axis_data, color = 'cornflowerblue',
                    size=2, physical = False)
            self.temporal_plotted = True
        else:
            self.fplot_temporal.updatePlot('Temporal', data,
                    axis_data, only_grow = True)
            self.fplot_temporal.updatePlot('Temporal_smooth', smooth_data,
                    axis_data, only_grow = True)
        self.fplot_temporal.fitView(0)
        self.sparkplot.fitView(0)


    def plot_spatial(self):
        loc = self.hor_slider.value()
        halfspan = self.spatial_slice_span_spinb.value()
        smoothing = self.s_smooth_spinb.value()

        self.spark_roi.h_loc = loc
        self.spark_roi.h_halfspan = halfspan
        self.spark_roi.spatial_smoothing = smoothing

        data = self.spark_roi.spatial_data
        smooth_data = self.spark_roi.spatial_smooth_data
        axis_data = self.spark_roi.spatial_axis_data
        if not self.spatial_plotted:
            self.fplot_spatial.addPlot('Spatial', data,
                    axis_data, color = 'magenta',
                    size=1, physical = False)
            self.fplot_spatial.addPlot('Spatial_smooth', smooth_data,
                    axis_data, color = 'purple',
                    size=2, physical = False)
            self.spatial_plotted = True
        else:
            self.fplot_spatial.updatePlot('Spatial', data,
                    axis_data, only_grow = True)
            self.fplot_spatial.updatePlot('Spatial_smooth', smooth_data,
                    axis_data, only_grow = True)
        self.fplot_spatial.fitView(0)
        self.sparkplot.fitView(0)

    def fit_all_plots(self):
        self.sparkplot.fitView(0)
        self.fplot_spatial.fitView(0)
        self.fplot_temporal.fitView(0)

    def make_spark_boundary(self, toggle):
        if toggle:
            self.roi_manager.activate_builder_by_type_name(TBSTN.MANUAL)
        else:
            self.roi_manager.disable_builder()

    def edit_spark_boundary(self, toggle):
        boundary = self.roi_manager.selections[0]
        boundary.set_editable(toggle)

    def delete_spark_boundary(self):
        self.roi_manager.remove_selections()
        self.make_spark_boundary_pb.setEnabled(True)
        self.edit_spark_boundary_pb.setEnabled(False)
        self.delete_spark_boundary_pb.setEnabled(False)
        self.calculate_spark_properties.setEnabled(False)
        pass

    def spark_roi_selected(self):
        if self.active_boundary_index is None:
            self.active_boundary_index = 0





    def setup_ui(self):
        main_layout = QW.QGridLayout()
        self.setLayout(main_layout)

        self.temporal_stack = QW.QStackedWidget()
        self.spatial_stack = QW.QStackedWidget()
        temporal_plot_groupbox = QW.QGroupBox('Temporal slice')
        temporal_plot_groupbox.setLayout(QW.QVBoxLayout())
        temporal_plot_groupbox.layout().addWidget(self.temporal_stack)
        main_layout.addWidget(temporal_plot_groupbox, 0, 0)
        temporal_plot_groupbox.setStyleSheet("""
        QGroupBox
        {
            font-weight: bold;
            color:cornflowerblue;
        }
        """)

        spatial_plot_groupbox = QW.QGroupBox('Spatial slice')
        spatial_plot_groupbox.setLayout(QW.QVBoxLayout())
        spatial_plot_groupbox.layout().addWidget(self.spatial_stack)
        main_layout.addWidget(spatial_plot_groupbox, 1, 0)
        main_layout.setRowStretch(0,1)
        main_layout.setRowStretch(1,1)

        spatial_plot_groupbox.setStyleSheet("""
        QGroupBox
        {
            font-weight: bold;
            color:purple;
        }
        """)
        main_layout.setColumnStretch(0,2)
        main_layout.setColumnStretch(1,2)
        select_and_result_layout = QW.QVBoxLayout()
        interaction_layout = QW.QVBoxLayout()
        main_layout.addLayout(interaction_layout, 0, 1, 2, 1)
        interaction_layout.addLayout(select_and_result_layout)

        self.spark_select_combobox = QW.QComboBox(self)
        for spark_roi in self.spark_rois:
            self.spark_select_combobox.addItem(spark_roi.icon, spark_roi.name)
        spark_and_boundary_button_layout = QW.QHBoxLayout()
        spark_select_groupbox = QW.QGroupBox('Select spark ROI')
        self.previous_spark_pb = QW.QPushButton(QG.QIcon(":/arrow_left.png"),'Previous')
        self.next_spark_pb = QW.QPushButton(QG.QIcon(":/arrow_right.png"),'Next')
        next_prev_layout = QW.QHBoxLayout()
        next_prev_layout.addWidget(self.previous_spark_pb)
        next_prev_layout.addWidget(self.next_spark_pb)
        self.previous_spark_pb.clicked.connect(self.activate_previous_spark)
        self.next_spark_pb.clicked.connect(self.activate_next_spark)
        self.previous_spark_pb.setEnabled(False)
        if len(self.spark_rois)<2:
            self.next_spark_pb.setEnabled(False)

        #delete_spark_pb = QG.QPushButton(QG.QIcon(":/cross.png"),'Remove')
        spark_select_button_layout = QW.QGridLayout()
        spark_select_groupbox.setLayout(spark_select_button_layout)
        spark_and_boundary_button_layout.addWidget(spark_select_groupbox)
        select_and_result_layout.addLayout(spark_and_boundary_button_layout)
        spark_select_button_layout.addWidget(self.spark_select_combobox,0,0)
        spark_select_button_layout.addLayout(next_prev_layout,1,0)
        #spark_select_button_layout.addWidget(delete_spark_pb,2,0)

        spark_boundaries_groupbox = QW.QGroupBox('Spark boundaries')

        self.selection_widget = SelectionWidget()
        self.selection_widget.item_clicked.connect(self.change_active_spark)
        self.selection_datamodel = SelectionDataModel()


        spark_and_boundary_button_layout.addWidget(spark_boundaries_groupbox)
        boundary_buttons_layout = QW.QGridLayout()
        spark_boundaries_groupbox.setLayout(boundary_buttons_layout)
        boundary_buttons_layout.addWidget(self.selection_widget)



        self.spark_select_combobox.currentIndexChanged.\
                connect(self.change_active_spark_region)

        results_groupbox = QW.QGroupBox('Analysis results')
        results_layout = QW.QGridLayout()
        results_groupbox.setLayout(results_layout)
        self.spark_result = SparkResultWidget(self)
        results_pb = QW.QPushButton(QG.QIcon(":/report_go.png"), 'Make table')
        results_pb.clicked.connect(self.results_table_clicked)

        self.calculate_spark_properties = QW.QPushButton(QG.QIcon(":/cog_go.png"),
                'Analyze')
        self.calculate_all_spark_properties = QW.QPushButton(QG.QIcon(":/cog_add.png"),
                'Analyze all')
        self.calculate_spark_properties.clicked.connect(self.analyze_spark)
        self.calculate_all_spark_properties.clicked.connect(self.analyze_all_sparks)

        self.accept_button = QW.QPushButton(QG.QIcon(":/lock_open.png"),'Accept')
        self.accept_button.setCheckable(True)
        self.accept_button.toggled.connect(self.accept_toggled)

        self.recalc_button=QW.QPushButton(QG.QIcon(":/find.png"), 'ReFind')
        self.recalc_button.clicked.connect(self.recalculate_locations)

        self.spark_result.setSizePolicy(QW.QSizePolicy.Maximum,
                QW.QSizePolicy.Maximum)

        results_layout.addWidget(self.spark_result,0,0,3,1)
        results_layout.addWidget(self.calculate_spark_properties,0,1)
        results_layout.addWidget(self.calculate_all_spark_properties,1,1)
        results_layout.addWidget(self.accept_button,0,2)
        results_layout.addWidget(results_pb,1,2)
        results_layout.addWidget(self.recalc_button, 2,1)
        select_and_result_layout.addWidget(results_groupbox, 0, QtCore.Qt.AlignHCenter)
        select_and_result_layout.addStretch()

        self.sparkplot = PlotWidget(self)


        spark_plot_layout = QW.QGridLayout()
        interaction_layout.addLayout(spark_plot_layout)
        spark_plot_layout.addWidget(self.sparkplot, 1, 0)
        ver_layout = QW.QVBoxLayout()
        hor_layout = QW.QHBoxLayout()
        self.hor_slider = QW.QSlider(QtCore.Qt.Horizontal)
        self.ver_slider = QW.QSlider(QtCore.Qt.Vertical)
        self.hor_spinner = QW.QSpinBox()
        self.hor_spinner.setStyleSheet("""
        QSpinBox{
            color:purple;
            font-weight:bold;
            }
        """)
        self.ver_spinner = QW.QSpinBox()
        self.ver_spinner.setStyleSheet("""
        QSpinBox{
            color:cornflowerblue;
            color:steelblue;
            font-weight:bold;
            }
        """)
        ver_layout.addWidget(self.ver_slider)
        ver_layout.addWidget(self.ver_spinner)
        hor_layout.addWidget(self.hor_slider)
        hor_layout.addWidget(self.hor_spinner)
        spark_plot_layout.addLayout(ver_layout, 1, 1)
        spark_plot_layout.addLayout(hor_layout, 2, 0)
        vis_options_pb = QW.QToolButton()
        vis_options_pb.clicked.connect(self.show_vis_options_dialog)
        vis_options_pb.setIcon(QG.QIcon('://color_wheel.png'))
        spark_plot_layout.addWidget(vis_options_pb)


        self.left_F0_slider = QW.QSlider(QtCore.Qt.Horizontal)
        self.right_F0_slider = QW.QSlider(QtCore.Qt.Horizontal)
        F0_layout = QW.QHBoxLayout()
        F0_layout.addWidget(QW.QLabel('<b>F0:</b> left:'))
        F0_layout.addWidget(self.left_F0_slider)
        F0_layout.addWidget(QW.QLabel(' right:'))
        F0_layout.addWidget(self.right_F0_slider)

        spark_plot_layout.addLayout(F0_layout,0,0,1,2)
        self.left_F0_slider.valueChanged.connect(self.left_F0_changed)
        self.right_F0_slider.valueChanged.connect(self.right_F0_changed)
        st_span_layout = QW.QGridLayout()
        self.temporal_slice_span_spinb = QW.QSpinBox()
        self.temporal_slice_span_spinb.setMaximum(20)
        st_span_layout.addWidget(QW.QLabel("<b>Slice</b>"),0,0)
        st_span_layout.addWidget(QW.QLabel("<b>Pixels &plusmn;</b>"),0,1)
        st_span_layout.addWidget(QW.QLabel("<b>Physical span</b>"),0,2)
        st_span_layout.addWidget(QW.QLabel("<b>Smoothing</b>"),0,3)
       # self.temporal_slice_span_spinb.setSizePolicy(QG.QSizePolicy.Maximum,QG.QSizePolicy.Maximum)
        st_span_layout.addWidget(QW.QLabel('<p style="background-color:cornflowerblue;font-weight:bold;">Temporal</p>' ),1,0)
        st_span_layout.addWidget(self.temporal_slice_span_spinb, 1, 1)
        self.t_span_label = QW.QLabel('0')
        st_span_layout.addWidget(self.t_span_label, 1, 2)

        self.spatial_slice_span_spinb = QW.QSpinBox()
        self.spatial_slice_span_spinb.setMaximum(20)
        st_span_layout.addWidget(QW.QLabel('<p style="background-color:magenta;font-weight:bold;">Spatial</p> '),2,0)
        st_span_layout.addWidget(self.spatial_slice_span_spinb, 2, 1)
        self.s_span_label = QW.QLabel('0')
        st_span_layout.addWidget(self.s_span_label,2,2)

        self.s_smooth_spinb = QW.QSpinBox()
        self.s_smooth_spinb.setMaximum(10)
        self.s_smooth_spinb.setValue(1)

        #t_smooth_label
        self.t_smooth_spinb = QW.QSpinBox()
        self.t_smooth_spinb.setMaximum(10)
        self.t_smooth_spinb.setValue(1)
        st_span_layout.addWidget(self.s_smooth_spinb, 2, 3)
        st_span_layout.addWidget(self.t_smooth_spinb, 1, 3)
        self.s_smooth_spinb.valueChanged.connect(self.spatial_smoothing_changed)
        self.t_smooth_spinb.valueChanged.connect(self.temporal_smoothing_changed)

        frame = QW.QFrame(self)
        frame.setFrameStyle(QW.QFrame.HLine)
        frame.setFrameShadow(QW.QFrame.Sunken)
        spark_plot_layout.addWidget(frame, 3,0,1,2)
        spark_plot_layout.addLayout(st_span_layout,4,0,1,2)

        self.ver_spinner.valueChanged.connect(self.ver_slider.setValue)
        self.hor_spinner.valueChanged.connect(self.hor_slider.setValue)
        self.ver_slider.valueChanged.connect(self.ver_spinner.setValue)
        self.hor_slider.valueChanged.connect(self.hor_spinner.setValue)
        self.hor_slider.valueChanged.connect(self.sparkplot.move_vline)
        self.ver_slider.valueChanged.connect(self.sparkplot.move_hline)

        self.sparkplot.vlinemoved.connect(self.hor_slider.valueChanged)
        self.sparkplot.hlinemoved.connect(self.ver_slider.valueChanged)
        self.ver_slider.valueChanged.connect(self.ver_slider_changed)
        self.hor_slider.valueChanged.connect(self.hor_slider_changed)

        self.spatial_slice_span_spinb.valueChanged.connect(self.st)
        self.temporal_slice_span_spinb.valueChanged.connect(self.tt)

        #plot first spark

        self.spatial_slice_span_spinb.setValue(3)
        self.temporal_slice_span_spinb.setValue(self.estimate_spatial_span())
        #hack to make sure that the view is resized correctly when shown
        if 0:#self.spark_roi.imagedata.old_blur_image is not None:
            d2 = self.spark_roi.imagedata.old_blur_image
            max_vals = n.where(d2 == d2.max())
            #print 'max blur',max_vals,d2.max()
        else:
            max_vals = n.where(self.spark_roi.data==self.spark_roi.data.max())
            #print 'max',max_vals,self.ds.data.max()


        #QtCore.QTimer.singleShot(20, lambda:self.change_active_spark_region(0))
        self.change_active_spark_region(0)
        #self.recalculate_locations()
        #QtCore.QTimer.singleShot(40, lambda:self.recalculate_locations())
        #main_height = main_layout.sizeHint().height()
        self.fplot_temporal.setSizePolicy(QW.QSizePolicy.Expanding,QW.QSizePolicy.Expanding)
        self.fplot_spatial.setSizePolicy(QW.QSizePolicy.Expanding,QW.QSizePolicy.Expanding)
        QtCore.QTimer.singleShot(50,lambda:self.sparkplot.fitView(0))

    def show_vis_options_dialog(self):
        dialog = QW.QDialog(self)
        layout = QW.QHBoxLayout()
        dialog.setLayout(layout)
        widget = VisualizationOptionsWidget(self.spark_roi, self.sparkplot, parent=dialog)
        layout.addWidget(widget)
        #new_boundary_widget.accept.connect(dialog.accept)
        #new_boundary_widget.cancel.connect(dialog.reject)
        dialog.setModal(False)
        dialog.show()


    def results_table_clicked(self):
        if not self.resultwidget:
            self.resultwidget = SparkResultsWidget(self.sparks, self.imagedata)
            self.parent_tab.addTab(self.resultwidget, 'Results')
            self.parent_tab.resultTab = self.resultwidget
        index = self.parent_tab.indexOf(self.resultwidget)
        self.parent_tab.setCurrentIndex(index)
    def activate_next_spark(self):
        self.spark_select_combobox.setCurrentIndex(self.active_roi + 1)

    def activate_previous_spark(self):
        self.spark_select_combobox.setCurrentIndex(self.active_roi - 1)

    def accept_toggled(self, accepted):
        state = not accepted
        if accepted:
            self.accept_button.setIcon(QG.QIcon(":/lock.png"))
        else:
            self.accept_button.setIcon(QG.QIcon(":/lock_open.png"))
        self.right_F0_slider.setEnabled(state)
        self.left_F0_slider.setEnabled(state)
        self.hor_slider.setEnabled(state)
        self.ver_slider.setEnabled(state)
        self.spatial_slice_span_spinb.setEnabled(state)
        self.temporal_slice_span_spinb.setEnabled(state)
        self.ver_spinner.setEnabled(state)
        self.hor_spinner.setEnabled(state)
        self.recalc_button.setEnabled(state)
        self.sparkplot.accept_input(state)
        self.spark_roi.set_approved(accepted)
        self.spark_select_combobox.setItemIcon(self.spark_rois.index(self.spark_roi),
                self.spark_roi.icon)

    def find_index(self, val):
        axis_data = self.spark_roi.temporal_axis_data
        for i in range(len(axis_data)-1):
            if axis_data[i+1]>val and axis_data[i]<=val:
                return i
        if val < self.spark_roi.temporal_axis_data[0]:
            return 0
        elif val >  self.spark_roi.temporal_axis_data[-1]:
            return len(self.spark_roi.temporal_axis_data) - 1



    def analyze_all_sparks(self):
        rows = self.selection_datamodel.rowCount(None)
        for row in range(rows):
            index = self.selection_datamodel.index(row)
            print index
            self.selection_widget.set_index(index)
            self.change_active_spark(index)
            self.analyze_spark()

    def analyze_spark(self):
        if self.active_boundary_index is not None:
            boundary = self.roi_manager.selections[self.active_boundary_index]
            x1 = boundary.graphic_item.rect().left()
            x2 = boundary.graphic_item.rect().right()
            start_x = self.fplot_temporal.scene2data((min(x1, x2), 0)).x()
            end_x = self.fplot_temporal.scene2data((max(x1, x2), 0)).x()
            self.spark = self.spark_roi.make_spark(start_x, end_x)
            self.spark.result_update.connect(self.update_resultswidget)
            self.spark.set_number(self.spark_roi_number + 1,
                                  self.active_boundary_index + 1)
            self.spark.analyze()

            location_h = self.hor_slider.value()
            location_v =  self.ver_slider.value()
            located_spark = LocatedSpark(self.spark, location_h, location_v)
            self.located_sparks[boundary] = located_spark
            self.sparks[self.spark_roi_number][boundary] = self.spark
            if self.resultwidget:
                self.resultwidget.update(self.sparks)

        else:
            print 'fail'


    def left_F0_changed(self, value):
        self.sparkplot.F0_changed(value, None)
        self.spark_roi.F0_left = value
        self.replot()
        self.right_F0_slider.setMinimum(value + 1)

    def right_F0_changed(self, value):
        self.sparkplot.F0_changed(None, value)
        self.spark_roi.F0_right = value
        self.replot()
        self.left_F0_slider.setMaximum(value - 1)
    def replot(self):
        if self.temporal_plotted and self.spatial_plotted:
            self.plot_spatial()
            self.plot_temporal()

    def estimate_spatial_span(self):
        pixelsize = self.spark_roi.pixel_size
        span_needed = 1.0 #um
        n = int(round((span_needed / pixelsize -1.)/2.))
        return n

    def recalculate_locations(self):
        new_max, new_max_h = self.get_max_spatial_loc()
        if new_max:
            QtCore.QTimer.singleShot(12,
                    lambda:self.ver_slider.setValue(new_max))
            QtCore.QTimer.singleShot(13,
                    lambda:self.hor_slider.setValue(new_max_h))
        return

    def get_max_spatial_loc(self, left = None, right = None):
        halfspan = self.temporal_slice_span_spinb.value()
        rows = self.spark_roi.data.shape[0]
        max_val = 0.0
        max_index = None
        max_index_horizontal = None
        for vloc in range(halfspan+1,rows-halfspan+1):
            data_slice = self.spark_roi.data[vloc-halfspan-1:vloc+halfspan, :]
            data = data_slice.sum(axis=0)/(1.+2*halfspan)
            if data.max() > max_val:
                max_index = vloc
                max_val = data.max()
                if left is None and right is None:
                    max_index_horizontal = data.argmax()
                else:
                    max_index_horizontal = data[left:right].argmax()

        return rows-max_index, max_index_horizontal


    def st(self, number):
        shape = self.spark_roi.data.shape

        self.hor_slider.setMaximum(shape[1] - self.spatial_slice_span_spinb.value()-1)
        self.hor_spinner.setMaximum(shape[1] - self.spatial_slice_span_spinb.value()-1)
        print '\n\n\n ST max',shape[1] - self.spatial_slice_span_spinb.value()-1, self.hor_spinner.maximum()
        self.hor_slider.setMinimum(self.spatial_slice_span_spinb.value()+1)
        self.hor_spinner.setMinimum(self.spatial_slice_span_spinb.value()+1)
        if self.spatial_plotted:
            self.sparkplot.move_vbox(number)
            self.plot_spatial()
        self.s_span_label.setText("%.3f <i>ms</i>"%((2*number+1)*self.spark_roi.time_interval*1000))

    def tt(self, number):
        shape = self.spark_roi.data.shape
        self.ver_slider.setMaximum(shape[0]-self.temporal_slice_span_spinb.value()-1)
        self.ver_slider.setMinimum(self.temporal_slice_span_spinb.value()+1)
        self.ver_spinner.setMaximum(shape[0]-self.temporal_slice_span_spinb.value()-1)
        self.ver_spinner.setMinimum(self.temporal_slice_span_spinb.value()+1)
        if self.temporal_plotted:
            self.sparkplot.move_hbox(number)
            self.plot_temporal()
        self.t_span_label.setText("<b></b>%.3f <i>&mu;m</i>"%((2*number+1)*self.spark_roi.pixel_size))
        return

    def ver_slider_changed(self, value):
        if self.temporal_plotted:
            self.plot_temporal()
        else:
            pass
        return

    def hor_slider_changed(self, value):
        if self.spatial_plotted:
            self.plot_spatial()
        else:
            pass
        return

    def temporal_smoothing_changed(self, value):
        self.ver_slider_changed(value)

    def spatial_smoothing_changed(self, value):
        self.hor_slider_changed(value)

    def update_resultswidget(self):
        #isinstance(self.spark, Spark)
        if self.spark.decay_constant:
            self.spark_result.decay_label.setText("%.2f ms"%self.spark.decay_constant)
        if self.spark.max_val:
            self.spark_result.amp_label.setText("%.3f"%(self.spark.max_val))
        if self.spark.risetime:
            self.spark_result.risetime_label.setText("%.1f ms"%self.spark.risetime)
            self.spark_result.baseline_label.setText("%.2f "%self.spark.baseline)
        if self.spark.FDHM:
            self.spark_result.FDHM_label.setText("%.1f ms"%self.spark.FDHM)
            self.spark_result.time_at_max_label.setText("%.1f ms"%self.spark.FDHM_location)
            self.fplot_temporal.plot_FDHM(self.spark)
        if self.spark.FWHM:
            self.spark_result.FWHM_label.setText("<b></b>%.1f &mu;m"%self.spark.FWHM)
            self.spark_result.location_at_max_label.setText("<b></b>%.1f &mu;m"%self.spark.FWHM_max_location)
            self.fplot_spatial.plot_FWHM(self.spark)
        self.spark_result.spark_name_label.setText("%s"%self.spark.name)
        self.spark_result.setVisible(True)

    def update_spatial_slice_coords(self, xv, yv, xs, ys):
        #print 'ups','x: %.3f [ms], : %.3f [um], sx: %i, sy: %i'%(xv, yv, xs, ys)
        pass
        #self.status.showMessage('x: %.2f [um], dF/F0: %.2f'%(xv, yv))
        #self.emit(QC.SIGNAL('positionTXT(QString)'),'x: %.3f [um], y: %.2f [ms], sx: %i, sy: %i'%(xv,yv,xs,ys))

    def update_temporal_slice_coords(self, xv, yv, xs, ys):
        #print 'upt','x: %.3f [ms], y: %.3f [um], sx: %i, sy: %i'%(xv, yv, xs, ys)
        pass
        #self.status.showMessage('x: %.2f [ms], dF/F0: %.2f'%(xv, yv))
        #self.emit(QC.SIGNAL('positionTXT(QString)'),'x: %.3f [ms], y: %.2f [um], sx: %i, sy: %i'%(xv,yv,xs,ys))
