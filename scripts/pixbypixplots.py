import pylab as p

def doplots(res, raw):
    baseline = clean_plot_data(res, only_bl=True)
    f_fit = clean_plot_data(res)
    mean_bl = baseline.mean(axis=0)
    plots = range(9)
    #plots = [8]
    A0 = make_data_by_size_and_time(res, 'A',0)/mean_bl + 1
    A1 = make_data_by_size_and_time(res, 'A',1)/mean_bl + 1
    A3 = make_data_by_size(res,'A',2)/mean_bl + 1
    A4 = make_data_by_size(res,'A',3)/mean_bl + 1
    A_max = max(A0.max(), A1.max())
    A_min = min(A0.min(), A1.min())
    time = n.arange(res['frames'])
    if 1 in plots:
        p.figure()
        p.suptitle("Wave amplitudes",fontsize=16)
        p.subplot(3,1,1)
        p.title("First wave amplitude : $A_1$ [$F/F_0$]")
        cmap0 = p.cm.gnuplot
        p.imshow(A0, cmap = cmap0,vmin=A_min, vmax=A_max)

        p.colorbar()
        p.subplot(3,1,2)
        p.imshow(A1, cmap = cmap0,vmin=A_min, vmax=A_max)
        p.title("Second wave amplitude : $A_2$ [$F/F_0$]")
        p.colorbar()
        p.subplot(3,1,3)
        p.title("Amplitude ratio : $A_1/A_2$")

        cmap1 = p.cm.gist_rainbow_r
        p.imshow(nd.uniform_filter(A0/A1,2), cmap =
                p.cm.RdBu_r,interpolation='nearest')#,vmin=1.0)
        p.colorbar()
        #p.subplots_adjust(.05,0.0,1,0.95, 0.1,0.1)


    if 2 in plots:
        p.figure()
        cmap1 = p.cm.gnuplot
        p.title("Normalized baseline fluorescence : $F_0/\min(F_0)$")
        p.imshow(mean_bl/mean_bl.min(), cmap=cmap1)
        p.colorbar(orientation='horizontal')

    if 3 in plots:
        multiplot(raw,20)
        p.suptitle("Recorded fluorescence",fontsize=16)

    if 4 in plots:
        multiplot(f_fit,20)
        p.suptitle("Fit result",fontsize=16)

    if 5 in plots:
        #histograms
        amplitudes = []
        decays = []
        durations = []
        rises =[]
        for fitres in res['fits'].values():
            pf = n.poly1d(fitres['baseline'])
            baseline = pf(time).mean()
            transients = fitres['transients']
            for t in transients.values():
                amplitudes.append(t['A']/baseline+1)
                decays.append(t['tau2'])
                rises.append(t['d'])
                durations.append(t['d2'])
        #print len(amplitudes)
        p.figure()
        p.subplot(2,2,1)
        x0,bins,patches =\
        p.hist(amplitudes,bins=100,histtype='step',lw=2,label='All')
        p.hist(A0.flatten(),bins=bins,histtype='bar',alpha=0.5,label='First wave')
        p.hist(A1.flatten(),bins=bins,histtype='bar',alpha=0.5,label='Second wave')
        p.hist(n.hstack((A3.flatten(),A4.flatten())),bins=bins,histtype='bar',alpha=0.5,color='orange',label='Non-waves')
        p.xlabel("Release event amplitude [$F/F_0$]")
        p.title("Release event amplitude")
        p.legend()

        #p.figure()
        p.subplot(2,2,2)
        f_time = 6.0 #msec
        decays = n.array(decays)*f_time
        mask = decays<50*f_time
        T0 = make_data_by_size_and_time(res, 'tau2',0)*f_time
        T1 = make_data_by_size_and_time(res, 'tau2',1)*f_time
        T3 = make_data_by_size(res,'tau2',2)*f_time
        T4 = make_data_by_size(res,'tau2',3)*f_time
        x0,bins,patches =\
        p.hist(decays[mask],bins=100,histtype='step',lw=2,label='All')
        p.hist(T0.flatten(),bins=bins,histtype='bar',alpha=0.5,label='First wave')
        p.hist(T1.flatten(),bins=bins,histtype='bar',alpha=0.5,label='Second wave')
        p.hist(n.hstack((T3.flatten(),T4.flatten())),bins=bins,histtype='bar',alpha=0.5,color='orange',label='Non-waves')
        p.xlabel("Uptake time-constant [ms]")
        p.title("Uptake time-constant")
        p.xlim(25, 250)
        p.legend(loc=2)


        #p.figure()
        p.subplot(2,2,3)
        f_time = 6.0 #msec
        rises = n.array(rises)*f_time
        mask = rises<50*f_time
        R0 = make_data_by_size_and_time(res, 'd',0)*f_time
        R1 = make_data_by_size_and_time(res, 'd',1)*f_time
        R3 = make_data_by_size(res,'d',2)*f_time
        R4 = make_data_by_size(res,'d',3)*f_time
        x0,bins,patches =\
        p.hist(rises[mask].flatten(),bins=100,histtype='step',lw=2,label='All')
        p.hist(R0.flatten(),bins=bins,histtype='bar',alpha=0.5,label='First wave')
        p.hist(R1.flatten(),bins=bins,histtype='bar',alpha=0.5,label='Second wave')
        p.hist(n.hstack((R3.flatten(),R4.flatten())),bins=bins,histtype='bar',alpha=0.5,color='orange',label='Non-waves')
        p.xlabel("Rise phase time-constant [ms]")
        p.title("Rise phase time-constant")
        p.xlim(0, 175)
        p.legend()

        #p.figure()
        p.subplot(2,2,4)
        f_time = 6.0 #msec
        durations = n.array(durations)*f_time
        mask = rises<90*f_time
        D0 = make_data_by_size_and_time(res, 'd2',0)*f_time
        D1 = make_data_by_size_and_time(res, 'd2',1)*f_time
        D3 = make_data_by_size(res,'d2',2)*f_time
        D4 = make_data_by_size(res,'d2',3)*f_time
        x0,bins,patches =\
        p.hist(durations[mask].flatten(),bins=100,histtype='step',lw=2,label='All')
        p.hist(D0.flatten(),bins=bins,histtype='bar',alpha=0.5,label='First wave')
        p.hist(D1.flatten(),bins=bins,histtype='bar',alpha=0.5,label='Second wave')
        p.hist(n.hstack((D3.flatten(),D4.flatten())),bins=bins,\
                histtype='bar',alpha=0.5,color='orange',label='Non-waves')
        p.xlabel("Dration [ms]")
        p.title("Plateau duration")
        p.xlim(0, 250)
        p.legend(loc=2)
        #p.subplots_adjust(.05,0.05,0.95,.95, 0.1,0.3)


    if 6 in plots:
        p.figure()
        f_time = 6e-3 #frame time
        T0 = make_data_by_size_and_time(res, 'm2',0)*f_time
        T1 = make_data_by_size_and_time(res, 'm2',1)*f_time
        p.suptitle("Release initiation",fontsize=16)
        p.subplot(3,1,1)
        p.title("First wave start time : $t_1$ [s]")
        cmap0 = p.cm.gnuplot
        p.imshow(T0, cmap = cmap0)

        p.colorbar()
        p.subplot(3,1,2)
        p.imshow(T1, cmap = cmap0)
        p.title("Second wave start time : $t_2$ [s]")
        p.colorbar()

        p.subplot(3,1,3)
        p.title("Time between two waves $\Delta t = t_2-t_1$ [s]")

        cmap1 = p.cm.gist_rainbow_r
        p.imshow(nd.uniform_filter(T1-T0,3), cmap =
                cmap1,interpolation='nearest')#,vmin=1.0)
        p.colorbar()
        #p.subplots_adjust(.05,0.0,1,0.95, 0.1,0.1)
        #p.figure()
        #print len(time),len(T1.mean(axis=0))
        #t0m = T0.mean(axis=0)
        #t1m = T1.mean(axis=0)
        #p.plot(n.arange(T0.shape[1]-1), n.diff(t0m-t0m[0]))
        #p.plot(n.arange(T1.shape[1]-1), n.diff(t1m-t1m[0]))
    if 7 in plots:
        p.figure()
        events=data_events(res)
        p.imshow(events,cmap=p.cm.RdPu_r)
        cb=p.colorbar(orientation='horizontal')
        cb.set_ticks([2,3,4])
        p.title("Number of release events")

    if 8 in plots:

        A0 = make_data_by_size_and_time(res, 'd',0)*6

        A1 = make_data_by_size_and_time(res, 'd',1)*6
        p.figure()
        p.suptitle("Wave decay time constants",fontsize=16)
        p.subplot(3,1,1)
        p.title("First wave decay constant : $\\tau_1$ [ms]")
        cmap0 = p.cm.gnuplot
        A_min = min(A0.mean()-3*A0.std(),A1.mean()-3*A1.std())
        A_max = max(A0.mean()+3*A0.std(),A1.mean()+2*A1.std())
        p.imshow(A0, cmap = cmap0,vmin=A_min, vmax=A_max)

        p.colorbar()
        p.subplot(3,1,2)
        p.imshow(A1, cmap = cmap0,vmin=A_min, vmax=A_max)
        p.title("Second wave decay constant : $\\tau_2$ [ms]")
        p.colorbar()
        p.subplot(3,1,3)
        p.title("Difference : $\\tau_2-\\tau_1$ [ms]")

        cmap1 = p.cm.gist_rainbow_r
        p.imshow(nd.uniform_filter(A1-A0,2), cmap =
                p.cm.RdBu_r,interpolation='nearest')#,vmin=1.0)
        p.colorbar()
        #p.subplots_adjust(.05,0.0,1,0.95, 0.1,0.1)
    p.show()

