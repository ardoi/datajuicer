import traceback
import math
import uuid
import pickle

from scipy.optimize import leastsq
from scipy.interpolate import interp1d
import numpy

#from util.residualcalculator import ResidualCalculator
from lsjuicer.util import helpers
from lsjuicer.data.analysis import fitfun


class SparkSpatialProfile(object):

    def __init__(self, fdata, sdata):
        self.data = numpy.array(fdata)
        self.space = numpy.array(sdata)
        self.start = self.space[0]
        self.end = self.space[-1]
        self.width = self.end - self.start
        self.F_max, self.s_at_F_max = self.get_max()
        self.F_min = min(self.data)
        self.F_spread = self.F_max-self.F_min
        self.fit_function = fitfun.gaussian_1d
        self.do_analysis()
    def get_max(self):
        max_f_val = max(self.data)
        t_at_max_y = self.data.tolist().index(max_f_val)
        return max_f_val,t_at_max_y
    def do_analysis(self):
        oo = fitfun.Optimizer(self.space, self.data)
        oo.set_function(self.fit_function)
        oo.set_parameter_range('A', 0., 5*self.F_max, 1.)
        oo.set_parameter_range('B', 0., self.F_max-0.5*self.F_spread,
                self.F_min + 0.25*self.F_spread)
        oo.set_parameter_range('mu', self.start, self.end,self.space[self.s_at_F_max])
        oo.set_parameter_range('s',0, 500.,1.)
        #print 'start'
        try:
            oo.optimize()
        except RuntimeError:
            f= open('ppps.pickle','w')
            pickle.dump(self.data,f)
            pickle.dump(self.space,f)
            f.close()
            raise RuntimeError
        #oo.optimize()
        self.oo=oo
        #print 'optimize done'
        self.params = oo.solutions
        self.bl = self.params['B']
        #max from fit
        #maxsolver =  fitfun.MaxSolver()
        #maxsolver.set_function(self.fit_function, self.params)
        #maxsolver.set_solve_range(self.start, self.end, self.space[self.s_at_F_max])
        #maxsolver.solve()

        #print 'max-sol done'
        self.fit_max_value = self.params['A']+self.params['B']
        self.fit_max_loc = self.params['mu']
        #Half max time
        #half_dF_max_value = (self.fit_max_value - self.bl) / 2. + self.bl
        self.FWHM = self.params['s']*2*numpy.sqrt(2.*numpy.log(2.))
        #solver = fitfun.Solver()
        #solver.set_function(self.fit_function, self.params,
        #        value = half_dF_max_value)
        #solver.set_solve_range(self.fit_max_loc,
        #        self.fit_max_loc + 10*self.width, self.fit_max_loc + 1.0)
        #solver.solve()
        #print 'half-sol done'
        #self.FDHM_loc = solver.solution
        #self.FDHM_value = solver.function(solver.solution)
        #self.FDHM = self.FDHM_loc - self.fit_max_loc
        #if self.params.has_key('d'):
        #    self.rise = self.params['d']
        #else:
        #    self.rise = self.fit_max_loc - self.params['mu']

