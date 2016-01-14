#!/usr/bin/python
__author__ = 'wzz'

# import utility modules
import sys
import os

# import PyQt modules
from PyQt4 import QtGui, QtCore, Qt

# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

""" import GUI components generated from Qt Designer .ui file """
sys.path.append('//home/wzz/Projects/PyVDrive/PyVDrive/')
import PyVDrive
import PyVDrive.ui.gui.VdriveMain as mainUi
import PyVDrive.ui.GuiUtility as guiutil
import PyVDrive.ui.snapgraphicsview as spview
import PyVDrive.ui.ReducedDataView as data_view
import PyVDrive.ui.PeakPickWindow as PeakPickWindow

""" import PyVDrive library """
import PyVDrive.VDriveAPI as vdrive

import PyVDrive.ui.AddRunsIPTS as dlgrun
import PyVDrive.ui.Window_LogPicker as LogPicker
import PyVDrive.ui.LogSnapView as dlgSnap

# Define enumerate
ACTIVE_SLICER_TIME = 0
ACTIVE_SLICER_LOG = 1
ACTIVE_SLICER_MANUAL = 2


class VDrivePlotBeta(QtGui.QMainWindow):
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
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle('VDrivePlot (Beta)')
        self.ui = mainUi.Ui_MainWindow()
        self.ui.setupUi(self)

        # Define status variables
        # new work flow
        self._myWorkflow = vdrive.VDriveAPI('VULCAN')
        self._numSnapViews = 6

        # Initialize widgets
        self._init_widgets()

        # Define event handling
        self.connect(self.ui.pushButton_selectIPTS, QtCore.SIGNAL('clicked()'),
                     self.do_add_runs_by_ipts)
        self.connect(self.ui.pushButton_readSampleLogFile, QtCore.SIGNAL('clicked()'),
                     self.do_read_sample_log_file)

        # Column 2
        # about vanadium calibration
        self.connect(self.ui.pushButton_loadCalFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_calibration)
        self.connect(self.ui.pushButton_showCalDetails, QtCore.SIGNAL('clicked()'),
                     self.do_show_calibration_map)

        # select and set runs from run-info-tree
        self.connect(self.ui.pushButton_addRunsToReduce, QtCore.SIGNAL('clicked()'),
                     self.do_add_runs_to_reduce)
        self.connect(self.ui.checkBox_selectRuns, QtCore.SIGNAL('stateChanged(int)'),
                     self.do_update_selected_runs)
        self.connect(self.ui.pushButton_deleteRuns, QtCore.SIGNAL('clicked()'),
                     self.do_remove_runs_from_reduction)
        self.connect(self.ui.pushButton_sortSelectedRuns, QtCore.SIGNAL('clicked()'),
                     self.do_sort_selected_runs)

        self.connect(self.ui.checkBox_chopRun, QtCore.SIGNAL('stateChanged(int)'),
                     self.evt_chop_run_state_change)
        self.connect(self.ui.pushButton_manualPicker, QtCore.SIGNAL('clicked()'),
                     self.pop_manual_picker)

        # Column 3
        # Tab-1
        # sub-tab-1
        self.connect(self.ui.pushButton_loadTimeSegmentsFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_time_seg_file)
        self.connect(self.ui.pushButton_chopData, QtCore.SIGNAL('clicked()'),
                     self.do_slice_data_by_time)

        # sub-tab-2
        self.connect(self.ui.pushButton_applyManual, QtCore.SIGNAL('clicked()'),
                     self.do_apply_manual_slicer)
        self.connect(self.ui.pushButton_applyLog, QtCore.SIGNAL('clicked()'),
                     self.do_apply_log_slicer)
        self.connect(self.ui.pushButton_saveSlicer, QtCore.SIGNAL('clicked()'),
                     self.do_save_log_slicer)

        # Tab-2
        self.connect(self.ui.pushButton_binData, QtCore.SIGNAL('clicked()'),
                     self.do_bin_data)

        # Tab-3: view reduction result
        self.connect(self.ui.pushButton_viewReducedData, QtCore.SIGNAL('clicked()'),
                     self.do_view_reduction)

        # Tab-4: fig single peak
        self.connect(self.ui.pushButton_fitSinglePeak, QtCore.SIGNAL('clicked()'),
                     self.do_fit_single_peak)

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
            self.connect(combo_box, QtCore.SIGNAL('currentIndexChanged(int)'),
                         self.do_change_log_snap_view)

        # Event handling for menu
        self.connect(self.ui.actionSave_Project, QtCore.SIGNAL('triggered()'),
                     self.menu_save_session)
        self.connect(self.ui.actionSave_Project_As, QtCore.SIGNAL('triggered()'),
                     self.menu_save_session_as)
        self.connect(self.ui.actionOpen_Project, QtCore.SIGNAL('triggered()'),
                     self.menu_load_session)

        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'),
                     self.evt_quit)

        # Group widgets
        self._groupedSnapViewList = list()
        self._setup_snap_view_groups(self._numSnapViews)

        # Sub windows
        # controls to the sub windows
        self._openSubWindows = []
        self._manualPikerWindow = None
        self._snapViewWindow = None

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

        # Load settings
        self.load_settings()

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
                self._currSlicerLogName = spview.SampleLogView(
                    self._groupedSnapViewList[i_radio], self).get_log_name()
                found = True
                print '[DB] VDrivePlot: snap view for radio button %d is selected.' % i_radio
                break

        if found is False:
            guiutil.pop_dialog_error('Unable to locate any sample log to be picked up.')


        # self._apply_slicer_snap_view() : disabled because there is no need to do this

        return

    def do_apply_manual_slicer(self):
        """ Pick up (time) slicing information and show it by indicating lines in snap view
        :return:
        """
        self._myWorkflow.set_slicer('Manual')

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
        # Process data slicers
        if self.ui.checkBox_chopRun.isChecked():
            raise NotImplementedError('Binning data with option to chop will be solved later!')

        # Collect information for reduction
        # binning parameter
        if self.ui.radioButton_binStandard.isChecked():
            # default
            bin_par = None
        elif self.ui.radioButton_binCustomized.isChecked():
            # customized bin parameters
            bin_width = guiutil.parse_float(self.ui.lineEdit_binWidth)
            min_tof = guiutil.parse_float(self.ui.lineEdit_binMinTOF)
            max_tof = guiutil.parse_float(self.ui.lineEdit_binMaxTOF)
            bin_par = (min_tof, bin_width, max_tof)
        else:
            # violate requirements
            guiutil.pop_dialog_error(self, '')
            return

        # bin over pixel
        if self.ui.checkBox_overPixel.isChecked():
            # binning pixel
            bin_pixel_direction = ''
            if self.ui.radioButton_binVerticalPixels.isChecked():
                bin_pixel_size = guiutil.parse_integer(self.ui.lineEdit_pixelSizeVertical)
                bin_pixel_direction = 'vertical'
            elif self.ui.radioButton_binHorizontalPixels.isChecked():
                bin_pixel_size = guiutil.parse_integer(self.ui.lineEdit_pixelSizeHorizontal)
                bin_pixel_direction = 'horizontal'
            else:
                guiutil.pop_dialog_error(self, 'Neither of 2 radio buttons is selected.')
                return
            raise NotImplementedError('Will be implemented in #32.')
        # END-IF-ELSE

        # Other parameters
        do_subtract_bkgd = self.ui.checkBox_reduceSubtractBackground.isChecked()
        do_normalize_by_vanadium = self.ui.checkBox_reduceNormalizedByVanadium.isChecked()
        do_substract_special_pattern = self.ui.checkBox_reduceSubstractSpecialPattern.isChecked()
        do_write_fullprof = self.ui.checkBox_outFullprof.isChecked()
        do_write_gsas = self.ui.checkBox_outGSAS.isChecked()

        # Reduce data
        # retrieve the runs to reduce
        run_number_list = self.ui.tableWidget_selectedRuns.get_selected_runs()
        if len(run_number_list) == 0:
            guiutil.pop_dialog_error(self, 'No run is selected in run number table.')
        status, error_message = self._myWorkflow.set_runs_to_reduce(run_numbers=run_number_list)
        if status is False:
            guiutil.pop_dialog_error(self, error_message)

        status, ret_obj = self._myWorkflow.reduce_data_set()
        if status is False:
            error_msg = ret_obj
            guiutil.pop_dialog_error(self, error_msg)

        # Show message to notify user that the reduction is complete
        guiutil.pop_dialog_information(self, 'Reduction is complete.')
        # switch the tab to 'VIEW'
        self.ui.tabWidget_reduceData.setCurrentIndex(2)

        return

    def do_update_selected_runs(self):
        """
        # TODO/FIXME/
        :return:
        """
        curr_state = self.ui.checkBox_selectRuns.isChecked()

        self.ui.tableWidget_selectedRuns.select_all_rows(curr_state)

        return

    def do_view_reduction(self):
        """
        Purpose: Launch reduction view
        Requirements: ... ...
        Guarantees: ... ...
        :return:
        """
        # TODO/NOW/1st complete it!

        # Launch data view and set up
        self._reducedDataViewWindow = data_view.GeneralPurposedDataViewWindow(self)
        self._reducedDataViewWindow.setup(self._myWorkflow)
        # set up more parameters such as unit ...
        # ... ...

        """ TODO/NOW/ Add methods to set up to plot window
        radioButton_viewInTOF
        radioButton_viewInD
        radioButton_viewInQ

        lineEdit_minX
        lineEdit_maxX

        checkBox_normaliseCurrent
        checkBox_normaliseByVanadium
        checkBox_logScaleIntensity
        """

        self._reducedDataViewWindow.show()

        # TODO/FIXME/NOW/1st register the window for closing procedure!

        return

    def do_remove_runs_from_reduction(self):
        """
        TODO/FIXME
        :return:
        """
        # get run to delete
        try:
            remove_run = guiutil.parse_integer(self.ui.lineEdit_runsToDelete)
        except ValueError as ve:
            guiutil.pop_dialog_error(str(ve))
            return

        # determine the rows for the runs to delete
        if remove_run is not None:
            row_number_list = self.ui.tableWidget_selectedRuns.get_rows_by_run([remove_run])
            # check
            if row_number_list[0] < 0:
                guiutil.pop_dialog_error(self, 'Run number %d is not in the selected runs.' % remove_run)
                return
            else:
                self.ui.lineEdit_runsToDelete.setText('')
        else:
            row_number_list = self.ui.tableWidget_selectedRuns.get_selected_rows()
            if len(row_number_list) == 0:
                guiutil.pop_dialog_error(self, 'There is no run selected to delete.')
                return

        # delete
        self.ui.tableWidget_selectedRuns.remove_rows(row_number_list)

        return

    def do_slice_data_by_time(self):
        """ Event handler to slice/chop data by time
        :return:
        """
        # Check selected run numbers
        selected_run_list = self.ui.tableWidget_selectedRuns.get_selected_runs()
        print '[DB] Slice data by time: runs to chop = %s' % str(selected_run_list)

        do_connect_runs = self.ui.checkBox_chopContinueRun.isChecked()

        # Check radio button to generate relative-time slicer
        if self.ui.radioButton_chopContantDeltaT.isChecked() is True:
            # chop data by standard runs
            start_time = guiutil.parse_float(self.ui.lineEdit_chopTimeSegStartTime)
            time_interval = guiutil.parse_float(self.ui.lineEdit_chopTimeSegInterval)
            stop_time = guiutil.parse_float(self.ui.lineEdit_chopTimeSegStopTime)

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
                    guiutil.pop_dialog_error(err_msg)

        elif self.ui.radioButton_chopByTimeSegments.isChecked() is True:
            # chop with user-defined time segment
            raise RuntimeError('IMPLEMENT IMPORTING TIME SEGMENT FILE ASAP')

        else:
            # Impossible status
            guiutil.pop_dialog_error(self, 'User must choose one radio button.')
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
                QtGui.QFileDialog.getSaveFileName(self, 'Data Slice File',
                                                  self._myWorkflow.get_working_dir()))

        print '[DB] Save slicer for run ', self._currLogRunNumber, ' sample log ', self._currSlicerLogName,
        print 'to file', out_file_name
        # Save slicer for run  57325  sample log  Voltage

        if self._currSlicerLogName is None:
            guiutil.pop_dialog_error(self, 'Neither log-value slicer nor manual slicer is applied.')
            return
        else:
            # Save splitters workspace
            if self._currSlicerLogName == '__manual__':
                raise NotImplementedError('ASAP')
            else:
                # save splitters from log
                status, err_msg = self._myWorkflow.save_splitter_workspace(
                    self._currLogRunNumber, self._currSlicerLogName, out_file_name)
                if status is False:
                    guiutil.pop_dialog_error(self, err_msg)

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
        '''
        # IPTS and run tree view
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'IPTS')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Run')
        self.ui.treeView_iptsRun.setModel(model)
        self.ui.treeView_iptsRun.setColumnWidth(0, 90)
        self.ui.treeView_iptsRun.setColumnWidth(1, 60)
        self.ui.treeView_iptsRun.setDragEnabled(True)
        '''

        # Selecting runs
        # NEXT/TODO/FIXME
        self.ui.tableWidget_selectedRuns.setup()
        self.ui.tableWidget_timeSegment.setup()

        self.ui.treeView_iptsRun.set_main_window(self)

        # Chopping
        self.ui.checkBox_chopRun.setCheckState(QtCore.Qt.Unchecked)
        self.ui.tabWidget_reduceData.setCurrentIndex(1)
        self.ui.tabWidget_reduceData.setTabEnabled(0, False)

        # Reduction
        self.ui.radioButton_binStandard.setChecked(True)

        # View
        self.ui.radioButton_viewInTOF.setChecked(True)
        self.ui.radioButton_plotData1D.setChecked(True)

        # Plotting log
        self.ui.checkBox_logSkipSec.setCheckState(QtCore.Qt.Checked)
        self.ui.lineEdit_numSecLogSkip.setText('1')

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
                assert isinstance(radio_button, QtGui.QRadioButton)
            except AttributeError as e:
                raise RuntimeError('GUI changed but python code is not changed accordingly: %s'%(str(e)))
            else:
                # set up group
                graph_group = spview.SnapGraphicsView(graph_view, combo1, combo2, radio_button)
                self._groupedSnapViewList.append(graph_group)
        # END_FOR(i)

        return

    def do_add_runs_by_ipts(self):
        """ import runs by IPTS number or directory
        Purpose: Import runs from archive according to IPTS or specified data directory
        Guarantees: launch a window and get user inputs from the dialog
        :return: None
        """
        # Launch window
        child_window = dlgrun.AddRunsByIPTSDialog(self)
        child_window.set_data_root_dir(self._myWorkflow.get_data_root_directory())
        r = child_window.exec_()

        # Return due to 'cancel'
        ipts_dir = child_window.get_ipts_dir()
        if ipts_dir is None:
            return

        # Get IPTS from dialog and set to archive
        ipts_number = child_window.get_ipts_number()
        if ipts_number is None:
            status, ret_obj = self._myWorkflow.get_ipts_number_from_dir(ipts_dir)
            if status is False:
                message = 'Unable to get IPTS number due to %s. Using user directory.' % ret_obj
                guiutil.pop_dialog_error(self, message)
                ipts_number = 0
            else:
                ipts_number = ret_obj
        self._myWorkflow.set_ipts(ipts_number)

        begin_date, end_date, begin_run, end_run = child_window.get_date_run_range()
        print '[DB-BAT] Dialog gives out %s, %s, %s, %s' % (str(begin_date), str(end_date),
                                                            str(begin_run), str(end_run))
        in_archive = child_window.scan_data_skipped()

        # Get a list of runs including run numbers and data file paths.
        if in_archive:
            status, ret_obj = self._myWorkflow.get_ipts_info(ipts_number, begin_run, end_run)
        else:
            status, ret_obj = self._myWorkflow.get_ipts_info(ipts_dir, begin_run, end_run)
        if status is True:
            run_tup_list = ret_obj
        else:
            # Pop error
            error_message = ret_obj
            guiutil.pop_dialog_error(self, error_message)
            return

        # FIXME/TODO/1st - THIS SHOULD BE REFACTORED INTO VdriveAPI
        # raise NotImplementedError('vdrive.filter_runs_by_date() won\'t work!')
        # Filter by time if it is specified
        if begin_date is not None and end_date is not None:
            # Filter runs by date
            status, ret_obj = vdrive.filter_runs_by_date(run_tup_list, begin_date, end_date,
                                                         include_end_date=True)
            if status is True:
                run_tup_list = ret_obj
            else:
                #  pop error
                error_message = ret_obj
                guiutil.pop_dialog_error(self, error_message)
                return
        elif begin_date is not None or end_date is not None:
            # Unsupported scenario
            raise RuntimeError('Unable to handle the case that only begin date or end date is specified.')

        # Add runs to workflow
        status, error_message = self._myWorkflow.add_runs(run_tup_list, ipts_number)
        if status is False:
            guiutil.pop_dialog_error(self, error_message)
            return

        # Filter runs by run
        """
        status, ret_obj = vdrive.filter_runs_by_run(run_tup_list, begin_run, end_run)
        if status is False:
            guiutil.pop_dialog_error(ret_obj)
            return
        else:
            run_tup_list = ret_obj

        status, error_message = self._myWorkflow.add_runs(run_tup_list, ipts_number)
        if status is False:
            guiutil.pop_dialog_error(self, error_message)
            return
        """

        # Set to tree
        if ipts_number == 0:
            ipts_number = os.path.basename(ipts_dir)
        self.ui.treeView_iptsRun.add_ipts_runs(ipts_number, run_tup_list)

        # Set to file tree directory
        if ipts_number > 0:
            home_dir = '/SNS/VULCAN'
        else:
            home_dir = os.path.expanduser('~')
        curr_dir = ipts_dir
        self.ui.treeView_runFiles.set_root_path(home_dir)
        self.ui.treeView_runFiles.set_current_path(curr_dir)

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
                guiutil.pop_dialog_error(self, error_message)
                return

        elif self.ui.radioButton_runsAddPartial.isChecked():
            # case to add a subset of runs
            start_run = guiutil.parse_integer(self.ui.lineEdit_runFirst)
            end_run = guiutil.parse_integer(self.ui.lineEdit_runLast)

            # switch start run and end run if user specifies in wrong order
            if start_run > end_run:
                temp = start_run
                start_run = end_run
                end_run = temp
                self.ui.lineEdit_runFirst.setText(str(start_run))
                self.ui.lineEdit_runLast.setText(str(end_run))

            # get subset of runs
            status, ret_obj = self._myWorkflow.get_runs(start_run, end_run)
            if status is True:
                run_list = ret_obj
                self.ui.tableWidget_selectedRuns.append_runs(run_list)
            else:
                # Error and return
                error_message = ret_obj
                guiutil.pop_dialog_error(error_message)
                return

            if len(run_list) == 0:
                error_message = 'No available run can be found between %d and %d ' \
                                'for this project.' % (start_run, end_run)
                guiutil.pop_dialog_error(self, error_message)
        else:
            guiutil.pop_dialog_error(self, 'Neither of 2 radio buttons is selected.')
            return

        # Add all runs to table
        self.ui.tableWidget_selectedRuns.append_runs(run_list)

        return

    def do_change_log_snap_view(self):
        """
        Event handling if user chooses to plot another log in snap view
        :return:
        """
        num_skip_second = guiutil.parse_float(self.ui.lineEdit_numSecLogSkip)

        for i in xrange(len(self._group_left_box_list)):
            curr_index = int(self._group_left_box_list[i].currentIndex())
            if curr_index < 0:
                # skip if it is not set!
                continue
            if curr_index != self._group_left_box_values[i]:
                self._group_left_box_values[i] = curr_index
                print '[DB] Left box No. %d log index is changed to %d' % (i, curr_index)
                spview.SampleLogView(self._groupedSnapViewList[i], self).plot_sample_log(num_skip_second)
                break

        return

    def do_fit_single_peak(self):
        """ Collect parameters and launch Peak-picker window
        :return:
        """
        # TODO/NOW/1st collect parameters' values to set up the peak-picker window
        self._peakPickerWindow = PeakPickWindow.PeakPickerWindow(self)
        self._peakPickerWindow.set_controller(self._myWorkflow)
        self._peakPickerWindow.show()

        return

    def do_load_calibration(self):
        """
        Purpose:
            Select and check vanadium calibration file for the current runs
        Requirements:
            Some runs are light-loaded to project
        Guarantee:
            Load calibration...

        Nomenclature:
        1. light-loaded: a run that is said to be loaded to project, but NOT loaded by Mantid.
        :return:
        """
        # TODO/NEXT/NOW
        raise NotImplementedError('ASAP')

        # Get calibration file
        if os.path.exists(self._calibCriteriaFile) is False:
            self._calibCriteriaFile = str(
                QtGui.QFileDialog.getOpenFileName(self, 'Get Vanadium Criteria', '/SNS/VULCAN/')
            )
            if self._calibCriteriaFile is None or len(self._calibCriteriaFile) == 0:
                return

        # Launch second dialog to select the criteria from table
        import ui.Dialog_SetupVanCalibrationRules as vanSetup
        setupdialog = vanSetup.SetupVanCalibRuleDialog(self)
        setupdialog.exec_()

        return

    def do_load_time_seg_file(self):
        """
        Load time segment file
        :return:
        """
        # Get file name
        file_filter = "CSV (*.csv);;Text (*.txt);;All files (*.*)"
        log_path = self._myWorkflow.get_working_dir()
        seg_file_name = str(QtGui.QFileDialog.getOpenFileName(
            self, 'Open Time Segment File', log_path, file_filter))
        print '[DB-BAR] Importing time segment file: %s' % seg_file_name

        # Import file
        status, ret_obj = vdrive.parse_time_segment_file(seg_file_name)
        if status is False:
            err_msg = ret_obj
            guiutil.pop_dialog_error(self, err_msg)
            return
        else:
            ref_run, run_start, time_seg_list = ret_obj

        # Set to table
        self.ui.tableWidget_timeSegment.remove_all_rows()
        self.ui.tableWidget_timeSegment.set_segments(time_seg_list)

        return

    def do_read_sample_log_file(self):
        """ Load nexus file for plotting sample log.
        The file should be selected from runs in the tree
        :return:
        """
        # Get the default file path
        log_path = self._myWorkflow.get_data_root_directory()

        # If
        status, ret_obj = self.ui.treeView_iptsRun.get_current_run()
        if status is True:
            run_number = ret_obj
            status, ret_obj = self._myWorkflow.get_run_info(run_number)
            if status is True:
                # run is located in workflow controller
                run_file_name, ipts_number = ret_obj
                if run_file_name.startswith('/SNS/'):
                    # data is from data server: redirect to IPTS-???/0/.. directory
                    ipts_number = ipts_number
                    log_path = os.path.join('/SNS/VULCAN/',
                                                  'IPTS-%d/0/%d/NeXus' % (ipts_number, run_number))
                else:
                    # local data file
                    log_path = os.path.dirname(run_file_name)
            else:
                guiutil.pop_dialog_error(self, 'Unable to get run from tree view: %s' % ret_obj)
            self._currLogRunNumber = run_number
        else:
            guiutil.pop_dialog_error(self, 'Unable to get run from tree view: %s' % ret_obj)
        # END-IF

        # Dialog to get the file name
        file_filter = "NXS (*.nxs);;All files (*.*)"
        log_file_name = str(QtGui.QFileDialog.getOpenFileName(self, 'Open NeXus File',
                                                              log_path, file_filter))

        # Load log
        log_name_list = self.load_sample_run(log_file_name, smart=True)

        # Plot first 6 sample logs
        do_skip = self.ui.checkBox_logSkipSec.checkState() == QtCore.Qt.Checked
        if do_skip is True:
            num_sec_skipped = guiutil.parse_integer(self.ui.lineEdit_numSecLogSkip)
        else:
            num_sec_skipped = None

        # Set up and plot all 6 widgets groups
        for i in xrange(min(self._numSnapViews, len(log_name_list))):
            # create a log_widget from base snap view widgets and set up
            snap_widget = self._groupedSnapViewList[i]
            log_widget = spview.SampleLogView(snap_widget, self)

            log_widget.reset_log_names(log_name_list)
            log_widget.set_current_log_name(i)

            # get log value
            # log_name = log_name_list[i]
            # vec_times, vec_log_value = self.get_sample_log_value(log_name)

            # plot log value
            # log_widget.plot_data(vec_times, vec_log_value, do_skip, num_sec_skipped)

        # END-FOR

        # Record sample log file
        self._lastSampleLogFileName = log_file_name

        return

    def do_save_slicer(self):
        """ Save the slicer (splitters) for future splitting
        :return:
        """
        guiutil.pop_dialog_error('ASAP')

    def do_show_calibration_map(self):
        """
        Purpose:
            Show detailed calibration file mapping information.
        Example:
            -rw-rwxr-- 1 13489 49133 403704 Jun 16 16:43 70487-s.gda
            -rw-rwxr-- 1 13489 49133 3240 Jun 16 16:43 Vulcan-70487-s.prm
        Requirements:
            ???
        Guarantees:
            ???
        :return:
        """
        # TODO/NOW/FIXME
        raise NotImplementedError('ASAP')

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
                self.ui.menu = QtGui.QMenu(self)

                pop_action = QtGui.QAction('Pop', self)
                pop_action.triggered.connect(self.pop_snap_view)
                self.ui.menu.addAction(pop_action)

                # add other required actions
                self.ui.menu.popup(QtGui.QCursor.pos())
        # END-IF

        return

    def evt_quit(self):
        """
        Quit application without saving
        :return:
        """
        self.save_settings()

        # FIXME - Save the session automatically before leaving
        self.close()

    def get_sample_log_value(self, log_name, relative=False):
        """
        Get sample log vaue
        :param log_name:
        :return: 2-tuple as (numpy.1darray, numpy.1darray)
        """
        status, ret_obj = self._myWorkflow.get_sample_log_values(None, log_name, relative=relative)
        if status is False:
            raise RuntimeError(ret_obj)

        vec_times, vec_log_value = ret_obj

        return vec_times, vec_log_value

    def get_ipts_runs(self):
        """
        Get added IPTS and run to caller
        :return:
        """
        return self._myWorkflow.get_project_runs()

    def get_workflow(self):
        """
        Get workflow instance
        :return:
        """
        return self._myWorkflow

    def load_sample_run(self, run, smart):
        """
        Load sample run
        :param run: string or integer as nxs file name or run number
        :param smart: flag to give the log name in a smart way
        :return: list of string for log names
        """
        # Check
        assert isinstance(run, str) or isinstance(run, int)

        # Get NeXus file name
        if isinstance(run, int):
            # in case of run number is given
            status, run_tuple = self._myWorkflow.get_run_info(run)
            if status is False:
                raise RuntimeError(run_tuple)
            nxs_file_name = run_tuple[0]
            run_number = int(run)
        else:
            nxs_file_name = run
            run_number = None

        # Load file
        status, errmsg = self._myWorkflow.set_slicer_helper(nxs_file_name=nxs_file_name, run_number=run_number)
        if status is False:
            raise RuntimeError(errmsg)

        # Get log names
        status, ret_value = self._myWorkflow.get_sample_log_names(smart)
        if status is False:
            errmsg = ret_value
            raise RuntimeError(errmsg)
        else:
            log_name_list = ret_value

        return log_name_list

    def menu_save_session(self):
        """
        Save session called from menu
        :return:
        """
        if self._savedSessionFileName is None:
            self._savedSessionFileName = str(
                QtGui.QFileDialog.getSaveFileName(self, 'Save Session', self._myWorkflow.get_working_dir(),
                                                  'XML files (*.xml);; All files (*.*)'))

        self._myWorkflow.save_session(self._savedSessionFileName)

        return

    def menu_save_session_as(self):
        """
        Save session as
        :return:
        """
        saved_session_file_name = str(
                QtGui.QFileDialog.getSaveFileName(self, 'Save Session', self._myWorkflow.get_working_dir(),
                                                  'XML files (*.xml); All files (*.*)'))

        self._myWorkflow.save_session(saved_session_file_name)

        return

    def menu_load_session(self):
        """
        Load session from file
        :return:
        """
        # Get file name
        input_file_name = str(
            QtGui.QFileDialog.getOpenFileName(self, 'Load Session', self._myWorkflow.get_working_dir(),
                                              'XML files (*.xml);; All files (*.*)')
        )

        # Load
        status, input_file_name = self._myWorkflow.load_session(input_file_name)
        if status is False:
            guiutil.pop_dialog_error('Unable to load session from %s' % input_file_name)

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

    def pop_manual_picker(self):
        """
        Pop out manual picker window
        :return:
        """
        # Start
        if isinstance(self._manualPikerWindow, LogPicker.WindowLogPicker):
            self._manualPikerWindow.show()
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
            self._manualPikerWindow = LogPicker.WindowLogPicker(self, run_number)

        # Set up tree view for runs
        self._manualPikerWindow.setup()

        # Show
        self._manualPikerWindow.show()

        return

    def pop_snap_view(self):
        """ Pop out snap view dialog (window)
        :return:
        """
        # Check index
        if self._currentSnapViewIndex < 0 \
                or self._currentSnapViewIndex >= len(self._groupedSnapViewList):
            error_message = 'Current snap view index (%d) is either not defined ' \
                            'or out of boundary' % self._currentSnapViewIndex
            guiutil.pop_dialog_error(error_message)

        # Create a Snap view window if needed
        if self._snapViewWindow is None:
            # Create a new window
            print '[DB Trace] Creating a new SnapViewDialog.'
            self._snapViewWindow = dlgSnap.DialogLogSnapView(self)

        # Refresh?
        if self._snapViewWindow.allow_new_session() is False:
            # If window is open but not saved, pop error message
                guiutil.pop_dialog_error(self, 'Current window is not saved.')
                return
        # END-IF

        # Get the final data
        sample_log_view = spview.SampleLogView(self._groupedSnapViewList[self._currentSnapViewIndex], self)
        sample_log_name = sample_log_view.get_log_name()
        num_skipped_second = guiutil.parse_float(self.ui.lineEdit_numSecLogSkip)
        self._snapViewWindow.setup(self._myWorkflow, self._currLogRunNumber, sample_log_name, num_skipped_second)

        self._snapViewWindow.show()

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

    """
    def _apply_slicer_snap_view(self):
        Apply Slicers to all 6 view
        :return:
        vec_time, vec_y = self._myWorkflow.get_event_slicer_active(relative_time=True)

        for snap_view_suite in self._groupedSnapViewList:
            snap_view_suite.update_event_slicer(vec_time)

        return
    """

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = VDrivePlotBeta()
    myapp.show()

    #exit_code=app.exec_()
    #sys.exit(exit_code)
