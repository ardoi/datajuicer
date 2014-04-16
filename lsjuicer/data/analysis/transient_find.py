import traceback
import logging

from scipy import ndimage as nd
import numpy as n

import lsjuicer.data.analysis.fitfun as fitfun
from lsjuicer.data.analysis import regionfinder as rf
from lsjuicer.util.helpers import timeIt

def get_logger(name):
    logger = logging.getLogger(__name__)
    if not logger.root.handlers and not logger.handlers:
    #if not logger.handlers:
        #hh = logging.StreamHandler(sys.stdout)
        hh = logging.FileHandler("log.log")
        log_format = "%(levelname)s:%(name)s:%(funcName)s:%(lineno)d:%(asctime)s %(message)s"
        hh.setFormatter(logging.Formatter(log_format))
        logger.addHandler(hh)
        logger.setLevel(logging.DEBUG)
    return logger

class Region(object):
    minimum_size = 20
    #maximum distance the left and right sides can be from the maximum
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
        #print 'fdhm is:',fdhm
        return (self.left - extra, self.right+extra)

    def __init__(self, left, right, maximum, data, smooth_data, time_data):

        self._left = left
        self._right = right
        self.maximum = maximum
        self.bad = False
        self.aic_line = 0
        self.aic_curve = 0
        self.fit_res=[]
        #print '\n'+"#"*10,"new region",self
        self._all_time_data = time_data
        self._all_data = data
        self.all_smooth_data = smooth_data
        self.check()
        #print self.bad

    def fit_curve(self):
        #print '\n'
        fu = self.all_smooth_data
        ri = self.right
        le = self.left
        self.maximum = self.time_data[self.data.argmax()]
        #print le,ri,self.maximum
        oo = fitfun.Optimizer(self.time_data, self.data)
        #make first fit with non-convolved function
        f0r = fu[ri-5:min(len(fu), ri+5)].mean()
        f0l = fu[max(0,le-5):le+5].mean()
        oo.set_function(fitfun.ff50)
        b_init = (f0r+f0l)/2.
        oo.set_parameter_range('B',b_init*0.75,b_init*1.25,b_init)
        min_amp = 50.0
        if fu[self.maximum]-b_init < min_amp:
            print 'A'
            #print f0r,f0l,b_init, fu[self.maximum]
            #print ri,le
            #print fu[self.maximum]-b_init
            #self.bad=True
            return None
        oo.set_parameter_range('tau2',2,100.,30.)
        mu_est = self.maximum
        #mu_est = self.time_data[self.data.argmax()]
        oo.set_parameter_range('m2', le+1, ri-1, mu_est)
        d_est = (self.maximum-le)/2.+1.
        left_data = fu[le:self.maximum]
        d_est = 5.0
        try:
            oo.set_parameter_range('d',1, mu_est - le,min(0.95*(mu_est-le), d_est))
        except AssertionError:
            print 'B'
            return None
        oo.set_parameter_range('A',min_amp, 1.5*(self.data.max()-b_init), fu[self.maximum]-b_init)
        #FIXME why 51?
        oo.set_parameter_range('d2',.1,51,2)
        c_init = f0l - b_init
        c_init_delta = max(abs(c_init*0.5), 25)
        oo.set_parameter_range('C',c_init-c_init_delta, c_init +
                c_init_delta, c_init)
        #oo.show_parameters()
        oo.optimize(max_fev = 10000)
        #optimization failed
        print oo.parameters
        print fu[self.maximum], b_init, self.maximum
        if not oo.solutions:
            print 'C'
            #print  self.data.tolist()
            #print self.time_data.tolist()
            #for p in oo.parameters:
            #    print p, oo.parameters[p]['min'],oo.parameters[p]['max'],oo.parameters[p]['init']
            return None
        #skip transients which start before the recording
        if oo.solutions['m2'] - oo.solutions['d'] < 0:
            print 'D'
            return None
        return oo

    def check(self):
        """Checks the validity of the region, first by looking for simple criteria and then by fitting the region with a transient function and line. If the line has a lower AICc score than the transient function then the region is considered not to contain an event"""
        try:
            assert (self.left < self.right) and (self.left < self.maximum) \
                    and (self.right > self.maximum), "Assert failed: %s"%self
            assert self.size > self.minimum_size, "Assert failed: Size is %i, \
                minimum size is %i"%(self.size, self.minimum_size)
        except AssertionError:
            #print 'a0'
            self.bad=True
            return
        logger = get_logger(__name__)
        logger.debug("\nregion:%s"%self)
        try:
            oo = self.fit_curve()
            if not oo:
                raise ValueError
        except:
            self.bad = True
            return
        aicc_curve = oo.aicc()
        logger.debug("AICc curve1 %f"%aicc_curve)

       # new_right = oo.solutions['tau2']*(9.0 + n.log(1-n.exp(-2.)))+oo.solutions['m2']
       # if new_right < self.right:
       #     self._right = new_right
       #     self.maximum = oo.solutions['m2']
       #     oo=self.fit_curve()
       #     if not oo:
       #         self.bad = True
       #         #print 'aa'
       #         return
       #     aicc_curve = oo.aicc()
       #     logger.debug("AICc curve %f"%aicc_curve)

        #fit the line
        oo2 = fitfun.Optimizer(self.time_data, self.data)
        oo2.set_function(fitfun.linear)
        oo2.set_parameter_range('a',-500, 500, 0)
        oo2.set_parameter_range('b',-1e5, 1e5, self.data.mean())
        oo2.optimize(max_fev = 1000)
        aicc_line = oo2.aicc()
        #print "AICc line",aicc_line
        logger.debug("AICc line %f"%aicc_line)
        self.aic_line = aicc_line
        self.aic_curve = aicc_curve
        if aicc_curve < 1.00 * aicc_line:
        #if aicc_line/aicc_curve < 0.99:
            self.bad = False
            self.fit_res = [oo]

        else:
            self.bad = True
            #print 'aaa'
        logger.debug("bad: %s"%str(self.bad))

    def __repr__(self):
        return "<left:%i right:%i max:%i size:%i bad:%s AL:%.1f AC:%.1f>"%(self.left, self.right,
                self.maximum, self.size, str(self.bad), self.aic_line, self.aic_curve)


