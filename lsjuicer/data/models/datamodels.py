import glob
import os

from PyQt5 import QtGui as QG
from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC


from lsjuicer.inout.converters.OMEXMLMaker import OMEXMLMaker
from lsjuicer.static.constants import Constants
from lsjuicer.inout.db.sqla import ImageMaker
import lsjuicer.inout.db.sqla as sa
from lsjuicer.static.constants import ImageStates
from lsjuicer.util.helpers import timeIt
import lsjuicer.data.analysis.transient_find as tf

class FitResultDataModel(QC.QAbstractTableModel):
    """Model for non-db fit results"""
    def __init__(self, parent = None):
        super(FitResultDataModel, self).__init__(parent)
        self.fit_result = None
        self.columns = 7

    @property
    def regions(self):
        if self.fit_result:
            return self.fit_result['regions']
        else:
            return {}

    @property
    def rows(self):
        return len(self.regions)

    def set_fit_result(self, fit_result):
        print 'set res', fit_result
        self.layoutAboutToBeChanged.emit((),0)
        self.fit_result= fit_result
        self.ff0_func = tf.FF0(fit_result)
        self.layoutChanged.emit((),0)

    #def remove_transients(self, indexes):
    #    self.layoutAboutToBeChanged.emit((),0)
    #    transients_to_remove = []
    #    for index in indexes:

    #        transient_key = self.visual_transient_collection.transient_group.order[index.row()]
    #        if transient_key not in transients_to_remove:
    #            transients_to_remove.append(transient_key)
    #        #vtr = self.visual_transient_collection[transient_key]
    #    for key in transients_to_remove:
    #        print 'remove', key
    #        self.visual_transient_collection.remove_transient(key)
    #    self.layoutChanged.emit((),0)


    #def set_transients_state(self, attrib, indexes):
    #    function = {'visible':'set_visible', 'editable':'set_editable'}
    #    assert attrib in function
    #    self.layoutAboutToBeChanged.emit((),0)
    #    transients_to_modify_keys = []
    #    states = []
    #    for index in indexes:
    #        transient_key = self.visual_transient_collection.transient_group.order[index.row()]
    #        vtr = self.visual_transient_collection[transient_key]
    #        if transient_key not in transients_to_modify_keys:
    #            transients_to_modify_keys.append(transient_key)
    #            states.append(not getattr(vtr,attrib))
    #    print 'set state', attrib, indexes
    #    f = getattr(self.visual_transient_collection, function[attrib])
    #    f(transients_to_modify_keys, states)
    #    self.layoutChanged.emit((),0)

    #def set_transients_visible(self, indexes):
    #    self.set_transients_state('visible', indexes)

    #def set_transients_editable(self, indexes):
    #    self.set_transients_state('editable', indexes)

    def rowCount(self, parent):
        return self.rows

    def columnCount(self, parent):
        return self.columns

    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section == 0:
                    return "Event"
                elif section == 1:
                    return "A"
                elif section == 2:
                    return 'mu'
                elif section == 3:
                    return 'rise'
                elif section == 4:
                    return 'd'
                elif section == 5:
                    return 'decay'
                elif section == 6:
                    return 'dF/F0'
                else:
                    return QC.QVariant()
            else:
#                return 'Transient %i'%(section+1)
                QC.QVariant()
        else:
            return QC.QVariant()

    def data(self, index, role):
        if self.regions:
            row = index.row()
            keys = self.regions.keys()
            keys.sort()
            key = keys[row]
            col = index.column()
            region = self.regions[key]
            sol = region.fit_res[-1].solutions
            if role == QC.Qt.DisplayRole:
                    if col == 0:
                        return "%i"%key
                    elif col == 1:
                        return "%.4g"%sol['A']
                    elif col==2:
                        return "%i"%sol['m2']
                    elif col==3:
                        return "%i"%sol['d']
                    elif col==4:
                        return "%i"%sol['d2']
                    elif col==5:
                        return "%i"%sol['tau2']
                    elif col==6:
                        return "%.3f"%self.ff0_func(sol['m2'])
                    else:
                        return QC.QVariant()

            elif role==QC.Qt.TextAlignmentRole:
                return QC.Qt.AlignCenter

            else:
                return QC.QVariant()
        else:
            return QC.QVariant()

