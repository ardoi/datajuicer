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
        for x,y in zip(xvals,yvals):
            amps.append(cwt[y,x])
            ws.append(y)
        print '\n',xvals[0]
        print 'xx,yy=',ws,",",amps
        #index of the weight at ridge maximum
        max_ws_index = find_first_max(amps)
        #print 'max',max_windex
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
    filtered = _filter_ridge_lines(cwt_dat, ridge_lines, min_snr=min_snr, min_length=5)
    #if pad:
    #    good_ones = [x for x in filtered if x[1][0]>vector.size/pad\
    #                and x[1][0]<vector.size+vector.size/pad]
    #else:
    good_ones = filtered
    #print '\n\ngood ones'
    #for g in good_ones:
    #    print g
    #adjust = vector.size/pad - 1 if pad else 0
    #find boundaries of region from its half height cwd by looking for local minima around the peak
    max_locs = []
    for g in good_ones:
        loc = g[0][-1]*5/12
        minima = n.argwhere(ss._peak_finding._boolrelextrema(cwt_dat[loc], n.less)).flatten()
        x_loc = g[1][2]
        left_min = 0
        right_min = len(cwt_dat[loc])
        for mi in minima:
            if mi < x_loc and mi > left_min:
                left_min = mi
            if mi>x_loc and mi<right_min:
                right_min = mi
        max_locs.append((x_loc ,g[0][-1], left_min, right_min,loc))
    #print 'mm',max_locs
    return n.array(sorted(max_locs, key=lambda x:x[0]))

def find_first_max(vec_in):
    """find the first local maximum in a vector"""
    i = 1
    threshold = 1.05#peak cannot be more than treshold x neighbour value
    vec = n.diff(vec_in)
    remembered = None
    while i<len(vec)-2:
        if vec[i]>0 and vec[i]*vec[i+1]<0:
            if min(vec[i]/vec[i-1], vec[i]/vec[i+1])<threshold:
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
    #print '\n\ngood ones'
    #for g in good_ones:
    #    print g
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

def remove_overlapping_regions(regs):
    def test_overlap(a,b):
        return not(a[3]<b[2] or b[3]<a[2])
    if len(regs) == 1:
        return regs
    print 'all:',regs
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
            #overlap so the region with the )highest score gets +1
            res[one]+=max(0, cmp(one[4],two[4]))
            res[two]+=max(0, cmp(two[4],one[4]))
    good=[]
    #only regions which have len(res) - 1 as score have no overlaps
    #with higher scored regions and are kept
    for k,v in res.iteritems():
        if v == len(res) - 1:
            good.append(k)
    print 'good:',good
    return good

def find_regions3(rrr, widths, data_size):
    regions = {}
    #print 'all regions',rrr
    rrr = remove_overlapping_regions(rrr)
    #print 'nonoverlapped', rrr
    for ri, r in enumerate(rrr):
        p=int(r[0])
        regions[p]=(r[2],r[3])
    return regions



def find_regions2(rrr, widths, data_size):
    regions = {}
    keep_right = False
    right_new = None
    #print 'rrr',rrr
    for ri, r in enumerate(rrr):
        p=int(r[0])
        width = widths[r[1]]
        #print 'get width', p,r[1],width,widths
        if keep_right:
            left = right_new
        else:
            left = r[2]
        keep_right = False
        right = r[3]
        #print ri,r
        if ri<len(rrr)-1:
            #print 'a'
            next_left = rrr[ri+1][2]
            next_p = rrr[ri+1][0]
            #next_w = widths[rrr[ri+1][1]]
            #regions[p] = (max(0, p - width/2), min(p+1*width,next_p-next_w/2))
            #print next_left,next_p
            if 0:#next_left < right:
                #limit the right side to the left side of the next
                min_next_left = next_p - 4*(next_p - next_left)/5
                right_new = min(min_next_left, p+((right-p)+abs(p-next_left))/2)
                #print right_new, p+2*width,right
                regions[p] = ( max(left, p - width), min(right_new, p + 2*width))
                if regions[p][1]==right_new:
                    keep_right = True
            else:
                #print 'else'
                regions[p] = (max(left, p - width), min(right, p+2*width))
        else:
            regions[p] = (max(left, p - width), min(right, p+2*width))
            #regions[p] = (left, right)
            #regions[p] = (max(0, p - width/2), min(p+1*width, data_size))
        assert regions[p][0]<p and regions[p][1]>p,str(regions[p])+" "+str(p)
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

def get_peaks(data, min_snr=3.5, max_width=75):
    #w = [1, 5, 10, 15, 20, 25, 50, 100, 150]
    #widths=n.array(w)
    #changed 2->4 for puffs
    #wlist = [1] + range(2,20,4)+range(20,120,5)
    #wlist = range(1,120,5)
    #widths = n.array(wlist)
    widths =  n.arange(1,max_width ,2)
    peaks_all = find_peaks_cwt2(data, widths, min_snr)
    if not peaks_all:
        return {}
    #if not peaks_all.any():
    #    return {}
    #peaks = peaks_all[:,0]
    #sizes = peaks_all[:,1]
    #wavelet width to use for estimating region sizes
    #we use the smallest size to ensure we have no blending of regions
    #use_size = sizes.min()/2 + 1
    #cwd = ss.cwt(data, ss.ricker, [widths[use_size]])[0]
    #regions = find_regions(peaks, cwd)
    regions = find_regions3(peaks_all, widths, data.size)
    #print 'found regions', regions
    return regions

def show_peaks(data, min_snr=5.0, max_width = 50, xmin=None, xmax=None):
    import pylab
    pylab.plot(data)
    regions = get_peaks(data, min_snr, max_width)
    ca=pylab.gca()
    for r,b in regions.iteritems():
        pylab.plot(r,data.max(),'ro')
        ca.add_patch(pylab.Rectangle((b[0],data.min()),b[1]-b[0],
                                data.max(),alpha=0.5,facecolor='orange'))
    if xmin and xmax:
        pylab.xlim(xmin, xmax)
    pylab.show()
    return regions

