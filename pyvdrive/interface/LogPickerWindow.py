########################################################################
#
# Window for set up log slicing splitters
#
########################################################################
import os
import numpy
try:
    import qtconsole.inprocess
    from PyQt5 import QtCore as QtCore
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5.QtWidgets import QMainWindow, QButtonGroup, QFileDialog
except ImportError:
    from PyQt4 import QtCore as QtCore
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4.QtGui import QMainWindow, QButtonGroup, QFileDialog

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.GuiUtility as GuiUtility
from pyvdrive.interface.gui.vdrivetreewidgets import VdriveRunManagerTree
from pyvdrive.interface.gui.samplelogview import LogGraphicsView
from pyvdrive.lib import datatypeutility
import ReducedDataView
import LoadMTSLogWindow
import QuickChopDialog

OUT_PICKER = 0
IN_PICKER = 1
IN_PICKER_MOVING = 2
IN_PICKER_SELECTION = 3


# TODO/ISSUE/NOWNOW - label_runStartEpoch never been written


class WindowLogPicker(QMainWindow):
    """ Class for general-puposed plot window
    """
    # class
    def __init__(self, parent=None, ipts_number=None, init_run=None):
        """ Init
        """
        # call base
        QMainWindow.__init__(self)

        # child windows
        self._manualSlicerDialog = None

        # parent
        self._myParent = parent
        self._mutexLockSwitchSliceMethod = False

        # special slicer helper
        self._curr_curve_slicer = None

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/VdriveLogPicker.ui")
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()

        # Set up widgets
        self._disable_widgets()
        self._init_widgets_setup()

        # Defining widget handling methods
        self.ui.pushButton_loadRunSampleLog.clicked.connect(self.do_load_run)
        self.ui.pushButton_prevLog.clicked.connect(self.do_load_prev_log)
        self.ui.pushButton_nextLog.clicked.connect(self.do_load_next_log)
        self.ui.pushButton_readLogFile.clicked.connect(self.do_scan_log_file)
        self.ui.pushButton_loadMTSLog.clicked.connect(self.do_load_mts_log)
        self.ui.comboBox_blockList.currentIndexChanged.connect(self.do_load_mts_log)
        self.ui.comboBox_logFrameUnit.currentIndexChanged.connect(self.evt_re_plot_mts_log)

        self.ui.checkBox_hideSingleValueLog.stateChanged.connect(self.load_log_names)

        # chopping setup
        self.ui.radioButton_timeSlicer.toggled.connect(self.evt_switch_slicer_method)
        self.ui.radioButton_logValueSlicer.toggled.connect(self.evt_switch_slicer_method)
        self.ui.radioButton_manualSlicer.toggled.connect(self.evt_switch_slicer_method)
        self.ui.pushButton_slicer.clicked.connect(self.do_chop)
        self.ui.pushButton_viewReduced.clicked.connect(self.do_view_reduced_data)
        self.ui.pushButton_setXAxis.clicked.connect(self.do_plot_sample_logs)

        # Further operation
        # self.ui.pushButton_highlight.clicked.connect()
        # #              self.do_highlight_selected)

        # automatic slicer setup
        self.ui.pushButton_setupAutoSlicer.clicked.connect(self.do_setup_uniform_slicer)
        self.ui.checkBox_showSlicer.stateChanged.connect(self.evt_show_slicer)

        # manual slicer picker
        self.ui.pushButton_showManualSlicerTable.clicked.connect(self.do_show_manual_slicer_table)
        self.ui.pushButton_loadSlicerFile.clicked.connect(self.do_import_slicer_file)

        # Slicer table
        # Canvas
        self.ui.pushButton_doPlotSample.clicked.connect(self.evt_plot_sample_log)
        self.ui.pushButton_resizeCanvas.clicked.connect(self.do_resize_canvas)
        self.ui.comboBox_logNames.currentIndexChanged.connect(self.evt_plot_sample_log)

        self.ui.radioButton_useMaxPointResolution.toggled.connect(self.evt_change_resolution_type)

        self.ui.radioButton_useTimeResolution.toggled.connect(self.evt_change_resolution_type)

        self.ui.pushButton_prevPartialLog.clicked.connect(self.do_load_prev_log_frame)
        self.ui.pushButton_nextPartialLog.clicked.connect(self.do_load_next_log_frame)

        # menu actions
        self.ui.actionExit.triggered.connect(self.evt_quit_no_save)

        # TODO - TONIGHT 1: pushButton_cyclic_helper

        self.ui.actionOpenH5Log.triggered.connect(self.do_load_h5_log)
        self.ui.actionIPython_Command_Console.triggered.connect(self.do_launch_console_view)

        # # Event handling for pickers
        self._mtsFileLoaderWindow = None

        # child windows
        self._quickChopDialog = None

        # Initial setup
        if init_run is not None:
            datatypeutility.check_int_variable('Initial run number', init_run, (0, None))
            self.ui.lineEdit_runNumber.setText('%d' % init_run)
            self._iptsNumber = ipts_number
        else:
            self._iptsNumber = None

        # Class variables
        self._logNameList = list()
        self._sampleLogDict = dict()

        # self._currentPickerID = None
        self._myPickerMode = OUT_PICKER
        self._currMousePosX = 0.
        self._currMousePosY = 0.

        # Picker management
        self._myPickerIDList = list()

        # Experiment-related variables
        self._currLogType = None
        self._currRunNumber = None
        self._currLogName = None

        self._currentBlockIndex = None
        self._currentFrameUnit = str(self.ui.comboBox_logFrameUnit.currentText())
        self._currentStartPoint = None
        self._currentStopPoint = None
        self._averagePointsPerSecond = None
        self._blockIndex = None

        # MTS log format dictionary.  key is file name, value is the format dictionary
        self._mtsLogFormat = dict()

        # Highlighted lines list
        self._myHighLightedLineList = list()

        # Mutex/Lock, multiple threading
        self._mutexLockLogNameComboBox = False

        # Reference to slicers that have been set up
        self._currSlicerKey = None
        self._slicerKeyList = list()

        return

    def _promote_widgets(self):
        treeView_iptsRun_layout = QVBoxLayout()
        self.ui.frame_treeView_iptsRun.setLayout(treeView_iptsRun_layout)
        self.ui.treeView_iptsRun = VdriveRunManagerTree(self)
        treeView_iptsRun_layout.addWidget(self.ui.treeView_iptsRun)

        graphicsView_main_layout = QVBoxLayout()
        self.ui.frame_graphicsView_main.setLayout(graphicsView_main_layout)
        self.ui.graphicsView_main = LogGraphicsView(self)
        graphicsView_main_layout.addWidget(self.ui.graphicsView_main)

        return

    def _disable_widgets(self):
        """
        Disable some widgets temporarily
        :return:
        """
        self.ui.pushButton_nextLog.setEnabled(False)
        self.ui.pushButton_nextLog.hide()

        self.ui.pushButton_prevLog.setEnabled(False)
        self.ui.pushButton_prevLog.hide()

    def _init_widgets_setup(self):
        """
        Initialize widgets
        :return:
        """
        # graphic view
        self.ui.graphicsView_main.set_parent_window(self)

        # ipts-run selection tree
        self.ui.treeView_iptsRun.set_main_window(self)
        # about plotting
        self.ui.checkBox_autoResize.setChecked(True)
        # options to create slicing segments
        self.ui.radioButton_noExpand.setChecked(True)
        # set up the check boxes
        self.ui.checkBox_hideSingleValueLog.setChecked(True)

        # type of slicer picker
        self.ui.radioButton_timeSlicer.setChecked(True)
        self.ui.radioButton_logValueSlicer.setChecked(False)
        self.ui.radioButton_manualSlicer.setChecked(False)
        self._set_main_slice_method()
        for item in ['Both', 'Increase', 'Decrease']:
            self.ui.comboBox_logChangeDirection.addItem(item)

        # resolution
        self.ui.radioButton_useMaxPointResolution.setChecked(True)
        self.ui.radioButton_useTimeResolution.setChecked(False)

        self.ui.lineEdit_resolutionMaxPoints.setText('10000')
        self.ui.lineEdit_resolutionMaxPoints.setEnabled(True)
        self.ui.lineEdit_timeResolution.setText('1')
        self.ui.lineEdit_timeResolution.setEnabled(False)

        # group radio buttons
        self.ui.resolution_group = QButtonGroup(self)
        self.ui.resolution_group.addButton(self.ui.radioButton_useMaxPointResolution, 0)
        self.ui.resolution_group.addButton(self.ui.radioButton_useTimeResolution, 1)

        # combo box
        self.ui.comboBox_logFrameUnit.clear()
        self.ui.comboBox_logFrameUnit.addItems(['points', 'seconds'])
        self.ui.comboBox_logFrameUnit.setCurrentIndex(0)
        # initial value for number of points on
        self.ui.lineEdit_logFrameSize.setText('5000')

        # check boxes
        self.ui.checkBox_showSlicer.setChecked(True)

        return

    def _set_main_slice_method(self):
        """
        Set the main slicer method, manual or auto
        :return:
        """
        # check for a possible error condition
        if self.ui.radioButton_timeSlicer.isChecked() is False:
            try:
                self.ui.graphicsView_main.get_data_range()
            except RuntimeError:
                # data range is not set up yet
                self._mutexLockSwitchSliceMethod = True   # lock slicer
                self.ui.radioButton_timeSlicer.setChecked(True)
                self._mutexLockSwitchSliceMethod = True   # un-lock slicer
                return
        # END-IF

        # enable to disable
        if self.ui.radioButton_timeSlicer.isChecked():
            # time slicer
            self.ui.groupBox_sliceSetupAuto.setEnabled(True)
            self.ui.groupBox_slicerSetupManual.setEnabled(False)

            self.ui.lineEdit_minSlicerLogValue.setEnabled(False)
            self.ui.lineEdit_slicerLogValueStep.setEnabled(True)
            self.ui.lineEdit_maxSlicerLogValue.setEnabled(False)
            self.ui.comboBox_logChangeDirection.setEnabled(False)

            # hide some labels and line edits
            self.ui.label_minValue.setHidden(True)
            self.ui.label_maxValue.setHidden(True)
            self.ui.label_direction.setHidden(True)
            self.ui.lineEdit_minSlicerLogValue.setHidden(True)
            self.ui.lineEdit_maxSlicerLogValue.setHidden(True)
            self.ui.comboBox_logChangeDirection.setHidden(True)

            self.ui.label_step.setText('Time Step')

            # set up graphic view's mode
            self.ui.graphicsView_main.set_manual_slicer_setup_mode(False)

        elif self.ui.radioButton_logValueSlicer.isChecked():
            # log value slicer
            self.ui.groupBox_sliceSetupAuto.setEnabled(True)
            self.ui.groupBox_slicerSetupManual.setEnabled(False)

            self.ui.lineEdit_minSlicerLogValue.setEnabled(True)
            self.ui.lineEdit_slicerLogValueStep.setEnabled(True)
            self.ui.lineEdit_maxSlicerLogValue.setEnabled(True)
            self.ui.comboBox_logChangeDirection.setEnabled(True)

            # also set up the min and max log value
            x_min, x_max, y_min, y_max = self.ui.graphicsView_main.get_data_range()

            self.ui.lineEdit_minSlicerLogValue.setText('%.4f' % y_min)
            self.ui.lineEdit_maxSlicerLogValue.setText('%.4f' % y_max)

            # show some labels and line edits
            self.ui.label_minValue.setHidden(False)
            self.ui.label_maxValue.setHidden(False)
            self.ui.label_direction.setHidden(False)
            self.ui.lineEdit_minSlicerLogValue.setHidden(False)
            self.ui.lineEdit_maxSlicerLogValue.setHidden(False)
            self.ui.comboBox_logChangeDirection.setHidden(False)
            # set up graphic view's mode
            self.ui.graphicsView_main.set_manual_slicer_setup_mode(False)

            self.ui.label_step.setText('Log Value Step')

        else:
            # manual slicer
            self.ui.groupBox_sliceSetupAuto.setEnabled(False)
            self.ui.groupBox_slicerSetupManual.setEnabled(True)

            # set up graphic view's mode
            self.ui.graphicsView_main.set_manual_slicer_setup_mode(True)

            # set up and launch ManualSlicerSetupDialog
            self.do_show_manual_slicer_table()

        return

    def do_chop(self):
        """
        Save a certain number of time segment from table tableWidget_segments
        :return:
        """
        # get the run and raw file
        raw_file_name = None
        try:
            run_number = int(self.ui.lineEdit_runNumber.text())
            status, info_tup = self.get_controller().get_run_info(run_number)
            if status:
                raw_file_name = info_tup[0]
        except ValueError as val_error:
            raise RuntimeError('Unable to find out run number due to {0}'.format(val_error))

        # pop up the dialog
        self._quickChopDialog = QuickChopDialog.QuickChopDialog(self, self._currRunNumber, raw_file_name)
        result = self._quickChopDialog.exec_()

        # quit if user cancels the operation
        if result == 0:
            # cancel operation
            return
        else:
            # get information from the dialog box
            output_to_archive = self._quickChopDialog.output_to_archive
            if output_to_archive:
                output_dir = None
            else:
                output_dir = self._quickChopDialog.output_directory

            to_save_nexus = self._quickChopDialog.save_to_nexus
            to_reduce_gsas = self._quickChopDialog.reduce_data
        # END-IF-ELSE

        # check slicer keys
        if self._currSlicerKey is None:
            GuiUtility.pop_dialog_error(self, 'Slicer has not been set up yet.')
        else:
            datatypeutility.check_string_variable('Current slicer key', self._currSlicerKey, None)
        # slice data
        status, message = self.get_controller().project.chop_run(run_number, self._currSlicerKey,
                                                                 reduce_flag=to_reduce_gsas,
                                                                 vanadium=None,
                                                                 save_chopped_nexus=to_save_nexus,
                                                                 number_banks=3,  # TODO - NIGHT - Shall be settable
                                                                 tof_correction=False,
                                                                 output_directory=output_dir,
                                                                 user_bin_parameter=None,
                                                                 roi_list=list(),
                                                                 mask_list=list(),
                                                                 nexus_file_name=None,
                                                                 gsas_iparm_file='vulcan.prm',
                                                                 overlap_mode=False,
                                                                 gda_start=1)
        if status:
            GuiUtility.pop_dialog_information(self, message)
        else:
            GuiUtility.pop_dialog_error(self, message)

        return

    def do_import_slicer_file(self):
        """ Import an ASCII file which contains the slicers.
        The format will be a 3 column file as run start (in second), run stop(in second) and target workspace
        :return:
        """
        from pyvdrive.lib import file_utilities

        # get file
        default_dir = self._myParent.get_controller().get_working_dir()
        slicer_file_name = GuiUtility.get_load_file_by_dialog(self, 'Read Slicer File', default_dir,
                                                              'Data File (*.dat);;Text (*.txt)')

        if len(slicer_file_name) == 0:
            # return if operation is cancelled
            return

        try:
            ref_run, run_start_time, slicer_list = file_utilities.parse_data_slicer_file(slicer_file_name)
            self.get_controller().import_data_slicers(slicer_file_name)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self, '{}'.format(run_err))
            return

        # check
        if len(slicer_list) == 0:
            GuiUtility.pop_dialog_error(self, 'There is no valid slicers in file {0}'.format(slicer_file_name))
            return
        else:
            # sort
            slicer_list.sort()

        # get run start time in second
        # TODO - TONIGHT 0 - Fix this: TypeError: 'TimeSegment' object does not support indexing
        slicer_start_time = slicer_list[0][0]   # Error:  TypeError: 'TimeSegment' object does not support indexing
        # Error above line

        if slicer_start_time > 3600 * 24 * 365:
            # larger than 1 year. then must be an absolute time
            run_start_s = int(self.ui.label_runStartEpoch.text())
        else:
            # relative time: no experiment in 1991
            run_start_s = 0.

        # set to figure
        prev_stop_time = -1.E-20
        for slicer in slicer_list:
            start_time, stop_time, target = slicer
            if start_time > prev_stop_time:
                self.ui.graphicsView_main.add_picker(start_time - run_start_s)
            self.ui.graphicsView_main.add_picker(stop_time - run_start_s)
            prev_stop_time = stop_time

        return

    def do_show_manual_slicers(self):
        """ Color the segment from different target workspaces
        :return:
        """
        return

    def do_launch_console_view(self):
        """ Launch IPython console view
        :return:
        """
        self._myParent.menu_workspaces_view()

        return

    def do_load_h5_log(self):
        """ Load sample log file in HDF5 format
        :return:
        """
        from pyvdrive.lib import file_utilities

        h5_log_name = GuiUtility.get_load_file_by_dialog(self, title='Sample log file in HDF5 format',
                                                         default_dir=self.get_controller().working_dir(),
                                                         file_filter='HDF5 (*.hdf5);;HDF5 (*.hdf)')

        sample_log_dict = file_utilities.load_sample_logs_h5(log_h5_name=h5_log_name)

        # TODO - TODAY - Need to find out what is the next step after loading sample logs

        return

    def do_load_mts_log(self):
        """ Load MTS log file

        :return:
        """
        # get file and match
        mts_log_file = str(self.ui.lineEdit_logFileName.text())
        assert mts_log_file in self._mtsLogFormat, 'MTS log format has not key for log file %s. Current keys are' \
                                                   '%s.' % (mts_log_file, str(self._mtsLogFormat.keys()))

        # block ID and set up average step size
        block_index = int(self.ui.comboBox_blockList.currentText())

        # get this dictionary
        mts_log_dict = self._mtsLogFormat[mts_log_file]

        print '[DB...BAT] mts log dict: ', mts_log_dict

        duration = mts_log_dict['duration'][block_index][1] - mts_log_dict['duration'][block_index][0]
        num_points = mts_log_dict['data'][block_index][1] - mts_log_dict['data'][block_index][0]
        self._averagePointsPerSecond = int(num_points / duration)
        assert self._averagePointsPerSecond > 1, 'Number of data points per seconds %d must be large than 0.' \
                                                 '' % self._averagePointsPerSecond

        # get delta points
        delta_points = self.get_data_size_to_load()

        # set up start and stop
        self._currentStartPoint = 0
        self._currentStopPoint = self._currentStartPoint + delta_points
        self._blockIndex = block_index

        # load
        self.load_plot_mts_log(reset_canvas=True)

        self._currLogType = 'mts'

        return

    def do_load_next_log_frame(self):
        """
        Load the next frame of the on-show sample log
        :return:
        """
        # get parameters & check
        delta_points = self.get_data_size_to_load()
        if delta_points <= 0:
            # no point to load
            print '[DB INFO] calculated delta-points = %d < 0. No loading' % delta_points

        # get the file
        mts_log_file = str(self.ui.lineEdit_logFileName.text())
        format_dict = self._mtsLogFormat[mts_log_file]

        # reset the start and stop points
        prev_end_point = self._currentStopPoint

        if self._currentStopPoint + delta_points > format_dict['data'][self._blockIndex][1]:
            # the next frame is not a complete frame
            stop_point = format_dict['data'][self._blockIndex][1]
            if stop_point == self._currentStopPoint:
                # already at the last frame. no operation is needed.
                # TODO - a better message is required.
                orig_text = str(self.ui.label_logFileLoadInfo.text())
                self.ui.label_logFileLoadInfo.setText(orig_text + '  [End]')
                return
            else:
                self._currentStopPoint = stop_point
            # END-IF
        else:
            # next frame is still a complete frame
            self._currentStopPoint += delta_points
        # END-IF

        # reset starting
        self._currentStartPoint = prev_end_point

        # load
        self.load_plot_mts_log(reset_canvas=True)

        return

    def do_load_prev_log_frame(self):
        """
        Load the previous frame of the on-showing sample log
        :return:
        """
        # get parameters & check
        delta_points = self.get_data_size_to_load()

        # reset the start and stop points
        self._currentStopPoint = self._currentStartPoint
        self._currentStartPoint = max(0, self._currentStartPoint-delta_points)

        # load and plot
        self.load_plot_mts_log(reset_canvas=True)

        return

    def do_load_run(self):
        """
        Load a (single) run and plot
        :return:
        """
        # Get run number
        ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber)
        run_number = GuiUtility.parse_integer(self.ui.lineEdit_runNumber)
        if run_number is None or ipts_number is None:
            GuiUtility.pop_dialog_error(self, 'Unable to load: both IPTS or run value must be specified.')
            return

        # Get sample logs
        try:
            self._logNameList, run_info_str = self._myParent.load_sample_run(ipts_number, run_number, None,
                                                                             smart=True)
            self._logNameList.sort()

            # Update class variables, add a new entry to sample log value holder
            self._currRunNumber = run_number
            self._sampleLogDict[self._currRunNumber] = dict()

            # set run information
            self.ui.label_runInformation.setText(run_info_str)

        except NotImplementedError as err:
            GuiUtility.pop_dialog_error(self,
                                        'Unable to load sample logs from run %d due to %s.' % (run_number, str(err)))
            return
        finally:
            # self.ui.graphicsView_main.remove_slicers()
            # TODO ASAP Need to find out which is better remove_slicers or clear_picker
            self.ui.graphicsView_main.clear_picker()

        # set the type of file
        self._currLogType = 'nexus'

        # Load log names to combo box _logNames
        self.load_log_names()

        # plot the first log
        log_name = str(self.ui.comboBox_logNames.currentText())
        log_name = log_name.replace(' ', '').split('(')[0]
        self.plot_nexus_log(log_name)
        self._currLogName = log_name

        return

    def do_load_next_log(self):
        """ Load next log
        :return:
        """
        # get current index of the combo box and find out the next
        current_index = self.ui.comboBox_logNames.currentIndex()
        max_index = self.ui.comboBox_logNames.size()
        # TODO - TODAY - Test - logNames.size() may not a correction method to find total number of entries of a combo box
        next_index = (current_index + 1) % int(max_index)

        # advance to the next one
        self.ui.comboBox_logNames.setCurrentIndex(next_index)
        sample_log_name = str(self.ui.comboBox_logNames.currentText())
        sample_log_name = sample_log_name.split('(')[0].strip()

        # Plot
        if self._currLogType == 'nexus':
            self.plot_nexus_log(log_name=sample_log_name)
        else:
            self.plot_mts_log(log_name=sample_log_name,
                              reset_canvas=not self.ui.checkBox_overlay.isChecked())

        # Update
        self._currLogName = sample_log_name

        return

    def do_load_prev_log(self):
        """ Load previous log
        :return:
        """
        # get current index of the combo box and find out the next
        current_index = self.ui.comboBox_logNames.currentIndex()
        if current_index == 0:
            prev_index = self.ui.comboBox_logNames.size() - 1
        else:
            prev_index = current_index - 1

        # advance to the next one
        self.ui.comboBox_logNames.setCurrentIndex(prev_index)
        sample_log_name = str(self.ui.comboBox_logNames.currentText())
        sample_log_name = sample_log_name.split('(')[0].strip()

        # Plot
        if self._currLogType == 'nexus':
            self.plot_nexus_log(log_name=sample_log_name)
        else:
            self.plot_mts_log(log_name=sample_log_name,
                              reset_canvas=not self.ui.checkBox_overlay.isChecked())

        # Update
        self._currLogName = sample_log_name

        return

    def do_show_manual_slicer_table(self):
        """

        :return:
        """
        import ManualSlicerSetupDialog

        if self._manualSlicerDialog is None:
            self._manualSlicerDialog = ManualSlicerSetupDialog.ManualSlicerSetupTableDialog(self)
            self._manualSlicerDialog.setWindowTitle('New!')
        else:
            self._manualSlicerDialog.setHidden(False)
            self._manualSlicerDialog.setWindowTitle('From Hide')

        self._manualSlicerDialog.show()

        return

    def do_view_reduced_data(self):
        """
        launch the window to view reduced data
        :return:
        """
        # launch reduced-data-view window
        view_window = self._myParent.do_launch_reduced_data_viewer()
        assert isinstance(view_window, ReducedDataView.GeneralPurposedDataViewWindow),\
            'The view window ({0}) is not a proper ReducedDataView.GeneralPurposedDataViewWindow instance.' \
            ''.format(view_window.__class__.__name__)

        # get chopped and reduced workspaces from controller
        try:
            info_dict = self.get_controller().get_chopped_data_info(self._currRunNumber,
                                                                    slice_key=self._currSlicerKey,
                                                                    reduced=True)
            print ('[DB...BAT] Chopped data info: {}'.format(info_dict))
            data_key = self.get_controller().project.current_chopped_key()
            view_window.do_refresh_existing_runs(set_to=data_key, plot_selected=True, is_chopped=True)

            if False:
                # chopped_workspace_list = info_dict['workspaces']
                # view_window.add_chopped_workspaces(self._currRunNumber, chopped_workspace_list, focus_to_it=True)
                # view_window.ui.groupBox_plotChoppedRun.setEnabled(True)
                # view_window.ui.groupBox_plotSingleRun.setEnabled(False)
                # view_window.do_plot_diffraction_data()

                # set up the run time
                # view_window.label_loaded_data(run_number=self._currRunNumber,
                #                               is_chopped=True,
                #                               chop_seq_list=range(len(chopped_workspace_list)))
                raise NotImplementedError('Removed!')

        except RuntimeError as run_err:
            error_msg = 'Unable to get chopped and reduced workspaces. for run {0} with slicer {1} due to {2}.' \
                        ''.format(self._currRunNumber, self._currSlicerKey, run_err)
            GuiUtility.pop_dialog_error(self, error_msg)

        return

    def do_plot_sample_logs(self):
        """
        Plot sample logs
        :return:
        """
        log_name_x = str(self.ui.comboBox_logNamesX.currentText())
        log_name_y = str(self.ui.comboBox_logNames.currentText())

        self.plot_nexus_log(log_name_y, log_name_x)
        # self.plot_mts_log(log_name=log_name_y, reset_canvas=True, x_axis_log=log_name_x)

        return

    def do_scan_log_file(self):
        """
        Purpose: read MTS log file by launching an MTS log file parsing window
        :return:
        """
        self._mtsFileLoaderWindow = LoadMTSLogWindow.LoadMTSLogFileWindow(self)
        self._mtsFileLoaderWindow.show()

        return

    def do_resize_canvas(self):
        """ Resize canvas
        :return:
        """
        if self._currLogType == 'nexus':
            self.plot_nexus_log(self._currLogName)
        else:
            self.plot_mts_log(self._currLogName, reset_canvas=True)

        return

    def do_setup_uniform_slicer(self):
        """
        Set up the log value or time chopping
        :return:
        """
        # read the values
        start_time = GuiUtility.parse_float(self.ui.lineEdit_slicerStartTime)
        stop_time = GuiUtility.parse_float(self.ui.lineEdit_slicerStopTime)
        step = GuiUtility.parse_float(self.ui.lineEdit_slicerLogValueStep)

        # choice
        if self.ui.radioButton_timeSlicer.isChecked():
            # filter events by time
            # set and make time-based slicer

            status, ret_obj = self.get_controller().gen_data_slicer_by_time(self._currRunNumber,
                                                                            start_time=start_time,
                                                                            end_time=stop_time,
                                                                            time_step=step)
            if status:
                self._currSlicerKey = ret_obj
                message = 'Time slicer: from %s to %s with step %f.' % (str(start_time), str(stop_time), step)
            else:
                GuiUtility.pop_dialog_error(self, 'Failed to generate data slicer by time due to %s.'
                                                  '' % str(ret_obj))
                return

        elif self.ui.radioButton_logValueSlicer.isChecked():
            # set and make log vale-based slicer
            log_name = str(self.ui.comboBox_logNames.currentText())
            # log name might be with information
            log_name = log_name.split('(')[0].strip()
            min_log_value = GuiUtility.parse_float(self.ui.lineEdit_minSlicerLogValue)
            max_log_value = GuiUtility.parse_float(self.ui.lineEdit_maxSlicerLogValue)
            log_value_step = GuiUtility.parse_float(self.ui.lineEdit_slicerLogValueStep)
            value_change_direction = str(self.ui.comboBox_logChangeDirection.currentText())

            try:
                status, ret_obj = self.get_controller().gen_data_slicer_sample_log(self._currRunNumber,
                                                                                   log_name, log_value_step,
                                                                                   start_time, stop_time, min_log_value,
                                                                                   max_log_value,
                                                                                   value_change_direction)
                if status:
                    self._currSlicerKey = ret_obj
                else:
                    GuiUtility.pop_dialog_error(self, 'Failed to generate data slicer from sample log due to %s.'
                                                      '' % ret_obj)
            except RuntimeError as run_err:
                # run time error
                GuiUtility.pop_dialog_error(self, 'Unable to generate data slicer from sample log due to %s.'
                                                  '' % str(run_err))
                return

            message = 'Log {0} slicer: from {1} to {2} with step {3}.'.format(log_name,
                                                                              str(min_log_value),
                                                                              str(max_log_value),
                                                                              log_value_step)

        else:
            # bad coding
            raise RuntimeError('Neither time nor log value chopping is selected.')

        # set up message
        self.ui.label_slicerSetupInfo.setText(message)

        # possibly show the slicer?
        if self.ui.checkBox_showSlicer.isChecked():
            self.evt_show_slicer()

        return

    def evt_change_resolution_type(self):
        """
        event handling for changing resolution type
        :return:
        """
        if self.ui.radioButton_useTimeResolution.isChecked():
            self.ui.lineEdit_resolutionMaxPoints.setEnabled(False)
            self.ui.lineEdit_timeResolution.setEnabled(True)

        else:
            self.ui.lineEdit_resolutionMaxPoints.setEnabled(True)
            self.ui.lineEdit_timeResolution.setEnabled(False)

        return

    def evt_rewrite_manual_table(self, slicers_list):
        """

        :param slicers_list:
        :return:
        """
        # print '[DB...BAT] Input slicers', slicers_list

        if self._manualSlicerDialog is not None:
            self._manualSlicerDialog.write_table(slicers_list)

        return

    def evt_switch_slicer_method(self):
        """
        handling the change of slicing method
        :return:
        """
        # return if mutex is on to avoid nested calling for this event handling method
        if self._mutexLockSwitchSliceMethod:
            return

        # Lock
        self._mutexLockSwitchSliceMethod = True

        # Only 1 situation requires
        print '[DB...BAT] called!'
        self._set_main_slice_method()

        # Unlock
        self._mutexLockSwitchSliceMethod = False

        return

    def evt_plot_sample_log(self):
        """
        Plot sample log
        :return:
        """
        # check mutex
        if self._mutexLockLogNameComboBox:
            return

        # get current log name
        log_name = str(self.ui.comboBox_logNames.currentText())
        if self._currLogType == 'nexus':
            log_name = log_name.replace(' ', '').split('(')[0]

        # set class variables
        self._currLogName = log_name

        # plot
        if self._currLogType == 'nexus':
            # nexus log
            self.plot_nexus_log(log_name)
        else:
            # external MTS log file
            self.plot_mts_log(log_name, reset_canvas=not self.ui.checkBox_overlay.isChecked())

        return

    def evt_re_plot_mts_log(self):
        """
        MTS log set up parameters are changed. Re-plot!
        :return:
        """
        # get new set up as it is about to load different logs, then it is better to reload
        self.do_load_mts_log()

        return

    def evt_show_slicer(self):
        """
        Show or hide the set up mantid-generated slicers on the canvas
        :return:
        """
        if self.ui.checkBox_showSlicer.isChecked():
            # show the slicers
            status, ret_obj = self.get_controller().get_slicer(self._currRunNumber, self._currSlicerKey)
            if status:
                slicer_time_vec, slicer_ws_vec = ret_obj
            else:
                GuiUtility.pop_dialog_error(self, str(ret_obj))
                return
            self.ui.graphicsView_main.show_slicers(slicer_time_vec, slicer_ws_vec)

        else:
            # hide the slicers
            self.ui.graphicsView_main.remove_slicers()

        return

    def evt_quit_no_save(self):
        """
        Cancelled
        :return:
        """
        self.close()

        return

    def generate_manual_slicer(self, split_tup_list, slicer_name):
        """
        call the controller to generate an arbitrary event slicer
        :param split_tup_list:
        :param slicer_name:
        :return:
        """
        status, ret_obj = self._myParent.get_controller().gen_data_slice_manual(run_number=self._currRunNumber,
                                                                                relative_time=True,
                                                                                time_segment_list=split_tup_list,
                                                                                slice_tag=slicer_name)

        if status:
            self._currSlicerKey = ret_obj
        else:
            GuiUtility.pop_dialog_error(self, 'Failed to generate arbitrary data slicer due to {0}.'.format(ret_obj))

        return

    def get_controller(self):
        """
        Get the workflow controller
        :return:
        """
        return self._myParent.get_controller()

    def get_data_size_to_load(self):
        """
        read the frame size with unit.  convert to the
        :return: number of points to load
        """
        # block
        block_index = int(self.ui.comboBox_blockList.currentText())
        assert self._currentBlockIndex is None or block_index == self._currentBlockIndex, \
            'Block index on GUI is different from the stored value.'

        # unit
        unit = str(self.ui.comboBox_logFrameUnit.currentText())
        assert unit == self._currentFrameUnit, 'target unit %s is not same as current frame unit %s.' \
                                               '' % (unit, self._currentFrameUnit)

        # get increment value
        if unit == 'points':
            delta = int(self.ui.lineEdit_logFrameSize.text())
        elif unit == 'seconds':
            delta = float(self.ui.lineEdit_logFrameSize.text())
        else:
            raise AttributeError('Frame unit %s is not supported.' % unit)

        # get stop point
        if self._currentFrameUnit == 'seconds':
            # convert delta (second) to delta (points)
            delta_points = int(delta/self._avgFrameStep)
            assert delta_points >= 1
        else:
            # use the original value
            delta_points = delta

        return delta_points

    def load_log_names(self):
        """
        Load log names to combo box comboBox_logNames
        :return:
        """
        # get configuration
        hide_1value_log = self.ui.checkBox_hideSingleValueLog.isChecked()

        # lock event response
        self._mutexLockLogNameComboBox = True

        # clear box
        self.ui.comboBox_logNamesX.clear()
        self.ui.comboBox_logNames.clear()

        # add Time for X
        self.ui.comboBox_logNamesX.addItem('Time (second)')

        # add sample logs to combo box
        for log_name in self._logNameList:
            # check whether to add
            if hide_1value_log and log_name.count('(') > 0:
                log_size = int(log_name.split('(')[1].split(')')[0])
                if log_size == 1:
                    continue
            # add log
            self.ui.comboBox_logNamesX.addItem(log_name.split()[0])
            self.ui.comboBox_logNames.addItem(str(log_name))
        # END-FOR
        self.ui.comboBox_logNamesX.setCurrentIndex(0)
        self.ui.comboBox_logNames.setCurrentIndex(0)

        # release
        self._mutexLockLogNameComboBox = False

        return

    def load_plot_mts_log(self, reset_canvas):
        """
        Load and plot MTS log.  The log loaded and plot may the only a part of the complete log
        :param reset_canvas: if true, then reset canvas
        :return:
        """
        # get the file
        mts_log_file = str(self.ui.lineEdit_logFileName.text())

        # load MTS log file
        self._myParent.get_controller().read_mts_log(mts_log_file, self._mtsLogFormat[mts_log_file],
                                                     self._blockIndex,
                                                     self._currentStartPoint, self._currentStopPoint)

        # get the log name
        log_names = sorted(self._myParent.get_controller().get_mts_log_headers(mts_log_file))
        assert isinstance(log_names, list)
        # move Time to last position
        if 'Time' in log_names:
            log_names.remove('Time')
            log_names.append('Time')

        # lock
        self._mutexLockLogNameComboBox = True

        self.ui.comboBox_logNames.clear()
        for log_name in log_names:
            self.ui.comboBox_logNames.addItem(log_name)

        self.ui.comboBox_logNames.setCurrentIndex(0)
        curr_log_name = str(self.ui.comboBox_logNames.currentText())

        # unlock
        self._mutexLockLogNameComboBox = False

        # plot
        extra_message = 'Total data points = %d' % (
            self._mtsLogFormat[mts_log_file]['data'][self._blockIndex][1] -
            self._mtsLogFormat[mts_log_file]['data'][self._blockIndex][0])
        self.plot_mts_log(curr_log_name, reset_canvas, extra_message)

        return

    def load_run(self, run_number):
        """
        load a NeXus file by run number
        :param run_number:
        :return:
        """
        # check
        assert isinstance(run_number, int), 'Run number %s must be an integer but not %s.' % (str(run_number),
                                                                                              type(run_number))

        # set
        self.ui.lineEdit_runNumber.setText(str(run_number))

        # and load
        self.do_load_run()

        return

    def plot_mts_log(self, log_name, reset_canvas, x_axis_log='Time', extra_message=None):
        """
        :param log_name:
        :param reset_canvas:
        :param extra_message:
        :return:
        """
        # set extra message to label
        if extra_message is not None:
            self.ui.label_logFileLoadInfo.setText(extra_message)

        # check
        datatypeutility.check_string_variable('Log name (X)', x_axis_log)
        datatypeutility.check_string_variable('Log name (Y)', log_name)

        # further process
        x_axis_log = x_axis_log.split()[0]
        log_name = log_name.split()[0]

        assert isinstance(log_name, str), 'Log name %s must be a string but not %s.' \
                                          '' % (str(log_name), str(type(log_name)))

        mts_data_set = self._myParent.get_controller().get_mts_log_data(log_file_name=None,
                                                                        header_list=[x_axis_log, log_name])
        # plot a numpy series'
        try:
            vec_x = mts_data_set[x_axis_log]
            vec_y = mts_data_set[log_name]
            print (vec_x.shape, vec_y.shape)
            assert isinstance(vec_x, numpy.ndarray)
            assert isinstance(vec_y, numpy.ndarray)
        except KeyError as key_err:
            raise RuntimeError('Log name %s does not exist (%s).' % (log_name, str(key_err)))

        # clear if overlay
        if reset_canvas or self.ui.checkBox_overlay.isChecked() is False:
            self.ui.graphicsView_main.reset()

        # plot
        self.ui.graphicsView_main.plot_sample_log(vec_x, vec_y, log_name)

        return

    def plot_nexus_log(self, log_name, x_axis_log='Time'):
        """
        Plot log from NEXUX file
        Requirement:
        1. sample log name is valid;
        2. resolution is set up (time or maximum number of points)
        :param log_name:
        :return:
        """
        # check
        datatypeutility.check_string_variable('Log name (X)', x_axis_log)
        datatypeutility.check_string_variable('Log name (Y)', log_name)

        # further process
        x_axis_log = x_axis_log.split()[0]
        log_name = log_name.split()[0]

        if x_axis_log == 'Time':
            # get resolution
            use_time_res = self.ui.radioButton_useTimeResolution.isChecked()
            use_num_res = self.ui.radioButton_useMaxPointResolution.isChecked()
            if use_time_res:
                resolution = GuiUtility.parse_float(self.ui.lineEdit_timeResolution)
            elif use_num_res:
                resolution = GuiUtility.parse_float(self.ui.lineEdit_resolutionMaxPoints)
            else:
                GuiUtility.pop_dialog_error(self, 'Either time or number resolution should be selected.')
                return

            # get the sample log data
            if log_name in self._sampleLogDict[self._currRunNumber]:
                # get sample log value from previous stored
                vec_x, vec_y = self._sampleLogDict[self._currRunNumber][log_name]
            else:
                # get sample log data from driver
                vec_x, vec_y = self._myParent.get_sample_log_value(self._currRunNumber, log_name, relative=True)
                self._sampleLogDict[self._currRunNumber][log_name] = vec_x, vec_y
            # END-IF

            # get range of the data
            new_min_x = GuiUtility.parse_float(self.ui.lineEdit_minX)
            new_max_x = GuiUtility.parse_float(self.ui.lineEdit_maxX)

            # adjust the resolution
            plot_x, plot_y = self.process_data(vec_x, vec_y, use_num_res, use_time_res, resolution,
                                               new_min_x, new_max_x)

            # overlay?
            if self.ui.checkBox_overlay.isChecked() is False:
                # clear all previous lines
                self.ui.graphicsView_main.reset()

            # plot
            self.ui.graphicsView_main.plot_sample_log(plot_x, plot_y, log_name, '', 'Time (s)')

        else:
            # other solution
            # TODO - TODAY 0 - Make this correct!
            controller = self._myParent.get_controller()
            vec_times, plot_x, plot_y = controller.get_2_sample_log_values(data_key=self._currRunNumber,
                                                                           log_name_x=x_axis_log,
                                                                           log_name_y=log_name,
                                                                           start_time=None,
                                                                           stop_time=None)

            self.ui.graphicsView_main.plot_sample_log(plot_x, plot_y, plot_label='Along with time',
                                                      sample_log_name=log_name,
                                                      sample_log_name_x=x_axis_log)

            self._curr_curve_slicer = controller.create_curve_slicer_generator(vec_times, plot_x, plot_y)

        # END-IF

        return

    @staticmethod
    def process_data(vec_x, vec_y, use_number_resolution, use_time_resolution, resolution,
                     min_x, max_x):
        """
        re-process the original to plot on canvas smartly
        :param vec_x: vector of time in unit of seconds
        :param vec_y:
        :param use_number_resolution:
        :param use_time_resolution:
        :param resolution: time resolution (per second) or maximum number points allowed on canvas
        :param min_x:
        :param max_x:
        :return:
        """
        # check
        assert isinstance(vec_y, numpy.ndarray) and len(vec_y.shape) == 1
        assert isinstance(vec_x, numpy.ndarray) and len(vec_x.shape) == 1
        assert (use_number_resolution and not use_time_resolution) or \
               (not use_number_resolution and use_time_resolution), 'wrong to configure use number resolution and ...'

        # range
        if min_x is None:
            min_x = vec_x[0]
        else:
            min_x = max(vec_x[0], min_x)

        if max_x is None:
            max_x = vec_x[-1]
        else:
            max_x = min(vec_x[-1], max_x)

        index_array = numpy.searchsorted(vec_x, [min_x - 1.E-20, max_x + 1.E-20])
        i_start = index_array[0]
        i_stop = index_array[1]

        # define skip points
        if use_time_resolution:
            # time resolution
            num_target_pt = int((max_x - min_x + 0.) / resolution)
        else:
            # maximum number
            num_target_pt = int(resolution)

        num_raw_points = i_stop - i_start
        if num_raw_points < num_target_pt * 2:
            pt_skip = 1
        else:
            pt_skip = int(num_raw_points / num_target_pt)

        plot_x = vec_x[i_start:i_stop:pt_skip]
        plot_y = vec_y[i_start:i_stop:pt_skip]

        # print 'Input vec_x = ', vec_x, 'vec_y = ', vec_y, i_start, i_stop, pt_skip, len(plot_x)

        return plot_x, plot_y

    def set_ipts(self, ipts_number):
        """ Set IPTS number to text
        :param ipts_number:
        :return:
        """
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 9999999))
        self.ui.lineEdit_iptsNumber.setText('{}'.format(ipts_number))

        return

    def set_run(self, run_number):
        """
        Set run
        :return:
        """
        datatypeutility.check_int_variable('Run number set to Log Picker Window', run_number, (0, None))
        run_number = int(run_number)
        self.ui.lineEdit_runNumber.setText('%d' % run_number)

        return

    # Add slots for
    @QtCore.pyqtSlot(int)
    def signal_scanned_mts_log(self, val):
        """
        Handle signal from MTS log file window to notify that scanning MTS log file is finished.
        :param val:
        :return:
        """
        # check signal
        if val != 1:
            raise RuntimeError('Expecting signal value to be 1 but not %d.' % val)

        assert self._mtsFileLoaderWindow is not None, 'MTS file loader window is None, i.e.,' \
                                                      'it has not been launched.'

        # get data from window
        mts_log_file_name = self._mtsFileLoaderWindow.get_log_file()
        mts_log_format = self._mtsFileLoaderWindow.get_log_format()
        self._mtsLogFormat[mts_log_file_name] = mts_log_format

        # set up the GUI
        self.ui.lineEdit_logFileName.setText(mts_log_file_name)
        self.ui.comboBox_blockList.clear()
        for block_index in mts_log_format['block'].keys():
            self.ui.comboBox_blockList.addItems(str(block_index))

        return

    def smooth_sample_log_curve(self):
        print (self._curr_curve_slicer)

        self._curr_curve_slicer.smooth_curve('nearest', 1)
