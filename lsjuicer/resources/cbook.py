"""
A collection of utility functions and classes.  Many (but not all)
from the Python Cookbook -- hence the name cbook
"""
import numpy as np
import numpy.ma as ma




def iterable(obj):
    'return true if *obj* is iterable'
    try:
        iter(obj)
    except TypeError:
        return False
    return True


def is_string_like(obj):
    'Return True if *obj* looks like a string'
    if isinstance(obj, (str, unicode)): return True
    # numpy strings are subclass of str, ma strings are not
    if ma.isMaskedArray(obj):
        if obj.ndim == 0 and obj.dtype.kind in 'SU':
            return True
        else:
            return False
    try: obj + ''
    except: return False
    return True

try:
    np.copyto
except AttributeError:
    _putmask = np.putmask
else:
    def _putmask(a, mask, values):
        return np.copyto(a, values, where=mask)
