
import numpy as n

from scipy import diff
from scipy.interpolate import interp1d

from lsjuicer.util import helpers
from lsjuicer.data.transient import TransientGroup, Transient



class Fl_Data:
    def __init__(self, array, phys, coords, av = [], bl_per_transient = False):
        self.coords = coords
        self.av_mean = 1
        self.calculate_bl = False

        if len(coords) == 0:
            #use whole image
            self.coords = [0,array.shape[1]-1,0,array.shape[0]-1]

        #take slice of array
        print 'coords',self.coords
        print 'darray', array
        if len(self.coords)==2:
            self.data = array[0]
        elif self.coords[2] == 0 and self.coords[3]==0:
            self.data = array[0][:,self.coords[0]:self.coords[1]]
        else:
            self.data  = array[0][self.coords[2]:self.coords[3],self.coords[0]:self.coords[1]]
        if isinstance(av,list):
            print 'av is list',av
            if len(av) == 4:
                if sum(av[3:4])>0:
                    av_data  = array[0][av[2]:av[3],av[0]:av[1]]
                    print '2d',av_data
                    self.av_mean = n.mean(av_data)
                    if av[3]==av[2] and av[0]==av[1]:
                        #if no av roi
                        self.av_mean = 1
                else:
                    #1d case
                    av_data = array[0][:,av[0]:av[1]]
                    print array
                    print '1d',av_data
                    self.av_mean = n.mean(av_data)
                    if av[3]==av[2] and av[0]==av[1]:
                        #if no av roi
                        self.av_mean = 1
        elif av==None:
            print 'calculate'
