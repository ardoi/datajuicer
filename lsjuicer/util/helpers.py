import time

from PyQt5 import QtGui as QG

from PyQt5 import QtCore as QC


import numpy
from scipy.signal import convolve2d
import scipy.ndimage as sn

from lsjuicer.resources import cm
# from skimage.morphology import watershed


def round_point(point):
    point.setX(int(round(point.x())))
    point.setY(int(round(point.y())))

def floor_point_x(point):
    print 'floor', point
    point.setX(int(point.x()))
    point.setY(int(round(point.y())))
    print 'floored', point

def floor_rect_x(rect):
    tl = rect.topLeft()
    br = rect.bottomRight()
    floor_point_x(tl)
    floor_point_x(br)
    rect.setTopLeft(tl)
    rect.setBottomRight(br)

class shiftList:

    """Helper class for data that is shifted by some amount. For example
    flourescence data is taken to start at pixel 0 even though the actual data
    can be at any arbitrary pixel value of the image. Therefore it is necessary
    to shift the data and this class helps to do this automatically"""

    def __init__(self, data, shift):
        self.data = data
        self.shift = shift

    def __getitem__(self, ind):
        if isinstance(ind, int):
            return self.data[ind-self.shift]
        elif isinstance(ind, slice):
            if not isinstance(ind.start, int):
                raise ValueError
            return self.data.__getslice__(ind.start - self.shift,
                                          ind.stop - self.shift)

    def __len__(self):
        return len(self.data)

    def tolist(self):
        if isinstance(self.data, list):
            return self.data
        else:
            return self.data.tolist()


def find_p(x, p):
    x0 = x[0] - 1
    for i, el in enumerate(x):
        if el - 1 < p*x0:
            return i
    return -1


def remove_bad_gaps(timestamps, gaps, mean_gap_value, min_gap_value=0.5):
    """Remove gaps from timestamps that are less than min_gap_value.
    This is needed in some cases where LSM files have weird gaps in them,
    which makes analysis problematic

    :param timestamps: Timestamps to change.
    :type timestamps: list.
    :param gaps: Dictionary with gap locations as keys and gaps as values
    :type gaps: dict.
    :param mean_gap_value: value to replace bad gaps with
    :type mean_gap_value: float
    :returns: list of corrected timestamps
    """
    zerovalue = timestamps[0]
    diffs = numpy.diff(timestamps)
    remove_keys = []
    # print 'keys before' , gaps
    for location in gaps:
        if gaps[location] < min_gap_value:
            diffs[location] = mean_gap_value
            remove_keys.append(location)
    for bad_key in remove_keys:
        del gaps[bad_key]
    # print 'keys after' , remove_keys
    # print 'keys after' , gaps
    corrected_timestamps = diffs.cumsum() + zerovalue
    return (corrected_timestamps, gaps, len(remove_keys))


def find_outliers(data, spread=2.):
    if isinstance(data, list):
        d = data[:]
    else:
        d = data.tolist()
    finding = True
    found = {}
    data_array = numpy.array(d)
    mean = data_array.mean()
    while finding:
        finding = False
        data_array = numpy.array(d)
        mean = data_array.mean()
        std = data_array.std()
        print mean/std, mean, std, data_array.max()
        if mean > std:
            break
        else:
            for i, item in enumerate(data_array):
                if abs(item - mean) > spread*std:
                    finding = True
                    d.remove(item)
                    found[i] = item
        print data_array.max()
    return (found, mean)


def timeIt(f):
    timeIt.active = 0

    def tt(*args, **kwargs):
        timeIt.active += 1
        t0 = time.time()
        print '\n>>>%s Executing %s' % ('\t'*(timeIt.active-1)+'#', f.__name__)
        res = f(*args, **kwargs)
        print '>>>%s Function %s execution time: %.3f seconds\n' %\
            ('\t'*(timeIt.active-1)+'#', f.__name__, time.time()-t0)
        timeIt.active -= 1
        return res
    return tt

def log(f):
   def out(*args, **kwargs):
       print 'starting',f
       f(*args, **kwargs)
       print 'ending',f
       return
   return out

def list_2_str(list, prec=6):
    out = ''
    if isinstance(list[0], float):
        frmt = "%."+str(prec)+"f"
        list = [frmt % el for el in list]
    for x in list:
        out += str(x)
        out += ', '
    return out[:-2]


def gauss_kern(size, sizey=None):
    size = int(size)
    if not sizey:
        sizey = size
    else:
        sizey = int(sizey)
    x, y = numpy.mgrid[-size:size+1, -sizey:sizey+1]
    g = numpy.exp(-(x**2/float(size)+y**2/float(sizey)))
    return g / g.sum()