def save_frames_nw(cpd, dt,t_range=None):
    frames = cpd.shape[0]
    if t_range:
        times = n.arange(t_range[0], t_range[1], dt)
        t_min=t_range[0]
        t_max=t_range[1]
    else:
        times=n.arange(0, frames, dt)
        t_min=0
        t_max=frames
    mean = cpd[t_min:t_max].mean()
    std = cpd[t_min:t_max].std()
    fmin = cpd[t_min:t_max].min()
    fmax=cpd[t_min:t_max].max()
    print len(times),fmin,fmax,mean,std
    fmin = mean-std
    fmax = mean+std
    f=p.figure()
    for i,c in enumerate(times):
        #p.subplot(2, 1, 1)
        p.imshow(nd.uniform_filter(cpd[c],3),vmin=fmin,vmax=fmax,cmap=p.cm.rainbow,
                 interpolation='nearest',aspect='equal')
        p.title('Fit')
        #p.subplot(2, 1, 2)
        #p.title('Raw')
        #p.imshow(raw[c],vmin=fmin,vmax=fmax,cmap=p.cm.gnuplot,interpolation='nearest',aspect='equal')
        #ax.set_xticks([])
        #ax.set_yticks([])
        p.title("Non wave events. $t=%.2f$"%(c*6e-3), fontsize=12)
        p.savefig("movie/p_nw_%04i.png"%i)
        f.clear()

