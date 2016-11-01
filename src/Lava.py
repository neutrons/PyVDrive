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

        # init widgets
        self.ui.checkBox_keepOpen.setChecked(True)

        # define event handlers
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_exit)
        self.connect(self.ui.pushButton_vdrivePlot, QtCore.SIGNAL('clicked()'),
                     self.do_launch_vdrive)
        self.connect(self.ui.pushButton_choppingHelper, QtCore.SIGNAL('clicked()'),
                     self.do_launch_chopper)
        self.connect(self.ui.pushButton_peakProcessing, QtCore.SIGNAL('clicked()'),
                     self.do_launch_peak_picker)
        self.connect(self.ui.pushButton_terminal, QtCore.SIGNAL('clicked()'),
                     self.do_launch_terminal)

        # initialize main window (may not be shown though)
        self._mainReducerWindow = VdriveMainWindow()  # the main ui class in this file is called MainWindow

        self._myPeakPickerWindow = None
        self._myLogPickerWindow = None

        return

    def do_exit(self):
        """
        blabla
        :return:
        """
        self.close()

        return

    def do_launch_chopper(self):
        """
        blabla
        :return:
        """
        import interface.LogPickerWindow as LP

        self._myLogPickerWindow = LP.WindowLogPicker(self._mainReducerWindow)

        self._myLogPickerWindow.show()

        if not self.ui.checkBox_keepOpen.isChecked():
            self.close()

        return

    def do_launch_peak_picker(self):
        """
        blabla
        :return:
        """
        import interface.PeakPickWindow as PeakPickWindow

        self._myPeakPickerWindow = PeakPickWindow.PeakPickerWindow(self._mainReducerWindow)
        self._myPeakPickerWindow.set_controller(self._mainReducerWindow.get_controller())
        self._myPeakPickerWindow.show()

        if not self.ui.checkBox_keepOpen.isChecked():
            self.close()

        return

    def do_launch_terminal(self):
        """

        :return:
        """
        self._mainReducerWindow.menu_workspaces_view()

        if not self.ui.checkBox_keepOpen.isChecked():
            self.close()

        return

    def do_launch_vdrive(self):
        """
        blabla
        :return:
        """
        self._mainReducerWindow.show()

        if not self.ui.checkBox_keepOpen.isChecked():
            self.close()

        return

# END-DEFINITION (class)


# Main application
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
