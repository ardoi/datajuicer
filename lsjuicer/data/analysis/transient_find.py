from scipy import ndimage as nd
import scipy.stats as ss
import numpy as n

import lsjuicer.data.analysis.fitfun as fitfun
from lsjuicer.data.analysis import regionfinder as rf
from lsjuicer.util.helpers import timeIt
from lsjuicer.util import logger


class Region(object):
    minimum_size = 20
    # maximum distance the left and right sides can be from the maximum
    max_dist_from_max = 250

    @property
    def size(self):
        return self.right - self.left

    @property
    def left(self):
        return max(self._left, self.maximum - self.max_dist_from_max)

    @property
    def right(self):
        return min(self._right, self.maximum + self.max_dist_from_max)

    @property
    def time_data(self):
        return self._all_time_data[self.left:self.right]

    @property
    def data(self):
        return self._all_data[self.left:self.right]

    @property
    def smooth_data(self):
        return self.all_smooth_data[self.left:self.right]

    @property
    def fdhm(self):
        param = self.fit_res[-1].solutions
        m2 = param['m2']
        d = param['d']
        tau2 = param['tau2']
        d2 = param['d2']
        left_half = m2-d*(1+0.5*n.log((1+n.exp(-2))/2.))
        right_half = m2+d2+tau2*n.log(2)
        fdhm = right_half - left_half
        return fdhm

    def extra_range(self):
        """Give an extended range of the region based on FDHM from the last fit"""
        amount = 0.25
        extra = int(self.fdhm*amount)
        # print 'fdhm is:',fdhm
        return (max(0, self.left - extra), min(self.right + extra, self._all_data.size))

    def __init__(self, left, right, maximum, data, smooth_data, time_data):

        self._left = left
        self._right = right
        self.maximum = maximum
        self.bad = False
        self.aic_line = 0
        self.aic_curve = 0
        self.fit_res = []
        # print '\n'+"#"*10,"new region",self
        self._all_time_data = time_data
        self._all_data = data
        self.all_smooth_data = smooth_data
        self.check()

    def fit_curve(self):
        fu = self.all_smooth_data
        ri = self.right
        le = self.left
        self.maximum = self.time_data[self.smooth_data.argmax()]
        oo = fitfun.Optimizer(self.time_data, self.data)
        # make first fit with non-convolved function
        f0r = fu[ri-5:min(len(fu), ri+5)].mean()
        f0l = fu[max(0, le-5):le+5].mean()
        oo.set_function(fitfun.ff50)
        #b_init = (f0r+f0l)/2.
        b_init = f0r
        oo.set_parameter_range('B', b_init*0.75, b_init*1.5, b_init)
        min_amp = 50.0
        if fu[self.maximum]-b_init < min_amp:
            # print f0r,f0l,b_init, fu[self.maximum]
            # print ri,le
            # print fu[self.maximum]-b_init
            # self.bad=True
            return None
        oo.set_parameter_range('tau2', 2, 100., 30.)
        mu_est = self.maximum
        #mu_est = self.time_data[self.data.argmax()]
        oo.set_parameter_range('m2', le+1, ri-1, mu_est)
        d_est = (self.maximum-le)/2.+1.
        d_est = 5.0
        try:
            oo.set_parameter_range(
                'd', 1, mu_est - le, min(0.95*(mu_est-le), d_est))
        except AssertionError:
            return None
        oo.set_parameter_range(
            'A', min_amp, 1.5*(self.data.max()-b_init), fu[self.maximum]-b_init)
        # FIXME why 101?
        data_mean = self.data.mean()
        greater_than_mean = self.data[self.data > data_mean]
        cutoff = 99.0
        multiplier = 0.95
        cutoff_value = ss.scoreatpercentile(greater_than_mean, cutoff) * multiplier
        plateau_length = float(self.data[self.data > cutoff_value].size)
        #oo.set_parameter_range('d2', .1, plateau_length, plateau_length/2)
        oo.set_parameter_range('d2', .1, plateau_length, 2.)
        c_init = f0l - b_init
        c_init_delta = max(abs(c_init*0.5), 25)
        oo.set_parameter_range('C', c_init-c_init_delta, c_init +
                               c_init_delta, c_init)
        oo.show_parameters()
        oo.optimize(max_fev=10000)
        # optimization failed
        if not oo.solutions:
            # print  self.data.tolist()
            # print self.time_data.tolist()
            # for p in oo.parameters:
            # print p,
            # oo.parameters[p]['min'],oo.parameters[p]['max'],oo.parameters[p]['init']
            return None
        # skip transients which start before the recording
        if oo.solutions['m2'] - oo.solutions['d'] < 0:
            return None
        return oo

    def check(self):
        """Checks the validity of the region, first by looking for simple criteria and then by fitting the region with a transient function and line. If the line has a lower AICc score than the transient function then the region is considered not to contain an event"""
        try:
            assert (self.left < self.right) and (self.left < self.maximum) \
                and (self.right > self.maximum), "Assert failed: %s" % self
            assert self.size > self.minimum_size, "Assert failed: Size is %i, \
                minimum size is %i" % (self.size, self.minimum_size)
        except AssertionError:
            self.bad = True
            return
        log = logger.get_logger(__name__)
        log.debug("\nregion:%s" % self)
        try:
            oo = self.fit_curve()
            if not oo:
                raise ValueError
        except:
            self.bad = True
            return
        aicc_curve = oo.aicc()
        log.debug("AICc curve1 %f" % aicc_curve)

       # new_right = oo.solutions['tau2']*(9.0 + n.log(1-n.exp(-2.)))+oo.solutions['m2']
       # if new_right < self.right:
       #     self._right = new_right
       #     self.maximum = oo.solutions['m2']
       #     oo=self.fit_curve()
       #     if not oo:
       #         self.bad = True
       #         return
       #     aicc_curve = oo.aicc()
       #     logger.debug("AICc curve %f"%aicc_curve)

        # fit the line
        oo2 = fitfun.Optimizer(self.time_data, self.data)
        oo2.set_function(fitfun.linear)
        oo2.set_parameter_range('a', -500, 500, 0)
        oo2.set_parameter_range('b', -1e5, 1e5, self.data.mean())
        oo2.optimize(max_fev=1000)
        aicc_line = oo2.aicc()
        # print "AICc line",aicc_line
        log.debug("AICc line %f" % aicc_line)
        self.aic_line = aicc_line
        self.aic_curve = aicc_curve
        if aicc_curve < 1.00 * aicc_line:
        # if aicc_line/aicc_curve < 0.99:
            self.bad = False
            self.fit_res = [oo]

        else:
            self.bad = True
            # print 'aaa'
        # print 'test',self, aicc_line, aicc_curve
        #params = {}
        # for key,val in oo.parameters.iteritems():
        #    params[key] = val['init']
        # print 'param=',params
        # print 'sols=',oo.solutions
        # print self.data.tolist()
        # print self.time_data.tolist()
        log.debug("bad: %s" % str(self.bad))

    def __repr__(self):
        return "<left:%i right:%i max:%i size:%i bad:%s AL:%.1f AC:%.1f>" %\
            (self.left, self.right, self.maximum, self.size, str(self.bad),
             self.aic_line, self.aic_curve)