def flat_kern(size, sizey=None):
    size = int(size)
    if not sizey:
        sizey = size
    else:
        sizey = int(sizey)
    # x, y = numpy.mgrid[-size:size+1, -sizey:sizey+1]
    # g = numpy.exp(-(x**2/float(size)+y**2/float(sizey)))
    g = numpy.ones((size*2+1, sizey*2+1))
    return g / g.sum()


@timeIt
def blur_image(im, n, ny=None, kernel='gauss'):
#    g = numpy.array([[1,1,1],[1,1,1],[1,1,1]])
    if kernel == 'gauss':
        g = gauss_kern(n, sizey=ny)
    else:
        g = flat_kern(n, sizey=ny)
    improc = convolve2d(im, g, mode='same')
    # improc = numpy.abs(ss.ifft2(ss.fft2(g)*numpy.conj(ss.fft2(im))))
    return(improc)


def self_ratio(d, start, lines):
    array_for_mean = d[:, start:start+lines]
    means = array_for_mean.mean(axis=1)
    means_array = numpy.column_stack((means,)*d.shape[1])
    q = d/means_array
    return q


def smooth(x, window_len=10, window='blackman'):

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")

    if window_len < 3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Wrong window type %s" % window)

    s = numpy.r_[2*x[0]-x[window_len:1:-1], x, 2*x[-1]-x[-1:-window_len:-1]]
    if window == 'flat':  # moving average
        w = numpy.ones(window_len, 'd')
    else:
        w = eval('numpy.'+window+'(window_len)')
    y = numpy.convolve(w/w.sum(), s, mode='same')
    return y[window_len-1:-window_len+1]


def smooth_times(data, times=1, wl=[10], win='blackman'):
    smoothed = numpy.copy(data)
    if len(wl) < times:
        wl = wl * times
    for i in range(times):
        smoothed = smooth(smoothed, window_len=wl[i], window=win)
    return smoothed


def make_pixmap(data, blur, saturate, colormap):
        """Make pixmap with saved visualization properties"""
        dd = data

        if blur:
            dd = blur_image(dd, blur)

        # normalize data to range 0..255
        # make contrast better
        dd = (dd - dd.min())/(1.0*(dd.max()-dd.min()))
        dd = dd.clip(0.0, saturate)
        dd /= saturate
        # apply colormap
        cmap = cm.get_cmap(colormap)
        d2 = cmap.__call__(dd, bytes=True)
        d2.shape = (dd.size, 4)
        # swap columns
        d2[:, numpy.array([0, 2])] = d2[:, numpy.array([2, 0])]
        im_data = d2.tostring()
        y_points = dd.shape[0]
        x_points = dd.shape[1]
        im = QG.QImage(im_data, x_points,
                       y_points, QG.QImage.Format_ARGB32)
        pixmap = QG.QPixmap.fromImage(im)
        return pixmap

# sparkfinder
# def doit(data):
#    figure()
#    imshow(data)
#    sd = data.std()
#    mean = data.mean()
#    c1 = sd*1.5 + mean
#    print c1, data.min(), data.max()
#    mask = where(data > c1, 1, 0)
# mask = h.blur_image(mask,2)
#    print mask.min(), mask.max()
#    figure()
#    imshow(mask, interpolation='nearest')
#    print c1, mean, sd
#
#    im1 = data*(1-mask)
#    figure()
#    imshow(im1)
#    im1f = im1.flatten()
#    nonzero_indices = (im1f>0).nonzero()
#    nonzero_elements = n.take(im1f, nonzero_indices)
# nonzero_elements = im1
#    sd1 = nonzero_elements.std()
#    mean1 = nonzero_elements.mean()
#    c2= sd1*2 + mean1
#    print c2,mean1,sd1
#    mask = where(data > c2, 1, 0)
#    figure()
#    imshow(mask, interpolation='nearest')
#
#    im2 = data*(1-mask)
#    im2f = im2.flatten()
#    nonzero_indices = (im2f>0).nonzero()
#    nonzero_elements = n.take(im2f, nonzero_indices)
# nonzero_elements = im2
#    sd2 = nonzero_elements.std()
#    mean2 = nonzero_elements.mean()
#    c3= sd2*3.8 + mean2
#    print c3
#    mask = where(data > c3, 1, 0)
#    figure()
#    imshow(mask, interpolation='nearest')
#    return mask


#def make_box(l, r, t, b):
#    plot([l, l], [b, t], lw=2, color='black')
#    plot([r, r], [b, t], lw=2, color='black')
#    plot([l, r], [b, b], lw=2, color='black')
#    plot([l, r], [t, t], lw=2, color='black')