class SparkTransient(object):
    def __init__(self, fdata, tdata):
        self.data = fdata
        self.time = tdata
        self.start = self.time[0]
        self.end = self.time[-1]
        self.duration = self.end - self.start
        self.tstep = tdata[1]-tdata[0]
        self.F_max, self.t_at_F_max = self.get_max()
        self.F_min = min(self.data)
        self.F_spread = self.F_max-self.F_min
        self.fit_function = fitfun.fit_func_4
        self.params=None

        self.do_analysis()

    def get_max(self):
        max_f_val = max(self.data)
        t_at_max_y = self.data.tolist().index(max_f_val)
        return max_f_val,t_at_max_y

    def do_analysis(self):
        oo = fitfun.Optimizer(self.time, self.data)
        oo.set_function(self.fit_function)
        if self.fit_function in [fitfun.fit_func_1,fitfun.fit_func_2]:
            oo.set_parameter_range('A', 0., 5*self.F_max, 1.)
            oo.set_parameter_range('B', 0., self.F_max-0.5*self.F_spread, self.F_min + 0.25*self.F_spread)
            oo.set_parameter_range('tau1', 0., 100.,10.)
            oo.set_parameter_range('tau2',0, 500.,10.)
            oo.set_parameter_range('mu',self.start, self.end, self.time[self.t_at_F_max])
        else:
            oo.set_parameter_range('A', 0., 5*self.F_max, 1.)
            oo.set_parameter_range('B', 0., self.F_max-0.5*self.F_spread,
                    self.F_min + 0.25*self.F_spread)
            oo.set_parameter_range('C', -0.5*self.F_spread, 0.5*self.F_spread,
                    0.0)
            #oo.set_parameter_range('tau1', 0., 5000.,10.)

            oo.set_parameter_range('tau2',0, 500.,10.)

            #up_dur = self.time[self.t_at_F_max] - self.start

            #Get estimate for mu1
            dF_func = interp1d(self.time[:-1], numpy.diff(self.data))
            def dF(arg):
                return dF_func(arg)
            max_solver = fitfun.MaxSolver()
            max_solver.set_function(dF, {})
            max_solver.set_solve_range(self.start, self.end, self.time[self.t_at_F_max])
            max_solver.solve()
            mu1_estimate = max_solver.solution
            up_dur = self.time[self.t_at_F_max] - mu1_estimate
            #print up_dur
            #print self.time[self.t_at_F_max],self.t_at_F_max,self.start
            if up_dur<1e-3:
                #print 'first'
                up_dur   = self.time[self.t_at_F_max] - self.start

                oo.set_parameter_range('mu',self.start, self.time[self.t_at_F_max], self.time[self.t_at_F_max]-0.3*up_dur)
            else:
                #print 'second'
                oo.set_parameter_range('mu',self.start, self.time[self.t_at_F_max], mu1_estimate)
            oo.set_parameter_range('d',0, up_dur*3,up_dur)

        try:
            oo.optimize()
        except RuntimeError:
            f= open('ppp.pickle','w')
            pickle.dump(self.data,f)
            pickle.dump(self.time,f)
            f.close()
            raise RuntimeError

        self.oo=oo
        print 'optimize done'
        self.params = oo.solutions
        print self.params
        self.bl_left = self.params['B']+self.params['C']
        self.bl_right = self.params['B']
        #max from fit
        #maxsolver =  fitfun.MaxSolver()
        #maxsolver.set_function(self.fit_function, self.params)
        #maxsolver.set_solve_range(self.start, self.end, self.time[self.t_at_F_max])
        #maxsolver.solve()

        #print 'max-sol done'
        self.fit_max_loc = self.params['mu'] + self.params['d']
        #self.fit_max_loc = maxsolver.solution
        #self.fit_max_value = maxsolver.function(self.fit_max_loc)
        self.fit_max_value = self.params['A']*(1-numpy.exp(-2.)) + self.bl_left
        #Half max time
        #half_dF_max_value = (self.fit_max_value - self.bl) / 2. + self.bl
        #solver = fitfun.Solver()
        #solver.set_function(self.fit_function, self.params,
        #        value = half_dF_max_value)
        #solver.set_solve_range(self.fit_max_loc,
        #        self.fit_max_loc + 10*self.duration, self.fit_max_loc + 1.0)
        #solver.solve()
        #print 'half-sol done'
        #self.FDHM_loc = solver.solution
        self.FDHM_loc = self.params['tau2']*numpy.log(2.)+self.params['mu'] + self.params['d']
        self.FDHM_value = (self.bl_right + self.fit_max_value)/2.
        self.FDHM = self.FDHM_loc - self.fit_max_loc
        if self.params.has_key('d'):
            self.rise = self.params['d']
        else:
            self.rise = self.fit_max_loc - self.params['mu']





