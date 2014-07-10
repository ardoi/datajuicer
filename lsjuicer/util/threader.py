from multiprocessing import cpu_count
import time
import random

import numpy as np

import lsjuicer.util.logger as logger
from lsjuicer.inout.converters.OMEXMLMaker import ShellRunner

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
        if not self.view_result:
            self.logger.info("Start {} jobs".format(self.jobs_to_run))
            random.shuffle(self.params)
            self.view_result = self.view.map_async(single, self.params, ordered=False)#, chunksize=self.chunk)
            self.waiting = set(self.view_result.msg_ids)
            self.failed = 0
        try:
            self.client.wait(self.waiting, 1e-3)
        except parallel.TimeoutError:
            pass
        just_finished = self.waiting.difference(self.client.outstanding)
        self.waiting = self.waiting.difference(just_finished)
        self.logger.info('waiting: {}'.format(len(self.waiting)*self.chunk))
        self.logger.info('just finished: {}'.format(len(just_finished)*self.chunk))
        self.logger.info('failed: {}'.format(self.failed))
        self.new_finished = bool(len(just_finished))

        for job_id in just_finished:
            result = self.client.get_result(job_id)
            self.logger.info("job {} finished on engine {}".
                             format(job_id, result.engine_id))
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
        jobs_left = len(self.waiting)
        jobs_done = self.jobs_to_run - jobs_left
        if jobs_done:
            time_per_job = time_so_far / float(jobs_done)
        else:
            time_per_job = 0
        time_left = int(time_per_job * jobs_left)
        self.timings = (time_per_job, time_left, time_so_far)
        print 'timings', self.timings
        self.progress = (jobs_left, jobs_done, 0, self.failed)
        print 'progress', self.progress
        self.logger.info("time: {} sec".format(time_so_far))
        if jobs_left == 0:
            self.done()


    def __init__(self):
        #QC.QObject.__init__(self, parent)
        self.waiting_workers = []
        self.running_workers = []
        self.finished_workers = []
        self.failed_workers = []
        self.workers = {}
        self.start_time = None
        self.end_time = None
        self.finished = False
        self.runner = None

        self.slots = cpu_count() - 1
        self.logger = logger.get_logger(__name__)
        try:
            self.client = parallel.Client()
        except IOError:
            self.logger.warn("No cluster running. Trying to start")
            self.runner = ShellRunner("ipcluster start -n {}".format(self.slots))
            self.runner.start()
        self.view = self.client.load_balanced_view()
        self.logger.info("start Threader")
        #self.view = self.client.direct_view()
        #self.view.execute("import lsjuicer.data.analysis.transient_find as tf")
        self.view_result = None
        self.actual_slots = len(self.client.ids)
        self.results = {}
        self.errors = {}
        self.chunk = 1
        self.new_finished = False


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
        self.done()

    def done(self):
        if not self.finished:
            self.finished = True
            self.end_time = time.time()
            av_time = (self.end_time - self.start_time)/float(self.jobs_to_run)
            self.logger.info("time per job={}".format(av_time))
            self.logger.info("time per job (actual)={}".format(av_time*self.actual_slots))
            self.client.close()



