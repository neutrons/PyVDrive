from datetime import datetime
from PyQt4 import QtCore
from PyQt4 import QtGui
import random
import time
import numpy

from LiveDataChildWindows import SampleLogPlotSetupDialog
from LiveDataChildWindows import LiveViewSetupDialog
import gui.ui_LiveDataView_ui as ui_LiveDataView
import pyvdrive.lib.LiveDataDriver as ld
import pyvdrive.lib.mantid_helper as helper
from gui.pvipythonwidget import IPythonWorkspaceViewer


# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

# TODO/ISSUE/FUTURE - Consider https://www.tutorialspoint.com/pyqt/pyqt_qsplitter_widget.htm
#
# TODO - NEW TO TEST
# 1. Test live plot with improved data structure
# 2. 2D contour plot for reduced runs and in-accumulation run

# Note: Atomic workspace: output_xxxx
#       Accumulated workspace: adding output_xxx together

"""
Note:
1. workspace (output) only has 10 seconds log and refreshed each time how to resolve this issue?
"""


class VulcanLiveDataView(QtGui.QMainWindow):
    """
    Reduced live data viewer for VULCAN
    """
    def __init__(self, parent, live_driver):
        """initialization
        :param parent:
        """
        # call parent
        super(VulcanLiveDataView, self).__init__(parent)

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
        self._myRefreshTimeStep = 10  # seconds
        self._myAccumulationTime = 30  # 30 x 10 = 300 seconds = 5 min per accumulation
        # decide whether a new workspace shall be started
        self._myMaxIncrementalNumber = self._myAccumulationTime / self._myRefreshTimeStep
        # containing 2 sets of incremental workspaces for safe
        self._myIncrementalWorkspaceNumber = self._myAccumulationTime / self._myRefreshTimeStep * 2
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
        # Bank ID (current): shall be updated with event to handle change of bank ID selection
        self._currentBankID = 1

        # plotting setup
        self._bankViewDMin = None
        self._bankViewDMax = None

        # Live sample log related
        self._currSampleLogX = None
        self._currSampleLogY = None
        self._currSampleLogTimeVector = None
        self._currSampleLogValueVector = None
        self._logStartTime = None

        # other time
        self._liveStartTimeStamp = None

        # start UI
        self.ui = ui_LiveDataView.Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize widgets
        self._init_widgets()

        # set up the event handlers
        self.connect(self.ui.pushButton_startLiveReduction, QtCore.SIGNAL('clicked()'),
                     self.do_start_live)
        self.connect(self.ui.pushButton_stopLiveReduction, QtCore.SIGNAL('clicked()'),
                     self.do_stop_live)
        self.connect(self.ui.pushButton_setROI, QtCore.SIGNAL('clicked()'),
                     self.do_set_roi)

        # 2D contour

        self.connect(self.ui.pushButton_refresh2D, QtCore.SIGNAL('clicked()'),
                     self.do_refresh_2d)

        # menu bar
        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'),
                     self.do_quit)
        self.connect(self.ui.actionClear_Logs, QtCore.SIGNAL('triggered()'),
                     self.do_clear_log)
        self.connect(self.ui.actionIPython_Console, QtCore.SIGNAL('triggered()'),
                     self.do_launch_ipython)
        self.connect(self.ui.actionControl_Panel, QtCore.SIGNAL('triggered()'),
                     self.menu_launch_setup)

        # other widgets
        self.connect(self.ui.comboBox_currUnits, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_bank_view_change_unit)

        self.connect(self.ui.checkBox_showPrevReduced,  QtCore.SIGNAL('stateChanged(int)'),
                     self.evt_show_high_prev_data)

        self.connect(self.ui.checkBox_2dBank1, QtCore.SIGNAL('stateChanged(int)'),
                     self.evt_bank1_changed)
        self.connect(self.ui.checkBox_2dBank2, QtCore.SIGNAL('stateChanged(int)'),
                     self.evt_bank2_changed)
        self.connect(self.ui.checkBox_2dBank3, QtCore.SIGNAL('stateChanged(int)'),
                     self.evt_bank3_changed)

        # general purpose
        self.connect(self.ui.pushButton_setupGeneralPurposePlot, QtCore.SIGNAL('clicked()'),
                     self.do_setup_gpplot)

        # multiple thread pool
        self._checkStateTimer = None

        self._bankColorDict = {1: 'red', 2: 'blue', 3: 'green'}
        self._mainGraphicDict = {1: self.ui.graphicsView_currentViewB1,
                                 2: self.              ui.graphicsView_currentViewB2,
                                 3: self.ui.graphicsView_currentViewB3}

        # timer for accumulation start time
        self._accStartTime = datetime.now()

        # list of run numbers to process
        self._processedRunNumberList = list()

        # flag for 2D plotting
        self._2dMode = 'acc'  # options are 'acc', 'runs', 'unit' (for each refreshed workspace)
        # about 'runs' option
        self._2dStartRunNumber = None

        # peak integration
        self._integratePeakFlag = False
        self._minDPeakIntegration = None
        self._maxDPeakIntegration = None

        # mutexes
        self._bankSelectMutex = False

        # random seed
        random.seed(1)

        return

    def _init_widgets(self):
        """
        initialize some widgets
        :return:
        """
        # widgets to show/high previous reduced date
        self.ui.checkBox_showPrevReduced.setChecked(True)
        self.ui.lineEdit_showPrevNCycles.setText('1')

        self._bankSelectMutex = True
        self._set_bank_checkbox()
        self.ui.checkBox_2dBank1.setChecked(True)
        self._bankSelectMutex = False

        return

    # TEST TODO/NOW - recently implemented
    def _set_workspace_manager(self, max_acc_ws_number, accumulation_time, update_time):
        """
        set the workspace numbers, indicators and etc.
        Note: all the time given will be in seconds
        :param max_acc_ws_number: number of accumulated workspace that will be stored in memory
        :param accumulation_time: for long run, the time for a chopped section, i.e., an accumulation workspace's time
        :param update_time: frequency for update
        :return:
        """
        # check inputs
        assert isinstance(max_acc_ws_number, int), 'Maximum accumulation workspace number {0} must be' \
                                                   'an integer but not a {1}'.format(max_acc_ws_number,
                                                                                     type(max_acc_ws_number))
        assert isinstance(accumulation_time, int), 'blabla 2'
        assert isinstance(update_time, int), 'blabla 3'

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
        self._myRefreshTimeStep = update_time
        if accumulation_time % update_time == 0:
            self._myAccumulationTime = accumulation_time
        else:
            # accumulation time is not a multiplication to update/refresh time
            self._myAccumulationTime = (self._myAccumulationTime/self._myRefreshTimeStep + 1) * self._myRefreshTimeStep
            self.write_log(level='warning', message='Accumulation time is modified to {0}'
                                                    ''.format(self._myAccumulationTime))
        # END-IF
        self._myIncrementalWorkspaceNumber = self._myAccumulationTime / self._myRefreshTimeStep * 2  # leave some space
        self._myMaxIncrementalNumber = self._myAccumulationTime / self._myRefreshTimeStep

        # set the lists
        self._myIncrementalWorkspaceList = [None] * self._myIncrementalWorkspaceNumber
        self._myAccumulationWorkspaceList = [None] * self._myAccumulationWorkspaceNumber

        return

    def _set_bank_checkbox(self):
        """
        uncheck all the checkboxes for bank ID
        :return:
        """
        self._bankSelectMutex = True
        self.ui.checkBox_2dBank1.setChecked(False)
        self.ui.checkBox_2dBank2.setChecked(False)
        self.ui.checkBox_2dBank3.setChecked(False)
        self._bankSelectMutex = False

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

    def evt_bank1_changed(self):
        """
        handling event as any of the bank checkbox is checked or uncheced
        :return:
        """
        # return if mutex is on and no operation is required
        if self._bankSelectMutex:
            return

        # get the selected status
        checked = self.ui.checkBox_2dBank1.isChecked()

        # turn on mutex
        self._bankSelectMutex = True

        if not checked:
            # cannot be unchecked by itself
            self.ui.checkBox_2dBank1.setChecked(True)
            re_plot = False
        else:
            # disable others
            self._set_bank_checkbox()
            self.ui.checkBox_2dBank1.setChecked(True)
            # set flat to update 2D plot and re-set the current bank ID
            re_plot = True
            self._currentBankID = 1

        # turn off mutex
        self._bankSelectMutex = False

        # plot if it is True
        if re_plot:
            self.update_2d_plot()

        return

    def evt_bank2_changed(self):
        """
        handling event as any of
        :return:
        """
        # return if mutex is on and no operation is required
        if self._bankSelectMutex:
            return

        # get the selected status
        checked = self.ui.checkBox_2dBank2.isChecked()

        # turn on mutex
        self._bankSelectMutex = True

        if not checked:
            # cannot be unchecked by itself
            self.ui.checkBox_2dBank2.setChecked(True)
            re_plot = False
        else:
            # disable others
            self._set_bank_checkbox()
            self.ui.checkBox_2dBank2.setChecked(True)
            # set flat to update 2D plot and re-set the current bank ID
            re_plot = True
            self._currentBankID = 2

        # turn off mutex
        self._bankSelectMutex = False

        # plot if it is True
        if re_plot:
            self.update_2d_plot()

        return

    def evt_bank3_changed(self):
        """
        handling event as any of
        :return:
        """
        # return if mutex is on and no operation is required
        if self._bankSelectMutex:
            return

        # get the selected status
        checked = self.ui.checkBox_2dBank3.isChecked()

        # turn on mutex
        self._bankSelectMutex = True

        if not checked:
            # cannot be unchecked by itself
            self.ui.checkBox_2dBank3.setChecked(True)
            re_plot = False
        else:
            # disable others
            self._set_bank_checkbox()
            self.ui.checkBox_2dBank3.setChecked(True)
            # set flat to update 2D plot and re-set the current bank ID
            re_plot = True
            self._currentBankID = 3

        # turn off mutex
        self._bankSelectMutex = False

        # plot if it is True
        if re_plot:
            self.update_2d_plot()

        return

    def add_new_workspace(self, ws_name):
        """
        add a new workspace to the list.  if the list is full, then replace the existing one.
        :param ws_name:
        :return:
        """
        # replace previous one
        if self._myIncrementalWorkspaceList[self._myIncrementalListIndex] is not None:
            prev_ws_name = self._myIncrementalWorkspaceList[self._myIncrementalListIndex]
            self._controller.delete_workspace(prev_ws_name)

        # set the new one
        self._myIncrementalWorkspaceList[self._myIncrementalListIndex] = ws_name

        # update index
        self._myIncrementalListIndex += 1
        if self._myIncrementalListIndex == len(self._myIncrementalWorkspaceList):
            self._myIncrementalListIndex = 0
        elif self._myIncrementalListIndex > len(self._myIncrementalWorkspaceList):
            raise RuntimeError("Impossible for myListIndex")

        return

    def do_clear_log(self):
        """ clear the live data processing log
        :return:
        """
        self.ui.plainTextEdit_Log.clear()

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

    def do_refresh_2d(self):
        """
        refresh 2D contour view
        :return:
        """
        self.update_2d_plot()

        return

    def do_setup_gpplot(self):
        """ set up general-purpose view by ...
        :return:
        """
        if self._gpPlotSetupDialog is None:
            self._gpPlotSetupDialog = SampleLogPlotSetupDialog(self)

        # get axis
        curr_ws_name = self._myIncrementalWorkspaceList[self._myIncrementalListIndex - 1]
        logs = helper.get_sample_log_names(curr_ws_name, smart=True)
        x_axis_logs = ['Time']
        # TODO/LATER: x_axis_logs.extend(logs)

        self._gpPlotSetupDialog.set_axis_options(x_axis_logs, logs, reset=True)
        self._gpPlotSetupDialog.show()

        return

    # TEST TODO - newly implemented
    def do_set_roi(self):
        """ set the region of interest by set the X limits on the canvas
        :return:
        """
        try:
            left_x_bound = float(str(self.ui.lineEdit_roiStart.text()).strip())
            # self.ui.graphicsView_currentViewB1.setXYLimit(xmin=left_x_bound)
            # self.ui.graphicsView_currentViewB2.setXYLimit(xmin=left_x_bound)
            # self.ui.graphicsView_currentViewB3.setXYLimit(xmin=left_x_bound)
            self._bankViewDMin = left_x_bound
        except ValueError:
            # keep as before
            left_x_bound = None

        try:
            right_x_bound = float(str(self.ui.lineEdit_roiEnd.text()).strip())
            # self.ui.graphicsView_currentViewB1.setXYLimit(xmax=right_x_bound)
            # self.ui.graphicsView_currentViewB2.setXYLimit(xmax=right_x_bound)
            # self.ui.graphicsView_currentViewB3.setXYLimit(xmax=right_x_bound)
            self._bankViewDMax = right_x_bound
        except ValueError:
            # keep as before
            right_x_bound = None

        # set limit
        self.set_bank_view_roi(left_x_bound, right_x_bound)

        return

    def set_bank_view_roi(self, left_x_bound, right_x_bound):
        """
        set region of interest on the 3 bank viewer
        :return:
        """
        self.ui.graphicsView_currentViewB1.setXYLimit(xmin=left_x_bound, xmax=right_x_bound)
        self.ui.graphicsView_currentViewB2.setXYLimit(xmin=left_x_bound, xmax=right_x_bound)
        self.ui.graphicsView_currentViewB3.setXYLimit(xmin=left_x_bound, xmax=right_x_bound)

    def do_start_live(self):
        """
        start live data reduction and view
        :return:
        """
        # start timer
        self._checkStateTimer = TimerThread(self._myRefreshTimeStep, self)
        self._checkStateTimer.start()

        # start start listener
        self._controller.run()

        return

    def do_stop_live(self):
        """
        stop live data reduction and view
        :return:
        """
        self._checkStateTimer.stop()

        self._controller.stop()

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

    # TODO/TEST/NEW Method
    def get_last_n_round_workspaces(self, last):
        """
        get the last round of workspaces
        :param last:
        :return: 2-tuple: list as workspace names and list as indexes of workspaces
        """
        assert isinstance(last, int), 'Last N intervals {0} must be given by an integer,' \
                                      'but not a {1}.'.format(last, type(last))
        if last <= 0:
            raise RuntimeError('Last N intervals must be a positive number.')

        # get list of workspace to plot
        ws_name_list = list()
        ws_index_list = list()
        for last_i in range(1, last+1):
            # get current workspace's position in the list
            ws_list_index = self._myIncrementalListIndex - last_i
            if ws_list_index < 0:
                # loop back to the end of the list
                ws_list_index += len(self._myIncrementalWorkspaceList)

            # get workspace name
            try:
                ws_name_i = self._myIncrementalWorkspaceList[ws_list_index]
            except IndexError as index_err:
                raise RuntimeError('Index {0} is out of incremental workspace range {1} due to {2}.'
                                   ''.format(ws_list_index, len(self._myIncrementalWorkspaceList),
                                             index_err))
            if ws_name_i is None:
                # print '[DB...BAT] workspace {0} name is None. CurrWSIndex = {1}. Last_i = {2} Workspace
                # names are {3}' \
                #       ''.format(ws_list_index, self._myListIndex, last_i, self._myWorkspaceList)
                break
            elif helper.workspace_does_exist(ws_name_i) is False:
                # print '[DB...BAT] workspace {0} does not exist.'.format(ws_name_i)
                break
            else:
                ws_name_list.append(ws_name_i)
                ws_index_list.append(last_i)
        # END-FOR

        # reverse the order
        ws_name_list.reverse()
        ws_index_list.reverse()

        return ws_name_list, ws_index_list

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
                print '[DB...BAT] Last {0}-th accumulated index = {1}, Others {2} and {3}' \
                      ''.format(inverse_index, list_index, self._myAccumulationListIndex,
                                self._inAccumulationWorkspaceName)
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
            data_set_dict, current_unit = helper.get_data_from_workspace(workspace_name=ws_name_i,
                                                                         bank_id=bank_id, target_unit='dSpacing',
                                                                         point_data=True, start_bank_id=1)
            # check .. here .. # TODO/DEBUG/REMOVE BUG FIXED
            data_bank = data_set_dict[bank_id]
            vec_y = data_bank[1]
            info = 'Workspace {0} Bank ID {1} Min and Max Y are {2} and {3}.'.format(ws_name_i, bank_id,
                                                                                     numpy.min(vec_y), numpy.max(vec_y))

            self.write_log('information', info)
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
        ws_name_list, ws_index_list = self.get_last_n_round_workspaces(last)

        # get data
        data_set = dict()
        for index, ws_name in enumerate(ws_name_list):
            data_set_dict, current_unit = helper.get_data_from_workspace(workspace_name=ws_name,
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

        # plot
        for bank_id in range(1, 4):
            # get data
            try:
                vec_y_i = in_sum_ws.readY(bank_id-1)
                vec_x_i = in_sum_ws.readX(bank_id-1)[:len(vec_y_i)]
                color_i = self._bankColorDict[bank_id]
                label_i = 'in accumulation bank {0}'.format(bank_id)
                self._mainGraphicDict[bank_id].plot_current_plot(vec_x_i, vec_y_i, color_i, label_i, target_unit)
            except RuntimeError as run_err:
                print '[ERROR] Unable to get data from workspace {0} due to {1}'.format(in_sum_ws_name, run_err)
                return

            if target_unit == 'TOF':
                self._mainGraphicDict[bank_id].setXYLimit(0, 70000)
            else:
                self._mainGraphicDict[bank_id].setXYLimit(0, 5.0)
        # END-FOR

        if is_new_ws:
            self._controller.delete_workspace(in_sum_name)

        # Plot 2D
        self.update_2d_plot()

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
        prev_ws_index = self._myAccumulationListIndex - 1 - int(self.ui.lineEdit_showPrevNCycles.text())
        if self._myAccumulationWorkspaceList[prev_ws_index] is None:
            message = 'There are only {0} previously accumulated and reduced workspace. ' \
                      'Unable to access previously {1}-th workspace.'.format(len(self._myAccumulationWorkspaceList),
                                                                       abs(prev_ws_index) - 1)
            self.write_log('error', message)
            return

        else:
            prev_ws_name = self._myAccumulationWorkspaceList[prev_ws_index]
        # END-IF-ELSE

        # skip if the previous plotted is sam
        if prev_ws_name == self._plotPrevCycleName:
            # minor/TODO/NOW - refactor to method
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
        for bank_id in range(1, 4):
            vec_y = prev_ws.readY(bank_id-1)[:]
            vec_x = prev_ws.readX(bank_id-1)[:len(vec_y)]
            self._mainGraphicDict[bank_id].plot_previous_run(vec_x, vec_y, 'black', line_label, target_unit)

        # clean
        if is_new_ws:
            self._controller.delete_workspace(prev_ws_name_tmp)

        return

    def integrate_peak_live(self, d_min, d_max):
        """
        set up to integrate peak with live data
        :param d_min:
        :param d_max:
        :return:
        """
        # integrate peak
        self._controller.integrate_peaks(self._myAccumulationWorkspaceList, d_min, d_max)

        # set the status flags
        self._integratePeakFlag = True
        self._minDPeakIntegration = d_min
        self._maxDPeakIntegration = d_max
        self._currSampleLogX = 'Time'

        return

    def load_sample_log(self, y_axis_name, last_n_intervals):
        """
        load a sample log from last N time intervals
        :param y_axis_name:
        :param last_n_intervals: starting from 1 because there is NO 'current' intervals as a workspace in ADS
        :return:
        """
        # check input
        assert isinstance(y_axis_name, str), 'Y-axis (sample log) name {0} must be a string but not a {1}.' \
                                             ''.format(y_axis_name, type(y_axis_name))
        assert isinstance(last_n_intervals, int), 'Last {0} interval must be an integer but not a {1}.' \
                                                  ''.format(last_n_intervals, type(last_n_intervals))
        if last_n_intervals <= 0:
            raise RuntimeError('Last {0} intervals cannot be negative.'.format(last_n_intervals))

        # get the workspace name list
        ws_name_list, index_list = self.get_last_n_round_workspaces(last_n_intervals)
        print '[DB...BAT] Last {0} intervals: {1}'.format(last_n_intervals, ws_name_list)

        time_vec, log_value_vec = self._controller.parse_sample_log(ws_name_list, y_axis_name)

        return time_vec, log_value_vec

    def plot_integrate_peak(self, d_min, d_max):
        """
        blabla
        :param d_min:
        :param d_max:
        :return:
        """
        self._controller.integrate_peaks(self._myAccumulationWorkspaceList, 0, d_min, d_max)

        vec_time, vec_peak_intensity = self._controller.get_peak_intensities(bank_id=1, time0=self._liveStartTimeStamp)

        # TODO/ISSUE/NOW Better to use update
        self.ui.graphicsView_comparison.clear_all_lines()
        self.ui.graphicsView_comparison.add_plot(vec_time, vec_peak_intensity,
                                                 label='Bank 1 Intensity', line_style='--', marker='o', color='blue')

        vec_time, vec_peak_intensity = self._controller.get_peak_intensities(bank_id=2, time0=self._liveStartTimeStamp)
        self.ui.graphicsView_comparison.add_plot(vec_time, vec_peak_intensity,
                                                 label='Bank 2 Intensity', line_style='--', marker='D', color='red')

        return

    def plot_log_with_reduced(self, x_axis_name, y_axis_name):
        """
        plot sample logs with previously reduced data
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

        # TODO/NOW/ASAP
        whatever()

    def plot_new_log_live(self, x_axis_name, y_axis_name):
        """
        plot the log in live data by loading the previously accumulated runs
        :param x_axis_name:
        :param y_axis_name:
        :return:
        """

        # TODO/NOW/TODO/IMPLEMENT

        # start from the current in-accumulation run
        blabla

        # trace back to previously accumulated runs until run number changed to non-zero
        blabla

    def plot_log_live(self, x_axis_name, y_axis_name):
        """
        Plot a sample log in live time
        Note: this model works in most case except a new sample log is chosen to
        Required class variables
          - self._currSampleLog = None
          - self._currSampleLogTimeVector = None
          - self._currSampleLogValueVector = None
        :param x_axis_name:
        :param y_axis_name:
        :return:
        """
        # parse the user-specified X and Y axis name and process name in case of 'name (#)'
        x_axis_name = str(x_axis_name).split('(')[0].strip()
        y_axis_name = str(y_axis_name).split('(')[0].strip()

        # determine to append or start from new
        if self._currSampleLogX != x_axis_name or self._currSampleLogY != y_axis_name \
                or self._currSampleLogTimeVector is None:
            append_log = False
            # print '[DB] Log View X-axis: {0} vs {1}'.format(self._currSampleLogX, x_axis_name)
            # print '[DB] Log View Y-axis: {0} vs {1}'.format(self._currSampleLogY, y_axis_name)
            # print '[DB] Sample log time vector: {0}'.format(self._currSampleLogTimeVector)

        else:
            append_log = True

        # get the data
        if x_axis_name == 'Time':
            # regular time-value plot
            if append_log:
                date_time_vec, value_vec = self.load_sample_log(y_axis_name, last_n_intervals=1)
                time_vec = self._controller.convert_time_stamps(date_time_vec, relative=self._logStartTime)
                self._currSampleLogTimeVector = numpy.append(self._currSampleLogTimeVector, time_vec)
                self._currSampleLogValueVector = numpy.append(self._currSampleLogValueVector, value_vec)
                debug_message = '[Append Mode] New time stamps: {0}... Log T0 = {1}' \
                                ''.format(time_vec[0], self._logStartTime)
                self.write_log('debug', debug_message)
            else:
                # New mode
                # TODO/ISSUE - Implement LastNLog!
                LastNLog = 1
                date_time_vec, value_vec = self.load_sample_log(y_axis_name, last_n_intervals=LastNLog)
                # set log start time
                # TODO/ISSUE/ - shall give users with more choice
                self._logStartTime = date_time_vec[0]

                time_vec = self._controller.convert_time_stamps(date_time_vec, relative=self._logStartTime)
                self._currSampleLogTimeVector = time_vec
                self._currSampleLogValueVector = value_vec
            # END-IF-ELSE
        else:
            # relation between two sample logs: not implemented
            raise RuntimeError('Develop ASAP')

        # clear all lines
        # TODO/ISSUE/NOW: need to consider to use a flag to determine whether to update or plot a new line
        self.ui.graphicsView_comparison.clear_all_lines()
        self.ui.graphicsView_comparison.add_plot(self._currSampleLogTimeVector, self._currSampleLogValueVector,
                                                 label=y_axis_name)

        # all success: keep it in record for auto update
        self._currSampleLogX = x_axis_name
        self._currSampleLogY = y_axis_name
        # turn off the flag to plot integrated peaks
        self._integratePeakFlag = False

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
            helper.mtd_convert_units(ws_name_i, 'dSpacing')

            # add new workspace to data manager
            self.add_new_workspace(ws_name_i)

            # update info
            self.ui.lineEdit_newestReducedWorkspace.setText(ws_name_i)

            # get reference to workspace
            workspace_i = helper.retrieve_workspace(ws_name_i)
            run_number_i = workspace_i.getRunNumber()
            self.ui.lineEdit_runNumber.setText(str(run_number_i))

            # live data start time
            if self._liveStartTimeStamp is None:
                self._liveStartTimeStamp = workspace_i.run().getProperty('proton_charge').firstTime()

            # skip non-matrix workspace or workspace sounds not right
            if not (helper.is_matrix_workspace(ws_name_i) and 3 <= workspace_i.getNumberHistograms() < 20):
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
            db_msg = 'Unit = {0} Range = {1}, {2}'.format(self.ui.comboBox_currUnits.currentText(), self._bankViewDMin, self._bankViewDMax)
            self.write_log('debug', db_msg)
            if str(self.ui.comboBox_currUnits.currentText()) == 'dSpacing':
                self.set_bank_view_roi(self._bankViewDMin, self._bankViewDMax)

            # update log
            if self._currSampleLogX is not None and self._currSampleLogY is not None:
                self.plot_log_live(self._currSampleLogX, self._currSampleLogY)
            elif self._currSampleLogX == 'Time' and self._integratePeakFlag is True:
                self.plot_integrate_peak(self._minDPeakIntegration, self._maxDPeakIntegration)
        # END-FOR

        return

    def set_accumulation_time(self, accumulation_time):
        """
        set the accumulation time
        :param accumulation_time:
        :return:
        """
        # check
        assert isinstance(accumulation_time, int), 'blabla2'

        self._set_workspace_manager(max_acc_ws_number=self._myAccumulationWorkspaceNumber,
                                    accumulation_time=accumulation_time,
                                    update_time=self._myRefreshTimeStep)

        return

    def set_plot_run(self, plot_runs, start_run):
        """
        set the 2D figure to plot reduced runs instead of accumulated live data
        :param plot_runs:
        :param start_run:
        :return:
        """
        # check inputs
        assert isinstance(plot_runs, bool), 'blabla5'

        # set!
        if plot_runs:
            # plot reduced runs in 2D view
            self._2dMode = 'runs'
            assert isinstance(start_run, int), 'blabla8'

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
        assert isinstance(update_period, int), 'blabla3'

        self._set_workspace_manager(max_acc_ws_number=self._myAccumulationWorkspaceNumber,
                                    accumulation_time=self._myAccumulationTime,
                                    update_time=update_period)

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
            helper.clone_workspace(ws_name, accumulate_name)
            self._inAccumulationWorkspaceName = accumulate_name

            # add to list
            list_index = self._myAccumulationListIndex % self._myAccumulationWorkspaceNumber

            if self._myAccumulationWorkspaceList[list_index] is not None:
                old_ws_name = self._myAccumulationWorkspaceList[list_index]
                print '[INFO] Delete old workspace {0}'.format(old_ws_name)
                self._controller.delete_workspace(old_ws_name)
            self._myAccumulationWorkspaceList[list_index] = accumulate_name
            print '[DB...BAT] Acc workspace list {0} has workspace {1}' \
                  ''.format(list_index, self._myAccumulationWorkspaceList[list_index])

            # restart timer
            self._accStartTime = datetime.now()

            # increase list index
            self._myAccumulationListIndex += 1

            # set the info
            self.ui.lineEdit_inAccWsName.setText(self._inAccumulationWorkspaceName)
            self.ui.spinBox_currentIndex.setValue(self._myAccumulationListIndex)

        else:
            # add to existing accumulation workspace
            ws_in_acc = helper.retrieve_workspace(self._inAccumulationWorkspaceName, raise_if_not_exist=True)

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
            self._controller.sum_workspaces([self._inAccumulationWorkspaceName, workspace_i],
                                            self._inAccumulationWorkspaceName)
        # END-IF-ELSE

        # update the list of source accumulated workspace
        self._inAccumulationIncrementalWorkspaceList.append(ws_name)

        return

    def update_2d_plot(self):
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

        # get bank ID
        bank_id = self._currentBankID

        # get the last N time-intervals and create the meshdata
        last_n_run = parse_set_last_n()
        # retrieve data

        # TODO/ISSUE/NOW/FIXME - It is in a debug mode
        self._2dMode = 'acc'                        #
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
            self.ui.graphicsView_2D.plot_contour(data_set_dict)

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

        # update GUI
        total_index = self._controller.get_live_counter()
        self.ui.spinBox_totalIndex.setValue(total_index)

        # print '[UI-DB] Acc Index = {0}, Total Index = {1}'.format(self._currAccumulateIndex, total_index)

        # some counter += 1

        # message = '{0}\nNew Workspace: {1}'.format(ws_name_list, new_ws_name_list)
        message = ''
        for ws_name in new_ws_name_list:
            ws_i = helper.retrieve_workspace(ws_name)
            if ws_i.id() == 'Workspace2D' or ws_i.id() == 'EventWorkspace' and ws_i.name().startswith('output'):
                message += 'New workspace {0}: number of spectra = {1}'.format(ws_name, ws_i.getNumberHistograms())
        # END-FOR
        self.write_log('information', message)

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
