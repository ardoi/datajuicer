from multiprocessing import Process, cpu_count
import datetime
import random
import time
import os
import traceback

from PyQt5 import QtCore as QC

from PyQt5 import QtWidgets as QW

import numpy as np
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from lsjuicer.data.analysis import transient_find as tf
import lsjuicer.util.logger as logger

from IPython import parallel

def single(args):
    data = args['data']
    import lsjuicer.data.analysis.transient_find as tf
    try:
        f = tf.fit_2_stage(data, min_snr=5.5)
        error = None
    except:
        import traceback
        error=traceback.format_exc()
        f = None
    return args['coords'], f, error


class Threader(object):
    #threads_done = QC.pyqtSignal()
    #progress_update = QC.pyqtSignal(int, int, int, int)
    #time_stats = QC.pyqtSignal(float, float, float)
    #new_progress_array = QC.pyqtSignal()


    def update(self):
        if self.start_time is None:
            self.start_time = time.time()
            #self.run_times []

        self.logger.info("UPDATE")
        newly_finished = []
        if not self.view_result:
            self.logger.info("Start {} jobs".format(self.jobs_to_run))
            self.view_result = self.view.map_async(single, self.params)#, chunksize=self.chunk)
            self.waiting = set(self.view_result.msg_ids)
            self.failed = 0
        try:
            self.client.wait(self.waiting, 1e-3)
        except parallel.TimeoutError:
            pass
        finished = self.waiting.difference(self.client.outstanding)
        self.waiting = self.waiting.difference(finished)
        self.logger.info('waiting: {}'.format(len(self.waiting)*self.chunk))
        self.logger.info('newly finished: {}'.format(len(finished)*self.chunk))
        self.logger.info('failed: {}'.format(self.failed))

        for job_id in finished:
            result = self.client.get_result(job_id)
            print "job {} finished on engine {}".format(job_id, result.engine_id)
            for res in result.result:
                xy = res[0]
                x = xy[0]  # - self.settings['dx']
                y = xy[1]  # - self.settings['dy']
                self.results[xy] = res[1]
                try:
                    if res[1]:
                        self.state_array[y, x] = 1
                    else:
                        self.state_array[y, x] = 2
                        self.failed += 1
                        self.errors[xy] = res[2]
                except:
                    import traceback
                    self.logger.warning(traceback.format_exc())

        time_so_far = int(time.time() - self.start_time)
        self.logger.info("time: {} sec".format(time_so_far))


    def __init__(self):
        #QC.QObject.__init__(self, parent)
        self.waiting_workers = []
        self.running_workers = []
        self.finished_workers = []
        self.failed_workers = []
        self.workers = {}
        self.start_time = None
        self.end_time = None
        self.done = None

        self.slots = cpu_count() - 1
        self.logger = logger.get_logger(__name__)
        self.client = parallel.Client()
        self.view = self.client.load_balanced_view()
        self.logger.info("start Threader")
        #self.view = self.client.direct_view()
        #self.view.execute("import lsjuicer.data.analysis.transient_find as tf")
        self.view_result = None
        self.actual_slots = len(self.client.ids)
        self.results = {}
        self.errors = {}
        self.chunk = 1


    def do(self, params, settings):
        self.jobs_to_run = len(params)
        self.settings = settings
        self.params = params
        self.state_array = np.zeros(
            shape=(settings['height'] - 2 * settings['dy'],
                   settings['width'] - 2 * settings['dx']))

    def run(self):
        self.update()
        while len(self.waiting) > 0:
            time.sleep(5)
            self.update()
        self.done = True
        self.end_time = time.time()
        av_time = (self.end_time - self.start_time)/float(self.jobs_to_run)
        logger.info("time per job={}".format(av_time))
        logger.info("time per job (actual)={}".format(av_time*self.actual_slots))
        self.client.close()