def make_region_objects(data, regions, smooth_data):
    #smooth_data = data
    time_data = n.arange(data.size)
    region_objects = []
    regions.sort(key=lambda x: x[0])
    for reg in regions:
        left = reg[2]
        right = reg[3]
        maxval = reg[0]
        reg = Region(left, right, maxval, data, smooth_data, time_data)
        region_objects.append(reg)


    return region_objects


def fit_regs(f, all_ranges, plot=False, second_fit = True):
    #
    # Make initial regions (each region tests its own goodness)
    #
    time = n.arange(len(f))
    f_cleaned = f.copy()
    range_keys = all_ranges.keys()
    range_keys.sort(reverse=True)
    all_good_regions = []
    event_fits = {}
    i = 0
    for key in range_keys:
        ranges = all_ranges[key]
        i += 1
        smooth_data = nd.uniform_filter(f_cleaned, 5)
        regs = make_region_objects(f, ranges, smooth_data)
        print '\n regions'
        print regs
        good_regions = []
        if plot:
            import pylab as p
            p.figure(1)
            p.plot(f, marker='o', ls='None', ms=4, mec='None', alpha=.5)
            p.xlim(0, len(f))
            ax = p.gca()
        for r in regs:
            if not r.bad:
                oo = r.fit_res[-1]
                if not oo.solutions:
                    r.bad = True
                else:
                    good_regions.append(r)
                if plot:
                    fcolor = 'orange'
                    if r.bad:
                        fcolor = 'salmon'
                    transient_t = time[r.left:r.right]
                    fmin = f.min()
                    fmax = f.max()
                    ax.add_patch(p.Rectangle((r.left, fmin), r.size, fmax - fmin,
                                              facecolor=fcolor, alpha=0.1))
                    if oo.solutions:
                        p.plot(transient_t, oo.function(transient_t, **oo.solutions),
                            lw=2, color='red')
        z = n.zeros_like(f)
        all_good_regions.extend(good_regions)
        for r in good_regions:
            sol = r.fit_res[-1].solutions
            fit_vals = fitfun.ff50(time, **sol)
            event_fit = fit_vals - fitfun.ff5_bl(arg=time, **sol)
            event_fits[id(r)] = event_fit
            z += event_fit

        f_cleaned -= z
        #n.savetxt('f_cleaned_{}.dat'.format(i), f_cleaned)
    f2 = f_cleaned
    baseline_fit_params = n.polyfit(time, f2, 4)
    pf_fun = n.poly1d(baseline_fit_params)
    baseline = pf_fun(time)

    fullres = n.zeros_like(baseline)
    events = f - f2
    if plot:
        p.figure(2)
        p.plot(time, f2, color='orange', label='signal - fits')
        p.plot(time, f, label='signal')
        p.plot(time, events, label='event fit')
        p.plot(time, baseline, label='bl')
        p.legend()
    # create data for each transient with the other transients removed
    final = {'transients': {}, 'baseline':
             baseline_fit_params, 'peak_fits': {}, 'regions': {},
             'xrange':(min(time),max(time))}
    if not all_good_regions:
        return final
    if plot:
        p.figure(3)
        rows = int(n.ceil(n.sqrt(len(all_good_regions))))
        cols = int(n.ceil(float(len(all_good_regions))/rows))
        assert rows*cols >= len(all_good_regions)

    added_index = 0
    event_fits_new = {}
    for i, r in enumerate(all_good_regions):
        if plot:
            p.figure(3)
            p.subplot(rows, cols, i+1)

        #remove all other regions  and baseline from the signal
        corrected_f  = f - baseline
        for reg in all_good_regions:
            #only remove OTHER regions
            if id(reg) != id(r):
                corrected_f -= event_fits[id(reg)]

        le, ri = r.extra_range()
        fff = corrected_f[le:ri]
        time_new = time[le:ri]
        if plot:
            p.plot(time_new, fff, '-o', ms=4, mec='None', alpha=.5)
        oo = fitfun.Optimizer(time_new, fff)
        oo.set_function(fitfun.ff60)
        # copy fit parameter ranges from previous fit
        oo.parameters = r.fit_res[-1].parameters.copy()
        previous_sol = r.fit_res[-1].solutions
        oo.rerange_parameters(previous_sol)
        # remove B and C since we have already corrected the baseline
        del(oo.parameters['C'])
        del(oo.parameters['B'])
        oo.optimize()
        if not oo.solutions:
            r.bad = True
            continue
        peak = oo.solutions['A']*(1-n.exp(-2.0))
        peak_loc = oo.solutions['m2'] + oo.solutions['d']
        baseline_at_peak = pf_fun(peak_loc)
        # dF/F0 = (F-F0)/F0 = F/F0 -1
        # here F = S + BL and F0=BL, so F/F0 - 1 = (S + BL)/BL - 1 = S/BL =
        # dF/F0
        f_over_f0_max = peak / baseline_at_peak
        min_f_over_f0_max = 0.1
        if f_over_f0_max < min_f_over_f0_max:
            r.bad = True
            continue
        if not second_fit:
            final['transients'][added_index] = oo.solutions
            final['peak_fits'][added_index] = r.fit_res[-1]
            final['regions'][added_index] = r
            added_index += 1
        r.fit_res.append(oo)
        event_fit = oo.function(time, **oo.solutions)
        event_fits_new[id(r)] = event_fit
        #if plot:
        #    fullres += oo.function(time, **oo.solutions)
        if plot:
            #p.plot(time_new, event_fit,lw=2,color='brown')
            p.plot(time_new, oo.function(time_new, **oo.solutions), lw=2, color='brown')
            p.xlim(time_new[0], time_new[-1])
            if not second_fit:
                fullres += oo.function(time, **oo.solutions)

    print 'all regs'
    old_good_regions = all_good_regions
    all_good_regions = []
    for r in old_good_regions:
        if r.bad is not True:
            all_good_regions.append(r)

    if not all_good_regions:
        return final

    if second_fit:
        added_index = 0
        #estimate baseline again
        baseline_f = f.copy()
        for ef in event_fits_new.values():
            baseline_f -= ef
        baseline_fit_params = n.polyfit(time, baseline_f, 4)
        pf_fun = n.poly1d(baseline_fit_params)
        baseline = pf_fun(time)
        final['baseline'] = baseline_fit_params
        for i, r in enumerate(all_good_regions):
            if plot:
                p.figure(3)
                p.subplot(rows, cols, i+1)

            #remove all other regions  and baseline from the signal
            corrected_f = f - baseline
            print 'correct'
            for reg in all_good_regions:
                #only remove OTHER regions
                print id(reg),reg.bad, id(r),r.bad
                if id(reg) != id(r):
                    corrected_f -= event_fits_new[id(reg)]
            le, ri = r.extra_range()
            fff = corrected_f[le:ri]
            time_new = time[le:ri]
            if plot:
                p.plot(time_new, fff, '-o', ms=4, mec='None', alpha=.5)
            oo = fitfun.Optimizer(time_new, fff)
            oo.set_function(fitfun.ff60)
            # copy fit parameter ranges from previous fit
            oo.parameters = r.fit_res[-1].parameters.copy()
            previous_sol = r.fit_res[-1].solutions
            oo.rerange_parameters(previous_sol)
            oo.optimize()
            if not oo.solutions:
                r.bad = True
                continue
            final['transients'][added_index] = oo.solutions
            final['peak_fits'][added_index] = r.fit_res[-1]
            final['regions'][added_index] = r
            added_index += 1
            r.fit_res.append(oo)
            if plot:
                p.plot(time_new, oo.function(time_new, **oo.solutions), lw=2, color='red')
                p.xlim(time_new[0], time_new[-1])
                fullres += oo.function(time, **oo.solutions)
    ## last stage
    # estimate baseline again
    baseline_old = baseline
    do_last_fit = True
    if do_last_fit:
        baseline_f = f.copy()
        for i, r in enumerate(all_good_regions):
            sol = r.fit_res[-1].solutions
            res = oo.function(time, **sol)
            baseline_f -= res
        baseline_fit_params = n.polyfit(time, baseline_f, 4)
        if n.isnan(baseline_fit_params).any():
            baseline_fit_params = n.zeros_like(baseline_fit_params)
        #pf_fun = n.poly1d(baseline_fit_params)
        final['baseline'] = baseline_fit_params
    if plot:
        pf_fun = n.poly1d(baseline_fit_params)
        baseline = pf_fun(time)
        fullres += baseline
        p.figure(5)
        p.plot(time, f, 'o', ms=4, mec='None', alpha=.5)
        p.plot(time, fullres, color='red', lw=2)
        p.plot(time, baseline, color='magenta')
        p.plot(time, baseline_old, color='cyan')
    return final


