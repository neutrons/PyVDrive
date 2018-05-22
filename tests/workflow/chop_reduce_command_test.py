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



# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 251.323285103   Total output workspaces = 733
# Details for thread = 8:
# 	Loading  = 92.1773381233
# 	Chopping = 35.1145699024
# 	Focusing = 79.9583420753
# 	SaveGSS = 44.0730350018
# ********* SEGMENTATION FAULT *********

# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 255.423187971   Total output workspaces = 733
# Details for thread = 16:
# 	Loading  = 91.5541679859
# 	Chopping = 35.390401125
# 	Focusing = 82.6177368164
# 	SaveGSS = 45.8608820438

# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 256.438976049   Total output workspaces = 733
# Details for thread = 32:
# 	Loading  = 92.5543420315
# 	Chopping = 35.9679849148
# 	Focusing = 84.067358017
# 	SaveGSS = 43.8492910862


# /SNS/VULCAN/IPTS-19577/nexus/VULCAN_155771.nxs.h5: Runtime = 269.704912901   Total output workspaces = 733
# Details for thread = 12:
# 	Loading  = 91.6898329258
# 	Chopping = 35.2826209068
# 	Focusing = 97.724822998
# 	SaveGSS = 45.0076360703
