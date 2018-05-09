#!/usr/bin/python
# Test the chop and reduce command
import sys
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

    chop_cmd01 = "CHOP, IPTS=13924, RUNS=160989, dbin=60,loadframe=1,bin=1,DRYRUN=0, output='/tmp/'"
    command_tester.run_command(chop_cmd01)
    chop_cmd02 = "CHOP, IPTS=19577, RUNS=155771, dbin=60,loadframe=1,bin=1,DRYRUN=0, output='/tmp/x/'"
    # command_tester.run_command(chop_cmd02)

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


# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 218.696499109   Total output workspaces = 733
# Details for thread = 16:
# 	Loading  = 59.3131201267
# 	Chopping = 70.8570668697
# 	Focusing = 88.5263121128

