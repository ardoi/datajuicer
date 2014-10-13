#!/usr/bin/env python
"""Main execution file for the application"""
import os
import sys
from subprocess import Popen, PIPE

from PyQt5 import QtWidgets
from PyQt5 import QtCore as QC

from lsjuicer.util import config, logger
from lsjuicer.ui.windows.main import MainUI


def java_check(parent):
    java_cmd = "java -version"
    p = Popen(java_cmd, shell=True, stdout=PIPE, stderr=PIPE)
    retcode = p.wait()
    if retcode:
        QtWidgets.QMessageBox.warning(parent, 'Java missing', """<html>It appears you do not
        have Java installed.  It is needed to convert files into a readable
        format. Please download it from here: <a
        href="http://java.com/en/download/index.jsp">http://java.com</a>,
        install it and restart this program</html>""")
        return False
    return True


def dependencies_for_myprogram():
    #for creating package blobs
    from scipy.sparse.csgraph import _validation
    id(_validation)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # app.setStyle(QtGui.QStyleFactory.create('GTK+'))
    # app.setStyle(QtGui.QStyleFactory.create('Plastique'))
    app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
    #app.setStyle(QtWidgets.QStyleFactory.create('Macintosh (aqua)'))
    #make sure icons are shown in menus
    app.setAttribute(QC.Qt.AA_DontShowIconsInMenus, on = False)

    log = logger.get_logger(__name__)
    log.info('Available styles: %s' % (str(" : ".join(QtWidgets.QStyleFactory.keys()))))

    #logo = QtGui.QPixmap(":/juicerlogo.png")
    # splash = QtGui.QSplashScreen(logo)
    # splash.show()
    app.processEvents()

    # ome_folder = os.path.join(os.getenv('HOME'), '.JuicerTemp')
    # if not os.path.isdir(ome_folder):
    #    os.makedirs(ome_folder)
    # util.config.Config.set_property('ome_folder', ome_folder)

    config.default_configuration()
    ome_folder = config.dbmaster.get_config_setting_value('ome_folder')
    if not os.path.isdir(ome_folder):
        os.mkdir(ome_folder)
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
        app.exec_()
