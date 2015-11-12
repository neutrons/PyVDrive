#pylint: disable=invalid-name
"""
    Script used to start the DGS reduction GUI from MantidPlot
"""
import sys
import os
from PyQt4 import QtGui

#vdrive_path = os.path.expanduser('~/Projects/PyVDrive/PyVDrive/src')
#sys.path.append(vdrive_path)

from VDrivePlot import VDrivePlotBeta

def qapp():
    if QtGui.QApplication.instance():
        _app = QtGui.QApplication.instance()
    else:
        _app = QtGui.QApplication(sys.argv)
    return _app

app = qapp()

reducer = VDrivePlotBeta() #the main ui class in this file is called MainWindow
reducer.show()
app.exec_()
