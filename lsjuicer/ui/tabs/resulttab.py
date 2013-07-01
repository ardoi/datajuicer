import PyQt4.QtCore as QC
import PyQt4.QtGui as QG
import numpy as n
import datetime

from lsjuicer.ui.widgets.plot_with_axes_widget import ContinousPlotWidget
from lsjuicer.ui.scenes.displays import FDisplay
from lsjuicer.ui.views.dataviews import CopyTableView

import lsjuicer.data.spark as dspark
import lsjuicer.inout.db.sqla as sqla
class SparkDataModel(QC.QAbstractTableModel):
    def __init__(self, parent=None):
        super(SparkDataModel, self).__init__(parent)
        self.rows = 0
        self.columns = 12
    def rowCount(self, parent):
        return self.rows
    def columnCount(self, parent):
        return self.columns
    def setData(self, model_data):
        self.layoutAboutToBeChanged.emit()
        self.modelAboutToBeReset.emit()
        self.model_data = []
        for spark_roi in model_data:
            try:
                for boundary in model_data[spark_roi]:
                    spark = model_data[spark_roi][boundary]
                    self.model_data.append((spark_roi,spark))
            except TypeError:
                spark = model_data[spark_roi]
                self.model_data.append((spark_roi,spark))

        self.rows = len(self.model_data)
        print 'new rows', self.rows
        self.layoutChanged.emit()
        self.modelReset.emit()
    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section == 0:
                    return "Spark ROI"
                elif section == 1:
                    return "Spark in ROI"
                elif section == 2:
                    return "Amplitude"
                elif section == 3:
                    return "Baseline"
                elif section == 4:
                    return "FWHM[um]"
                elif section == 5:
                    return "FDHM[ms]"
                elif section == 6:
                    return "Risetime[ms]"
                elif section == 7:
                    return "Decay time[ms]"
                elif section == 8:
                    return "Time @ max[ms]"
                elif section == 9:
                    return "Loc @ max[um]"
                elif section == 10:
                    return "dF_max"
                elif section == 11:
                    return "dt"
            else:
                return section + 1
        else:
            return QC.QVariant()

    def get_active_spark_number(self, indexlist):
        indices = []
        for ind in indexlist:
            if ind.row() in indices:
                continue
            else:
                indices.append(ind.row())
        active = []
        for i in indices:
            spark = self.model_data[i][1]
            active.append(spark.number)
        return active

    def data(self, index, role):
        col = index.column()
        if role == QC.Qt.DisplayRole:
            spark = self.model_data[index.row()][1]
            if isinstance(spark, dspark.Spark):
                if col==0:
                    return spark.roi
                elif col == 1:
                    return spark.number
                elif col == 2:
                    if spark.max_val is None:
                        return QC.QVariant()
                    else:
                        return"%.3f"%spark.max_val
                elif col == 3:
                    if spark.max_val is None:
                        return QC.QVariant()
                    else:
                        return"%.3f"%spark.baseline
                elif col == 4:
                    if spark.FWHM is None:
                        return QC.QVariant()
                    else:
                        return "%.2f"%spark.FWHM
                elif col == 5:
                    if spark.FDHM is None:
                        return QC.QVariant()
                    else:
                        return "%.2f"%spark.FDHM
                elif col == 6:
                    if spark.risetime is None:
                        return QC.QVariant()
                    else:
                        return "%.2f"%spark.risetime
                elif col == 7:
                    if spark.decay_constant is None:
                        return QC.QVariant()
                    else:
                        return "%.2f"%spark.decay_constant
                elif col==8:
                    return "%.2f"%spark.max_time
                elif col==9:
                    try:
                        return "%.2f"%spark.FWHM_max_location
                    except:
                        return QC.QVariant()
                elif col == 10:
                    fparam = spark.transient.params
                    if fparam:
                        return "%.2f"%(spark.max_val - spark.baseline)
                        #return ", ".join(["%s:%.1f"%(key, fparam[key]) \
                        #    for key in fparam.keys()])
                    else:
                        return QC.QVariant()
                elif col == 11:
                    if index.row()==0:
                        return QC.QVariant()
                    else:
                        prev_index = index.row()-1
                        dt = spark.max_time - self.model_data[index.row()-1][1].max_time
                        return "%i"%int(dt)


            elif isinstance(spark, sqla.Spark):
                if col==0:
                    return "%i"%spark.region_id
                elif col == 1:
                    return spark.id
                elif col == 2:
                    if spark.val_at_max is None:
                        return QC.QVariant()
                    else:
                        return"%.3f"%spark.val_at_max
                elif col == 3:
                    if spark.val_at_max is None:
                        return QC.QVariant()
                    else:
                        return"%.3f"%spark.baseline
                elif col == 4:
                    if spark.fwhm is None:
                        return QC.QVariant()
                    else:
                        return "%.2f"%spark.fwhm
                elif col == 5:
                    if spark.fdhm is None:
                        return QC.QVariant()
                    else:
                        return "%.2f"%spark.fdhm
                elif col == 6:
                    if spark.risetime is None:
                        return QC.QVariant()
                    else:
                        return "%.2f"%spark.risetime
                elif col == 7:
                    if spark.decay_constant is None:
                        return QC.QVariant()
                    else:
                        return "%.2f"%spark.decay_constant
                elif col==8:
                    return "%.2f"%spark.time_at_max
                elif col==9:
                    try:
                        return "%.2f"%spark.loc_at_max
                    except:
                        return QC.QVariant()
                elif col == 10:
                    fparam = spark.temporal_fit_params
                    if fparam:
                        return "%.2f"%(spark.val_at_max - spark.baseline)
                        #return ", ".join(["%s:%.1f"%(key, fparam[key]) \
                        #    for key in fparam.keys()])
                    else:
                        return QC.QVariant()
                elif col == 11:
                    if index.row()==0:
                        return QC.QVariant()
                    else:
                        prev_index = index.row()-1
                        dt = spark.time_at_max - self.model_data[index.row()-1][1].time_at_max
                        return "%i"%int(dt)

        elif role == QC.Qt.TextAlignmentRole:
            return QC.Qt.AlignCenter
        else:
            return QC.QVariant()

