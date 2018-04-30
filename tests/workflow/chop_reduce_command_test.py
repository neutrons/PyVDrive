#!/usr/bin/python
# Test the chop and reduce command
import sys
from pyvdrive.lib import *
from pyvdrive.interface import *
from pyvdrive.interface.vdrive_commands import *
from pyvdrive.interface.VDrivePlot import VdriveMainWindow
from PyQt5.QtWidgets import QApplication

# create main application
import command_test_setup


def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    command_tester.run_command('chop, ipts=????, runs=????, delta_time=????, output=????')

    return command_tester.main_window


def main(argv):
    """
    """
    if QApplication.instance():
        _app = QApplication.instance()
    else:
        _app = QApplication(sys.argv)
    return _app

if __name__ == '__main__':
    # Main application
    print ('Test PyVDrive-Commands')
    app = main(sys.argv)

    # this must be here!
    test_window = test_main()
    test_window.show()
    # I cannot close it!  test_window.close()

    app.exec_()
