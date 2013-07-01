import sys
from collections import defaultdict
from itertools import cycle
#from pprint import pprint

import numpy

import webcolors
from mayavi import mlab

from lsjuicer.data.analysis import transient_find as tf
from lsjuicer.inout.db import sqla as sa
#import fitfun

s=sa.dbmaster.get_session()

ans=s.query(sa.PixelByPixelAnalysis).all()
an=ans[1]
pixels=an.fitregions[0].results[0].pixels
el=tf.do_event_list(pixels)

#an=ans[0]
#pixels=an.fitregions[0].results[0].pixels
#el2=tf.do_event_list(pixels)
#el.extend(el2)

def normify(a):
    #you can use preprocessing.scale instead
    return (a-a.mean())/a.std()

shape_params = ['A','tau2','d2','d']
ea_shape0 = tf.do_event_array(el,shape_params)

ea_shape = numpy.apply_along_axis(normify, 0, ea_shape0)
loc_params = ['m2','x','y']
ea_loc = tf.do_event_array(el,['m2','x','y'])
x_min, x_max = ea_loc[:, 1].min() , ea_loc[:, 1].max() +1
y_min, y_max = ea_loc[:, 2].min() , ea_loc[:, 2].max() +1
#print x_min, x_max, y_min, y_max
xx,yy = numpy.meshgrid(numpy.arange(x_min,x_max), numpy.arange(y_min, y_max))
#print xx,yy
#print xx.shape, yy.shape
z = numpy.ones_like(xx)
for x,y,a in zip(ea_loc[:,1], ea_loc[:,2],ea_shape0[:,0]):
    if z[y,x]==1.0:
        z[y,x]=a
#print z
#mlab.points3d(ea_loc[:,1],ea_loc[:,2],100*ea_shape0[:,0])
mlab.surf(xx.T,yy.T,z, warp_scale='auto',representation='surface',colormap='hot')
mlab.colorbar()
#mlab.contour_surf(xx.T,yy.T,z,warp_scale=10)
#ea_loc = numpy.apply_along_axis(normify, 0, ea_loc)

#mlab.show()
#s.close()
#sys.exit(0)

#print ea_loc.shape
#import pylab
#pylab.figure()
#pylab.plot(ea_loc[:,0],ea_loc[:,1],'o', alpha=0.3)
#pylab.figure()
#pylab.plot(ea_loc[:,0],ea_loc[:,2],'o', alpha=0.3)
#pylab.figure()
#pylab.plot(ea_loc[:,1],ea_loc[:,2],'o', alpha=0.3)
#pylab.show()
#import sys
#sys.exit(0)

#ea_loc = numpy.apply_along_axis(normify, 0, ea_loc)

#mlab.figure()
#first = 0
#second = 1
#third = 2
#mlab.points3d(ea_shape[:,first],ea_shape[:,second],ea_shape[:,third],scale_factor=.2, resolution=8, opacity=0.05,color=(1.0,0,0))
#mlab.outline()
#mlab.axes(opacity=0.5, xlabel=shape_params[first], ylabel = shape_params[second], zlabel=shape_params[third])
##mlab.title("Initial shape parameters")
#
mlab.figure()
first = 0
second = 1
third = 2
mlab.points3d(ea_loc[:,first],ea_loc[:,second],ea_loc[:,third],scale_factor=2, resolution=8, opacity=0.05,color=(1.0,0,0))
mlab.outline()
mlab.axes(opacity=0.5, xlabel=loc_params[first], ylabel = loc_params[second], zlabel=loc_params[third])
#mlab.title("Initial locationn parameters")
##
mlab.show()
from sklearn.cluster import DBSCAN
from sklearn import metrics

def cluster(data, eps=2.0, min_samples=100):
    #D = metrics.euclidean_distances(data)
    #S = 1 - (D / numpy.max(D))
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(data)
    core_samples = db.core_sample_indices_
    labels = db.labels_
    # Number of clusters in labels, ignoring noise if present.
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print "Clusters: ",n_clusters
    return labels, core_samples


def plot_res(ls, ea_data, loc_params, only = None):
    colornames = cycle(['red', 'green', 'blue', 'yellow', 'orange', 'teal', 'magenta', 'lime', 'navy', 'brown'])
    mlab.figure(size=(800,600))
    drange = ea_data.max()-ea_data.min()
    gsize = numpy.sqrt(drange)/10
    new_data = None
    for k, colorn in zip(set(ls), colornames):
        if only and k not in only:
            continue
        members = numpy.argwhere(ls == k).flatten()

        if k==-1:
            color=(0,0,0)
            gsize/=2
            #continue
        else:
            color = tuple((numpy.array(webcolors.name_to_rgb(colorn))/255.).tolist())
        #print k, len(members)

        data = ea_data[members]
        if new_data is None:
            new_data = data.copy()
        else:
            new_data = numpy.vstack((new_data, data))
        mlab.points3d(data[:,first],data[:,second],data[:,third],scale_factor=gsize, resolution=8, opacity=0.15,color=color)
    ea_data = new_data
    mlab.outline(extent=[ea_data[:,first].min(), ea_data[:,first].max(), ea_data[:,second].min(), ea_data[:,second].max(), ea_data[:,third].min(), ea_data[:,third].max()])
    mlab.axes(opacity=0.5, xlabel=loc_params[first], ylabel = loc_params[second], zlabel=loc_params[third], ranges=[ea_data[:,first].min(), ea_data[:,first].max(), ea_data[:,second].min(), ea_data[:,second].max(), ea_data[:,third].min(), ea_data[:,third].max()])
    #mlab.show()

