from multiprocessing import Process, cpu_count
import datetime
import logging
import random
import time
import os
import traceback

from PyQt5 import QtCore as QC

from PyQt5 import QtWidgets as QW

import numpy as np
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from lsjuicer.inout.db import sqlb2
from lsjuicer.data.analysis import transient_find as tf


class Worker(Process):

    def __init__(self, args):
        Process.__init__(self)
        dbmaster = sqlb2.dbmaster
        session = dbmaster.get_session()
        self.worker = sqlb2.Worker()
        self.worker.id = args[0]
        self.current_job_id = None
        session.add(self.worker)
        #session.commit()
        #session.close()
        dbmaster.end_session_retry(session)
        self.logger = logging.getLogger(__name__)

    def kill(self):
        session = sqlb2.dbmaster.get_session()
        session.add(self.worker)
        try:
            current_job = session.query(sqlb2.Job).\
                filter(sqlb2.Job.worker_id == self.worker.id).\
                filter(sqlb2.Job.running == True).one()
            current_job.running = False
            current_job.timed_out = True
            current_job.finished = True
            current_job.end_time = datetime.datetime.now()
            self.logger.warning("killing worker %i, job %i" % (
                self.worker.id, current_job.id))
        except NoResultFound:
            self.logger.warning("killing worker %i cancelled" % self.worker.id)
            # the job has finished so no need to kill anything
            return False
        except MultipleResultsFound:
            raise RuntimeError
        self.worker.end_time = datetime.datetime.now()
        #session.commit()
        #session.close()
        sqlb2.dbmaster.end_session_retry(session)
        # self.session.commit()
        # self.session.close()
        self.terminate()
        return True

    def single(self, job_params):
        args = job_params
        data = args['data']
        # xy = args['coords']
        self.logger.debug("job %i starting" %( self.current_job_id))
        #self.logger.info("job %i starting, pid=%i, ppid=%i" %( self.current_job_id,os.getpid(),os.getppid()))
        try:
            # f = tf.fit_regs(data)
            f = tf.fit_2_stage(data)
            #rr = random.random()
            #if rr<0.01:
            #    duration = 10 * random.randint(1,6)
            #    self.logger.warning("job %i LONG SLEEP %i" %( self.current_job_id,duration))
            #    time.sleep(duration)
            #else:
            #    time.sleep(.1)
            #f = 1.0
            #if random.random()<0.01:
            #    f = None
        except:
            # self.logger.debug("job %i failed"%self.current_job_id)
            #print '\n\n\nboooooo'
            self.logger.warning("job %i failed %s" % (
                self.current_job_id, traceback.format_exc()))
            f = None
        self.logger.debug("job %i returning" % self.current_job_id)
        return f

    def run(self):
        dbmaster = sqlb2.dbmaster
        session = dbmaster.get_session()
        session.add(self.worker)
        self.logger.debug('worker %i starting' % self.worker.id)
        self.worker.start_time = datetime.datetime.now()
        self.worker.running = True

        jobs = session.query(sqlb2.Job).filter(
            sqlb2.Job.worker_id == self.worker.id).all()
        #session.commit()
        #session.close()
        dbmaster.end_session_retry(session)

        for job in jobs:
            session = dbmaster.get_session()
            session.add(self.worker)
            session.add(job)

            self.logger.debug('worker %i, started job %i' % (
                self.worker.id, job.id))
            job.start_time = datetime.datetime.now()

            job.running = True
            self.worker.running_job = job.id
            self.current_job_id = job.id
            self.worker.job_start_time = job.start_time
            self.worker.job_end_time = None
            job_params = job.params
            dbmaster.end_session_retry(session)
            #session.commit()
            #close session so that we dont block the db
            #session.close()
            result = self.single(job_params)
            #reopen session and add job and worker
            session = dbmaster.get_session()
            session.add(self.worker)
            session.add(job)
            job.finished = True
            job.running = False
            if not result:
                job.failed = True
            job.result = result
            job.end_time = datetime.datetime.now()
            self.worker.job_end_time = job.end_time
            #session.commit()p
            self.logger.debug('worker %i, finished job %i' % (
                self.worker.id, job.id))
            #session.close()
            dbmaster.end_session_retry(session)

        session = dbmaster.get_session()
        session.add(self.worker)
        self.worker.finished = True
        self.worker.running = False
        self.worker.end_time = datetime.datetime.now()
        self.worker.locked_errors = dbmaster.lock_errors
        self.logger.debug('worker %i finished' % self.worker.id)
        #session.commit()
        #session.close()
        dbmaster.end_session_retry(session)
        return