class Transient:
    def __init__(self, data, start, end, physical_x, ds, bl = False):
        self.data = data
        self.calc_bl = bl
        self.start = start
        self.end = end
        self.max_y,self.max = self.get_max()
        self.min_y = min(self.data)
        self.mean_y = numpy.array(self.data).mean()
        self.phys_x = physical_x
        self.phys_x0 = physical_x[0]
        self.offset = start
        self.x0 = 0
        self.x_max = self.max
        self.x_end = len(self.data)
        self.x_start = 0
        self.start_phys =self.phys_x[0]
        self.end_phys =self.phys_x[-1]
        self.max_phys = self.phys_x[self.x_max]
        self.relaxation_duration = self.end_phys - self.max_phys
        self.tstep= numpy.mean(numpy.diff(physical_x))
        self.analyzed = False

        self.relaxation_bl = None
        self.decay = None
        self.decay_residual = None
        self.decay_y = None
        if bl:
            self.baseline, bl_loc = self.get_bl()
            print '\n\n\nmax is',self.max_y
            self.max_ymbl = self.max_y - self.baseline
            print '\n\n\nmaxybl is',self.max_ymbl, self.baseline
            self.max_ydbl = self.max_y / self.baseline
        else:
            self.baseline = -1
            #print 'bl: ',baseline,' maxy: ',self.max_y_bl

    def get_max(self):
        max_y_val = max(self.data)
        x_at_max_y = self.data.tolist().index(max_y_val)
        return max_y_val,x_at_max_y

    def get_bl(self):
        #bl_time = 20e-3
        #bl_length = int(bl_time/self.tstep)
        #print 'len',bl_length,self.tstep
        #if bl_length == 0:
        #    bl_length = 2
        #self.bl_end_phys = self.phys_x[bl_length]
        #self.bl = numpy.mean(self.data[:bl_length])
        look_index = int(self.max/2.)
        self.bl = self.data[0:look_index].mean()
        self.bl_loc = look_index/2
        #self.bl = self.data[0]
        #print 'bb',self.bl
        return self.bl, self.bl_loc

    def get_relaxation_bl(self):
        return self.relaxation_bl


    def fit_decay(self):
        #start = int((self.x_end - self.x_max) * 0.4)
        start = 0
        decay_data_all = self.data[self.x_max + start:self.x_end]
        x_all = self.phys_x[self.x_max+start:self.x_end]
#        start_percentage = 0.8
        start_percentage = 0.99
        perc_x = helpers.find_p(decay_data_all,start_percentage)
#        perc_x = 0
#        print 'P1',x_all[0],decay_data_all[0]
        decay_data_all = decay_data_all[perc_x:]
        x_all = x_all[perc_x:]
#        print 'PP',perc_x, x_all[0],decay_data_all[0]
#        print 'F',decay_data_all
#        print 'T',x_all
        if perc_x == -1 or self.x_end - perc_x < 5:
            self.decay = 0.0
            self.relaxation_bl = 0.0
            self.decay_residual = 0.0
        else:
        #if 1:
            #normalized = normalized_all[perc_x:]
            normalized = decay_data_all
            #print "["+", ".join(["%f"%el for el in normalized])+"]"
            try:
                #x = numpy.array(x_all[perc_x:])
                x = x_all - x_all[0]
                #print "["+", ".join(["%f"%el for el in x])+"]"
                #self.decay_x0 = x_all[0]
                self.decay_x = x_all
                print 'dur',self.relaxation_duration,self.max_y,self.mean_y,self.min_y
                limits = {'tau':(0, self.relaxation_duration*5.),\
#                        'a':(self.mean_y, self.mean_y + 2*abs(self.max_y-self.mean_y)),
                        #'a':(self.mean_y,self.mean_y + 20*(self.max_y - self.mean_y)),
                        ###'a':((self.max_y - self.min_y)*0.5,(self.max_y - self.min_y)*3 ),
                        'a':(0.0,self.max_y *3 ),
#                        'c':(self.mean_y - 2*abs(self.min_y-self.mean_y), self.mean_y)}
                        #'c':(self.mean_y - 20*(self.mean_y-self.min_y),self.mean_y)}
                        ###'c':(self.min_y*0.5,self.mean_y)}
                        'c':(min(0.0,self.min_y), self.max_y)}
