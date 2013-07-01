"""
A module for converting numbers or color arguments to *RGB* or *RGBA*

*RGB* and *RGBA* are sequences of, respectively, 3 or 4 floats in the
range 0-1.

This module includes functions and classes for color specification
conversions, and for mapping numbers to colors in a 1-D array of
colors called a colormap. Colormapping typically involves two steps:
a data array is first mapped onto the range 0-1 using an instance
of :class:`Normalize` or of a subclass; then this number in the 0-1
range is mapped to a color using an instance of a subclass of
:class:`Colormap`.  Two are provided here:
:class:`LinearSegmentedColormap`, which is used to generate all
the built-in colormap instances, but is also useful for making
custom colormaps, and :class:`ListedColormap`, which is used for
generating a custom colormap from a list of color specifications.

The module also provides a single instance, *colorConverter*, of the
:class:`ColorConverter` class providing methods for converting single
color specifications or sequences of them to *RGB* or *RGBA*.

Commands which take color arguments can use several formats to specify
the colors.  For the basic builtin colors, you can use a single letter

    - b  : blue
    - g  : green
    - r  : red
    - c  : cyan
    - m  : magenta
    - y  : yellow
    - k  : black
    - w  : white

Gray shades can be given as a string encoding a float in the 0-1
range, e.g.::

    color = '0.75'

For a greater range of colors, you have two options.  You can specify
the color using an html hex string, as in::

      color = '#eeefff'

or you can pass an *R* , *G* , *B* tuple, where each of *R* , *G* , *B*
are in the range [0,1].

Finally, legal html names for colors, like 'red', 'burlywood' and
'chartreuse' are supported.
"""
import re
import numpy as np
from numpy import ma
import cbook

parts = np.__version__.split('.')
NP_MAJOR, NP_MINOR = map(int, parts[:2])
# true if clip supports the out kwarg
NP_CLIP_OUT = NP_MAJOR>=1 and NP_MINOR>=2



def rgb2hex(rgb):
    'Given an rgb or rgba sequence of 0-1 floats, return the hex string'
    return '#%02x%02x%02x' % tuple([round(val*255) for val in rgb[:3]])

hexColorPattern = re.compile("\A#[a-fA-F0-9]{6}\Z")

def hex2color(s):
    """
    Take a hex string *s* and return the corresponding rgb 3-tuple
    Example: #efefef -> (0.93725, 0.93725, 0.93725)
    """
    if not isinstance(s, basestring):
        raise TypeError('hex2color requires a string argument')
    if hexColorPattern.match(s) is None:
        raise ValueError('invalid hex color string "%s"' % s)
    return tuple([int(n, 16)/255.0 for n in (s[1:3], s[3:5], s[5:7])])