class GroupDataModel(QC.QAbstractTableModel):
    def __init__(self, parent=None):
        super(GroupDataModel, self).__init__(parent)
        self.rows = 0
        self.columns = 4
        self.group_data = []

    def rowCount(self, parent):
        return self.rows
    def columnCount(self, parent):
        return self.columns

    def setData(self,data):
        self.rows = len(data)
        self.group_data = data
        self.groups = data.keys()
        self.groups.sort()

    def headerData(self, section, orientation, role):
        if role == QC.Qt.DisplayRole:
            if orientation == QC.Qt.Horizontal:
                if section == 0:
                    return "Group"
                elif section == 1:
                    return "Mean"
                elif section == 2:
                    return "Std"
                elif section == 3:
                    return "n"
            else:
                return section + 1
        else:
            return QC.QVariant()

    def data(self, index, role):
        k = self.groups[index.row()]
        col = index.column()
        if role == QC.Qt.DisplayRole:
            if col == 0:
                return self.groups[index.row()]
            elif col == 1:
                return "%.4f"%self.group_data[k]['mean']
            elif col == 2:
                return "%.4f"%self.group_data[k]['std']
            elif col == 3:
                return "%i"%self.group_data[k]['n']
        elif role == QC.Qt.DecorationRole:
            if col == 0:
                return QG.QColor(self.group_data[k]['color'])
            else:
                return QC.QVariant()
        else:
            return QC.QVariant()

def list2str(lin):
    return ", ".join(["%.5f"%el for el in lin])

