#!/usr/bin/python
import sys
import pyvdrive
from pyvdrive.interface.gui.mantidipythonwidget import MantidIPythonWidget
import os
try:
    from PyQt5 import QtCore as QtCore
    from PyQt5.QtWidgets import QDialog, QApplication
    from PyQt5.uic import loadUi as load_ui
except ImportError:
    from PyQt4 import QtCore as QtCore
    from PyQt4.QtGui import QDialog, QApplication
    from PyQt4.uic import loadUi as load_ui

# from pyvdrive.interface.gui import ui_LaunchManager
from pyvdrive.interface.VDrivePlot import VdriveMainWindow
import pyvdrive.interface.LiveDataView
import pyvdrive.interface.PeakPickWindow as PeakPickWindow
import pyvdrive.interface.ExperimentRecordView as ev

#  Script used to start the VDrive reduction GUI from MantidPlot


class LauncherManager(QDialog):
    """
    Launcher manager
    """
    def __init__(self):
        """

        """
        super(LauncherManager, self).__init__(None)

        # set up UI: it is tricky
        script_dir = os.path.dirname(__file__)
        dir_names = os.listdir('{}/..'.format(script_dir))
        lib_dir = None
        for dir_name in dir_names:
            if dir_name.startswith('lib'):
                lib_dir = dir_name
        ui_dir = os.path.join(script_dir, '../{}/pyvdrive/interface/gui'.format(lib_dir))
        ui_path = os.path.join(ui_dir, 'LaunchManager.ui')
        self.ui = load_ui(ui_path, baseinstance=self)

        # init widgets
        self.ui.checkBox_keepOpen.setChecked(True)

        # define event handlers
        self.ui.pushButton_quit.clicked.connect(self.do_exit)
        self.ui.pushButton_vdrivePlot.clicked.connect(self.do_launch_vdrive)
        self.ui.pushButton_choppingHelper.clicked.connect(self.do_launch_chopper)
        self.ui.pushButton_peakProcessing.clicked.connect(self.do_launch_peak_picker)
        self.ui.pushButton_reducedDataViewer.clicked.connect(self.do_launch_viewer)
        self.ui.pushButton_terminal.clicked.connect(self.do_launch_terminal)

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

        self._myPeakPickerWindow = PeakPickWindow.PeakPickerWindow(self._mainReducerWindow,
                self._mainReducerWindow.get_controller())
        # self._myPeakPickerWindow.set_controller(self._mainReducerWindow.get_controller())
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
    option = '-t'
if isinstance(option, str):
    option = option.lower()
else:
    print('Lava option must be a string.  Execute "lava --help" for help')
    sys.exit(-1)

app = lava_app()

launcher = LauncherManager()
launcher.show()


if option in ['-h', '--help']:
    print('Options:')
    print('  -t: launch IPython terminal')
    print('  -c: launch chopping/slicing interface')
    print('  --view (-v): launch reduced data view interface')
    print('  --peak (-p): launch peak processing interface')
    print('  --main (-m): launch main PyVDrive GUI control panel')
    print('  --live (-l): launch live data view interface in auto mode')
    print('  --live-prof: launch live data view interface in professional mode')
    print('  --record: launch experimental record manager')
    sys.exit(1)

elif option in ['-v', '--view']:
    launcher.do_launch_vdrive()
    launcher.close()

elif option in ['-t']:
    launcher.do_launch_terminal()
    launcher.close()

elif option in ['-c']:
    launcher.do_launch_chopper()
    launcher.close()

elif option in ['-p', '--peak']:
    launcher.do_launch_peak_picker()
    launcher.close()

elif option in ['-v', '--view']:
    launcher.do_launch_viewer()
    launcher.close()

elif option in ['--live', '-l']:
    # live view widget
    auto_start = option.lower().count('prof') == 0
    launcher.do_launch_live_view(auto_start)
    launcher.close()

elif option in ['--record']:
    launcher.do_launch_record_view()
    launcher.close()

app.exec_()