class ColorConverter:
    """
    Provides methods for converting color specifications to *RGB* or *RGBA*

    Caching is used for more efficient conversion upon repeated calls
    with the same argument.

    Ordinarily only the single instance instantiated in this module,
    *colorConverter*, is needed.
    """
    colors = {
        'b' : (0.0, 0.0, 1.0),
        'g' : (0.0, 0.5, 0.0),
        'r' : (1.0, 0.0, 0.0),
        'c' : (0.0, 0.75, 0.75),
        'm' : (0.75, 0, 0.75),
        'y' : (0.75, 0.75, 0),
        'k' : (0.0, 0.0, 0.0),
        'w' : (1.0, 1.0, 1.0),
        }

    cache = {}
    def to_rgb(self, arg):
        """
        Returns an *RGB* tuple of three floats from 0-1.

        *arg* can be an *RGB* or *RGBA* sequence or a string in any of
        several forms:

            1) a letter from the set 'rgbcmykw'
            2) a hex color string, like '#00FFFF'
            3) a standard name, like 'aqua'
            4) a float, like '0.4', indicating gray on a 0-1 scale

        if *arg* is *RGBA*, the *A* will simply be discarded.
        """
        try: return self.cache[arg]
        except KeyError: pass
        except TypeError: # could be unhashable rgb seq
            arg = tuple(arg)
            try: return self.cache[arg]
            except KeyError: pass
            except TypeError:
                raise ValueError(
                      'to_rgb: arg "%s" is unhashable even inside a tuple'
                                    % (str(arg),))

        try:
            if cbook.is_string_like(arg):
                argl = arg.lower()
                color = self.colors.get(argl, None)
                if color is None:
                    str1 = cnames.get(argl, argl)
                    if str1.startswith('#'):
                        color = hex2color(str1)
                    else:
                        fl = float(argl)
                        if fl < 0 or fl > 1:
                            raise ValueError(
                                   'gray (string) must be in range 0-1')
                        color = tuple([fl]*3)
            elif cbook.iterable(arg):
                if len(arg) > 4 or len(arg) < 3:
                    raise ValueError(
                           'sequence length is %d; must be 3 or 4'%len(arg))
                color = tuple(arg[:3])
                if [x for x in color if (float(x) < 0) or  (x > 1)]:
                    # This will raise TypeError if x is not a number.
                    raise ValueError('number in rbg sequence outside 0-1 range')
            else:
                raise ValueError('cannot convert argument to rgb sequence')

            self.cache[arg] = color

        except (KeyError, ValueError, TypeError), exc:
            raise ValueError('to_rgb: Invalid rgb arg "%s"\n%s' % (str(arg), exc))
            # Error messages could be improved by handling TypeError
            # separately; but this should be rare and not too hard
            # for the user to figure out as-is.
        return color

    def to_rgba(self, arg, alpha=None):
        """
        Returns an *RGBA* tuple of four floats from 0-1.

        For acceptable values of *arg*, see :meth:`to_rgb`.
        In addition, if *arg* is "none" (case-insensitive),
        then (0,0,0,0) will be returned.
        If *arg* is an *RGBA* sequence and *alpha* is not *None*,
        *alpha* will replace the original *A*.
        """
        try:
            if arg.lower() == 'none':
                return (0.0, 0.0, 0.0, 0.0)
        except AttributeError:
            pass

        try:
            if not cbook.is_string_like(arg) and cbook.iterable(arg):
                if len(arg) == 4:
                    if [x for x in arg if (float(x) < 0) or  (x > 1)]:
                        # This will raise TypeError if x is not a number.
                        raise ValueError('number in rbga sequence outside 0-1 range')
                    if alpha is None:
                        return tuple(arg)
                    if alpha < 0.0 or alpha > 1.0:
                        raise ValueError("alpha must be in range 0-1")
                    return arg[0], arg[1], arg[2], alpha
                r,g,b = arg[:3]
                if [x for x in (r,g,b) if (float(x) < 0) or  (x > 1)]:
                    raise ValueError('number in rbg sequence outside 0-1 range')
            else:
                r,g,b = self.to_rgb(arg)
            if alpha is None:
                alpha = 1.0
            return r,g,b,alpha
        except (TypeError, ValueError), exc:
            raise ValueError('to_rgba: Invalid rgba arg "%s"\n%s' % (str(arg), exc))

    def to_rgba_array(self, c, alpha=None):
        """
        Returns a numpy array of *RGBA* tuples.

        Accepts a single mpl color spec or a sequence of specs.

        Special case to handle "no color": if *c* is "none" (case-insensitive),
        then an empty array will be returned.  Same for an empty list.
        """
        try:
            nc = len(c)
        except TypeError:
            raise ValueError(
                "Cannot convert argument type %s to rgba array" % type(c))
        try:
            if nc == 0 or c.lower() == 'none':
                return np.zeros((0,4), dtype=np.float)
        except AttributeError:
            pass
        try:
            # Single value? Put it in an array with a single row.
            return np.array([self.to_rgba(c, alpha)], dtype=np.float)
        except ValueError:
            if isinstance(c, np.ndarray):
                if c.ndim != 2 and c.dtype.kind not in 'SU':
                    raise ValueError("Color array must be two-dimensional")
                if (c.ndim == 2 and c.shape[1] == 4 and c.dtype.kind == 'f'):
                    if (c.ravel() > 1).any() or (c.ravel() < 0).any():
                        raise ValueError(
                            "number in rgba sequence is outside 0-1 range")
                    result = np.asarray(c, np.float)
                    if alpha is not None:
                        if alpha > 1 or alpha < 0:
                            raise ValueError("alpha must be in 0-1 range")
                        result[:,3] = alpha
                    return result
                    # This alpha operation above is new, and depends
                    # on higher levels to refrain from setting alpha
                    # to values other than None unless there is
                    # intent to override any existing alpha values.

            # It must be some other sequence of color specs.
            result = np.zeros((nc, 4), dtype=np.float)
            for i, cc in enumerate(c):
                result[i] = self.to_rgba(cc, alpha)
            return result

