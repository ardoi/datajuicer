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
    print vector[:av], vector[-av:]
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

    def filt_func(line):
        if len(line[0]) < min_length:
            return False
        #snr = abs(cwt[line[0][0], line[1][0]] / noises[line[1][0]])

        snr = -cwt[line[0][-1]/2, line[1][0]] / noises[line[1][0]]
        #line.append(['snr=',snr,cwt[line[0][-1], line[1][0]] , noises[line[1][0]]] )
        if snr < min_snr:
            return False
        return True

    return list(filter(filt_func, ridge_lines))

def find_peaks_cwt(vector, widths, min_snr=1):
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
    #filtered = ss._peak_finding._filter_ridge_lines(cwt_dat, ridge_lines, min_snr=min_snr)
    filtered = _filter_ridge_lines(cwt_dat, ridge_lines, min_snr=min_snr)
    #if pad:
    #    good_ones = [x for x in filtered if x[1][0]>vector.size/pad\
    #                and x[1][0]<vector.size+vector.size/pad]
    #else:
    good_ones = filtered
    #print '\n\ngood ones'
    #for g in good_ones:
    #    print g
    #adjust = vector.size/pad - 1 if pad else 0
    adjust=0
    max_locs = [(max(0,x[1][0] - adjust) ,x[0][-1]) for x in good_ones]
    return n.array(sorted(max_locs, key=lambda x:x[0]))

def find_regions2(rrr, widths, data_size):
    regions = {}
    for ri, r in enumerate(rrr):
        p=int(r[0])
        width = widths[r[1]]
        if ri<len(rrr)-1:
            next_p = rrr[ri+1][0]
            next_w = widths[rrr[ri+1][1]]
            regions[p] = (max(0, p - width/2), min(p+1*width,next_p-next_w/2))
        else:
            regions[p] = (max(0, p - width/2), min(p+1*width, data_size))
    return regions

def find_regions(peaks, cwd_data):
    mins = ss._peak_finding.argrelmin(cwd_data)[0]
    regions = {}

    last = 0
    for pi, p in enumerate(peaks):
        p=int(p)
        for ii in range(last,len(mins)-1):
            if mins[ii] < p and mins[ii + 1] > p:
                last=ii
                if pi<len(peaks)-1 and ii<len(mins)-3 and mins[ii+2] < peaks[pi+1] :
                    regions[p]= (mins[ii], min(mins[ii+1] + mins[ii+1] - mins[ii], mins[ii+2]))
                else:
                    regions[p] = (mins[ii], mins[ii+1])
                break
        if p not in regions:
            #didn't find minima on both sides
            #so let's check either side
            #left
            left = mins[mins<p]
            minleft = None
            minright = None
            if left.any():
                minleft = left.max()
            #right
            right = mins[mins>p]
            if right.any():
                minright = right.min()
            if minleft and not minright:
                minright = min(p + 2*(p-minleft), cwd_data.size)
            elif minright and not minleft:
                minleft = max(p - (minright - p), 0)
            else:
                raise RuntimeError
            regions[p] = (minleft, minright)
    return regions

def get_peaks(data, min_snr=3.0):
    #w = [1, 5, 10, 15, 20, 25, 50, 100, 150]
    #widths=n.array(w)
    widths =  n.arange(1,120 ,5)
    peaks_all = find_peaks_cwt(data, widths, min_snr)
    if not peaks_all.any():
        return {}
    #peaks = peaks_all[:,0]
    #sizes = peaks_all[:,1]
    #wavelet width to use for estimating region sizes
    #we use the smallest size to ensure we have no blending of regions
    #use_size = sizes.min()/2 + 1
    #cwd = ss.cwt(data, ss.ricker, [widths[use_size]])[0]
    #regions = find_regions(peaks, cwd)
    regions = find_regions2(peaks_all, widths, data.size)
    print 'found regions', regions
    return regions

def show_peaks(data, min_snr=5.0, xmin=None, xmax=None):
    import pylab
    pylab.plot(data)
    regions = get_peaks(data, min_snr)
    ca=pylab.gca()
    for r,b in regions.iteritems():
        pylab.plot(r,data.max(),'ro')
        ca.add_patch(pylab.Rectangle((b[0],data.min()),b[1]-b[0],
                                data.max(),alpha=0.5,facecolor='orange'))
    if xmin and xmax:
        pylab.xlim(xmin, xmax)
    pylab.show()
    return regions

