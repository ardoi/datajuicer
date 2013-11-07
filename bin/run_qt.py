#!/usr/bin/env python
"""Main execution file for the application"""
import time
import os
import sys
import logging
from subprocess import Popen, PIPE

from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore as QC

from lsjuicer.util import config
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
    print 'Available styles: %s' % (str(" : ".join(QtWidgets.QStyleFactory.keys())))
    logo = QtGui.QPixmap(":/juicerlogo.png")
    # splash = QtGui.QSplashScreen(logo)
    # splash.show()
    app.processEvents()
    # time.sleep(1)
    #screen_size = app.desktop().screenGeometry()
    # splash.hide()

    # defaults for conf file
    # username = os.getlogin()
    # defaults = {'basedir':'/home/%s/.config/lsjuicer'%username}
    # cp = ConfigParser.ConfigParser(defaults)

    # logging setup
    # cp.read('config.ini')
    # logfolder = cp.get('logging', 'logfolder')
    # check for folder existance and create if necessary
    # if not os.path.isdir(logfolder):
    #    os.makedirs(logfolder)
    # try:
    #    loglevel = int(cp.get('logging', 'loglevel'))
    #    assert loglevel in range(0, 60, 10)
    # except (AssertionError, ValueError):
    #    print 'fallback'
    #    loglevel = logging.INFO
    # filetype = 'csv'
    # filetype = 'oib'
    # util.config.Config.set_property('filetype', filetype)
    # shelf_db = shelve.open('db.shelf',writeback = True)
    # util.config.Config.set_property('shelf_db', shelf_db)
    # util.config.init_config(shelf_db)
    start_time_and_date = time.strftime("%d-%b-%Y__%H-%M-%S")

    logfolder = 'log'
    # check for folder existance and create if necessary
    if not os.path.isdir(logfolder):
        os.makedirs(logfolder)
    #loglevel = logging.INFO
    loglevel = logging.INFO
    logfilename = "juicer_" + start_time_and_date + ".log"
    logfilefullname = os.path.join(logfolder, logfilename)
    log_format = "%(levelname)s:%(name)s:%(funcName)s:\
            %(lineno)d:%(asctime)s %(message)s"
    logging.basicConfig(filename=logfilefullname,
                        level=loglevel, filemode='w', format=log_format)
    logger = logging.getLogger(__name__)
    logger.info('starting')

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
        gui.show()
        gui.showMaximized()
        gui.raise_()
        app.exec_()
