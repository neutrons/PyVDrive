#!/usr/bin/python
#pylint: disable=invalid-name
"""
    Script used to start the VDrive reduction GUI from MantidPlot
"""
import sys
import os

# a fix to iPython console
home_dir = os.path.expanduser('~')
if home_dir.startswith('/home/wzz') is False:
    # Mac debug build
    sys.path.append('/Users/wzz/MantidBuild/debug/bin')
    # Analysis cluster build
    sys.path.append('/SNS/users/wzz/Mantid_Project/vulcan-build/bin/')

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
        exit the application
        :return:
        """
        self.close()

        return

    def do_launch_chopper(self):
        """
        launch the log picker window
        :return:
        """
        self._mainReducerWindow.do_launch_log_picker_window()

        if not self.ui.checkBox_keepOpen.isChecked():
            self.close()

        return

    def do_launch_peak_picker(self):
        """
        launch peak picker window
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
        launch the main VDrivePlot window
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

# get arguments
args = sys.argv
if len(args) == 2:
    option = args[1]
else:
    option = None

app = lava_app()

launcher = LauncherManager()
launcher.show()

if isinstance(option, str) and option.lower().startswith('t'):
    launcher.do_launch_terminal()
    launcher.close()

app.exec_()
