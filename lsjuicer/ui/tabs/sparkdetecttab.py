import PyQt4.QtCore as QC
import PyQt4.QtGui as QG
import numpy

from lsjuicer.data.pipes.tools import PipeChain
from lsjuicer.data.data import PixmapMaker
from lsjuicer.static.constants import ImageSelectionTypeNames as ISTN
from lsjuicer.ui.widgets.plot_with_axes_widget import DiscontinousPlotWidget, SparkFluorescencePlotWidget
from lsjuicer.util import helpers
from lsjuicer.ui.scenes import FDisplay
from lsjuicer.data.spark import SparkData
from lsjuicer.ui.tabs.resulttab import SparkResultsWidget
from lsjuicer.data.data import ImageDataMaker
from lsjuicer.ui.widgets.smallwidgets import VisualizationOptionsWidget
from lsjuicer.inout.db.sqlbase import dbmaster
from lsjuicer.inout.db.sqla import SearchRegion, Spark

from scipy import ndimage as sn
#from skimage.morphology import watershed, is_local_maximum

def dic2str(dic):
    return "\n".join(["%s: %.3f"%(key,dic[key]) for key in dic.keys()])

class SparkDataDialog(QG.QDialog):
    def __init__(self, spark, parent = None):
        super(SparkDataDialog, self).__init__(parent)
        layout = QG.QFormLayout()
        self.setLayout(layout)
        digits = 5
        temporal_F_field = QG.QPlainTextEdit(
                "["+helpers.list_2_str(spark.temporal_smooth_data.tolist(),digits)+"]")
        temporal_F_field.setTextInteractionFlags(QC.Qt.TextSelectableByMouse)
        temporal_t_field = QG.QPlainTextEdit(
                "["+helpers.list_2_str(spark.temporal_x_phys.tolist(),digits)+"]")
        temporal_t_field.setTextInteractionFlags(QC.Qt.TextSelectableByMouse)
        temporal_fit_field = QG.QPlainTextEdit(
                dic2str(spark.transient.params))
        temporal_fit_field.setTextInteractionFlags(QC.Qt.TextSelectableByMouse)
        spatial_F_field = QG.QPlainTextEdit(
                "["+helpers.list_2_str(spark.spatial_smooth_data.tolist(),digits)+"]")
        spatial_F_field.setTextInteractionFlags(QC.Qt.TextSelectableByMouse)
        spatial_y_field = QG.QPlainTextEdit(
                "["+helpers.list_2_str(spark.spatial_axis_data.tolist(),digits)+"]")
        spatial_y_field.setTextInteractionFlags(QC.Qt.TextSelectableByMouse)
        spatial_fit_field = QG.QPlainTextEdit(
                dic2str(spark.spatial_profile.params))
        spatial_fit_field.setTextInteractionFlags(QC.Qt.TextSelectableByMouse)
        layout.addRow("Temporal:: F", temporal_F_field)
        layout.addRow("Temporal:: time:", temporal_t_field)
        layout.addRow("Temporal:: fit:", temporal_fit_field)
        layout.addRow("Spatial:: F:", spatial_F_field)
        layout.addRow("Spatial:: space:", spatial_y_field)
        layout.addRow("Spatial:: fit:", spatial_fit_field)

#class SaveSparksDialog(QG.QDialog):
#    def __init__(self, no_of_sparks, parent = None, new = True):
#        super(SaveSparksDialog, self).__init__(parent)
#        layout = QG.QVBoxLayout()
#        self.setLayout(layout)
#        location_layout = QG.QHBoxLayout()
#        location_layout.addWidget(QG.QLabel("Saving %i sparks to:"%no_of_sparks))
#        self.save_folder_name = None
#        self.location_label = QG.QLabel()
#        location_layout.addWidget(self.location_label)
#        location_change_pb = QG.QPushButton("Change folder")
#        location_layout.addWidget(location_change_pb)
#        layout.addLayout(location_layout)
#        location_change_pb.clicked.connect(self.choose_folder)
#
#        exp_type_layout = QG.QHBoxLayout()
#        exp_type_layout.addWidget(QG.QLabel('Experiment type:'))
#
#
#        exp_type_layout.addWidget(self.exp_type_combo)
#
#        layout.addLayout(exp_type_layout)
#
#        button_layout = QG.QHBoxLayout()
#        self.save_pb = QG.QPushButton("Save")
#        cancel_pb = QG.QPushButton("Cancel")
#        button_layout.addWidget(self.save_pb)
#        button_layout.addWidget(cancel_pb)
#        self.save_pb.clicked.connect(self.accept)
#        cancel_pb.clicked.connect(self.reject)
#
#        comment_layout = QG.QHBoxLayout()
#        comment_layout.addWidget(QG.QLabel("Comment"))
#        self.comment_box = QG.QLineEdit()
#        if not new:
#            try:
#                key ='comment'
#                #comment = Config.get_property(key)
#                #self.comment_box.setText(comment)
#            except KeyError:
#                pass
#        comment_layout.addWidget(self.comment_box)
#        layout.addLayout(comment_layout)
#        layout.addLayout(button_layout)
#
#        self.set_location_label()
#
#    def choose_folder(self):
#        folder = self.choose_folder_dialog()
#        self.save_folder_name = folder
#        self.set_location_label()
#
#    def choose_folder_dialog(self):
#        save_folder_name = QG.QFileDialog.getExistingDirectory(self)
#        return save_folder_name
#
#    def set_location_label(self):
#        if self.save_folder_name:
#            self.location_label.setText(self.save_folder_name)
#            self.save_pb.setEnabled(True)
#        else:
#            self.location_label.setText("---")
#            self.save_pb.setEnabled(False)
#
#    def accept(self):
#        self.exp_type = self.exp_type_combo.currentText()
#        #Config.set_property('exp_type',self.exp_type)
#        self.comment = self.comment_box.text()
#        #Config.set_property('comment', self.comment)
#        return QG.QDialog.accept(self)