#                        'c':(-0.2,self.mean_y)}
 #                       'a':(self.max_y-0.5*abs(self.min_y),self.max_y+0.5*abs(self.min_y))}
#                        'c':(self.max_y-0.5*abs(self.min_y),self.max_y+0.5*abs(self.min_y))}

                print limits
                print len(x),len(normalized)
                #limits = {}
                #R = ResidualCalculator(x, normalized, limits)
                R=None
                param = leastsq(R.residuals, [0., 0.,  0.], maxfev = 50000)[0]
                self.decay = R.scaleparam(param)[0]
                self.decay_a = R.scaleparam(param)[1]
                self.relaxation_bl = R.scaleparam(param)[2]
                self.decay_residual = -math.log10(R.res_error(param))
                self.decay_y=R.func(param)
            except:
                print 'error'
                traceback.print_exc()
                self.decay = 0.0
                self.relaxation_bl = 0.0
                self.decay_a=0.0
                self.relaxation_bl = 0.0
                self.decay_residual = 0.0
        #print 'tau:', self.decay, 'a:',self.decay_a,' rbl:',self.relaxation_bl,\
        #        ' residual:',self.decay_residual

        self.analyzed = True
    def find_halftime(self):
        decay_data_all = self.data[self.x_max:self.x_end]
        normalized = [(el-min(decay_data_all))/(max(decay_data_all)-\
                min(decay_data_all)) for el in decay_data_all]
        self.halftime = self.phys_x[helpers.find_p(normalized,0.5)+\
                self.x_max]-self.phys_x[self.x_max]

class TransientGroup():
    def __init__(self,ds):
        self.transients = {}
        self.ds = ds
        self.order = []
#        self.transients_since_start = 0

    def addTransient(self,transient,key=None):
        if key is not None:
            self.transients[key] = transient
            print 'updating transient',key
        else:
            tr_key = uuid.uuid4().hex
            self.transients[tr_key] = transient
#            self.transients_since_start += 1
            print 'adding transient', len(self.transients), tr_key
        self.order_transients()

    def sortf(self,x,y):
        if self.transients[x].start > self.transients[y].start:
            return 1
        elif self.transients[x].start < self.transients[y].start:
            return -1
        else:
            return 0
    def order_transients(self):
        self.order = self.transients.keys()
        self.order.sort(cmp=self.sortf)
        print 'order',self.order

    def remove(self,key):
        self.transients.pop(key)
        self.order_transients()

    def update(self,key,start,end):
        start = self.ds.find_phys_index(start)
        end = self.ds.find_phys_index(end)
        print self.transients.keys()
