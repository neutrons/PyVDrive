#!/usr/bin/python
#pylint: disable=invalid-name
"""
    Script used to start the VDrive reduction GUI from MantidPlot
"""
import sys

# a fix to iPython console
from interface.gui.mantidipythonwidget import MantidIPythonWidget
from PyQt4 import QtGui, QtCore

from interface.gui import ui_LaunchManager
from interface.VDrivePlot import VdriveMainWindow


class LauncherManager(QtGui.QDialog):
    """
    Launcher manager
    """
    def __init__(self):
        """

        """
        super(LauncherManager, self).__init__(None)

        # set up UI
        self.ui = ui_LaunchManager.Ui_Dialog_Launcher()
        self.ui.setupUi(self)

        # define event handlers
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_exit)
        self.connect(self.ui.pushButton_vdrivePlot, QtCore.SIGNAL('clicked()'),
                     self.do_launch_vdrive)
        self.connect(self.ui.pushButton_peakProcessing, QtCore.SIGNAL('clicked()'),
                     self.do_launch_peak_picker)
        self.connect(self.ui.pushButton_terminal, QtCore.SIGNAL('clicked()'),
                     self.do_launch_terminal)

        return

    def do_exit(self):
        """
        blabla
        :return:
        """
        self.close()

    def do_launch_peak_picker(self):
        """
        blabla
        :return:
        """
        import interface.PeakPickWindow as PeakPickWindow
        reducer = VdriveMainWindow()  # the main ui class in this file is called MainWindow

        peakPickerWindow = PeakPickWindow.PeakPickerWindow(reducer)
        peakPickerWindow.set_controller(reducer.get_controller())
        peakPickerWindow.show()

        self.close()

        return

    def do_launch_terminal(self):
        """

        :return:
        """
        reducer = VdriveMainWindow()  # the main ui class in this file is called MainWindow
        reducer.menu_workspaces_view()

        self.close()

        return

    def do_launch_vdrive(self):
        """
        blabla
        :return:
        """
        reducer = VdriveMainWindow()  # the main ui class in this file is called MainWindow
        reducer.show()

        self.close()

        return


def lava_app():
    if QtGui.QApplication.instance():
        _app = QtGui.QApplication.instance()
    else:
        _app = QtGui.QApplication(sys.argv)
    return _app

app = lava_app()

launcher = LauncherManager()
launcher.show()

app.exec_()
