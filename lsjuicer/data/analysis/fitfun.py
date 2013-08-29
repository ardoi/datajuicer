import numpy as n
n.seterr(over="ignore")
from collections import OrderedDict
import inspect
import itertools

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
            assert minval <= initial and maxval >= initial and maxval>minval, "%s = %f, %f, %f"%(name,minval, maxval, initial)
            self.parameters[name]={'min':float(minval), 'max':float(maxval), 'init':float(initial)}

    def shift_parameter(self, name, shift):
        self.parameters[name]['min']+=shift
        self.parameters[name]['max']+=shift
        self.parameters[name]['init']+=shift

    def show_parameters(self):
        for p in self.parameters:
            print p, self.parameters[p]

    def unscale(self, x, name):
        if not self.scaled:
            return x
        minval = self.parameters[name]['min']
        maxval = self.parameters[name]['max']
        return ((n.arctan(x)/n.pi+0.5)*(maxval-minval))+minval


    def scale(self, sx, name):
        if not self.scaled:
            return sx
        minval = self.parameters[name]['min']
        maxval = self.parameters[name]['max']
        v = n.tan(((sx-minval)/(maxval-minval)-0.5)*n.pi)
        return v

    def func_for_scaled_values(self, x, *scaled_parameters):
        kw_args = {}
        parameter_names = self.parameters.keys()
        if isinstance(scaled_parameters[0], list):
            scaled_parameters = scaled_parameters[0]
        for i,p in enumerate(scaled_parameters):
            name = parameter_names[i]
            sparam_value = scaled_parameters[i]
            #print sparam_value
            kw_args[name] = self.unscale(float(sparam_value), name)
        return self.operation_func(kw_args)

class Solver(ScaledOperation):
    def set_function(self, function, f_params, value=0.0):
        variables = inspect.getargspec(function).args
        if 'arg' not in variables:
            error = "argument to function has to be given with arg keyword"
            raise ValueError(error)
        else:
            for v in variables:
                if v == 'arg':
                    self.parameters['arg'] = {}
                else:
                    continue
        self.function = lambda x:function(arg=x,**f_params)-value
        print "Parameters of the function are: %s"%(str(self.parameters.keys()))


    def solve(self):
        ic = self.parameters['arg']['init']
        sic = self.scale(ic, 'arg')
        res = so.fsolve(self.func_for_scaled_values, sic)
        self.solution = self.unscale(res[0], 'arg')
        #print self.solution


    def set_solve_range(self, start, end, initial):
        self.set_parameter_range('arg', start, end, initial)

    def func_for_scaled_values(self, *scaled_parameters):
        kw_args = {}
        parameter_names = self.parameters.keys()
        for i,p in enumerate(scaled_parameters):
            name = parameter_names[i]
            sparam_value = scaled_parameters[i]
            #print sparam_value
            kw_args[name] = self.unscale(float(sparam_value), name)
        return self.operation_func(kw_args)

    def operation_func(self,args):
        return self.function(args['arg'])

class MaxSolver(Solver):
    def solve(self):
        ic = self.parameters['arg']['init']
        sic = self.scale(ic, 'arg')
        res = so.fmin(self.func_for_scaled_values, sic)
        self.solution = self.unscale(res[0], 'arg')
        print self.solution

    def operation_func(self,args):
        out= -self.function(args['arg'])
        return out

