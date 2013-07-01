#from PyQt4 import QtGui as QG
#
#from ui.scenes import LSMSparkDisplay
#from ui.tabs import AnalysisImageTab
#from ui.widgets import ImagePlotWidget, AnalysisWidget
#from util import helpers
#
#class SparkAnalysisImageTab(AnalysisImageTab):
#
#    def makePlotArea(self):
#        return ImagePlotWidget(sceneClass=LSMSparkDisplay)
#    def show_image(self,image):
#        self.startPB.setEnabled(True)
#        AnalysisWidget.show_image(self,image)
#    def makeButtons(self):
#        self.lsmCombo  = QG.QComboBox( )
#        self.lsmCombo.addItem("Use whole screen")
#        self.lsmCombo.addItem("Fit to screen")
#        self.lsmCombo.addItem("Full size")
#        self.lsmCombo.setEnabled(False)
#        self.lsmButtonLayout.addWidget(self.lsmCombo)
#        
#        plotIcon=QG.QIcon(":/chart_curve_go.png")
#        self.lsmPB  = QG.QPushButton(plotIcon,'Plot F')
#        self.lsmPB.setEnabled(False)
#        self.lsmButtonLayout.addWidget(self.lsmPB)
#        
#        #self.lsmROIButtonBox = QGroupBox('ROI selection')
#        ##self.lsmROIButtonBox.setEnabled(False)
#        #ROI_HB = QHBoxLayout()
#        #ROI_VB1 = QVBoxLayout()
#        #ROI_VB2 = QVBoxLayout()
#        #self.lsmROIButtonBox.setLayout(ROI_HB)
#        #ROI_HB.addLayout(ROI_VB1)
#        #ROI_HB.addLayout(ROI_VB2)
#        #self.startPB = QPushButton('Select ROIS')
#        #self.startPB.setCheckable(True)
#        #self.startPB.setEnabled(False)
#        #self.nextPB = QPushButton('Next')
#        #self.nextPB.setEnabled(False)
#        #self.clearLastPB = QPushButton('Clear last')
#        #self.clearAllPB = QPushButton('Clear all')
#        #ROI_VB1.addWidget(self.startPB)
#        #ROI_VB1.addWidget(self.nextPB)
#        #ROI_VB2.addWidget(self.clearLastPB)
#        #ROI_VB2.addWidget(self.clearAllPB)
#        #self.clearLastPB.setEnabled(False)
#        #self.clearAllPB.setEnabled(False)
#
#        #self.lsmButtonLayout.addWidget(self.lsmROIButtonBox)
##        self.lsmButtonLayout.addWidget(QG.QScroll
#        self.lsmButtonLayout.addStretch()
#        
#        #self.connect(self.startPB,QC.SIGNAL('toggled(bool)'),self.select)
#        #self.connect(self.nextPB,QC.SIGNAL('clicked()'),self.next)
#        #self.connect(self.lsmPlot,QC.SIGNAL('updateLocation(int,int)'),self.updateCoords)
#        #self.connect(self.lsmPB,QC.SIGNAL('clicked()'),self.plotF)
#        #self.connect(self.clearLastPB,QC.SIGNAL('clicked()'),self.clearLast)
#        #self.connect(self.clearAllPB,QC.SIGNAL('clicked()'),self.clearAll)
#        #self.connect(self.lsmCombo,QC.SIGNAL('currentIndexChanged(int)'),self.on_lsmCombo_changed)
#    
#    def clearAll(self):
#        self.lsmPlot.fscene.clear_ROIS()
#        self.lsmPB.setEnabled(False)
#    def clearLast(self):
#        self.lsmPlot.fscene.clearLast()
#        if len(self.lsmPlot.fscene.ROIS) == 0:
#            self.lsmPB.setEnabled(False)
#
#    def next(self):
#        self.lsmPlot.fscene.nextROI()
#    
#    def updateCoords(self,x,y):
#        xv = self.data.timestamps[x]
#        yv = self.data.y_step*y/1e-6
#        self.parent.status.showMessage('x: %.3f [s], y: %.1f [um], sx: %i, sy: %i'%(xv,yv,x,y))
#
#    def select(self,start):
#        self.lsmPlot.fscene.toggleSelectionMode(start)
#        self.nextPB.setEnabled(start)
#        #print 'width', 1e-6/self.data.y_step
#        self.lsmPlot.fscene.setMidWidth(1e-6/self.data.y_step)
#        if start:
#            self.clearLastPB.setEnabled(False)
#            self.clearAllPB.setEnabled(False)
#            self.lsmPB.setEnabled(False)
#        else:
#            if len(self.lsmPlot.fscene.ROIS) > 0:
#                self.lsmPB.setEnabled(True)
#                self.clearLastPB.setEnabled(True)
#                self.clearAllPB.setEnabled(True)
#
#    def resetButtons(self):
#        self.startPB.setChecked(False)
#        self.lsmPB.setEnabled(False)
#        self.clearLastPB.setEnabled(False)
#        self.clearAllPB.setEnabled(False)
#    
#    def on_lsmCombo_changed(self, value):
#        self.lsmPlot.fitView(value)
#    
#    def enableButtons(self,on):
#        if on:
#            self.lsmCombo.setEnabled(True)
#    
#    def write_out(self,fname,imname):
#        comment,ok = QG.QInputDialog.getText(self,'info','Please give comment for this lsm file', QG.QLineEdit.Normal,self.data.notes)
#        comment = str(comment)
#        if not ok:
#            return False
#        outfile = open(fname, 'w')
#        outfile.write( "\n\nImage file: %s\n"%imname )
#        if len(comment)>0:
#            outfile.write("Comment: %s\n"%comment )  
#        #if len(self.event_times)>0:
#        #    outfile.write( 'Events: ' + list_2_str(self.event_times,2) )
#        #    outfile.write("\n")
#        for tab in range(1,self.parent.tabs.count()):
#            datastruct = self.parent.tabs.widget(tab).ds
#            outfile.write('Region %i'%(tab))
#            outfile.write('\n')
#            try:
#                outfile.write( 'Positions: ' + helpers.list_2_str( datastruct.transientGroup.times ) )
#                outfile.write("\n")
#                outfile.write( 'Amplitudes: ' + helpers.list_2_str( datastruct.transientGroup.bl_amps_div ) )
#                outfile.write("\n")
#            except:
#                pass
#            try:
#                outfile.write('Delays: ' + helpers.list_2_str( datastruct.transientGroup.delays ) )
#                outfile.write("\n")
#            except:
#                pass
#            try:
#                outfile.write( 'Decay times: ' + helpers.list_2_str( datastruct.transientGroup.decays ) )
#                outfile.write("\n")
#            except:
#                pass
#            try:
#                outfile.write( 'Halftimes: ' + helpers.list_2_str( datastruct.transientGroup.halftimes ) )
#                outfile.write("\n")
#            except:
#                pass
#            try:
#                outfile.write( 'A2/A1: ' + helpers.list_2_str(datastruct.transientGroup.A2A1_ratios ))
#                outfile.write("\n")
#                outfile.write("\n")
#                outfile.write( 'A2/A1 delays: ' + helpers.list_2_str(datastruct.transientGroup.A2A1_delays ))
#                outfile.write("\n")
#                outfile.write( 'A2/A1 indexes: ' +
#                        helpers.list_2_str(datastruct.transientGroup.A2A1_indexes ))
#                outfile.write("\n")
#                outfile.write( 'A2/A1 amps: ' +
#                        helpers.list_2_str(datastruct.transientGroup.A2A1_amps ))
#                outfile.write("\n")
#            except:
#                pass
#        outfile.flush()
#        outfile.close() 
#        return True
#
