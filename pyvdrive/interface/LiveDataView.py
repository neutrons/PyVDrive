from datetime import datetime
import os
try:
    import qtconsole.inprocess
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5.QtWidgets import QMainWindow, QLineEdit
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4.QtGui import QMainWindow, QLineEdit
import random
import time
import numpy

from LiveDataChildWindows import SampleLogPlotSetupDialog
from LiveDataChildWindows import LiveViewSetupDialog
from pyvdrive.interface.gui.livedatagraphicswidgets import SingleBankView
from pyvdrive.interface.gui.livedatagraphicswidgets import GeneralPurpose1DView
from pyvdrive.interface.gui.livedatagraphicswidgets import Live2DView
import pyvdrive.lib.LiveDataDriver as ld
import pyvdrive.lib.optimize_utilities as optimize_utilities
from pyvdrive.lib import mantid_helper
from gui.pvipythonwidget import IPythonWorkspaceViewer
from pyvdrive.lib import vdrivehelper
from pyvdrive.lib import datatypeutility

# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

# TODO/ISSUE/FUTURE - Consider https://www.tutorialspoint.com/pyqt/pyqt_qsplitter_widget.htm
#
# 2. 2D contour plot for reduced runs and in-accumulation run

# Note: Atomic workspace: output_xxxx
#       Accumulated workspace: adding output_xxx together

"""
Note:
1. workspace (output) only has 10 seconds log and refreshed each time how to resolve this issue?
"""


