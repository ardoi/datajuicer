import numpy as n
n.seterr(over="ignore")
from collections import OrderedDict
import inspect
#import itertools

import scipy.optimize as so
import scipy.special as ss

class ScaledOperation(object):
    def __init__(self, scaled = True):
        self.function = None
        self.parameters = OrderedDict()
        self.unscaled_solutions = {}
        self.scaled = scaled

    def set_parameter_range(self, name, minval, maxval, initial):
        #print 'Set parameter: %s min=%f max=%f init=%f'%(name,float(minval),float(maxval),float(initial))
        if name not in self.parameters:
            error= "%s not a parameter of the function to be optimized"%name
            raise ValueError(error)
        else:
            assert minval <= initial , "%s = %f, %f"%(name,minval, initial)
            assert maxval >= initial , "%s = %f, %f"%(name, maxval, initial)
            assert maxval>minval, "%s = %f, %f"%(name,minval, maxval)
            self.parameters[name]={'min':float(minval), 'max':float(maxval), 'init':float(initial)}

    def show_parameters(self):
        initial = {}
        for p in self.parameters:
            print p, self.parameters[p]
            initial[p] = self.parameters[p]['init']
        print 'init=',initial


    def unscale(self, x):
        return x


    def scale(self, sx):
        return sx


    def make_parameter_arrays(self):
        pc = len(self.parameters)
        #self.minvals = n.zeros(pc)
        #self.maxvals = n.zeros(pc)
        self.initial_conditions = n.zeros(pc)
        self.bounds = []
        i=0
        for p,d in self.parameters.iteritems():
            #self.minvals[i] = d['min']
            #self.maxvals[i] = d['max']
            self.bounds.append((d['min'],d['max']))
            self.initial_conditions[i] = d['init']
            i+=1

    def func_for_scaled_values(self, x, *scaled_parameters):
        #if isinstance(scaled_parameters[0], list):
        #    scaled_parameters = scaled_parameters[0]
        #args = self.unscale(scaled_parameters)
        return self.operation_func(scaled_parameters)

    def rerange_parameters(self, previous_sol,amount = 0.5):
        """Try to increase allowed ranges of parameters for fitting plus/minus
        amount*100 percent from the 'initial' value
        """
        for param, p_range in self.parameters.iteritems():
            p_range['init'] = previous_sol[param]
            p_range['min'] = min(p_range['min'], p_range['init']*amount)
            p_range['max'] = max(p_range['max'], p_range['init']*(1+amount))

class Optimizer(ScaledOperation):
    def __init__(self, xvals, yvals, scaled = True):
        self.arg_vals = n.array(xvals)
        self.func0_vals = n.array(yvals)
        self.sigmas = None
        #print 'optimizer',self.arg_vals.tolist()
        #print self.func0_vals.tolist()
        self.ftol = 1.49e-7
        self.xtol = 1.49e-7
        super(Optimizer,self).__init__(scaled=scaled)

    def additional_parameters(self, param_names):
        for pn in param_names:
            self.parameters[pn] = {}

    def set_function(self, function, only_function=False):
        variables = inspect.getargspec(function).args
        #print 'set func',function, variables
        if 'arg' not in variables:
            error = "argument to function has to be given with arg keyword"
            raise ValueError(error)
        else:
            for v in variables:
                if v in ['arg','self']:
                    continue
                if not only_function:
                    self.parameters[v] = {}
        self.function = function
        #print "Parameters of the function are: %s"%(str(self.parameters.keys()))


    def operation_func(self, args):
        #return self.function(arg=self.arg_vals, *args)# - self.func0_vals
        #print 'args=', args
        return ((self.function(self.arg_vals, *args) - self.func0_vals)**2).sum()

    def set_sigmas(self, sigmas):
        self.sigmas = sigmas

    def optimize(self, max_fev = 100000):
        self.make_parameter_arrays()
        #print '\noptimize'
        #print self.function
        #print self.initial_conditions.tolist()
        try:
            #scaled_initial_conditions = self.scale(self.initial_conditions)
            #res = so.curve_fit(self.func_for_scaled_values, self.arg_vals, self.func0_vals,
            #        scaled_initial_conditions, sigma=self.sigmas, maxfev=max_fev, factor=.1,
            #        epsfcn=1e-5, ftol=self.ftol, xtol=self.xtol)
            res = so.minimize(self.operation_func, self.initial_conditions,method='L-BFGS-B', bounds=self.bounds, options={'ftol':1.49e-7})
            scaled_solutions = res.x.tolist()
            unscaled_solutions = self.unscale(scaled_solutions)
            self.solutions = {}
            for i,p in enumerate(self.parameters.keys()):
                self.solutions[p] = unscaled_solutions[i]
        except:
            print 'exception in optimize'
            import traceback
            traceback.print_exc()
            self.solutions = {}
        #print 'sol=',self.solutions

    def param_error(self, params):
        errors = self.function(self.arg_vals, **params)-self.func0_vals
        error = (errors**2).sum()#.mean()
        return error

    def aic(self):
        err = self.param_error(self.solutions)
        aic = self.arg_vals.size*n.log(err) + len(self.solutions)*2
        return aic

    def aicc(self):
        k=len(self.solutions)
        nn=self.arg_vals.size
        aicc = self.aic() + 2*k*(k+1)/float(nn-k-1)
        return aicc

    def closeness_to_limit(self):
        #print 'close'
        treshold = 0.05
        count_limit = 3
        count = 0
        for p in self.solutions:
            pmin = self.parameters[p]['min']
            pmax = self.parameters[p]['max']
            prange = pmax-pmin
            val = self.solutions[p]
            tr = 1 - max((pmax-val)/prange, (val-pmin)/prange)
            if tr<treshold:
                count += 1
        #print "too close = %i"%count
        if count >= count_limit:
            return True
        else:
            return False

    def show_solution(self):
        if self.solutions:
            import pylab
            pylab.plot(self.arg_vals, self.func0_vals, 's',mec='None',ms=7,alpha=0.7,color='navy')
            pylab.plot(self.arg_vals,
                    self.function(arg=self.arg_vals, **self.solutions),
                    '-',color='orange', lw=2)
            title = ", ".join(["%s=%.4f"%(el,self.solutions[el]) for el in self.solutions.keys()])
            pylab.title(title)
            pylab.show()