#        print self.transients_since_start
        print 'key now', key
        #self.transients.pop(key)
        self.addTransient(Transient(self.ds.smoothed.data[start:end],\
                start,end,self.ds.physical_x_axis_values.data[start:end],\
                self.ds,self.ds.calculate_bl), key)
        #return self.transients_since_start

    def append(self,transientgroup):
        for key in transientgroup.transients:
            tr = transientgroup.transients[key]
            print 'adding',key,tr
            self.addTransient(tr, key)

    def get_transient(self,i):
        keys=self.transients.keys()
        keys.sort()
        return self.transients[keys[i]]

    def get_delays(self):
        self.delays=[]
        self.delaytimes=[]
        keys=self.order
        print 'order',keys
        for k in range(1,len(keys)):
            self.delays.append(self.transients[keys[k]].max_phys -\
                    self.transients[keys[k-1]].max_phys)
            self.delaytimes.append(self.transients[keys[k]].max_phys)
        return self.delays,self.delaytimes

    def get_amps(self):
        self.amps=[]
        self.times=[]
        keys=self.order
        for k in keys:
            print 'k=',k
            self.amps.append(self.transients[k].max_y)
            self.times.append(self.transients[k].max_phys)
        print 'sending', self.amps, self.times
        return self.amps,self.times

    def get_amps_minus_bl(self):
        self.bl_amps_minus = []
        self.times=[]
        keys=self.order
        for k in keys:
            print 'kk=',k,self.transients[k].max_ymbl
            self.bl_amps_minus.append(self.transients[k].max_ymbl)
            self.times.append(self.transients[k].max_phys)
        print 'sending mbl', self.bl_amps_minus, self.times
        return self.bl_amps_minus,self.times

    def get_amps_minus_relbl(self):
        self.bl_amps_minus_relbl = []
        self.times=[]
        keys=self.order
        for k in keys:
            self.bl_amps_minus_relbl.append(self.transients[k].max_y-self.transients[k].relaxation_bl)
            self.times.append(self.transients[k].max_phys)
        return self.bl_amps_minus_relbl,self.times


    def get_amps_div_bl(self):
        self.bl_amps_div = []
        self.times=[]
        keys=self.order
        for k in keys:
            self.bl_amps_div.append(self.transients[k].max_ydbl)
            self.times.append(self.transients[k].max_phys)
        return self.bl_amps_div,self.times

    def get_decays(self):
        self.decays=[]
        self.times=[]
        keys=self.order
        for k in keys:
            self.transients[k].fit_decay()
            self.decays.append(self.transients[k].decay)
            self.times.append(self.transients[k].max_phys)
        return self.decays,self.times

    def get_relaxation_baselines(self):
        self.relaxation_baselines=[]
        self.times=[]
        keys=self.order
        for k in keys:
            if not hasattr(self.transients[k],'relaxation_baseline'):
                self.transients[k].fit_decay()
            self.relaxation_baselines.append(self.transients[k].relaxation_bl)
            self.times.append(self.transients[k].max_phys)
        return self.relaxation_baselines,self.times

    def get_decay_residuals(self):
        self.decay_residuals=[]
        self.times=[]
        keys=self.order
        for k in keys:
            if not hasattr(self.transients[k],'decay_residual'):
                self.transients[k].fit_decay()
            self.decay_residuals.append(self.transients[k].decay_residual)
            self.times.append(self.transients[k].max_phys)
        return self.decay_residuals,self.times

    def get_halftimes(self):
        self.halftimes=[]
        self.times=[]
        keys=self.order
        for k in keys:
            self.transients[k].find_halftime()
            self.halftimes.append(self.transients[k].halftime)
            self.times.append(self.transients[k].max_phys)
        return self.halftimes,self.times

    def get_baselines(self):
        self.baselines=[]
        self.times=[]
        keys=self.order
        for k in keys:
            self.baselines.append(self.transients[k].bl)
            self.times.append(self.transients[k].max_phys)
        return self.baselines,self.times

    def get_A2A1(self,min_delay):
        self.ratios =[]
        self.A2A1_ratios = []
        self.A2A1_delays = []
        self.A2A1_indexes = []
        self.A2A1_amps = []
        keys=self.order
        for i in range(1,len(keys)):
            delay = self.transients[keys[i]].max_phys-self.transients[keys[i-1]].max_phys
            if i == 1:
                self.ratios.append([(i-1,i),self.transients[keys[i]].max_ymbl/self.transients[keys[i-1]].max_ymbl,delay])
                self.A2A1_ratios.append(self.transients[keys[i]].max_ymbl/self.transients[keys[i-1]].max_ymbl)
                self.A2A1_delays.append(delay)
                self.A2A1_indexes.append(str((i-1,i)))
                self.A2A1_amps.append(str((self.transients[keys[i-1]].max_ymbl,str(self.transients[keys[i]].max_ymbl))))
            else:
                previous_delay =  self.transients[keys[i-1]].max_phys-self.transients[keys[i-2]].max_phys
                if previous_delay>min_delay:
                    self.ratios.append([(i-1,i),self.transients[keys[i]].max_ymbl/self.transients[keys[i-1]].max_ymbl,delay])
                    self.A2A1_ratios.append(self.transients[keys[i]].max_ymbl/self.transients[keys[i-1]].max_ymbl)
                    self.A2A1_delays.append(delay)
                    self.A2A1_indexes.append(str((i-1,i)))
                    self.A2A1_amps.append(str((self.transients[keys[i-1]].max_ymbl,self.transients[keys[i]].max_ymbl)))
        return self.ratios