colorConverter = ColorConverter()

def makeMappingArray(N, data, gamma=1.0):
    """Create an *N* -element 1-d lookup table

    *data* represented by a list of x,y0,y1 mapping correspondences.
    Each element in this list represents how a value between 0 and 1
    (inclusive) represented by x is mapped to a corresponding value
    between 0 and 1 (inclusive). The two values of y are to allow
    for discontinuous mapping functions (say as might be found in a
    sawtooth) where y0 represents the value of y for values of x
    <= to that given, and y1 is the value to be used for x > than
    that given). The list must start with x=0, end with x=1, and
    all values of x must be in increasing order. Values between
    the given mapping points are determined by simple linear interpolation.

    Alternatively, data can be a function mapping values between 0 - 1
    to 0 - 1.

    The function returns an array "result" where ``result[x*(N-1)]``
    gives the closest value for values of x between 0 and 1.
    """

    if callable(data):
        xind = np.linspace(0, 1, N)**gamma
        lut = np.clip(np.array(data(xind), dtype=np.float), 0, 1)
        return lut

    try:
        adata = np.array(data)
    except:
        raise TypeError("data must be convertable to an array")
    shape = adata.shape
    if len(shape) != 2 and shape[1] != 3:
        raise ValueError("data must be nx3 format")

    x  = adata[:,0]
    y0 = adata[:,1]
    y1 = adata[:,2]

    if x[0] != 0. or x[-1] != 1.0:
        raise ValueError(
           "data mapping points must start with x=0. and end with x=1")
    if np.sometrue(np.sort(x)-x):
        raise ValueError(
           "data mapping points must have x in increasing order")
    # begin generation of lookup table
    x = x * (N-1)
    lut = np.zeros((N,), np.float)
    xind = (N - 1) * np.linspace(0, 1, N)**gamma
    ind = np.searchsorted(x, xind)[1:-1]

    lut[1:-1] = ( ((xind[1:-1] - x[ind-1]) / (x[ind] - x[ind-1]))
                  * (y0[ind] - y1[ind-1]) + y1[ind-1])
    lut[0] = y1[0]
    lut[-1] = y0[-1]
    # ensure that the lut is confined to values between 0 and 1 by clipping it
    np.clip(lut, 0.0, 1.0)
    #lut = where(lut > 1., 1., lut)
    #lut = where(lut < 0., 0., lut)
    return lut


