import numpy as n


class ResidualCalculator:

    def __init__(self, X, Y0, limits={}):
        self.limits = {'tau': (0.0, 10), 'a': (.01, 100), 'c': (0.0, 100.)}
        self.limits.update(limits)
        self.tau_min = self.limits['tau'][0]
        self.tau_max = self.limits['tau'][1]
        self.a_min = self.limits['a'][0]
        self.a_max = self.limits['a'][1]
        self.c_min = self.limits['c'][0]
        self.c_max = self.limits['c'][1]
        self.X = n.array(X)
        self.Y0 = n.array(Y0)

    def scaleparam(self, param):
        tau = self.cp(self.tau_min, self.tau_max, param[0])
        a = self.cp(self.a_min, self.a_max, param[1])
        c = self.cp(self.c_min, self.c_max, param[2])
        return tau, a, c

    def func(self, param, showparam=False):
        tau, a, c = self.scaleparam(param)
        if showparam:
            print tau, a, c
        f = a * n.exp(-1. / tau * self.X) + c
        return f

    def residuals(self, param, showparam=False):
        f = self.func(param, showparam)
        return f - self.Y0

    def res_error(self, param):
        res = self.residuals(param, True)
        err = sum(res ** 2) / len(self.Y0)
        return err

    def cp(self, min, max, x):
        # scale x from -oo..+oo to min..max
        return (max - min) * (n.arctan(x) / n.pi + 0.5) + min
