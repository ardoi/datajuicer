"""
This module provides a large set of colormaps, functions for
registering new colormaps and for getting a colormap by name

"""
import colors
from _cm import datad

cmap_d = dict()

# reverse all the colormaps.
# reversed colormaps have '_r' appended to the name.

def _reverser(f):
    def freversed(x):
        return f(1-x)
    return freversed

def revcmap(data):
    """Can only handle specification *data* in dictionary format."""
    data_r = {}
    for key, val in data.iteritems():
        if callable(val):
            valnew = _reverser(val)
                # This doesn't work: lambda x: val(1-x)
                # The same "val" (the first one) is used
                # each time, so the colors are identical
                # and the result is shades of gray.
        else:
            # Flip x and exchange the y values facing x = 0 and x = 1.
            valnew = [(1.0 - x, y1, y0) for x, y0, y1 in reversed(val)]
        data_r[key] = valnew
    return data_r

def _reverse_cmap_spec(spec):
    """Reverses cmap specification *spec*, can handle both dict and tuple
    type specs."""

    if 'red' in spec:
        return revcmap(spec)
    else:
        revspec = list(reversed(spec))
        if len(revspec[0]) == 2:    # e.g., (1, (1.0, 0.0, 1.0))
            revspec = [(1.0 - a, b) for a, b in revspec]
        return revspec

def _generate_cmap(name, lutsize):
    """Generates the requested cmap from it's name *name*.  The lut size is
    *lutsize*."""

    spec = datad[name]

    # Generate the colormap object.
    if 'red' in spec:
        return colors.LinearSegmentedColormap(name, spec, lutsize)
    else:
        return colors.LinearSegmentedColormap.from_list(spec, spec, lutsize)

LUTSIZE = 256

_cmapnames = datad.keys()  # need this list because datad is changed in loop

# Generate the reversed specifications ...

for cmapname in _cmapnames:
    spec = datad[cmapname]
    spec_reversed = _reverse_cmap_spec(spec)
    datad[cmapname + '_r'] = spec_reversed

# Precache the cmaps with ``lutsize = LUTSIZE`` ...

# Use datad.keys() to also add the reversed ones added in the section above:
for cmapname in datad.keys():
    cmap_d[cmapname] = _generate_cmap(cmapname, LUTSIZE)

locals().update(cmap_d)

def get_cmap(name=None, lut=None):
    """
    Get a colormap instance, defaulting to rc values if *name* is None.

    Colormaps added with :func:`register_cmap` take precedence over
    builtin colormaps.

    If *name* is a :class:`colors.Colormap` instance, it will be
    returned.

    If *lut* is not None it must be an integer giving the number of
    entries desired in the lookup table, and *name* must be a
    standard mpl colormap name with a corresponding data dictionary
    in *datad*.
    """
    if name is None:
        name = mpl.rcParams['image.cmap']

    if isinstance(name, colors.Colormap):
        return name

    if name in cmap_d:
        if lut is None:
            return cmap_d[name]
        elif name in datad:
            return _generate_cmap(name, lut)
        else:
            raise ValueError("Colormap %s is not recognized" % name)