class Colormap:
    """Base class for all scalar to rgb mappings

        Important methods:

            * :meth:`set_bad`
            * :meth:`set_under`
            * :meth:`set_over`
    """
    def __init__(self, name, N=256):
        """
        Public class attributes:
            :attr:`N` : number of rgb quantization levels
            :attr:`name` : name of colormap

        """
        self.name = name
        self.N = N
        self._rgba_bad = (0.0, 0.0, 0.0, 0.0) # If bad, don't paint anything.
        self._rgba_under = None
        self._rgba_over = None
        self._i_under = N
        self._i_over = N+1
        self._i_bad = N+2
        self._isinit = False


    def __call__(self, X, alpha=None, bytes=False):
        """
        *X* is either a scalar or an array (of any dimension).
        If scalar, a tuple of rgba values is returned, otherwise
        an array with the new shape = oldshape+(4,). If the X-values
        are integers, then they are used as indices into the array.
        If they are floating point, then they must be in the
        interval (0.0, 1.0).
        Alpha must be a scalar between 0 and 1, or None.
        If bytes is False, the rgba values will be floats on a
        0-1 scale; if True, they will be uint8, 0-255.
        """

        if not self._isinit: self._init()
        mask_bad = None
        if not cbook.iterable(X):
            vtype = 'scalar'
            xa = np.array([X])
        else:
            vtype = 'array'
            xma = ma.array(X, copy=False)
            mask_bad = xma.mask
            xa = xma.data.copy()   # Copy here to avoid side effects.
            del xma
            # masked values are substituted below; no need to fill them here

        if xa.dtype.char in np.typecodes['Float']:
            # Treat 1.0 as slightly less than 1.
            cbook._putmask(xa, xa==1.0, np.nextafter(xa.dtype.type(1),
                                                     xa.dtype.type(0)))
            # The following clip is fast, and prevents possible
            # conversion of large positive values to negative integers.

            xa *= self.N
            if NP_CLIP_OUT:
                np.clip(xa, -1, self.N, out=xa)
            else:
                xa = np.clip(xa, -1, self.N)

            # ensure that all 'under' values will still have negative
            # value after casting to int
            cbook._putmask(xa, xa<0.0, -1)
            xa = xa.astype(int)
        # Set the over-range indices before the under-range;
        # otherwise the under-range values get converted to over-range.
        cbook._putmask(xa, xa>self.N-1, self._i_over)
        cbook._putmask(xa, xa<0, self._i_under)
        if mask_bad is not None:
            if mask_bad.shape == xa.shape:
                cbook._putmask(xa, mask_bad, self._i_bad)
            elif mask_bad:
                xa.fill(self._i_bad)
        if bytes:
            lut = (self._lut * 255).astype(np.uint8)
        else:
            lut = self._lut.copy() # Don't let alpha modify original _lut.

        if alpha is not None:
            alpha = min(alpha, 1.0) # alpha must be between 0 and 1
            alpha = max(alpha, 0.0)
            if bytes:
                alpha = int(alpha * 255)
            if (lut[-1] == 0).all():
                lut[:-1, -1] = alpha
                # All zeros is taken as a flag for the default bad
                # color, which is no color--fully transparent.  We
                # don't want to override this.
            else:
                lut[:,-1] = alpha
                # If the bad value is set to have a color, then we
                # override its alpha just as for any other value.

        rgba = np.empty(shape=xa.shape+(4,), dtype=lut.dtype)
        lut.take(xa, axis=0, mode='clip', out=rgba)
                    #  twice as fast as lut[xa];
                    #  using the clip or wrap mode and providing an
                    #  output array speeds it up a little more.
        if vtype == 'scalar':
            rgba = tuple(rgba[0,:])
        return rgba

    def set_bad(self, color = 'k', alpha = None):
        '''Set color to be used for masked values.
        '''
        self._rgba_bad = colorConverter.to_rgba(color, alpha)
        if self._isinit: self._set_extremes()

    def set_under(self, color = 'k', alpha = None):
        '''Set color to be used for low out-of-range values.
           Requires norm.clip = False
        '''
        self._rgba_under = colorConverter.to_rgba(color, alpha)
        if self._isinit: self._set_extremes()

    def set_over(self, color = 'k', alpha = None):
        '''Set color to be used for high out-of-range values.
           Requires norm.clip = False
        '''
        self._rgba_over = colorConverter.to_rgba(color, alpha)
        if self._isinit: self._set_extremes()

    def _set_extremes(self):
        if self._rgba_under:
            self._lut[self._i_under] = self._rgba_under
        else:
            self._lut[self._i_under] = self._lut[0]
        if self._rgba_over:
            self._lut[self._i_over] = self._rgba_over
        else:
            self._lut[self._i_over] = self._lut[self.N-1]
        self._lut[self._i_bad] = self._rgba_bad

    def _init():
        '''Generate the lookup table, self._lut'''
        raise NotImplementedError("Abstract class only")

    def is_gray(self):
        if not self._isinit: self._init()
        return (np.alltrue(self._lut[:,0] == self._lut[:,1])
                    and np.alltrue(self._lut[:,0] == self._lut[:,2]))


