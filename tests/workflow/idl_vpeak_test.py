#!/usr/bin/python
# Test the chop and reduce command
import os
import sys
import command_test_setup
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication

# create main application
from command_test_setup import set_test_dir


def test_pre_ned(tester):
    """
    """
    # create chop
    test_dir = '/tmp/choptest2/'
    set_test_dir(test_dir)

    command = "VPEAK,ITPS=16062,RUNV=98237,SHIFT=1, output='/tmp'"
    tester.run_command(command)

    return


def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    test_pre_ned(command_tester)

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
    print ('Test PyVDrive-Commands: VPEAK')
    app = main(sys.argv)

    # this must be here!
    test_window = test_main()
    test_window.show()
    # I cannot close it!  test_window.close()

    app.exec_()