#def show_sparks(spark_coords, data):
#    figure()
#    imshow(data)
#    for spark in spark_coords:
#        l = spark_coords[spark]['left']
#        r = spark_coords[spark]['right']
#        t = spark_coords[spark]['top']+1
#        b = spark_coords[spark]['bottom']
#        make_box(l, r, t, b)
#    t_plots = {}
#    s_plots = {}
#    for spark in spark_coords:
#        l = spark_coords[spark]['left']
#        r = spark_coords[spark]['right']
#        t = spark_coords[spark]['top']+1
#        b = spark_coords[spark]['bottom']
#        sdata = data[b:t, l:r]
#        figure()
#        imshow(sdata, interpolation='nearest')
#        t_plots[spark] = sdata.mean(axis=1)
#        s_plots[spark] = sdata.mean(axis=0)
#    figure()
#    for spark in t_plots:
#        plot(t_plots[spark], label=str(spark))
#    legend()
#    figure()
#    for spark in s_plots:
#        plot(s_plots[spark], label=str(spark))
#    legend()
#

#def find_sparks(sd3data, sd2data):
#    # first find peaks from
#    peaks, s = counter(sd3data)
#    # with one point from each peak area check if the underlying 2SD area is connected
#    # make the list of test points
#    coords = {'x': [], 'y': []}
#    for key in peaks:
#        loc = peaks[key][0]
#        coords['x'].append(loc[0])
#        coords['y'].append(loc[1])
#    areas, sparks = counter(sd2data, coords)
#    return sparks


def counter(data, coords=None):
    width = data.shape[1]
    height = data.shape[0]
    areas = {}
    count = 0
    if coords:
        xcoords = coords['x']
        ycoords = coords['y']
    else:
        xcoords = range(width)
        ycoords = range(height)

    for i in xcoords:
        for j in ycoords:
            if data[j, i] == 1:
                coordinates = []
                filler(data, i, j, coordinates)
                areas[count] = coordinates
                count += 1
                # figure()
                # imshow(data.copy())
    print '%i areas found' % count
    print "i\tarea\tleft\tright\ttop\tbottom"
    print '='*50
    spark_bounds = {}
    for key in areas:
        xs = []
        ys = []
        for c in areas[key]:
            xs.append(c[0])
            ys.append(c[1])
        spark_bounds[key] = {'left': min(xs), 'right': max(
            xs), 'top': max(ys), 'bottom': min(ys)}
        print "%i\t%i\t%i\t%i\t%i\t%i" % (key, len(areas[key]), min(xs), max(xs), min(ys), max(ys))
    print '='*50
    print '\n'
    return areas, spark_bounds


def filler(data, x, y, coordinates):
    width = data.shape[1]
    height = data.shape[0]
    if data[y, x] == 0:
        return
    else:
        data[y, x] = 0
        coordinates.append((x, y))
    if x > 0:
        filler(data, x-1, y, coordinates)
    if x < width-1:
        filler(data, x+1, y, coordinates)
    if y > 0:
        filler(data, x, y-1, coordinates)
    if y < height-1:
        filler(data, x, y+1, coordinates)


# sparkbf=h.blur_image(sparks,3,kernel='flat')
def doit(data):
    # figure()
    # imshow(data)
    sd = data.std()
    mean = data.mean()
    c1 = sd*1.5 + mean
    print c1, data.min(), data.max()
    mask = numpy.where(data > c1, 1, 0)
    # mask = h.blur_image(mask,2)
    print mask.min(), mask.max()
    # figure()
    # imshow(mask, interpolation='nearest')
    print c1, mean, sd

    im1 = data*(1-mask)
    # figure()
    # imshow(im1)
    im1f = im1.flatten()
    nonzero_indices = (im1f > 0).nonzero()
    nonzero_elements = numpy.take(im1f, nonzero_indices)
    # nonzero_elements = im1
    sd1 = nonzero_elements.std()
    mean1 = nonzero_elements.mean()
    c2 = sd1*2 + mean1
    print c2, mean1, sd1
    mask = numpy.where(data > c2, 1, 0)
    # figure()
    # imshow(mask, interpolation='nearest')

    im2 = data*(1-mask)
    im2f = im2.flatten()
    nonzero_indices = (im2f > 0).nonzero()
    nonzero_elements = numpy.take(im2f, nonzero_indices)
    # nonzero_elements = im2
    sd2 = nonzero_elements.std()
    mean2 = nonzero_elements.mean()
    c3 = sd2*3.8 + mean2
    print c3
    maskc = numpy.where(data > c3, 1, 0)
    # figure()
    # imshow(mask, interpolation='nearest')
    return mask, maskc