class LinearSegmentedColormap(Colormap):
    """Colormap objects based on lookup tables using linear segments.

    The lookup table is generated using linear interpolation for each
    primary color, with the 0-1 domain divided into any number of
    segments.
    """
    def __init__(self, name, segmentdata, N=256, gamma=1.0):
        """Create color map from linear mapping segments

        segmentdata argument is a dictionary with a red, green and blue
        entries. Each entry should be a list of *x*, *y0*, *y1* tuples,
        forming rows in a table.

        Example: suppose you want red to increase from 0 to 1 over
        the bottom half, green to do the same over the middle half,
        and blue over the top half.  Then you would use::

            cdict = {'red':   [(0.0,  0.0, 0.0),
                               (0.5,  1.0, 1.0),
                               (1.0,  1.0, 1.0)],

                     'green': [(0.0,  0.0, 0.0),
                               (0.25, 0.0, 0.0),
                               (0.75, 1.0, 1.0),
                               (1.0,  1.0, 1.0)],

                     'blue':  [(0.0,  0.0, 0.0),
                               (0.5,  0.0, 0.0),
                               (1.0,  1.0, 1.0)]}

        Each row in the table for a given color is a sequence of
        *x*, *y0*, *y1* tuples.  In each sequence, *x* must increase
        monotonically from 0 to 1.  For any input value *z* falling
        between *x[i]* and *x[i+1]*, the output value of a given color
        will be linearly interpolated between *y1[i]* and *y0[i+1]*::

            row i:   x  y0  y1
                           /
                          /
            row i+1: x  y0  y1

        Hence y0 in the first row and y1 in the last row are never used.


        .. seealso::

            :meth:`LinearSegmentedColormap.from_list`
               Static method; factory function for generating a
               smoothly-varying LinearSegmentedColormap.

            :func:`makeMappingArray`
               For information about making a mapping array.
        """
        self.monochrome = False  # True only if all colors in map are identical;
                                 # needed for contouring.
        Colormap.__init__(self, name, N)
        self._segmentdata = segmentdata
        self._gamma = gamma

    def _init(self):
        self._lut = np.ones((self.N + 3, 4), np.float)
        self._lut[:-3, 0] = makeMappingArray(self.N,
                self._segmentdata['red'], self._gamma)
        self._lut[:-3, 1] = makeMappingArray(self.N,
                self._segmentdata['green'], self._gamma)
        self._lut[:-3, 2] = makeMappingArray(self.N,
                self._segmentdata['blue'], self._gamma)
        self._isinit = True
        self._set_extremes()

    def set_gamma(self, gamma):
        """
        Set a new gamma value and regenerate color map.
        """
        self._gamma = gamma
        self._init()

    @staticmethod
    def from_list(name, colors, N=256, gamma=1.0):
        """
        Make a linear segmented colormap with *name* from a sequence
        of *colors* which evenly transitions from colors[0] at val=0
        to colors[-1] at val=1.  *N* is the number of rgb quantization
        levels.
        Alternatively, a list of (value, color) tuples can be given
        to divide the range unevenly.
        """

        if not cbook.iterable(colors):
            raise ValueError('colors must be iterable')

        if cbook.iterable(colors[0]) and len(colors[0]) == 2 and \
                not cbook.is_string_like(colors[0]):
            # List of value, color pairs
            vals, colors = zip(*colors)
        else:
            vals = np.linspace(0., 1., len(colors))

        cdict = dict(red=[], green=[], blue=[])
        for val, color in zip(vals, colors):
            r,g,b = colorConverter.to_rgb(color)
            cdict['red'].append((val, r, r))
            cdict['green'].append((val, g, g))
            cdict['blue'].append((val, b, b))

        return LinearSegmentedColormap(name, cdict, N, gamma)