def make_region_objects(data, regions, smooth_data):
    #smooth_data = data
    time_data = n.arange(data.size)
    region_objects = []
    for reg in regions:
        left = reg[2]
        right = reg[3]
        maxval = reg[0]
        reg = Region(left, right, maxval, data, smooth_data, time_data)
        region_objects.append(reg)
    return region_objects


def fit_regs(f, regions, plot=False):
    #print 'regs are', regs
    time = n.arange(len(f))
    z = n.zeros_like(f)
    bl = n.zeros_like(f)
    smooth_data = nd.uniform_filter(f, 5)
    regs = make_region_objects(f, regions, smooth_data)
    good_regions = []
    if plot:
        import pylab as p
        p.figure(1)
        p.plot(f,marker='o',ls='None',ms=4,mec='None',alpha=.5)
        p.xlim(0, len(f))
        ax=p.gca()
    for i,r in enumerate(regs):
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
                le = r.left
                ri = r.right
                transient_t = time[le:ri]
                fmin=f.min()
                fmax=f.max()
                ax.add_patch(p.Rectangle((le,fmin),r.size,fmax-fmin,facecolor=fcolor,alpha=0.1))
                if oo.solutions:
                    p.plot(transient_t, oo.function(transient_t, **oo.solutions),lw=2,color='red')

    i=0
    #print '\n\n'
    while i<len(good_regions):
        r = good_regions[i]
        #le = r.left
        #ri = r.right
        le,ri = r.extra_range()
        #print '\nranges',le,ri,r.left,r.right
        #transient_t = time[le:ri]
        transient_t = time
        sol = r.fit_res[-1].solutions
        #print r,sol,r.extra_range()
        fit_vals = fitfun.ff50(transient_t, **sol)
        #print 'sol',sol
        z += 1*fit_vals - fitfun.ff5_bl(arg=transient_t, **sol)
        #bl[le:ri] = fitfun.ff5_bl(arg=transient_t, **sol)
        i+=1
    f2 = f-z
    baseline_fit_params = n.polyfit(time, f2, 4)
    pf_fun = n.poly1d(baseline_fit_params)
    baseline = pf_fun(time)
    fullres = n.zeros_like(baseline)
    if plot:
        p.figure(2)
        p.plot(time, f-z,color='orange',label='signal - fits')
        p.plot(time, f, label='signal')
        p.plot(time, z,label='fit - bl')
        p.plot(time, baseline,label='bl')
        p.legend()
    #create data for each transient with the other transients removed
    final = {'transients':{},'baseline':baseline_fit_params, 'peak_fits':{},'regions':{}}
    if not good_regions:
        return final
    if plot:
        p.figure(3)
        rows = int(n.ceil(n.sqrt(len(good_regions))))
        cols = int(n.ceil(float(len(good_regions))/rows))
        assert rows*cols >= len(good_regions)
    #do_last_fit = False
    do_last_fit = True
    added_index = 0
    for i,r in enumerate(good_regions):
        #print '\n',i
        if plot:
            p.figure(3)
            p.subplot(rows, cols, i+1)
        #le = r.left
        #ri = r.right
        le,ri = r.extra_range()
        transient_f = f[le:ri]
        #transient_t = time[le:ri]
        ff = n.zeros_like(f)
        ff[:le] = f2[:le]
        ff[ri:] = f2[ri:]
        ff[le:ri] = transient_f
        #use transient as 50% of data. add 25% of transient duration from left and right sides
        #as extra data for fitting (good for cases where the baseline is cut off by a
        #close-by transient
        #points = len(transient_f)
        #end = min(len(ff), ri + points/2)
        #start = max(0,le-points/2)
        start,end = r.extra_range()
        #nprint 'extra range',(le,ri),(start,end)
        fff = ff[start:end]
        time_new = time[start:end]
        #subtract fit of baseline from fff
        fff = fff-baseline[start:end]
        if plot:
            p.plot(time_new, fff,'-o',ms=4,mec='None',alpha=.5)
        oo = fitfun.Optimizer(time_new, fff)
        oo.set_function(fitfun.ff60)
        #copy fit parameter ranges from previous fit
        oo.parameters = r.fit_res[-1].parameters.copy()
        previous_sol = r.fit_res[-1].solutions
        oo.rerange_parameters(previous_sol)
        #remove B and C since we have already corrected the baseline
        del(oo.parameters['C'])
        del(oo.parameters['B'])
        oo.optimize()
        if not oo.solutions:
            r.bad=True
            continue
        peak = oo.solutions['A']*(1-n.exp(-2.0))
        peak_loc = oo.solutions['m2'] + oo.solutions['d']
        baseline_at_peak = pf_fun(peak_loc)
        #dF/F0 = (F-F0)/F0 = F/F0 -1
        #here F = S + BL and F0=BL, so F/F0 - 1 = (S + BL)/BL - 1 = S/BL = dF/F0
        f_over_f0_max = peak / baseline_at_peak
        min_f_over_f0_max = 0.1
        if f_over_f0_max<min_f_over_f0_max:
            r.bad = True
            continue
        final['transients'][added_index] = oo.solutions
        final['peak_fits'][added_index] = r.fit_res[0]
        final['regions'][added_index]=r
        added_index += 1
        r.fit_res.append(oo)
        if plot:
            p.title("%i"%i)
            p.plot(time_new, oo.function(time_new, **oo.solutions),lw=2,color='brown')
            p.xlim(time_new[0], time_new[-1])
            fullres += oo.function(time, **oo.solutions)

    #last stage
    #estimate baseline again
    very_good_regions = []
    for region in good_regions:
        if region.bad:
            #print 'found bad'
            continue
        else:
            very_good_regions.append(region)
    #print 'very good', very_good_regions
    if do_last_fit:
        baseline_f = f.copy()
        for i,r in enumerate(very_good_regions):
            sol = r.fit_res[-1].solutions
            res = oo.function(time, **sol)
            baseline_f -= res
        baseline_fit_params = n.polyfit(time, baseline_f, 4)
        if n.isnan(baseline_fit_params).any():
            baseline_fit_params = n.zeros_like(baseline_fit_params)
        pf_fun = n.poly1d(baseline_fit_params)
        final['baseline'] = baseline_fit_params
    if plot:
        pf_fun = n.poly1d(baseline_fit_params)
        baseline = pf_fun(time)
        fullres+=baseline
        p.figure(5)
        p.plot(time,f, 'o',ms=4,mec='None',alpha=.5)
        p.plot(time, fullres,color='red',lw=2)

    return final

