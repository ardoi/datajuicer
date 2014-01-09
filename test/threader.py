import lsjuicer.util.threader as t
from PyQt5 import QtCore as QC
import logging
if __name__=="__main__":
    app = QC.QCoreApplication([])
    threader = t.Threader()
    params = []
    logging.basicConfig(level=logging.INFO)
    count = 500000
    for i in range(count):
        params.append({'data':i, 'coords':(0,i)})
    settings = {'height':count, 'width':1, 'dy':0, 'dx':0}
    threader.do(params, settings)
    timer =  QC.QTimer()
    timer.timeout.connect(threader.update)
    threader.threads_done.connect(timer.stop)
    timer.start(3000)
    app.exec_()