class TransientDataModel(QC.QAbstractTableModel):
    def __init__(self, parent = None):
        super(TransientDataModel, self).__init__(parent)
        self.visual_transient_collection = None
        #self.rows = 4
        self.columns = 9

    def get_rows(self):
        if self.visual_transient_collection:
            return len(self.visual_transient_collection)
        else:
            return 4
    rows = property(get_rows)
    def set_visual_transient_collection(self, visual_transient_collection):
        self.layoutAboutToBeChanged.emit((),0)
        self.visual_transient_collection = visual_transient_collection
        #self.transients = transients.ts
        #self.rows = len(self.visual_transient_collection)
        #print 'set %i vis transients'%self.rows
        #print 'transients',self.rows
        self.layoutChanged.emit((),0)

    def remove_transients(self, indexes):
        self.layoutAboutToBeChanged.emit((),0)
        transients_to_remove = []
        for index in indexes:
            transient_key = self.visual_transient_collection.transient_group.order[index.row()]
            if transient_key not in transients_to_remove:
                transients_to_remove.append(transient_key)
            #vtr = self.visual_transient_collection[transient_key]
        for key in transients_to_remove:
            print 'remove', key
            self.visual_transient_collection.remove_transient(key)
        self.layoutChanged.emit((),0)


    def set_transients_state(self, attrib, indexes):
        function = {'visible':'set_visible', 'editable':'set_editable'}
        assert attrib in function
        self.layoutAboutToBeChanged.emit((),0)
        transients_to_modify_keys = []
        states = []
        for index in indexes:
            transient_key = self.visual_transient_collection.transient_group.order[index.row()]
            vtr = self.visual_transient_collection[transient_key]
            if transient_key not in transients_to_modify_keys:
                transients_to_modify_keys.append(transient_key)
                states.append(not getattr(vtr,attrib))
        print 'set state', attrib, indexes
        f = getattr(self.visual_transient_collection, function[attrib])
        f(transients_to_modify_keys, states)
        self.layoutChanged.emit((),0)

    def set_transients_visible(self, indexes):
        self.set_transients_state('visible', indexes)

    def set_transients_editable(self, indexes):
        self.set_transients_state('editable', indexes)

    def rowCount(self, parent):
        return self.rows

    def columnCount(self, parent):
        return self.columns

    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section == 1:
                    return "Start"
                elif section == 2:
                    return "Duration"
                elif section == 0:
                    return 'Transient'
                elif section == 3:
                    return 'Decay'
                elif section == 4:
                    return 'Amplitude ABS'
                elif section == 5:
                    return 'Amplitude RBL'
                elif section == 6:
                    return 'Relaxation'
                elif section == 7:
                    return 'Residual'
                elif section == 8:
                    return 'Baseline'
                #elif section == 9:
                #    return 'V'
                else:
                    return QC.QVariant()
            else:
#                return 'Transient %i'%(section+1)
                QC.QVariant()
        else:
            return QC.QVariant()

    def data(self, index, role):
        if self.visual_transient_collection:
            row = index.row()
            key = self.visual_transient_collection.transient_group.order[row]
            col = index.column()
            try:
                vtr = self.visual_transient_collection[key]
#                print 'trtr',vtr
                tr = vtr.transient_rect.transient
            except KeyError:
                print 'error', key
                return QC.QVariant()
#            tr = self.vis_transients.ts.transients[key]
            if role == QC.Qt.DisplayRole:
                    if col == 0:
                        return "%i"%(row + 1)
                    elif col==1:
                        return "%.2f"%tr.start_phys
                    elif col==2:
                        return "%.2f"%(tr.end_phys-tr.start_phys)
                    elif col==3:
                        return str(tr.decay)
                    elif col==4:
                        return str(tr.max_y)
                    elif col==5:
                        return str(tr.max_ymbl)
                    elif col==6:
                        return str(tr.relaxation_bl)
                    elif col==7:
                        return str(tr.decay_residual)
                    elif col==8:
                        return str(tr.baseline)
                    #elif col==9:
                    #    return vtr.visible
                    else:
                        return QC.QVariant()

            elif role==QC.Qt.TextAlignmentRole:
                return QC.Qt.AlignCenter

            elif role == QC.Qt.DecorationRole:
                if col==0:
                    pix = QG.QPixmap(20,20)
                    pix.fill(vtr.color)
                    painter = QG.QPainter(pix)
                    painter.setRenderHint(QG.QPainter.Antialiasing)
                    if vtr.group_color:
                        painter.setBrush(QG.QBrush(vtr.group_color))
                        painter.setPen(QG.QPen(vtr.group_color))
                        painter.drawEllipse(QC.QPointF(10.,10.),5.,5.)
                    return pix
            #elif role == QC.Qt.CheckStateRole:
            #    if col == 9:
            #        #print 'col 9'
            #        if vtr.visible:
            #            #print 'check'
            #            return QC.Qt.Checked
            #        else:
            #            #print 'ucheck'
            #            return QC.Qt.Unchecked
            #    else:
            #        return QC.QVariant()
            else:
                return QC.QVariant()
        else:
            return QC.QVariant()
    #def flags(self, index):
        #selection = self.filePath(index)
        #if os.path.isdir(selection):
        #if index.column()==9:
    #    return QC.Qt.ItemIsEnabled | QC.Qt.ItemIsUserCheckable | QC.Qt.ItemIsEditable | QC.Qt.ItemIsSelectable
        #else:
        #    return QC.Qt.ItemIsEnabled

