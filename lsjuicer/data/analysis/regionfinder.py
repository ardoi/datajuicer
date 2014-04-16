import itertools
from collections import defaultdict
import numpy as n
import scipy.signal as ss
from scipy.stats import scoreatpercentile
from lsjuicer.util.helpers import timeIt

def pad_data(vector, pad):
    vec = n.hstack((vector[:vector.size/pad+1][::-1], vector, vector[-vector.size/pad:][::-1]))
    return vec

def pad_data_const(vector, pad):
    av = 10
    left_av = vector[:av].mean()
    right_av=vector[-av:].mean()
    #print vector[:av], vector[-av:]
    pad_size = vector.size/pad
    vec = n.hstack((n.ones(pad_size)*left_av, vector,n.ones(pad_size)*right_av ))
    return vec

def _filter_ridge_lines(cwt, ridge_lines, window_size=None, min_length=None,
                       min_snr=1, noise_perc=10):

    num_points = cwt.shape[1]
    if min_length is None:
        min_length = n.ceil(cwt.shape[0] / 4)
    if window_size is None:
        window_size = n.ceil(num_points / 20)
    hf_window = window_size / 2

    #Filter based on SNR
    row_one = cwt[0, :]
    noises = n.zeros_like(row_one)
    for ind, val in enumerate(row_one):
        window = n.arange(max([ind - hf_window, 0]), min([ind + hf_window, num_points]))
        window = window.astype(int)
        noises[ind] = scoreatpercentile(row_one[window], per=noise_perc)
        #noises[ind] = n.std(row_one[window])
    noise_level = scoreatpercentile(row_one, per = noise_perc)

    def filt_func(line):
        if len(line[0]) < min_length:
            return False
        #snr = abs(cwt[line[0][0], line[1][0]] / noises[line[1][0]])
        c=line[0][-1]/2
        #snr = -cwt[c, line[1][0]] / noises[line[1][0]]
        #snr = cwt[c, line[1][0]] / abs(noises[line[1][0]]) + 1
        snr = cwt[c, line[1][0]] / abs(noise_level) + 1
        #line.append(['snr=',snr,c,cwt[c, line[1][0]] , noises[line[1][0]]] )
        line.append(['snr=',snr,c,cwt[c, line[1][0]] , noise_level] )
        if snr < min_snr:
            return False
        return True

    return list(filter(filt_func, ridge_lines))

def _filter_ridge_lines2(cwt, ridge_lines, window_size=None, min_length=None,
                       min_snr=1, noise_perc=10):

    num_points = cwt.shape[1]
    if min_length is None:
        min_length = n.ceil(cwt.shape[0] / 4)
    if window_size is None:
        window_size = n.ceil(num_points / 20)
    hf_window = window_size / 2

    #Filter based on SNR
    row_one = cwt[0, :]
    noises = n.zeros_like(row_one)
    for ind, val in enumerate(row_one):
        window = n.arange(max([ind - hf_window, 0]), min([ind + hf_window, num_points]))
        window = window.astype(int)
        noises[ind] = scoreatpercentile(row_one[window], per=noise_perc)
        #noises[ind] = n.std(row_one[window])
    noise_level = scoreatpercentile(row_one, per = noise_perc)

    def filt_func(line):
        if len(line[0]) < min_length:
            return False
        yvals,xvals = line
        amps = [] #amplitudes along the ridge
        ws=[] #w indices along the rigde
        locs=[] #ridge locations
        for x,y in zip(xvals,yvals):
            amps.append(cwt[y,x])
            ws.append(y)
            locs.append(x)
        print '\n',xvals[0]
        print 'xx,yy,zz=',ws,",",amps,",",locs
        #index of the weight at ridge maximum
        max_ws_index = find_first_max(amps)
        print 'max',max_ws_index
        if max_ws_index is None:
            return False
        c=amps[max_ws_index]
        #add 2 to the index for a bit bigger span and take the actual weight index
        max_w_index = ws[max_ws_index + min(2, len(ws)-1-max_ws_index)]
        snr = c / abs(noise_level) + 1
        #line.append(['snr=',snr,c,cwt[c, line[1][0]] , noises[line[1][0]]] )
        line.append(['snrr=',snr,c,max_w_index , noise_level] )
        if snr < min_snr:
            return False
        return True

    return list(filter(filt_func, ridge_lines))