class SparkResultsWidget(QG.QWidget):
    sparks_active = QC.pyqtSignal(list)
    def  __init__(self, sparks, imagedata, parent = None):
        super(SparkResultsWidget, self).__init__( parent)
        self.sparks = sparks
        layout = QG.QVBoxLayout()
        self.setLayout(layout)
        self.tableview = CopyTableView(self)
        self.dm = SparkDataModel()
        if self.sparks:
            self.dm.setData(self.sparks)
        self.tableview.setModel(self.dm)
        self.tableview.items_selected.connect(self.spark_selected)
        self.tableview.setSelectionMode(QG.QAbstractItemView.ExtendedSelection)
        self.tableview.setSelectionBehavior(QG.QAbstractItemView.SelectRows)
        self.tableview.setAlternatingRowColors(True)
        #self.tableview.horizontalHeader().setResizeMode(QG.QHeaderView.Fixed)
        self.tableview.horizontalHeader().setResizeMode(QG.QHeaderView.ResizeToContents)
        self.tableview.horizontalHeader().setResizeMode(self.dm.rows-1, QG.QHeaderView.Stretch)

        #self.tableview.setSizePolicy(QG.QSizePolicy.Maximum, QG.QSizePolicy.Maximum)
        layout.addWidget(self.tableview)
        self.imagedata = imagedata

    def set_selected(self, row):
        index = self.dm.createIndex(row,0)
        self.tableview.setCurrentIndex(index)

    def get_selected_spark_numbers(self):
        indices = self.tableview.selectedIndexes()
        return self.dm.get_active_spark_number(indices)

    def spark_selected(self, state):
        if state:
            try:
                indices = self.tableview.selectedIndexes()
                active = self.dm.get_active_spark_number(indices)
                self.sparks_active.emit(active)
            except AttributeError:
                print "Showing loaded spark. Trace plotting not implemented yet"

    def update(self, sparks):
        print 'update 1', sparks
        #self.dm.modelReset.emit()
        self.sparks = sparks
        self.dm.setData(self.sparks)
        self.tableview.resizeColumnsToContents()
    def save_data(self,datafilename):
        comment,ok = QG.QInputDialog.getText(self,
                'info','You can enter a comment on the line below:',QG.QLineEdit.Normal, '')
        if not ok:
            QG.QMessageBox.information(self,'Cancelled','Saving was cancelled')
            return
        #print comment, ok
        print '::Saving::', datafilename
        try:
            datafile = open(datafilename,'w')
        except IOError:
            txt = 'Error saving file \n%s'%datafilename
            QG.QMessageBox.warning(self,'Error',txt)
            return
        datafile.write("# Comment: %s\n"%comment)
        reader = self.imagedata.readers[0] #use the first reader
        datafile.write("# File notes: %s\n"%reader.notes)
        datafile.write("# File info: %s\n"%reader.info_txt)
        datafile.write("# File recorded: %s\n"%reader.datetime)
        date = datetime.datetime.now()
        datestring = date.strftime('%Y-%m-%d %H:%M:%S')
        datafile.write("# File analyzed: %s\n"%datestring)
        #data = []
        #for spark_roi in self.sparks:
        #    for boundary in self.sparks[spark_roi]:
        #        spark = self.sparks[spark_roi][boundary]
        #        data.append((spark_roi,spark))
        #self.rows = len(self.data)
        #restypes.sort()
        #header = ", ".join(restypes)
        #datafile.write("# Spark, "+header+"\n")
        column_names = ["\n#Column names:"]
        column_names.append("# 1: Spark")
        columns = ["1"]
        for i in range(self.dm.columnCount(None)):
            value = self.dm.headerData(i, QC.Qt.Horizontal, QC.Qt.DisplayRole)
            column_names.append("# %i: %s"%(i+2,value))
            columns.append(str(i+2))
        header = "\n".join(column_names)
        column_header = ", ".join(columns)
        #datafile.write("# Spark, Spark number in ROI, ROI number, FWHM, FDHM, max dF/F0, rise time, decay constant, time of maximum \n")
        datafile.write(header + "\n\n")
        datafile.write(column_header + "\n\n")


        outdatas = []
        for i in range(self.dm.rowCount(None)):
            out = []
            out.append(str(i+1))
            for j in range(self.dm.columnCount(None)):
                index = self.dm.index(i, j)
                value = self.dm.data(index, QC.Qt.DisplayRole)
                #print type(value)
                out.append(str(value))
            outline = ", ".join(out)
            datafile.write(outline + "\n")
        #for i, d in enumerate(data):
        #    spark = d[1]
        #    roi = d[0]
        #    out = "%i\t%i"% (i, roi)
        #    try:
        #        out += " %f\t%f\t%f\t%f\t%f\t%f" % (spark.FWHM, spark.FDHM,
        #                spark.max_val, spark.risetime, spark.decay_constant,
        #                spark.max_time)
        #    except:
        #        QG.QMessageBox.information(self,'Error','Please analyze data first!')
        #        datafile.close()
        #        return
#
        #    outdatas.append(out)
        #for vec in outdatas:
        #    datafile.write(vec + "\n")
        txt = 'Results saved to:\n%s'%datafilename
        QG.QMessageBox.information(self,'Success',txt)
        datafile.close()

