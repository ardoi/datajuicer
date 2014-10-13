#!/usr/bin/env python
"""Main execution file for the application"""
import sys
import time
from subprocess import Popen, PIPE

from PyQt5 import QtWidgets as QW
from PyQt5 import QtGui as QG
from PyQt5 import QtCore as QC

from lsjuicer.util import config
from lsjuicer.util import logger
from lsjuicer.inout.db import sqlbase
from lsjuicer.ui.windows.main import MainUI


def java_check(parent):
    java_cmd = "java -version"
    p = Popen(java_cmd, shell=True, stdout=PIPE, stderr=PIPE)
    retcode = p.wait()
    if retcode:
        QW.QMessageBox.warning(parent, 'Java missing', """<html>It appears you do not
        have Java installed.  It is needed to convert files into a readable
        format. Please download it from here: <a
        href="http://java.com/en/download/index.jsp">http://java.com</a>,
        install it and restart this program</html>""")
        return False
    return True


def dependencies_for_myprogram():
    #for creating package blobs
    from scipy.sparse.csgraph import _validation
    pass

if __name__ == "__main__":
    app = QW.QApplication(sys.argv)
    # app.setStyle(QtGui.QStyleFactory.create('GTK+'))
    # app.setStyle(QtGui.QStyleFactory.create('Plastique'))
    app.setStyle(QW.QStyleFactory.create('Fusion'))
    #app.setStyle(QW.QStyleFactory.create('Macintosh (aqua)'))
    #make sure icons are shown in menus
    app.setAttribute(QC.Qt.AA_DontShowIconsInMenus, on = False)

    log = logger.get_logger(__name__)
    log.info('Available styles: %s' % (str(" : ".join(QW.QStyleFactory.keys()))))

    logo = QG.QPixmap(":/juicerlogo.png")
    t0 = time.time()
    min_splash_time = 4
    splash = QW.QSplashScreen(logo)
    splash.show()
    app.processEvents()

    gui = MainUI()
    ret = java_check(gui)
    if not ret:
        gui.close()
        app.exit()
    else:
        #Remove unnecessary prompt input to avoid conflicts with embedded IPython
        QC.pyqtRemoveInputHook()
        gui.show()
        gui.showMaximized()
        gui.raise_()
        #keep the splash up for a while
        if time.time() - t0 < min_splash_time:
            time.sleep(1)
        splash.close()

        app.exec_()
