from PyQt4 import QtCore
from PyQt4 import QtGui

import gui.ui_LiveDataView as ui_LiveDataView
import PyVDrive.lib.LiveDataDriver as ld
import PyVDrive.lib.mantid_helper as helper


# TODO/ISSUE/FUTURE - Consider https://www.tutorialspoint.com/pyqt/pyqt_qsplitter_widget.htm


class VulcanLiveDataView(QtGui.QMainWindow):
    """
    Reduced live data viewer for VULCAN
    """
    def __init__(self, parent, live_driver):
        """
        init
        :param parent:
        """
        # call parent
        super(VulcanLiveDataView, self).__init__(parent)

        # get hold of controller/driver
        self._controller = live_driver

        # define data structure
        self._myTimeStep = 10  # seconds
        self._myWorkspaceNumber = 360  # containing 1 hour data for dT = 10 seconds
        self._myWorkspaceList = [None] * self._myWorkspaceNumber  # a holder for workspace names
        self._myListIndex = 0

        self._currAccumulateIndex = 0  # index for accumulated workspaces

        # start UI
        self.ui = ui_LiveDataView.Ui_MainWindow()
        self.ui.setupUi(self)

        # set up the event handlers
        self.connect(self.ui.pushButton_startLiveReduction, QtCore.SIGNAL('clicked()'),
                     self.do_start_live)
        self.connect(self.ui.pushButton_stopLiveReduction, QtCore.SIGNAL('clicked()'),
                     self.do_stop_live)

        # menu bar
        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'),
                     self.do_quit)
        self.connect(self.ui.actionClear_Logs, QtCore.SIGNAL('triggered()'),
                     self.do_clear_log)
        self.connect(self.ui.actionIPython_Console, QtCore.SIGNAL('triggered()'),
                     self.do_launch_ipython)

        # other widgets
        self.connect(self.ui.comboBox_currUnits, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_change_unit)

        # multiple thread pool
        self._checkStateTimer = None

        # collection of workspace names
        self._workspaceSet = set()

        # accumulated workspace
        self._accumulatedWorkspace = None
        self._accumulatedList = list()  # list of accumulated workspace

        return

    def do_clear_log(self):
        """

        :return:
        """
        self.ui.plainTextEdit_Log.clear()

        return

    def do_launch_ipython(self):
        """

        :return:
        """

        # TODO/ISSUE/NOW - blabla

        return

    def do_quit(self):
        """

        :return:
        """
        # stop live view
        self.do_stop_live()

        self.close()

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
        self._controller = ld.LiveDataDriver()
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

    def evt_change_unit(self):
        """ blabla """
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

        return

    def process_new_workspaces(self, ws_name_list):
        """
        blabla
        :param ws_name_list:
        :return:
        """
        # check
        assert isinstance(ws_name_list, list), 'blabla'
        if len(ws_name_list) == 0:
            return

        # TODO/ISSUE/NOW - Shall be refactored to other part of the code
        COLOR = {1: 'black', 2: 'red', 3: 'blue'}
        self._mainGraphicDict = {1: self.ui.graphicsView_currentViewB1,
                                 2: self.ui.graphicsView_currentViewB2,
                                 3: self.ui.graphicsView_currentViewB3}

        # sort
        ws_name_list.sort(reverse=True)
        for ws_name in ws_name_list:
            # skip temporary workspace
            if ws_name.startswith('temp'):
                continue

            if ws_name.startswith('output'):
                self.ui.plainTextEdit_Log.appendPlainText('Processing new workspace {0}'.format(ws_name))
            else:
                # also a new workspace might be the accumulated workspace
                continue

            # get reference to workspace
            workspace_i = helper.retrieve_workspace(ws_name)

            # skip non-matrix workspace or workspace sounds not right
            if not (helper.is_matrix_workspace(ws_name) and 3 <= workspace_i.getNumberHistograms() < 20):
                # skip weird workspace
                log_message = 'Workspace {0} of type {1} is not expected.\n'.format(workspace_i, type(workspace_i))
                self.ui.plainTextEdit_Log.setPlainText(log_message)
                continue

            # decide whether a new workspace shall be started
            WORKSPACE_LIMIT = 5 * 60 / 10
            prev_acc_name = None
            if self._accumulatedWorkspace is None or len(self._accumulatedList) == WORKSPACE_LIMIT:
                # reset if pre-existing of accumulated workspace
                if self._accumulatedWorkspace is not None:
                    prev_acc_name = self._accumulatedWorkspace.name()
                    self._accumulatedList = list()
                # clone workspace
                accumulate_name = 'FiveMinutes_{0}'.format(self._currAccumulateIndex)
                self._accumulatedWorkspace = helper.clone_workspace(ws_name, accumulate_name)

            else:
                # add
                self._accumulatedWorkspace += workspace_i
                accumulate_name = self._accumulatedWorkspace.name()
            self._accumulatedList.append(ws_name)

            # plot
            # self.ui.plainTextEdit_Log.clear()
            self.ui.plainTextEdit_Log.appendPlainText('Plotting {0}: X-size = {1}'
                                                      ''.format(accumulate_name,
                                                                len(self._accumulatedWorkspace.readX(0))))
            self.ui.plainTextEdit_Log.appendPlainText('\n')

            data_set_dict = dict()
            current_unit = 'TOF'
            for i in range(3):
                vec_x = self._accumulatedWorkspace.readX(i)[:-1]
                vec_y = self._accumulatedWorkspace.readY(i)
                data_set_dict[i+1] = vec_x, vec_y, None

            # data_set_dict, current_unit = helper.get_data_from_workspace(workspace_name=ws_name)
            #
            for bank_id in data_set_dict.keys():
                vec_x, vec_y, vec_e = data_set_dict[bank_id]
                self.ui.plainTextEdit_Log.appendPlainText('X range: {0}, {1}.  Y range: {2}, {3}'
                                                          ''.format(vec_x[0], vec_x[-1], min(vec_y), max(vec_y)))
                self._mainGraphicDict[bank_id].clear_all_lines()
                self._mainGraphicDict[bank_id].add_plot_1d(vec_x, vec_y, color=COLOR[bank_id],
                                                           label='{0}: bank {1}'.format(accumulate_name, bank_id),
                                                           x_label=current_unit)

            # update other information
            num_events = int(self._controller.get_live_events())
            self.ui.lineEdit_numberEventsNewsReduced.setText(str(num_events))
            self.ui.lineEdit_newestReducedWorkspace.setText(str(ws_name))

            # plot previous
            if prev_acc_name is not None:
                prev_acc_ws = helper.retrieve_workspace(prev_acc_name)
                data_set_dict = dict()
                current_unit = 'TOF'
                for i in range(3):
                    vec_x = prev_acc_ws.readX(i)[:-1]
                    vec_y = prev_acc_ws.readY(i)
                    data_set_dict[i + 1] = vec_x, vec_y, None

                # data_set_dict, current_unit = helper.get_data_from_workspace(workspace_name=ws_name)
                #
                # self.ui.graphicsView_previous.clear_all_lines()
                # need to read into option
                for bank_id in data_set_dict.keys():
                    vec_x, vec_y, vec_e = data_set_dict[bank_id]
                    self._mainGraphicDict[bank_id].add_plot_1d(vec_x, vec_y, color='black',
                                                               label='{0}: bank {1}'.format(prev_acc_name, bank_id),
                                                               x_label=current_unit)

        # END-FOR

        return

    def update_timer(self, i_signal):
        """
        update timer
        :return:
        """
        # refresh with workspace list
        ws_name_list = self._controller.get_workspaces()
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

        message = '{0}\nNew Workspace: {1}'.format(ws_name_list, new_ws_name_list)
        for ws_name in new_ws_name_list:
            ws_i = helper.retrieve_workspace(ws_name)
            if ws_i.id() == 'Workspace2D' or ws_i.id() == 'EventWorkspace' and ws_i.name().startswith('output'):
                message += 'workspace {0}: number of spectra = {1}'.format(ws_name, ws_i.getNumberHistograms())
        # self.ui.plainTextEdit_Log.clear()
        self.ui.plainTextEdit_Log.appendPlainText(message)

        return


class TimerThread(QtCore.QThread):

    time_due = QtCore.pyqtSignal(int)

    def __init__(self, time_step, parent):
        """
        blabla
        :param time_step:
        :param parent:
        """
        QtCore.QThread.__init__(self)

        self._parent = parent

        self._continueTimerLoop = True

        self.time_due.connect(self._parent.update_timer)

        return

    def run(self):
        """ run the timer thread.  this thread won't be kill until flag _continueTimerLoop is set to False
        :return:
        """
        import time

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