class ResultTab(QG.QTabWidget):
    def  __init__(self, parent = None):
        super(ResultTab, self).__init__(parent)
        self.currentChanged.connect(self.setc)
        self.groups={}

    def save_data(self,datafilename):
        comment,ok = QG.QInputDialog.getText(self,
                'info','You can enter a comment on the line below:',QG.QLineEdit.Normal, '')
        if not ok:
            QG.QMessageBox.information(self,'Cancelled','Saving was cancelled')
            return
        #print comment, ok
        print '::Saving::', datafilename
        try:
            datafile = open(datafilename,'w')
        except IOError:
            txt = 'Error saving file \n%s'%datafilename
            QG.QMessageBox.warning(self,'Error',txt)
            return
        datafile.write("# Comment: %s\n"%comment)
        restypes = self.groups.keys()
        restypes.sort()
        header = ", ".join(restypes)
        datafile.write("# Transient number, "+header+"\n")
        outdatas = []
        times = None
        for restype in restypes:
            #datafile.write('\n'+"="*30+'\n'+restype+'\n'+"="*30+'\n')
            groups = self.groups[restype].group_data.keys()
            groups.sort()
            for group in groups:
                d = self.groups[restype].group_data[group]
                #datafile.write("-"*15+'\n'+group+'\n'+"-"*15+"\n")
                #datafile.write("n = %i\n"%d['n'])
                #datafile.write("mean = %f\n"%d['mean'])
                #datafile.write("std = %f\n"%d['std'])
                #datafile.write("T = %s\n"%list2str(d['x']))
                #datafile.write("%s = %s\n"%(restype,list2str(d['y'])))
                if not times:
                    times = d['x']
                outdatas.append(d['y'])
        for i,t in enumerate(times):
            out = ["%.3f"%t]
            for vec in outdatas:
                if vec[i] < 1e-3:
                    out.append("%.5e"%vec[i])
                else:
                    out.append("%.5f"%vec[i])
            datafile.write(", ".join(out) + "\n")
        txt = 'Results saved to:\n%s'%datafilename
        QG.QMessageBox.information(self,'Success',txt)

    def addResPlot(self, name, yval, xval,groups, size, plottype, color,append):
        groupsdata = {}
        glines = []
        print 'add res', name, yval, xval
        if groups:
            for i,g in enumerate(groups):
                x0 = g[1][0]
                x1 = g[1][1]
                glines.append(x1)
                r = g[0]
                gdata = []
                xvals =[]
                for x,y in zip(xval,yval):
                    if x>=x0 and x<x1:
                        gdata.append(y)
                        xvals.append(x)
                gdata=n.array(gdata)
                fillcolor = r.selection_type.appearance.fillcolor
                print 'here',r,dir(r),fillcolor
                groupsdata['Group %i'%i] = {'mean':gdata.mean(),
                        'std':gdata.std(),'n':len(gdata),
                        'color':fillcolor,'y':gdata,'x':xvals}
        else:
            gdata = n.array(yval)
            groupsdata['Group 1'] = {'mean':gdata.mean(),
                    'std':gdata.std(),'n':len(gdata),
                    'color':'white','y':gdata,'x':xval}
        dm = GroupDataModel()
        dm.setData(groupsdata)
        self.groups[name]=dm
        print groupsdata
        if glines:
            glines.pop()
        plot_widget = QG.QWidget()
        layout = QG.QVBoxLayout()
        plot_widget.setLayout(layout)
        plot = ContinousPlotWidget(sceneClass = FDisplay, parent = plot_widget)
        plot.updateLocation.connect(self.updateCoords)
        layout.addWidget(plot)
        #w = QG.QWidget()
        #w.setMaximumHeight(120)
        #w.setLayout(QG.QHBoxLayout())
        #w.layout().setContentsMargins(1,1,1,1)
        tableview = QG.QTableView()
        #w.layout().addWidget(tableview)
        #tableview.setMaximumHeight(130)
        #tableview.setMinimumWidth(450)
        tableview.setModel(dm)
        tableview.setSizePolicy(QG.QSizePolicy.Maximum, QG.QSizePolicy.Maximum)
        #w.setSizePolicy(QG.QSizePolicy.Minimum,QG.QSizePolicy.Minimum)
        #plot.extendControlArea(w)
        layout.addWidget(tableview)
        layout.setStretchFactor(tableview, 1)
        layout.setStretchFactor(plot, 4)

        self.addTab(plot_widget,name)
        self.setCurrentIndex(self.count()-1)
        size = 0.1
        plot.addPlot(name, yval, xval, size = size,
                type = plottype,color = color,append = append)
        for g in glines:
            try:
                plot.makeHLine(g,'orange')
            except:
                pass
        #for i,gg in enumerate(groupsdata.keys()):
        #    g = groupsdata[gg]
        #    print g
        #    plot.addPlot(name + " "+gg,g['y'],g['x'],size = size,type =plottype,color = g['color'],append = append)
        #plot.addPlot(name+"_",yval,xval,size = 0.1,type =plottype,color = 'red',append = append)

        self.setCurrentIndex(self.count()-1)
        plot.fitView(0)
    def setc(self, t):
        #self.widget(t).fitView(0)
        print t
    def updateCoords(self, xv, yv, xs, ys):
        #self.status.showMessage('x: %.3f, y: %.3f, sx: %i, sy: %i'%(xv, yv, xs, ys))
        self.emit(QC.SIGNAL('positionTXT(QString)'),'x: %.3f , y: %.2f , sx: %i, sy: %i'%(xv,yv,xs,ys))