def remove_fits(vec, fitdict):
    tt = n.arange(vec.size)
    s2 = vec.copy()
    for ev in fitdict['transients'].values():
        fit = fitfun.ff60(tt, **ev)
        s2 -= fit
    return s2


def fit_2_stage(data, plot=False, min_snr=5.0, two_stage=True):
    """Perform a 2 stage fitting routine. In the first stage all found events
    are fitted. For the second stage the baseline obtained in first stage is
    subtracted from the data and fit is performed again

    Returns the result from the second fit call with the exception of the
    baseline which is taken from the first fit"""

    found_regions = rf.get_regions(data, min_snr=min_snr, max_width=200)
    res_out = fit_regs(data, found_regions, plot, two_stage)
    return res_out


def make_data_by_size_and_time(results, key, number):
    """get data for the 'number'th transient sorted by size and then by time"""
    out = n.zeros((results['height'], results['width']), dtype='float')
    for res in results['fits']:
        x = res[0]
        y = res[1]
        try:
            transients = results['fits'][res]['transients'].values()
            transients.sort(key=lambda x: x['A'], reverse=True)
            two_biggest = transients[:2]
            two_biggest.sort(key=lambda x: x['m2'])
            transient = two_biggest[number]
            val = transient[key]
            out[y, x] = val
        except:
            out[y, x] = None
            pass
    return out