class SparkROIGraphicItem(object):
    def __init__(self, plot, rect, loc_x,loc_y, h_span, v_span, d_mask,m_mask):
        self.fscene = plot.fscene
        self.plot = plot
        self.spark_roi = self.makeSparkROI(rect, loc_x,loc_y, h_span, v_span)
        self.normal_pen = QG.QPen(QG.QColor('black'))
        self.active_pen = QG.QPen(QG.QColor('white'))
        self.active_pen.setWidth(2)
        self.active_pen.setCosmetic(True)
        self.d_mask = d_mask
        self.m_mask = m_mask
        #self.d_pixmap = helpers.make_mask_pixmap(self.d_mask, 'green')
        #self.d_pixmap_item = self.fscene.addPixmap(self.d_pixmap)
        #self.d_pixmap_item.setPos(rect.left(), rect.top())
        #self.m_pixmap = helpers.make_mask_pixmap(self.m_mask, 'white')
        #self.m_pixmap_item = self.fscene.addPixmap(self.m_pixmap)
        #self.m_pixmap_item.setPos(rect.left(), rect.top())

    def makeSparkROI(self, rect, loc_x, loc_y, h_span, v_span):
        group = QG.QGraphicsItemGroup()
        self.fscene.addItem(group)
        #self.ROI_rect = self.plot.makeRect(rect)
        #c = self.makeCircle(loc_x, loc_y)
        hr = QC.QRectF(rect.left(), loc_y - v_span, rect.width(), v_span*2+1)
        vr = QC.QRectF(loc_x - h_span,rect.top(), h_span*2+1,rect.height())
        self.ROI_hrect = self.plot.makeRect(hr)
        self.ROI_vrect = self.plot.makeRect(vr)
        #group.addToGroup(self.ROI_rect)
        #group.addToGroup(c)
        group.addToGroup(self.ROI_hrect)
        group.addToGroup(self.ROI_vrect)
        group.setZValue(100)
        return group

    def active_look(self, enable):
        if enable:
            pen = self.active_pen
        else:
            pen = self.normal_pen
        #self.ROI_rect.setPen(pen)
        self.ROI_hrect.setPen(pen)
        self.ROI_vrect.setPen(pen)

    def __del__(self):
        print 'deleting',self
        self.fscene.removeItem(self.spark_roi)
        #self.fscene.removeItem(self.d_pixmap_item)
        #self.fscene.removeItem(self.m_pixmap_item)
        super(SparkROIGraphicItem, self).__del__()

class SparkRegionsTab(QG.QTabWidget):
    def __init__(self, rois, imagedata, analysis, parent = None):
        super(SparkRegionsTab, self).__init__(parent)
        for i,roi in enumerate(rois[ISTN.ROI]):

            tab = SparkDetectTab(roi, imagedata, analysis, self)
            self.addTab(tab, "Region %i"%i)
            tab.saved.connect(self.tab_saved)
        self.currentChanged.connect(self.tab_changed)

    def tab_saved(self):
        sender = self.sender()
        index = self.indexOf(sender)
        print 'saved signal sent by', sender,index
        self.setTabIcon(index, QG.QIcon(":/report_disk.png"))

    def tab_changed(self, index):
        #force refit of the sparkdetecttab just made active
        w = self.currentWidget()
        w.fit_sparkregion_plot()

def dict_float(dict_in):
    out = {}
    for key in dict_in:
        out[key] = float(dict_in[key])
    return out

