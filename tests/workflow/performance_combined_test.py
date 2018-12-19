#!/usr/bin/python
# Performance test: test a combined set of commands of VBIN, CHOP, VPEAK and MERGE
import os
import sys
import command_test_setup
try:
    import qtconsole.inprocess
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication



def test_vbin_chop_simple():
    """
    Test a set of commands including VBIN, CHOP
    Data will be relatively smaller in order to test potential conflict
    :return:
    """
    #
    # run: VBIN,IPTS=20280,RUNS=169186, output='/tmp/'
    # run: chop, ipts=20717, runs=170464, dbin=30, loadframe=1, output='/tmp'



def test_main():
    """
    test main
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    test_vbin_chop_simple(command_tester)

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