#def find_peaks_cwt(vector, widths, min_snr=1):
#    #print vector.size, widths
#    gap_thresh = n.ceil(widths[0])
#    max_distances = widths / 3.0
#    wavelet = ss.ricker
#    pad = 1
#    if pad:
#        #vec = n.hstack((vector[:vector.size/pad+1][::-1], vector, vector[-vector.size/pad:][::-1]))
#        vec = pad_data_const(vector, pad)
#    else:
#        vec=vector
#    cwt_dat_all = ss.cwt(vec, wavelet, widths)
#    cwt_dat = cwt_dat_all[:,vector.size/pad:vector.size/pad+vector.size]
#    ridge_lines = ss._peak_finding._identify_ridge_lines(cwt_dat, max_distances, gap_thresh)
#    filtered = _filter_ridge_lines(cwt_dat, ridge_lines, min_snr=min_snr, min_length=5)
#    #if pad:
#    #    good_ones = [x for x in filtered if x[1][0]>vector.size/pad\
#    #                and x[1][0]<vector.size+vector.size/pad]
#    #else:
#    good_ones = filtered
#    #print '\n\ngood ones'
#    #for g in good_ones:
#    #    print g
#    #adjust = vector.size/pad - 1 if pad else 0
#    #find boundaries of region from its half height cwd by looking for local minima around the peak
#    max_locs = []
#    for g in good_ones:
#        loc = g[0][-1]*5/12
#        minima = n.argwhere(ss._peak_finding._boolrelextrema(cwt_dat[loc], n.less)).flatten()
#        x_loc = g[1][2]
#        left_min = 0
#        right_min = len(cwt_dat[loc])
#        for mi in minima:
#            if mi < x_loc and mi > left_min:
#                left_min = mi
#            if mi>x_loc and mi<right_min:
#                right_min = mi
#        max_locs.append((x_loc ,g[0][-1], left_min, right_min,loc))
#    #print 'mm',max_locs
#    return n.array(sorted(max_locs, key=lambda x:x[0]))

def find_first_max(vec_in):
    """find the first local maximum in a vector"""
    i = 0
    threshold = 1.05#peak cannot be more than treshold x neighbour value
    vec = n.diff(vec_in)
    remembered = None
    while i<len(vec)-2:
        if vec[i]>0 and vec[i]*vec[i+1]<0:
            check = []
            check.append(vec[i]/vec[i+1])
            if i>0:
                check.append(vec[i]/vec[i-1])
            if min(check)<threshold:
                return i + 1
            else:
                #we want the peak not to be more than 5% of neighbours
                #in order to avoid noise forcing a smaller region to
                #be detected instead of a larger one. However,
                #if it turns out that it is the only maximum then
                #still want to return it
                remembered = i+1
                continue
        i+=1
    if not remembered:
        i = 0
        #no maximum was found. Look for inflection point then
        vec = n.diff(vec)
        while i<len(vec)-2:
            if vec[i]*vec[i+1]<0:
                return i + 2
            i+=1

    return remembered