@timeIt
def make_data_by_size(results, key, number):
    """get data for the 'number'th biggest transient"""
    out = n.zeros((results['height'], results['width']), dtype='float')
    print '\n make data'
    for res in results['fits']:
        x = res.x
        y = res.y
        try:
            transients = res.pixel_events
            transients.sort(key=lambda x: x.parameters['A'], reverse=True)
            transient = transients[number]
            val = transient.parameters[key]
            out[y, x] = val
        except:
            # traceback.print_exc()
            out[y, x] = None
            pass
    return out


def make_data(results, key, transient_no):
    """get data for the 'transient_no'-th transient"""
    out = n.zeros((results['height'], results['width']), dtype='float')
    for res in results['fits']:
        x = res[0]
        y = res[1]
        try:
            transient = results['fits'][res]['transients'][transient_no]
            val = transient[key]
            out[y, x] = val
        except:
            out[y, x] = None
    return out


def get_res(fit_result):
    import inout.sqla as sa
    results = {}
    session = sa.dbmaster.get_session()
    # session.add(self.fit_result)
    fitted_pixels = fit_result.pixels
    # self.fit_result.region.height
    results['width'] = fit_result.region.width - \
        2*fit_result.fit_settings['padding']
    results['height'] = fit_result.region.height - \
        2*fit_result.fit_settings['padding']
    # FIXME
    #results['frames'] = self.fit_result.region.analysis.imagefile.image_frames
    #results['frames'] = self.acquisitions
    results['dx'] = fit_result.fit_settings['padding']
    results['dy'] = fit_result.fit_settings['padding']
    results['x0'] = fit_result.region.x0
    results['y0'] = fit_result.region.y0
    results['fits'] = fitted_pixels
    session.close()
    return results