def remove_fits(vec, fitdict):
    tt=n.arange(vec.size)
    s2 = vec.copy()
    for ev in fitdict['transients'].values():
        fit=fitfun.ff60(tt,**ev)
        s2-=fit
    return s2

def fit_2_stage(data, plot=False, min_snr=5.0):
    """Perform a 2 stage fitting routine. In the first stage all found events are fitted. For the second stage the baseline obtained in first stage is subtracted from the data and fit is performed again

    Returns the result from the second fit call with the exception of the baseline which is taken from the first fit"""
    found_regions = rf.get_regions(data, min_snr=min_snr)
    #use the regions with maximum overlap index
    use_regions = found_regions[max(found_regions.keys())]
    res_1 = fit_regs(data, use_regions, plot)
    do_clean = True
    print 'keys',found_regions.keys()
    if do_clean and len(found_regions.keys())>1:
        print 'do clean'
        cleaned = remove_fits(data, res_1)
        found_regions = rf.get_regions(cleaned, min_snr=min_snr)
        #use the regions with maximum overlap index
        use_regions = found_regions[max(found_regions.keys())]
        print 'using', use_regions
        res_2 = fit_regs(cleaned, use_regions, plot)
        if res_2['transients'] is not {}:
            new_res = {}
            for k,v in res_1['transients'].iteritems():
                new_res[k] = v
            for k,v in res_2['transients'].iteritems():
                new_res[k+len(res_1['transients'])] = v
            res_1['transients'] = new_res
            res_1['baseline'] = res_2['baseline']
    #bl_1_func = n.poly1d(res_1['baseline'])
    #bl_1 = bl_1_func(time)
    #print (max(bl_1)-min(bl_1))/min(bl_1)
    #print 'second',len(time), len(data), len(bl_1),
    #print res_1
    #data_2 = data - bl_1
    #print res_1
    #print "stage 2"
    #res_2 = fit_regs(data_2, plot, baseline = bl_1)
    #res_2['baseline'] = res_1['baseline']
    return res_1