ls,cs = cluster(ea_shape,eps=2.0, min_samples=50)
first = 0
second = 1
third = 2
shape_groups={}
print "\n clusters by shape"
for k in set(ls):
    members = numpy.argwhere(ls == k).flatten()
    shape_groups[k] = members
shape_ls = ls
#plot_res(ls,ea_shape,loc_params)
clusters = defaultdict(dict)
labels = {}
for group in shape_groups:
#if 1:
    indices = shape_groups[group]
    sh_data = ea_shape0[indices]
    print "group %i"%group, numpy.mean(sh_data,axis=0)
    data=ea_loc[indices]
    #data = ea_loc
    data[:,0]=data[:,0]*1
    if group == -1:
        continue
    print numpy.apply_along_axis(numpy.min, 0, data)
    print numpy.apply_along_axis(numpy.max, 0, data)
    #data = numpy.apply_along_axis(normify, 0, data)
    #print numpy.apply_along_axis(numpy.min, 0, data)
    #print numpy.apply_along_axis(numpy.max, 0, data)
    #ls,cs = cluster(data,eps=0.25, min_samples=15)
    ls,cs = cluster(data,eps=2.5, min_samples=15)
    for k in set(ls):
        members = numpy.argwhere(ls == k).flatten()
        clusters[group][k] = data[members]
    #print group, set(ls)
    #print data
    labels[group] = ls
    #plot_res(ls,data,loc_params)
#print 'clusters',clusters
sgi=0
spark_bad = clusters[sgi][-1]

#Find events that were previously classified as outliers and redo clustering
#with a dataset where each cluster is combined with the 'bad' events
for c in clusters[sgi]:
    print '\nevent', c
    if c==-1:
        continue
    spark = clusters[sgi][c]
    spark_cluster = spark

    alld=numpy.vstack((spark_cluster,spark_bad))
    ls,cs = cluster(alld,eps=3.5, min_samples=15)
    for k in set(ls):
        if k  == -1:
            continue
        members = numpy.argwhere(ls == k).flatten()
        right_one = alld[members[0]].tolist() == spark_cluster[0].tolist()
        from_bad = members[spark_cluster.shape[0]:] - spark_cluster.shape[0]
        #print k, len(members),right_one,from_bad

        if right_one:
            print 'original size ', spark.shape[0]
            print 'new size ',spark.shape[0]+from_bad.shape[0]
            #mark bad labels as new groups
            for b in spark_bad[from_bad]:
                ii = numpy.argwhere((ea_loc[shape_groups[sgi]]==b).all(axis=1))
                labels[sgi][ii] = c
        #    plot_res(ls, alld, loc_params,only=[k])

plot_res(labels[sgi],ea_loc[shape_groups[sgi]],loc_params)


z = numpy.ones_like(xx)
#z = numpy.zeros_like(xx)
good_l=ea_loc[shape_groups[sgi]]
good_s=ea_shape0[shape_groups[sgi]]
z = None
#for l,x,y,i in zip(labels[sgi],good_l[:,1], good_l[:,2],shape_groups[sgi]):
for x,y,i in zip(good_l[:,1], good_l[:,2],shape_groups[sgi]):
    l = shape_ls[i]
    #pixel = pixels[i]
    event = el[i].copy()
    pixel = event['pixel']
    event_no = event['n']
    #print pixel, pixel.event_count
    if l==-1:
        continue
    if pixel.event_count:
        if z is None:
            duration = tf.fitted_pixel_ff0(pixel,event_no)
            shape = [len(duration)]
            shape.extend(xx.shape)
            z = numpy.ones(shape)
        z[:,y,x] = tf.fitted_pixel_ff0(pixel)
        #print x,y,z[:,y,x]

#print z.shape
#import pylab
#pylab.plot(z[:,10,50])
#pylab.show()
#sys.exit(0)
#mlab.figure( size=(800,600))
#l = mlab.surf(xx.T,yy.T,z[0], warp_scale=10,representation='surface',colormap='hot')
#ms=l.mlab_source
#@mlab.animate
#def animate():
#    i = 0
#    while 1:
#        #print "frame",i
#        i+=1
#        i=i%400
#        #i=i%117
#
#        #print z[i].shape, z[i].mean(),z[i].max()
#        ms.scalars=z[i]
#        yield
#a=animate()
#mlab.show()
#mlab.colorbar()

#import pylab
#pylab.imshow(z[50])
#pylab.show()

#z = numpy.zeros_like(xx)
#for l,x,y,a,i in zip(labels[sgi],good_l[:,1], good_l[:,2], good_s[:,0],shape_groups[sgi]):
#    event = el[i].copy()
#    del event['x']
#    del event['y']
#    del event['pixel']
#    del event['n']
#    t = numpy.array([50.0])
#    a = fitfun.ff6(t, **event)
#    if l!=-1:
#        z[y,x]=a

#import pylab
#pylab.imshow(z)
#pylab.show()
#print z
#mlab.points3d(ea_loc[:,1],ea_loc[:,2],100*ea_shape0[:,0])
#mlab.figure(size=(800,600))
#mlab.surf(xx.T,yy.T,z, warp_scale='auto',representation='surface',colormap='hot')
#mlab.colorbar()

mlab.show()
s.close()


