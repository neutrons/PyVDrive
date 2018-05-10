#!/usr/bin/python
# import utility modules
import sys
import os

# import PyQt modules
try:
    from PyQt5 import QtCore as QtCore
    from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QSizePolicy, QLabel, QMenuBar, QStatusBar, QToolBar
    from PyQt5.QtWidgets import QFileDialog, QRadioButton, QMenu, QAction
    from PyQt5.QtGui import QCursor
    is_qt_4 = False
except ImportError as import_e:
    from PyQt4 import QtCore as QtCore
    from PyQt4.QtGui import QMainWindow, QWidget, QGridLayout, QSizePolicy, QLabel, QMenuBar, QStatusBar, QToolBar
    from PyQt4.QtGui import QFileDialog, QRadioButton, QMenu, QAction, QCursor
    is_qt_4 = True

# include this try/except block to remap QString needed when using IPython
if is_qt_4:
    try:
        _fromUtf8 = QtCore.QString.fromUtf8
    except AttributeError:
        _fromUtf8 = lambda s: s

# Set up path to PyVDrive: if it is on analysis computer, then import from wzz explicitly
import socket
if socket.gethostname().count('analysis-') > 0 or os.path.exists('/home/wzz') is False:
    sys.path.append('/SNS/users/wzz/local/lib/python/site-packages/')

import gui.ui_VdrivePlot as mainUi
import PeakPickWindow as PeakPickWindow
import snapgraphicsview as SnapGView
import ReducedDataView as DataView
import gui.GuiUtility as GuiUtility
import AddRunsIPTS as dlgrun
import LogPickerWindow as LogPicker
import LogSnapView as dlgSnap
from vcommand_processor import VdriveCommandProcessor
import VDrivePlotDataBinning as ReductionUtil
import configwindow
import config


""" import PyVDrive library """
import pyvdrive as PyVDrive
import pyvdrive.lib.VDriveAPI as VdriveAPI

__author__ = 'wzz'

# Define enumerate
ACTIVE_SLICER_TIME = 0
ACTIVE_SLICER_LOG = 1
ACTIVE_SLICER_MANUAL = 2


