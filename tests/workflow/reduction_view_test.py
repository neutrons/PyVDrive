#!/usr/bin/python
# Test the chop and reduce command
import syss
import command_test_setup
try:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    print ('PyQt4 will be imported')
    from PyQt4.QtGui import QApplication


def test_main():
    """
    test main
    """
    main_window = VdriveMainWindow(None)
    data_view_window = main_window.do_launch_reduced_data_viewer()

    return data_view_window


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
    test_window.load_preprocess_nexus(file_name='.nxs')
    # I cannot close it!  test_window.close()

    app.exec_()