class VulcanLiveDataView(QMainWindow):
    """
    Reduced live data viewer for VULCAN
    """
    IN_COLLECTION_MESSAGE = 'In Live Reduction   '

    def __init__(self, parent, live_driver):
        """ initialization
        :param parent:
        :param live_driver:
        """
        # call parent
        super(VulcanLiveDataView, self).__init__(parent)

        # configuration
        self._myConfiguration = parent.configuration

        # get hold of controller/driver
        if live_driver is None:
            self._controller = ld.LiveDataDriver()
        else:
            self._controller = live_driver

        # sub window
        self._workspaceView = None
        self._gpPlotSetupDialog = None
        self._liveSetupDialog = None
        self._myChildWindows = list()

        # collection of workspace names
        self._workspaceSet = set()

        # define data structure by setting some default
        self._myAccumulationWorkspaceNumber = 360  # default as 360 * 0.5 (min) = = 180 min = 3 hours
        self._myUpdateTimePeriod = 10   # seconds.  time interval to update live view
        self._myAccumulationTime = 30   # seconds.  time interval to start a new slice/chopped = 5 min per accumulation
        # decide whether a new workspace shall be started
        self._myMaxIncrementalNumber = self._myAccumulationTime / self._myUpdateTimePeriod
        # containing 2 sets of incremental workspaces for safe
        self._myIncrementalWorkspaceNumber = self._myAccumulationTime / self._myUpdateTimePeriod * 2
        # incremental workspace list
        self._myIncrementalWorkspaceList = [None] * self._myIncrementalWorkspaceNumber  # a holder for workspace names
        self._myIncrementalListIndex = 0  # This is always the next index to write except in add...()
        # summed workspace list and index for accumulated workspaces
        self._myAccumulationWorkspaceList = [None] * self._myAccumulationWorkspaceNumber  # name of summed workspaces
        self._myAccumulationListIndex = 0

        # GSAS workspaces recorded in dictionary: key = run number, value = workspace name
        self._myGSASWorkspaceDict = dict()
        self._myMaxGSASWorkspaceNumber = 100  # only the latest will be recorded.

        # workspace manager for accumulating operation
        # workspace that is currently in accumulation
        self._inAccumulationWorkspaceName = None
        self._inAccumulationIncrementalWorkspaceList = list()  # list of accumulated workspace

        # about previous round pot
        self._plotPrevCycleName = None

        # plotting setup
        self._bankViewDMin = None
        self._bankViewDMax = None

        # Live sample log related
        # name for X-axis
        self._currSampleLogX = None
        # name for Y-axis
        self._currLogNameMainY = None
        self._currLogNameRightY = None
        # time vector
        self._currMainYLogTimeVector = None
        self._currRightYLogTimeVector = None
        # vector for main Y values
        self._currMainYLogValueVector = None
        self._currRightYLogValueVector = None

        # peak integration: recorded for peak upgrading
        self._minDPeakIntegration = {1: None, 0: None}  # 1 for True/main axis, 0 for False/right axis
        self._maxDPeakIntegration = {1: None, 0: None}  # 1 for True/main axis, 0 for False/right axis
        self._plotPeakVanadiumNorm = {1: False, 0: False}  # 1 for True/main axis, 0 for False/right axis

        # other time
        self._liveStartTimeStamp = None  # shall be of time numpy.datetime64

        # start UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/LiveDataView.ui")
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()

        # initialize widgets
        self._init_widgets()

        # banks
        self._bankViewDict = {1: self.ui.graphicsView_currentViewB1,
                              2: self.ui.graphicsView_currentViewB2,
                              3: self.ui.graphicsView_currentViewB3}

        # set up the event handlers
        self.ui.pushButton_startLiveReduction.clicked.connect(self.do_start_live)
        self.ui.pushButton_stopLiveReduction.clicked.connect(self.do_stop_live)

        self.ui.pushButton_setROIb1.clicked.connect(self.do_set_bank1_roi)
        self.ui.pushButton_setROIb2.clicked.connect(self.do_set_bank2_roi)
        self.ui.pushButton_setROIb3.clicked.connect(self.do_set_bank3_roi)
        self.ui.pushButton_fitB1.clicked.connect(self.do_fit_bank1_peak)

        # 2D contour

        # menu bar
        self.ui.actionQuit.triggered.connect(self.do_quit)
        self.ui.actionClear_Logs.triggered.connect(self.do_clear_log)
        self.ui.actionIPython_Console.triggered.connect(self.do_launch_ipython)
        self.ui.actionControl_Panel.triggered.connect(self.menu_launch_setup)
        self.ui.actionMulti_Purpose_Plot.triggered.connect(self.menu_show_multi_purpose_dock)

        # other widgets
        self.ui.comboBox_currUnits.currentIndexChanged.connect(self.evt_bank_view_change_unit)

        self.ui.checkBox_showPrevReduced.stateChanged.connect(self.evt_show_high_prev_data)

        # general purpose
        self.ui.pushButton_setupGeneralPurposePlot.clicked.connect(self.do_setup_gpplot)

        # multiple thread pool
        self._checkStateTimer = None
        self._2dUpdater = None

        self._bankColorDict = {1: 'red', 2: 'blue', 3: 'green'}
        self._mainGraphicDict = {1: self.ui.graphicsView_currentViewB1,
                                 2: self.ui.graphicsView_currentViewB2,
                                 3: self.ui.graphicsView_currentViewB3}

        self._contourFigureDict = {1: self.ui.graphicsView_2DBank1,
                                   2: self.ui.graphicsView_2DBank2,
                                   3: self.ui.graphicsView_2DBank3}

        # timer for accumulation start time
        self._accStartTime = datetime.now()

        # list of run numbers to process
        self._processedRunNumberList = list()

        # flag for 2D plotting
        self._2dMode = 'acc'  # options are 'acc', 'runs', 'unit' (for each refreshed workspace)
        # about 'runs' option
        self._2dStartRunNumber = None

        # mutexes

        # random seed
        random.seed(1)
        # GUI update control
        self._update2DCounter = 0
        #
        self.show_refresh_info()

        return

    def _promote_widgets(self):
        graphicsView_currentViewB1_layout = QVBoxLayout()
        self.ui.frame_graphicsView_currentViewB1.setLayout(graphicsView_currentViewB1_layout)
        self.ui.graphicsView_currentViewB1 = SingleBankView(self)
        graphicsView_currentViewB1_layout.addWidget(self.ui.graphicsView_currentViewB1)

        graphicsView_2DBank1_layout = QVBoxLayout()
        self.ui.frame_graphicsView_2DBank1.setLayout(graphicsView_2DBank1_layout)
        self.ui.graphicsView_2DBank1 = Live2DView(self)
        graphicsView_2DBank1_layout.addWidget(self.ui.graphicsView_2DBank1)

        graphicsView_2DBank2_layout = QVBoxLayout()
        self.ui.frame_graphicsView_2DBank2.setLayout(graphicsView_2DBank2_layout)
        self.ui.graphicsView_2DBank2 = Live2DView(self)
        graphicsView_2DBank2_layout.addWidget(self.ui.graphicsView_2DBank2)

        graphicsView_2DBank3_layout = QVBoxLayout()
        self.ui.frame_graphicsView_2DBank3.setLayout(graphicsView_2DBank3_layout)
        self.ui.graphicsView_2DBank3 = Live2DView(self)
        graphicsView_2DBank3_layout.addWidget(self.ui.graphicsView_2DBank3)

        graphicsView_currentViewB2_layout = QVBoxLayout()
        self.ui.frame_graphicsView_currentViewB2.setLayout(graphicsView_currentViewB2_layout)
        self.ui.graphicsView_currentViewB2 = SingleBankView(self)
        graphicsView_currentViewB2_layout.addWidget(self.ui.graphicsView_currentViewB2)

        graphicsView_currentViewB3_layout = QVBoxLayout()
        self.ui.frame_graphicsView_currentViewB3.setLayout(graphicsView_currentViewB3_layout)
        self.ui.graphicsView_currentViewB3 = SingleBankView(self)
        graphicsView_currentViewB3_layout.addWidget(self.ui.graphicsView_currentViewB3)

        graphicsView_comparison_layout = QVBoxLayout()
        self.ui.frame_graphicsView_comparison.setLayout(graphicsView_comparison_layout)
        self.ui.graphicsView_comparison = GeneralPurpose1DView(self)
        graphicsView_comparison_layout.addWidget(self.ui.graphicsView_comparison)

        return

    def menu_show_multi_purpose_dock(self):
        """
        show multiple-purpose docker widget if it is closed
        :return:
        """
        action = self.ui.dockWidget_multiPurposeView.toggleViewAction()
        print '[DB...PROTOTYPE] action : {0} of type {1}'.format(action, type(action))
        action.setVisible(True)
        self.ui.dockWidget_multiPurposeView.show()

    def _init_widgets(self):
        """
        initialize some widgets
        :return:
        """
        # widgets to show/high previous reduced date
        self.ui.checkBox_showPrevReduced.setChecked(True)
        self.ui.lineEdit_showPrevNCycles.setText('1')
        self.ui.checkBox_normByVanadium.setChecked(False)

        self.ui.label_info.setText('')

        self.ui.checkBox_roiSyncB1B2.setChecked(True)

        # disable some features temporarily
        self.ui.pushButton_fitB1.setEnabled(False)
        self.ui.pushButton_fitB2.setEnabled(False)
        self.ui.pushButton_fitB3.setEnabled(False)

        return

    def _set_workspace_manager(self, max_acc_ws_number, accumulation_time, update_time):
        """
        set the workspace numbers, indicators and etc.
        Note: all the time given will be in seconds
        :param max_acc_ws_number: number of accumulated workspace that will be stored in memory
        :param accumulation_time: for long run, the time for a chopped section,
                                  i.e., an accumulation workspace's time
                                  (unit=second, integer)
        :param update_time: time period to update the live view (unit=second, integer)
        :return:
        """
        # check inputs
        assert isinstance(max_acc_ws_number, int), 'Maximum accumulation workspace number {0} must be' \
                                                   'an integer but not a {1}'.format(max_acc_ws_number,
                                                                                     type(max_acc_ws_number))
        assert isinstance(accumulation_time, int), 'Data accumulation time {0} ({1}) must be an integer but not other' \
                                                   'type.'.format(accumulation_time, type(accumulation_time))
        assert isinstance(update_time, int), 'Update/refresh time {0} ({1}) must be an integer but not any other ' \
                                             'type.'.format(update_time, type(update_time))

        # logic check
        if max_acc_ws_number < 2:
            raise RuntimeError('Maximum accumulation workspace number (now {0}) must be larger or equal to 2.'
                               ''.format(max_acc_ws_number))
        if update_time <= 0:
            raise RuntimeError('Update/refresh time (in second) {0} must be a positive integer.'.format(update_time))
        if accumulation_time < update_time:
            raise RuntimeError('Accumulation time {0} cannot be shorted than update time {1}.'
                               ''.format(accumulation_time, update_time))

        # set as all the inputs are validated
        self._myAccumulationWorkspaceNumber = max_acc_ws_number
        self._myUpdateTimePeriod = update_time
        if accumulation_time % update_time == 0:
            self._myAccumulationTime = accumulation_time
        else:
            # accumulation time is not a multiplication to update/refresh time
            # reset define the accumulation time to be nearest integer multiplication to update time period
            accumulation_time = (accumulation_time/self._myUpdateTimePeriod+1)*self._myUpdateTimePeriod
            self._myAccumulationTime = accumulation_time
            self.write_log(level='warning', message='Accumulation time is modified to {0}'
                                                    ''.format(self._myAccumulationTime))
        # END-IF
        self._myIncrementalWorkspaceNumber = self._myAccumulationTime / self._myUpdateTimePeriod * 2  # leave some space
        self._myMaxIncrementalNumber = self._myAccumulationTime / self._myUpdateTimePeriod

        # set the lists
        self._myIncrementalWorkspaceList = [None] * self._myIncrementalWorkspaceNumber
        self._myAccumulationWorkspaceList = [None] * self._myAccumulationWorkspaceNumber

        return

    @property
    def plotrun(self):
        return self._plotRun

    @plotrun.setter
    def plotrun(self, state):
        """
        set to plot run
        :param state:
        :return:
        """
        self._plotRun = state

        return

    def add_new_workspace(self, ws_name):
        """
        add a new workspace to the list.  if the list is full, then replace the existing one.
        :param ws_name:
        :return:
        """
        # replace previous one
        try:
            if self._myIncrementalWorkspaceList[self._myIncrementalListIndex] is not None:
                prev_ws_name = self._myIncrementalWorkspaceList[self._myIncrementalListIndex]
                self._controller.delete_workspace(prev_ws_name)
        except IndexError as index_err:
            msg = 'Cyclic incremental index {0} is out of range {1}.  It is not possible.' \
                  ''.format(self._myIncrementalListIndex, len(self._myIncrementalWorkspaceList))
            raise RuntimeError('{0}: {1}'.format(msg, index_err))

        # set the new one
        self._myIncrementalWorkspaceList[self._myIncrementalListIndex] = ws_name

        # update index
        self._myIncrementalListIndex += 1
        if self._myIncrementalListIndex == len(self._myIncrementalWorkspaceList):
            self._myIncrementalListIndex = 0
        elif self._myIncrementalListIndex > len(self._myIncrementalWorkspaceList):
            raise RuntimeError("Impossible for myListIndex")

        return

    @property
    def controller(self):
        """
        get the reference to the controller instance of this window
        :return:
        """
        return self._controller

    def get_controller(self):
        return self._controller

    def do_clear_log(self):
        """ clear the live data processing log
        :return:
        """
        self.ui.plainTextEdit_Log.clear()

        return

    def do_fit_bank1_peak(self):
        """

        :return:
        """
        bank_id = 1
        self.fit_single_peak(bank_id, self.ui.graphicsView_currentViewB1, self.ui.lineEdit_bank1RoiStart,
                             self.ui.lineEdit_bank1RoiEnd)

        if self.ui.checkBox_peakFitSyncB1B2.isChecked():
            pass

        self.ui.pushButton_fitB1.setText('Stop Fit')
        if self.ui.checkBox_peakFitSyncB1B2.isChecked():
            self.ui.pushButton_fitB2.setText('Stop Fit')

    def fit_single_peak(self, bank_id, graphics_view, x_min_widget, x_max_widget):
        """
        start to fit single peak of certain bank
        :param bank_id:
        :param graphics_view:
        :param x_max_widget:
        :param x_min_widget
        :return:
        """
        # check inputs
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, None))

        # check input special instances
        assert graphics_view.__class__.__name__.count('SingleBankView') > 0,\
            'Graphics view {0} must be a Q GraphicsView instance but not a {1}.' \
            ''.format(graphics_view, type(graphics_view))
        assert isinstance(x_min_widget, QLineEdit), 'Min X widget {0} must be a QLineEdit but not a ' \
                                                          '{1}'.format(x_min_widget, type(x_min_widget))
        assert isinstance(x_max_widget, QLineEdit), 'Max X widget {0} must be a QLineEdit but not a ' \
                                                          '{1}'.format(x_max_widget, type(x_max_widget))

        try:
            x_min = float(str(x_min_widget.text()))
            x_max = float(str(x_max_widget.text()))
        except ValueError as value_err:
            err_msg = 'Unable to parse x-min {0} or x-max {1} due to {2}.' \
                      ''.format(x_min_widget.text(), x_max_widget.text(), value_err)
            self.write_log('error', err_msg)
            return

        # TODO - ASAP : need a use case to continue
        # FIXME - the data obtained is current or previous?
        vec_x, vec_y = graphics_view.get_data(x_min, x_max)
        coeff, model_y = optimize_utilities.fit_gaussian(vec_x, vec_y)

        # plot the fitted data
        graphics_view.plot_fitted_peak(vec_x, model_y)

        return

    def do_launch_ipython(self):
        """ launch IPython console
        :return:
        """
        if self._workspaceView is None:
            self._workspaceView = IPythonWorkspaceViewer(self)
        self._workspaceView.widget.set_main_window(self)
        self._workspaceView.show()

        self._myChildWindows.append(self._workspaceView)

        return

    def do_quit(self):
        """quit the application
        :return:
        """
        # stop live view
        self.do_stop_live()

        self.close()

        return

    def do_setup_gpplot(self):
        """ set up general-purpose view by ...
        :return:
        """
        if self._gpPlotSetupDialog is None:
            self._gpPlotSetupDialog = SampleLogPlotSetupDialog(self)

        if self._myIncrementalWorkspaceList[self._myIncrementalListIndex - 1] is None:
            self.write_log('error', 'Setup must be followed by starting run.')
            return

        # get axis
        curr_ws_name = self._myIncrementalWorkspaceList[self._myIncrementalListIndex - 1]
        logs = mantid_helper.get_sample_log_names(curr_ws_name, smart=True)

        self._gpPlotSetupDialog.set_axis_options(logs, reset=True)
        self._gpPlotSetupDialog.show()

        return

    def do_set_bank1_roi(self):
        """ set the region of interest by set the X limits on the canvas
        :return:
        """
        self.set_bank_view_roi(bank_id=1, left_x_bound=self.ui.lineEdit_bank1RoiStart,
                               right_x_bound=self.ui.lineEdit_bank1RoiEnd)

        if self.ui.checkBox_roiSyncB1B2.isChecked():
            self.ui.lineEdit_bank2RoiStart.setText(self.ui.lineEdit_bank1RoiStart.text())
            self.ui.lineEdit_bank2RoiEnd.setText(self.ui.lineEdit_bank1RoiEnd.text())
            self.set_bank_view_roi(bank_id=2, left_x_bound=self.ui.lineEdit_bank2RoiStart,
                                   right_x_bound=self.ui.lineEdit_bank2RoiEnd)

        return

    def do_set_bank2_roi(self):
        """ set the region of interest by set the X limits on the canvas
        :return:
        """
        self.set_bank_view_roi(bank_id=2, left_x_bound=self.ui.lineEdit_bank2RoiStart,
                               right_x_bound=self.ui.lineEdit_bank2RoiEnd)

        if self.ui.checkBox_roiSyncB1B2.isChecked():
            self.ui.lineEdit_bank1RoiStart.setText(self.ui.lineEdit_bank2RoiStart.text())
            self.ui.lineEdit_bank1RoiEnd.setText(self.ui.lineEdit_bank2RoiEnd.text())
            self.do_set_bank1_roi()
            self.set_bank_view_roi(bank_id=1, left_x_bound=self.ui.lineEdit_bank1RoiStart,
                                   right_x_bound=self.ui.lineEdit_bank1RoiEnd)

        return

    def do_set_bank3_roi(self):
        """ set the region of interest by set the X limits on the canvas
        :return:
        """
        self.set_bank_view_roi(bank_id=3, left_x_bound=self.ui.lineEdit_bank3RoiStart,
                               right_x_bound=self.ui.lineEdit_bank3RoiEnd)

        return

    def set_bank_view_roi(self, bank_id, left_x_bound, right_x_bound):
        """
        set and apply region of interest on the 3 bank viewer
        :param bank_id:
        :param left_x_bound:
        :param right_x_bound:
        :return:
        """
        # allow multiple format of inputs
        if left_x_bound is not None:
            if isinstance(left_x_bound, QLineEdit):
                try:
                    left_x_bound = float(str(left_x_bound.text()).strip())
                except ValueError:
                    # keep as before
                    left_x_bound = None
            else:
                assert isinstance(left_x_bound, float), 'Left boundary {0} must be either QLineEdit, None or float, ' \
                                                        'but not of {1}'.format(left_x_bound, type(left_x_bound))
        # END-IF

        if right_x_bound is not None:
            if isinstance(right_x_bound, QLineEdit):
                try:
                    right_x_bound = float(str(right_x_bound.text()).strip())
                except ValueError:
                    right_x_bound = None
            else:
                assert isinstance(right_x_bound, float), 'Right boundary {0} must be either QLineEdit, None or ' \
                                                         'float, but not of {1}'.format(right_x_bound,
                                                                                        type(right_x_bound))
        # END-IF
    
        # set
        self._bankViewDict[bank_id].set_roi(left_x_bound, right_x_bound)
        self._bankViewDict[bank_id].rescale_y_axis(left_x_bound, right_x_bound)

        return

    def set_info(self, message, append=True, insert_at_beginning=False):
        """

        :param message:
        :param append:
        :param insert_at_beginning:
        :return:
        """
        if append:
            original_message = str(self.ui.label_info.text())

            if insert_at_beginning:
                message = '{0} | {1}'.format(message, original_message)
            else:
                message = '{0} | {1}'.format(original_message, message)

        self.ui.label_info.setText(message)

        return

    def do_start_live(self):
        """
        start live data reduction and view
        :return:
        """
        # start timer
        self._checkStateTimer = TimerThread(self._myUpdateTimePeriod, self)
        self._checkStateTimer.start()

        self._2dUpdater = TwoDimPlotUpdateThread()
        self._2dUpdater.start()

        # start start listener
        self._controller.run()

        # edit the states
        self.set_info(VulcanLiveDataView.IN_COLLECTION_MESSAGE, append=True,
                      insert_at_beginning=True)

        # disable the start-live-data button
        self.ui.pushButton_startLiveReduction.setEnabled(False)

        return

    def do_stop_live(self):
        """
        stop live data reduction and view
        :return:
        """
        if self._checkStateTimer is not None:
            self._checkStateTimer.stop()

        if self._2dUpdater is not None:
            self._2dUpdater.stop()

        if self._controller is not None:
            self._controller.stop()

        # remove the message
        curr_message = str(self.ui.label_info.text())
        if curr_message.count(VulcanLiveDataView.IN_COLLECTION_MESSAGE) > 0:
            new_msg = curr_message.replace(VulcanLiveDataView.IN_COLLECTION_MESSAGE + ' | ', '')
            self.set_info(new_msg, append=False)

        # enable the start-live-data button
        self.ui.pushButton_startLiveReduction.setEnabled(True)

        return

    def evt_bank_view_change_unit(self):
        """
        change the unit of the plotted workspaces of the top 3 bank view
        :return:
        """
        self.plot_data_in_accumulation()
        self.plot_data_previous_cycle()

        return

    def evt_show_high_prev_data(self):
        """
        show or high previous data
        :return:
        """
        # get state
        state = self.ui.checkBox_showPrevReduced.isChecked()

        # turn on or off the widgets related
        self.ui.lineEdit_showPrevNCycles.setEnabled(state)

        # plot or hide plot
        if state:
            self.plot_data_previous_cycle()
        else:
            self.hide_data_previous_cycle()

        return

    @staticmethod
    def get_reserved_commands():
        """an empty method for IPython console
        :return:
        """
        return list()

    # TEST TODO/Newly Implemented Method
    def get_accumulation_workspaces(self, last_n_round):
        """ get the last N round of accumulation workspaces
        Note of application:
        (1) get sample logs:  the latest incremental workspace has been added to current/last accumulated workspace
        :param last_n_round:
        :return: 2-tuple: list as workspace names and list as indexes of workspaces
        """
        # check inputs
        assert isinstance(last_n_round, int), 'Last N ({0}) round for accumulated workspaces must be given by ' \
                                              'an integer, but not a {1}.'.format(last_n_round, type(last_n_round))

        # if less than 0, then it means that all the available workspace shall be contained
        if last_n_round <= 0:
            last_n_round = self._myAccumulationWorkspaceNumber

        # get list of workspace to plot
        ws_name_list = list()
        ws_index_list = list()
        print '[DB...BAT...BAT] Index = {0} ' \
              'Workspace Name = {1}'.format(self._myAccumulationListIndex,
                                            self._myAccumulationWorkspaceList[self._myAccumulationListIndex])

        for ws_count in range(last_n_round):
            # get accumulation workspace list index
            acc_list_index = self._myAccumulationListIndex - 1 - ws_count
            if acc_list_index < 0:
                acc_list_index += self._myAccumulationWorkspaceNumber
                if acc_list_index < 0:
                    raise RuntimeError('Accumulation list index {0} is still less than 0 after add {1}.'
                                       ''.format(acc_list_index, self._myAccumulationWorkspaceNumber))
            # END-IF

            # get workspace name
            try:
                ws_name_i = self._myAccumulationWorkspaceList[acc_list_index]
                # check
                if ws_name_i is None:
                    # no more workspace (range is too big)
                    break
                elif mantid_helper.workspace_does_exist(ws_name_i) is False:
                    # this is weird!  shouldn't be removed
                    break
                else:
                    ws_name_list.append(ws_name_i)
                    ws_index_list.append(acc_list_index)
            except IndexError as index_err:
                raise RuntimeError('Index {0} is out of incremental workspace range {1} due to {2}.'
                                   ''.format(acc_list_index, len(self._myAccumulationWorkspaceList),
                                             index_err))
            # END-TRY-EXCEPT
        # END-FOR

        # reverse the order
        ws_name_list.reverse()
        ws_index_list.reverse()

        return ws_name_list, ws_index_list

    def get_incremental_workspaces(self, last_n_round):
        """
        just get the last round now!
        :param last_n_round:
        :return:
        """
        # TODO ASAP FIXME case for last_n_round > 0
        # print '[DB...BAT...BAT] Current index: {0}'.format()
        # print '[DB...BAT...BAT] Current workspaces: {0}'.format(self._myIncrementalWorkspaceList)
        # #last_workspace_name = self._myIncrementalWorkspaceList[]

        index = (self._myIncrementalListIndex - 1) % self._myIncrementalWorkspaceNumber
        ws_name = self._myIncrementalWorkspaceList[index]

        return [ws_name]

    def menu_launch_setup(self):
        """
        launch live data setup dialog
        :return:
        """
        if self._liveSetupDialog is None:
            self._liveSetupDialog = LiveViewSetupDialog(self)
            self._myChildWindows.append(self._liveSetupDialog)

        self._liveSetupDialog.show()

        return

    def get_last_n_acc_data(self, last, bank_id):
        """
        get last n accumulation data including the current one
        :param last:
        :param bank_id:
        :return:
        """
        # check inputs' types
        assert isinstance(bank_id, int), 'Bank ID {0} must be an integer but not a {1}.' \
                                         ''.format(bank_id, type(bank_id))
        if not 1 <= bank_id <= 3:
            raise RuntimeError('Bank ID {0} is out of range.'.format(bank_id))

        assert isinstance(last, int), 'Last {0} accumulation data must be an integer but not a {1}' \
                                      ''.format(last, type(last))
        if last < 2:
            raise RuntimeError('Last {0} accumulation data must be larger than 2'.format(last))

        # collect last N accumulated
        self.write_log('debug', 'Get Last {0} Accumulated Data'.format(last))

        acc_data_dict = dict()
        prev_acc_index = self._myAccumulationListIndex
        debug_info = ''
        for inverse_index in range(last):
            # start from self._myAccumulationListIndex - 1
            list_index = self._myAccumulationListIndex % self._myAccumulationWorkspaceNumber - 1 - inverse_index
            try:
                ws_name_i = self._myAccumulationWorkspaceList[list_index]
            except IndexError as index_err:
                raise RuntimeError('Inverted workspace index {0} is converted to workspace index {1} '
                                   'and out of range [0, {2}) due to {3}.'
                                   ''.format(inverse_index, list_index, len(self._myAccumulationWorkspaceList),
                                             index_err))

            if ws_name_i is None:
                # no workspace is set for that
                break

            # get the accumulation index of the workspace
            acc_index = int(ws_name_i.split('_')[-1])
            debug_info += '{0}: {1} | '.format(acc_index, ws_name_i)
            if acc_index >= prev_acc_index:
                # buffer is smaller than the number of acc required and limit is reached
                break
            else:
                prev_acc_index = acc_index

            # get data from memory
            data_set_dict, current_unit = mantid_helper.get_data_from_workspace(workspace_name=ws_name_i,
                                                                                bank_id=bank_id, target_unit='dSpacing',
                                                                                point_data=True, start_bank_id=1)
            acc_data_dict[acc_index] = data_set_dict[bank_id]
        # END-FOR

        # write conclusion message
        self.write_log('debug', debug_info)

        return acc_data_dict

    def get_last_n_round_data(self, last, bank_id):
        """
        get data to plot about the last N runs
        :param last:
        :param bank_id:
        :return: dictionary of data: key = index (integer),
                    value = tuple a 2-tuple (vecx, vecy, vece)
        """
        # check inputs
        assert isinstance(bank_id, int), 'Bank ID {0} must be an integer but not a {1}.' \
                                         ''.format(bank_id, type(bank_id))
        if not 1 <= bank_id <= 3:
            raise RuntimeError('Bank ID {0} is out of range.'.format(bank_id))

        # get the last N workspaces
        ws_name_list, ws_index_list = self.get_accumulation_workspaces(last)

        # get data
        data_set = dict()
        for index, ws_name in enumerate(ws_name_list):
            data_set_dict, current_unit = mantid_helper.get_data_from_workspace(workspace_name=ws_name,
                                                                                bank_id=bank_id, target_unit='dSpacing',
                                                                                point_data=True, start_bank_id=1)
            data_set[ws_index_list[index]] = data_set_dict[bank_id]
        # END-FOR

        return data_set

    def hide_data_previous_cycle(self):
        """

        :return:
        """
        for bank_id in self._bankColorDict:
            self._mainGraphicDict[bank_id].delete_previous_run()
        # END-FOR

        return

    def plot_data_in_accumulation(self):
        """ plot data that is in accumulation
        :return:
        """
        # get new unit
        target_unit = str(self.ui.comboBox_currUnits.currentText())
        self.write_log('information',
                       'Plot in-accumulation data of unit {0}'.format(target_unit))
        # check
        if self._inAccumulationWorkspaceName is None:
            self.write_log('warning', 'No in-accumulation workspace in ADS.')
            return

        # get the workspace names
        in_sum_name = '_temp_curr_ws_{0}'.format(random.randint(1, 10000))
        in_sum_ws, is_new_ws = self._controller.convert_unit(self._inAccumulationWorkspaceName, target_unit,
                                                             in_sum_name)
        in_sum_ws_name = in_sum_ws.name()

        # use vanadium or not
        norm_by_van = self.ui.checkBox_normByVanadium.isChecked()

        # plot
        for bank_id in range(1, 4):
            # get data
            try:
                vec_y_i = in_sum_ws.readY(bank_id-1)[:]

                # Normalize by vanadium: only acted on the vector to plot
                if norm_by_van:
                    vec_y_van = self._controller.get_vanadium(bank_id)
                    vec_y_i = vec_y_i / vec_y_van

                vec_x_i = in_sum_ws.readX(bank_id-1)[:len(vec_y_i)]
                color_i = self._bankColorDict[bank_id]
                label_i = 'in-accumulation bank {0}'.format(bank_id)
                if norm_by_van:
                    label_i += ': normalized by vanadium'
                self._mainGraphicDict[bank_id].plot_current_plot(vec_x_i, vec_y_i, color_i, label_i, target_unit,
                                                                 auto_scale_y=False)
            except RuntimeError as run_err:
                self.write_log('error', 'Unable to get data from workspace {0} due to {1}'
                                        ''.format(in_sum_ws_name, run_err))
                return

            if target_unit == 'TOF':
                self._mainGraphicDict[bank_id].setXYLimit(0, 70000)
            else:
                self._mainGraphicDict[bank_id].setXYLimit(0, 5.0)
        # END-FOR

        if is_new_ws:
            self._controller.delete_workspace(in_sum_name)

        return

    def plot_data_previous_cycle(self):
        """
        plot data collected and reduced in previous accumulated workspace
        this method has no idea whether it should keep the previous reduced plot or not
        :return:
        """
        # return if there is no such need
        if self.ui.checkBox_showPrevReduced.isChecked() is False:
            if self._plotPrevCycleName is not None:
                # if previous cycles are plotted, then remove them
                for bank_id in range(1, 4):
                    self._mainGraphicDict[bank_id].delete_previous_run()
                self._plotPrevCycleName = None
            else:
                raise RuntimeError('Simply not possible!')
            return
        # END-IF

        # get the previous-N cycle accumulated workspace's name: remember that currentIndex is 1 beyond what it is
        prev_ws_index = (self._myAccumulationListIndex - 1 - int(self.ui.lineEdit_showPrevNCycles.text()))
        prev_ws_index %= self._myAccumulationWorkspaceNumber
        if self._myAccumulationWorkspaceList[prev_ws_index] is None:
            message = 'There are only {0} previously accumulated and reduced workspace. ' \
                      'Unable to access previously {1}-th workspace.' \
                      ''.format(len(self._myAccumulationWorkspaceList), abs(prev_ws_index) - 1)
            self.write_log('error', message)
            return
        else:
            prev_ws_name = self._myAccumulationWorkspaceList[prev_ws_index]
        # END-IF-ELSE

        # skip if the previous plotted is sam
        if prev_ws_name == self._plotPrevCycleName:
            debug_message = 'Previous cycle data {0} is same as currently plotted. No need to plot again.' \
                            ''.format(prev_ws_name)
            self.write_log('debug', debug_message)
            return
        else:
            self._plotPrevCycleName = prev_ws_name

        # plot previous ones

        # get new unit
        target_unit = str(self.ui.comboBox_currUnits.currentText())
        prev_ws_name_tmp = '_temp_prev_ws_{0}'.format(random.randint(1, 10000))
        prev_ws, is_new_ws = self._controller.convert_unit(prev_ws_name, target_unit, prev_ws_name_tmp)

        # plot
        line_label = '{0}'.format(prev_ws_name)
        norm_by_van = self.ui.checkBox_normByVanadium.isChecked()
        for bank_id in range(1, 4):
            vec_y = prev_ws.readY(bank_id-1)[:]
            if norm_by_van:
                vec_y_van = self._controller.get_vanadium(bank_id)
                vec_y = vec_y / vec_y_van
            vec_x = prev_ws.readX(bank_id-1)[:len(vec_y)]
            self._mainGraphicDict[bank_id].plot_previous_run(vec_x, vec_y, 'black', line_label)

        # clean
        if is_new_ws:
            self._controller.delete_workspace(prev_ws_name_tmp)

        return

    def load_sample_log(self, y_axis_name, last_n_accumulation, relative_time=None):
        """
        load a sample log from last N time intervals
        :param y_axis_name:
        :param last_n_accumulation: (1) >= 0.  get specified number (2) < 0: get all (3) None: append mode
        :param relative_time
        :return: vector of datetime64 or float (seconds), log value vector
        """
        # check input
        assert isinstance(y_axis_name, str), 'Y-axis (sample log) name {0} must be a string but not a {1}.' \
                                             ''.format(y_axis_name, type(y_axis_name))

        if last_n_accumulation is None:
            # append mode implicitly
            ws_name_list = self.get_incremental_workspaces(last_n_round=0)
        else:
            # new log mode implicitly
            # get the workspace name list: get the last N round of workspace from the beginning of live data
            ws_name_list, index_list = self.get_accumulation_workspaces(last_n_accumulation)

        # get log values
        time_vec, log_value_vec, last_pulse_time = self._controller.parse_sample_log(ws_name_list, y_axis_name)

        # convert the vector of time
        if relative_time is not None:
            time_vec = self._controller.convert_time_stamps(time_vec, relative_time)

        return time_vec, log_value_vec

    def plot_log_with_reduced(self, x_axis_name, y_axis_name):
        """
        plot sample logs with previously reduced data that will be retrieved from GSAS
        :param x_axis_name:
        :param y_axis_name:
        :return:
        """
        # load sample log data
        try:
            ipts_number = int(self.ui.lineEdit_currIPTS.text())
        except ValueError:
            self.write_log('error', 'Unable to parse IPTS {0} to load reduced data.'
                                    ''.format(self.ui.lineEdit_currIPTS.text()))
            return

        curr_run_number = int(self.ui.lineEdit_runNumber.text())

        if self._controller.has_loaded_logs(ipts_number, self._2dStartRunNumber, curr_run_number):
            x_axis_vec, y_axis_vec = self._controller.get_loaded_logs(self._2dStartRunNumber, curr_run_number,
                                                                      self._inAccumulationWorkspaceName)
        else:
            self._controller.load_nexus_sample_logs(ipts_number, self._2dStartRunNumber, curr_run_number,
                                                    run_on_thread=True)

        # TODO/NOW/ASAP - ...
        raise NotImplementedError('ASAP')

    def plot_log_live(self, x_axis_name, y_axis_name_list, side_list, peak_range_list, norm_by_van_list):
        """
        plot log value/peak parameters in a live data
        Note: this model works in most case except a new sample log is chosen to
        Required class variables
          - self._currSampleLog = None
          - self._currSampleLogTimeVector = None
          - self._currSampleLogValueVector = None
        :param x_axis_name:
        :param y_axis_name_list:
        :param side_list: list of boolean. True = left/main axis; False = right axis
        :param d_min:
        :param d_max:
        :param norm_by_van:
        :return:
        """
        # parse the user-specified X and Y axis name and process name in case of 'name (#)'
        # check and etc
        assert isinstance(y_axis_name_list, list), '{0} shall be list but not {1}' \
                                                   ''.format(y_axis_name_list, type(y_axis_name_list))
        assert isinstance(side_list, list), 'Axis-side {0} shall be given in a list but not a {1}.' \
                                            ''.format(side_list, type(side_list))
        if len(y_axis_name_list) != len(side_list):
            raise RuntimeError('Number of Y-axis names ({0}) must be same as number of sides ({1}).'
                               ''.format(len(y_axis_name_list), len(side_list)))

        # check y axis: side
        num_right = 0
        num_left = 0
        main_y_name = None
        right_y_name = None
        for index, side in enumerate(side_list):
            if side:
                num_left += 1
                main_y_name = y_axis_name_list[index]
            else:
                num_right += 1
                right_y_name = y_axis_name_list[index]
            # END-IF
        # END-FOR
        self.write_log('debug', 'Plot main Y: {0}; right Y: {1}'.format(main_y_name, right_y_name))

        # check: the following user-error shall be handled in the caller
        if num_right > 1:
            raise RuntimeError('At most 1 (now {0}) log/peak parameter can be assigned to right axis.'
                               ''.format(num_right))
        elif num_left > 1:
            raise RuntimeError('At most 1 (now {0}) log/peak parameter can be assigned to main axis.'
                               ''.format(num_left))
        elif num_left + num_right == 0:
            raise RuntimeError('At least one log/peak parameter must be assigned either main or right axis.')

        # plot
        for index, y_axis_name in enumerate(y_axis_name_list):
            is_main = side_list[index]
            min_d, max_d = peak_range_list[index]
            norm_by_van = norm_by_van_list[index]

            if x_axis_name == 'Time':
                self.plot_time_arb_live(y_axis_name, min_d, max_d, norm_by_van, is_main=is_main)
            else:
                raise NotImplementedError('Contact PyVDrive develop to implement non-time X-axis ({0}) case.'
                                          ''.format(x_axis_name))

            if is_main:
                self._currLogNameMainY = y_axis_name
            else:
                self._currLogNameRightY = y_axis_name
        # END-FOR

        # all success: keep it in record for auto update
        self._currSampleLogX = x_axis_name

        # # determine to append or start from new
        # if self._currSampleLogX == x_axis_name and self._currLogNameMainY == main_y_name:
        #     append_main = True
        # else:
        #     append_main = False
        # if self._currSampleLogX == x_axis_name and self._currLogNameRightY == right_y_name:
        #     append_right = True
        # else:
        #     append_right = False
        #
        # # plot
        # if x_axis_name == 'Time':
        #     # plot live data
        #     self.plot_time_arb_live(main_y_name, d_min, d_max, norm_by_van, append=append_main, is_main=True)
        #     self.plot_time_arb_live(right_y_name, d_min, d_max, norm_by_van, append=append_right, is_main=False)
        # else:
        #     # non-supported case so far
        #     raise NotImplementedError('Contact PyVDrive develop to implement non-time X-axis ({0}) case.'
        #                               ''.format(x_axis_name))

        return

    def plot_time_arb_live(self, y_axis_name, d_min, d_max, norm_by_van, is_main):
        """
        plot arbitrary live data against with time
        :param y_axis_name:
        :param d_min:
        :param d_max:
        :param norm_by_van:
        :param is_main:
        :return:
        """
        # pre-screen for peak integration
        if y_axis_name is None:
            # nothing to plot
            self.ui.graphicsView_comparison.clear_axis(is_main)

        elif y_axis_name.startswith('* Peak:'):
            # integrate peak for all the accumulated runs
            accumulation_ws_list, index_list = self.get_accumulation_workspaces(last_n_round=-1)
            self._controller.integrate_peaks(accumulated_workspace_list=accumulation_ws_list,
                                             d_min=d_min, d_max=d_max,
                                             norm_by_vanadium=norm_by_van)

            # record for future update
            self._minDPeakIntegration[int(is_main)] = d_min
            self._maxDPeakIntegration[int(is_main)] = d_max
            self._plotPeakVanadiumNorm[int(is_main)] = norm_by_van

            # get peak name
            peak_name = y_axis_name.split('* Peak:')[1].strip()

            # gather the data in banks
            BANK_LIST = [1, 2]              # TODO/FUTURE - shall allow bank 3
            if peak_name.lower().count('center') > 0:
                param_type = 'center'
            elif peak_name.lower().count('intensity') > 0:
                param_type = 'intensity'
            else:
                raise RuntimeError('Peak parameter type {0} is not supported.'.format(peak_name))
            vec_time, peak_value_bank_dict = self._controller.get_peaks_parameters(param_type=param_type,
                                                                                   bank_id_list=BANK_LIST,
                                                                                   time0=self._liveStartTimeStamp)

            self.ui.graphicsView_comparison.plot_peak_parameters(vec_time, peak_value_bank_dict, peak_name,
                                                                 is_main=is_main)

        else:
            # plot sample log
            # process log name in order to get rid of appended information
            log_name = y_axis_name.strip().split('(')[0].strip()

            # find out whether it shall be in append mode or new mode
            if self.ui.graphicsView_comparison.is_same(is_main=is_main, plot_param_name=log_name):
                # append mode
                time_vec, value_vec = self.load_sample_log(log_name, last_n_accumulation=None,
                                                           relative_time=self._liveStartTimeStamp)
                # append
                if is_main:
                    if len(time_vec) == 1 and time_vec[0] <= self._currMainYLogTimeVector[-1]:
                        print '[DEBUG] CRAP Main: {0} comes after {1}'.format(time_vec[0],
                                                                              self._currMainYLogTimeVector[-1])
                    self._currMainYLogTimeVector = numpy.append(self._currMainYLogTimeVector, time_vec)
                    self._currMainYLogValueVector = numpy.append(self._currMainYLogValueVector, value_vec)
                else:
                    if len(time_vec) == 1 and time_vec[0] <= self._currRightYLogTimeVector[-1]:
                        print '[DEBUG] CRAP Right: {0} comes after {1}'.format(time_vec[0],
                                                                               self._currRightYLogTimeVector[-1])
                    self._currRightYLogTimeVector = numpy.append(self._currRightYLogTimeVector, time_vec)
                    self._currRightYLogValueVector = numpy.append(self._currRightYLogValueVector, value_vec)
                # END-IF-ELSE

                debug_message = '[Append Mode] New time stamps: {0}... Log T0 = {1}' \
                                ''.format(time_vec[0], self._liveStartTimeStamp)
                self.write_log('debug', debug_message)

                append = True

            else:
                # New mode
                time_vec, value_vec = self.load_sample_log(log_name, last_n_accumulation=-1,
                                                           relative_time=self._liveStartTimeStamp)
                if is_main:
                    self._currMainYLogTimeVector = time_vec
                    self._currMainYLogValueVector = value_vec
                else:
                    self._currRightYLogTimeVector = time_vec
                    self._currRightYLogValueVector = value_vec

                append = False
            # END-IF-ELSE

            # set the label... TODO ASAP shall leave for the graphicsView to do it
            y_label = log_name
            if is_main:
                value_vec = self._currMainYLogValueVector
                label_y, label_line, color, marker, line_style = y_label, y_label, 'green', '*', ':'
                time_vec = self._currMainYLogTimeVector
            else:
                value_vec = self._currRightYLogValueVector
                label_y, label_line, color, marker, line_style = y_label, y_label, 'blue', '+', ':'
                time_vec = self._currRightYLogTimeVector

            if not append:
                # clear all lines if new lines to plot
                self.ui.graphicsView_comparison.remove_all_plots(include_main=is_main,
                                                                 include_right=not is_main)

            # plot!  FIXME - why APPEND is not passed to plot_sample_log!??
            self.ui.graphicsView_comparison.plot_sample_log(time_vec, value_vec, is_main=is_main,
                                                            x_label=None,
                                                            y_label=label_y, line_label=label_line,
                                                            line_style=line_style, marker=marker,
                                                            color=color)
            # END-IF-ELSE (peak or sample)
        # END-FOR (y-axis-name)

        return

    def process_new_workspaces(self, ws_name_list):
        """ get a list of current workspaces, compare with the existing (or previously recorded workspaces),
        find out new workspace available to plot
        :param ws_name_list:
        :return:
        """
        # check
        assert isinstance(ws_name_list, list), 'workspace names {0} must be given in a list but not a {1}.' \
                                               ''.format(ws_name_list, type(ws_name_list))

        # update timer
        curr_time = datetime.now()
        delta_time = curr_time - self._accStartTime
        total_seconds = int(delta_time.total_seconds())
        hours = total_seconds / 3600
        minutes = total_seconds % 3600 / 60
        seconds = total_seconds % 60
        self.ui.lineEdit_collectionTime.setText('{0:02}:{1:02}:{2:02}'.format(hours, minutes, seconds))

        # return if there is no new workspace to process
        if len(ws_name_list) == 0:
            return

        # sort
        ws_name_list.sort(reverse=True)
        for ws_name_i in ws_name_list:
            # skip temporary workspace
            if ws_name_i.startswith('temp'):
                continue

            if ws_name_i.startswith('output'):
                self.write_log('information', 'Processing new workspace {0}'.format(ws_name_i))
            else:
                # also a new workspace might be the accumulated workspace
                continue

            # convert unit
            if mantid_helper.get_workspace_unit(ws_name_i) != 'dSpacing':
                mantid_helper.mtd_convert_units(ws_name_i, 'dSpacing')
            else:
                self.write_log('information', 'Input workspace {0} has unit dSpacing.'.format(ws_name_i))
            # END-IF-ELSE

            # rebin
            mantid_helper.rebin(ws_name_i, '0.3,-0.001,3.5', preserve=False)

            # reference to workspace
            workspace_i = mantid_helper.retrieve_workspace(ws_name_i)

            ws_x_info = ''
            for iws in range(3):
                ws_x_info += 'Workspace {0}: From {1} to {2}, # of bins = {3}\n'.format(iws, workspace_i.readX(0)[0],
                                                                                        workspace_i.readX(0)[-1],
                                                                                        len(workspace_i.readX(0)))
            self.write_log('debug', ws_x_info)

            # add new workspace to data manager
            self.add_new_workspace(ws_name_i)

            # update info
            self.ui.lineEdit_newestReducedWorkspace.setText(ws_name_i)

            # get reference to workspace
            run_number_i = workspace_i.getRunNumber()
            self.ui.lineEdit_runNumber.setText(str(run_number_i))

            # live data start time
            if self._liveStartTimeStamp is None:
                # get from the proton charge for T0
                self._liveStartTimeStamp = workspace_i.run().getProperty('proton_charge').times[0]
                # convert to local time for better communication
                east_time = vdrivehelper.convert_utc_to_local_time(self._liveStartTimeStamp)
                # set time
                self.ui.lineEdit_logStarTime.setText(str(east_time))

            # skip non-matrix workspace or workspace sounds not right
            if not (mantid_helper.is_matrix_workspace(ws_name_i) and 3 <= workspace_i.getNumberHistograms() < 20):
                # skip weird workspace
                log_message = 'Workspace {0} of type {1} is not expected.\n'.format(workspace_i, type(workspace_i))
                self.write_log('error', log_message)
                continue

            # now it is the workspace that is to plot
            self.sum_incremental_workspaces(workspace_i)
            #  accumulate_name = self._accumulatedWorkspace.name()

            # always plot the current in-accumulation one
            self.plot_data_in_accumulation()

            # previous one if it is checked to plot
            if self.ui.checkBox_showPrevReduced.isChecked():
                self.plot_data_previous_cycle()

            # re-set the ROI if the unit is d-spacing
            db_msg = 'Unit = {0} Range = {1}, {2}'.format(self.ui.comboBox_currUnits.currentText(),
                                                          self._bankViewDMin, self._bankViewDMax)
            self.write_log('debug', db_msg)
            if str(self.ui.comboBox_currUnits.currentText()) == 'dSpacing':
                print '[DB...BAT...BAT...BAT] Set bank View of ROI'
                for bank_id in [1, 2, 3]:
                    self.set_bank_view_roi(bank_id=bank_id, left_x_bound=None, right_x_bound=None)
            else:
                print '[DB...BAT...BAT...BAT] Set bank View to original'

            # update log
            if self._currSampleLogX is not None:
                y_axis_list = [self._currLogNameMainY, self._currLogNameRightY]
                side_list = [True, False]
                peak_range_list = [(self._minDPeakIntegration[1], self._maxDPeakIntegration[1]),
                                   (self._minDPeakIntegration[0], self._maxDPeakIntegration[0])]
                norm_by_van_list = [self._plotPeakVanadiumNorm[1], self._plotPeakVanadiumNorm[0]]
                self.plot_log_live(self._currSampleLogX, y_axis_list, side_list, peak_range_list, norm_by_van_list)
        # END-FOR

        return

    def set_accumulation_time(self, accumulation_time):
        """
        set the accumulation time
        :param accumulation_time:
        :return:
        """
        # check
        assert isinstance(accumulation_time, int), 'Accumulation time {0} to set must be an integer but not a {1}.' \
                                                   ''.format(accumulation_time, type(accumulation_time))

        self._set_workspace_manager(max_acc_ws_number=self._myAccumulationWorkspaceNumber,
                                    accumulation_time=accumulation_time,
                                    update_time=self._myUpdateTimePeriod)

        return

    def set_plot_run(self, plot_runs, start_run):
        """
        set the 2D figure to plot reduced runs instead of accumulated live data
        :param plot_runs:
        :param start_run:
        :return:
        """
        # check inputs
        assert isinstance(plot_runs, bool), 'Flag to plot runs{0} must be a boolean but not a {1}.' \
                                            ''.format(plot_runs, type(plot_runs))

        # set!
        if plot_runs:
            # plot reduced runs in 2D view
            self._2dMode = 'runs'
            assert isinstance(start_run, int), 'Start run number {0} to plot must be an integer but not a {1}.' \
                                               ''.format(start_run, int(start_run))

            if start_run <= 0:
                raise RuntimeError('Starting run number {0} cannot be less than 1.'.format(start_run))

            self._2dStartRunNumber = start_run
        else:
            # plot regular ones
            self._2dMode = 'acc'

        return

    def set_refresh_rate(self, update_period):
        """
        set the refresh rate
        :param update_period:
        :return:
        """
        # check
        assert isinstance(update_period, int), 'Update/refresh rate {0} must be an integer but not a {1}.' \
                                               ''.format(update_period, type(update_period))

        self._set_workspace_manager(max_acc_ws_number=self._myAccumulationWorkspaceNumber,
                                    accumulation_time=self._myAccumulationTime,
                                    update_time=update_period)

        return

    def set_vanadium_norm(self, turn_on, van_file_name=None):
        """
        set the state to normalize vanadium or not
        :param turn_on:
        :param van_file_name:
        :return:
        """
        self.ui.checkBox_normByVanadium.setChecked(turn_on)

        # add vanadium file name to list
        if turn_on:
            # do it only when it is turned on
            # get the current vanadium files and check
            num_items = self.ui.comboBox_loadedVanRuns.count()
            exist_item_index = -1
            for p_index in range(num_items):
                van_name_i = str(self.ui.comboBox_loadedVanRuns.itemText(p_index))
                if van_file_name == van_name_i:
                    exist_item_index = p_index
                    break
            # END-IF

            # add new item if it has not been loaded
            if exist_item_index < 0:
                self.ui.comboBox_loadedVanRuns.addItem(van_file_name)
                exist_item_index = num_items  # currently count() - 1

            # set current index
            self.ui.comboBox_loadedVanRuns.setCurrentIndex(exist_item_index)
        # END-IF

        return

    def show_refresh_info(self):
        """ Show the accumulation/refresh/update rate information
        :return:
        """
        acc_time = self._myAccumulationTime
        self.ui.lineEdit_accPeriod.setText('{0} sec'.format(acc_time))
        self.ui.lineEdit_updateTime.setText('{} sec'.format(self._myUpdateTimePeriod))

        return

    def sum_incremental_workspaces(self, workspace_i):
        """sum up the incremental workspace to an accumulated workspace
        :param workspace_i: a MatrixWorkspace instance
        :return:
        """
        try:
            ws_name = workspace_i.name()
        except AttributeError as att_err:
            raise RuntimeError('Input workspace {0} of type {1} is not a MatrixWorkspace: Error {2}'
                               ''.format(workspace_i, type(workspace_i), att_err))

        if self._inAccumulationWorkspaceName is None or \
                        len(self._inAccumulationIncrementalWorkspaceList) == self._myMaxIncrementalNumber:
            # reset if pre-existing of accumulated workspace. It is a time of a new accumulation workspace
            self._inAccumulationIncrementalWorkspaceList = list()

            # clone workspace
            accumulate_name = 'Accumulated_{0:05d}'.format(self._myAccumulationListIndex)
            mantid_helper.clone_workspace(ws_name, accumulate_name)
            self._inAccumulationWorkspaceName = accumulate_name

            # add to list
            list_index = self._myAccumulationListIndex % self._myAccumulationWorkspaceNumber

            if self._myAccumulationWorkspaceList[list_index] is not None:
                old_ws_name = self._myAccumulationWorkspaceList[list_index]
                self.write_log('information', 'Delete old workspace {0}'.format(old_ws_name))
                self._controller.delete_workspace(old_ws_name)
            self._myAccumulationWorkspaceList[list_index] = accumulate_name

            # restart timer
            self._accStartTime = datetime.now()

            # increase list index
            self._myAccumulationListIndex += 1

            # set the info
            self.ui.lineEdit_inAccWsName.setText(self._inAccumulationWorkspaceName)
            self.ui.spinBox_currentIndex.setValue(self._myAccumulationListIndex)

        else:
            # add to existing accumulation workspace
            ws_in_acc = mantid_helper.retrieve_workspace(self._inAccumulationWorkspaceName, raise_if_not_exist=True)

            # more check on histogram number and spectrum size
            if ws_in_acc.getNumberHistograms() != workspace_i.getNumberHistograms():
                raise RuntimeError('Accumulated workspace {0} has different number of spectra ({1}) than the '
                                   'incremental workspace {2} ({3}).'
                                   ''.format(self._inAccumulationWorkspaceName,
                                             ws_in_acc.getNumberHistograms(),
                                             workspace_i.getNumberHistograms.name(),
                                             workspace_i.getNumberHistograms()))
            # END-IF (test)

            # sum 2 workspaces together
            self._controller.sum_workspaces([self._inAccumulationWorkspaceName, ws_name],
                                            self._inAccumulationWorkspaceName)
        # END-IF-ELSE

        # update the list of source accumulated workspace
        self._inAccumulationIncrementalWorkspaceList.append(ws_name)

        return

    def update_2d_plot(self, bank_id=None):
        """
        update 2D contour plot for the reduced data in the last N time-intervals
        :return:
        """
        def parse_set_last_n():
            """
            parse and set last N intervals to plot
            :return:
            """
            n_str = str(self.ui.lineEdit_lastNInterval2D.text())
            if len(n_str) == 0:
                n_str = 10
                self.ui.lineEdit_lastNInterval2D.setText('10')
            last_n = int(n_str)
            if last_n <= 0:
                last_n = 10  # default value
                self.ui.lineEdit_lastNInterval2D.setText('10')

            return last_n

        if bank_id is None:
            bank_id_list = [1, 2, 3]
        else:
            bank_id_list = [bank_id]

        for bank_id in bank_id_list:
            # get bank ID

            # get the last N time-intervals and create the meshdata
            last_n_run = parse_set_last_n()
            # retrieve data

            # TODO/ISSUE/NOW/FIXME - It is in a debug mode
            self._2dMode = 'acc'  #
            # --------------------------------------------

            if self._2dMode == 'unit':
                data_set_dict = self.get_last_n_round_data(last=last_n_run, bank_id=bank_id)
            elif self._2dMode == 'acc':
                # plot accumulations
                data_set_dict = self.get_last_n_acc_data(last_n_run, bank_id=bank_id)
            elif self._2dMode == 'runs':
                data_set_dict = self.get_last_n_runs_data(last_n_run, bank_id=bank_id)
            else:
                raise RuntimeError('2D plot mode {0} is not supported.'.format(self._2dMode))

            # plot
            if len(data_set_dict) > 1:
                if bank_id in bank_id_list:
                    # self._2dUpdater.set_new_plot(self._contourFigureDict[bank_id], data_set_dict)
                    self._contourFigureDict[bank_id].plot_contour(data_set_dict)
                else:
                    pass
                    # self._contourFigureDict[bank_id].plot_image(data_set_dict)
            # END-IF
        # END-FOR

        return

    def update_timer(self, i_signal):
        """
        update timer
        :param i_signal: signal integer from event
        :return:
        """
        # refresh with workspace list
        try:
            ws_name_list = self._controller.get_workspaces()
        except RuntimeError as run_err:
            self.write_log('error', 'Unable to get workspaces due to {0}'.format(run_err))
            return

        # check whether there is any new workspace in ADS
        ws_name_set = set(ws_name_list)
        diff_set = ws_name_set - self._workspaceSet
        if len(diff_set) > 0:
            new_ws_name_list = list(diff_set)
            self._workspaceSet = ws_name_set
        else:
            new_ws_name_list = list()

        # process new workspace
        self.process_new_workspaces(new_ws_name_list)
        if len(new_ws_name_list) > 0:
            # update 2D
            self._update2DCounter += 1
            self.update_2d_plot(self._update2DCounter % 3 + 1)

        # update GUI
        total_index = self._controller.get_live_counter()
        self.ui.spinBox_totalIndex.setValue(total_index)

        # print '[UI-DB] Acc Index = {0}, Total Index = {1}'.format(self._currAccumulateIndex, total_index)

        # some counter += 1

        message = ''
        for ws_name in new_ws_name_list:
            ws_i = mantid_helper.retrieve_workspace(ws_name)
            if ws_i is None:
                self.write_log('error', 'In update-timer: unable to retrieve workspace {0}'.format(ws_name))
            elif ws_i.id() == 'Workspace2D' or ws_i.id() == 'EventWorkspace' and ws_i.name().startswith('output'):
                message += 'New workspace {0}: number of spectra = {1}'.format(ws_name, ws_i.getNumberHistograms())
        # END-FOR
        if len(message) > 0:
            self.write_log('information', message)

        # update time display
        time_now = datetime.now()
        self.ui.lineEdit_currentTime.setText(str(time_now))
        # NOTE: time difference is left to lineEdit_elapsedTime as log

        return

    def write_log(self, level, message):
        """ write message to the message log
        :param level:
        :param message:
        :return:
        """
        message_prefix = ''

        if level == 'warning':
            message_prefix = 'WARNING'
        elif level == 'information':
            message_prefix = 'INFO'
        elif level == 'error':
            message_prefix = 'ERROR'
        elif level == 'debug':
            message_prefix = 'DEBUG'

        # write
        message = '[{0}]\t {1}'.format(message_prefix, message)
        self.ui.plainTextEdit_Log.appendPlainText(message)

        return