def data_events(results):
    out = n.zeros((results['height'], results['width']), dtype='float')
    for res in results['fits']:
        x = res.x
        y = res.y
        val = res.event_count
        if val is not None:
            out[y, x] = val
        else:
            out[y, x] = 0  # None
    return out


def make_raw(res):
    import sqlb2
    sess = sqlb2.dbmaster.get_session()
    jobs = sess.query(sqlb2.Job).all()
    shape = (res['frames'], res['height'], res['width'])
    out = n.zeros(shape)
    for j in jobs:
        x, y = j.params['coords']
        out[:, y, x] = j.params['data']
    sess.close()
    return out


class SyntheticData(object):

    def __init__(self, result=None):
        if result:
            self.result = result
            self.region = result.region
            self.times = n.arange(int(self.region.frames))
            print 'times shape is', self.times.shape, self.region.frames
            if self.region.width == 1:
                self.linescan = True
            else:
                self.linescan = False
        self.func = None
        self.filter = None

    def _zeros(self):
        if self.linescan:
            out = n.zeros(
                (1, self.region.height, int(self.region.frames)), dtype='float')
            print 'out shape is', out.shape, self.region.frames
        else:
            out = n.zeros(
                (self.region.frames, self.region.height, self.region.width), dtype='float')
        return out

    def _make_res(self):
        out = self._zeros()
        for res in self.result.pixels:
            x = res.x
            y = res.y
            if not self.linescan:
                out[:, y, x] = self.func(res)
            else:
                out[0, y, :] = self.func(res)
        self.filter = None
        self.func = None
        return out

    def func_fit(self, result):
        f = n.zeros_like(self.times, dtype='float')
        for i, t in enumerate(result.pixel_events):
            if self.filter:
                # skip pixelevents that are not part of any event
                # if not t.event_id in self.filter:
                if not t.id in self.filter:
                    continue
            res = fitfun.ff60(self.times, **t.parameters)
            if True not in n.isnan(res):
                f += res
            else:
                print "NAN for", t
        return f

    def func_baseline(self, result):
        if result.baseline is None:
            return n.array([n.nan]*self.times.size)
        pf = n.poly1d(result.baseline)
        baseline = pf(self.times)
        return baseline

    def func_all(self, result):
        return self.func_fit(result) + self.func_baseline(result)

    def get_fit(self):
        self.func = self.func_fit
        return self._make_res()

    def get_events(self, filter):
        self.func = self.func_fit
        self.filter = filter
        return self._make_res()

    def get_baseline(self):
        self.func = self.func_baseline
        return self._make_res()

    def get_all(self):
        self.func = self.func_all
        return self._make_res()


