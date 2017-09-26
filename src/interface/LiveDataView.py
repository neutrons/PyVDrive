from PyQt4 import QtCore
from PyQt4 import QtGui
import random

import gui.ui_LiveDataView as ui_LiveDataView
import PyVDrive.lib.LiveDataDriver as ld
import PyVDrive.lib.mantid_helper as helper

# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


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
        self._myWorkspaceNumber = 1800  # containing 1 hour data for dT = 10 seconds
        self._myWorkspaceList = [None] * self._myWorkspaceNumber  # a holder for workspace names
        self._myListIndex = 0

        # summed workspace list
        self._mySummedWorkspaceList = list()   # name of summed workspaces

        # index for accumulated workspaces
        self._currAccumulateIndex = 0

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

        # menu bar
        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'),
                     self.do_quit)
        self.connect(self.ui.actionClear_Logs, QtCore.SIGNAL('triggered()'),
                     self.do_clear_log)
        self.connect(self.ui.actionIPython_Console, QtCore.SIGNAL('triggered()'),
                     self.do_launch_ipython)

        # other widgets
        self.connect(self.ui.comboBox_currUnits, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_bank_view_change_unit)

        self.connect(self.ui.checkBox_showPrevReduced,  QtCore.SIGNAL('stateChanged(int)'),
                     self.evt_show_high_prev_data)

        # multiple thread pool
        self._checkStateTimer = None

        # collection of workspace names
        self._workspaceSet = set()

        # accumulated workspace
        self._accumulatedWorkspace = None
        self._accumulatedList = list()  # list of accumulated workspace

        self._bankColorDict = {1: 'black', 2: 'red', 3: 'blue'}
        self._mainGraphicDict = {1: self.ui.graphicsView_currentViewB1,
                                 2: self.ui.graphicsView_currentViewB2,
                                 3: self.ui.graphicsView_currentViewB3}

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
        # TODO/ISSUE/NOW - Find out how to generalize this class to a standalone class.. (VDrivePlot)
        class WorkspacesView(QtGui.QMainWindow):
            """
            class
            """

            def __init__(self, parent=None):
                """
                Init
                :param parent:
                """
                from gui.workspaceviewwidget import WorkspaceViewWidget

                QtGui.QMainWindow.__init__(self)

                # set up
                self.setObjectName(_fromUtf8("MainWindow"))
                self.resize(1600, 1200)
                self.centralwidget = QtGui.QWidget(self)
                self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
                self.gridLayout = QtGui.QGridLayout(self.centralwidget)
                self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
                self.widget = WorkspaceViewWidget(self)
                sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(0)
                sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
                self.widget.setSizePolicy(sizePolicy)
                self.widget.setObjectName(_fromUtf8("widget"))
                self.gridLayout.addWidget(self.widget, 1, 0, 1, 1)
                self.label = QtGui.QLabel(self.centralwidget)
                self.label.setObjectName(_fromUtf8("label"))
                self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
                self.setCentralWidget(self.centralwidget)
                self.menubar = QtGui.QMenuBar(self)
                self.menubar.setGeometry(QtCore.QRect(0, 0, 1005, 25))
                self.menubar.setObjectName(_fromUtf8("menubar"))
                self.setMenuBar(self.menubar)
                self.statusbar = QtGui.QStatusBar(self)
                self.statusbar.setObjectName(_fromUtf8("statusbar"))
                self.setStatusBar(self.statusbar)
                self.toolBar = QtGui.QToolBar(self)
                self.toolBar.setObjectName(_fromUtf8("toolBar"))
                self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

                # self.retranslateUi(self)
                QtCore.QMetaObject.connectSlotsByName(self)

                return

        self._workspaceView = WorkspacesView(self)
        self._workspaceView.widget.set_main_window(self)
        self._workspaceView.show()

        self._myChildWindows.append(self._workspaceView)

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

    def plot_data_in_accumulation(self):
        """
        plot data that is in accumulation
        :return:
        """
        # get new unit
        target_unit = str(self.ui.comboBox_currUnits.currentText())

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
        # END-FOR

        if is_new_ws:
            self._controller.delete_workspace(in_sum_name)

        return

    def plot_data_previous_cycle(self):
        """
        plot data collected and reduced in previous cycles
        this method has no idea whether it should keep the previous reduced plot or not
        :return:
        """
        # return if there is no such need
        if self.ui.checkBox_showPrevReduced.isChecked() is False:
            if self._isPrevCyclePlotted:
                # if previous cycles are plotted, then remove them
                for bank_id in range(1, 4):
                    self._mainGraphicDict[bank_id].delete_previous_run()
            return

        # plot previous ones
        prev_ws_index = -1 - int(self.ui.lineEdit_showPrevNCycles.text())
        prev_ws = self._mySummedWorkspaceList[prev_ws_index]

        # get new unit
        target_unit = str(self.ui.comboBox_currUnits.currentText())
        prev_ws_name = '_temp_prev_ws_{0}'.format(random.randint(1, 10000))
        prev_ws, is_new_ws = self._controller.convert_unit(prev_ws, target_unit, prev_ws_name)

        # clean
        if is_new_ws:
            self._controller.delete_workspace(prev_ws_name)

        return

    def evt_bank_view_change_unit(self):
        """
        change the unit of the plotted workspaces of the top 3 bank view
        :return:
        """
        self.plot_data_in_accumulation()
        self.plot_data_previous_cycle()

        # # get new unit
        # new_unit = str(self.ui.comboBox_currUnits.currentText())
        #
        # # get the workspace names
        # in_sum_name = '_temp_curr_ws_{0}'.format(random.randint(1, 10000))
        # in_sum_ws = self._controller.convert_unit(self._accumulatedWorkspace, new_unit, in_sum_name)
        #
        # if self.ui.checkBox_showPrevReduced.isChecked():
        #     prev_ws_index = -1 - int(self.ui.lineEdit_showPrevNCycles.text())
        #     prev_ws = self._mySummedWorkspaceList[prev_ws_index]
        #     prev_ws_name = '_temp_prev_ws_{0}'.format(random.randint(1, 10000))
        #     prev_ws = self._controller.convert_unit(prev_ws, new_unit, prev_ws_name)
        # else:
        #     prev_ws = None
        #     prev_ws_name = ''
        #
        # # plot
        # for bank_id in range(1, 4):
        #     # get data
        #     vec_y_i = in_sum_ws.readY(bank_id-1)
        #     vec_x_i = in_sum_ws.readX(bank_id-1)[:len(vec_y_i)]
        #     color_i = self._bankColorDict[bank_id]
        #     label_i = 'in accumulation bank {0}'.format(bank_id)
        #     self._mainGraphicDict[bank_id].plot_current_plot(vec_x_i, vec_y_i, color_i, label_i, new_unit)
        #
        #     if prev_ws is not None:
        #         vec_y_i = prev_ws.readY(bank_id)
        #         vec_x_i = prev_ws.readX(bank_id)[:len(vec_y_i)]
        #         label_i = 'previous {0} run bank {1}'.format(str(self.ui.lineEdit_showPrevNCycles), bank_id)
        #         self._mainGraphicDict[bank_id].plot_previous_run(vec_x_i, vec_y_i, 'black', label_i, new_unit)
        #     # END-IF
        # # END-FOR
        #
        # # clean
        # self._controller.delete_workspace(in_sum_name)
        # if prev_ws is not None:
        #     self._controller.delete_workspace(prev_ws_name)

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

        # for bank_id in self._bankColorDict:
        #     if state:
        #         self._mainGraphicDict[bank_id].plotPreviousRun(self._reducedWorkspace[-2], bank_id)
        #     else:
        #         self._mainGraphicDict[bank_id].hidePreviousRun()
        # # END-IF

        return

    def hide_data_previous_cycle(self):
        """

        :return:
        """
        for bank_id in self._bankColorDict:
            self._mainGraphicDict[bank_id].delete_previous_run()
        # END-FOR

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

    def get_reserved_commands(self):
        """

        :return:
        """
        # TODO/ISSUE/NOW - Implement

        return list()

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

            # get reference to workspace
            workspace_i = helper.retrieve_workspace(ws_name_i)

            # skip non-matrix workspace or workspace sounds not right
            if not (helper.is_matrix_workspace(ws_name_i) and 3 <= workspace_i.getNumberHistograms() < 20):
                # skip weird workspace
                log_message = 'Workspace {0} of type {1} is not expected.\n'.format(workspace_i, type(workspace_i))
                self.ui.plainTextEdit_Log.setPlainText(log_message)
                continue

            # # decide whether a new workspace shall be started
            # WORKSPACE_LIMIT = 5 * 60 / 10
            # prev_acc_name = None
            # if self._accumulatedWorkspace is None or len(self._accumulatedList) == WORKSPACE_LIMIT:
            #     # reset if pre-existing of accumulated workspace
            #     if self._accumulatedWorkspace is not None:
            #         prev_acc_name = self._accumulatedWorkspace.name()
            #         self._accumulatedList = list()
            #     # clone workspace
            #     accumulate_name = 'FiveMinutes_{0}'.format(self._currAccumulateIndex)
            #     self._accumulatedWorkspace = helper.clone_workspace(ws_name, accumulate_name)
            #     self._mySummedWorkspaceList.append(self._accumulatedWorkspace)
            #
            # else:
            #     # add
            #     self._accumulatedWorkspace += workspace_i
            #     accumulate_name = self._accumulatedWorkspace.name()
            # self._accumulatedList.append(ws_name)

            self.sum_incremental_workspaces(workspace_i)
            accumulate_name = self._accumulatedWorkspace.name()

            # TODO/ISSUE/NOW - Find out how to have a record whether the previously cycle is plotted or not
            # including workspace name and status (on/off)

            # plot
            # self.ui.plainTextEdit_Log.clear()
            self.ui.plainTextEdit_Log.appendPlainText('Plotting {0}: X-size = {1}'
                                                      ''.format(accumulate_name,
                                                                len(self._accumulatedWorkspace.readX(0))))
            self.ui.plainTextEdit_Log.appendPlainText('\n')

            # TODO/ISSUE/ - Fixed to bank 1, 2, 3
            target_unit = str(self.ui.comboBox_currUnits.currentText())
            for bank_id in range(1, 4):
                # convert unit if necessary
                to_plot_ws = self._controller.convert_unit()




                vec_x = self._accumulatedWorkspace.readX(i)[:-1]
                vec_y = self._accumulatedWorkspace.readY(i)
                data_set_dict[i+1] = vec_x, vec_y, None

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
            self.ui.lineEdit_newestReducedWorkspace.setText(str(ws_name_i))

            # plot previous
            if self.ui.checkBox_showPrevReduced.isChecked():
                # prev_acc_name is not None and

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

    def sum_incremental_workspaces(self, workspace_i):
        """

        :return:
        """
        # decide whether a new workspace shall be started
        # TODO/ISSUE/NOW - This shall be made more flexible!
        WORKSPACE_LIMIT = 5 * 60 / 10

        ws_name = workspace_i.name()
        if self._accumulatedWorkspace is None or len(self._accumulatedList) == WORKSPACE_LIMIT:
            # reset if pre-existing of accumulated workspace
            self._accumulatedList = list()

            # clone workspace
            accumulate_name = 'Accumulated_{0}'.format(self._currAccumulateIndex)
            self._accumulatedWorkspace = helper.clone_workspace(ws_name, accumulate_name)

            # append to list
            self._mySummedWorkspaceList.append(self._accumulatedWorkspace)

        else:
            # add to existing
            assert self._accumulatedWorkspace.getNumberHistograms() == workspace_i.getNumberHistograms(), 'blabla xx'

            for iws in range(workspace_i.getNumberHistograms()):
                assert len(self._accumulatedWorkspace.readY(iws)) == len(workspace_i.readY(iws)),\
                    'blabla yy {0}'.format(iws)

                self._accumulatedWorkspace.setY(iws, self._accumulatedWorkspace.readY(iws) + workspace_i.readY(iws))
            # END-iws

            # update the workspace
            self._mySummedWorkspaceList[-1] = self._accumulatedWorkspace

        # update the list of source accumulated workspace
        self._accumulatedList.append(ws_name)

        return

    def update_2d_plot(self):
        # TODO/ISSUE/NOW - Maybe need a better name but definiately IMPLEMENT IT!

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

        # TODO/NOW - Implement timer
        print self.ui.timeEdit_collectTime

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
