import numpy as n
import scipy.signal as ss

def find_peaks_cwt(vector, widths, min_snr=1):
    print vector.size, widths
    gap_thresh = n.ceil(widths[0])
    max_distances = widths / 3.0
    wavelet = ss.ricker
    pad = 16
    if pad:
        vec = n.hstack((vector[:vector.size/pad+1][::-1], vector, vector[-vector.size/pad:][::-1]))
    else:
        vec=vector
    cwt_dat = ss.cwt(vec, wavelet, widths)
    ridge_lines = ss._peak_finding._identify_ridge_lines(cwt_dat, max_distances, gap_thresh)
    filtered = ss._peak_finding._filter_ridge_lines(cwt_dat, ridge_lines, min_snr=min_snr)
    good_ones = [x for x in filtered if x[1][0]>vector.size/pad\
                 and x[1][0]<vector.size+vector.size/pad]
    adjust = vector.size/pad - 1 if pad else 0
    max_locs = [(x[1][0] - adjust ,x[0][-1]) for x in good_ones]
    return n.array(sorted(max_locs, key=lambda x:x[0]))

def find_regions2(rrr, widths, data_size):
    regions = {}
    for ri, r in enumerate(rrr):
        p=int(r[0])
        width = widths[r[1]]
        if ri<len(rrr)-1:
            next_p = rrr[ri+1][0]
            next_w = widths[rrr[ri+1][1]]
            regions[p] = (p - width/2, min(p+2*width,next_p-next_w/2))
        else:
            regions[p] = (p - width/2, min(p+2*width, data_size))
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
    widths =  n.arange(5,110 ,5)
    peaks_all = find_peaks_cwt(data, widths, min_snr)
    peaks = peaks_all[:,0]
    sizes = peaks_all[:,1]
    #wavelet width to use for estimating region sizes
    #we use the smallest size to ensure we have no blending of regions
    use_size = sizes.min()/2 + 1
    cwd = ss.cwt(data, ss.ricker, [widths[use_size]])[0]
    #regions = find_regions(peaks, cwd)
    regions = find_regions2(peaks_all, widths, data.size)
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

