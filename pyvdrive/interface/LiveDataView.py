from datetime import datetime
from PyQt4 import QtCore
from PyQt4 import QtGui
import random
import time
import numpy

from LiveDataChildWindows import SampleLogPlotSetupDialog
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
# 1. 2D contour plot on different bank

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
    # decide whether a new workspace shall be started
    # TODO/ISSUE/NOW - This shall be made more flexible!
    WORKSPACE_LIMIT = 5 * 60 / 10

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
        self._myChildWindows = list()

        # define data structure
        self._myTimeStep = 10  # seconds
        self._myWorkspaceNumber = 360  # containing 1 hour data for dT = 10 seconds
        self._myWorkspaceList = [None] * self._myWorkspaceNumber  # a holder for workspace names
        self._myListIndex = 0  # This is always the next index to write except in add...()

        # summed workspace list
        self._mySummedWorkspaceList = list()   # name of summed workspaces

        # index for accumulated workspaces
        self._currAccumulateIndex = 0
        # about previous round pot
        self._plotPrevCycleName = None
        # Bank ID (current): shall be updated with event to handle change of bank ID selection
        self._currentBankID = 1

        # Live sample log related
        self._currSampleLogX = None
        self._currSampleLogY = None
        self._currSampleLogTimeVector = None
        self._currSampleLogValueVector = None
        self._logStartTime = None

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

        # collection of workspace names
        self._workspaceSet = set()

        # accumulated workspace
        self._accumulatedWorkspace = None
        self._accumulatedList = list()  # list of accumulated workspace

        self._bankColorDict = {1: 'red', 2: 'blue', 3: 'green'}
        self._mainGraphicDict = {1: self.ui.graphicsView_currentViewB1,
                                 2: self.ui.graphicsView_currentViewB2,
                                 3: self.ui.graphicsView_currentViewB3}

        # timer for accumulation start time
        self._accStartTime = datetime.now()
        self._processedRunNumberList = list()

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
        if self._myWorkspaceList[self._myListIndex] is not None:
            prev_ws_name = self._myWorkspaceList[self._myListIndex]
            self._controller.delete_workspace(prev_ws_name)

        # set the new one
        self._myWorkspaceList[self._myListIndex] = ws_name

        # update index
        self._myListIndex += 1
        if self._myListIndex == len(self._myWorkspaceList):
            self._myListIndex = 0
        elif self._myListIndex > len(self._myWorkspaceList):
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
        curr_ws_name = self._myWorkspaceList[self._myListIndex-1]
        logs = helper.get_sample_log_names(curr_ws_name, smart=True)
        x_axis_logs = ['Time']
        # TODO/LATER: x_axis_logs.extend(logs)

        self._gpPlotSetupDialog.set_axis_options(x_axis_logs, logs, reset=True)
        self._gpPlotSetupDialog.show()

        return

    def do_set_roi(self):
        """
        blabla
        :return:
        """
        # TODO/ISSUE/TODO/FIXME - ASAP

        return

    def do_start_live(self):
        """
        start live data reduction and view
        :return:
        """
        # start timer
        self._checkStateTimer = TimerThread(self._myTimeStep, self)
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
            ws_list_index = self._myListIndex - last_i
            if ws_list_index < 0:
                # loop back to the end of the list
                ws_list_index += len(self._myWorkspaceList)

            # get workspace name
            ws_name_i = self._myWorkspaceList[ws_list_index]
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
        # TODO/TODO/ISSUE/NOW
        return

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
        self.ui.plainTextEdit_Log.appendPlainText('[INFO] Plot in-accumulation data of unit {0}'.format(target_unit))

        # check
        if self._accumulatedWorkspace is None:
            self.ui.plainTextEdit_Log.appendPlainText('[WARNING] No in-accumulation workspace in ADS.')
            return

        # get the workspace names
        in_sum_name = '_temp_curr_ws_{0}'.format(random.randint(1, 10000))
        in_sum_ws, is_new_ws = self._controller.convert_unit(self._accumulatedWorkspace, target_unit, in_sum_name)

        # plot
        for bank_id in range(1, 4):
            # get data
            vec_y_i = in_sum_ws.readY(bank_id-1)
            vec_x_i = in_sum_ws.readX(bank_id-1)[:len(vec_y_i)]
            color_i = self._bankColorDict[bank_id]
            label_i = 'in accumulation bank {0}'.format(bank_id)
            self._mainGraphicDict[bank_id].plot_current_plot(vec_x_i, vec_y_i, color_i, label_i, target_unit)

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
        plot data collected and reduced in previous cycles
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

        # plot previous ones
        prev_ws_index = -1 - int(self.ui.lineEdit_showPrevNCycles.text())
        if len(self._mySummedWorkspaceList) < abs(prev_ws_index):
            self.ui.plainTextEdit_Log.appendPlainText(
                'There are only {0} previously accumulated and reduced workspace.  '
                'Unable to access previously {1}-th workspace.'.format(len(self._mySummedWorkspaceList),
                                                                       abs(prev_ws_index)-1))
            return
        else:
            prev_ws = self._mySummedWorkspaceList[prev_ws_index]
            prev_ws_name = prev_ws.name()

        # skip if the previous plotted is sam
        if prev_ws_name == self._plotPrevCycleName:
            debug_message = 'Previous cycle data {0} is same as currently plotted. No need to plot again.' \
                            ''.format(prev_ws_name)
            self.ui.plainTextEdit_Log.appendPlainText('{0}\n'.format(debug_message))
            return
        else:
            self._plotPrevCycleName = prev_ws_name

        # get new unit
        target_unit = str(self.ui.comboBox_currUnits.currentText())
        prev_ws_name_tmp = '_temp_prev_ws_{0}'.format(random.randint(1, 10000))
        prev_ws, is_new_ws = self._controller.convert_unit(prev_ws, target_unit, prev_ws_name_tmp)

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

    def plot_log_live(self, x_axis_name, y_axis_name):
        """
        Plot a sample log in live time
        Required class variables
          - self._currSampleLog = None
          - self._currSampleLogTimeVector = None
          - self._currSampleLogValueVector = None
        :param x_axis_name:
        :param y_axis_name:
        :return:
        """
        # parse the user-specified X and Y axis name
        x_axis_name = str(x_axis_name)
        y_axis_name = str(y_axis_name)

        # process name in case of 'name (#)'
        x_axis_name = x_axis_name.split('(')[0].strip()
        y_axis_name = y_axis_name.split('(')[0].strip()

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
                print '[DB...BAT] {0}'.format(debug_message)
                self.ui.plainTextEdit_Log.appendPlainText('{0}\n'.format(debug_message))
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
                self.ui.plainTextEdit_Log.appendPlainText('Processing new workspace {0}'.format(ws_name_i))
            else:
                # also a new workspace might be the accumulated workspace
                continue

            # add new workspace to data manager
            self.add_new_workspace(ws_name_i)

            # get reference to workspace
            workspace_i = helper.retrieve_workspace(ws_name_i)
            run_number_i = workspace_i.getRunNumber()
            self.ui.lineEdit_runNumber.setText(str(run_number_i))

            # skip non-matrix workspace or workspace sounds not right
            if not (helper.is_matrix_workspace(ws_name_i) and 3 <= workspace_i.getNumberHistograms() < 20):
                # skip weird workspace
                log_message = 'Workspace {0} of type {1} is not expected.\n'.format(workspace_i, type(workspace_i))
                self.ui.plainTextEdit_Log.setPlainText(log_message)
                continue

            # now it is the workspace that is to plot
            self.sum_incremental_workspaces(workspace_i)
            #  accumulate_name = self._accumulatedWorkspace.name()

            # always plot the current in-accumulation one
            self.plot_data_in_accumulation()

            # previous one if it is checked to plot
            if self.ui.checkBox_showPrevReduced.isChecked():
                self.plot_data_previous_cycle()

            # update log
            if self._currSampleLogX is not None and self._currSampleLogY is not None:
                self.plot_log_live(self._currSampleLogX, self._currSampleLogY)
        # END-FOR

        return

    def sum_incremental_workspaces(self, workspace_i):
        """

        :return:
        """
        ws_name = workspace_i.name()
        if self._accumulatedWorkspace is None or len(self._accumulatedList) == VulcanLiveDataView.WORKSPACE_LIMIT:
            # reset if pre-existing of accumulated workspace
            self._accumulatedList = list()

            # clone workspace
            accumulate_name = 'Accumulated_{0}'.format(self._currAccumulateIndex)
            self._accumulatedWorkspace = helper.clone_workspace(ws_name, accumulate_name)

            # append to list
            self._mySummedWorkspaceList.append(self._accumulatedWorkspace)

            # restart time
            self._accStartTime = datetime.now()

        else:
            # add to existing
            if self._accumulatedWorkspace.getNumberHistograms() != workspace_i.getNumberHistograms():
                raise RuntimeError('Accumulated workspace {0} has different number of spectra ({1}) than the '
                                   'incremental workspace {2} ({3}).'
                                   ''.format(self._accumulatedWorkspace.name(),
                                             self._accumulatedWorkspace.getNumberHistograms(),
                                             workspace_i.getNumberHistograms.name(),
                                             workspace_i.getNumberHistograms()))

            for iws in range(workspace_i.getNumberHistograms()):
                if len(self._accumulatedWorkspace.readY(iws)) != len(workspace_i.readY(iws)):
                    raise RuntimeError('Spectrum {0}: accumulated workspace {1} has a different X size ({2}) than '
                                       'incremental workspace {3} ({4}).'
                                       ''.format(iws, self._accumulatedWorkspace.name(),
                                                 len(self._accumulatedWorkspace.readX(iws)),
                                                 workspace_i.name(),
                                                 len(workspace_i.readX(iws))))
                # END-IF

                self._accumulatedWorkspace.setY(iws, self._accumulatedWorkspace.readY(iws) + workspace_i.readY(iws))
            # END-iws

            # update the workspace
            self._mySummedWorkspaceList[-1] = self._accumulatedWorkspace

        # update the list of source accumulated workspace
        self._accumulatedList.append(ws_name)

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
        data_set_dict = self.get_last_n_round_data(last=last_n_run, bank_id=bank_id)

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
            self.ui.plainTextEdit_Log.setPlainText('[Error]: {0}'.format(run_err))
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
        self.ui.spinBox_currentIndex.setValue(self._currAccumulateIndex)
        total_index = self._controller.get_live_counter()
        self.ui.spinBox_totalIndex.setValue(total_index)

        # print '[UI-DB] Acc Index = {0}, Total Index = {1}'.format(self._currAccumulateIndex, total_index)

        self._currAccumulateIndex += 1

        # message = '{0}\nNew Workspace: {1}'.format(ws_name_list, new_ws_name_list)
        message = ''
        for ws_name in new_ws_name_list:
            ws_i = helper.retrieve_workspace(ws_name)
            if ws_i.id() == 'Workspace2D' or ws_i.id() == 'EventWorkspace' and ws_i.name().startswith('output'):
                message += 'New workspace {0}: number of spectra = {1}'.format(ws_name, ws_i.getNumberHistograms())
        # self.ui.plainTextEdit_Log.clear()
        self.ui.plainTextEdit_Log.appendPlainText(message)

        return


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
