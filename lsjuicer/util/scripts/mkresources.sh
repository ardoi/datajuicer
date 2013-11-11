#!/bin/bash
#create resources.qrc based on images in lib/pics
python2 makeqrc.py
cd ../../../lib
#generate resources.py
pyrcc5 -o resources.py resources.qrc
cd ..
#move generated resources.py to resources folder
rm lsjuicer/ui/resources/resources.py*
mv lib/resources.py lsjuicer/ui/resources/