def get_job(joblist, coords):
    for j in joblist:
        if coords == j.params['coords']:
            return j
    return None


def redo(jobs, res):
    bad_jobs = []
    for i, j in enumerate(jobs):
        j_res = j.result
        transients = j_res['transients']
        bad = False
        if len(transients) == 0:
            bad = True
        for t in transients.values():
            if t['d'] == 100:
                bad = True
                break
        if bad:
            bad_jobs.append(j)
    print "%i jobs to redo" % (len(bad_jobs))
    for i, bj in enumerate(bad_jobs):
       # print i
        result = fit_regs(bj.params[0])
        bj.result = result

    fit_dict = {}
    for job in jobs:
        jres = job.result
        params = job.params
        xy = params[2]
        if jres:
            fit_dict[(xy[0], xy[1])] = jres
        else:
            fit_dict[(xy[0], xy[1])] = None
    ff = open("fit_results.pickle", 'w')
    res["fits"] = fit_dict
    import pickle
    pickle.dump(res, ff)
    ff.close()

def reconstruct_signal(result, event_array=False):
    """Take result dictionary given by fit_2_stage and return
    baseline and event fits
    If event_array == True then send array with each event instead
    of summed up events
    """
    xvals = n.arange(result['xrange'][0], result['xrange'][1], 1.0)
    if event_array:
        events = n.zeros(shape=(xvals.size, len(result['regions'])))
    else:
        events = n.zeros_like(xvals)
    for key, region in result['regions'].iteritems():
        opt = region.fit_res[-1]
        signal = opt.function(xvals, **opt.solutions)
        if event_array:
            events[:,key] = signal
        else:
            events += signal
    baseline = n.poly1d(result['baseline'])(xvals)
    return xvals, events, baseline

class FF0(object):
    def __init__(self, result):
        self.result = result
        self.baseline_f = n.poly1d(result['baseline'])

    def __call__(self, arg):
        bl = self.baseline_f(arg)
        f = 0.0
        for key, region in self.result['regions'].iteritems():
            opt = region.fit_res[-1]
            try:
                event_f = opt.function(arg, **opt.solutions)
                f += event_f
            except:
                print 'failed for', arg, opt.solutions
                continue
        return f/bl





def fitted_pixel_ff0(pixel, event=0):
    # possible bug if baseline is higher than A
    region = pixel.result.region
    #times = n.arange(region.start_frame, region.end_frame,1.0)
    # FIXME probably has to be changed to actual time
    times = n.arange(0, region.end_frame-region.start_frame, 1.0)
    param = pixel.pixel_events[event].parameters
    f_vals = fitfun.ff60(times, **param)
    baseline_f = n.poly1d(pixel.baseline)
    baseline = baseline_f(times)
    return f_vals/baseline + 1


def fitted_pixel_max(pixel, event=0):
    param = pixel.pixel_events[event].parameters
    maxval = param['A']*(1-n.exp(-2.0))
    baseline_f = n.poly1d(pixel.baseline)
    baseline = baseline_f(param['m2'])
    #vals = fitted_pixel_ff0(pixel, event)
    # if n.isnan(maxval):
        # print 'max is nan'
        # print param
    # elif n.isnan(baseline):
        # print 'base is nan'
        # print param
        # print pixel.baseline, pixel.id
    # elif n.isinf(baseline):
        # print 'base is inf'
        # print param
    f_max = maxval/baseline + 1  # F/F0 not dF/F0
    return f_max


def do_event_list(pixs):
    events = []
    for p in pixs:
        for i, pixel_event in enumerate(p.pixel_events):
            event = {}
            event['pixel'] = p
            event['n'] = i
            event['x'] = p.x
            event['y'] = p.y
            event['id'] = pixel_event.id
            ep = pixel_event.parameters
            for param in ep:
                if param == 'A':
                    # use dF/F0 instead of raw A value
                    # -1 because fitted_pixel_max returns F/F0
                    event[param] = fitted_pixel_max(p, i) - 1
                else:
                    event[param] = ep[param]
            events.append(event)
            # break
    return events


def do_event_array(elist, names):
    out = n.zeros((len(elist), len(names)))
    for i, e in enumerate(elist):
        for j, name in enumerate(names):
            out[i, j] = e[name]
    return out