class VdriveMainWindow(QMainWindow):
    """ Main GUI class for VDrive of the beta version
    """
    # Define signals to child windows as None(s)
    myLogSignal = QtCore.pyqtSignal(str)
    mySideBarSignal = QtCore.pyqtSignal(str)

    # initialize app
    def __init__(self, parent=None):
        """ Init
        """
        # Setup main window
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('VDrivePlot (Beta)')
        self.ui = mainUi.Ui_MainWindow()
        self.ui.setupUi(self)

        # Define status variables
        # new work flow
        template_data_dir = PyVDrive.__path__[0]

        # configuration
        self._myConfiguration = config.PyVDriveConfiguration()
        self._myWorkflow = VdriveAPI.VDriveAPI('VULCAN', template_data_dir)

        # IPTS number (shortcut)
        self._currIptsNumber = None

        self._numSnapViews = 6

        # Initialize widgets
        self._init_widgets()

        # Define event handling
        self.ui.pushButton_selectIPTS.clicked.connect(self.do_add_runs_by_ipts)
        self.ui.pushButton_readSampleLogFile.clicked.connect(self.do_load_sample_log)

        # Column 2
        # about vanadium calibration
        self.ui.pushButton_loadCalFile.clicked.connect(self.do_load_vanadium_calibration)

        # select and set runs from run-info-tree
        self.ui.pushButton_addRunsToReduce.clicked.connect(self.do_add_runs_to_reduce)
        self.ui.checkBox_selectRuns.stateChanged.connect(self.do_update_selected_runs)
        self.ui.pushButton_deleteRuns.clicked.connect(self.do_remove_runs_from_reduction)
        self.ui.pushButton_sortSelectedRuns.clicked.connect(self.do_sort_selected_runs)
        self.ui.pushButton_reduceRuns.clicked.connect(self.do_to_reduction_stage)

        self.ui.checkBox_chopRun.stateChanged.connect(self.evt_chop_run_state_change)

        # Column 3
        # Tab-1
        # sub-tab-1
        self.ui.pushButton_loadTimeSegmentsFile.clicked.connect(self.do_load_time_seg_file)
        self.ui.pushButton_chopData.clicked.connect(self.do_slice_data_by_time)
        self.ui.pushButton_manualPicker.clicked.connect(self.do_launch_log_picker_window)

        # sub-tab-2
        self.ui.pushButton_applyManual.clicked.connect(self.do_apply_manual_slicer)
        self.ui.pushButton_applyLog.clicked.connect(self.do_apply_log_slicer)
        self.ui.pushButton_saveSlicer.clicked.connect(self.do_save_log_slicer)

        # Tab-2
        self.ui.pushButton_browseOutputDir.clicked.connect(self.do_browse_output_dir)
        self.ui.checkBox_autoReduction.stateChanged.connect(self.do_use_output_vulcan_shared)
        self.ui.pushButton_binData.clicked.connect(self.do_bin_data)

        # Tab-3: view reduction result
        self.ui.pushButton_viewReducedData.clicked.connect(self.do_launch_reduced_data_viewer)

        # Tab-4: fig single peak
        self.ui.pushButton_fitSinglePeak.clicked.connect(self.do_fit_single_peak)

        # # Define event handling
        # self.connect(self.ui.pushButton_selectIPTS, QtCore.SIGNAL('clicked()'),
        #              self.do_add_runs_by_ipts)
        # self.connect(self.ui.pushButton_readSampleLogFile, QtCore.SIGNAL('clicked()'),
        #              self.do_load_sample_log)
        #
        # # Column 2
        # # about vanadium calibration
        # self.connect(self.ui.pushButton_loadCalFile, QtCore.SIGNAL('clicked()'),
        #              self.do_load_vanadium_calibration)
        #
        # # select and set runs from run-info-tree
        # self.connect(self.ui.pushButton_addRunsToReduce, QtCore.SIGNAL('clicked()'),
        #              self.do_add_runs_to_reduce)
        # self.connect(self.ui.checkBox_selectRuns, QtCore.SIGNAL('stateChanged(int)'),
        #              self.do_update_selected_runs)
        # self.connect(self.ui.pushButton_deleteRuns, QtCore.SIGNAL('clicked()'),
        #              self.do_remove_runs_from_reduction)
        # self.connect(self.ui.pushButton_sortSelectedRuns, QtCore.SIGNAL('clicked()'),
        #              self.do_sort_selected_runs)
        # self.connect(self.ui.pushButton_reduceRuns, QtCore.SIGNAL('clicked()'),
        #              self.do_to_reduction_stage)
        #
        # self.connect(self.ui.checkBox_chopRun, QtCore.SIGNAL('stateChanged(int)'),
        #              self.evt_chop_run_state_change)
        #
        # # Column 3
        # # Tab-1
        # # sub-tab-1
        # self.connect(self.ui.pushButton_loadTimeSegmentsFile, QtCore.SIGNAL('clicked()'),
        #              self.do_load_time_seg_file)
        # self.connect(self.ui.pushButton_chopData, QtCore.SIGNAL('clicked()'),
        #              self.do_slice_data_by_time)
        # self.connect(self.ui.pushButton_manualPicker, QtCore.SIGNAL('clicked()'),
        #              self.do_launch_log_picker_window)
        #
        # # sub-tab-2
        # self.connect(self.ui.pushButton_applyManual, QtCore.SIGNAL('clicked()'),
        #              self.do_apply_manual_slicer)
        # self.connect(self.ui.pushButton_applyLog, QtCore.SIGNAL('clicked()'),
        #              self.do_apply_log_slicer)
        # self.connect(self.ui.pushButton_saveSlicer, QtCore.SIGNAL('clicked()'),
        #              self.do_save_log_slicer)
        #
        # # Tab-2
        # self.connect(self.ui.pushButton_browseOutputDir, QtCore.SIGNAL('clicked()'),
        #              self.do_browse_output_dir)
        # self.connect(self.ui.checkBox_autoReduction, QtCore.SIGNAL('stateChanged(int)'),
        #              self.do_use_output_vulcan_shared)
        # self.connect(self.ui.pushButton_binData, QtCore.SIGNAL('clicked()'),
        #              self.do_bin_data)
        #
        # # Tab-3: view reduction result
        # self.connect(self.ui.pushButton_viewReducedData, QtCore.SIGNAL('clicked()'),
        #              self.do_launch_reduced_data_viewer)
        #
        # # Tab-4: fig single peak
        # self.connect(self.ui.pushButton_fitSinglePeak, QtCore.SIGNAL('clicked()'),
        #              self.do_fit_single_peak)

        # Column 4
        self.ui.graphicsView_snapView1.canvas().mpl_connect('button_release_event', self.evt_snap1_mouse_press)
        self.ui.graphicsView_snapView2.canvas().mpl_connect('button_release_event', self.evt_snap2_mouse_press)
        self.ui.graphicsView_snapView3.canvas().mpl_connect('button_release_event', self.evt_snap3_mouse_press)
        self.ui.graphicsView_snapView4.canvas().mpl_connect('button_release_event', self.evt_snap4_mouse_press)
        self.ui.graphicsView_snapView5.canvas().mpl_connect('button_release_event', self.evt_snap5_mouse_press)
        self.ui.graphicsView_snapView6.canvas().mpl_connect('button_release_event', self.evt_snap6_mouse_press)

        self._group_left_box_list = [self.ui.comboBox_g11, self.ui.comboBox_g21,
                                     self.ui.comboBox_g31, self.ui.comboBox_g41,
                                     self.ui.comboBox_g51, self.ui.comboBox_g61]
        for combo_box in self._group_left_box_list:
            combo_box.currentIndexChanged.connect(self.event_change_log_snap_view)
            # self.connect(combo_box, QtCore.SIGNAL('currentIndexChanged(int)'),
            #              self.event_change_log_snap_view)
        self._logSnapViewLock = False

        # Event handling for menu
        self.ui.actionSave_Project.triggered.connect(self.menu_save_project)
        self.ui.actionSave_Project_As.triggered.connect(self.menu_save_session_as)
        self.ui.actionOpen_Project.triggered.connect(self.menu_load_project)
        self.ui.actionAuto_Saved.triggered.connect(self.menu_load_auto)
        self.ui.actionQuit.triggered.connect(self.evt_quit)
        self.ui.actionOpen_Configuration.triggered.connect(self.menu_config)
        self.ui.actionWorkspaces.triggered.connect(self.menu_workspaces_view)

        # self.connect(self.ui.actionSave_Project, QtCore.SIGNAL('triggered()'),
        #              self.menu_save_project)
        # self.connect(self.ui.actionSave_Project_As, QtCore.SIGNAL('triggered()'),
        #              self.menu_save_session_as)
        # self.connect(self.ui.actionOpen_Project, QtCore.SIGNAL('triggered()'),
        #              self.menu_load_project)
        # self.connect(self.ui.actionAuto_Saved, QtCore.SIGNAL('triggered()'),
        #              self.menu_load_auto)
        # self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'),
        #              self.evt_quit)
        #
        # self.connect(self.ui.actionOpen_Configuration, QtCore.SIGNAL('triggered()'),
        #              self.menu_config)
        #
        # self.connect(self.ui.actionWorkspaces, QtCore.SIGNAL('triggered()'),
        #              self.menu_workspaces_view)

        # Group widgets
        self._groupedSnapViewList = list()
        self._setup_snap_view_groups(self._numSnapViews)

        # Sub windows
        # controls to the sub windows
        self._myChildWindows = []
        self._logPickerWindow = None
        self._peakPickerWindow = None
        self._snapViewWindow = None
        self._workspaceView = None
        self._reducedDataViewWindow = None

        # Snap view related variables and data structures
        self._currentSnapViewIndex = -1
        self._group_left_box_values = [-1] * self._numSnapViews

        # variables for event data slicing
        self._currLogRunNumber = None  # current run number for slicing with log
        self._currSlicerLogName = None  # current sample for slicer, __manual__ is for manual mode
        self._activeSlicer = ''

        # Some class variable for recording status
        self._savedSessionFileName = None
        self._lastSampleLogFileName = ''

        self._calibCriteriaFile = ''

        # some historical data storage
        self._addedIPTSNumber = None

        # Load settings
        self.load_settings()

        # VDRIVE command
        self._vdriveCommandProcessor = VdriveCommandProcessor(self, self._myWorkflow)

        return

    def closeEvent(self, QCloseEvent):
        """
        Connect close by 'X' to proper quit handler
        :param QCloseEvent:
        :return:
        """
        self.evt_quit()

    def menu_workspaces_view(self):
        """
        Launch workspace viewer
        :return:
        """
        class WorkspacesView(QMainWindow):
            """
            class
            """
            def __init__(self, parent=None):
                """
                Init
                :param parent:
                """
                from gui.workspaceviewwidget import WorkspaceViewWidget

                QMainWindow.__init__(self)

                # set up
                self.setObjectName(_fromUtf8("MainWindow"))
                self.resize(1600, 1200)
                self.centralwidget = QWidget(self)
                self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
                self.gridLayout = QGridLayout(self.centralwidget)
                self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
                self.widget = WorkspaceViewWidget(self)
                sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(0)
                sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
                self.widget.setSizePolicy(sizePolicy)
                self.widget.setObjectName(_fromUtf8("widget"))
                self.gridLayout.addWidget(self.widget, 1, 0, 1, 1)
                self.label = QLabel(self.centralwidget)
                self.label.setObjectName(_fromUtf8("label"))
                self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
                self.setCentralWidget(self.centralwidget)
                self.menubar = QMenuBar(self)
                self.menubar.setGeometry(QtCore.QRect(0, 0, 1005, 25))
                self.menubar.setObjectName(_fromUtf8("menubar"))
                self.setMenuBar(self.menubar)
                self.statusbar = QStatusBar(self)
                self.statusbar.setObjectName(_fromUtf8("statusbar"))
                self.setStatusBar(self.statusbar)
                self.toolBar = QToolBar(self)
                self.toolBar.setObjectName(_fromUtf8("toolBar"))
                self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

                #self.retranslateUi(self)
                QtCore.QMetaObject.connectSlotsByName(self)

                return

        self._workspaceView = WorkspacesView(self)
        self._workspaceView.widget.set_main_window(self)
        self._workspaceView.show()

        self._myChildWindows.append(self._workspaceView)

        return

    # TODO/FIXME - Replace homemade by QSettings: Issue XXX
    def save_settings(self):
        settings = QtCore.QSettings()
        settings.setValue('test01', str(self.ui.lineEdit_userLogFileName.text()))

    def load_settings(self):
        settings = QtCore.QSettings()
        value1 = settings.value('test01', '')
        if isinstance(value1, QtCore.QVariant) is False:
            print '[Error] to load QSettings.  Value1 is of type %s' % str(type(value1))
            return
        value1str = value1.toString()
        print '[DB] Value 1 without previous setting', str(value1str), 'of type', str(type(value1str))
        self.ui.lineEdit_userLogFileName.setText(value1str)

    def do_apply_log_slicer(self):
        """ Pick up the splitters made from sample log values
        :return:
        """
        found = False
        for i_radio in xrange(self._numSnapViews):
            if self._groupedSnapViewList[i_radio].is_selected() is True:
                self._currSlicerLogName = SnapGView.SampleLogView(
                    self._groupedSnapViewList[i_radio], self).get_log_name()
                found = True
                print '[DB] VDrivePlot: snap view for radio button %d is selected.' % i_radio
                break

        if found is False:
            GuiUtility.pop_dialog_error('Unable to locate any sample log to be picked up.')


        # self._apply_slicer_snap_view() : disabled because there is no need to do this

        return

    def do_apply_manual_slicer(self):
        """ Pick up (time) slicing information and show it by indicating lines in snap view
        :return:
        """
        raise NotImplementedError('Think of whether this feature shall be kept?')

        run_number = self._get_run_numbers()

        self._myWorkflow.set_slicer(run_number, 'Manual')

        self._apply_slicer_snap_view()

        return

    def do_bin_data(self):
        """ Brief: Bin a set of data
        Purpose:
            Reduce the event data to focused diffraction pattern.
            The process includes align, focus, rebin and calibration with vanadium.
        Requirements:
            At least 1 run is selected for reduce;
            calibration file for focusing is specified;
            ... ...
        Guarantees:
            Selected runs are reduced from event data to focused diffraction pattern
            good for Rietveld refinement.
            If the data slicing is selected, then reduce the sliced data.
        :return:
        """
        reducer = ReductionUtil.VulcanGuiReduction(self.ui, self._myWorkflow)

        status, error_message = reducer.reduce_data()
        if status:
            # Show message to notify user that the reduction is complete
            GuiUtility.pop_dialog_information(self, 'Reduction is complete.')
            # switch the tab to 'VIEW'
            self.ui.tabWidget_reduceData.setCurrentIndex(2)
        else:
            # reduction failed
            GuiUtility.pop_dialog_error(self, error_message)
            return

        return

    def do_browse_output_dir(self):
        """
        browse output directory
        :return:
        """
        output_dir = str(QFileDialog.getExistingDirectory(self, 'Directory for output files',
                                                          self._myWorkflow.get_working_dir()))
        if len(output_dir) > 0:
            self.ui.lineEdit_outputDir.setText(output_dir)

        return

    def do_to_reduction_stage(self):
        """ Advance to data-reduction stage from run-selection stage
        :return:
        """
        # get runs to be reduced
        selected_row_list = self.ui.tableWidget_selectedRuns.get_selected_rows()
        if len(selected_row_list) == 0:
            GuiUtility.pop_dialog_error(self, 'No run is selected.')
            return
        else:
            run_number_list = list()
            for i_row in selected_row_list:
                row_number = self.ui.tableWidget_selectedRuns.get_cell_value(i_row, 0)
                run_number_list.append(row_number)

        # check status
        if self.ui.checkBox_chopRun.isChecked():
            # advance to 'chop'-tab
            self.ui.tabWidget_reduceData.setCurrentIndex(0)

            # set up current run to chop
            current_run_number = run_number_list[0]
            self.ui.comboBox_chopTabRunList.clear()
            for run_number in run_number_list:
                self.ui.comboBox_chopTabRunList.addItem('%d' % run_number)

            # set up current run and run list in chop-tab
            # self._myWorkflow.load_log_only(current_run_number)

        else:
            # advance to 'bin'-tab
            self.ui.tabWidget_reduceData.setCurrentIndex(1)

        return

    def do_update_selected_runs(self):
        """
        # TODO/FIXME/
        :return:
        """
        curr_state = self.ui.checkBox_selectRuns.isChecked()

        self.ui.tableWidget_selectedRuns.select_all_rows(curr_state)

        return

    def do_use_output_vulcan_shared(self):
        """
        use VULCAN shared directory for output
        :return:
        """
        if self.ui.checkBox_autoReduction.isChecked():
            # turn on auto reduction mode
            parent_dir = '/SNS/VULCAN/shared'

            # check access to directories
            if not os.path.exists(parent_dir):
                self.ui.checkBox_autoReduction.setChecked(False)
                GuiUtility.pop_dialog_error(self, 'Archive directory %s cannot found!' % parent_dir)
                return
            if not os.access(parent_dir, os.W_OK):
                self.ui.checkBox_autoReduction.setChecked(False)
                GuiUtility.pop_dialog_error(self, 'User has no writing permit to archive.')
                return

            # set other check boxes
            self.ui.checkBox_outGSAS.setChecked(True)
            self.ui.checkBox_outputAutoRecords.setChecked(True)
            self.ui.checkBox_outputSampleLogs.setChecked(True)
            self.ui.checkBox_outGSAS.setEnabled(False)
            self.ui.checkBox_outputAutoRecords.setEnabled(False)
            self.ui.checkBox_outputSampleLogs.setEnabled(False)
            self.ui.checkBox_outFullprof.setEnabled(False)

        else:
            # turn off auto reduction mode
            self.ui.checkBox_outGSAS.setEnabled(True)
            self.ui.checkBox_outputAutoRecords.setEnabled(True)
            self.ui.checkBox_outputSampleLogs.setEnabled(True)
            self.ui.checkBox_outFullprof.setEnabled(True)

        return

    def do_launch_reduced_data_viewer(self):
        """
        Purpose: Launch reduction view and set up
        Requirements: ... ...
        Guarantees: ... ...
        :return: handler to child window
        """
        # create the instance of a reduction data view window
        if self._reducedDataViewWindow is None:
            # initialize a window instance it has not been
            self._reducedDataViewWindow = DataView.GeneralPurposedDataViewWindow(self)
            self._reducedDataViewWindow.init_setup(self._myWorkflow)
            self._myChildWindows.append(self._reducedDataViewWindow)
        # END-IF

        # show the window if it exists and return
        self._reducedDataViewWindow.show()

        return self._reducedDataViewWindow

    def do_remove_runs_from_reduction(self):
        """
        :return:
        """
        # TODO / FIXME
        # get run to delete
        try:
            remove_run = GuiUtility.parse_integer(self.ui.lineEdit_runsToDelete)
        except ValueError as ve:
            GuiUtility.pop_dialog_error(self, str(ve))
            return

        # determine the rows for the runs to delete
        if remove_run is not None:
            row_number_list = self.ui.tableWidget_selectedRuns.get_rows_by_run([remove_run])
            # check
            if row_number_list[0] < 0:
                GuiUtility.pop_dialog_error(self, 'Run number %d is not in the selected runs.' % remove_run)
                return
            else:
                self.ui.lineEdit_runsToDelete.setText('')
        else:
            row_number_list = self.ui.tableWidget_selectedRuns.get_selected_rows()
            if len(row_number_list) == 0:
                GuiUtility.pop_dialog_error(self, 'There is no run selected to delete.')
                return

        # delete
        self.ui.tableWidget_selectedRuns.remove_rows(row_number_list)

        return

    def do_slice_data_by_time(self):
        """ Event handler to slice/chop data by time
        :return:
        """
        raise RuntimeError('NOWNOW: Need to redo this method!')

        # Check selected run numbers
        selected_run_list = self.ui.tableWidget_selectedRuns.get_selected_runs()
        print '[DB] Slice data by time: runs to chop = %s' % str(selected_run_list)

        do_connect_runs = self.ui.checkBox_chopContinueRun.isChecked()

        # Check radio button to generate relative-time slicer
        if self.ui.radioButton_chopContantDeltaT.isChecked() is True:
            # chop data by standard runs
            start_time = GuiUtility.parse_float(self.ui.lineEdit_chopTimeSegStartTime)
            time_interval = GuiUtility.parse_float(self.ui.lineEdit_chopTimeSegInterval)
            stop_time = GuiUtility.parse_float(self.ui.lineEdit_chopTimeSegStopTime)

            if do_connect_runs is True:
                # special handling to chop data by connecting runs
                self._myWorkflow.chop_data_connect_runs(selected_run_list, start_time, stop_time, time_interval)

            else:
                # regular chopping with run by run
                err_msg = ''
                for run_number in selected_run_list:
                    status, ret_obj = self._myWorkflow.gen_data_slicer_by_time(
                        run_number=run_number, start_time=start_time,
                        end_time=stop_time, time_step=time_interval)
                    if status is False:
                        err_msg += ret_obj + '\n'
                        continue

                    status, ret_obj = self._myWorkflow.slice_data(
                        run_number=run_number, by_time=True)
                    if status is False:
                        err_msg += ret_obj + '\n'
                # END-FOR
                if err_msg != '':
                    GuiUtility.pop_dialog_error(self, err_msg)

        elif self.ui.radioButton_chopByTimeSegments.isChecked() is True:
            # chop with user-defined time segment
            raise RuntimeError('IMPLEMENT IMPORTING TIME SEGMENT FILE ASAP')

        else:
            # Impossible status
            GuiUtility.pop_dialog_error(self, 'User must choose one radio button.')
            return

        # Pop a summary dialog and optionally shift next tab
        # TODO/FIXME Implement pop up dialog for summary

        # shift
        do_change_tab = self.ui.checkBox_chopBinLater.isChecked()
        if do_change_tab is True:
            self.ui.tabWidget_reduceData.setCurrentIndex(1)

        return

    def do_save_log_slicer(self):
        """ Save slicer to file in 'log value' sub-tab of CHOP tab
        :return:
        """
        out_file_name = str(
                QFileDialog.getSaveFileName(self, 'Data Slice File',
                                            self._myWorkflow.get_working_dir()))

        print '[DB] Save slicer for run ', self._currLogRunNumber, ' sample log ', self._currSlicerLogName,
        print 'to file', out_file_name
        # Save slicer for run  57325  sample log  Voltage

        if self._currSlicerLogName is None:
            GuiUtility.pop_dialog_error(self, 'Neither log-value slicer nor manual slicer is applied.')
            return
        else:
            # Save splitters workspace
            if self._currSlicerLogName == '__manual__':
                raise NotImplementedError('ASAP')
            else:
                # save_to_buffer splitters from log
                status, err_msg = self._myWorkflow.save_splitter_workspace(
                    self._currLogRunNumber, self._currSlicerLogName, out_file_name)
                if status is False:
                    GuiUtility.pop_dialog_error(self, err_msg)

        return

    def do_sort_selected_runs(self):
        """
        TODO/FIXME
        :return:
        """
        sort_order = self.ui.checkBox_runsOrderDescend.isChecked()

        if sort_order is False:
            self.ui.tableWidget_selectedRuns.sortByColumn(0, 0)
        else:
            self.ui.tableWidget_selectedRuns.sortByColumn(0, 1)

        return

    def _init_widgets(self):
        """ Initialize widgets including
        (1) project runs view
        :return: None
        """
        # Selecting runs
        self.ui.tableWidget_selectedRuns.setup()
        self.ui.tableWidget_timeSegment.setup()

        self.ui.treeView_iptsRun.set_main_window(self)

        # Chopping
        self.ui.checkBox_chopRun.setCheckState(QtCore.Qt.Unchecked)
        self.ui.tabWidget_reduceData.setCurrentIndex(1)
        self.ui.tabWidget_reduceData.setTabEnabled(0, False)

        # Reduction
        self.ui.radioButton_binStandard.setChecked(True)
        self.ui.checkBox_outGSAS.setChecked(True)

        # View
        self.ui.radioButton_viewInTOF.setChecked(True)
        self.ui.radioButton_plotData1D.setChecked(True)

        # Plotting log
        self.ui.lineEdit_maxSnapResolution.setText('200')

        return

    def _setup_snap_view_groups(self, num_groups):
        """ Set up 6 snap view and control widgets groups
        Class variable _groupSnapViewList will record all of them accordingly
        :param num_groups: number of groups to initialize
        :return: None
        """
        for i in xrange(1, num_groups+1):
            try:
                # get on hold of three widgets with systematic naming
                graph_view = getattr(self.ui, 'graphicsView_snapView%d'% i)
                combo1 = getattr(self.ui, 'comboBox_g%d1'% i)
                combo2 = getattr(self.ui, 'comboBox_g%d2'% i)
                radio_button = getattr(self.ui, 'radioButton_plot%d' % i)
                assert isinstance(radio_button, QRadioButton)
            except AttributeError as e:
                raise RuntimeError('GUI changed but python code is not changed accordingly: %s'%(str(e)))
            else:
                # set up group
                graph_group = SnapGView.SnapGraphicsView(graph_view, combo1, combo2, radio_button)
                self._groupedSnapViewList.append(graph_group)
        # END_FOR(i)

        return

    @property
    def configuration(self):
        """return configuration instance
        :return:
        """
        return self._myConfiguration

    def add_runs_trees(self, ipts_number, ipts_dir, run_tuple_list):
        """
        Add IPTS number and run numbers to the TreeViews in VDrivePlot main GUI
        :param ipts_number:
        :param ipts_dir:
        :param run_tuple_list:
        :return: 2-tuple: boolean, string (error message)
        """
        # check validity
        assert isinstance(ipts_number, int), 'IPTS number {0} must be a integer.'.format(ipts_number)
        assert isinstance(ipts_dir, str), 'Data directory {0} must be a string.'.format(ipts_dir)
        assert isinstance(run_tuple_list, list), 'Run number list should be a list but not a {0}.' \
                                                 ''.format(type(run_tuple_list))

        # Set to tree
        if ipts_number == 0:
            ipts_number = os.path.basename(ipts_dir)
        self.ui.treeView_iptsRun.add_ipts_runs(ipts_number, run_tuple_list)

        # Set to file tree directory
        if ipts_number > 0:
            home_dir = '/SNS/VULCAN'
        else:
            home_dir = os.path.expanduser(ipts_dir)
        curr_dir = ipts_dir
        self.ui.treeView_runFiles.set_root_path(home_dir)
        self.ui.treeView_runFiles.set_current_path(curr_dir)

        return True, ''

    def do_add_runs_by_ipts(self):
        """ import runs by IPTS number or directory
        Purpose: Import runs from archive according to IPTS or specified data directory
        Guarantees: launch a window and get user inputs from the dialog
        :return: None
        """
        # Launch window
        child_window = dlgrun.AddRunsByIPTSDialog(self)

        # init set up
        if self._addedIPTSNumber is not None:
            child_window.set_ipts_number(self._addedIPTSNumber)

        data_root_dir = self._myWorkflow.get_data_root_directory(throw=False)
        child_window.set_data_root_dir(data_root_dir)
        r = child_window.exec_()

        # set the close one
        self._addedIPTSNumber = child_window.get_ipts_number()

        return

    def do_add_runs_to_reduce(self):
        """
        Purpose:
            Add selected runs to reduce.  Selected runs can be all runs of current IPTS
            or from a given range of run numbers
        Requirements:
            At least one radio button is selected.
        Guarantees:
            Selected runs are added to table widget 'tableWidget_selectedRuns'
        :return:
        """
        # Find out the list of runs to add
        if self.ui.radioButton_runsAddAll.isChecked():
            # case to add all runs
            status, ret_obj = self._myWorkflow.get_runs()
            if status is True:
                run_list = ret_obj
            else:
                # Error!
                error_message = ret_obj
                GuiUtility.pop_dialog_error(self, error_message)
                return

        elif self.ui.radioButton_runsAddPartial.isChecked():
            # case to add a subset of runs
            run_list = GuiUtility.parse_integer_list(self.ui.lineEdit_runs)
            print ('[DB...BAT] Parsed run list: {0}'.format(run_list))
            if len(run_list) == 0:
                GuiUtility.pop_dialog_error(self, 'No run is input by user.')
                return

            # check runs with
            status, error_message, exist_run_list = self._myWorkflow.check_runs(self._currIptsNumber, run_list)

            if status is False:
                # Error and return
                GuiUtility.pop_dialog_error(self, error_message)
                if len(exist_run_list) == 0:
                    return
                else:
                    run_list = exist_run_list
            # END-IF

        elif self.ui.radioButton_runsAllInTree.isChecked():
            # case to add all the runs in the IPTS-Run tree
            GuiUtility.pop_dialog_error(self, 'Not Implemented Yet! ASAP Flag 1155B')
            return

        else:
            GuiUtility.pop_dialog_error(self, 'Neither of 2 radio buttons is selected.')
            return

        # Add all runs to table
        self.ui.tableWidget_selectedRuns.append_runs(run_list)

        # Add all runs to my project
        self._myWorkflow.add_runs_to_project(run_list)

        return

    def event_change_log_snap_view(self):
        """
        Event handling if user chooses to plot another log in snap view
        :return:
        """
        # If snap view is locked, then return without any change
        if self._logSnapViewLock:
            return

        snap_resolution = GuiUtility.parse_integer(self.ui.lineEdit_maxSnapResolution)

        for i in xrange(len(self._group_left_box_list)):
            curr_index = int(self._group_left_box_list[i].currentIndex())

            # skip if it is not set!
            if curr_index < 0:
                continue

            # skip if there is no change
            if curr_index == self._group_left_box_values[i]:
                return

            # apply change to status record
            self._group_left_box_values[i] = curr_index
            # plot
            SnapGView.SampleLogView(self._groupedSnapViewList[i], self).plot_sample_log(snap_resolution)
        # END-FOR

        return

    def do_fit_single_peak(self):
        """ Collect parameters and launch Peak-picker window
        :return:
        """
        # create PeakPickerWindow if it is not initialized
        if self._peakPickerWindow is None:
            self._peakPickerWindow = PeakPickWindow.PeakPickerWindow(self)
            self._peakPickerWindow.set_controller(self._myWorkflow)
            self._myChildWindows.append(self._peakPickerWindow)

        # show it!
        self._peakPickerWindow.show()

        return

    def do_load_vanadium_calibration(self):
        """
        Purpose:
            Select and load vanadium calibration GSAS file for the current runs
        Requirements:
            Some runs are light-loaded to project
            The GSAS file must be a time focused vanadium run with proper range, bin size and
            number of spectra.
        Guarantee:
            GSAS file is loaded and inspected.
        :return:
        """
        # user specify the smoothed vanadium file
        # get default directory for smoothed vanadium: /SNS/IPTS-????/shared/Instrument/
        default_van_dir = '/SNS/IPTS-%d/shared/Instrument' % self._currIPTS

        # get calibration file
        file_types = 'GSAS (*.gsa);;All (*.*)'
        smooth_van_file = str(QFileDialog.getOpenFileName(self, 'Get smoothed vanadium GSAS',
                                                          default_van_dir, file_types))

        # return if cancel
        if len(smooth_van_file) == 0:
            return

        # load vanadium file
        van_key = self._myWorkflow.load_smoothed_vanadium(smooth_van_file)

        # get information
        van_info = self._myWorkflow.get_vanadium_info(van_key)

        # write vanadium information in somethere
        # ... write vanadium ...

        return

    def do_load_time_seg_file(self):
        """
        Load time segment file
        :return:
        """
        # Get file name
        file_filter = "CSV (*.csv);;Text (*.txt);;All files (*.*)"
        log_path = self._myWorkflow.get_working_dir()
        seg_file_name = str(QFileDialog.getOpenFileName(self, 'Open Time Segment File', log_path, file_filter))

        # Import file
        status, ret_obj = self._myWorkflow.parse_time_segment_file(seg_file_name)
        if status is False:
            err_msg = ret_obj
            GuiUtility.pop_dialog_error(self, err_msg)
            return
        else:
            ref_run, run_start, time_seg_list = ret_obj

        # Set to table
        self.ui.tableWidget_timeSegment.remove_all_rows()
        self.ui.tableWidget_timeSegment.set_segments(time_seg_list)

        return

    def do_load_sample_log(self):
        """ Load nexus file for plotting sample log.
        The file should be selected from runs in the tree
        :return:
        """
        # Set up a more detailed file path to load log file according to selected run
        # from the project tree
        # run number first
        run_str = str(self.ui.comboBox_chopTabRunList.currentText())
        if run_str.isdigit():
            run_number = int(run_str)
        else:
            GuiUtility.pop_dialog_error(self, 'Run number %s selected in combo-box is not integer.' % run_str)
            return

        # find default directory
        status, ret_obj = self._myWorkflow.get_run_info(run_number)
        if not status:
            GuiUtility.pop_dialog_error(self, 'Unable to get run from tree view: %s' % ret_obj)
            return

        # run is located in workflow controller
        run_file_name, ipts_number = ret_obj
        if os.path.exists(run_file_name):
            self._currLogRunNumber = run_number
            log_file_name = run_file_name
        else:
            # local data file
            log_path = os.path.dirname('/SNS/VULCAN/IPTS-{0}/'.format(ipts_number))
            # Dialog to get the file name
            file_filter = "Event Nexus (*_event.nxs);;All files (*.*)"
            log_file_name = str(QFileDialog.getOpenFileName(self, 'Open NeXus File', log_path, file_filter))
            run_number = 0  # parse_run_number(log_file_name)
        # END-IF

        # Load log
        log_name_list, run_info_str = self.load_sample_run(run_number, log_file_name, smart=True)
        log_name_list = GuiUtility.sort_sample_logs(log_name_list, reverse=False, ignore_1_value=True)

        # Plot first 6 sample logs
        max_resolution = GuiUtility.parse_integer(self.ui.lineEdit_maxSnapResolution)

        # Set up and plot all 6 widgets groups. Need to lock the event handler for 6 combo boxes first
        self._logSnapViewLock = True
        for i in xrange(min(self._numSnapViews, len(log_name_list))):
            # create a log_widget from base snap view widgets and set up
            snap_widget = self._groupedSnapViewList[i]
            log_widget = SnapGView.SampleLogView(snap_widget, self)

            log_widget.reset_log_names(log_name_list)
            log_widget.set_current_log_name(i)

            log_widget.plot_sample_log(max_resolution)
        # END-FOR
        self._logSnapViewLock = False

        # Record sample log file
        self._lastSampleLogFileName = log_file_name

        return

    def do_save_slicer(self):
        """ Save the slicer (splitters) for future splitting
        :return:
        """
        GuiUtility.pop_dialog_error('ASAP')

    def evt_chop_run_state_change(self):
        """
        Event handling for checkbox 'chop data' is checked or unchecked
        :return:
        """
        new_status = self.ui.checkBox_chopRun.checkState()
        if new_status == QtCore.Qt.Unchecked:
            self.ui.tabWidget_reduceData.setCurrentIndex(1)
            self.ui.tabWidget_reduceData.setTabEnabled(0, False)
        else:
            self.ui.tabWidget_reduceData.setCurrentIndex(0)
            self.ui.tabWidget_reduceData.setTabEnabled(0, True)

        return

    def evt_snap1_mouse_press(self, event):
        """
        :return:
        """
        self.ui.radioButton_plot1.setChecked(True)
        self.evt_snap_mouse_press(event, 0)

    def evt_snap2_mouse_press(self, event):
        """
        :return:
        """
        self.ui.radioButton_plot2.setChecked(True)
        self.evt_snap_mouse_press(event, 1)

    def evt_snap3_mouse_press(self, event):
        """
        :return:
        """
        self.ui.radioButton_plot3.setChecked(True)
        self.evt_snap_mouse_press(event, 2)

    def evt_snap4_mouse_press(self, event):
        """
        :return:
        """
        self.ui.radioButton_plot4.setChecked(True)
        self.evt_snap_mouse_press(event, 3)

    def evt_snap5_mouse_press(self, event):
        """
        :return:
        """
        self.ui.radioButton_plot5.setChecked(True)
        self.evt_snap_mouse_press(event, 4)

    def evt_snap6_mouse_press(self, event):
        """
        :return:
        """
        self.ui.radioButton_plot6.setChecked(True)
        self.evt_snap_mouse_press(event, 5)

    def evt_snap_mouse_press(self, event, snap_view_index):
        """ Generalized snap canvas mouse event handler
        NOTE: on Linux, button 1 is left button, buton 3 is right button
        :param event:
        :return:
        """
        # Set class variable for communication
        self._currentSnapViewIndex = snap_view_index

        x = event.xdata
        y = event.ydata
        button = event.button

        if x is not None and y is not None:
            if button == 3:
                # right click of mouse will pop up a context-menu
                self.ui.menu = QMenu(self)

                pop_action = QAction('Pop', self)
                pop_action.triggered.connect(self.pop_snap_view)
                self.ui.menu.addAction(pop_action)

                # add other required actions
                self.ui.menu.popup(QCursor.pos())
        # END-IF

        return

    def evt_quit(self):
        """
        Quit application without saving
        :return:
        """
        # TODO/NEXT - Save the session automatically before leaving
        self.save_settings()
        # and ... ...

        for child_window in self._myChildWindows:
            child_window.close()

        self.close()

        return

    def execute_command(self, vdrive_command):
        """
        Execute a Vdrive command
        No exception is expected to be raised from this method
        :param vdrive_command: a command (including all the arguments)
        :return:
        """
        # check
        assert isinstance(vdrive_command, str), 'VDRIVE command must be a string but not.' \
                                                '' % str(type(vdrive_command))

        # split
        # need to strip the space around command
        # vdrive_command = vdrive_command.replace(' ', '')

        # split the command from arguments
        command_script = vdrive_command.split(',')
        command = command_script[0].strip()
        status, err_msg = self._vdriveCommandProcessor.process_commands(command, command_script[1:])

        return status, err_msg

    def get_sample_log_value(self, run_number, log_name, time_range=None, relative=False):
        """
        Get sample log value
        :param run_number:
        :param log_name:
        :param time_range:
        :param relative:
        :return: 2-tuple as (numpy.ndarray, numpy.ndarray)
        """
        # check
        if time_range is None:
            start_time = None
            stop_time = None
        else:
            assert len(time_range) == 2, 'blabla'
            start_time = time_range[0]
            stop_time = time_range[1]
            assert start_time < stop_time, 'blabla'

        # about run number
        if run_number is None:
            run_number = int(self.ui.comboBox_chopTabRunList.currentText())

        vec_times, vec_log_value = self._myWorkflow.get_sample_log_values(run_number, log_name, start_time, stop_time,
                                                                          relative=relative)

        return vec_times, vec_log_value

    def get_ipts_runs(self):
        """
        Get added IPTS and run to caller
        :return:
        """
        return self._myWorkflow.get_project_runs()

    def get_reserved_commands(self):
        """
        Get reserved commands from VDrive command processor
        :return:
        """
        # all commands are upper case.  make them also to be lower case too
        command_list = self._vdriveCommandProcessor.get_vdrive_commands()
        lower_case_commands = list()
        for command in command_list:
            lower_case_commands.append(command.lower())

        # merge them
        command_list.extend(lower_case_commands)

        return command_list

    def get_controller(self):
        """
        Get workflow controller instance
        :return:
        """
        return self._myWorkflow

    def load_sample_run(self, run, nxs_file_name, smart):
        """
        Load sample run
        :param run: string or integer as nxs file name or run number
        :param smart: flag to give the log name in a smart way
        :return: list of string for log names
        """
        # Check
        assert isinstance(run, int), 'Run number {0} must be an integer but not a {1}'.format(run, type(run))
        assert isinstance(nxs_file_name, str) or nxs_file_name is None,\
            'Nexus file name {0} must be a string but not a {1}.'.format(nxs_file_name, type(nxs_file_name))

        # get files
        if nxs_file_name is None:
            # Load data without file name, IPTS number and etc.
            self._myWorkflow.load_nexus_file(ipts_number=None, run_number=run, file_name='VULCAN_{0}'.format(run),
                                             meta_data_only=True)
        else:
            self._myWorkflow.load_nexus_file(ipts_number=None, run_number=run, file_name=nxs_file_name,
                                             meta_data_only=True)

        # Get log names
        log_name_list = self._myWorkflow.get_sample_log_names(run, smart)

        # get run information
        run_info_str = self._myWorkflow.get_run_experiment_information(run)

        return log_name_list, run_info_str

    def menu_save_project(self):
        """
        Save session called from menu
        :return:
        """
        if self._savedSessionFileName is None:
            # save to configuration directory
            # get default path, make it if does not exist
            default_path = os.path.expanduser('~/.vdrive')
            if os.path.exists(default_path) is False:
                os.mkdir(default_path)

            # get the default name
            session_file_name = os.path.join(default_path, 'auto_save.xml')
            self._savedSessionFileName = session_file_name

        self._myWorkflow.save_session(self._savedSessionFileName)

        return

    def menu_save_session_as(self):
        """
        Save session as
        :return:
        """
        saved_session_file_name = str(QFileDialog.getSaveFileName(self, 'Save Session',
                                                                  self._myWorkflow.get_working_dir(),
                                                                  'XML files (*.xml); All files (*.*)'))

        self._myWorkflow.save_session(saved_session_file_name)

        return

    def menu_load_auto(self):
        """ Load auto-saved project
        :return:
        """
        default_path = os.path.expanduser('~/.vdrive')
        session_file_name = os.path.join(default_path, 'auto_save.xml')
        assert os.path.exists(session_file_name), 'Auto saved project file %s does not exist.' % session_file_name

        self.load_project(session_file_name)

        return

    def menu_setup_auto_vanadium_file(self):
        """
        set up the auto-seek vanadium file
        :return:
        """
        import VanCalibrationRulesSetup as vanSetup
        setup_dialog = vanSetup.SetupVanCalibRuleDialog(self)
        setup_dialog.exec_()

        return

    def load_project(self, project_file_name):
        """

        :param project_file_name:
        :return:
        """
        # Load
        status, input_file_name = self._myWorkflow.load_session(project_file_name)
        if status is False:
            GuiUtility.pop_dialog_error('Unable to load session from %s' % input_file_name)

        # Set input file to default session back up file
        self._savedSessionFileName = input_file_name

        # Set up tree
        # FIXME - Consider to refactor these to a method with do_add_runs_by_ipts
        ipts_dict = self._myWorkflow.get_project_runs()
        for ipts_number in sorted(ipts_dict.keys()):
            self.ui.treeView_iptsRun.add_ipts_runs(ipts_number, ipts_dict[ipts_number])
            # FIXME - Need to figure out how to deal with this
            home_dir = '/SNS/VULCAN'
            curr_dir = os.path.join(home_dir, 'IPTS-%d' % ipts_number)
            self.ui.treeView_runFiles.set_root_path(home_dir)
            self.ui.treeView_runFiles.set_current_path(curr_dir)

        return

    def menu_load_project(self):
        """
        Load session from file
        :return:
        """
        # Get file name
        input_file_name = str(QFileDialog.getOpenFileName(self, 'Load Session', self._myWorkflow.get_working_dir(),
                                                          'XML files (*.xml);; All files (*.*)'))
        if len(input_file_name) == 0:
            # aborted, quit
            return

        # Load
        # FIXME/NOW - consider to replace the following by method load_project!
        status, input_file_name = self._myWorkflow.load_session(input_file_name)
        if status is False:
            GuiUtility.pop_dialog_error('Unable to load session from %s' % input_file_name)

        # Set input file to default session back up file
        self._savedSessionFileName = input_file_name

        # Set up tree
        # FIXME - Consider to refactor these to a method with do_add_runs_by_ipts
        ipts_dict = self._myWorkflow.get_project_runs()
        for ipts_number in sorted(ipts_dict.keys()):
            self.ui.treeView_iptsRun.add_ipts_runs(ipts_number, ipts_dict[ipts_number])
            # FIXME - Need to figure out how to deal with this
            home_dir = '/SNS/VULCAN'
            curr_dir = os.path.join(home_dir, 'IPTS-%d' % ipts_number)
            self.ui.treeView_runFiles.set_root_path(home_dir)
            self.ui.treeView_runFiles.set_current_path(curr_dir)

        return

    def menu_config(self):
        """ Open configuration menu
        :return:
        """
        self._configWindow = configwindow.ConfigWindow(self)

        self._configWindow.set_controller(self._myWorkflow)

        self._configWindow.show()

        return

    def do_launch_log_picker_window(self):
        """
        Pop out manual picker window
        :return: handler to log picker window
        """
        # Start
        if isinstance(self._logPickerWindow, LogPicker.WindowLogPicker):
            self._logPickerWindow.show()
        else:
            # Get selected run number from sidebar tree view
            status, ret_obj = self.ui.treeView_iptsRun.get_current_run()
            if status is True:
                run_number = ret_obj
                try:
                    run_number = int(run_number)
                except ValueError:
                    run_number = None
            else:
                run_number = None

            # get IPTS from archive
            if run_number is not None:
                # current IPTS number
                ipts_number = self._myWorkflow.get_ipts_from_run(run_number)
            else:
                ipts_number = None

            # create the log processing window
            self._logPickerWindow = LogPicker.WindowLogPicker(self, ipts_number, run_number)
            self._myChildWindows.append(self._logPickerWindow)

        # Set up tree view for runs
        self._logPickerWindow.setup()

        # Show
        self._logPickerWindow.show()

        return self._logPickerWindow

    def pop_snap_view(self):
        """ Pop out snap view dialog (window)
        :return:
        """
        # Check index
        if self._currentSnapViewIndex < 0 \
                or self._currentSnapViewIndex >= len(self._groupedSnapViewList):
            error_message = 'Current snap view index (%d) is either not defined ' \
                            'or out of boundary' % self._currentSnapViewIndex
            GuiUtility.pop_dialog_error(error_message)

        # Create a Snap view window if needed
        if self._snapViewWindow is None:
            # Create a new window
            print '[DB Trace] Creating a new SnapViewDialog.'
            self._snapViewWindow = dlgSnap.DialogLogSnapView(self)

        # Refresh?
        if self._snapViewWindow.allow_new_session() is False:
            # If window is open but not saved, pop error message
                GuiUtility.pop_dialog_error(self, 'Current window is not saved.')
                return
        # END-IF

        # Get the final data
        sample_log_view = SnapGView.SampleLogView(self._groupedSnapViewList[self._currentSnapViewIndex], self)
        sample_log_name = sample_log_view.get_log_name()
        num_skipped_second = GuiUtility.parse_float(self.ui.lineEdit_numSecLogSkip)
        self._snapViewWindow.setup(self._myWorkflow, self._currLogRunNumber, sample_log_name, num_skipped_second)

        self._snapViewWindow.show()

        return

    def set_ipts_number(self, ipts_number):
        """
        set IPTS number
        :param ipts_number:
        :return:
        """
        assert isinstance(ipts_number, int), 'blabla'

        self._currIptsNumber = ipts_number

        return

    def set_selected_runs(self, run_list):
        """ Set selected runs from a list..
        :param run_list:
        :return:
        """
        assert isinstance(run_list, list)
        assert len(run_list) > 0

        self.ui.tableWidget_selectedRuns.append_runs(run_list)

        return