class FitDialog(QW.QDialog):
    progress_map_update = QC.pyqtSignal(np.ndarray)

    def __init__(self, parameters, settings, parent=None):
        QW.QDialog.__init__(self, parent)

        self.d = Threader(self)
        self.d.do(parameters, settings)

        self.timer = QC.QTimer(self)
        self.timer.timeout.connect(self.d.update)

        self.d.threads_done.connect(self.timer.stop)
        self.d.threads_done.connect(self.threader_done)
        self.d.progress_update.connect(self.update_progress)
        self.d.time_stats.connect(self.update_timings)
        self.d.new_progress_array.connect(self.update_progress_pixmap)

        layout = QW.QVBoxLayout()
        self.setLayout(layout)

        progress_layout = QW.QGridLayout()
        layout.addLayout(progress_layout)

        # waiting_layout = QG.QHBoxLayout()
        # progress_layout.addLayout(waiting_layout)
        label = QW.QLabel("Waiting")
        waiting_progress = QW.QProgressBar()
        waiting_progress.setMinimum(0)
        waiting_progress.setValue(0)
        waiting_progress.setMaximum(self.d.jobs_to_run)
        # waiting_progress.setStyleSheet(self.make_progress_style("skyblue"))
        waiting_label = QW.QLabel()
        self.waiting_progress = waiting_progress
        self.waiting_label = waiting_label
        progress_layout.addWidget(label, 0, 0)
        progress_layout.addWidget(waiting_progress, 0, 1)
        progress_layout.addWidget(waiting_label, 0, 2)

        label = QW.QLabel("Finished")
        finished_progress = QW.QProgressBar()
        finished_progress.setValue(0)
        # finished_progress.setStyleSheet(self.make_progress_style("lime"))
        finished_progress.setMinimum(0)
        finished_progress.setMaximum(self.d.jobs_to_run)
        finished_label = QW.QLabel()
        self.finished_progress = finished_progress
        self.finished_label = finished_label
        progress_layout.addWidget(label, 1, 0)
        progress_layout.addWidget(finished_progress, 1, 1)
        progress_layout.addWidget(finished_label, 1, 2)

        label = QW.QLabel("Failed")
        failed_progress = QW.QProgressBar()
        # style = self.make_progress_style("red")
        # failed_progress.setStyleSheet(style)
        failed_progress.setMinimum(0)
        failed_progress.setMaximum(self.d.jobs_to_run)
        failed_label = QW.QLabel()
        self.failed_progress = failed_progress
        self.failed_label = failed_label
        progress_layout.addWidget(label, 2, 0)
        progress_layout.addWidget(failed_progress, 2, 1)
        progress_layout.addWidget(failed_label, 2, 2)

        label = QW.QLabel("Timed out")
        timed_out_progress = QW.QProgressBar()
        # timed_out_progress.setStyleSheet(self.make_progress_style("black"))
        timed_out_progress.setMinimum(0)
        timed_out_progress.setMaximum(self.d.jobs_to_run)
        timed_out_label = QW.QLabel()
        self.timed_out_progress = timed_out_progress
        self.timed_out_label = timed_out_label
        progress_layout.addWidget(label, 3, 0)
        progress_layout.addWidget(timed_out_progress, 3, 1)
        progress_layout.addWidget(timed_out_label, 3, 2)
        self.time_label = QW.QLabel()
        layout.addWidget(self.time_label)
        button_layout = QW.QHBoxLayout()
        stop_pb = QW.QPushButton("Stop")
        start_pb = QW.QPushButton("Start")
        save_pb = QW.QPushButton("Save")
        close_pb = QW.QPushButton("Close")

        button_layout.addWidget(start_pb)
        button_layout.addWidget(stop_pb)
        button_layout.addWidget(save_pb)
        button_layout.addWidget(close_pb)
        layout.addLayout(button_layout)
        stop_pb.clicked.connect(self.stop)
        start_pb.clicked.connect(self.start)
        close_pb.clicked.connect(self.close)
        save_pb.clicked.connect(self.save)
        self.stop_pb = stop_pb
        self.start_pb = start_pb
        self.close_pb = close_pb
        self.save_pb = save_pb
        self.success = False
        self.save_pb.setEnabled(False)
        self.stop_pb.setEnabled(False)

        self.update_progress(len(parameters), 0, 0, 0)

    def update_timings(self, per_job, left, so_far):
        out = "%.3f sec per job, %s elapsed, ~%s left" % \
            (per_job, str(datetime.timedelta(seconds=so_far)),
                str(datetime.timedelta(seconds=left)))
        self.time_label.setText(out)

    def update_progress(self, waiting, finished, timed_out, failed):
        self.waiting_progress.setValue(waiting)
        self.failed_progress.setValue(failed)
        self.finished_progress.setValue(finished)
        self.timed_out_progress.setValue(timed_out)

        self.waiting_label.setText("%i (%i%%)" % (
            waiting, 100*waiting/self.d.jobs_to_run))
        self.finished_label.setText("%i (%i%%)" % (
            finished, 100*finished/self.d.jobs_to_run))
        self.failed_label.setText("%i (%i%%)" % (
            failed, 100*failed/self.d.jobs_to_run))
        self.timed_out_label.setText("%i (%i%%)" % (
            timed_out, 100*timed_out/self.d.jobs_to_run))

    def update_progress_pixmap(self):
        self.progress_map_update.emit(self.d.state_array)

    def start(self):
        # when start button is clicked
        self.timer.start(5000)
        self.start_pb.setEnabled(False)
        self.stop_pb.setEnabled(True)
        self.close_pb.setEnabled(False)

    def stop(self):
        # when stop button is clicked
        self.timer.stop()
        self.d.stop()
        self.start_pb.setEnabled(True)
        self.stop_pb.setEnabled(False)
        self.close_pb.setEnabled(True)
        self.save_pb.setEnabled(True)
        self.success = False

    def threader_done(self):
        # when threader finishes
        self.success = True
        self.close_pb.setEnabled(True)
        self.stop_pb.setEnabled(False)
        self.start_pb.setEnabled(False)
        self.save_pb.setEnabled(False)

    def save(self):
        self.success = True

    def close(self):
        # when close button is clicked
        if self.success:
            self.accept()
        else:
            self.reject()

    def make_progress_style(self, color):
        out = """
         QProgressBar {
             border: 2px solid grey;
             border-radius: 5px;
         }
         QProgressBar::chunk {
             background-color: %s;
             width: 20px;
         }""" % color
        return out