class MyProxyModel(QC.QSortFilterProxyModel):
    """
    Extended QSortFilterProxyModel to allow only unique indices to set to be plotted
    """
    #def __init__(self,parent = None):
    #    super(MyProxyModel, self).__init__(parent)
    doPlot = QC.pyqtSignal(object)
    def setView(self, view):
        self.view=view

    def uniqueIndices(self, indexlist):
        indices = []
        for ind in indexlist:
            row = self.mapToSource(ind).row()
            if row in indices:
                continue
            else:
                indices.append(row)
        return indices

    def preparePlot(self):
        indices = self.uniqueIndices(self.view.selectedIndexes())
        self.doPlot.emit(indices)
    def prepareShowReference(self):
        indices = self.uniqueIndices(self.view.selectedIndexes())
        return indices
        #self.emit(QC.SIGNAL('plotReference(PyQt_PyObject)'),indices)

class MyFileIconProvider(QW.QFileIconProvider):
    def icon(self, icontype):
        if icontype.isDir():
            return QG.QIcon(':/folder.png')
        elif icontype.isFile():
            return QG.QIcon(':/picture.png')
        else:
            return QW.QFileIconProvider.icon(self,icontype)

class MyFileSystemModel(QW.QFileSystemModel):
    """FileSystemModel that links to a :class:`RandomDataModel`

    Attributes
    -----------
    target : :class:`RandomDataModel`
        Model with image file data
    """
    inspect_visible = QC.pyqtSignal(bool)
    inspect_needed = QC.pyqtSignal(int)
    def __init__(self,parent = None):
        super(MyFileSystemModel, self).__init__(parent)
        self.icon_provider = MyFileIconProvider()
        self.target = None
        self.ftype = None
    def set_filetype(self, ftype):
        self.ftype = ftype
        print 'ftype', ftype
        if ftype=="oib":
            self.ftype="oib,oif"
            self.setNameFilters([str("*.oib"),str("*.oif")])
        else:
            self.setNameFilters([str("*.%s"%ftype)])

    def setTarget(self, target):
        self.target = target

    def updateTarget(self, index):
        dd = self.filePath(index)
        self.target.change_ftype(self.ftype)
        self.target.setDir(dd)
        #return dd

    def checkFiles(self, index):
        suffixes = self.ftype.split(",")
        filelist=[]
        for s in suffixes:
            suffix  = "*.%s"%str(s).lower()
            dd = self.filePath(index)
            fl = glob.glob(os.path.join(str(dd),str(suffix)))
            filelist.extend(fl)
            print 'FILES',dd,len(filelist),os.path.join(str(dd),str(suffix)), filelist
        if filelist:
            self.inspect_visible.emit(True)
            self.inspect_needed.emit(len(filelist))
        else:
            self.inspect_visible.emit(False)
        return dd

    def flags(self, index):
        selection = self.filePath(index)
        if os.path.isdir(selection):
            return QC.Qt.ItemIsEnabled | QC.Qt.ItemIsSelectable
        else:
            return QC.Qt.ItemIsEnabled


class RandomDataModel(QC.QAbstractTableModel):
    """DataModel to display data from image file in a directory"""
    conversion_finished = QC.pyqtSignal()
    switchToFileSelection = QC.pyqtSignal(str)
    filesRead = QC.pyqtSignal(int)
    totalFiles = QC.pyqtSignal(int)
    progressVisible = QC.pyqtSignal(bool)
    conversion_needed = QC.pyqtSignal(int)
    convert_pb_visible = QC.pyqtSignal(bool)
    convert_progress_visible = QC.pyqtSignal(bool)
    fitColumns=QC.pyqtSignal()
    plotFile = QC.pyqtSignal(object)
    def __init__(self, parent=None):
        super(RandomDataModel, self).__init__(parent)
        print 'parent', parent
        self.columns = 16
        self.dirname = ""
        self.data = []
        self.dirdatas = []
        self.session = None
        self.ftype = sa.dbmaster.get_config_setting_value('filetype')
        #formats = ["*.lsm","*.ome"]
        self.omexml_maker = OMEXMLMaker()
        self.omexml_maker.conversion_update.connect(self.conversion_update)