def make_data_by_size_and_time(results, key, number ):
    """get data for the 'number'th transient sorted by size and then by time"""
    out = n.zeros((results['height'], results['width']),dtype='float')
    #print out.shape
    for res in results['fits']:
        x = res[0]
        y = res[1]
        try:
            transients = results['fits'][res]['transients'].values()
            transients.sort(key=lambda x:x['A'], reverse = True)
            two_biggest = transients[:2]
            two_biggest.sort(key = lambda x:x['m2'])
            transient = two_biggest[number]
            val = transient[key]
            out[y,x]=val
        except:
            #traceback.print_exc()
            out[y,x]=None
            pass
    return out

@timeIt
def make_data_by_size(results, key, number ):
    """get data for the 'number'th biggest transient"""
    out = n.zeros((results['height'], results['width']),dtype='float')
    print '\n make data'
    for res in results['fits']:
        x = res.x
        y = res.y
        try:
            transients = res.pixel_events
            transients.sort(key=lambda x:x.parameters['A'], reverse = True)
            transient = transients[number]
            val = transient.parameters[key]
            out[y,x]=val
        except:
            #traceback.print_exc()
            out[y,x] = None
            pass
    return out

def make_data(results, key, transient_no):
    """get data for the 'transient_no'-th transient"""
    out = n.zeros((results['height'], results['width']),dtype='float')
    #print out.shape
    for res in results['fits']:
        x = res[0]
        y = res[1]
        try:
            transient = results['fits'][res]['transients'][transient_no]
            val = transient[key]
            out[y,x]=val
        except:
            out[y,x]=None
    return out


def get_res(fit_result):
    import inout.sqla as sa
    results = {}
    session = sa.dbmaster.get_session()
    #session.add(self.fit_result)
    fitted_pixels = fit_result.pixels
    #print "get res", self.fit_result.region.width, self.fit_result.region.height
    results['width'] = fit_result.region.width - 2*fit_result.fit_settings['padding']
    results['height'] = fit_result.region.height - 2*fit_result.fit_settings['padding']
    #FIXME
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
    out = n.zeros((results['height'], results['width']),dtype='float')
    #print out.shape
    for res in results['fits']:
        x = res.x
        y = res.y
        val = res.event_count
        if val is not None:
            out[y, x]=val
        else:
            out[y, x]=0#None
    return out

def make_raw(res):
    import sqlb2
    sess = sqlb2.dbmaster.get_session()
    jobs = sess.query(sqlb2.Job).all()
    #print len(jobs)
    shape = (res['frames'],res['height'],res['width'])
    out = n.zeros(shape)
    for j in jobs:
        x,y = j.params['coords']
        out[:,y,x] = j.params['data']
    sess.close()
    return out




