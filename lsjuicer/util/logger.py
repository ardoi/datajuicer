import logging
import time
import os

class Logger(object):
    def __init__(self, level=logging.INFO):
        start_time_and_date = time.strftime("%d-%b-%Y__%H-%M-%S")
        logfolder = 'log'
        # check for folder existance and create if necessary
        print logfolder
        if not os.path.isdir(logfolder):
            print 'make'
            os.makedirs(logfolder)
        loglevel = level
        logfilename = "juicer_" + start_time_and_date + ".log"
        logfilefullname = os.path.join(logfolder, logfilename)
        self.logfilename = logfilefullname
        log_format = "%(levelname)s:%(name)s:%(funcName)s: %(lineno)d:%(asctime)s %(message)s"
        logging.basicConfig(filename=logfilefullname,
                            level=loglevel, filemode='w', format=log_format)
        logger = logging.getLogger(__name__)
        logger.info('starting')
        print "started"

    def get_logger(self, name):
        return logging.getLogger(name)

logger = Logger()
def get_logger(name):
    return logger.get_logger(name)

