find . -type f -name "*.py"|xargs gsed -i -e 's|import PyQt4\.QtGui as QG|from PyQt4 import QtGui|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|import PyQt4\.QtCore as QC|from PyQt4 import QtCore|g'
find . -type f -name "*.py"|xargs sed -i "" -e 's|QG\.Q|QtGui\.Q|g'
find . -type f -name "*.py"|xargs sed -i "" -e 's|QC\.Q|QtCore\.Q|g'
mv lsjuicer/resources/resources.py lsjuicer/resources/resources.pyc
python pyqt4topyqt5.py lsjuicer  --diff out.diff

find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtGui as QG, QtWidgets|from PyQt5 import QtGui\nfrom PyQt5 import QtWidgets|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtCore as QC, QtWidgets|from PyQt5 import QtCore as QC|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtWidgets|from PyQt5 import QtWidgets as QW|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtGui|from PyQt5 import QtGui as QG|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|QtGui\.Q|QG\.Q|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|QtWidgets\.Q|QW\.Q|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtGui as QG, QtWidgets|from PyQt5 import QtGui as QG\nfrom PyQt5 import QtWidgets as QW|g'
mv lsjuicer/resources/resources.pyc lsjuicer/resources/resources.py
rsync -rtvuc lsjuicer_PyQt5/ lsjuicer/

find . -type f -name "*.py"|xargs sed -i "" -e 's|QtGui\.Q|QG\.Q|g'
find . -type f -name "*.py"|xargs sed -i "" -e 's|QtCore\.Q|QC\.Q|g'

find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtGui as QG as QG|from PyQt5 import QtGui as QG|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtCore as QC as QC|from PyQt5 import QtCore as QC|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtWidgets as QW as QW|from PyQt5 import QtWidgets as QW|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtCore, QtWidgets|from PyQt5 import QtCore as QC|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|from PyQt5 import QtCorex|from PyQt5 import QtCore as QC|g'


find . -type f -name "*.py"|xargs gsed -i -e 's|self.layoutAboutToBeChanged.emit()|self.layoutAboutToBeChanged.emit((),0)|g'
find . -type f -name "*.py"|xargs gsed -i -e 's|self.layoutAboutToBeChanged.emit((),0)|self.layoutAboutToBeChanged.emit()|g'