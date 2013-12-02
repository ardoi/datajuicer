import pickle

from PyQt5 import QtWidgets as QW

from PyQt5 import QtCore as QC

import PyQt5.QtNetwork as QN

class VersionChecker(QC.QObject):
    def __init__(self,version):
        self.version = version
    
    def checkVersion(self):
        self.url = QC.QUrl("http://lsjuicer.googlecode.com/files/version")
        self.buffer = QC.QBuffer()
        self.http = QN.QHttp()
        self.http.done[bool].connect(self.done)
        self.http.setHost(self.url.host())
        self.http.get(self.url.path(),self.buffer)
        self.http.close()
        print 'done',self.http.error()
        print 'd',self.buffer.data()
    
    def done(self,error):
        print 'done',error,self.http.error()
        if not error and len(self.buffer.data())>0:
            version_d = pickle.loads(self.buffer.data())
            print version_d
            versiontxt = ''
            k = version_d.keys()
            k.sort(reverse=True)
            #find where current version fits
            updates = []
            for i in k:
                if self.version<i:
                    updates.append(i)
            if len(updates) == 0:
                return
            else:
                versiontxt += 'A newer version of the program is available!\n'
                versiontxt += 'Newest version is: <b>%.3f</b>\nYour version is: <b>%.3f</b>\n'%(updates[0],self.version)
                versiontxt += 'Download it from <a href="http://code.google.com/p/lsjuicer/downloads/list">here</a>\n\n'
                versiontxt += '<b>New changes:</b>\n' 

            for key in updates:
                versiontxt+=' * '+version_d[key]+'\n'

            te = QW.QTextBrowser()
            te.setOpenExternalLinks(True)
            te.setHorizontalScrollBarPolicy(QC.Qt.ScrollBarAlwaysOff)
            te.setHtml(versiontxt.replace('\n','<br>'))
            
            infoL = QW.QHBoxLayout()
            infoL.addWidget(te)
            self.versiondialog = QW.QDialog()
            self.versiondialog.setWindowTitle('New version')
            self.versiondialog.setFixedWidth(350)
            self.versiondialog.setFixedHeight(300)
            self.versiondialog.setLayout(infoL)
            self.versiondialog.show()