class SparkDetectTab(QG.QTabWidget):
    saved = QC.pyqtSignal()
    def __init__(self, roi, imagedata, analysis, parent = None):
        super(SparkDetectTab, self).__init__(parent)
        channel = 0
        self.analysis = analysis

        self.d_graphicpixmapitem = None

        self.m_graphicpixmapitem = None

        #fname = imagedata.ome_sha1
        #self.mycount = SparkDetectTab.roi_count[fname]
        self.image_shown = False
        self.sparks = {}
        self.sparks_plotted = []
        self.spark_no = None
        self.spark_stack_relation = {}
        self.roi = roi
        print "roi is",self.roi
        r = roi.graphic_item.rect()
        r_r = [min(int(r.x()), int(r.x()+r.width())),
                max(int(r.x()), int(r.x()+r.width())),
                min(int(r.y()), int(r.y()+r.height())),
                max(int(r.y()), int(r.y()+r.height()))]
        self.coords = r_r
        l,r,b,t = self.coords
        self.load_saved = False

        self.search_region = None
        for search_region in self.analysis.searchregions:
            if search_region.check_coords(self.coords):
                self.load_saved = True
                self.search_region = search_region
                break


        self.imagedata = ImageDataMaker.from_imagedata(imagedata, cut=(l, r, b, t))
        self.data = self.imagedata.all_image_data[channel]
        self.xvals = self.imagedata.xvals
        self.yvals = self.imagedata.yvals

        pc = PipeChain(self.imagedata.pixel_size)
        pc.set_source_data(self.data)
        pc.pipe_state_changed.connect(self.force_new_pixmap)
        self.pipechain = pc
        pixmaker = PixmapMaker(pc)
        self.pixmaker = pixmaker
        self.setup_ui()
        self.force_new_pixmap()
        print "\n\n\n\n", self.size()
        #QC.QTimer.singleShot(250,lambda :self.find_sparks())

    @helpers.timeIt
    def find_sparks(self):
        if self.sparks:
            self.delete_all_sparks()
        treshold = self.treshold_spinbox.value()
        delta_f_treshold = self.delta_f_spinbox.value()
        area_treshold = self.area_spinbox.value()


        self.sparkfinder = SparkFinder(self.imagedata, treshold, area_treshold)

        #calculate the pixel sizes needed to match
        #physical blur sizes given above
        #uniform_blur_temporal = int(round(\
        #        uniform_blur_temporal_size/(self.imagedata.delta_time)))
        #uniform_blur_spatial = int(round(\
        #        uniform_blur_spatial_size/(self.imagedata.delta_space)))
        #uniform_blur_size = (uniform_blur_spatial, uniform_blur_temporal)

        #gaussian_blur_temporal = gaussian_blur_temporal_size/\
        #        (self.imagedata.delta_time)
        #gaussian_blur_spatial = gaussian_blur_spatial_size/\
        #        (self.imagedata.delta_space)
        #gaussian_blur_size = (gaussian_blur_spatial, gaussian_blur_temporal)
        #print 'blur params: uniform %s, gaussian %s'\
        #        %(str(uniform_blur_size), str(gaussian_blur_size))
        spark_coords, spark_max_area_coords,\
                adj_mean, max_mask, dilated_mask = self.sparkfinder.get_sparks()
        spark_rois = {}
        dilated_mask_with_holes = dilated_mask - max_mask
        #print dilated_mask_with_holes,max_mask,dilated_mask
        d_pix=helpers.make_mask_pixmap_cm(dilated_mask_with_holes,'prism')
        m_pix=helpers.make_mask_pixmap(max_mask,'white')
        spark_max_rois  = {}
        sparkROIGIs = {}
        spark_datas =  {}
        sparks = {}
        for spark_no in spark_coords:
            print '\n\nSPARK NO:%i'%spark_no

            l = spark_coords[spark_no]['left']
            r = spark_coords[spark_no]['right']
            t = spark_coords[spark_no]['top']
            b = spark_coords[spark_no]['bottom']

            roi = [l,r,b,t]
            rect = QC.QRectF(l, b, r-l, t-b)

            #separate roi for finding the maximum of the spark
            #this is needed in cases where a dim spark is close to
            #a bright one and would otherwise find the bright max
            #for its amplitude
            ml = spark_max_area_coords[spark_no]['left']
            mr = spark_max_area_coords[spark_no]['right']
            mt = spark_max_area_coords[spark_no]['top']
            mb = spark_max_area_coords[spark_no]['bottom']

            mroi = [ml,mr,mb,mt]
            mrect = QC.QRectF(ml,mb, mr-ml, mt-mb)
            print l,r,t,b
            print 'ROI', roi, rect
            print ml,mr,mt,mb
            print 'MROI', mroi, mrect
            print 'valid', rect.contains(mrect)
            #print spark_no,rect,self.sparkfinder.blurred_data,self.sparkfinder.data
            spark_data = SparkData(self.imagedata, roi,
                    im_mean = adj_mean,
                    new_image =self.sparkfinder.blurred_data,
                    max_roi = mroi, max_mask = max_mask,
                    dilated_mask = dilated_mask,
                    raw_data = self.data)
            #spark_data = SparkData(self.imagedata, roi)

            try:
                spark_data.spatial_smoothing = 0
                spark_data.temporal_smoothing = 0
                spark_data.h_halfspan = spark_data.estimate_temporal_span()
                spark_data.v_halfspan = spark_data.estimate_spatial_span()
            except ValueError:
                print 'cannot set smoothing or halfspan'
                continue
            #horizonta = spatial
            #vertical = temporal
            v_loc, h_loc = spark_data.get_max_loc()
            #self.sparksplot.makeCircle(l+h_loc, b+v_loc)
            #m,s=spark_data.estimate_sparkyness()
            #means.append(m)
            #stds.append(s)
            #print 'max loc ',v_loc, h_loc
            try:
                spark_data.v_loc = v_loc
                spark_data.h_loc = h_loc
            except ValueError:
                print 'cannot set vloc or hloc. skipping spark'
                continue
            try:
                spark = spark_data.make_spark()
            except:
                import traceback
                traceback.print_exc()
                continue
            #    import pickle
            #    pf = open('simage.p','w')
            #    pickle.dump(self.sparkfinder.blurred_data,pf)
            #    pickle.dump(dilated_mask,pf)
            #    pickle.dump(max_mask,pf)
            #    pickle.dump(spark_coords,pf)
            #    pickle.dump(spark_data.data,pf)
            #    pf.close()
            #    raise RuntimeError
            if spark.get_delta_f()<delta_f_treshold:
                print 'skip', spark_no, spark.get_delta_f()
                #pdb.set_trace()
                continue
            else:
                spark.analyze()
                #sparkROIGI = SparkROIGraphicItem(self.sparksplot, mrect, ml+h_loc,
                #        mb+v_loc, spark_data.h_halfspan,
                #        spark_data.v_halfspan)
                sparkROIGI = SparkROIGraphicItem(self.sparksplot, rect, l+h_loc,
                        b+v_loc, spark_data.h_halfspan,
                        spark_data.v_halfspan, spark_data.dilated_mask, spark_data.max_mask)
                sparkROIGIs[spark_no] = sparkROIGI
                #spark_data.set_spatial_data()
                #spark_data.set_temporal_data()
                #plot sparks
                #r = self.sparksplot.makeRect(rect)
                #spark_rois[spark_no] = r
                spark_datas[spark_no] = spark_data
                sparks[spark_no] = spark
                spark.set_number(spark_no)

        self.pipechain.set_source_data(self.sparkfinder.blurred_data)
        self.make_new_pixmap()
        self.spark_datas = spark_datas
        self.sparks = sparks
        self.sparkROIGIs =sparkROIGIs
        self.sparkresult.update(self.sparks)
        if self.d_graphicpixmapitem:
            self.sparksplot.fscene.removeItem(self.d_graphicpixmapitem)
            self.sparksplot.fscene.removeItem(self.m_graphicpixmapitem)
        self.d_graphicpixmapitem = self.sparksplot.fscene.addPixmap(d_pix)
        self.m_graphicpixmapitem = self.sparksplot.fscene.addPixmap(m_pix)
        self.d_graphicpixmapitem.setZValue(5)
        self.m_graphicpixmapitem.setZValue(6)

        #from IPython.frontend.terminal.embed import InteractiveShellEmbed
        #from IPython import embed_kernel
        ##QC.pyqtRemoveInputHook()
        #ipshell=InteractiveShellEmbed()
        #ipshell()
        #embed_kernel()

    def load_sparks(self):
        region_sparks = self.search_region.sparks
        self.sparks = {}
        spark_pen = QG.QPen(QG.QColor("white"))
        spark_pen.setWidth(5)
        spark_pen.setCosmetic(True)
        for saved_spark in region_sparks:
            self.sparks[saved_spark.id] = saved_spark
            rect = saved_spark.get_qrectf()
            print "rect is ", rect
            r = self.sparksplot.fscene.addRect(rect, spark_pen)
            r.setZValue(100)
        self.sparkresult.update(self.sparks)
        self.save_label.setText('<html style="background:green;">%i sparks loaded</html>'%len(self.sparks))


    def show_sparks(self, sparklist, notify = False):
        """
        Make sparks in sparklist visible

        Args:
            notify: True if sparkresult view should be notified about the change in selection.
                    By default the sparkresult calls this function and does not need to be notified.

        """
        #show the last spark in the sparklist in the plots
        self.show_spark(sparklist[-1], notify)
        #make them look active. sparks not in sparklist make look inactive
        for spark_no in self.sparks:
            sparkROIGI = self.sparkROIGIs[spark_no]
            if spark_no in sparklist:
                sparkROIGI.active_look(True)
                self.sparksplot.center_graphicsitem(sparkROIGI.spark_roi)
            else:
                sparkROIGI.active_look(False)

    def show_spark(self, spark_no, notify):
        number = spark_no
        self.spark_no = spark_no
        self.spark_roi = self.spark_datas[spark_no]
        self.spark  = self.sparks[spark_no]
        if spark_no == len(self.sparks) - 1:
            self.next_spark_pb.setEnabled(False)
            self.previous_spark_pb.setEnabled(True)
        elif spark_no == 0:
            self.next_spark_pb.setEnabled(True)
            self.previous_spark_pb.setEnabled(False)
        else:
            self.next_spark_pb.setEnabled(True)
            self.previous_spark_pb.setEnabled(True)
        if notify:
            self.sparkresult.set_selected(spark_no)
        if number in self.sparks_plotted:
            stack_number = self.spark_stack_relation[number]
            self.fplot_temporal = self.temporal_stack.widget(stack_number)
            self.fplot_spatial = self.spatial_stack.widget(stack_number)
            self.temporal_plotted = True
            self.spatial_plotted = True
        else:
            self.fplot_temporal = SparkFluorescencePlotWidget(sceneClass =
                    FDisplay, antialias = True, parent = self.temporal_stack)
            #self.fplot_temporal.updateLocation.connect(self.update_temporal_slice_coords)
            self.fplot_spatial = SparkFluorescencePlotWidget(sceneClass =
                    FDisplay, antialias = True, parent = self.spatial_stack)
            #self.fplot_spatial.updateLocation.connect(self.update_spatial_slice_coords)


            stack_number = self.temporal_stack.addWidget(self.fplot_temporal)
            self.spatial_stack.addWidget(self.fplot_spatial)
            self.sparks_plotted.append(number)
            self.spark_stack_relation[number] = stack_number
        self.temporal_stack.setCurrentIndex(stack_number)
        self.spatial_stack.setCurrentIndex(stack_number)
        self.plot_temporal()
        self.plot_spatial()

    def show_spark_data(self):
        dialog = SparkDataDialog(self.spark, parent=self)
        dialog.exec_()

    def save_sparks(self):
        if not self.sparks:
            return
        sparks = []
        search_region = SearchRegion()
        l,r,b,t = self.coords
        search_region.analysis = self.analysis
        search_region.set_coords(self.coords)
        search_region.x0 = 10
        for spark_no in self.sparks:
            spark = self.sparks[spark_no]
            db_spark = Spark()
            db_spark.fwhm = spark.FWHM
            db_spark.fdhm = spark.FDHM
            db_spark.val_at_max = spark.max_val
            db_spark.time_at_max = spark.max_time
            db_spark.loc_at_max = spark.max_location
            db_spark.baseline = spark.baseline
            db_spark.risetime = spark.risetime
            db_spark.decay_constant = spark.decay_constant
            db_spark.temporal_fit_params = dict_float(spark.transient.params)
            db_spark.temporal_fit_fun=spark.transient.fit_function.__name__
            db_spark.spatial_fit_params = dict_float(spark.spatial_profile.params)
            db_spark.spatial_fit_fun=spark.spatial_profile.fit_function.__name__
            db_spark.region = search_region
            db_spark.set_coords(spark.coords)
        #try to get analysis session
        session = dbmaster.object_session(self.analysis)
        if session is None:
            session = dbmaster.get_session()
            session.add(self.analysis)
        session.add(search_region)
        for spark in sparks:
            session.add(spark)
        print 'new', session.new
        print 'dirty', session.dirty
        #dbmaster.end_session(session)
        self.roi.set_state('saved')
        count = len(self.sparks)
        self.save_label.setText('<html style="background:lime;">%i sparks saved</html>'%len(self.sparks))
        self.saved.emit()
        session.commit()

    #def save_sparks_old(self):
    #    count = len(self.sparks)
    #    dialog = SaveSparksDialog(count, parent=self)
    #    if dialog.exec_():
    #        fname = self.imagedata.ome_sha1
    #        save_folder_name = str(dialog.save_folder_name)
    #        exp_type = str(dialog.exp_type)

    #        fname_shelf = os.path.join(save_folder_name, fname+".shelf")
    #        try:
    #            shelf = shelve.open(fname_shelf, writeback = True)
    #        except:
    #            QG.QMessageBox.warning(self,'Error',"Problem with saving file.")
    #            return
    #        print 'saving %i sparks to'%count, save_folder_name, exp_type
    #        self.save_label.setText("%i sparks saved"%count)
    #        #roi_no = SparkDetectTab.roi_count[fname]
    #        roi_no = self.mycount
    #        save_sparks = {}
    #        for spark_no in self.sparks:
    #            spark = self.sparks[spark_no]
    #            save_sparks[spark_no] = SparkResult(spark).data
    #        data = {}
    #        data['Sparks'] = save_sparks
    #        data['Comment'] = str(dialog.comment)
    #        data['Save date'] = datetime.datetime.now()
    #        data['ROI_cords'] = self.coords
    #        data['detection'] = {'min_area':self.area_spinbox.value(),
    #                'min_df':self.delta_f_spinbox.value(),
    #                'treshold':self.treshold_spinbox.value()}
    #
    #        #check if any sparks have been saved for this file
    #        if not shelf.has_key('Sparks'):
    #            shelf['Sparks'] = {}

    #        spark_data = shelf['Sparks']
    #        #check if any sparks were saved for this roi
    #        if roi_no in spark_data:
    #            print "WARNING: overwriting spark data"
    #            print "%i sparks exist for ROI %i"%(len(spark_data[roi_no]['Sparks']), roi_no)
    #            print "%i sparks will be inserted instead"%(len(save_sparks))
    #        else:
    #            pass
    #            # if this is the first save for this roi then increment roi count for the file
    #        spark_data[roi_no] = data
    #        if not shelf.has_key('Type'):
    #            #only save image info on the first save
    #            shelf['Type'] = exp_type
    #            #shelf['Acquisition date'] = self.imagedata.readers[0].datetime
    #            shelf['Image name']= self.imagedata.name
    #            #shelf['Full image name'] = self.imagedata.readers[0].filename
    #            shelf['Image width']= self.imagedata.x_points
    #            shelf['Image height'] = self.imagedata.y_points
    #            shelf['Image notes'] = self.imagedata.notes
    #            shelf['Image info text'] = self.imagedata.info_txt
    #            shelf['dy'] = self.imagedata.delta_space
    #            shelf['dx'] = self.imagedata.delta_time
    #            shelf['sha1'] = fname
	#    #print shelf
	#    #keys = shelf.keys()
	#    #for k in keys:
	#    #		print k, shelf[k]
    #        shelf.close()

        #fname_csv = os.path.join(dirname,fname+".csv")
    def delete_all_sparks(self):
        spark_numbers = self.sparks.keys()
        for s in spark_numbers:
            del(self.sparks[s])
            del(self.spark_datas[s])
            del(self.sparkROIGIs[s])
        self.sparkresult.update(self.sparks)

    def delete_selected_sparks(self):
        selected=self.sparkresult.get_selected_spark_numbers()
        for s in selected:
            del(self.sparks[s])
            del(self.spark_datas[s])
            del(self.sparkROIGIs[s])
        self.sparkresult.update(self.sparks)

    def setup_ui(self):
        main_layout = QG.QGridLayout()
        self.setLayout(main_layout)
        #label = QG.QLabel('sparks')
        self.sparksplot = DiscontinousPlotWidget(self)
        main_layout.addWidget(self.sparksplot,0,0)
        main_layout.setRowStretch(0,1)
        main_layout.setRowStretch(1,3)

        bottom_layout = QG.QGridLayout()
        self.sparkresult=SparkResultsWidget(None, self.imagedata)
        self.sparkresult.sparks_active.connect(self.show_sparks)
        bottom_layout.addWidget(self.sparkresult, 0,0)
        interaction_layout = QG.QVBoxLayout()

        detection_layout = QG.QHBoxLayout()
        deltaf_treshold_layout = QG.QHBoxLayout()
        deltaf_treshold_layout.addWidget(QG.QLabel('<b>Minimum &Delta;F</b>:'))
        delta_f_spinbox = QG.QDoubleSpinBox()
        delta_f_spinbox.setDecimals(2)
        delta_f_spinbox.setMinimum(0.00)
        delta_f_spinbox.setMaximum(2.0)
        delta_f_spinbox.setValue(0.25)
        delta_f_spinbox.setSingleStep(0.05)
        deltaf_treshold_layout.addWidget(delta_f_spinbox)
        self.delta_f_spinbox = delta_f_spinbox
        interaction_layout.addLayout(deltaf_treshold_layout)

        detection_layout.addWidget(
                QG.QLabel('<b>Detection treshold (value &times; SD):</b>'))
        treshold_spinbox = QG.QDoubleSpinBox()
        treshold_spinbox.setDecimals(1)
        treshold_spinbox.setMinimum(2.0)
        treshold_spinbox.setMaximum(6.0)
        treshold_spinbox.setValue(3.8)
        treshold_spinbox.setSingleStep(0.1)
        self.treshold_spinbox =treshold_spinbox
        detection_layout.addWidget(treshold_spinbox)


        area_treshold_layout = QG.QHBoxLayout()
        area_treshold_layout.addWidget(
                QG.QLabel('<b>Minimum ROI area [&mu;m &times; ms]:</b>'))
        area_spinbox = QG.QSpinBox()
        area_spinbox.setMinimum(20)
        area_spinbox.setMaximum(100)
        area_spinbox.setValue(20)
        area_spinbox.setSingleStep(2)
        area_treshold_layout.addWidget(area_spinbox)
        self.area_spinbox = area_spinbox
        interaction_layout.addLayout(area_treshold_layout)


        find_pb = QG.QPushButton(QG.QIcon(":/find.png"),'Find sparks')
        delete_pb = QG.QPushButton(QG.QIcon(":/delete.png"),'Remove selected sparks')
        save_pb = QG.QPushButton(QG.QIcon(":/report_disk.png"),'Save spark data')
        show_mask_pb = QG.QPushButton('Show spark masks')
        show_data_pb = QG.QPushButton(QG.QIcon(":/report.png"),'Show spark data')
        next_spark_pb = QG.QPushButton(QG.QIcon(":/arrow_right.png"), 'Next spark')
        previous_spark_pb = QG.QPushButton(QG.QIcon(":/arrow_left.png"),'Previous spark')
        visualization_options_pb = QG.QPushButton(QG.QIcon(":/color_wheel.png"),'Visualization')

        find_pb.clicked.connect(lambda x:self.find_sparks())
        interaction_layout.addLayout(detection_layout)
        pb_layout = QG.QVBoxLayout()
        pb_layout_1= QG.QHBoxLayout()
        pb_layout_2= QG.QHBoxLayout()
        pb_layout.addLayout(pb_layout_1)
        pb_layout.addLayout(pb_layout_2)
        interaction_layout.addLayout(pb_layout)
        interaction_widget = QG.QWidget(self)
        interaction_widget.setLayout(interaction_layout)
        bottom_layout.addWidget(interaction_widget, 1,0)
        visualization_options_pb.clicked.connect(self.show_vis_options_dialog)
        visualization_options_pb.setCheckable(True)
        self.visualization_options_pb =visualization_options_pb
        self.next_spark_pb =next_spark_pb
        self.previous_spark_pb = previous_spark_pb
        self.save_label = QG.QLabel('<html style="background:red;"> Not saved</html>')
        show_mask_pb.setCheckable(True)
        show_mask_pb.setChecked(True)
        pb_layout_1.addWidget(delete_pb)
        pb_layout_1.addWidget(save_pb)
        pb_layout_1.addWidget(find_pb)
        #pb_layout.addWidget(previous_spark_pb)
        #pb_layout.addWidget(next_spark_pb)
        pb_layout_2.addWidget(visualization_options_pb)
        pb_layout_2.addWidget(show_mask_pb)
        pb_layout_2.addWidget(show_data_pb)
        pb_layout_1.addWidget(self.save_label)
        show_data_pb.clicked.connect(self.show_spark_data)
        show_mask_pb.toggled.connect(self.show_masks)
        delete_pb.clicked.connect(self.delete_selected_sparks)
        #next_spark_pb.clicked.connect(self.next_spark)
        #previous_spark_pb.clicked.connect(self.previous_spark)
        save_pb.clicked.connect(self.save_sparks)

        main_layout.addLayout(bottom_layout,1,0)

        bottom_layout.setColumnStretch(0,2)
        bottom_layout.setColumnStretch(1,2)

        sparkplots_layout = QG.QGridLayout()
        #self.sparkplot = PlotWidget(self)
        #sparkplots_layout.addWidget(self.sparksplot)
        bottom_layout.addLayout(sparkplots_layout, 0, 1)
        ##
        self.temporal_stack = QG.QStackedWidget(self)
        self.spatial_stack = QG.QStackedWidget(self)
        temporal_plot_groupbox = QG.QGroupBox('Temporal slice')
        temporal_plot_groupbox.setLayout(QG.QVBoxLayout())
        temporal_plot_groupbox.layout().addWidget(self.temporal_stack)
        sparkplots_layout.addWidget(temporal_plot_groupbox,0,0)
        temporal_plot_groupbox.setStyleSheet("""
        QGroupBox
        {
            font-weight: bold;
            color:cornflowerblue;
        }
        """)

        spatial_plot_groupbox = QG.QGroupBox('Spatial slice')
        spatial_plot_groupbox.setLayout(QG.QVBoxLayout())
        spatial_plot_groupbox.layout().addWidget(self.spatial_stack)
        sparkplots_layout.addWidget(spatial_plot_groupbox,1,0)
        sparkplots_layout.addWidget(QG.QLabel('x'),1,1)

        spatial_plot_groupbox.setStyleSheet("""
        QGroupBox
        {
            font-weight: bold;
            color:purple;
        }
        """)
        if self.load_saved:
            save_pb.setEnabled(False)
            delete_pb.setEnabled(False)
            find_pb.setEnabled(False)
            self.load_sparks()

    def show_vis_options_dialog(self):
        dialog = QG.QDialog(self)
        layout = QG.QHBoxLayout()
        dialog.setLayout(layout)
        widget = VisualizationOptionsWidget(self.pipechain, parent=dialog)
        widget.settings_changed.connect(self.change_pixmap_settings)
        widget.close.connect(dialog.accept)
        widget.close.connect(lambda: self.visualization_options_pb.setChecked(False))
        layout.addWidget(widget)
        self.vis_widget = widget
        dialog.setModal(False)
        dialog.show()
        dialog.resize(600, 600)
        widget.do_histogram()

    def change_pixmap_settings(self, settings):
        self.make_new_pixmap(settings )


    def next_spark(self):
        if self.spark_no is None:
            return
        spark_no = self.spark_no + 1
        if spark_no < len(self.sparks):
            self.show_sparks([spark_no], notify=True)

    def previous_spark(self):
        if self.spark_no is None:
            return
        spark_no = self.spark_no - 1
        if spark_no > -1:
            self.show_sparks([spark_no], notify=True)

    def show_masks(self, state):
        if self.d_graphicpixmapitem:
            self.d_graphicpixmapitem.setVisible(state)
            self.m_graphicpixmapitem.setVisible(state)

    def plot_temporal(self):
        #data = self.spark_roi.temporal_data
        #smooth_data = self.spark_roi.temporal_smooth_data
        #axis_data = self.spark_roi.temporal_axis_data
        smooth_data = self.spark.temporal_smooth_data
        axis_data = self.spark.temporal_x_phys
        #self.fplot_temporal.addPlot('Temporal', data,
        #        axis_data, color = 'cyan',
        #        size=1, physical = False)
        self.fplot_temporal.addPlot('Temporal_smooth', smooth_data,
                axis_data, color = 'cornflowerblue',
                size=2, physical = False,type='circles')
        if self.spark.transient.params:
            self.fplot_temporal.addPlot('Temporal_fit', self.spark.transient.fit_function(arg=axis_data,
                    **self.spark.transient.params),
                    axis_data, color = 'orange',
                    size=2, physical = False)
        self.temporal_plotted = True
        self.fplot_temporal.fitView(0)


    def plot_spatial(self):
        #data = self.spark_roi.spatial_data
        smooth_data = self.spark.spatial_smooth_data
        axis_data = self.spark.spatial_axis_data
        #self.fplot_spatial.addPlot('Spatial', data,
        #        axis_data, color = 'magenta',
        #        size=1, physical = False)
        self.fplot_spatial.addPlot('Spatial_smooth', smooth_data,
                axis_data, color = 'purple',type='circles',
                size=2, physical = False)
        if self.spark.spatial_profile.params:
            self.fplot_spatial.addPlot('Spatial_Fit', self.spark.spatial_profile.fit_function(arg=axis_data, **self.spark.spatial_profile.params),
                    axis_data, color = 'orange',
                    size=2, physical = False)
        self.spatial_plotted = True
        self.fplot_spatial.fitView(0)

    def force_new_pixmap(self, v = None):
        self.make_new_pixmap(force = True)

    def make_new_pixmap(self, settings = {}, force = False):
        print 'making new pix', force
        pixmaker = self.pixmaker
        QC.QTimer.singleShot(100,lambda :
                pixmaker.makeImage(image_settings = settings, force = force))
        if self.image_shown:
            QC.QTimer.singleShot(150,lambda :
                    self.sparksplot.replacePixmap(pixmaker.pixmap))
        else:
            print 'showing image with tstamps'
            QC.QTimer.singleShot(200,lambda :
                    self.sparksplot.addPixmap(pixmaker.pixmap,
                        self.xvals, self.yvals)
                    )
            self.image_shown = True
        QC.QTimer.singleShot(250,lambda :self.sparksplot.fitView(0))
    def fit_sparkregion_plot(self):
        self.sparksplot.fitView(0)