#        self.connect(self.omexml_maker,QC.SIGNAL('conversion_finished()'),self.conversion_finished)
        self.omexml_maker.conversion_finished.connect(self.ome_conversion_finished)

    def __del__(self):
        print 'del'

    def destroyed(self, obj):
        print 'destroy', obj

    def closeEvent(self, event):
        print "close data"

    def ome_conversion_finished(self):
        print 'finished converting'
        self.conversion_finished.emit()
        if self.session:
            print 'Have SQLA DB session', self.session
            print 'Session state:'
            print "new", self.session.new
            print 'dirty', self.session.dirty
            self.session.commit()
            #self.session.close()
            #self.session=None

    def change_ftype(self, ftype):
        self.ftype = str(ftype)
        print 'ftype',ftype
        fts = self.ftype.split(',')
        self.formats = []
        for ft in fts:
            self.formats.append("*.%s"%str(ft).lower())
        print 'formats:',self.formats

    def conversion_update(self):
        self.layoutAboutToBeChanged.emit((),0)
        self.layoutChanged.emit((),0)
        self.fitColumns.emit()

    def rowCount(self, parent):
        return self.rows

    def columnCount(self, parent):
        return self.columns

    def plot(self, indexlist):
        toplot = []
        for ind in indexlist:
            print 'index',ind
            f = self.dirdatas[ind]
            f.state=Constants.PLOTTED
            toplot.append(self.dirdatas[ind])
        print 'toplot:::',toplot
        self.plotFile.emit(toplot)

    def show_ref(self, indexlist):
        toplot = []
        for ind in indexlist:
            #f = self.dirdatas[ind]
            toplot.append(self.dirdatas[ind])
        return toplot

    @property
    def rows(self):
        return len(self.dirdatas)

    @timeIt
    def updateData(self):
        print '\n\n\n\ndata update'
        import time
        t0=time.time()
        self.dirdatas = []
        self.progressVisible.emit(True)
        files = []
        new_files=False
        for fmt in self.formats:
            files.extend(glob.glob(os.path.join(str(self.dirname),fmt)))
        self.totalFiles.emit(len(files)-1)
        self.session = sa.dbmaster.get_session()
        import time
        self.omexml_maker.reset_convert_list()
        t0 = time.time()
        for i,f in enumerate(files):
            print '\n\n read',f
            new_files = True
            im = ImageMaker.check_in_database(f, self.session)
            self.dirdatas.append(im)
            print 't=', time.time()-t0
            t0=time.time()
            #analyses = im.analyses
            #fit_results = self.session.query(sa.PixelByPixelRegionFitResult).\
            #        join(sa.PixelByPixelFitRegion).join(sa.PixelByPixelAnalysis).\
            #        join(sa.MicroscopeImage).filter(sa.MicroscopeImage.id == im.id).all()
            #for result in fit_results:
            #    syn_im = sa.PixelFittedSyntheticImage(result)
            #    self.dirdatas.append(syn_im)
            self.filesRead.emit(i)

        ##self.files.sort(key=lambda f:self.dirdatas[self.dirname][f].datetime)
        #find how many files need to be converted
        print '\ndone with read'
        for v in self.dirdatas:
            print v
        if new_files:
            needs_converting = 0
            for fr in self.dirdatas:
                if fr.state == ImageStates.NOT_CONVERTED:
                    needs_converting += 1
                    print 'adding',fr
                    self.omexml_maker.add_file_to_convert(fr)
            print 'conversion needed for %i files'%needs_converting
            if needs_converting:
                self.conversion_needed.emit(needs_converting)
                self.totalFiles.emit(needs_converting)

        self.progressVisible.emit(False)
        if self.dirdatas:
            self.switchToFileSelection.emit(self.dirname)
        print self.dirdatas
        self.session.commit()

    def convert(self):
        print 'singleshot'
        #return QC.QTimer.singleShot(500,lambda :self.omexml_maker.convert_all())
        self.convert_progress_visible.emit(True)
        self.convert_pb_visible.emit(False)