class Optimizer(ScaledOperation):
    def __init__(self, xvals, yvals, scaled = True):
        self.arg_vals = n.array(xvals)
        self.func0_vals = n.array(yvals)
        self.sigmas = None
        #print 'optimizer',self.arg_vals.tolist()
        #print self.func0_vals.tolist()
        super(Optimizer,self).__init__(scaled=scaled)

    def additional_parameters(self, param_names):
        for pn in param_names:
            self.parameters[pn] = {}

    def set_function(self, function, only_function=False):
        #print 'set function',function
        variables = inspect.getargspec(function).args
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


    def operation_func(self, kwargs):
        return self.function(arg=self.arg_vals, **kwargs)# - self.func0_vals
        #return self.function(arg=self.arg_vals, **kwargs)# - self.func0_vals

    def optimize_with_permutations(self):
        permutations = itertools.product((-1,0,1), repeat=1)
        parameter_names = self.parameters.keys()
        amount=0.2
        min_error = None
        best_p=None
        for p in permutations:
            scaled_initial_conditions = []
            ics=[]
            ranges=[]
            for i,parameter_name in enumerate(parameter_names):
                param = self.parameters[parameter_name]
                ic = param['init']
                param_range = param['max']-param['min']
                ranges.append(param_range)
                #ic += param_range*amount*p[i]
                ic += ic*amount*p[i]
                ics.append(ic)
                sic = self.scale(ic, parameter_name)
                scaled_initial_conditions.append(sic)
            res = so.leastsq(self.func_for_scaled_values, scaled_initial_conditions)
            sol4p = res[0]
            errors = self.func_for_scaled_values(sol4p)
            error = n.sqrt((errors**2).mean())
            #print p,error
            if min_error is None:
                min_error = error
                scaled_solutions = sol4p
                best_p = p
                continue
            if error<min_error:
                min_error = error
                scaled_solutions = sol4p
                best_p = p
                continue

        #print parameter_names
        #print min_error, scaled_solutions, best_p
        status = res[1]
        self.solutions = {}
        for i, ssol in enumerate(scaled_solutions):
            parameter_name = parameter_names[i]
            sol = self.unscale(ssol, parameter_name)
            self.solutions[parameter_name] = sol
        #print 'solutions=',self.solutions
        #print min_error

    def set_sigmas(self, sigmas):
        self.sigmas = sigmas

    def optimize(self):
        try:
            parameter_names = self.parameters.keys()
            scaled_initial_conditions = []
            for parameter_name in parameter_names:
                ic = self.parameters[parameter_name]['init']
                sic = self.scale(ic, parameter_name)
                scaled_initial_conditions.append(sic)
            #res = so.leastsq(self.func_for_scaled_values, scaled_initial_conditions,ftol=1e-12, xtol=1e-12)
            #print 'ic', scaled_initial_conditions
            #res = so.curve_fit(self.func_for_scaled_values, self.arg_vals, self.func0_vals,scaled_initial_conditions, sigma=self.sigmas,maxfev=100000,factor=.1, epsfcn=1e-7, ftol=1e-12, xtol=1e-12)
            res = so.curve_fit(self.func_for_scaled_values, self.arg_vals, self.func0_vals,scaled_initial_conditions, sigma=self.sigmas, maxfev=100000, factor=.1, ftol=1e-12, xtol=1e-12)
            scaled_solutions = res[0].tolist()
            #print 'ss',scaled_solutions
            self.solutions = {}
            for i, ssol in enumerate(scaled_solutions):
                parameter_name = parameter_names[i]
                sol = self.unscale(ssol, parameter_name)
                self.solutions[parameter_name] = sol
            try:
                if res[1].ndim == 2:
                    variations = res[1].diagonal()
                else:
                    variations = res[1]
            #errors = self.func_for_scaled_values(self.arg_vals, scaled_solutions)
            #self.error = n.sqrt((errors**2).mean())
            #status = res[1]
                self.errors_plus = {}
                self.errors_minus = {}
                for i, ssol in enumerate(scaled_solutions):
                    parameter_name = parameter_names[i]
                    serror_plus = ssol + variations[i]
                    serror_minus = ssol - variations[i]
                    error_plus = self.unscale(serror_plus, parameter_name)
                    error_minus = self.unscale(serror_minus, parameter_name)
                    self.errors_plus[parameter_name] = error_plus-sol
                    self.errors_minus[parameter_name] = sol - error_minus
                #print self.errors_plus,self.errors_minus
            except AttributeError:
                pass
        except:
            print 'exception in optimize'
            import traceback
            traceback.print_exc()
            self.solutions = {}
        #print 'sol=',self.solutions

    def param_error(self, params):
        errors = self.operation_func(params)-self.func0_vals
        error = (errors**2).mean()
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

    def jiggle(self, params):
        #print "\n jiggle"
        control = self.param_error(params)
        #print 'control', control
        #print 'params', params
        parameter_names = self.parameters.keys()
        if 's' in parameter_names:
            parameter_names.remove('s')
        amount = 0.2
        treshold = -0.001
        new_params = params.copy()
        for i,parameter_name in enumerate(parameter_names):
            sol = params.copy()
            new_plus = sol[parameter_name] * (1+amount)
            if new_plus <= self.parameters[parameter_name]['max']:
                sol[parameter_name] = new_plus
                error_plus = self.param_error(sol)
            else:
                #print parameter_name, 'too far', new_plus, self.parameters[parameter_name]['max']
                error_plus = control
            new_minus = sol[parameter_name] * (1-amount)
            if new_minus >= self.parameters[parameter_name]['min']:
                sol[parameter_name] = new_minus
                error_minus = self.param_error(sol)
            else:
                #print parameter_name, 'too far', new_minus, self.parameters[parameter_name]['min']
                error_minus = control
            min_change = error_minus/control -1
            plus_change = error_plus/control - 1
            #print parameter_name, "%.3f"%(error_plus/control-1), "%.3f"%(error_minus/control-1)
            if min_change <= treshold:
                new_params[parameter_name] *= (1-amount)
            elif plus_change <= treshold:
                new_params[parameter_name] *= (1+amount)
        #print 'new error', self.param_error(new_params)
        #print new_params == params
        return new_params

    def jiggle_rec(self, params):
        return params
        old = params.copy()
        start_error = self.param_error(old)
        steps = 0
        max_steps = 100
        while steps<max_steps:#old != new:
            new = self.jiggle(old)
            steps+=1
            if new == old:
                break
            else:
                old = new
        end_error = self.param_error(new)
        #print 'jiggle res',steps, start_error, end_error
        #print params, new
        return new

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

