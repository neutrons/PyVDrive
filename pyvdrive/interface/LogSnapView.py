########################################################################
#
# General-purposed plotting window
#
########################################################################
import sys

try:
    import qtconsole.inprocess
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5.QtWidgets import QDialog, QApplication
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4.QtGui import QDialog, QApplication

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import gui.GuiUtility as gutil
from pyvdrive.interface.gui.mplgraphicsview import MplGraphicsView


class DialogLogSnapView(QDialog):
    """ Class for general-puposed plot window
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QDialog.__init__(self)

        # parent
        self._myParent = parent

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/LogSnapView.ui")
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()

        # Event handling
        self.ui.pushButton_apply.clicked.connect(self.do_apply_change)
        self.ui.pushButton_saveQuit.clicked.connect(self.do_save_quit)
        self.ui.pushButton_cancel.clicked.connect(self.do_quit_no_save)

        # Class state variables
        self._slicerIsSaved = False
        self._currSessionDiscardable = True

        self._logName = None
        self._myRunNumber = None

        # Controller variables
        self._myWorkflowController = None
        self._horizontalIndicatorList = None
        self._verticalIndicatorList = [None, None]

        return

    def _promote_widgets(self):
        graphicsView_main_layout = QVBoxLayout()
        self.ui.frame_graphicsView_main.setLayout(graphicsView_main_layout)
        self.ui.graphicsView_main = MplGraphicsView(self)
        graphicsView_main_layout.addWidget(self.ui.graphicsView_main)

        return

    def allow_new_session(self):
        """
        Return the flag if it is fine to start to plot a new log
        :return:
        """
        return self._currSessionDiscardable

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
        max_log_value = gutil.parse_float(self.ui.lineEdit_maxLogValue)
        v_id_0 = self.ui.graphicsView_main.add_horizontal_indicator(min_log_value, 'blue')
        v_id_1 = self.ui.graphicsView_main.add_horizontal_indicator(max_log_value, 'blue')
        self._verticalIndicatorList[0] = v_id_0
        self._verticalIndicatorList[1] = v_id_1

        return

    def do_get_log_name(self):
        """

        :return:
        """
        return self._logName

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
        # Get parameter values from GUI
        start_time = gutil.parse_float(self.ui.lineEdit_minTime)
        stop_time = gutil.parse_float(self.ui.lineEdit_maxTime)
        min_log_value = gutil.parse_float(self.ui.lineEdit_minLogValue)
        max_log_value = gutil.parse_float(self.ui.lineEdit_maxLogValue)
        delta_value = gutil.parse_float(self.ui.lineEdit_logValueInterval)

        # FIXME - Treat 'comboBox_direction'

        if start_time < 0.:
            start_time = 0.
        self._myParent.get_controller().gen_data_slicer_sample_log(
            run_number=self._myRunNumber,
            sample_log_name=self._logName,
            start_time=start_time,
            end_time=stop_time,
            min_log_value=min_log_value,
            max_log_value=max_log_value,
            log_value_step=delta_value)

        # Update the state variables
        self._slicerIsSaved = True
        self._currSessionDiscardable = True

        # Quit
        self.close()

        return

    def get_log_name(self):
        """

        :return:
        """
        return self._logName

    def is_saved(self):
        """ Return whether the information is saved or not
        :return:
        """
        return self._slicerIsSaved

    def setup(self, workflow_controller, run_number, sample_log_name, num_sec_skip):
        """ Set up from parent main window
        :return:
        """
        # Get workflow controller
        self._myWorkflowController = workflow_controller
        if run_number != self._myRunNumber:
            new_graph = True
            self._myRunNumber = run_number
            self._logName = sample_log_name
        elif self._logName != sample_log_name:
            new_graph = True
            self._logName = sample_log_name
        else:
            new_graph = False

        # Return and do nothing if just want to show a hidden window
        if new_graph is False:
            return

        # Reset some state variables for new
        self._slicerIsSaved = False
        self._currSessionDiscardable = False

        # Get log value
        vec_x, vec_y = self._myWorkflowController.get_sample_log_values(data_key=self._currRunNumber,
                                                                        log_name=sample_log_name, relative=True)

        # Plot
        self.ui.graphicsView_main.clear_all_lines()
        self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, label=sample_log_name)

        # reset limit
        y_min = min(vec_y)
        y_max = max(vec_y)
        dy = y_max - y_min
        y_min -= dy*0.1
        y_max += dy*0.1
        self.ui.graphicsView_main.setXYLimit(ymin=y_min, ymax=y_max)

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
        self.ui.lineEdit_maxLogValue.setText('%.5f' % max_y)

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

    app = QApplication(argv)

    # my plot window app
    myapp = DialogLogSnapView(parent)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return

if __name__ == "__main__":
    testmain(sys.argv)
