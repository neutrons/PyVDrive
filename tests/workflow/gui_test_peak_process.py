#!/usr/bin/python
# Test the chop and reduce command
import os
import sys
from pyvdrive.interface.VDrivePlot import VdriveMainWindow
try:
    from PyQt5.QtWidgets import QApplication
except (ImportError, RuntimeError) as import_error:
    print ('[ild_vbin_test] Import PyQt5/qtconsole Error: {}'.format(import_error))
    from PyQt4.QtGui import QApplication


class PeakProcessingGUITestEnvironment(object):
    """
    PyVDrive commands testing environment
    """
    def __init__(self):
        """
        initialization
        """
        self._main_window = VdriveMainWindow(None)
        self._peak_process_window = self._main_window.do_launch_peak_process_window()

        return

    @property
    def main_window(self):
        """
        return the main window's handler
        :return:
        """
        return self._peak_process_window

    def load_gsas(self, ipts_number=None, run_number=None):
        """

        :return:
        """
        if ipts_number is not None:
            self._peak_process_window.ui.lineEdit_iptsNumber.setText('{}'.format(ipts_number))
        if run_number is not None:
            self._peak_process_window.ui.lineEdit_runNumber.setText('{}'.format(run_number))

        self._peak_process_window.do_load_data()

        return

    def set_ipts_run(self, ipts_number, run_number):
        """

        :param ipts_number:
        :param run_number:
        :return:
        """
        # self._slice_window.ui.lineEdit_iptsNumber.setText('{}'.format(22126))
        # self._slice_window.ui.lineEdit_runNumber.setText('{}'.format(171898))

        self._peak_process_window.ui.lineEdit_iptsNumber.setText('{}'.format(22126))
        self._peak_process_window.ui.lineEdit_runNumber.setText('{}'.format(171899))

        self._peak_process_window.do_load_run()

        return

    def vanadium_test(self):
        """

        :return:
        """
        # /SNS/VULCAN/IPTS-22752/nexus/VULCAN_171966.nxs.h5
        self.load_gsas(22752, 171966)


def test_main():
    """
    test main
    """
    peak_process_ui_test = PeakProcessingGUITestEnvironment()

    if False:  # simple use case test: disabled now
        # simple test:
        peak_process_ui_test.load_gsas()

    # Vanadium processing test
    peak_process_ui_test.vanadium_test()

    return peak_process_ui_test.main_window


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
    print ('Test PyVDrive-Slice-Assistant-UI')
    app = main(sys.argv)

    # this must be here!
    test_window = test_main()
    test_window.show()
    # I cannot close it!  test_window.close()

    app.exec_()