def save_frames(cpd,raw,nw=None, dt=1,t_range=None):
    import pylab as p
    frames = cpd.shape[0]
    if t_range:
        times = n.arange(t_range[0], t_range[1], dt)
        t_min=t_range[0]
        t_max=t_range[1]
    else:
        times=n.arange(0, frames, dt)
        t_min=0
        t_max=frames
    #rows = int(n.ceil(n.sqrt(len(times))))
    #cols = int(n.ceil(float(len(times))/rows))

    #mean = cpd[t_min:t_max].mean()
    #std = cpd[t_min:t_max].std()
    fmin = cpd[t_min:t_max].min()
    fmax=cpd[t_min:t_max].max()

    #nw_mean = nw[t_min:t_max].mean()
    #nw_std = nw[t_min:t_max].std()
    #nw_fmin = nw[t_min:t_max].min()
    #nw_fmax= nw[t_min:t_max].max()
    ##print rows,cols,len(times),fmin,fmax,mean,std
    #fmin = mean-std
    #nw_fmin = nw_mean-nw_std
    #nw_fmin = nw_mean+nw_std
    f=p.figure()
    for i,c in enumerate(times):
        p.subplot(2, 1, 1)
        p.title('Raw')
        p.imshow(raw[c],vmin=fmin,vmax=fmax,cmap=p.cm.gnuplot,interpolation='nearest',aspect='equal')
        p.subplot(2, 1, 2)
        p.imshow(cpd[c],vmin=fmin,vmax=fmax,cmap=p.cm.gnuplot,interpolation='nearest',aspect='equal')
        p.title('Fit')
        #ax.set_xticks([])
        #ax.set_yticks([])
        #p.subplot(3, 1, 3)
        #p.title("Non-wave events")
        #p.imshow(nd.uniform_filter(nw[c],2),vmin=nw_fmin,vmax=nw_fmax,cmap=p.cm.gnuplot,interpolation='nearest',aspect='equal')
        #p.suptitle("$t=%.2f$"%(c*6e-3), fontsize=12)
        p.savefig("movie/p_%04i.png"%i)
        #p.subplots_adjust(.05,0.05,.95,0.90, 0.15,0.35)
        f.clear()
        #p.title(c, fontsize=10)


def multiplot(cpd, dt,t_range=None):
    import pylab as p
    frames = cpd.shape[0]
    if t_range:
        times = n.arange(t_range[0], t_range[1], dt)
        t_min=t_range[0]
        t_max=t_range[1]
    else:
        times=n.arange(0, frames, dt)
        t_min=0
        t_max=frames
    rows = int(n.ceil(n.sqrt(len(times))))
    cols = int(n.ceil(float(len(times))/rows))

    mean = cpd[t_min:t_max].mean()
    std = cpd[t_min:t_max].std()
    fmin = cpd[t_min:t_max].min()
    fmax=cpd[t_min:t_max].max()
    #print rows,cols,len(times),fmin,fmax,mean,std
    fmin = mean-std
    p.figure()
    for i,c in enumerate(times):
        ax=p.subplot(rows, cols, i+1)
        p.imshow(cpd[c],vmin=fmin,vmax=fmax,cmap=p.cm.gnuplot,interpolation='nearest',aspect='auto')
        ax.set_xticks([])
        ax.set_yticks([])
        p.title("$t=%.2f$"%(c*6e-3), fontsize=10)
        #p.title(c, fontsize=10)
    #p.subplots_adjust(.01,0.01,.99,0.90, 0.15,0.35)

def non_waves(time, result):
    f = n.zeros(len(time))
    transients = result['transients'].values()
    if len(transients) <= 2:
        return f
    else:
        transients.sort(key=lambda x:x['A'], reverse = True)
        use = transients[2:]
        for t in use:
            res = fitfun.ff6(time, **t)
            if True not in n.isnan(res):
                f+=res
            else:
                print "NAN for", t
        return f


