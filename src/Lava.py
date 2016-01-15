#!/usr/bin/python
#pylint: disable=invalid-name
"""
    Script used to start the VDrive reduction GUI from MantidPlot
"""
import sys
from PyQt4 import QtGui

#vdrive_path = os.path.expanduser('~/Projects/PyVDrive/PyVDrive/src')
#sys.path.append(vdrive_path)

from interface.VDrivePlot import VdriveMainWindow


def lava_app():
    if QtGui.QApplication.instance():
        _app = QtGui.QApplication.instance()
    else:
        _app = QtGui.QApplication(sys.argv)
    return _app

app = lava_app()

reducer = VdriveMainWindow()  # the main ui class in this file is called MainWindow
reducer.show()
app.exec_()
