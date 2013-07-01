#from pylab import *
if __name__=="__main__":
    import pylab
    from resources import cm
    from numpy import outer,arange,ones
    pylab.rc('text', usetex=False)
    a=outer(arange(0,1,0.01),ones(10))
    #maps=[m for m in cm.datad if not m.endswith("_r")]
    maps=cm.datad.keys()
    maps.sort()
    for i, m in enumerate(maps):
        pylab.figure(figsize=(10,1))
        pylab.subplots_adjust(top=1.0,bottom=0.00,left=0.00,right=1.0)
        pylab.axis("off")
        colormap = pylab.cm.get_cmap(m)
        print colormap
        pylab.imshow(a.transpose(),cmap=colormap)
        pylab.savefig("pics/colormap_%s.png"%m,dpi=20)
        print m