#            self.av_mean = n.mean(self.data)
            self.av_mean = 1.0
        else :
            print 'av is number'
            self.av_mean = av
        if bl_per_transient == True:
            self.calculate_bl = True
        fl_list = []
        row_len = self.data.shape[0]
        print 'rows',row_len,self.av_mean,self.data.shape
        print 'data',self.data
        #for row in self.data:#:.transpose():
        #    assert len(row)==row_len
        #    fl_list.append( (sum(row) / row_len - self.av_mean) / self.av_mean + 1)
        if len(self.coords)==2:
            self.x_axis_values = range(0,self.coords[1])
        else:
            self.x_axis_values  = range(self.coords[0],self.coords[1])#pixel numbers

        fld = self.data.mean(axis=0)
        self.offset = self.x_axis_values[0]
        self.physical_x_axis_values  = helpers.shiftList(n.array(phys), self.offset)
        #self.phys = phys
        self.fl_func = interp1d(self.physical_x_axis_values.data,helpers.smooth(fld,1),kind='slinear')
        if 1:
            self.fl = helpers.shiftList(self.fl_func(phys),self.offset)
        #self.mx = []
        #self.my = []
        #self.xlim = 0
        #self.ylim = 0
        self.taus = []
        self.halftimes = []

    def set_events(self,all_events):
        self.events=[]
        for event in all_events:
            if event >self.physical_x_axis_values.data[0] and event < self.physical_x_axis_values.data[-1]:
                self.events.append(event)
    def set_gaps(self, all_gaps):
        self.gaps=[]
        for gap in all_gaps:
            if gap >self.physical_x_axis_values.data[0] and gap < self.physical_x_axis_values.data[-1]:
                self.gaps.append(gap)
    def addTransientGroup(self,tg):
        if not hasattr(self,'transientGroup'):
            self.transientGroup = tg
        else:
            self.transientGroup.append(tg)
            print 'done adding transient'
    def index_2_val(self,x):
        return self.phys_coords[0]+(x - self.x_axis_values[0])*self.phys_step

    #def val_2_index_x(self,v):
    #    return int((v - self.phys_coords[0])/self.phys_step + self.x_axis_values[0])

    #def val_2_index_y(self,v):
    #    return (v - self.phys_coords[2])/self.phys_step_y + self.y_axis_values[0]



    def get_limit(self, x):
        #limit function max_limit is given in physical coordinates so pixels cant be used
        return self.max_limit(x)


    #def deriv(self,x,y):
    #    dx = n.diff(x)
    #    dy = n.diff(y)
    #    der = []
    #    for x,y in zip(dx,dy):
    #        #print x,y,y/x
    #        der.append(y/x)
    #    return n.array(der)

    def find_phys_index(self,val):
        print 'total ',len(self.physical_x_axis_values.data)
        print 'looking for',val
        try:
            print 't1'
            ind = self.physical_x_axis_values.index(val) + 0*self.offset
            return ind
        except:
            print 't2'
            for i in range(len(self.physical_x_axis_values.data)-1):
                if self.physical_x_axis_values.data[i+1]>val and self.physical_x_axis_values.data[i]<=val:
                    return i+0*self.offset
            print 'error'

    def make_transient(self,edges, phys_coords = False):
        if phys_coords:
            start = self.find_phys_index(edges[0])
            end = self.find_phys_index(edges[1])
        else:
            start = edges[0]
            end = edges[1]
        return Transient(self.smoothed.data[start:end],start,end,self.physical_x_axis_values.data[start:end],self,self.calculate_bl)

    def make_transients(self,all_edges,physical_coords = False):
        tG = TransientGroup(self)

        #max_ys = []
        #if self.calculate_bl:
        #    max_ybs = []
        #max_xs = []
        for edge in all_edges:
            transient = self.make_transient(edge, physical_coords)
            tG.addTransient(transient)
            #max_ys.append(transient.max_y)
            #max_xs.append(transient.max)
            #if self.calculate_bl:
            #    max_ybs.append(transient.max_y_bl)
        return tG
        #self.mx = max_xs
        #self.my = max_ys
        #if self.calculate_bl:
        #    self.myb = max_ybs
        #self.pmx = [self.physical_x_axis_values[x] for x in self.mx]

    def find_transients(self,start,end,smooth_val):
        data = helpers.smooth(self.smoothed.data,smooth_val)
        f = data
        d1 = diff(data)
        d2 = diff(d1)
        zeros0 = []
        last = d1[0]
        index = 0
        for d,dd in zip( d1[1:], d2):
            phys_x = self.physical_x_axis_values.data[index]
            index +=1
            if (phys_x < start or phys_x > end):
                #if phys_x out of search range continue
                continue
            if d * last < 0.0 and dd > 0:
                #if the sign of the derivative changes and second derivative is >0 then we have local minimum
                zeros0.append(index)
            last = d
        #second run
        #make sure that each zero is in actual minimum, if not then adjust

        #third run
        #determine which zero is start/end of a transient
        dm = []
        for z in range(1,len(zeros0)):
            b0 = zeros0[z-1]
            b1 = zeros0[z]
            dm.append(max(f[b0:b1])-max(f[b0],f[b1]))
        avdm = n.mean(dm)
        #zeros = []
        starts = []
        ends = []
        amnt = 0.15
        for z in range(1,len(zeros0)):
            b0 = zeros0[z-1]
            b1 = zeros0[z]
            if max(f[b0:b1]) - max(f[b0], f[b1]) > amnt * avdm :
                starts.append(b0)
                ends.append(b1)

        for i in range(len(starts)):
            z = starts[i]
            #search_range = 5
            zero_value = self.smoothed.data[z]
            k = 1
            new_z_left = z
            new_z_right = z
            left_val = zero_value
            right_val = zero_value
            while self.smoothed.data[z - k] < zero_value:
                #look left
                new_z_left = z - k
                k += 1
            if k != 1:
                #add 1 cause during while the last step is invalid
                new_z_left += 1
            left_val = self.smoothed.data[new_z_left]
            k = 1
            while self.smoothed.data[z + k] < zero_value:
                #look right
                new_z_right = z + k
                k += 1
            if k != 1:
                #subtract 1 cause during while the last step is invalid
                new_z_right -= 1
            right_val = self.smoothed.data[new_z_right]
            if new_z_left == new_z_right == z:
                #we already were at minimum
                continue
            elif left_val< right_val:
                print 'adjusted left %i,%f to %i,%f'%(z,zero_value,new_z_left,left_val)
                starts[i] = new_z_left
            else:
                print 'adjusted right %i,%f to %i,%f'%(z,zero_value,new_z_right,right_val)
                starts[i] = new_z_right

        for i in range(len(ends)):
            z = ends[i]
            #search_range = 5
            zero_value = self.smoothed.data[z]
            k = 1
            new_z_left = z
            new_z_right = z
            left_val = zero_value
            right_val = zero_value
            while self.smoothed.data[z - k] < zero_value:
                #look left
                new_z_left = z - k
                k += 1
            if k != 1:
                #add 1 cause during while the last step is invalid
                new_z_left += 1
            left_val = self.smoothed.data[new_z_left]
            k = 1
            while self.smoothed.data[z + k] < zero_value:
                #look right
                new_z_right = z + k
                k += 1
            if k != 1:
                #subtract 1 cause during while the last step is invalid
                new_z_right -= 1
            right_val = self.smoothed.data[new_z_right]
            if new_z_left == new_z_right == z:
                #we already were at minimum
                continue
            elif left_val< right_val:
                print 'adjusted left %i,%f to %i,%f'%(z,zero_value,new_z_left,left_val)
                ends[i] = new_z_left
            else:
                print 'adjusted right %i,%f to %i,%f'%(z,zero_value,new_z_right,right_val)
                ends[i] = new_z_right

        edges = []
        for s,e in zip(starts,ends):
            edges.append([s,e])
        return self.make_transients(edges)

    def get_max_index(self,start,end):
        max = -1e6
        ind = None
        phys_offseted = helpers.shiftList(self.x_axis_values,self.offset)
        for x,val in zip(phys_offseted[start:end],self.smoothed[start:end]):
            if val > max:
                max = val
                ind = x
        return max,ind


    def calc_A1A2(self,min_delay):
        self.ratios =[]
        self.A2A1_ratios = []
        self.A2A1_delays = []
        for i in range(1,len(self.pmx)):
            delay = self.pmx[i]-self.pmx[i-1]
            if i == 1:
                self.ratios.append([(i-1,i),self.myb[i]/self.myb[i-1],delay])
                self.A2A1_ratios.append(self.myb[i]/self.myb[i-1])
                self.A2A1_delays.append(delay)
            else:
                previous_delay =  self.pmx[i-1]-self.pmx[i-2]
                if previous_delay>min_delay:
                    self.ratios.append([(i-1,i),self.myb[i]/self.myb[i-1],delay])
                    self.A2A1_ratios.append(self.myb[i]/self.myb[i-1])
                    self.A2A1_delays.append(delay)


    def find_start_end(self,x,percentage):
        """Find start and end positions of transient peaking at position x."""
        #find start
        min = self.smoothed[x]
        start_index = x
        index = 0
        search_active = False
        #go back till F goes below limit and then find minimum until F goes above limit again
        while True:
            #print x,index,self.offset
            if x-index > self.offset:
                F_val = self.smoothed[x - index]
                #print F_val,x-index
                if F_val > self.max_limit(self.physical_x_axis_values[x - index]):
                    if not search_active:
                        #not yet below limit, continue
                        index += 1
                        continue
                    if search_active:
                        #went above limit during searching, meaning we have reached the other end. break
                        break
                else:
                    search_active = True
                    if F_val < min:
                        #found new minimum. store it
                        min = F_val
                        start_index = x - index
                    index += 1
            else:
                #we went too far back over the ROI window
                break
        start_val = self.smoothed[start_index]
        #find end
        end_criteria = percentage
        #end is where (F-F0)/(F_max-F0) = end_criteria. F0 = start_val
        index = 0
        end_index = x
        F_max = self.smoothed[x]
        min_val = F_max
        crossings = 0
        while True:
            if x+index < self.x_axis_values[-1] and crossings < 2:
                #make sure we are not out of ROI range nor that we have not started climbing a new transient
                F_val = self.smoothed[x + index]
                if (F_val - start_val)/(F_max-start_val) < end_criteria:
                    end_index = x+index
                    break
                if (F_val - self.max_limit(self.physical_x_axis_values[x+index]))*(self.smoothed[x + index - 1] - self.max_limit(self.physical_x_axis_values[x+index-1])) <0:
                    #val-limit would have different signs during consequtive steps if we crossed the limit line
                    crossings += 1
                if F_val < min_val:
                    min_val = F_val
                    end_index = x + index
                index += 1
            else:
                #we went too far back over the ROI window,take the last value as end point
                print 'End criteria %f not reached. Stopped at x=%i for max at x=%i with ratio %f'\
                        %(end_criteria,end_index,x,(min_val-start_val)/(F_max-start_val))
                break
        return start_index,end_index

    def find_halftimes(self):
        self.halftimes = self.transientGroup.find_halftimes()

    def fit_taus(self):
        self.taus = self.transientGroup.fit_taus()

    def smooth(self, times = 1, wl = [10], win = 'blackman'):
        self.smoothed = n.array(self.fl.data)
        for i in range(times):
            self.smoothed = helpers.smooth(self.smoothed, window_len = wl[i], window = win)
        self.smoothed = helpers.shiftList(self.smoothed,self.offset)