class SparkFinder:
    def __init__(self, imagedata, treshold=3.8, min_area = 20):
        #min area in units of ms*um
        self.data = imagedata.all_image_data[0]
        self.blurred_data = None
        self.imagedata = imagedata
        self.treshold = treshold
        self.min_area = int(float(min_area)/(\
                self.imagedata.delta_space*self.imagedata.delta_time))#in pixels
        print 'min area in pixels = %i'%self.min_area


    def get_masks(self, data):
        sd = data.std()
        mean = data.mean()
        c1 = sd*1.5 + mean
        mask = numpy.where(data > c1, 1, 0)
        im1 = data*(1-mask)
        im1f = im1.flatten()
        nonzero_indices = (im1f>0).nonzero()
        nonzero_elements = numpy.take(im1f, nonzero_indices)
        sd1 = nonzero_elements.std()
        mean1 = nonzero_elements.mean()
        c2= sd1*2 + mean1
        mask = numpy.where(data > c2, 1, 0)

        im2 = data*(1-mask)
        im2f = im2.flatten()
        nonzero_indices = (im2f>0).nonzero()
        nonzero_elements = numpy.take(im2f, nonzero_indices)
        sd2 = nonzero_elements.std()
        mean2 = nonzero_elements.mean()
        c3= sd2*self.treshold + mean2
        maskc = numpy.where(data > c3, 1, 0)
        #return both masks and the adjusted mean (with sparks excised)
        return mask, maskc, mean2

    def get_sparks_old(self):
        data2sd, data3sd = self.get_masks(self.blurred_data)
        d2=data2sd.copy()
        d3=data3sd.copy()
        sparks = self.find_sparks(data2sd, data3sd)
        return sparks, d2-data2sd, d3

    def get_sparks(self):

        if self.blurred_data is None:
            uniform_blur_temporal_size = 14.0/2 #ms
            uniform_blur_spatial_size = 2.0 /2#um
            gaussian_blur_temporal_size = 4.0/2 #ms
            gaussian_blur_spatial_size = 0.6/2 #um
            #calculate the pixel sizes needed to match
            #physical blur sizes given above
            uniform_blur_temporal = int(round(\
                    uniform_blur_temporal_size/(self.imagedata.delta_time)))
            uniform_blur_spatial = int(round(\
                    uniform_blur_spatial_size/(self.imagedata.delta_space)))
            uniform_blur_size = (uniform_blur_spatial, uniform_blur_temporal)

            gaussian_blur_temporal = gaussian_blur_temporal_size/\
                    (self.imagedata.delta_time)
            gaussian_blur_spatial = gaussian_blur_spatial_size/\
                    (self.imagedata.delta_space)
            gaussian_blur_size = (gaussian_blur_spatial, gaussian_blur_temporal)
            print 'blur params: uniform %s, gaussian %s'\
                    %(str(uniform_blur_size), str(gaussian_blur_size))
            self.blurred_data = sn.uniform_filter(self.data, uniform_blur_size)
            self.blurred_data = sn.gaussian_filter(self.blurred_data, gaussian_blur_size)

        data2sd, data3sd, im_mean = self.get_masks(self.blurred_data)
        #structures from 3.8SD mask
        labels, s = sn.label(data3sd)
        #find sizes of structures
        sizes = sn.sum( data3sd, labels, range(s+1))
        #discard small structures
        mask_sizes = sizes < self.min_area
        remove_struc = mask_sizes[labels]
        labels[remove_struc] = 0
        #sort
        ll = numpy.unique(labels)
        labels = numpy.searchsorted(ll, labels)

        #qq2 = numpy.where(labels, self.blurred_data, numpy.zeros_like(self.data))
        #maskk = labels.astype(bool).astype(int)
        #
        #qq3 = qq2/qq2.max()
        ##have to be odd numbers
        #ssize = int(round(1./self.imagedata.delta_space))
        #tsize = int(round(45./(self.imagedata.delta_time)))
        #if ssize%2 == 0:
        #    ssize += 1
        #if tsize%2 == 0:
        #    tsize+=1
        #print 'looking for maximums L_space=%i, L_time=%i'%(ssize,tsize)
        #local_maxi = is_local_maximum( qq3, labels, numpy.ones((ssize,tsize)))
        #nz=numpy.nonzero(local_maxi)
        #markers, nn = sn.label(local_maxi)
        #lll=watershed(-numpy.exp(qq3), markers, mask=maskk)
        #
        #spark_sizes = sn.sum(lll.astype(bool), lll,range(nn+1))
        #mask_sizes = spark_sizes < self.min_area
        #remove_struc = mask_sizes[lll]
        #lll[remove_struc] = 0
        #sort
        #ll = numpy.unique(lll)
        #labels = numpy.searchsorted(ll, lll)


        coords_list = []
        max_area_coords_list = []
        dt = self.imagedata.delta_time
        ds = self.imagedata.delta_space
        n_dilate = 5.0
        #b = int((48.0/dt/n_dilate))
        b = int((30.0/dt/n_dilate))
        a = int((1.5/ds/n_dilate))
        print 'struct axes',(a,b)
        if b%2==0:
            b+=1
        if a%2==0:
            a+=1
        print 'struct axes',(a,b)
        evolve_times = int(max(a*n_dilate, b*n_dilate)) - 2
        print 'evolve times=',evolve_times
        spread = helpers.evolve_in_bits(labels,a,b,evolve_times)

        sd3_areas = sn.find_objects(labels)
        spread_areas = sn.find_objects(spread)
        for slice_max, slice_spread in zip(sd3_areas, spread_areas):
            X = slice_spread[1]
            Y = slice_spread[0]
            MX = slice_max[1]
            MY = slice_max[0]
            loc = [X.start, X.stop, Y.stop, Y.start]
            max_loc = [MX.start, MX.stop, MY.stop, MY.start]
            coords_list.append(loc)
            max_area_coords_list.append(max_loc)
        CL = numpy.array(coords_list)
        MCL = numpy.array(max_area_coords_list)
        sort_order = CL[:,0].argsort()
        CL = CL[sort_order]
        MCL = MCL[sort_order]
        #calculate new image mean from portions of the image where no sparks were found
        im_mean = helpers.masked_mean(self.blurred_data, spread==0, give_slice = False)
        #print 'new mean',im_mean

        spark_bounds = {}
        spark_max_area_bounds = {}
        for i,c in enumerate(CL):
            spark_bounds[i] = {'left':c[0], 'right':c[1], 'top':c[2], 'bottom':c[3]}
        for i,c in enumerate(MCL):
            spark_max_area_bounds[i] = {'left':c[0], 'right':c[1], 'top':c[2], 'bottom':c[3]}
        return spark_bounds, spark_max_area_bounds, im_mean, labels, spread#, #d2-data2sd, d3

    #def find_sparks(self,sd2data, sd3data):
    #    #first find peaks from
    #    peaks,s = self.counter(sd3data)
    #    #with one point from each peak area check if the underlying 2SD area is connected
    #    #make the list of test points
    #    coords = {'x':[],'y':[]}
    #    for key in peaks:
    #        loc = peaks[key][0]
    #        coords['x'].append(loc[0])
    #        coords['y'].append(loc[1])
    #    areas,sparks = self.counter(sd2data, coords)
    #    return sparks

    #def counter(self,data, coords=None):
    #    width = data.shape[1]
    #    height = data.shape[0]
    #    areas = {}
    #    count = 0
    #    if coords:
    #        xcoords = coords['x']
    #        ycoords = coords['y']
    #    else:
    #        xcoords = range(width)
    #        ycoords = range(height)

    #    for i in xcoords:
    #        for j in ycoords:
    #            if data[j,i] == 1:
    #                coordinates = []
    #                self.filler(data, i, j, coordinates)
    #                areas[count] = coordinates
    #                count += 1
    #                #figure()
    #                #imshow(data.copy())
    #    print '%i areas found'%count
    #    print "i\tarea\tleft\tright\ttop\tbottom"
    #    print '='*50
    #    spark_bounds = {}
    #    for key in areas:
    #        xs = []
    #        ys = []
    #        for c in areas[key]:
    #            xs.append(c[0])
    #            ys.append(c[1])
    #        spark_bounds[key] = {'left':min(xs),'right':max(xs),'top':max(ys),'bottom':min(ys)}
    #        print "%i\t%i\t%i\t%i\t%i\t%i"%(key, len(areas[key]),min(xs),max(xs),min(ys),max(ys))
    #    print '='*50
    #    print '\n'
    #    return areas, spark_bounds
    #
    #def filler(self, data, x, y, coordinates):
    #    width = data.shape[1]
    #    height = data.shape[0]
    #    if data[y,x] == 0:
    #        return
    #    else:
    #        data[y,x] = 0
    #        coordinates.append((x,y))
    #    if x>0:
    #        self.filler(data, x-1, y, coordinates)
    #    if x<width-1:
    #        self.filler(data, x+1, y, coordinates)
    #    if y>0:
    #        self.filler(data, x, y-1, coordinates)
    #    if y<height-1:
    #        self.filler(data, x, y+1, coordinates)


