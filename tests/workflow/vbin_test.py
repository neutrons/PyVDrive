#!/usr/bin/python
# Test the chop and reduce command
import sys
# from pyvdrive.lib import *
# from pyvdrive.interface import *
# from pyvdrive.interface.vdrive_commands import *
# from pyvdrive.interface.VDrivePlot import VdriveMainWindow
try:
    import qtconsole.inprocess
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication

# create main application
import command_test_setup


def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    cmd = "VBIN,IPTS=14094,RUNS=96450, output='/home/wzz/Temp'"
    command_tester.run_command(cmd)

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