def find_peaks_cwt2(vector, widths, min_snr=1):
    #print vector.size, widths
    gap_thresh = n.ceil(widths[0])
    max_distances = widths / 3.0
    wavelet = ss.ricker
    pad = 1
    if pad:
        #vec = n.hstack((vector[:vector.size/pad+1][::-1], vector, vector[-vector.size/pad:][::-1]))
        vec = pad_data_const(vector, pad)
    else:
        vec=vector
    cwt_dat_all = ss.cwt(vec, wavelet, widths)
    cwt_dat = cwt_dat_all[:,vector.size/pad:vector.size/pad+vector.size]
    ridge_lines = ss._peak_finding._identify_ridge_lines(cwt_dat, max_distances, gap_thresh)
    min_length = 5

    #filtered = ss._peak_finding._filter_ridge_lines(cwt_dat, ridge_lines, min_snr=min_snr)
    filtered = _filter_ridge_lines2(cwt_dat, ridge_lines, min_snr=min_snr, min_length=min_length)
    #if pad:
    #    good_ones = [x for x in filtered if x[1][0]>vector.size/pad\
    #                and x[1][0]<vector.size+vector.size/pad]
    #else:
    good_ones = filtered
    #adjust = vector.size/pad - 1 if pad else 0
    #find boundaries of region from its half height cwd by looking for local minima around the peak
    max_locs = []
    for g in good_ones:
        x_loc = g[1][2]
        width_index = g[-1][-2]#the width at the maximum on the ridge
        width = widths[width_index]
        snr = g[-1][1]
        #print 'width',x_loc, width_index,width,snr
        left_min = max(0,x_loc-int(1.5*width))
        right_min = min(x_loc+2*width, len(cwt_dat[0]))
        max_locs.append((x_loc ,width, left_min, right_min, snr))
    #print 'mm',max_locs
    return sorted(max_locs, key=lambda x:x[0])

def detect_overlapping_regions(regs):
    def test_overlap(a,b):
        return not(a[3]<=b[2] or b[3]<=a[2])
    if len(regs) == 1:
        return regs
    #return regs
    #print 'all:',regs
    ii=itertools.combinations(regs,2)
    res = defaultdict(int)
    for i in ii:
        one = i[0]
        two = i[1]
        #print one,two
        test = test_overlap(one, two)
        if not test:
            #regions don't overlap so both get +1 score
            res[one]+=1
            res[two]+=1
        else:
            #overlap so the region with the higher snr score gets +1
            one_snr = one[4]
            if one_snr == two[4]:
                #same snr so we'll pick one at random by altering
                #the snr of the first region
                q = n.random.choice([-1,1])
                one_snr += q
            res[one] += max(0, -cmp(one_snr, two[4]))
            res[two] += max(0, -cmp(two[4], one_snr))
    good = defaultdict(list)
    #only regions which have len(res) - 1 as score have no overlaps
    #with higher scored regions and are kept. If none exist then len(res)-2
    #etc
    #print range(0, len(res))[::-1]
    for k,v in res.iteritems():
        good[v].append(k)
    #for j in range(1, len(res))[::-1]:
    #    #print 'j is',j
    #    for k,v in res.iteritems():
    #        if v == j:
    #            good.append(k)
    #    if good:
    #        break
    print 'good:',good
    return good


#def find_regions3(rrr):
#    regions = {}
#    rrr = remove_overlapping_regions(rrr)
#    for ri, r in enumerate(rrr):
#        p = int(r[0])
#        regions[p] = (r[2], r[3])
#    return regions


def get_regions(data, min_snr=3.5, max_width=150, step=5):
    #TODO max width should not be in pixels
    widths = n.arange(1, max_width, step)
    peaks_all = find_peaks_cwt2(data, widths, min_snr)
    if not peaks_all:
        return {}
    print 'bla'
    regions = detect_overlapping_regions(peaks_all)
    print 'regions', regions
    return regions


def show_regions(data, min_snr=5.0, max_width=150, step=5, xmin=None, xmax=None):
    import pylab
    pylab.plot(data)
    regions = get_regions(data, min_snr, max_width, step)
    ca = pylab.gca()
    keys = regions.keys()
    keys.sort(reverse=True)
    colors = iter(['orange', 'navy', 'magenta', 'lime','yellow'])
    for k in keys:
        b = regions[k]
        color = colors.next()
        for region in b:
            pylab.plot(region[0], data.max(), 'ro')
            print region
            ca.add_patch(pylab.Rectangle((region[2], data.min()), region[3]-region[2],
                            data.max(), alpha=0.5, facecolor=color))
    pylab.show()
    if xmin and xmax:
        pylab.xlim(xmin, xmax)
    return regions

