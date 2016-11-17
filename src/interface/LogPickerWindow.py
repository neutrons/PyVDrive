########################################################################
#
# Window for set up log slicing splitters
#
########################################################################
import sys
import numpy

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.GuiUtility as GuiUtility
import gui.VdriveLogPicker as VdriveLogPicker
import LoadMTSLogWindow
import QuickChopDialog

OUT_PICKER = 0
IN_PICKER = 1
IN_PICKER_MOVING = 2
IN_PICKER_SELECTION = 3


class WindowLogPicker(QtGui.QMainWindow):
    """ Class for general-puposed plot window
    """
    # class
    def __init__(self, parent=None, ipts_number=None, init_run=None):
        """ Init
        """
        # call base
        QtGui.QMainWindow.__init__(self)

        # parent
        self._myParent = parent

        # set up UI
        self.ui = VdriveLogPicker.Ui_MainWindow()
        self.ui.setupUi(self)

        # Set up widgets
        self._init_widgets_setup()

        # Defining widget handling methods
        self.connect(self.ui.pushButton_selectIPTS, QtCore.SIGNAL('clicked()'),
                     self.do_select_ipts)
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_quit_no_save)
        self.connect(self.ui.pushButton_saveTimeSegs, QtCore.SIGNAL('clicked()'),
                     self.do_save_time_segments)
        self.connect(self.ui.pushButton_loadRunSampleLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_run)
        self.connect(self.ui.pushButton_prevLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_prev_log)
        self.connect(self.ui.pushButton_nextLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_next_log)
        self.connect(self.ui.pushButton_readLogFile, QtCore.SIGNAL('clicked()'),
                     self.do_scan_log_file)
        self.connect(self.ui.pushButton_loadMTSLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_mts_log)
        self.connect(self.ui.comboBox_blockList, QtCore.SIGNAL('indexChanged(int)'),
                     self.do_load_mts_log)
        self.connect(self.ui.comboBox_logFrameUnit, QtCore.SIGNAL('indexChanged(int)'),
                     self.evt_re_plot_mts_log)

        self.connect(self.ui.radioButton_useNexus, QtCore.SIGNAL('toggled(bool)'),
                     self.do_set_log_options)
        self.connect(self.ui.radioButton_useLogFile, QtCore.SIGNAL('toggled(bool)'),
                     self.do_set_log_options)

        self.connect(self.ui.checkBox_hideSingleValueLog, QtCore.SIGNAL('stateChanged(int)'),
                     self.load_log_names)

        # chopping setup
        self.connect(self.ui.radioButton_timeSlicer, QtCore.SIGNAL('toggled (bool)'),
                     self.evt_switch_slicer_method)
        self.connect(self.ui.radioButton_logValueSlicer, QtCore.SIGNAL('toggled (bool)'),
                     self.evt_switch_slicer_method)
        self.connect(self.ui.radioButton_manualSlicer, QtCore.SIGNAL('toggled (bool)'),
                     self.evt_switch_slicer_method)
        self._mutexLockSwitchSliceMethod = False

        self.connect(self.ui.pushButton_slicer, QtCore.SIGNAL('clicked()'),
                     self.do_chop)

        # Further operation
        self.connect(self.ui.pushButton_highlight, QtCore.SIGNAL('clicked()'),
                     self.do_highlight_selected)

        # automatic slicer setup
        self.connect(self.ui.pushButton_setupAutoSlicer, QtCore.SIGNAL('clicked()'),
                     self.do_setup_uniform_slicer)

        # manual slicer picker
        self.connect(self.ui.pushButton_addPicker, QtCore.SIGNAL('clicked()'),
                     self.do_picker_add)
        self.connect(self.ui.pushButton_abortPicker, QtCore.SIGNAL('clicked()'),
                     self.do_picker_abort)
        self.connect(self.ui.pushButton_setPicker, QtCore.SIGNAL('clicked()'),
                     self.do_picker_set)
        self.connect(self.ui.pushButton_selectPicker, QtCore.SIGNAL('clicked()'),
                     self.do_enter_select_picker_mode)
        self.connect(self.ui.pushButton_processPickers, QtCore.SIGNAL('clicked()'),
                     self.do_picker_process)

        # Slicer table
        self.connect(self.ui.pushButton_selectAll, QtCore.SIGNAL('clicked()'),
                     self.do_select_time_segments)
        self.connect(self.ui.pushButton_deselectAll, QtCore.SIGNAL('clicked()'),
                     self.do_deselect_time_segments)

        # Canvas
        self.connect(self.ui.pushButton_doPlotSample, QtCore.SIGNAL('clicked()'),
                     self.evt_plot_sample_log)
        self.connect(self.ui.pushButton_resizeCanvas, QtCore.SIGNAL('clicked()'),
                     self.do_resize_canvas)
        self.connect(self.ui.comboBox_logNames, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_plot_sample_log)

        self.ui.radioButton_useMaxPointResolution.toggled.connect(self.evt_change_resolution_type)
        self.connect(self.ui.radioButton_useTimeResolution, QtCore.SIGNAL('toggled(bool)'),
                     self.evt_change_resolution_type)

        self.connect(self.ui.pushButton_prevPartialLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_prev_log_frame)
        self.connect(self.ui.pushButton_nextPartialLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_next_log_frame)

        # TODO/ISSUE/51 - link Quit()

        # Event handling for pickers
        self.ui.graphicsView_main._myCanvas.mpl_connect('button_press_event',
                                                        self.on_mouse_press_event)
        self.ui.graphicsView_main._myCanvas.mpl_connect('button_release_event',
                                                        self.on_mouse_release_event)
        self.ui.graphicsView_main._myCanvas.mpl_connect('motion_notify_event',
                                                        self.on_mouse_motion)

        self._mtsFileLoaderWindow = None

        # child windows
        self._quickChopDialog = None

        # Initial setup
        if init_run is not None:
            assert isinstance(init_run, int)
            self.ui.lineEdit_runNumber.setText('%d' % init_run)
            self._iptsNumber = ipts_number
        else:
            self._iptsNumber = None

        # Class variables
        self._logNameList = list()
        self._sampleLogDict = dict()

        self._currentPickerID = None
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

    def _init_widgets_setup(self):
        """
        Initialize widgets
        :return:
        """
        # slice segments table
        self.ui.tableWidget_segments.setup()
        # ipts-run selection tree
        self.ui.treeView_iptsRun.set_main_window(self)
        # about plotting
        self.ui.checkBox_autoResize.setChecked(True)
        # options to create slicing segments
        self.ui.radioButton_noExpand.setChecked(True)
        # set up the check boxes
        self.ui.checkBox_hideSingleValueLog.setChecked(True)
        # radio buttons
        self.ui.radioButton_useNexus.setChecked(True)
        self.ui.radioButton_useLogFile.setChecked(False)

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
        self.ui.resolution_group = QtGui.QButtonGroup(self)
        self.ui.resolution_group.addButton(self.ui.radioButton_useMaxPointResolution, 0)
        self.ui.resolution_group.addButton(self.ui.radioButton_useTimeResolution, 1)

        # combo box
        self.ui.comboBox_logFrameUnit.clear()
        self.ui.comboBox_logFrameUnit.addItems(['points', 'seconds'])
        self.ui.comboBox_logFrameUnit.setCurrentIndex(0)
        # initial value for number of points on
        self.ui.lineEdit_logFrameSize.setText('5000')

        return

    def _set_main_slice_method(self):
        """
        Set the main slicer method, manual or auto
        :return:
        """
        # enable to disable
        if self.ui.radioButton_timeSlicer.isChecked():
            # time slicer
            self.ui.groupBox_sliceSetupAuto.setEnabled(True)
            self.ui.groupBox_slicerSetupManual.setEnabled(False)

            self.ui.lineEdit_minSlicerLogValue.setEnabled(False)
            self.ui.lineEdit_slicerLogValueStep.setEnabled(True)
            self.ui.lineEdit_maxSlicerLogValue.setEnabled(False)
            self.ui.comboBox_logChangeDirection.setEnabled(False)

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

        else:
            # manual slicer
            self.ui.groupBox_sliceSetupAuto.setEnabled(False)
            self.ui.groupBox_slicerSetupManual.setEnabled(True)

        return

    def do_chop(self):
        """
        Save a certain number of time segment from table tableWidget_segments
        :return:
        """
        # get the run and raw file
        raw_file_name = None
        if self.ui.radioButton_useNexus.isChecked():
            try:
                run_number = int(self.ui.lineEdit_runNumber.text())
                status, info_tup = self.get_controller().get_run_info(run_number)
                if status:
                    raw_file_name = info_tup[0]
            except ValueError as val_error:
                raise RuntimeError('Unable to find out run number')
        else:
            # TODO/ISSUE/NEXT - Find out how to generalize the current data structure for external log file
            raise NotImplementedError('Coming Soon!')

        # pop up the dialog
        self._quickChopDialog = QuickChopDialog.QuickChopDialog(self, self._currRunNumber, raw_file_name)
        result = self._quickChopDialog.exec_()

        # quit if user cancels the operation
        if result == 0:
            # cancel operation
            return
        else:
            output_dir = self._quickChopDialog.get_output_dir()
            reduce_gsas = self._quickChopDialog.to_reduce_data()

        # get chop manager
        assert isinstance(self._currSlicerKey, str), 'Slicer key %s must be a string but not %s.' \
                                                     '' % (str(self._currSlicerKey), type(self._currSlicerKey))
        status, message = self.get_controller().slice_data(run_number, self._currSlicerKey,
                                                           reduce_data=reduce_gsas,
                                                           output_dir=output_dir)

        if status:
            GuiUtility.pop_dialog_information(self, message)
        else:
            GuiUtility.pop_dialog_error(self, message)

        return

    def do_select_time_segments(self):
        """
        mark all time segments in table to be selected in the table
        :return:
        """
        num_rows = self.ui.tableWidget_segments.rowCount()
        for i_row in xrange(num_rows):
            self.ui.tableWidget_segments.select_row(i_row, True)

        return

    def do_deselect_time_segments(self):
        """
        Mark all time segments in the table to be deselected
        :return:
        """
        num_rows = self.ui.tableWidget_segments.rowCount()
        for i_row in xrange(num_rows):
            self.ui.tableWidget_segments.select_row(i_row, False)

        return

    def do_highlight_selected(self):
        """
        Highlight the selected region of the log value
        :return:
        """
        # Clear the highlight lines
        if str(self.ui.pushButton_highlight.text()) == 'Clear':
            # Delete all lines
            for highlight_id in self._myHighLightedLineList:
                self.ui.graphicsView_main.remove_line(highlight_id)

            # Reset button text
            self.ui.pushButton_highlight.setText('Highlight')
            self._myHighLightedLineList = list()

            return

        # Add highlighted lines
        # Collect selected time segments
        source_time_segments, row_number_list = \
            self.ui.tableWidget_segments.get_selected_time_segments(True)

        # Name of current sample log
        log_name = str(self.ui.comboBox_logNames.currentText()).split('(')[0].strip()

        for i in xrange(len(source_time_segments)):
            time_segment = source_time_segments[i]
            status, ret_obj = self._myParent.get_controller().get_sample_log_values(
                self._currRunNumber, log_name, time_segment[0], time_segment[1], True)
            if status is False:
                GuiUtility.pop_dialog_error(self, ret_obj)
            else:
                vec_times, vec_value = ret_obj
                highlight_id = self.ui.graphicsView_main.add_plot_1d(vec_times, vec_value, color='red', marker='.')
                self._myHighLightedLineList.append(highlight_id)
        # END-FOR

        # Reset
        self.ui.pushButton_highlight.setText('Clear')

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
        Load a run and plot
        :return:
        """
        # Get run number
        run_number = GuiUtility.parse_integer(self.ui.lineEdit_runNumber)
        if run_number is None:
            GuiUtility.pop_dialog_error('Unable to load run as value is not specified.')
            return

        # Get sample logs
        try:
            log_name_with_size = True
            self._logNameList = self._myParent.load_sample_run(run_number, log_name_with_size)
            self._logNameList.sort()

            # Update class variables, add a new entry to sample log value holder
            self._currRunNumber = run_number
            self._sampleLogDict[self._currRunNumber] = dict()

        except RuntimeError as err:
            GuiUtility.pop_dialog_error(self,
                                        'Unable to load sample logs from run %d due to %s.' % (run_number, str(err)))
            return

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
        self.ui.comboBox_logNames.clear()

        # add sample logs to combo box
        for log_name in self._logNameList:
            # check whether to add
            if hide_1value_log and log_name.count('(') > 0:
                log_size = int(log_name.split('(')[1].split(')')[0])
                if log_size == 1:
                    continue
            # add log
            self.ui.comboBox_logNames.addItem(str(log_name))
        # END-FOR
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

    def do_enter_select_picker_mode(self):
        """ Enter picker selection mode
        :return:
        """
        if self._myPickerMode == IN_PICKER_MOVING:
            GuiUtility.pop_dialog_error(self, 'Canvas is in log-picker moving mode.  '
                                              'It is not allowed to enter picker-selection mode.')
            return

        self._myPickerMode = IN_PICKER_SELECTION

        return

    def do_load_next_log(self):
        """ Load next log
        :return:
        """
        # get current index of the combo box and find out the next
        current_index = self.ui.comboBox_logNames.currentIndex()
        max_index = self.ui.comboBox_logNames.size()
        next_index = (current_index + 1) % max_index

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

    def do_quit_no_save(self):
        """
        Cancelled
        :return:
        """
        self.close()

        return

    def do_picker_abort(self):
        """
        Abort the action to add a picker
        :return:
        """
        # Guide user from enable/disable widgets
        self.ui.pushButton_addPicker.setEnabled(True)
        self.ui.pushButton_setPicker.setDisabled(True)
        self.ui.pushButton_abortPicker.setDisabled(True)
        self.ui.pushButton_selectPicker.setEnabled(True)

        # Delete the current picker
        self.ui.graphicsView_main.remove_indicator(self._currentPickerID)
        self._myPickerIDList.pop(self._currentPickerID)
        self._currentPickerID = None

        self._myPickerMode = OUT_PICKER

        return

    def do_picker_add(self):
        """
        Add picker
        :return:
        """
        # Add a picker
        indicator_id = self.ui.graphicsView_main.add_vertical_indicator(color='red')

        # Guide user
        self.ui.pushButton_setPicker.setEnabled(True)
        self.ui.pushButton_abortPicker.setEnabled(True)
        self.ui.pushButton_addPicker.setDisabled(True)
        self.ui.pushButton_deletePicker.setDisabled(True)
        self.ui.pushButton_selectPicker.setDisabled(True)

        # Change status
        self._currentPickerID = indicator_id
        self._myPickerMode = IN_PICKER
        self._myPickerIDList.append(indicator_id)

        return

    def do_picker_process(self):
        """
        Process pickers by sorting and fill the stop time
        :return:
        """
        # Deselect all rows
        num_rows = self.ui.tableWidget_segments.rowCount()
        for i_row in xrange(num_rows):
            self.ui.tableWidget_segments.select_row(i_row, False)

        # Sort by start time
        self.ui.tableWidget_segments.sort_by_start_time()

        # Fill the stop by time by next star time
        self.ui.tableWidget_segments.fill_stop_time()

        return

    def do_picker_set(self):
        """
        Add the (open) picker to list
        :return:
        """
        # Fix the current picker
        x, x = self.ui.graphicsView_main.get_indicator_position(self._currentPickerID)
        current_time = x

        # Change the color
        self.ui.graphicsView_main.update_indicator(self._currentPickerID, color='black')

        # Guide user
        self.ui.pushButton_abortPicker.setDisabled(True)
        self.ui.pushButton_addPicker.setEnabled(True)
        self.ui.pushButton_deletePicker.setEnabled(True)
        self.ui.pushButton_setPicker.setDisabled(True)
        self.ui.pushButton_selectPicker.setEnabled(True)

        # Change status
        self._myPickerMode = OUT_PICKER
        self._currentPickerID = None

        # Set to table
        self.ui.tableWidget_segments.append_start_time(current_time)

        return

    def do_save_time_segments(self):
        """ Save selected segment
        :return:
        """
        # Get splitters
        try:
            split_tup_list = self.ui.tableWidget_segments.get_splitter_list()
        except RuntimeError as e:
            GuiUtility.pop_dialog_error(self, str(e))
            return

        # pop a dialog for the name of the slicer
        slicer_name, status = QtGui.QInputDialog.getText(self, 'Input Slicer Name', 'Enter slicer name:')
        # return if not given
        if status is False:
            return
        else:
            slicer_name = str(slicer_name)
            print '[DB...BAT] Slicer name: ', slicer_name

        # Call parent method
        if self._myParent is not None:
            self._myParent.get_controller().gen_data_slice_manual(run_number=self._currRunNumber,
                                                                  relative_time=True,
                                                                  time_segment_list=split_tup_list,
                                                                  slice_tag=slicer_name)
        # END-IF

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

    def do_select_ipts(self):
        """
        :return:
        """
        import AddRunsIPTS as IptsDialog

        # Launch window
        child_window = IptsDialog.AddRunsByIPTSDialog(self)

        # init set up
        if self._iptsNumber is not None:
            child_window.set_ipts_number(self._addedIPTSNumber)

        child_window.set_data_root_dir(self._myParent.get_controller().get_data_root_directory())
        r = child_window.exec_()

        # set the close one
        ipts_run_number = child_window.get_ipts_number()

        print ipts_run_number
        print type(ipts_run_number)

        return

    def do_set_log_options(self):
        """
        Get the different options for set log
        :return:
        """
        if self.ui.radioButton_useNexus.isChecked():
            # enable to load run from Nexus/standard Vulcan run
            self.ui.pushButton_loadRunSampleLog.setEnabled(True)
            self.ui.pushButton_readLogFile.setEnabled(False)

        elif self.ui.radioButton_useLogFile.isChecked():
            # enable to load Vulcan sample environment log file
            self.ui.pushButton_loadRunSampleLog.setEnabled(False)
            self.ui.pushButton_readLogFile.setEnabled(True)

        else:
            # false set up
            raise RuntimeError('Error setup to have both radio button (Nexus/log file) disabled.')

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
            # set and make time-based slicer
            self._currSlicerKey = self.get_controller().gen_data_slicer_by_time(self._currRunNumber, start_time,
                                                                                step, stop_time)

            message = 'Time slicer: from %s to %s with step %f.' % (str(start_time), str(stop_time), step)

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

            message = 'Log %s slicer: from %s to %s with step %.3f.' % (log_name, str(min_log_value),
                                                                      str(max_log_value), log_value_step)

        else:
            # bad coding
            raise RuntimeError('Neither time nor log value chopping is selected.')

        # set up message
        self.ui.label_slicerSetupInfo.setText(message)

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

    def evt_switch_slicer_method(self):
        """

        :return:
        """
        # TODO/ISSUE/NOW: doc

        if self._mutexLockSwitchSliceMethod:
            return

        # Lock
        self._mutexLockSwitchSliceMethod = True

        # Only 1 situation requires

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

    def plot_mts_log(self, log_name, reset_canvas, extra_message=None):
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
        assert isinstance(log_name, str), 'Log name %s must be a string but not %s.' \
                                          '' % (str(log_name), str(type(log_name)))

        mts_data_set = self._myParent.get_controller().get_mts_log_data(log_file_name=None,
                                                                        header_list=['Time', log_name])
        # plot a numpy series'
        try:
            vec_x = mts_data_set['Time']
            vec_y = mts_data_set[log_name]
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

    def plot_nexus_log(self, log_name):
        """
        Plot log from NEXUX file
        Requirement:
        1. sample log name is valid;
        2. resolution is set up (time or maximum number of points)
        :param log_name:
        :return:
        """
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
        self.ui.graphicsView_main.plot_sample_log(plot_x, plot_y, log_name)

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

    def highlight_picker(self, picker_id, flag, color='red'):
        """
        Highlight (by changing color) of the picker selected
        :param picker_id:
        :return:
        """
        if flag is False:
            if picker_id is None:
                for pid in self._myPickerIDList:
                    self.ui.graphicsView_main.update_indicator(pid, 'black')
            else:
                self.ui.graphicsView_main.update_indicator(picker_id, 'black')
        else:
            for pid in self._myPickerIDList:
                if pid == picker_id:
                    self.ui.graphicsView_main.update_indicator(pid, color)
                else:
                    self.ui.graphicsView_main.update_indicator(pid, 'black')
            # END-FOR
        # END-IF-ELSE

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

    def locate_picker(self, x_pos, ratio=0.2):
        """ Locate a picker with the new x
        :param x_pos:
        :param ratio:
        :return: 2-tuple (Boolean, Object)
        """
        # Check
        if len(self._myPickerIDList) == 0:
            return False, 'No picker to select!'

        assert isinstance(ratio, float)
        assert (ratio > 0.01) and (ratio <= 0.5)

        x_lim = self.ui.graphicsView_main.getXLimit()

        # Get the vector of x positions of indicator and
        vec_pos = [x_lim[0]]
        for ind_id in self._myPickerIDList:
            picker_x, picker_y = self.ui.graphicsView_main.get_indicator_position(ind_id)
            vec_pos.append(picker_x)
        # END-FOR
        vec_pos.append(x_lim[1])
        sorted_vec_pos = sorted(vec_pos)

        # Search
        post_index = numpy.searchsorted(sorted_vec_pos, x_pos)
        if post_index == 0:
            return False, 'Position %f is out of canvas left boundary %f. It is weird!' % (x_pos, vec_pos[0])
        elif post_index >= len(vec_pos):
            return False, 'Position %f is out of canvas right boundary %f. It is weird!' % (x_pos, vec_pos[-1])

        pre_index = post_index - 1
        dx = sorted_vec_pos[post_index] - sorted_vec_pos[pre_index]
        return_index = -1
        if sorted_vec_pos[pre_index] <= x_pos <= sorted_vec_pos[pre_index] + dx * ratio:
            return_index = pre_index
        elif sorted_vec_pos[post_index] - dx * ratio <= x_pos <= sorted_vec_pos[post_index]:
            return_index = post_index
        if return_index >= 0:
            nearest_picker_x = sorted_vec_pos[return_index]
            raw_index = vec_pos.index(nearest_picker_x)
        else:
            raw_index = return_index

        # correct for index=0 is boundary
        raw_index -= 1

        return raw_index

    def menu_select_nearest_picker(self):
        """ Select nearest picker
        :return:
        """
        # Get all the pickers' position
        picker_pos_list = self.ui.tableWidget_segments.get_start_times()

        # Find the nearest picker
        picker_pos_list.append(self._currMousePosX)
        picker_pos_list.sort()
        index = picker_pos_list.index(self._currMousePosX)

        prev_index = index - 1
        next_index = index + 1

        select_picker_pos = picker_pos_list[prev_index]

        if next_index < len(picker_pos_list) and \
            abs(picker_pos_list[next_index] - self._currMousePosX) < \
                        abs(picker_pos_list[prev_index] - self._currMousePosX):
            select_picker_pos = picker_pos_list[next_index]

        # Add the information to graphics
        self._currentPickerID = self.ui.graphicsView_main.get_indicator_key(select_picker_pos, None)
        self._myPickerMode = IN_PICKER_MOVING

        return

    def menu_quit_picker_selection(self):
        """ Quit picker-selecion mode
        :return:
        """
        print 'Cancel picker selection'
        self._myPickerMode = OUT_PICKER

        return

    def on_mouse_press_event(self, event):
        """ If in the picking up mode, as mouse's left button is pressed down,
        the indicator/picker
        is in the moving mode

        event.button has 3 values:
         1: left
         2: middle
         3: right
        and double click event is a subcategory to press_event
        """
        # Get event data
        x = event.xdata
        y = event.ydata
        button = event.button
        print "[DB] Button %d is (pressed) down at (%s, %s)." % (button, str(x), str(y))
        if event.dblclick:
            print '[DB... double click (press)] ', event.dblclick, type(event.dblclick)

        # Select situation
        if x is None or y is None:
            # mouse is out of canvas, return
            return

        if button == 1:
            # left button
            if self._myPickerMode == IN_PICKER:
                # allowed status to in picker-moving status
                self._myPickerMode = IN_PICKER_MOVING

        return

    def on_mouse_release_event(self, event):
        """ If the left button is released and prevoiusly in IN_PICKER_MOVING mode,
        then the mode is over

        Note: double click (event.dblclick) does not correspond to any mouse release event

        """
        button = event.button

        self._currMousePosX = event.xdata
        self._currMousePosY = event.ydata

        if button == 1:
            if self._myPickerMode == IN_PICKER_MOVING:
                self._myPickerMode = IN_PICKER

        elif button == 3:
            if self._myPickerMode == IN_PICKER_SELECTION:
                # Pop-out menu
                self.ui.menu = QtGui.QMenu(self)

                action1 = QtGui.QAction('Select', self)
                action1.triggered.connect(self.menu_select_nearest_picker)
                self.ui.menu.addAction(action1)

                action2 = QtGui.QAction('Cancel', self)
                action2.triggered.connect(self.menu_quit_picker_selection)
                self.ui.menu.addAction(action2)

                # add other required actions
                self.ui.menu.popup(QtGui.QCursor.pos())

        return

    def on_mouse_motion(self, event):
        """ Event handling in case mouse is moving
        """
        new_x = event.xdata
        new_y = event.ydata

        # Outside of canvas, no response
        if (new_x is None) or (new_y is None):
            return

        # Calculate the relative displacement
        dx = new_x - self._currMousePosX
        dy = new_y - self._currMousePosY

        x_min, x_max = self.ui.graphicsView_main.getXLimit()
        mouse_resolution_x = (x_max - x_min) * 0.001
        y_min, y_max = self.ui.graphicsView_main.getYLimit()
        mouse_resolution_y = (y_max - y_min) * 0.001

        if self._myPickerMode == IN_PICKER_MOVING:
            # Respond to motion of mouse and move the indicator
            if abs(dx) > mouse_resolution_x or abs(dy) > mouse_resolution_y:
                # it is considered that the mouse is moved
                self._currMousePosX = new_x
                self._currMousePosY = new_y
                # self.ui.graphicsView_main.move_indicator(self._currentPickerID, dx, dy)

                self.ui.graphicsView_main.set_indicator_position(self._currentPickerID, new_x, new_y)
            # END-IF(dx, dy)

        elif self._myPickerMode == IN_PICKER_SELECTION:
            # Highlight (change color) a picker and set the picker/indicator in active mode
            if abs(dx) > mouse_resolution_x:
                # Consider the picker by time only
                picker_list_index = self.locate_picker(x_pos=new_x, ratio=0.2)
                """
                if picker_list_index == -2:
                    pass
                    # print 'Middle of nowhere'
                elif picker_list_index == -1:
                    pass
                    # print 'Left boundary'
                elif picker_list_index == len(self._myPickerIDList):
                    pass
                    # print 'Right boundary'
                else:
                    pass
                    # print 'Pick indicator %d of %d' % (picker_list_index, len(self._myPickerIDList))
                """
                self.highlight_picker(picker_id=None, flag=False)
                if 0 <= picker_list_index < len(self._myPickerIDList):
                    picker_id = self._myPickerIDList[picker_list_index]
                    self.highlight_picker(picker_id, True)
            # END-IF

        # END-IF (PickerMode)

        return

    def set_run(self, run_number):
        """
        Set run
        :return:
        """
        run_number = int(run_number)
        self.ui.lineEdit_runNumber.setText('%d' % run_number)

        return

    def setup(self):
        """ Set up from parent main window
        :return:
        """
        # TODO/FIXME/NOW - How to make this work?
        # ipts_run_dict = self._myParent.get_archived_runs()
        #
        # # Set to tree
        # for ipts in ipts_run_dict.keys():
        #     run_list = ipts_run_dict[ipts]
        #     self.ui.treeView_iptsRun.add_ipts_runs(ipts, run_list)

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


def testmain(argv):
    """ Main method for testing purpose
    """
    parent = None

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = WindowLogPicker(parent)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return

if __name__ == "__main__":
    testmain(sys.argv)
