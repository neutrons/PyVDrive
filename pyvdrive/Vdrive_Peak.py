#!/usr/bin/python
# pylint: disable=invalid-name
"""
    Script used to start the VDrive reduction GUI from MantidPlot
"""
import sys

# a fix to iPython console
import pyvdrive.interface.config
if pyvdrive.interface.config.DEBUG:
    from pyvdrive.interface.gui.mantidipythonwidget import MantidIPythonWidget
    print(MantidIPythonWidget)

from PyQt4 import QtGui

from pyvdrive.interface.VDrivePlot import VdriveMainWindow
import pyvdrive.interface.PeakPickWindow as PeakPickWindow


def lava_app():
    if QtGui.QApplication.instance():
        _app = QtGui.QApplication.instance()
    else:
        _app = QtGui.QApplication(sys.argv)
    return _app


app = lava_app()

reducer = VdriveMainWindow()  # the main ui class in this file is called MainWindow

peakPickerWindow = PeakPickWindow.PeakPickerWindow(reducer)
peakPickerWindow.set_controller(reducer.get_controller())
peakPickerWindow.show()

app.exec_()