def rect_from_list(plist):
    l1 = plist
    r = QC.QRectF(l1[0], l1[2], l1[1]-l1[0], -(l1[2]-l1[3]))
    return r


def point_dict(rect):
    d = {'tl': rect.topLeft(), 'bl': rect.bottomLeft(),
         'tr': rect.topRight(), 'br': rect.bottomRight()}
    return d


#def plot_rect(r, color='black'):
#    if isinstance(r, list):
#        rect = rect_from_list(r)
#    elif isinstance(r, QC.QRectF):
#        rect = r
#    lines_x = []
#    lines_y = []
#    lines_x.append([rect.left()]*2)
#    lines_y.append([rect.bottom(), rect.top()])
#    lines_x.append([rect.right()]*2)
#    lines_y.append([rect.bottom(), rect.top()])
#    lines_x.append([rect.left(), rect.right()])
#    lines_y.append([rect.top()]*2)
#    lines_x.append([rect.left(), rect.right()])
#    lines_y.append([rect.bottom()]*2)
#    for lx, ly in zip(lines_x, lines_y):
#        # print lx,ly
#        plot(lx, ly, color=color)

# class Rect:
#    def __init__(self,l,r,t,b):
#        self.l=r
#        self.r=r
#        self.t=t
#        self.b=b
#    def intersects(self, b):
#        if self.r > b.l


def rect_from_dict(dict_in):
    print 'q'
    return QC.QRectF(dict_in['tl'].x(), dict_in['tl'].y(),
                     abs(dict_in['br'].x() - dict_in['bl'].x()),
                     abs(dict_in['tr'].y()-dict_in['br'].y()))


#def reduce_rect(a, b):
#    # a is the rect to reduce
#    # b is the one that should not be cut by a
#    rect_l1 = rect_from_list(a)
#    rect_ml2 = rect_from_list(b)
#    print rect_l1
#    print rect_ml2
#    intersected = False
#    if rect_l1.intersects(rect_ml2):
#        intersected = True
#        intersection = rect_l1.intersected(rect_ml2)
#        # intersection.setBottom(intersection.top() - intersection.height())
#        l1_points = point_dict(rect_l1)
#        contained = []
#        print l1_points
#        for point_name in l1_points:
#            point = l1_points[point_name]
#            if intersection.contains(point):
#                contained.append(point_name)
#
#        print contained, intersection
#        if len(contained) == 1:
#            # print 'simple intersection'
#            c1name = contained[0]
#            if c1name == 'bl':
#                rect_l1.setBottomLeft(intersection.topRight())
#            elif c1name == 'br':
#                rect_l1.setBottomRight(intersection.topLeft())
#            elif c1name == 'tr':
#                rect_l1.setTopRight(intersection.bottomLeft())
#            elif c1name == 'tl':
#                rect_l1.setTopLeft(intersection.bottomRight())
#
#        elif len(contained) in [0, 2]:
#            print 'contains 0 or 2'
#            pass
#            if rect_l1.left() == intersection.left():
#                rect_l1.setLeft(intersection.right())
#            elif rect_l1.right() == intersection.right():
#                rect_l1.setRight(intersection.left())
#            elif rect_l1.top() == intersection.top():
#                rect_l1.setTop(intersection.bottom())
#            elif rect_l1.bottom() == intersection.bottom():
#                rect_l1.setBottom(intersection.top())
#
#        else:
#            print 'impossible'
#            print contained
#            assert 1 == 0
#    if intersected:
#        print 'i', intersection
#        return (intersected,
#                [rect_l1.left(), rect_l1.right(),
#                 rect_l1.top(), rect_l1.bottom()],
#                [intersection.left(), intersection.right(
#                ), intersection.top(), intersection.bottom()]
#                )
#    else:
#        return (intersected,
#                [rect_l1.left(), rect_l1.right(), rect_l1.top(), rect_l1.bottom()], 0)
def ipython_shell():
    from IPython.frontend.terminal.embed import InteractiveShellEmbed
    #from IPython import embed_kernel
    QC.pyqtRemoveInputHook()
    ipshell=InteractiveShellEmbed()
    ipshell()

