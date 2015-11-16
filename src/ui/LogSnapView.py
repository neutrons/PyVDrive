########################################################################
#
# General-purposed plotting window
#
########################################################################
import sys

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import GuiUtility as gutil
import gui.ui_LogSnapView as ui_LogSnapView


class DialogLogSnapView(QtGui.QDialog):
    """ Class for general-puposed plot window
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QtGui.QDialog.__init__(self)

        # parent
        self._myParent = parent

        # set up UI
        self.ui = ui_LogSnapView.Ui_Dialog()
        self.ui.setupUi(self)

        # Event handling
        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'),
                     self.do_apply_change)
        self.connect(self.ui.pushButton_saveQuit, QtCore.SIGNAL('clicked()'),
                     self.do_save_quit)
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_quit_no_save)

        # Class state variables
        self._slicerIsSaved = False
        self._currSessionDiscardable = True

        self._logName = None

        # Controller variables
        self._myWorkflowController = None
        self._horizontalIndicatorList = None
        self._verticalIndicatorList = [None, None]

        return

    def do_apply_change(self):
        """ Apply new set up for the slicer range
        :return:
        """
        # Time
        min_time = gutil.parse_float(self.ui.lineEdit_minTime)
        self._move_time_boundary(self._horizontalIndicatorList[0], min_time)
        max_time = gutil.parse_float(self.ui.lineEdit_maxTime)
        self._move_time_boundary(self._horizontalIndicatorList[1], max_time)

        # Value
        min_log_value = gutil.parse_float(self.ui.lineEdit_minLogValue)
        max_log_value = gutil.parse_float(self.ui.lineEdit_maxLogTime)
        v_id_0 = self.ui.graphicsView_main.add_horizontal_indicator(min_log_value, 'blue')
        v_id_1 = self.ui.graphicsView_main.add_horizontal_indicator(max_log_value, 'blue')
        self._verticalIndicatorList[0] = v_id_0
        self._verticalIndicatorList[1] = v_id_1

        return

    def do_quit_no_save(self):
        """

        :return:
        """
        self._currSessionDiscardable = True
        self.close()

        return

    def do_save_quit(self):
        """
        Save and quit with applying to parent
        :return:
        """
        self._slicerIsSaved = True
        self._currSessionDiscardable = True

        # TODO/FIXME/NOW
        # start_time = gutil.parse_float('')
        """
        lineEdit_minTime
        lineEdit_maxTime
        lineEdit_minLogValue
        lineEdit_logValueInterval
        lineEdit_maxLogTime
        comboBox_direction
        """

        self._myParent.get_controller().gen_data_slicer_sample_log(
            run_number=self._myRunNumber,
            sample_log_name=self._myLogName,
            start_time=1.0,
            end_time=200.1,
            min_log_value=-10.0,
            max_log_value=-8.0,
            log_value_step=1.0)

        return

    def is_saved(self):
        """ Return whether the information is saved or not
        :return:
        """
        return self._slicerIsSaved

    def allow_new_session(self):
        """
        Return the flag if it is fine to start to plot a new log
        :return:
        """
        return self._currSessionDiscardable

    def setup(self, workflow_controller, sample_log_name, num_sec_skip):
        """ Set up from parent main window
        :return:
        """
        # Get workflow controller
        self._myWorkflowController = workflow_controller
        if self._logName != sample_log_name:
            new_graph = True
        else:
            new_graph = False

        # Return and do nothing if just want to show a hidden window
        if new_graph is False:
            return

        # Reset some state variables for new
        self._slicerIsSaved = False
        self._currSessionDiscardable = False

        # Get log value
        status, ret_value = self._myWorkflowController.get_sample_log_values(
            sample_log_name, relative=True)
        if status is True:
            vec_x, vec_y = ret_value
        else:
            gutil.pop_dialog_error(self, ret_value)
            return

        # Plot
        self.ui.graphicsView_main.clear_all_lines()
        self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, label=sample_log_name)

        # Set up boundary for time
        min_x = vec_x[0]
        max_x = vec_x[-1]

        self.ui.lineEdit_minTime.setText(str(min_x))
        self.ui.lineEdit_maxTime.setText(str(max_x))

        indicator_id_min = self.ui.graphicsView_main.add_vertical_indicator(min_x, 'green')
        indicator_id_max = self.ui.graphicsView_main.add_vertical_indicator(max_x, 'green')
        self._horizontalIndicatorList = [indicator_id_min, indicator_id_max]

        # Set up for log value
        min_y = min(vec_y)
        max_y = max(vec_y)
        self.ui.lineEdit_minLogValue.setText('%.5f' % min_y)
        self.ui.lineEdit_maxLogTime.setText('%.5f' % max_y)

        return

    def _move_time_boundary(self, line_id, time_value):
        """ Move the vertical indicator for time boundary
        :param line_id:
        :param time_value:
        :return:
        """
        # self.ui.graphicsView_main.set_indicator_horizontal(line_id, time_value)
        self.ui.graphicsView_main.set_indicator_position(line_id, time_value, None)

        return


def testmain(argv):
    """ Main method for testing purpose
    """
    parent = None

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = DialogLogSnapView(parent)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return

if __name__ == "__main__":
    testmain(sys.argv)