def fit_func_1(arg, mu, tau1, tau2, A, B):
    t1=tau1
    t2=tau2
    out = (1.0 - n.exp(-(arg-mu)/t1))*(A*n.exp(-(arg-mu)/t2))+B
    return n.where(arg < mu, B, out)

def fit_func_11(arg, mu, tau1, tau2, tau3, A1, A2, B):
    t1=tau1
    t2=tau2
    t3=tau3
    out = (1.0 - n.exp(-(arg-mu)/t1))*(A1*n.exp(-(arg-mu)/t2)+A2*n.exp(-(arg-mu)/t3))+B
    return n.where(arg < mu, B, out)

def fit_func_2(arg, mu, tau1, tau2, A, B):
    #Convolution of a Gaussian(0,s) with fit_func_1
    s=1.0
    t = arg
    t1=tau1
    t2=tau2
    a1 = (t1+t2)*(t2*s*s+t1*(-2*t*t2+2*t2*mu+s*s))/(2*t1*t1*t2*t2)
    a2 = (t*t1*t2-t2*s*s-t1*(t2*mu+s*s))/(n.sqrt(2.)*t1*t2*s)
    a3 = (-2*t*t2+2*t2*mu+s*s)/(2.*t2*t2)
    a4 = (-t*t2+t2*mu+s*s)/(n.sqrt(2.)*t2*s)
    return B + A/2.*(-n.exp(a1)*(1+ss.erf(a2))+n.exp(a3)*ss.erfc(a4))

def fit_func_3(arg, tau1, tau2, mu, d, A, B):
    s = 2.0
    s2 = n.sqrt(2.)*s
    t = arg
    mu1 = mu
    mu2 = mu1 + d
    a1  = (mu1-mu2)/tau1
    a2 = t/tau1
    a3 = (t - mu1)/s2
    a4 = (t - mu2)/s2
    a5 = (s**2 + 2*mu1*tau1)/(2.*tau1**2)
    a6 = (s**2 - t*tau1 + mu1*tau1)/(s2*tau1)
    a7 = (s**2 - t*tau1 + mu2*tau1)/(s2*tau1)
    a8 = (s**2 - 2*t*tau2+2*mu2*tau2)/(2*tau2**2)
    a9 = (s**2 - t*tau2 + mu2*tau2)/(s2*tau2)
    #print a1,a2,a3,a4,a5,a6,a7,a8,a9
    c = B
    f = c + 0.5*A*(\
            1./(1.-n.exp(a1))*n.exp(-a2)*(
                n.exp(a2)*ss.erf(a3)-n.exp(a2)*ss.erf(a4)+
                n.exp(a5)*(ss.erf(a6)-ss.erf(a7))) -
            n.exp(a8)*(-1+ss.erf(a9)))
    return f

def gaussian_1d(arg, mu, s, A, B):
    f = A*n.exp(-(arg-mu)**2/(2.*s**2)) + B
    return f

def normal_dist(arg, mu, s):
    f = 1./n.sqrt(2.0*n.pi)/s*n.exp(-(arg-mu)**2/(2.*s**2))
    return f

def fit_func_4(arg, tau2, mu, d, A, B, C):
    t=arg
    mu1 = mu
    mu2 = mu1 + d
    tau1=(mu2-mu1)/2.
    #force f2 and f3 to reach 1-exp(-2) at mu2
    f2 = (1-n.exp(-(t-mu1)/tau1))#/(1-n.exp((mu1-mu2)/tau1))
    f3 = n.exp(-(t-mu2)/tau2)*(1-n.exp(-2.)+C/A)
    f = A*(f2*((t>mu1)-(t>mu2))+f3*(t>mu2))+B+C*(t<=mu2)
    return f

