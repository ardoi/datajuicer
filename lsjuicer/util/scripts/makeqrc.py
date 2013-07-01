import glob
import os
pngs = glob.glob('../../../lib/pics/*.png')
fname = "../../../lib/resources.qrc"
f = open(fname,'w')
f.write("""<!DOCTYPE RCC><RCC version = "1.0">\n""")
f.write("""<qresource>\n""")
for png in pngs:
    name = os.path.basename(png)
    f.write('<file alias="%s">pics/%s</file>\n'%(name,name))
f.write("""</qresource>\n""")
f.write("""</RCC>\n""")
f.close()
