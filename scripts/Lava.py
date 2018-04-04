#!/usr/bin/python
import sys
sys.path.append('/SNS/users/wzz/.local//lib/python2.7/site-packages')

import pyvdrive
from pyvdrive.interface.gui.mantidipythonwidget import MantidIPythonWidget
import os
try:
    from PyQt5 import QtCore as QtCore
    from PyQt5.QtWidgets import QDialog, QApplication
except ImportError:
    from PyQt4 import QtCore as QtCore
    from PyQt4.QtGui import QDialog, QApplication

from pyvdrive.interface.gui import ui_LaunchManager_ui
from pyvdrive.interface.VDrivePlot import VdriveMainWindow
import pyvdrive.interface.LiveDataView
import pyvdrive.interface.PeakPickWindow as PeakPickWindow
import pyvdrive.interface.ExperimentRecordView as ev

#  Script used to start the VDrive reduction GUI from MantidPlot

# a fix to iPython console
home_dir = os.path.expanduser('~')
if home_dir.startswith('/home/wzz') is False:
    # Mac debug build
    sys.path.append('/Users/wzz/MantidBuild/debug-stable/bin')
    # Analysis cluster build
    # sys.path.append('/SNS/users/wzz/Mantid_Project/builds/build-vulcan/bin')
    # sys.path.append('/opt/mantidnightly/bin')
    sys.path.append('/SNS/users/wzz/Mantid_Project/builds/debug/bin')


class LauncherManager(QDialog):
    """
    Launcher manager
    """
    def __init__(self):
        """

        """
        super(LauncherManager, self).__init__(None)

        # set up UI
        self.ui = ui_LaunchManager_ui.Ui_Dialog_Launcher()
        self.ui.setupUi(self)

        # init widgets
        self.ui.checkBox_keepOpen.setChecked(True)

        # define event handlers
        self.ui.pushButton_quit.clicked.connect(self.do_exit)
        self.ui.pushButton_vdrivePlot.clicked.connect(self.do_launch_vdrive)
        self.ui.pushButton_choppingHelper.clicked.connect(self.do_launch_chopper)
        self.ui.pushButton_peakProcessing.clicked.connect(self.do_launch_peak_picker)
        self.ui.pushButton_reducedDataViewer.clicked.connect(self.do_launch_viewer)
        self.ui.pushButton_terminal.clicked.connect(self.do_launch_terminal)

        # self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
        #              self.do_exit)
        # self.connect(self.ui.pushButton_vdrivePlot, QtCore.SIGNAL('clicked()'),
        #              self.do_launch_vdrive)
        # self.connect(self.ui.pushButton_choppingHelper, QtCore.SIGNAL('clicked()'),
        #              self.do_launch_chopper)
        # self.connect(self.ui.pushButton_peakProcessing, QtCore.SIGNAL('clicked()'),
        #              self.do_launch_peak_picker)
        # self.connect(self.ui.pushButton_reducedDataViewer, QtCore.SIGNAL('clicked()'),
        #              self.do_launch_viewer)
        # self.connect(self.ui.pushButton_terminal, QtCore.SIGNAL('clicked()'),
        #              self.do_launch_terminal)

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

    def do_launch_live_view(self, auto_start):
        """ launch live view
        :param auto_start: flag to start the live view automatically
        :return:
        """
        live_view = pyvdrive.interface.LiveDataView.VulcanLiveDataView(self._mainReducerWindow, None)

        live_view.show()
        # start live
        live_view.do_start_live()

        return live_view

    def do_launch_peak_picker(self):
        """
        launch peak picker window
        :return:
        """

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

    def do_launch_record_view(self):
        """launch the experimental record viewer
        :return:
        """

        viewer = ev.VulcanExperimentRecordView(self)
        viewer.show()

        return

    def do_launch_viewer(self):
        """
        launch reduced data view
        :return:
        """
        self._mainReducerWindow.do_launch_reduced_data_viewer()

        if not self.ui.checkBox_keepOpen.isChecked():
            self.close()

        return


# END-DEFINITION (class)


# Main application
def lava_app():
    if QApplication.instance():
        _app = QApplication.instance()
    else:
        _app = QApplication(sys.argv)
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

if option is None:
    pass

elif isinstance(option, str) and (option.lower().startswith('-h') or option.lower().startswith('--h')):
    print 'Options:'
    print '  -t: launch IPython terminal'
    print '  -c: launch chopping/slicing interface'
    print '  -p: launch peak processing interface'
    print '  -v: launch reduced data view interface'
    print '  --live: launch live data view interface in auto mode'
    print '  --live-prof: launch live data view interface in professional mode'
    print '  --record: launch experimental record manager'
    sys.exit(1)

elif option.lower() == '-m':
    launcher.do_launch_vdrive()
    launcher.close()

elif isinstance(option, str) and option.lower() == '-t':
    launcher.do_launch_terminal()
    launcher.close()

elif isinstance(option, str) and option.lower().startswith('-c'):
    launcher.do_launch_chopper()
    launcher.close()

elif isinstance(option, str) and option.lower().startswith('-p'):
    launcher.do_launch_peak_picker()
    launcher.close()

elif isinstance(option, str) and option.lower().startswith('-v'):
    launcher.do_launch_viewer()
    launcher.close()

elif isinstance(option, str) and option.lower().count('t') and option.lower().count('c'):
    launcher.do_launch_chopper()
    launcher.do_launch_terminal()
    launcher.close()

elif isinstance(option, str) and option.lower().startswith('--live'):
    # live view widget
    auto_start = option.lower().count('prof') == 0
    launcher.do_launch_live_view(auto_start)
    launcher.close()

elif isinstance(option, str) and option.lower().startswith('--record'):
    launcher.do_launch_record_view()
    launcher.close()


app.exec_()