#        self.emit(QC.SIGNAL('filesRead(int)'),0)
        self.omexml_maker.convert_all()
        #self.emit(QC.SIGNAL('progressVisible(bool)'),False)

    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section == 0:
                    return "Filename"
                elif section == 1:
                    return "Height"
                elif section == 2:
                    return "Width"
                elif section==3:
                    return "d time"
                elif section== 4:
                    return "d space"
                elif section==5:
                    return "Channels"
                elif section==6:
                    return "Recorded"
                elif section==7:
                    return "Converted name"
                elif section==8:
                    return "Project"
                elif section==9:
                    return "Prep"
                elif section==10:
                    return "Solution"
                elif section==11:
                    return "Protocol"
                elif section==12:
                    return "Sample"
                elif section==13:
                    return "Cell"
                elif section==14:
                    return "Analyses"
                elif section==15:
                    return "Notes"
            else:
                return section+1
        else:
            return QC.QVariant()

    def flags(self, index):
        f = self.dirdatas[index.row()]
        if f.state in [ImageStates.CONVERSION_FAILED, ImageStates.NOT_CONVERTED]:
            return QC.Qt.ItemIsEnabled
        else:
            return QC.Qt.ItemIsEnabled | QC.Qt.ItemIsSelectable

    def recheck_images(self):
        #d = self.dirdatas
        for f in self.dirdatas:
            print 'check'
            print f
            f.populate_attributes()
            print f
        print 'dirty',self.session.dirty
        self.session.commit()


    def data(self, index, role):
        if role == QC.Qt.DisplayRole:
            f = self.dirdatas[index.row()]
            col = index.column()
            exp_info = f.exp_info
            na_string = "-"
            def ifname(val):
                if val:
                    return getattr(val, 'name')
                else:
                    return na_string
            def ifattr(name):
                val = getattr(exp_info, name)
                if val:
                    return val
                else:
                    return na_string
            if col == 0:
                return os.path.basename(f.file_name)
            elif col == 1:
                return f.image_height
            elif col == 2:
                return f.image_width
            elif col==3:
                if f.delta_time:
                    return "%.2f"%(f.delta_time)#in ms
                else:
                    return None
            elif col==4:
                if f.delta_space:
                    return "%.3f"%f.delta_space#in um
                else:
                    return None
            elif col==5:
                if f.channels:
                    return f.channels
                else:
                    return None
            elif col==6:
                fmt = '%Y-%m-%d %H:%M:%S'
                if f.record_date:
                    return f.record_date.strftime(fmt)
                else:
                    return QC.QVariant()
            elif col==7:
                if f.file_hash:
                    return f.file_hash
                else:
                    return QC.QVariant()
            elif col==8:
                return ifname(exp_info.project)
            elif col==9:
                return ifname(exp_info.preparation)
            elif col==10:
                return ifname(exp_info.solution)
            elif col==11:
                return ifname(exp_info.protocol)
            elif col==12:
                return ifattr("sample")
            elif col==13:
                return ifattr("cell")
            elif col==14:
                return len(f.analyses)
            elif col==15:
                if f.description:
                    dd=f.description
                else:
                    dd=""
                return " | ".join([ifattr("comment"), dd])
                #return d[f].description

        elif role == QC.Qt.DecorationRole:
            f = self.dirdatas[index.row()]
            col = index.column()
            if col==0:
                state = f.state
                if state == ImageStates.CONVERTED:
                    return QG.QColor('cornflowerblue')
                elif state==ImageStates.NOT_CONVERTED:
                    return QG.QColor('red')
                elif state==ImageStates.ANALYZED_IN_CURRENT_SESSION:
                    return QG.QColor('lime')
                elif state==ImageStates.ANALYZED_IN_PREVIOUS_SESSION:
                    return QG.QColor('magenta')
                elif state==ImageStates.CONVERSION_FAILED:
                    return QG.QColor('black')
            else:
                return QC.QVariant()
        elif role==QC.Qt.TextAlignmentRole:
            col = index.column()
            if col not in [0,8]:
                return QC.Qt.AlignCenter
            else:
                return QC.QVariant()
        else:
            return QC.QVariant()

    def setDir(self, dirname):
        #if dirname != self.dirname:
        if 1:
            self.dirname = str(dirname)
            print 'new dir',str(self.dirname)
            self.modelAboutToBeReset.emit()
            self.layoutAboutToBeChanged.emit((),0)
            self.updateData()
 #           self.beginResetModel()
            self.modelReset.emit()
            self.layoutChanged.emit((),0)
            #self.emit(QC.SIGNAL('fitColumns()'))
        else:
            print 'old dir'
    def data_update(self, tl, br):
        self.dataChanged.emit(tl, br)
        #self.emit(QC.SIGNAL('modelAboutToBeReset()'))
        #self.emit(QC.SIGNAL('layoutAboutToBeChanged()'))
        #self.emit(QC.SIGNAL('modelReset()'))
        #self.emit(QC.SIGNAL('layoutChanged()'))