def ff4_bl(t, tau2, mu,d2, d,C,B):
    return ff5_bl(t,tau2,mu,0.0,d,C,B)

def fit_func_4_0(arg, tau2, mu, d, A, B):
    t=arg
    mu1 = mu
    mu2 = mu1 + d
    tau1=(mu2-mu1)/2.
    #force f2 and f3 to reach 1-exp(-2) at mu2
    f2 = (1-n.exp(-(t-mu1)/tau1))#/(1-n.exp((mu1-mu2)/tau1))
    f3 = n.exp(-(t-mu2)/tau2)*(1-n.exp(-2.))
    f = A*(f2*((t>mu1)-(t>mu2))+f3*(t>mu2))+B
    return f

def ff40_start_tau(arg, tau2, mu,d):
    return fit_func_1(arg, tau2, mu, d, 12500., 6000.)


def f5(arg, tau2, d, d2, m2, A, B, C):
    """same as fit_func_4 but between has a plateau after the rising phase"""
    t=arg
    #mu1 = mu
    #mu2 = mu1 + d
    mu2 = m2
    mu1 = mu2 - d
    tau1=(mu2-mu1)/2.
    #force f2 and f3 to reach 1-exp(-2) at mu2
    f2 = (1-n.exp(-(t-mu1)/tau1))#/(1-n.exp((mu1-mu2)/tau1))
    f3 = n.exp(-(t-mu2)/tau2)*(1-n.exp(-2.))
    f = A*(f2*((t>mu1)-(t>mu2))+f3*(t>mu2))+B
    return f

def ff5_bl(arg, tau2, m2,d2, d,s,A,B,C):
    #start of decay after plateau
    mm2 = m2+d2
    t=arg
    return C*n.exp(-(t-mm2)/tau2)*(t>mm2)+B+C*(t<=mm2)

def ff50(arg, tau2, d, m2, A, B, C):
    """same as ff5 but with s and d2 fixed

    Args:
        arg: time vector
        tau2: decay time of transient decrease
        d: duration of transient increase (exp increase time d/2)
        d2: duration of plateau phase
        #m: start of transient
        m2: start of plateau phase
        s: width of the gaussian
        A: Amplitude of transient
        B: Baseline
        C: Initial baseline offset from B

    Returns:
        Function values for all arg values
    """
    d2 = 0.0
    s = 2.0
    return ff5(arg, tau2, d, d2, m2, s, A, B, C)

def ff5(arg, tau2, d, d2, m2, s, A, B, C):
    """convolution of gaussian(0,s) with f5

    Args:
        arg: time vector
        tau2: decay time of transient decrease
        d: duration of transient increase (exp increase time d/2)
        d2: duration of plateau phase
        #m: start of transient
        m2: start of plateau phase
        s: width of the gaussian
        A: Amplitude of transient
        B: Baseline
        C: Initial baseline offset from B

    Returns:
        Function values for all arg values
    """
    #frame = inspect.currentframe()
    #print 'call', inspect.getargvalues(frame)
    m = m2 - d

    t = arg
    E = n.exp(1.0)
    sqrt2 = n.sqrt(2.0)
    E2 = n.power(E, 2.0)
    s2 = n.power(s, 2.0)
    tau22 = n.power(tau2, 2.0)

    a1e = -2. - (2.*t)/d - t/tau2

    a2e = t/tau2

    a31e = (2.*(d*(d + m) + s2))/n.power(d,2)
    #a31 = n.power(E,a31e)
    a32 = ss.erf((2.*s2 + d*(m - t))/(sqrt2*d*s)) - \
            ss.erf((2*s2 + d*(d + m - t))/(sqrt2*d*s))

    a33e = 2.*t/d
    #a33 = n.power(E,a33e)
    a34 = (2.*B + C)*E2 - A*E2*ss.erf((m - t)/(sqrt2*s)) +\
            A*ss.erf((d + m - t)/(sqrt2*s)) + (-A + (A + C)*E2)*\
            ss.erf((d + d2 + m - t)/(sqrt2*s))
    #a3 = A*a31*a32 + a33*a34

    a4e = (4.*t*tau22 + d*(s2 + 2.*(d + d2 + m)*tau2))/(2.*d*tau22)
    #a4 = n.power(E,a4e)
    a5 = ss.erfc((s2 + (d + d2 + m - t)*tau2)/(sqrt2*s*tau2))

    #a1a2 = n.power(E,a1e+a2e)
    a1a4 = n.power(E,a4e+a1e)
    a1a2a31 = n.power(E,a1e+a2e+a31e)
    a1a2a33 = n.power(E,a1e+a2e+a33e)
    #res = a1*(a2*a3 +  a4*(-A + (A + C)*E2)*a5)
    #res = a1a2*(A*a31*a32 + a33*a34) + a1a4*(-A + (A + C)*E2)*a5
    #res = A*a1a2*a31*a32 + a1a2*a33*a34 + a1a4*(-A + (A + C)*E2)*a5
    mask = a32==0.0
    a1a2a31[mask]=0
    res = A*a1a2a31*a32 + a1a2a33*a34 + a1a4*(-A + (A + C)*E2)*a5
    res = res/2.
    return res