class Threader(QC.QObject):
    threads_done = QC.pyqtSignal()
    progress_update = QC.pyqtSignal(int, int, int, int)
    time_stats = QC.pyqtSignal(float, float, float)
    new_progress_array = QC.pyqtSignal()

    def stop(self):
        for wn in self.running_workers:
            w = self.workers[wn]
            w.kill()

    def update(self):
        if self.start_time is None:
            self.start_time = time.time()
            self.run_times = []

        self.logger.info("UPDATE")
        newly_finished = []
        kill_list = []
        time_limit = 30
        jobs_per_worker = 50
        session = sqlb2.dbmaster.get_session()
        for i, wn in enumerate(self.running_workers):
            # w = self.workers[wn]
            w = session.query(sqlb2.Worker).filter(sqlb2.Worker.id == wn).one()
            if w.finished:
                newly_finished.append(wn)
                self.run_times.append(w.run_time)
                continue
            #try:
            #    running_job = w.running_job
            #    if running_job is  None:
            #        running_job = 0
            #    self.logger.debug("worker %i,%i, time %.3f, current %i" % (
            #        w.id, wn, w.run_time, running_job))
            #except TypeError:
            #    import traceback
            #    traceback.print_exc()
            #    self.logger.error("worker %i,%i finished error" % (w.id, wn))

            if w.job_run_time > time_limit:
                self.logger.debug('kill %i' % wn)
                kill_list.append(wn)
        # session.close()
        for wn in kill_list:
            w = self.workers[wn]
            self.logger.debug("killing %i" % wn)
            status = w.kill()
            if not status:
                self.logger.debug("nothing to kill")
                continue
            # session = sqlb2.dbmaster.get_session()
            sql_w = session.query(sqlb2.Worker).filter(
                sqlb2.Worker.id == wn).one()
            self.run_times.append(sql_w.run_time)
            self.running_workers.remove(wn)
            undone_jobs = session.query(sqlb2.Job).\
                filter(sqlb2.Job.worker_id == wn).\
                filter(sqlb2.Job.finished == False).\
                filter(sqlb2.Job.timed_out == False).\
                filter(sqlb2.Job.failed == False).all()
            if undone_jobs:
                for job in undone_jobs:
                    job.worked_id = None
                undone_job_numbers = [job.id for job in undone_jobs]
                self.logger.debug("reinsert %i" % len(undone_job_numbers))
                # print "waiting old",len(self.waiting_jobs)
                # print self.waiting_jobs
                self.waiting_jobs = self.waiting_jobs.union(undone_job_numbers)
                self.logger.debug("after reinsert waiting  %i" % len(
                    self.waiting_jobs))
                # print self.waiting_jobs
            session.commit()
            # session.close()

        # session = sqlb2.dbmaster.get_session()
        for wn in newly_finished:
            self.running_workers.remove(wn)
            self.finished_workers.append(wn)
            # for making job progress plot
            worker_jobs = session.query(
                sqlb2.Job).filter(sqlb2.Job.worker_id == wn)
            for job in worker_jobs:
                xy = job.params['coords']
                x = xy[0]  # - self.settings['dx']
                y = xy[1]  # - self.settings['dy']
                try:
                    if job.failed:
                        self.state_array[y, x] = 2
                    elif job.timed_out:
                        self.state_array[y, x] = 3
                    else:
                        self.state_array[y, x] = 1
                except:
                    import traceback
                    traceback.print_exc()
                    print self.state_array
                    print self.state_array.shape
                    print x, y
        if newly_finished:
            self.new_progress_array.emit()

        # session.close()

        #print "before new Remaining: %i"%(len(self.waiting_jobs))
        running = len(self.running_workers)
        empty_slots = self.slots - running
        self.logger.debug("running workers before start %i %s" % (
            running, str(self.running_workers)))
        self.logger.debug("waiting jobs before start %i" % len(
            self.waiting_jobs))
        started_now = 0
        if self.waiting_jobs:
            for i in range(empty_slots):
                job_numbers = self.get_job_numbers(jobs_per_worker)
                if not job_numbers:
                    break
                wn = self.last_started_worker_number + 1
                self.last_started_worker_number = wn
                jobs = session.query(sqlb2.Job).filter(
                    sqlb2.Job.id.in_(job_numbers)).all()
                for job in jobs:
                    job.worker_id = wn
                session.commit()
                # session.close()

                worker = Worker(args=(wn,))
                self.running_workers.append(wn)
                self.workers[wn] = worker
                worker.start()
                started_now += 1

        self.logger.debug(
            "running workers after start %i %s" % (len(self.running_workers),
                                                   str(self.running_workers)))
        self.logger.debug("waiting jobs after start %i" % len(
            self.waiting_jobs))
        # session = sqlb2.dbmaster.get_session()
        finished_jobs = session.query(sqlb2.Job).filter(
            sqlb2.Job.finished == True).count()
        timed_out_jobs = session.query(sqlb2.Job).filter(
            sqlb2.Job.timed_out == True).count()
        running_jobs = session.query(sqlb2.Job).filter(
            sqlb2.Job.running == True).count()
        failed_jobs = session.query(sqlb2.Job).filter(
            sqlb2.Job.failed == True).count()

        time_so_far = int(time.time() - self.start_time)

        successful_jobs = finished_jobs - timed_out_jobs - failed_jobs
        jobs_remaining = self.jobs_to_run - finished_jobs
        if finished_jobs:
            mean_time_per_done_job = time_so_far / float(finished_jobs)
            time_left = int(jobs_remaining * mean_time_per_done_job)
            self.time_stats.emit(
                mean_time_per_done_job, time_left, time_so_far)
            self.progress_update.emit(jobs_remaining, finished_jobs,
                                      timed_out_jobs, failed_jobs)

        self.logger.info("Remaining: %i\t Finished:%i" % (
            jobs_remaining, finished_jobs))
        self.logger.info("Successful:%i\t Failed:%i" % (
            successful_jobs, failed_jobs))
        self.logger.info("Timed out: %i\t Running:%i" % (
            timed_out_jobs, running_jobs))
        if finished_jobs == self.jobs_to_run:
            print "ALL DONE. Stopping timer"
            total_time = time.time() - self.start_time
            computational_time = sum(self.run_times)
            average_comp_time = computational_time / float(len(self.run_times))
            finished_jobs = session.query(
                sqlb2.Job).filter(sqlb2.Job.finished == True)
            job_run_times = np.array([job.run_time for job in finished_jobs])
            print "TIMINGS: total:%.1f sec,\tcomputational: %.1f,\taverage per job: %.3f" %\
                (total_time, computational_time, average_comp_time)
            print job_run_times.mean(), job_run_times.min(), job_run_times.max()
            error_count = 0
            for c, in session.query(sqlb2.Worker.locked_errors).all():
                error_count+=c
            print 'db errors:%i'%error_count
            # print "RESULTS ",self.out_data
            # qc=QC.QCoreApplication.instance()
            # qc.exit()
            self.threads_done.emit()
        session.commit()
        session.close()

    def get_job_numbers(self, count):
        selection = random.sample(self.waiting_jobs, min(
            count, len(self.waiting_jobs)))
        self.waiting_jobs.difference_update(selection)
        return selection

    def __init__(self, parent=None):
        QC.QObject.__init__(self, parent)
        self.waiting_workers = []
        self.running_workers = []
        self.finished_workers = []
        self.failed_workers = []
        self.workers = {}
        self.start_time = None

        self.slots = cpu_count() - 1
        self.last_started_worker_number = 0
        self.logger = logging.getLogger(__name__)

    def do(self, params, settings):
        sqlb2.dbmaster.reset_tables()
        session = sqlb2.dbmaster.get_session()
        self.jobs_to_run = len(params)
        self.settings = settings
        self.state_array = np.zeros(
            shape=(settings['height'] - 2 * settings['dy'],
                   settings['width'] - 2 * settings['dx']))
        for i, param in enumerate(params):
            job = sqlb2.Job()
            job.params = param
            session.add(job)
        session.commit()
        session.close()
        #+1 because in sql id cannot be 0
        self.waiting_jobs = set(range(1, self.jobs_to_run + 1))
        self.running_jobs = []
        self.finished_jobs = []
        self.failed_jobs = []


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