@timeIt
def evolve_in_bits(qin, a, b, times=1):
    new = numpy.zeros_like(qin)
    # the x direction of the struc is stretched out more so that the right
    # hand side would be longer. This is because a spark decays slower than it
    # initiates. Therefore we need to use more data after the peak to fit the
    # relaxation properly
    struc = numpy.zeros((2*a+1, 4*b+1))
    struc[a, :] = 1
    struc[:, b] = 1
    # since the struc is asymmetric the origin for dilation needs to be shifted -b units in x direction
    # dilated is the mask within which the spark can grow in
    dilated = sn.binary_dilation(
        qin > 0, structure=struc, iterations=5, origin=(0, -b))
    ec = sn.distance_transform_edt(dilated)
    ll = sn.label(qin)[0]
    # TODO fix missing watershed
    # qq = watershed(-ec, ll, mask = ec.astype(bool))
    objects = sn.find_objects(qq)
    for i, o in enumerate(objects):
        new[o] = i+1
    return new
    # dilated_labels,dn = sn.label(dilated)
    objects = sn.find_objects(dilated_labels)
    skiplist = []
    for i in range(times):
        for o in objects:
            if o not in skiplist:
                ims = qin[o]
                u = numpy.unique(ims).tolist()
                print u, o
                if 0 in u:
                    u.remove(0)
                if len(u) == 1:
                    new[o] = u[0]
                    skiplist.append(o)
                else:
                    new[o] = evolve(ims)
        qin = new
    return new, objects


def evolve(qin):
    new = numpy.zeros_like(qin)
    labels = numpy.unique(qin).tolist()
    if 0 in labels:
        labels.remove(0)
    for i in range(1, qin.shape[0]):
        for j in range(1, qin.shape[1]):
            near = qin[i-1:i+2, j-1:j+2]
            max_c = 0
            new_label = 0
            for l in labels:
                count = (near == l).sum()
                if count > max_c:
                    new_label = l
                    max_c = count
                elif count == max_c:
                    new_label = 0
                    max_c = count
            if new_label:
                new[i, j] = new_label
            else:
                continue
    return new


def masked_mean(data, mask, axis=None, give_slice=True):
    mask = mask.astype(bool).astype(float)
    data = data*mask
    D = data.sum(axis=axis)
    M = mask.sum(axis=axis)
    # M=numpy.where(M > 0, M, 1)
    # D = numpy.where(D > 0, D, -1)
    # find biggest contigous block in M
    labels, nn = sn.label(M)
    objects = sn.find_objects(labels)
    object_sizes = sn.sum(M > 0, labels=labels, index=range(1, nn+1))
    try:
        max_label_no = object_sizes.argmax()
    except ValueError:
        print objects, object_sizes
        print mask
        print data
        raise ValueError
    valid_slice = objects[max_label_no]
    # print 'masked mean:',objects, object_sizes,max_label_no,valid_slice
    if give_slice:
        return D[valid_slice] / M[valid_slice], valid_slice
    else:
        return D[valid_slice] / M[valid_slice]


def make_mask_pixmap(twodmask, color):
    qcolor = QG.QColor(color)
    r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
    y_points, x_points = twodmask.shape
    onedmask = twodmask.flatten()
    res = numpy.zeros((onedmask.shape[0], 4), dtype='uint8')
    A = numpy.array((r, g, b, 200), dtype='uint8')
    B = numpy.array((r, g, b, 0), dtype='uint8')
    res[:] = B
    res[onedmask > 0] = A
    res[:, numpy.array([0, 2])] = res[:, numpy.array([2, 0])]
    im = QG.QImage(res.tostring(), x_points, y_points, QG.QImage.Format_ARGB32)
    pixmap = QG.QPixmap.fromImage(im)
    return pixmap


def make_mask_pixmap_cm(twodmask, colormap):
    # print 'cmmask',twodmask,numpy.unique(twodmask)
    dd = twodmask
    dd = (dd - dd.min())/(1.0*(dd.max()-dd.min()))
    # print 'cmmask 2',dd,numpy.unique(dd)
    y_points, x_points = twodmask.shape
    onedmask = twodmask.flatten()
    cmap = cm.get_cmap(colormap)
    d2 = cmap.__call__(dd, bytes=True)
    d2.shape = (dd.size, 4)
    d2[:, numpy.array([0, 2])] = d2[:, numpy.array([2, 0])]
    d2[:, 3] = 0
    d2[onedmask > 0, 3] = 120
    # print 'D2',d2
    # print numpy.unique(d2[:,0])
    # print numpy.unique(d2[:,1])
    # print numpy.unique(d2[:,2])
    im_data = d2.tostring()
    im = QG.QImage(im_data, x_points, y_points, QG.QImage.Format_ARGB32)
    pixmap = QG.QPixmap.fromImage(im)
    return pixmap


class SenderObject(QC.QObject):
    selection_changed = QC.pyqtSignal()