def ff6(arg, tau2, d, d2, m2, s, A):
    """convolution of gaussian(0,s) with f5 without baseline

    Args:
        arg: time vector
        tau2: decay time of transient decrease
        d: duration of transient increase (exp increase time d/2)
        d2: duration of plateau phase
        #m: start of transient
        m2: start of plateau phase
        s: width of the gaussian
        A: Amplitude of transient

    Returns:
        Function values for all arg values
    """
    #frame = inspect.currentframe()
    #print 'call', inspect.getargvalues(frame)
    m = m2 - d

    t = arg

    #t=t/1000.
    #d=d/1000.
    #d2=d2/1000.
    #m2=m2/1000.
    #s=s/1000.
    #tau2=tau2/1000.
    #m=m/1000.

    E = n.exp(1.0)
    sqrt2 = n.sqrt(2.0)
    E2 = n.power(E, 2.0)
    s2 = n.power(s, 2.0)
    tau22 = n.power(tau2, 2.0)

    a1e = -2. - (2.*t)/d - t/tau2

    a22=ss.erf((2.*s2 + d*(m - t))/(sqrt2*d*s)) - \
            ss.erf((2*s2 + d*(d + m - t))/(sqrt2*d*s))
    a23=- A*E2*ss.erf((m - t)/(sqrt2*s)) +\
            A*ss.erf((d + m - t)/(sqrt2*s)) + (-A + A*E2)*\
            ss.erf((d + d2 + m - t)/(sqrt2*s))

    a3e=(4.*t*tau22 + d*(s2 + 2.*(d + d2 + m)*tau2))/(2.*d*tau22)
    a4 = ss.erfc((s2 + (d + d2 + m - t)*tau2)/(sqrt2*s*tau2))
    a5e = t/tau2
    #a5 = n.power(E,t/tau2)
    a1a3 = n.power(E,a1e+a3e)
    a21e = (2.*(d*(d + m) + s2))/n.power(d,2)
    a1a21a5 = A*n.power(E,a1e+a21e+a5e)
    mask=a22==0.0
    a1a21a5[mask]=0

    a1a2a5 = a1a21a5*a22 +  n.power(E,(2.*t)/d+a1e+a5e)*a23
    res = a1a2a5 +  a1a3*(-A + A *E2)*a4
    res = res / 2.

    if n.any(n.isnan(res)):
        print 'nan'
        print a1a21a5
        print '22',a22,a22.max(),a22.min()

        print a21e
        print d,m,s2
        print d*(d+m),n.power(d,2)
    #    #print t
    #    #print res
    #    #print 'sum',a1e+a3e
    #    #print 'exp',n.power(E,a1e+a3e)
    #    #print 'exp2',a1a3
    #    print "1f",a1a2


        print 'call', tau2, d, d2, m2, s, A,res
    if n.any(n.isinf(res)):
        print 'inf'
        print 'call', tau2, d, d2, m2, s, A,res
    #    print n.any(n.isinf(a1))
    #    print n.any(n.isinf(a2))
    #    print n.any(n.isinf(a3))
    #    print n.any(n.isinf(a4))
    #    print n.any(n.isinf(a5))
    #    print n.any(n.isinf(res))
    #    print n.any(n.isinf(a1*(a5*a2 + a3*(-A + A *E2)*a4)))
    #    print n.any(n.isinf(a3*(-A + A *E2)*a4))
    #    print n.any(n.isinf(a3*a4))
    #    #print a3[-3:-1], a4[-3:-1],a3[0],a4[0]
    #    print (4.*t[-3:-1]*tau22)/(2.*d*tau22) , d*(s2 + 2.*(d + d2 +
    #        m)*tau2)/(2.*d*tau22)
    #    print -2. - (2.*t[-3:-1])/d - t[-3:-1]/tau2
    #    #print t.tolist()
    #    #print res.tolist()
    #    print 'call', tau2, d, d2, m2, s, A, B, C, sum(res)
    return res

def linear(arg, a, b):
    return a*arg + b