class SyntheticData(object):
    def __init__(self, result=None):
        if result:
            self.result = result
            self.region = result.region
            self.times = n.arange(int(self.region.frames))
            print 'times shape is',self.times.shape, self.region.frames
            if self.region.width==1:
                self.linescan = True
            else:
                self.linescan = False
        self.func = None
        self.filter = None

    def _zeros(self):
        if self.linescan:
            out = n.zeros((1, self.region.height, int(self.region.frames)),dtype='float')
            print 'out shape is',out.shape,self.region.frames
        else:
            out = n.zeros((self.region.frames, self.region.height, self.region.width),dtype='float')
        return out


    def _make_res(self):
        out = self._zeros()
        for res in self.result.pixels:
            x = res.x
            y = res.y
            if not self.linescan:
                out[:,y,x] = self.func(res)
            else:
                out[0,y,:] = self.func(res)
        self.filter = None
        self.func = None
        return out

    def func_fit(self, result):
        f = n.zeros_like(self.times, dtype='float')
        for i,t in enumerate(result.pixel_events):
            if self.filter:
                #skip pixelevents that are not part of any event
                #if not t.event_id in self.filter:
                if not t.id in self.filter:
                    continue
            res = fitfun.ff60(self.times, **t.parameters)
            if True not in n.isnan(res):
                f+=res
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
    for i,j in enumerate(jobs):
        j_res = j.result
        transients = j_res['transients']
        bad = False
        if len(transients) == 0:
            bad = True
        for t in transients.values():
            if t['d']==100:
                bad = True
                break
        if bad:
            bad_jobs.append(j)
    print "%i jobs to redo"%(len(bad_jobs))
    for i,bj in enumerate(bad_jobs):
       # print i
        result = fit_regs(bj.params[0])
        bj.result = result

    fit_dict={}
    for job in jobs:
        jres = job.result
        params = job.params
        xy = params[2]
        if jres:
            fit_dict[(xy[0], xy[1])] = jres
        else:
            fit_dict[(xy[0], xy[1])] = None
    ff = open("fit_results.pickle",'w')
    res["fits"] = fit_dict
    import pickle
    pickle.dump(res,ff)
    ff.close()

def fitted_pixel_ff0(pixel, event = 0):
    #possible bug if baseline is higher than A
    region = pixel.result.region
    #times = n.arange(region.start_frame, region.end_frame,1.0)
    #FIXME probably has to be changed to actual time
    times = n.arange(0, region.end_frame-region.start_frame,1.0)
    param = pixel.pixel_events[event].parameters
    f_vals = fitfun.ff60(times, **param)
    baseline_f = n.poly1d(pixel.baseline)
    baseline = baseline_f(times)
    return f_vals/baseline + 1

def fitted_pixel_max(pixel, event = 0):
    param = pixel.pixel_events[event].parameters
    maxval = param['A']*(1-n.exp(-2.0))
    baseline_f = n.poly1d(pixel.baseline)
    baseline = baseline_f(param['m2'])
    #vals = fitted_pixel_ff0(pixel, event)
    #if n.isnan(maxval):
        #print 'max is nan'
        #print param
    #elif n.isnan(baseline):
        #print 'base is nan'
        #print param
        #print pixel.baseline, pixel.id
    #elif n.isinf(baseline):
        #print 'base is inf'
        #print param
    f_max = maxval/baseline + 1 #F/F0 not dF/F0
    return f_max

def do_event_list(pixs):
    events=[]
    for p in pixs:
        for i, pixel_event in  enumerate(p.pixel_events):
            event={}
            event['pixel']=p
            event['n']= i
            event['x'] = p.x
            event['y'] = p.y
            event['id']= pixel_event.id
            ep = pixel_event.parameters
            for param in ep:
                if param=='A':
                    #use dF/F0 instead of raw A value
                    # -1 because fitted_pixel_max returns F/F0
                    event[param]=fitted_pixel_max(p, i) - 1
                else:
                    event[param] = ep[param]
            events.append(event)
            #break
    return events

def do_event_array(elist, names):
    out = n.zeros((len(elist),len(names)))
    for i,e in enumerate(elist):
        for j,name in enumerate(names):
            out[i,j] = e[name]
    return out

