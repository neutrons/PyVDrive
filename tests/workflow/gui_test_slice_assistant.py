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


class EventFilteringAssistantTestEnvironment(object):
    """
    PyVDrive commands testing environment
    """
    def __init__(self):
        """
        initialization
        """
        self._main_window = VdriveMainWindow(None)
        self._slice_window = self._main_window.do_launch_log_picker_window()

        return

    @property
    def main_window(self):
        """
        return the main window's handler
        :return:
        """
        return self._slice_window

    def chop_by_time(self):
        """

        :return:
        """
        # select time slicing
        self._slice_window.ui.radioButton_timeSlicer.setChecked(True)
        # specify time step
        self._slice_window.ui.lineEdit_slicerLogValueStep.setText('200')
        # set up slicer
        self._slice_window.do_setup_uniform_slicer()
        # chop
        self._slice_window.do_chop()

        return

    def set_ipts_run(self, ipts_number, run_number):
        """

        :param ipts_number:
        :param run_number:
        :return:
        """
        if ipts_number is not None and run_number is not None:
            self._slice_window.ui.lineEdit_iptsNumber.setText('{}'.format(ipts_number))
            self._slice_window.ui.lineEdit_runNumber.setText('{}'.format(run_number))
        elif False:
            self._slice_window.ui.lineEdit_iptsNumber.setText('{}'.format(22126))
            self._slice_window.ui.lineEdit_runNumber.setText('{}'.format(171899))
        else:
            self._slice_window.ui.lineEdit_iptsNumber.setText('{}'.format(20391))
            self._slice_window.ui.lineEdit_runNumber.setText('{}'.format(172373))

        self._slice_window.do_load_run()

        return

    def test_issue_164(self):
        """
        plot strain vs stress
        :return:
        """
        # TODO - TONIGHT 0 (#164)
        # 1. search log names and set index to
        #    loadframe.strain, loadframe.stress
        #    in GuiUtility: AllItems = [QComboBoxName.itemText(i) for i in range(QComboBoxName.count())]
        # 2. 'push' button: pushButton_setXAxis()

        return


def test_main():
    """
    test main
    """
    slice_ui_tester = EventFilteringAssistantTestEnvironment()

    if True:
        # strain/stress chop
        slice_ui_tester.set_ipts_run(21381, 163411)  # ISSUE 164
        slice_ui_tester.test_issue_164()

    else:
        # regular
        slice_ui_tester.set_ipts_run(None, None)
        slice_ui_tester.chop_by_time()


    return slice_ui_tester.main_window


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