class TwoDimPlotUpdateThread(QtCore.QThread):
    """
    blabla
    """
    def __init__(self):
        """

        """
        # call base class's constructor
        super(TwoDimPlotUpdateThread, self).__init__()

        self._mutex = False

        self._update = False
        self._currFigure = None
        self.data_set_dict = None

        self._continueTimerLoop = True

        return

    def run(self):
        """
        run the thread!
        :return:
        """
        while self._continueTimerLoop:
            # sleep
            time.sleep(5)

            # check whether it is time to plot
            if self._mutex:
                continue
            else:
                self._mutex = True

            # update
            if self._update:
                self._currFigure.plot_contour(self.data_set_dict)
                self._update = False

            # release
            self._mutex = False
        # END-WHILE

        return

    def set_new_plot(self, figure, data_set_dict):
        """

        :return:
        """
        self._update = True
        self._currFigure = figure
        self.data_set_dict = data_set_dict

    def stop(self):
        """ stop the timer by turn off _continueTimeLoop (flag)            :return:
        """
        self._continueTimerLoop = False

        return


class SampleLoadingThread(QtCore.QThread):
    """
    Thread function to load sample logs from Nexus files
    """
    # signal
    FileLoaded = QtCore.pyqtSignal(str, str)  # x-axis, y-axis name

    def __init__(self, parent, x_axis_name, y_axis_name, ipts_number, start_run, stop_run):
        """ initialization
        :param x_axis_name:
        :param y_axis_name:
        :param ipts_number:
        :param start_run:
        :param stop_run:
        """
        super(SampleLoadingThread, self).__init__()

        # check inputs
        assert parent is not None, 'Parent cannot be None.'
        assert isinstance(x_axis_name, str), 'X-axis name {0} must be a string but not a {1}' \
                                             ''.format(x_axis_name, type(x_axis_name))
        assert isinstance(y_axis_name, str), 'Y-axis name {0} must be a string but not a {1}' \
                                             ''.format(y_axis_name, type(y_axis_name))
        assert isinstance(ipts_number, int), 'IPTS number {0} must be an integer but not a {1}' \
                                             ''.format(ipts_number, type(ipts_number))
        assert isinstance(start_run, int), 'Start run number {0} must be an integer but not a {1}' \
                                           ''.format(start_run, type(start_run))
        assert isinstance(stop_run, int), 'Stop run number {0} must be an integer but not a {1}' \
                                          ''.format(stop_run, type(stop_run))

        self._parent = parent
        self._x_name = x_axis_name
        self._y_name = y_axis_name
        self._iptsNumber = ipts_number
        self.first_run_number = start_run
        self.stop_run_number = stop_run   # exclusive

        # define the signal connection
        self.FileLoaded.connect(self._parent.plot_log_with_reduced)

        return

    def run(self):
        """
        main to process data
        :return:
        """
        archive_manager = self._parent.get_archive_manager()
        if self.stop_run_number == 0:
            self.stop_run_number = None
        archive_manager.load_nexus_files(self._iptsNumber, self.first_run_number, self.stop_run_number,
                                         meta_data_only=True)


class TimerThread(QtCore.QThread):
    """
    Thread functions as a timer to check for the change of workspaces
    """

    # signal
    time_due = QtCore.pyqtSignal(int)

    def __init__(self, time_step, parent):
        """
        initialization
        :param time_step:
        :param parent:
        """
        # call base class's constructor
        super(TimerThread, self).__init__()

        # set up parent
        self._parent = parent

        # define status
        self._continueTimerLoop = True

        # connect to parent
        self.time_due.connect(self._parent.update_timer)

        return

    def run(self):
        """ run the timer thread.  this thread won't be kill until flag _continueTimerLoop is set to False
        :return:
        """
        while self._continueTimerLoop:
            time.sleep(1)
            self.time_due.emit(1)
        # END-WHILE

        return

    def stop(self):
        """ stop the timer by turn off _continueTimeLoop (flag)
        :return:
        """
        self._continueTimerLoop = False

        return
