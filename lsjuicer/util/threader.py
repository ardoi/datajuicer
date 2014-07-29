from multiprocessing import cpu_count
import time
import random
import traceback

import numpy as np
import pexpect

import lsjuicer.util.logger as logger

from IPython import parallel

def single(args):
    data = args['data']
    import lsjuicer.data.analysis.transient_find as tf
    try:
        f = tf.fit_2_stage(data, min_snr=4.00)
        error = None
    except:
        import traceback
        error=traceback.format_exc()
        f = None
    return args['coords'], f, error


class Threader(object):

    def update(self):
        if self.start_time is None:
            self.start_time = time.time()
            #self.run_times []

        self.logger.info("Threader update")
        if not self.view_result:
            self.logger.info("Start {} jobs".format(self.jobs_to_run))
            random.shuffle(self.params)
            self.view_result = self.view.map_async(single, self.params, ordered=False,
                                                   chunksize=self.chunk)
            self.waiting = set(self.view_result.msg_ids)
            self.failed = 0
        try:
            self.client.wait(self.waiting, 1e-3)
        except parallel.TimeoutError:
            pass
        just_finished = self.waiting.difference(self.client.outstanding)
        self.waiting = self.waiting.difference(just_finished)
        finished_now = 0
        for job_id in just_finished:
            result = self.client.get_result(job_id)
            self.logger.info("job {} finished on engine {}".
                             format(job_id, result.engine_id))
            for res in result.result:
                finished_now += 1
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

        self.jobs_done += finished_now
        jobs_left = self.jobs_to_run - self.jobs_done
        self.logger.info('ff: {} {} {}'.format(finished_now, self.jobs_done, jobs_left ))
        self.logger.info('waiting: {}'.format(jobs_left))
        self.logger.info('just finished: {}'.format(finished_now))
        self.logger.info('failed: {}'.format(self.failed))
        self.new_finished = bool(len(just_finished))
        time_so_far = int(time.time() - self.start_time)
        #jobs_left = len(self.waiting)*self.chunk
        #jobs_done = self.jobs_to_run - jobs_left
        #self.logger.info("qq: {} {}".format(jobs_left, jobs_done))
        if self.jobs_done:
            time_per_job = time_so_far / float(self.jobs_done)
        else:
            time_per_job = 0
        time_left = int(time_per_job * jobs_left)
        self.timings = (time_per_job, time_left, time_so_far)
        print 'timings', self.timings
        self.progress = (jobs_left, self.jobs_done, 0, self.failed)
        print 'progress', self.progress
        self.logger.info("time: {} sec".format(time_so_far))
        if jobs_left == 0:
            self.done()


    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.finished = False
        self.runner = None

        self.slots = cpu_count() - 1
        self.logger = logger.get_logger(__name__)
        try:
            self.client = parallel.Client()
        except (IOError, parallel.error.TimeoutError):
            self.logger.warn("No cluster running. Trying to start")
            timeout = 10 #how long to wait for cluster to become available. IPython default is 30
            self.runner = pexpect.spawn("ipcluster start -n {} --IPClusterEngines.early_shutdown={}".format(self.slots, timeout))
            try:
                cluster_start_time = time.time()
                q = self.runner.expect(["Engines appear to have started successfully", "Cluster is already running"], timeout = timeout*2)
                if q==0:
                    self.logger.info("Cluster started with -n {} in {} seconds".format(self.slots, time.time() - cluster_start_time))
                    self.client = parallel.Client()
                else:
                    raise RuntimeError()
            except (pexpect.TIMEOUT, RuntimeError) as e:
                self.logger.error("Cannot start cluster")
                self.logger.error(traceback.format_exc(e))
                raise RuntimeError("No cluster")

        self.view = self.client.load_balanced_view()
        self.logger.info("start Threader")
        self.view_result = None
        self.actual_slots = len(self.client.ids)
        self.results = {}
        self.errors = {}
        self.chunk = 10
        self.new_finished = False
        self.jobs_done = 0


    def do(self, params, settings):
        self.jobs_to_run = len(params)
        self.settings = settings
        self.params = params
        self.jobs_done = 0
        selection = settings['selection']
        self.state_array = np.zeros(
            shape=(selection.height - 2 * settings['dy'],
                   selection.width - 2 * settings['dx']))

    def run(self):
        self.update()
        while len(self.waiting) > 0:
            time.sleep(5)
            self.update()
        self.done()

    def done(self):
        if not self.finished:
            self.finished = True
            self.client.close()
            if self.start_time:
                self.end_time = time.time()
                av_time = (self.end_time - self.start_time)/float(self.jobs_to_run)
                self.logger.info("time per job={}".format(av_time))
                self.logger.info("time per job (actual)={}".format(av_time*self.slots))
            if self.runner:
                #self.client.shutdown(hub=True)
                self.runner.terminate()
                self.runner = None



