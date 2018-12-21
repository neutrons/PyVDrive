#!/usr/bin/python
# Test the IDL-like command INFO
import sys
import command_test_setup
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt4.QtGui import QApplication



def test_help(command_tester):
    """
    no argument for help information
    :param command_tester:
    :return:
    """
    command_line = 'INFO'
    command_tester.run_command(command_line)

    return


def test_case_duration(command_tester):
    """
    test viewing data from archive with multiple reduced runs
    :return:
    """
    # command_line = 'INFO,IPTS=14094,RUNS=96450, DURATION=1, -n=30'
    command_line = 'INFO, IPTS=21356, DURATION=1, -n=40'
    command_tester.run_command(command_line)

    return


def test_main():
    """
    test main for command VIEW
    """
    command_tester = command_test_setup.PyVdriveCommandTestEnvironment()

    test_case_duration(command_tester)

    return command_tester.main_window


def main(argv):
    """ main to define QApplication
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

    app.exec_()
