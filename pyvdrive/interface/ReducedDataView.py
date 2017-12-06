########################################################################
#
# General-purposed plotting window
#
# NOTE: Bank ID should always start from 1 or positive
#
########################################################################
import os
from PyQt4 import QtCore, QtGui

import gui.GuiUtility as GuiUtility

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import gui.ui_ReducedDataView_ui
import vanadium_controller_dialog


class GeneralPurposedDataViewWindow(QtGui.QMainWindow):
    """ Class for general-purposed plot window to view reduced data
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        super(GeneralPurposedDataViewWindow, self).__init__(parent)

        # Parent & others
        self._myParent = parent
        self._myController = None

        self._bankIDList = [1, 2]

        # workspace management dictionary
        self._choppedRunDict = dict()  # key: run number (key/ID), value: list of workspaces' names
        self._choppedSampleDict = dict()  # key: data workspace name. value: sample (NeXus) workspace name

        # Controlling data structure on lines that are plotted on graph
        self._reducedDataDict = dict()  # key: run number, value: dictionary (key = spectrum ID, value = (vec x, vec y)
        self._dataIptsRunDict = dict()  # key: workspace/run number, value: 2-tuple, IPTS/run number

        # A status flag to show whether the current plot is for sample log or diffraction data
        self._currentPlotSampleLogs = False

        # current status
        self._iptsNumber = None
        self._runNumberList = list()

        self._currRunNumber = None
        self._currChoppedData = False
        self._currWorkspaceTag = None
        self._currBank = 1
        self._currUnit = 'TOF'

        self._choppedRunNumber = 0
        self._choppedSequenceList = None

        self._canvasDimension = 1
        self._plotType = None

        # range of X value to plot
        self._minX = 0
        self._maxX = 1E20

        # mutexes to control the event handling for changes in widgets
        self._mutexRunNumberList = False
        self._mutexChopSeqList = False
        self._mutexBankIDList = False

        # data structure to manage the fitting result
        self._stripBufferDict = dict()  # key = [self._iptsNumber, self._currRunNumber, self._currBank]
        self._lastVanPeakStripWorkspace = None
        self._smoothBufferDict = dict()
        self._lastVanSmoothedWorkspace = None
        self._vanStripPlotID = None
        self._smoothedPlotID = None

        # about vanadium process
        self._vanadiumFWHM = None

        # set up UI
        self.ui = gui.ui_ReducedDataView_ui.Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize widgets
        self._init_widgets()

        # Event handling
        # push buttons 
        self.connect(self.ui.pushButton_prevView, QtCore.SIGNAL('clicked()'),
                     self.do_plot_prev_run)
        self.connect(self.ui.pushButton_nextView, QtCore.SIGNAL('clicked()'),
                     self.do_plot_next_run)
        self.connect(self.ui.pushButton_plot, QtCore.SIGNAL('clicked()'),
                     self.do_plot_diffraction_data)
        self.connect(self.ui.pushButton_plotSampleLog, QtCore.SIGNAL('clicked()'),
                     self.do_plot_sample_logs)
        self.connect(self.ui.pushButton_clearCanvas, QtCore.SIGNAL('clicked()'),
                     self.do_clear_canvas)

        self.connect(self.ui.pushButton_allFillPlot, QtCore.SIGNAL('clicked()'),
                     self.do_plot_contour)

        self.connect(self.ui.pushButton_normByCurrent, QtCore.SIGNAL('clicked()'),
                     self.do_normalise_by_current)

        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'),
                     self.do_apply_new_range)

        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_close)

        # combo boxes
        # self.connect(self.ui.comboBox_runs, QtCore.SIGNAL('currentIndexChanged(int)'),
        #              self.evt_select_new_run_number)
        self.connect(self.ui.comboBox_chopSeq, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_select_new_chopped_child)
        self.connect(self.ui.comboBox_spectraList, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_bank_id_changed)
        self.connect(self.ui.comboBox_unit, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_unit_changed)

        # check boxes
        self.connect(self.ui.checkBox_choppedDataMem, QtCore.SIGNAL(''),
                     self.evt_toggle_load_logs)

        # vanadium
        self.connect(self.ui.pushButton_launchVanProcessDialog, QtCore.SIGNAL('clicked()'),
                     self.do_launch_vanadium_dialog)

        # widgets to load reduced data
        self.connect(self.ui.pushButton_setReducedRunMem, QtCore.SIGNAL('clicked()'),
                     self.do_set_current_run)
        self.connect(self.ui.pushButton_loadArchivedGSAS, QtCore.SIGNAL('clicked()'),
                     self.do_load_archived_gsas)
        self.connect(self.ui.pushButton_browseAnyGSAS, QtCore.SIGNAL('clicked()'),
                     self.do_browse_local_gsas)
        self.connect(self.ui.pushButton_loadAnyGSAS, QtCore.SIGNAL('clicked()'),
                     self.do_load_local_gsas)
        self.connect(self.ui.pushButton_loadSampleLogs, QtCore.SIGNAL('clicked()'),
                     self.do_load_sample_logs)

        self.connect(self.ui.radioButton_fromArchive, QtCore.SIGNAL('toggled (bool)'),
                     self.event_load_options)
        self.connect(self.ui.radioButton_anyGSAS, QtCore.SIGNAL('toggled (bool)'),
                     self.event_load_options)

        # sub window
        self._vanadiumProcessDialog = None

        return

    def _init_widgets(self):
        """
        Initialize some widgets
        :return:
        """
        # default to load data from memory
        self.ui.radioButton_fromArchive.setChecked(True)
        self.ui.radioButton_anyGSAS.setChecked(False)
        self.ui.pushButton_loadSampleLogs.setEnabled(False)

        self.set_group1_enabled(True)
        self.set_group2_enabled(True)
        self.set_group3_enabled(False)

        return

    def set_group1_enabled(self, enabled):
        """
        set the group of widgets to load run from PyVdrive reduced in memory
        :param enabled:
        :return:
        """
        self.ui.comboBox_runs.setEnabled(enabled)
        self.ui.pushButton_setReducedRunMem.setEnabled(enabled)
        self.ui.checkBox_choppedDataMem.setEnabled(enabled)

        return

    def set_group2_enabled(self, enabled):
        """
        set the group of widgets to load run from archived reduced data
        :param enabled:
        :return:
        """
        self.ui.lineEdit_iptsNumber.setEnabled(enabled)
        self.ui.pushButton_loadArchivedGSAS.setEnabled(enabled)
        self.ui.lineEdit_run.setEnabled(enabled)
        self.ui.checkBox_loadChoppedArchive.setEnabled(enabled)

        return

    def set_group3_enabled(self, enabled):
        """
        set the group of widgets to load run from arbitrary reduced data
        :param enabled:
        :return:
        """
        self.ui.lineEdit_gsasFileName.setEnabled(enabled)
        self.ui.pushButton_browseAnyGSAS.setEnabled(enabled)
        self.ui.pushButton_loadAnyGSAS.setEnabled(enabled)
        self.ui.checkBox_loadChoppedAny.setEnabled(enabled)

        return

    def do_browse_local_gsas(self):
        """
        browse GSAS file or chopped GSAS files via local HDD
        :return:
        """
        # get setup
        is_chopped_data = self.ui.checkBox_loadChoppedAny.isChecked()
        default_dir = self._myController.get_working_dir()

        # get GSAS file or gsas files
        if is_chopped_data:
            # get the directory of chopped data
            chopped_data_dir = str(QtGui.QFileDialog.getExistingDirectory(self, 'Directory of chopped GSAS files',
                                                                          default_dir))
            self.ui.lineEdit_gsasFileName.setText(chopped_data_dir)
        else:
            # get the data file
            gsas_filter = 'GSAS(*.gda);;GSAS (*.gsa);;All Files(*.*)'
            gsas_file_name = QtGui.QFileDialog.getOpenFileName(self, 'GSAS file name', default_dir, gsas_filter)
            self.ui.lineEdit_gsasFileName.setText(gsas_file_name)

        return

    def do_clear_canvas(self):
        """
        clear canvas
        :return:
        """
        self.ui.graphicsView_mainPlot.reset_1d_plots()

        return

    def do_load_archived_gsas(self):
        """
        blabla
        :return:
        """
        # read from input
        ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, False)
        run_number = GuiUtility.parse_integer(self.ui.lineEdit_run, False)
        is_chopped_data = self.ui.checkBox_loadChoppedArchive.isChecked()

        # import GSAS in SNS archive: data key is workspace name
        try:
            data_key = self._myController.load_archived_gsas(ipts_number, run_number, is_chopped_data)
        except RuntimeError as run_error:
            GuiUtility.pop_dialog_error(self, 'Unable to load run {0} from archive due to\n{1}.'
                                              ''.format(run_number, run_error))
            return

        # set sequence list
        if is_chopped_data:
            seq_list = data_key['chopped sequence']
        else:
            seq_list = None

        # add data
        if is_chopped_data:
            raise NotImplementedError('It is not implemented to plot chopped data from GSAS.')
        else:
            self.add_data_set(ipts_number=ipts_number, run_number=run_number, controller_data_key=data_key)

        # set the label
        self.label_loaded_data(self._currRunNumber, is_chopped_data, seq_list)

        return

    def do_load_local_gsas(self):
        """
        load gsas or sequence of GSAS files
        If given a directory, then it is to load a series of GSAS files from chopping a run;
        If given a single file, then it is to
        :return:
        """
        # get GSAS file path
        gsas_path = str(self.ui.lineEdit_gsasFileName.text())
        if len(gsas_path) == 0:
            # check
            GuiUtility.pop_dialog_information(self, 'No GSAS file is given')
            return

        if os.path.isdir(gsas_path):
            # input is a directory: load chopped data series
            data_key_dict, run_number = self._myController.load_chopped_diffraction_files(gsas_path, None, 'gsas')

            # a key as run number
            if run_number is None:
                run_number = gsas_path

            # get workspaces from data key dictionary and add to data management
            diff_ws_list = self.process_loaded_chop_suite(data_key_dict)
            self.add_chopped_workspaces(run_number, diff_ws_list, True)

            data_key = None

        else:
            # input is a file: load a single GSAS file
            # load the data file and returned as data key
            data_key = self._myController.load_diffraction_file(file_name=gsas_path, file_type='gsas')

            # set up the data file to this data viewer and
            status, error_message = self._myController.get_run_info(run_number=None, data_key=data_key)
            if not status:
                GuiUtility.pop_dialog_error(self, error_message)
                return

            # clear some quick references, including GUI widgets its associated chopped data dictionary
            self._mutexChopSeqList = True
            self._mutexRunNumberList = True
            self.ui.comboBox_chopSeq.clear()
            self.ui.comboBox_runs.addItem(data_key)
            self._mutexChopSeqList = False
            self._mutexChopSeqList = False
        # END-IF-ELSE

        # activate it!
        # self.do_set_reduced_from_memory(data_key=data_key)

        return

    def do_load_sample_logs(self):
        """
        If the diffraction data is loaded from GSAS files, then you need to load the sample logs explicitly
        from associated NeXus files
        :return:
        """
        # TODO/NOWNOW - Implement!  What is the difference between this and do_plot_sample_logs() ???
        print '[IMPLEMENT] pushButton_loadSampleLogs'

        for gsas_ws_name in self._choppedSequenceList:
            self._choppedSampleDict

        return

    def add_data_set(self, ipts_number, run_number, controller_data_key, unit=None):
        """
        add a new data set to this data viewer window BUT without plotting including
        1. data management dictionary
        2. combo-box as data key
        :param ipts_number:
        :param run_number:
        :param controller_data_key:
        :param unit:
        :return:
        """
        # return if the controller data key exist
        if controller_data_key in self._reducedDataDict:
            return

        self._dataIptsRunDict[controller_data_key] = ipts_number, run_number

        # show on the list: turn or and off mutex locks around change of the combo box contents
        self._mutexRunNumberList = True
        # clear existing runs
        self.ui.comboBox_runs.addItem(str(controller_data_key))
        # release mutex lock
        self._mutexRunNumberList = False

        # get reduced data set from controller
        if unit is not None:
            self._currUnit = unit

        self.load_reduced_data(run_number=controller_data_key, unit=self._currUnit)

        return controller_data_key

    def add_run_numbers(self, run_tup_list, clear_previous=False):
        """
        set run numbers to combo-box-run numbers
        :param run_tup_list: a list of 2-tuples as (run number, IPTS number) or just a list of integers (run number)
        :param clear_previous:
        :return:
        """
        # check inputs
        assert isinstance(run_tup_list, list), 'Input %s must be a list of run numbers but not of type %s.' \
                                               '' % (str(run_tup_list), type(run_tup_list))

        # sort and add
        run_tup_list.sort()

        # show on the list: turn or and off mutex locks around change of the combo box conents
        self._mutexRunNumberList = True

        # clear existing runs
        if clear_previous:
            self.ui.comboBox_runs.clear()
            self._runNumberList = list()

        # add run number of combo-box and dictionary
        for run_tup in run_tup_list:
            assert isinstance(run_tup, tuple) and len(run_tup) == 2,\
                'Run tuple must contain just run number and ipts number but not {0}'.format(run_tup)
            run_number, ipts_number = run_tup
            self.ui.comboBox_runs.addItem(str(run_number))
            self._dataIptsRunDict[run_number] = ipts_number, run_number
            self._runNumberList.append(run_number)

            print '[DB...BAT] Reduction Window Add Run {0} ({1})'.format(run_number, type(run_number))
        # END-FOR

        # release mutex lock
        self._mutexRunNumberList = False

        return

    def add_chopped_workspaces(self, workspace_key, workspace_name_list, clear_previous=True):
        """
        add (CHOPPED) workspaces' names to the data viewer
        Note: It shall not trigger the event to plot any chopped data
        :param workspace_key:
        :param workspace_name_list:
        :param clear_previous:
        :return:
        """
        # turn on the mutex
        self._mutexRunNumberList = True
        self._mutexChopSeqList = True

        # check input
        assert workspace_key is not None, 'Workspace key (run number mostly) cannot be None'
        # force work key to be string
        workspace_key = '{0}'.format(workspace_key)

        # two cases to get list of chopped workspaces' names
        if workspace_name_list is None:
            # the workspace key must have been loaded before
            assert workspace_key in self._choppedRunDict, 'Workspace key {0} cannot be found in chopped run ' \
                                                          'dictionary whose keys are {1}.' \
                                                          ''.format(workspace_key, self._choppedRunDict.keys())
            workspace_name_list = self._choppedRunDict[workspace_key]
        else:
            # this sequence is set to this viewer first time
            assert isinstance(workspace_name_list, list), 'Workspaces names {0} must be given by list but not a ' \
                                                          '{1}.'.format(workspace_name_list,
                                                                        type(workspace_name_list))
            assert len(workspace_name_list) > 0, 'Workspaces name list cannot be empty'

            # add to widgets and data managing dictionary
            self._choppedRunDict[workspace_key] = list()
            for workspace_name in workspace_name_list:
                self._choppedRunDict[workspace_key].append(workspace_name)

            self.ui.comboBox_runs.addItem('{0}'.format(workspace_key))
        # END-IF-ELSE

        # set check box
        self.ui.checkBox_choppedDataMem.setChecked(True)

        # sort workspace names
        workspace_name_list.sort()

        # add chopped workspaces to (1) _choppedSequenceList (current) and ui.comboBox_chopSeq
        if clear_previous:
            self.ui.comboBox_chopSeq.clear()
            self._choppedSequenceList = list()
        for workspace_name in workspace_name_list:
            self.ui.comboBox_chopSeq.addItem(workspace_name)
            self._choppedSequenceList.append(workspace_name)

        # release mutex lock
        self._mutexRunNumberList = False
        self._mutexChopSeqList = False

        return range(len(workspace_name_list))

    def do_apply_new_range(self):
        """ Apply new data range to the plots on graph
        Purpose: Change the X limits of the figure
        Requirements: min X and max X are valid float
        Guarantees: figure is re-plot
        :return: None
        """
        # Get new x range
        curr_min_x, curr_max_x = self.ui.graphicsView_mainPlot.getXLimit()
        new_min_x_str = str(self.ui.lineEdit_minX.text()).strip()
        if len(new_min_x_str) != 0:
            curr_min_x = float(new_min_x_str)

        new_max_x_str = str(self.ui.lineEdit_maxX.text()).strip()
        if len(new_max_x_str) != 0:
            curr_max_x = float(new_max_x_str)

        if curr_max_x <= curr_min_x:
            GuiUtility.pop_dialog_error(self, 'Minimum X %f is equal to or larger than maximum X %f!'
                                              '' % (curr_min_x, curr_max_x))
            return

        # Set new X range
        self.ui.graphicsView_mainPlot.setXYLimit(xmin=curr_min_x, xmax=curr_max_x)

        return

    def do_close(self):
        """ Close the window
        :return:
        """
        self.close()

    def do_normalise_by_current(self):
        """
        Normalize by current/proton charge if the reduced run is not.
        :return:
        """
        # Get run number
        run_number = int(self.ui.comboBox_runs.currentText())

        # Get reduction information from run number
        status, ret_obj = self._myController.get_reduced_run_info(run_number)
        assert status, ret_obj
        reduction_info = ret_obj

        if reduction_info.is_noramalised_by_current() is True:
            GuiUtility.pop_dialog_error(self, 'Run %d has been normalised by current already.' % run_number)
            return

        # Normalize by current
        self._myController.normalise_by_current(run_number=run_number)

        # Re-plot
        bank_id = int(self.ui.comboBox_spectraList.currentText())
        over_plot = self.ui.checkBox_overPlot.isChecked()
        self.plot_by_run_number(run_number, bank_id=bank_id, over_plot=over_plot)

        return

    def do_launch_vanadium_dialog(self):
        """
        launch the vanadium run processing dialog
        :return:
        """
        # launch vanadium dialog window
        self._vanadiumProcessDialog = vanadium_controller_dialog.VanadiumProcessControlDialog(self)
        self._vanadiumProcessDialog.show()

        # get current workspace
        current_run_str = str(self.ui.comboBox_runs.currentText())
        if current_run_str.isdigit():
            current_run = int(current_run_str)
        else:
            current_run = current_run_str
        ipts_number, run_number = self._dataIptsRunDict[current_run]

        self._vanadiumProcessDialog.set_ipts_run(ipts_number, run_number)

        # FWHM
        if self._vanadiumFWHM is not None:
            self._vanadiumProcessDialog.set_peak_fwhm(self._vanadiumFWHM)

        return

    def do_plot_contour(self):
        """
        plot all the chopped data as contour
        :return:
        """
        # get chopped workspace keys
        num_items = self.ui.comboBox_chopSeq.count()
        ws_keys = list()
        for p in range(num_items):
            key_i = str(self.ui.comboBox_chopSeq.itemText(p))
            ws_keys.append(key_i)
        # END-FOR
        print '[DB...BAT] chopped workspace keys: {0}'.format(ws_keys)

        #
        curr_bank = int(self.ui.comboBox_spectraList.currentText())
        self.plot_multiple_runs_2d(bank_id=curr_bank, bank_id_from_1=True, ws_key_list=ws_keys)

        return

    def do_plot_diffraction_data(self):
        """
        Plot the diffraction data. The first choice is from the line edit. If it is blank,
        then from combo box
        :return:
        """
        # get bank to chop
        bank_id_str = str(self.ui.comboBox_spectraList.currentText())
        if bank_id_str.isdigit():
            bank_id = int(bank_id_str)
            bank_id_list = [bank_id]
        else:
            # plot all banks
            bank_id_list = self._bankIDList[:]

        # over plot existing
        over_plot = self.ui.checkBox_overPlot.isChecked()
        unit = str(self.ui.comboBox_unit.currentText())

        # possible chop sequence
        curr_index = self.ui.comboBox_runs.currentIndex()
        if curr_index < 0 or curr_index >= self.ui.comboBox_runs.count():
            self.ui.comboBox_runs.setCurrentIndex(0)
        data_str = str(self.ui.comboBox_runs.currentText())

        if self._currChoppedData or data_str in self._choppedRunDict:
            # chopped data by selecting data key from the chop sequence
            chop_seq_tag = str(self.ui.comboBox_chopSeq.currentText())
            # the chopped sequence tag MAY BE the workspace name. use it directly
            self.plot_chopped_data_1d(chop_seq_tag, bank_id=bank_id_list[0], unit=unit, over_plot=over_plot)

        else:
            # non-chopped data set

            if data_str.isdigit():
                # run number
                run_number = data_str
                self.plot_by_run_number(run_number=run_number, bank_id=bank_id_list[0], unit=unit, over_plot=over_plot)
            else:
                # data key
                data_key = data_str
                self.plot_by_data_key(data_key, bank_id_list=bank_id_list,
                                      over_plot=self.ui.checkBox_overPlot.isChecked())
            # END-IF-ELSE (data_str)
        # END-IF-ELSE

        return

    def do_plot_next_run(self):
        """
        Purpose: plot the previous run in the list and update the run list
        :return:
        """
        if self.ui.comboBox_chopSeq.count() == 0:
            # non-chopping option. get next run in order
            current_run_index = self.ui.comboBox_runs.currentIndex()
            current_run_index += 1
            if current_run_index >= self.ui.comboBox_runs.count():
                # already the last one. cyclic to first
                current_run_index = 0
            # reset the combo index. It will trigger an event
            self.ui.comboBox_runs.setCurrentIndex(current_run_index)

        else:
            # option for chopping data
            current_chop_index = self.ui.comboBox_chopSeq.currentIndex()
            current_chop_index += 1
            if current_chop_index >= self.ui.comboBox_chopSeq.count():
                # already the last one in the list, go back to first one
                current_chop_index = 0
            # reset the combobox index. It will trigger an event
            self.ui.comboBox_chopSeq.setCurrentIndex(current_chop_index)

        # END-IF

        return

    def do_plot_prev_run(self):
        """
        Purpose: plot the previous run in the list and update the run list
        If the current plot is chopped data, advance to previous chopped child workspace; (cyclic is supported)
        otherwise, advance to previously loaded/imported workspace.
        bank_id will be preserved
        :return:
        """
        if self.ui.comboBox_chopSeq.count() == 0:
            # non-chopping option. get next run in order
            current_run_index = self.ui.comboBox_runs.currentIndex()
            current_run_index -= 1
            if current_run_index < 0:
                # already the last one. cyclic to first
                current_run_index = self.ui.comboBox_runs.count() - 1
            # reset the combo index. It will trigger an event
            self.ui.comboBox_runs.setCurrentIndex(current_run_index)
        else:
            # option for chopping data
            current_chop_index = self.ui.comboBox_chopSeq.currentIndex()
            current_chop_index -= 1
            if current_chop_index < 0:
                # already the last one in the list, go back to first one
                current_chop_index = self.ui.comboBox_chopSeq.count() - 1
            # reset the combobox index. It will trigger an event
            self.ui.comboBox_chopSeq.setCurrentIndex(current_chop_index)

        # END-IF

        return

    def do_plot_sample_logs(self):
        """
        plot selected sample logs
        :return:
        """
        # get sample logs
        current_log_str = str(self.ui.comboBox_sampleLogsList.currentText()).strip()
        if len(current_log_str) == 0:
            GuiUtility.pop_dialog_information(self, 'There is no log that has been loaded.')
            return

        sample_name = current_log_str.split()[0]

        if self.ui.checkBox_plotallChoppedLog.isChecked():
            # plot the sample log of all the chopped workspaces
            workspace_key_list = self._choppedRunDict[self._currRunNumber]
            # reset if plot-all is checked
            self.ui.graphicsView_mainPlot.reset_1d_plots()
        else:
            # plot the sample log from the current selected chopped workspace
            workspace_key = str(self.ui.comboBox_chopSeq.currentText())
            workspace_key_list = [workspace_key]
        # END

        # plot
        for workspace_key in workspace_key_list:
            # get the name of the workspace containing sample logs
            if workspace_key in self._choppedSampleDict:
                # this is for loaded GSAS and NeXus file
                sample_key = self._choppedSampleDict[workspace_key]
            else:
                # just reduced workspace
                sample_key = workspace_key

            # get the sample log time and value
            vec_times, vec_value = self._myController.get_sample_log_values(sample_key, sample_name, relative=True)

            # plot
            self.ui.graphicsView_mainPlot.plot_sample_data(vec_times, vec_value, workspace_key, sample_name)
        # END-FOR

        # set flag
        self._currentPlotSampleLogs = True

        return

    def do_set_current_run(self, data_key=None):
        """
        select the run (data key) in comboBox_runs's current text as the current run to plot
        :return:
        """
        # get information: current run number be a string to be more flexible
        if data_key is None:
            self._currRunNumber = str(self.ui.comboBox_runs.currentText())
        else:
            self._currRunNumber = '{0}'.format(data_key)

        self._currChoppedData = self.ui.checkBox_choppedDataMem.isChecked()

        # pre-load the data
        if self._currChoppedData:
            # NOTE:
            # case 1: loaded GSAS file
            #       chopped sequence list (ui)  : RUN_CHOPINDEX (example: 12345_2)
            #       self._choppedSampleDict keys: chopped workspace name
            #       self._choppedRunDict keys   : run number, values: list of chopped workspace names
            #       loaded NeXus file containing logs and events: NOT MANAGED???

            # get the chopped run information from memory
            if self._currRunNumber not in self._choppedRunDict:
                error_message = 'Current run number {0} of type {1} is not in chopped run dictionary, whose keys are ' \
                                ''.format(self._currRunNumber, type(self._currRunNumber))
                for key in self._choppedRunDict.keys():
                    error_message += '{0} of type {1}    '.format(key, type(key))
                raise AssertionError(error_message)

            # get the first data set to find out the bank IDs
            arbitrary_ws_name = self._choppedRunDict[self._currRunNumber][0]
            status, ret_obj = self._myController.get_reduced_run_info(run_number=None, data_key=arbitrary_ws_name)
            if status:
                bank_id_list = ret_obj
            else:
                GuiUtility.pop_dialog_error(self, ret_obj)
                return
            for bank_id in bank_id_list:
                self.ui.comboBox_spectraList.addItem('{0}'.format(bank_id))

            # get sequence list:
            seq_list = sorted(self._choppedSequenceList)

            # set the sample logs. map to NeXus log workspace if applied
            try:
                log_ws_name = self._choppedSampleDict[arbitrary_ws_name]
                if log_ws_name is not None:
                    series_sample_log_list = self._myController.get_sample_log_names(run_number=log_ws_name, smart=True)
                    self.set_sample_log_names(series_sample_log_list)
                else:
                    print '[DEBUG] There is no raw workspace associated with {0}.'.format(arbitrary_ws_name)
            except KeyError as key_error:
                print '[ERROR] Chopped GSAS workspace {0} is not in _choppedSampleDict (containing {1}). FYI {2}' \
                      ''.format(arbitrary_ws_name, self._choppedSampleDict.keys(), key_error)
            # END-TRY
        else:
            # get the original reduced data and add the this.reduced_data_dictionary
            #
            if data_key is None:
                data_key = self._currRunNumber

            status, error_message = self.load_reduced_data(data_key, self._currUnit)
            if not status:
                GuiUtility.pop_dialog_error(self, error_message)
                return
            seq_list = None

        # set the label
        self.label_loaded_data(self._currRunNumber, self._currChoppedData, seq_list)

        return

    def evt_bank_id_changed(self):
        """
        Handling the event that the bank ID is changed: the figure should be re-plot.
        It should be avoided to plot the same data twice against evt_select_new_run_number
        :return:
        """
        # skip if it is locked
        if self._mutexBankIDList:
            return

        self.do_plot_diffraction_data()

        return

    def event_load_options(self):
        """
        handling event that the run loads option is changed
        :return:
        """
        if self.ui.radioButton_fromArchive.isChecked():
            # enable group 2 widgets
            self.set_group2_enabled(True)
            self.set_group3_enabled(False)
        elif self.ui.radioButton_anyGSAS.isChecked():
            # enable group 3 widgets
            self.set_group2_enabled(False)
            self.set_group3_enabled(True)
        else:
            # impossible situation
            raise RuntimeError('One of these 3 radio buttons must be selected!')

        return

    def evt_select_new_run_number(self):
        """ Event handling the case that a new run number is selected in combobox_run
        :return:
        """
        # skip if it is locked
        if self._mutexRunNumberList:
            return

        # plot diffraction data same as
        print '[DB...BAT] Event Select new run number! {0}'.format(self._mutexRunNumberList)
        self.do_plot_diffraction_data()

        return

    def evt_select_new_chopped_child(self):
        """
        Handle the event if there is change in chopped sequence list
        :return:
        """
        if self._mutexChopSeqList:
            return

        self.do_plot_diffraction_data()

        return

    def evt_toggle_load_logs(self):
        """

        :return:
        """
        # TODO/ISSUE/NOWNOW
        print self.ui.pushButton_loadSampleLogs

    def evt_unit_changed(self):
        """
        Purpose: Re-plot the current plots with new unit
        :return:
        """
        # Clear previous image and re-plot
        self.ui.graphicsView_mainPlot.clear_all_lines()

        # Get the data sets that are currently plot and replace them with new unit
        for run_number in self._reducedDataDict.keys():
            # plot
            self.plot_by_run_number(run_number, self._currBank, over_plot=True)
        # END-FOR

        return

    def get_reduced_data(self, run_number, bank_id, unit, bank_id_from_1=True):
        """
        get reduced data (load from HDD if necessary) in the form vectors of X and Y
        :param run_number: data key or run number
        :param bank_id:
        :param unit:
        :param bank_id_from_1:
        :return: 2-tuple [1] True, (vec_x, vec_y); [2] False, error_message
        """
        # run number to integer
        if isinstance(run_number, str) and run_number.isdigit():
            run_number = int(run_number)

        # load data if necessary
        status, error_message = self.load_reduced_data(run_number, unit)
        if not status:
            return False, 'Unable to load {0} due to {1}'.format(run_number, error_message)

        # TODO/ISSUE/NEXT - bank ID and spec ID from 1 is very confusing
        reduced_data_dict = self._reducedDataDict[run_number]
        bank_id_list = reduced_data_dict.keys()
        if 0 in bank_id_list:
            spec_id_from_0 = True
        else:
            spec_id_from_0 = False

        # determine the spectrum ID from controller
        if bank_id_from_1 and spec_id_from_0:
            spec_id = bank_id - 1
        else:
            spec_id = bank_id

        # check again
        if spec_id not in reduced_data_dict:
            raise RuntimeError('Bank ID %d (spec ID %d) does not exist in reduced data dictionary with spectra '
                               '%s.' % (bank_id, spec_id, str(reduced_data_dict.keys())))

        # get data
        vec_x = self._reducedDataDict[run_number][spec_id][0]
        vec_y = self._reducedDataDict[run_number][spec_id][1]

        return True, (vec_x, vec_y)

    @staticmethod
    def guess_run_number(gsas_path):
        """
        guess the run number from a file
        # Example:        / home / wzz / Projects / workspaces / VDrive / beta_test / 98237 - s.gda
        :param gsas_path:
        :return: integer or None
        """
        # get the GSAS file name
        gsas_file_name = os.path.basename(gsas_path)

        # get the first integer out of the file name
        run_number_str = ''
        for s in gsas_file_name:
            if s.isdigit():
                run_number_str += s
            elif len(run_number_str) > 0:
                # break when encounter the first non-digit letter
                break
        # END-FOR

        # convert string to integer
        if len(run_number_str) > 0:
            run_number = int(run_number_str)
        else:
            run_number = None

        return run_number

    def label_loaded_data(self, run_number, is_chopped, chop_seq_list):
        """
        make a label of loaded data to plot
        :param run_number:
        :param is_chopped:
        :param chop_seq_list:
        :return:
        """
        label_str = 'Run {0}'.format(run_number)
        if is_chopped:
            assert isinstance(chop_seq_list, list), 'If is chopped data, then neec to give chop sequence list.'
            chop_seq_list.sort()
            label_str += ': chopped sequence {0} - {1}'.format(chop_seq_list[0], chop_seq_list[-1])

        self.ui.label_currentRun.setText(label_str)

        return

    def load_reduced_data(self, run_number, unit):
        """
        Load reduced data (via run number) to _reducedDataDict.
        :param run_number: a run number (int or string) or data key (i..e, workspace name)
        :param unit:
        :return:
        """
        # search in this object's reduced data dictionary
        if run_number in self._reducedDataDict:
            assert isinstance(self._reducedDataDict[run_number], dict),\
                'Expected run data info {0} is stored in a dictionary but not a {1}.' \
                ''.format(self._reducedDataDict[run_number], type(self._reducedDataDict[run_number]))

            if self._reducedDataDict[run_number]['unit'] == unit:
                # data existing and unit is same
                return True, None

        # find out the input run number is a workspace name or a run number
        if isinstance(run_number, str) and run_number.isdigit() is False:
            # cannot be an integer. then must be a workspace name
            is_workspace = True
        else:
            # integer or can be a string, then shall be a run number
            is_workspace = False
            run_number = int(run_number)
            try:
                self._iptsNumber = self._dataIptsRunDict[run_number][0]
            except KeyError as key_err:
                raise RuntimeError('DataIPTSRunDict keys are {0}; Not include {1}. FYI {2}'
                                   ''.format(self._dataIptsRunDict.keys(),run_number, key_err))

        # try to load the data from memory
        print '[DB...BAT] Run {0} Unit {1} IPTS {2} IsWorkspace {3}'.format(run_number, unit,
                                                                            self._iptsNumber, is_workspace)

        status, ret_obj = self._myController.get_reduced_data(run_number, unit,
                                                              ipts_number=self._iptsNumber,
                                                              search_archive=False,
                                                              is_workspace=is_workspace)

        # if not in memory, try to load from archive
        if not status and not is_workspace:
            # or archive
            print '[DB...BAT] Loading data without searching archive fails... {0}'.format(ret_obj)
            status, ret_obj = self._myController.get_reduced_data(run_number, unit,
                                                                  ipts_number=self._iptsNumber,
                                                                  search_archive=True)

        if status:
            assert isinstance(ret_obj, dict), 'Reduced data set should be dict but not {0}.'.format(type(ret_obj))
            self._reducedDataDict[run_number] = ret_obj
            ret_obj['unit'] = unit

        else:
            error_message = str(ret_obj) + '\n' + 'Unable to find data in memory or archive.'
            return status, error_message

        return True, None

    def set_sample_log_names(self, log_name_list):
        """
        set sample log names to the log name combo box
        :param log_name_list:
        :return:
        """
        # check
        assert isinstance(log_name_list, list), 'Log names {0} must be given by a list but not a {1}.' \
                                                ''.format(log_name_list, type(log_name_list))

        # clear the previous session
        self.ui.comboBox_sampleLogsList.clear()

        # set by name
        for name in log_name_list:
            self.ui.comboBox_sampleLogsList.addItem(name)

        return

    @staticmethod
    def parse_runs_list(run_list_str):
        """ Parse a list of runs in string such as 122, 133, 444, i.e., run numbers are separated by ,
        :param run_list_str:
        :return:
        """
        assert isinstance(run_list_str, str)

        items = run_list_str.strip().split(',')
        run_number_list = list()
        for item in items:
            item = item.strip()
            if item.isdigit():
                run_number = int(item)
                run_number_list.append(run_number)
        # END-FOR

        # check validity
        assert len(run_number_list) > 0, 'There is no valid run number in string %s.' % run_list_str

        return run_number_list

    def plot_1d_diffraction(self, data_key, bank_id, label='', title='', clear_previous=False, color=None):
        """
        plot a spectrum in a workspace
        :exception: RuntimeError if the specified data and bank ID does not exist
        :param data_key: key for self._reductionDataDict
        :param bank_id:
        :param label:
        :param title:
        :param clear_previous: flag to clear the plots on the current canvas
        :param color:
        :return:
        """
        # check existence of data
        if data_key not in self._reducedDataDict:
            # check again whether the input data key is an integer but converted to string
            raise_key = True
            if isinstance(data_key, str) and data_key.isdigit():
                data_key = int(data_key)
                if data_key in self._reducedDataDict:
                    raise_key = False

            if raise_key: 
                raise KeyError('ReducedDataView\'s reduced data dictionary (keys are {0}) does not have data key {1}.'
                               ''.format(self._reducedDataDict.keys(), data_key))

        if bank_id not in self._reducedDataDict[data_key]:
            raise RuntimeError('Bank ID {0} of type {1} does not exist in reduced data key {2} (banks are {3}.'
                               ''.format(bank_id, type(bank_id), data_key, self._reducedDataDict[data_key].keys()))
        # get data and unit
        self._currUnit = str(self.ui.comboBox_unit.currentText())
        status, error_message = self.load_reduced_data(run_number=data_key, unit=self._currUnit)
        if not status:
            GuiUtility.pop_dialog_error(self, error_message)
            return
        vec_x = self._reducedDataDict[data_key][bank_id][0]
        vec_y = self._reducedDataDict[data_key][bank_id][1]

        # plot
        print '[DB...BAT] Check Unit = {0}, X Range = {1}, {2}'.format(self._currUnit, self._minX,
                                                                       self._maxX)

        line_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y), unit=self._currUnit,
                                                                      over_plot=not clear_previous,
                                                                      run_id=data_key, bank_id=bank_id,
                                                                      chop_tag=None)

        self.ui.graphicsView_mainPlot.auto_rescale()
        self.ui.graphicsView_mainPlot.setXYLimit(self._minX, self._maxX)

        # check the bank ID list
        if self.ui.comboBox_spectraList.count() != len(self._reducedDataDict):
            bank_id_list = sorted(self._reducedDataDict[data_key].keys())
            self.set_bank_ids(bank_id_list, bank_id)

        return line_id

    def plot_chopped_data_1d(self, chop_tag, bank_id, unit, over_plot):
        """
        plot chopped data with specified bank ID
        :param chop_tag:
        :param bank_id:
        :param unit:
        :param over_plot:
        :return:
        """
        # check input
        assert isinstance(chop_tag, str), 'Chop tag/chopped workspace name {0} must be a string'.format(chop_tag)
        assert isinstance(bank_id, int), 'Bank ID {0} must be an integer but not a {1}.' \
                                         ''.format(bank_id, type(bank_id))

        # load data if necessary
        status, error_message = self.load_reduced_data(run_number=chop_tag, unit=unit)
        if not status:
            GuiUtility.pop_dialog_error(self, error_message)
            return
        data_set_dict = self._reducedDataDict[chop_tag]

        # plot
        self.ui.graphicsView_mainPlot.plot_diffraction_data(data_set_dict[bank_id], unit,
                                                            run_id=self._currRunNumber, bank_id=bank_id,
                                                            over_plot=over_plot, chop_tag=chop_tag)

        # set the X limit
        if self._maxX < 1E19:  # 1E20 is the default value
            self.ui.graphicsView_mainPlot.setXYLimit(xmin=self._minX, xmax=self._maxX)

        # set the state flag for what is plot
        self._currentPlotSampleLogs = False

        return

    def plot_chopped_data_2d(self, run_number, chop_sequence, bank_id, bank_id_from_1=True, chopped_data_dir=None,
                             vanadium_run_number=None, proton_charge_normalization=False):
        """Plot a chopped run, which is only called from IDL-like command .. 2D
        :param run_number:
        :param chop_sequence:
        :param bank_id:
        :param bank_id_from_1:
        :param chopped_data_dir:
        :param vanadium_run_number:
        :param proton_charge_normalization:
        :return:
        """
        # check inputs' validity
        assert isinstance(run_number, int), 'Run number {0} must be an integer but not a {1}.' \
                                            ''.format(run_number, type(run_number))
        assert isinstance(chop_sequence, list), 'Chopped sequence list {0} must be a list but not a {1}.' \
                                                ''.format(chop_sequence, type(chop_sequence))

        # LOAD DATA
        if chopped_data_dir is None and self._myController.has_chopped_data(run_number, reduced=True):
            # load chopped data from reduction manager
            data_key_dict, run_number_str = self._myController.load_chopped_data(run_number, chop_sequence)
        else:
            # get data from stored GSAS files
            if chopped_data_dir is None:
                chopped_data_dir = self._myController.get_archived_data_dir(self._iptsNumber, run_number,
                                                                            chopped_data=True)
                if os.path.exists(chopped_data_dir) is False:
                    GuiUtility.pop_dialog_error(self, 'SNS archived chopped GSAS directory {0} cannot be found.'
                                                      ''.format(chopped_data_dir))
            # END-IF

            # get data from local directory
            data_key_dict, run_number_str = self._myController.load_chopped_diffraction_files(chopped_data_dir,
                                                                                              chop_sequence,
                                                                                              'gsas')
        # END-IF-ELSE

        # process loaded data
        if vanadium_run_number is not None:
            assert isinstance(vanadium_run_number, int), 'blabla'
            status, ret_obj = self._myController.load_vanadium_run(self._iptsNumber, vanadium_run_number,
                                                                   use_reduced_file=True, smoothed=True)
            if status:
                van_key = ret_obj
            else:
                err_msg = ret_obj
                GuiUtility.pop_dialog_error(self, 'Unable to load archived vanadium run {0} due to {1}.'
                                                  ''.format(vanadium_run_number, err_msg))
                return
            for gsas_ws_name in data_key_dict.keys():
                print '[DB...BAT...TRACE] ', gsas_ws_name, van_key
                status, err_msg = self._myController.normalise_by_vanadium(gsas_ws_name, van_key)
                if not status:
                    GuiUtility.pop_dialog_error(self, err_msg)
                    return
        # END-IF

        # normalize by proton charges
        if proton_charge_normalization:
            for gsas_ws_name in data_key_dict.keys():
                self._myController.normalize_by_proton_charge(gsas_ws_name, self._iptsNumber, run_number, chop_sequence)

        # get workspaces from data key dictionary and add to data management
        diff_ws_list = self.process_loaded_chop_suite(data_key_dict)
        self.add_chopped_workspaces(run_number, diff_ws_list, True)

        # set to current and plot
        self.do_set_current_run(run_number)
        self.ui.checkBox_plotallChoppedLog.setChecked(True)

        # plot
        # TODO/ISSUE/NOWNOW - Check whether min_x and max_x are applied!
        if len(data_key_dict) == 1:
            # only 1 data: plot 1D
            self.do_plot_diffraction_data()
        else:
            # plot 2D
            self.do_plot_contour()

        return

    def plot_by_data_key(self, data_key, bank_id_list, over_plot):
        """
        plot loaded GSAS data
        :param data_key:
        :param bank_id_list:
        :param over_plot:
        :return:
        """
        # check input
        assert isinstance(data_key, str), 'Data key {0} must be a string but not a {1}.'.format(data_key, str(data_key))

        # plot
        for index, bank_id in enumerate(bank_id_list):
            if index == 0:
                clear_canvas = not over_plot
            else:
                clear_canvas = False
            self.plot_1d_diffraction(data_key, bank_id, label='Bank {0}'.format(bank_id),
                                     title='data key: {0}'.format(data_key),
                                     clear_previous=clear_canvas)
        # END-FOR

        return

    def plot_multiple_runs_2d(self, bank_id, bank_id_from_1=False, ws_key_list=None):
        """
        Plot multiple runs (reduced data) to contour plot. 2D
        :return:
        """
        assert isinstance(bank_id, int) and bank_id >= 0, 'Bank ID %s must be a non-negative integer.' \
                                                          '' % str(bank_id)

        if ws_key_list is None and len(self._runNumberList) == 0:
            GuiUtility.pop_dialog_information(self, 'No workspace list or run number list for contour plot.')
            return

        # get the list of runs
        error_msg = ''
        run_number_list = list()
        data_set_list = list()

        # get unit
        self._currUnit = str(self.ui.comboBox_unit.currentText())

        if ws_key_list is None:
            for run_number in self._runNumberList:
                status, ret_obj = self.get_reduced_data(run_number, bank_id, unit=self._currUnit,
                                                        bank_id_from_1=bank_id_from_1)
                if status:
                    run_number_list.append(run_number)
                    data_set_list.append(ret_obj)
                else:
                    error_msg += 'Unable to get reduced data for run %d due to %s;\n' % (run_number, str(ret_obj))
                    continue
            # END-FOR
        else:
            for chop_index, ws_key in enumerate(ws_key_list):
                status, ret_obj = self.get_reduced_data(ws_key, bank_id, unit=self._currUnit,
                                                        bank_id_from_1=bank_id_from_1)
                if status:
                    run_number_list.append(chop_index+1)
                    data_set_list.append(ret_obj)
                else:
                    error_msg += 'Unable to get reduced data for run {0} due to {1};\n'.format(ws_key, str(ret_obj))
                    continue
            # END-FOR
        # END-FOR

        print '[DB...BAT] Run number list: {0} Data set list size: {1}'.format(run_number_list, len(data_set_list))

        # return if nothing to plot
        if len(run_number_list) == 0:
            GuiUtility.pop_dialog_error(self, error_msg)
            return
        elif len(error_msg) > 0:
            print '[Error message] {0}'.format(error_msg)

        # plot
        self.ui.graphicsView_mainPlot.plot_2d_contour(run_number_list, data_set_list)

        # remove the runs that cannot be found
        if len(run_number_list) != self._runNumberList:
            self._mutexRunNumberList = True
            self.ui.comboBox_runs.clear()
            for run_number in sorted(run_number_list):
                self.ui.comboBox_runs.addItem('{0}'.format(run_number))
            self._mutexRunNumberList = False
        # END-IF

        return

    def set_unit(self, unit):
        """

        :return:
        """
        unit_candidates = list()
        for i_text in range(self.ui.comboBox_unit.count()):
            unit_candidates.append(str(self.ui.comboBox_unit.itemText(i_text)))

        if unit.lower().count('tof') > 0:
            index = unit_candidates.index('TOF')
        elif unit.lower().count('spac') > 0:  # consider space or spacing both
            index = unit_candidates.index('dSpacing')
        elif unit.lower().count('q') > 0 or unit.lower().count('momentum'):
            index = unit_candidates.index('Q')
        else:
            raise RuntimeError('Unsupported unit {0}'.format(unit))

        self.ui.comboBox_unit.setCurrentIndex(index)

        # also set the current unit
        self._currUnit = str(self.ui.comboBox_unit.currentText())

        return

    def plot_by_run_number(self, run_number, bank_id, unit=None, over_plot=False):
        """
        Plot a run by RUN NUMBER (integer) on graph as the API to client method
        Requirements:
         1. run number is a positive integer
         2. bank id is a positive integer
        Guarantees:
        :param run_number: integer (run number) or string (workspace name/key)
        :param bank_id:
        :param over_plot:
        :param unit:  default (None) by using the current text in the unit-combo-box
        :return:
        """
        # check bank ID; leave the check for run_number to load_reduced_data
        assert isinstance(bank_id, int), 'Bank ID %s must be an integer, but not %s.' % (str(bank_id),
                                                                                         str(type(bank_id)))
        if bank_id <= 0:
            raise RuntimeError('Bank ID {0} must be positive.'.format(bank_id))

        # Get data (run)
        if unit is None:
            unit = str(self.ui.comboBox_unit.currentText())
        status, error_message = self.load_reduced_data(run_number, unit)
        if not status:
            GuiUtility.pop_dialog_error(self, 'Unable to load run {0} due to {1}'.format(run_number, error_message))
            return

        # update information
        self._currRunNumber = run_number
        self._currBank = bank_id

        # plot
        # FIXME/LATER/ line_id does not seems useful here.
        line_id = self.plot_1d_diffraction(data_key=run_number, bank_id=bank_id, clear_previous=not over_plot)
        self.label_loaded_data(run_number=run_number, is_chopped=False, chop_seq_list=None)

        return

    def process_loaded_chop_suite(self, data_key_dict):
        """
        get the chopped data's sequence inferred from the file names
        :param data_key_dict:
        :return:
        """
        # check inputs
        assert isinstance(data_key_dict, dict), 'Data key dictionary {0} must be a dictionary but not a {1}.' \
                                                ''.format(data_key_dict, type(data_key_dict))

        # get data sequence
        diff_ws_list = list()
        for gsas_ws_name in data_key_dict.keys():
            log_ws_name = data_key_dict[gsas_ws_name][0]
            diff_ws_list.append(gsas_ws_name)
            self._choppedSampleDict[gsas_ws_name] = log_ws_name
        # END-FOR

        print '[DB...BAT] For current chopped run {0} (FYI) Chopped Sample Dict Keys = {1}, Values = {2}' \
              ''.format(self._currRunNumber, self._choppedSampleDict.keys(), self._choppedSampleDict.values())

        return diff_ws_list

    def resize_canvas(self):
        """
        Resize the canvas if it is necessary
        :return:
        """
        # Init
        min_x = 1.E20
        max_x = -1.E20

        # Find minimum x and maximum x
        for run_number in self._reducedDataDict.keys():
            run_data_dict = self._reducedDataDict[run_number]
            assert isinstance(run_data_dict, dict)
            for spec_id in run_data_dict.keys():
                vec_x = run_data_dict[spec_id][0]
                min_x = min(min_x, vec_x[0])
                max_x = max(max_x, vec_x[-1])
        # END-FOR

        # Resize the canvas
        self.ui.graphicsView_mainPlot.setXYLimit(xmin=min_x, xmax=max_x)

        return

    def set_bank_ids(self, bank_id_list, bank_id=None):
        """

        :param bank_id_list:
        :return:
        """
        # lock it
        self._mutexBankIDList = True

        # get current index
        curr_index = self.ui.comboBox_spectraList.currentIndex()

        self.ui.comboBox_spectraList.clear()
        for bank_key in bank_id_list:
            self.ui.comboBox_spectraList.addItem('{0}'.format(bank_key))

        # set to original index
        if bank_id is None:
            if curr_index < len(bank_id_list):
                self.ui.comboBox_spectraList.setCurrentIndex(curr_index)
        else:
            try:
                combo_index = bank_id_list.index(bank_id)
                self.ui.comboBox_spectraList.setCurrentIndex(combo_index)
            except AttributeError as att_err:
                print '[ERROR] Bank ID {0} of type {1} cannot be found in Bank ID List {2}.' \
                      ''.format(bank_id, type(bank_id), self._bankIDList)
                raise att_err
        # END-IF-ELSE

        # unlock
        self._mutexBankIDList = False

        return

    def set_canvas_type(self, dimension, multi_dim_type=None):
        """
        set the canvas type: 1D, 2D, 3D, fill plot or etc
        :param dimension:
        :param multi_dim_type: type for multiple dimension plot
        :return:
        """
        # check
        assert isinstance(dimension, int), 'Dimension must be an integer but not %s.' % type(dimension)
        assert multi_dim_type is None or isinstance(multi_dim_type, str), 'Multiple-dimension plot type ' \
                                                                          'must be None or string but not ' \
                                                                          '%s.' % type(multi_dim_type)

        # change canvas/plot type?
        change_canvas_type = False
        if self._canvasDimension != dimension:
            change_canvas_type = True
        elif multi_dim_type is not None and self._plotType != multi_dim_type:
            change_canvas_type = True

        # set canvas
        if change_canvas_type:
            target_dim = dimension
            if multi_dim_type is not None:
                target_type = multi_dim_type
            else:
                target_type = self._plotType
            self.ui.graphicsView_mainPlot.set_dimension_type(target_dim, target_type)

            self._canvasDimension = dimension
            self._plotType = multi_dim_type
        # END-IF

        return

    def set_ipts_number(self, ipts_number):
        """

        :param ipts_number:
        :return:
        """
        assert isinstance(ipts_number, int), 'Set IPTS number must be an integer.'

        self._iptsNumber = ipts_number

        return

    def set_title_plot_run(self, title):
        """
        set title of the currently plot run
        :param title:
        :return:
        """
        self.ui.label_currentRun.setText(title)

        return

    def set_vanadium_fwhm(self, fwhm):
        """
        set vanadium peak's FWHM
        :param fwhm:
        :return:
        """
        assert isinstance(fwhm, float) or isinstance(fwhm, int) and fwhm > 0, 'FWHM {0} must be a float or integer,' \
                                                                              'but not a {1}.' \
                                                                              ''.format(fwhm, type(fwhm))

        if fwhm <= 0:
            raise RuntimeError('Peak FWHM ({0}) must be positive!'.format(fwhm))
        self._vanadiumFWHM = fwhm

        return

    def set_x_range(self, min_x, max_x):
        """
        set the range of X values
        :param min_x:
        :param max_x:
        :return:
        """
        self._minX = min_x
        self._maxX = max_x

        return

    def setup(self, controller):
        """ Set up the GUI from controller
        :param controller:
        :return:
        """
        # Check
        # assert isinstance(controller, VDriveAPI)
        self._myController = controller

        # Set the reduced runs
        reduced_run_number_list = self._myController.get_reduced_runs()
        reduced_run_number_list.sort()
        self.ui.comboBox_runs.clear()
        for run_number, ipts_number in reduced_run_number_list:
            self.ui.comboBox_runs.addItem(str(run_number))
            self._dataIptsRunDict[run_number] = ipts_number, run_number

        return

    def signal_save_processed_vanadium(self, output_file_name, ipts_number, run_number):
        """
        save GSAS file from GUI
        :param output_file_name:
        :param ipts_number:
        :param run_number:
        :return:
        """
        van_info_tuple = (self._lastVanSmoothedWorkspace, ipts_number, run_number)
        # convert string
        output_file_name = str(output_file_name)

        status, error_message = self._myController.save_processed_vanadium(van_info_tuple=None,
                                                                           output_file_name=output_file_name)
        if not status:
            GuiUtility.pop_dialog_error(self, error_message)

        return

    def signal_strip_vanadium_peaks(self, peak_fwhm, tolerance, background_type, is_high_background, bank_list):
        """
        process the signal to strip vanadium peaks
        :param peak_fwhm:
        :param tolerance:
        :param background_type:
        :param is_high_background:
        :param bank_list:
        :return:
        """
        # from signal, the string is of type unicode.
        background_type = str(background_type)

        # note: as it is from a signal with defined parameters types, there is no need to check
        #       the validity of parameters
        current_run_str = str(self.ui.comboBox_runs.currentText())
        if current_run_str.isdigit():
            current_run_number = int(current_run_str)
            ipts_number, run_number = self._dataIptsRunDict[current_run_number]
            data_key = None
        else:
            data_key = current_run_str
            ipts_number, run_number = self._dataIptsRunDict[data_key]

        # strip vanadium peaks
        status, ret_obj = self._myController.strip_vanadium_peaks(ipts_number, run_number, bank_list,
                                                                  peak_fwhm, tolerance,
                                                                  background_type, is_high_background,
                                                                  data_key)
        if status:
            result_ws_name = ret_obj
            # self.load_reduced_data(run_number=controller_data_key, unit=self._currUnit)
            self.load_reduced_data(run_number=result_ws_name, unit=self._currUnit)
        else:
            err_msg = ret_obj
            GuiUtility.pop_dialog_error(self, err_msg)
            return

        # plot the data without vanadium peaks
        # re-plot the original data because the operation can back from final stage
        # TODO/FIXME/NOW - what if data_key is None??? VDrivePlot version
        self._currUnit = 'dSpacing'
        self.plot_1d_diffraction(data_key=data_key, bank_id=self._currBank,
                                 label='blabla raw label', title='blabla raw title', clear_previous=True,
                                 color='black')

        self._vanStripPlotID = self.plot_1d_diffraction(data_key=result_ws_name, bank_id=self._currBank,
                                                        label='Vanadium peaks striped', title='blabla strip title',
                                                        clear_previous=False,
                                                        color='green')

        if self._iptsNumber is None:
            self._lastVanPeakStripWorkspace = result_ws_name
        else:
            self._stripBufferDict[self._iptsNumber, self._currRunNumber, self._currBank] = result_ws_name

        return

    def signal_smooth_vanadium(self, smoother_type, param_n, param_order):
        """
        process the signal to smooth vanadium spectra
        :param smoother_type:
        :param param_n:
        :param param_order:
        :return:
        """
        # convert smooth_type to string from unicode
        smoother_type = str(smoother_type)

        # get the input workspace
        if self._iptsNumber is None:
            van_peak_removed_ws = self._lastVanPeakStripWorkspace
        else:
            van_peak_removed_ws = self._stripBufferDict[self._iptsNumber, self._currRunNumber, self._currBank]
        status, ret_obj = self._myController.smooth_diffraction_data(workspace_name=van_peak_removed_ws,
                                                                     bank_id=None,
                                                                     smoother_type=smoother_type,
                                                                     param_n=param_n,
                                                                     param_order=param_order,
                                                                     start_bank_id=1)
        if status:
            smoothed_ws_name = ret_obj
            if self._iptsNumber is None:
                self._lastVanSmoothedWorkspace = smoothed_ws_name
            else:
                self._smoothBufferDict[self._iptsNumber, self._currRunNumber, self._currBank] = smoothed_ws_name
            self.load_reduced_data(run_number=smoothed_ws_name)
        else:
            err_msg = ret_obj
            GuiUtility.pop_dialog_error(self, 'Unable to smooth data due to {0}.'.format(err_msg))
            return

        # plot data: the unit is changed to TOF due to Mantid's behavior
        #            as a consequence of this, the vanadium spectrum with peak removed shall be re-plot in TOF space
        # # TODO/NOW/ - a better name
        # label_no_peak = 'blabla no peak'
        # self.plot_1d_diffraction(data_key=van_peak_removed_ws, bank_id=self._currBank,
        #                          title=label_no_peak,
        #                          label=label_no_peak,
        #                          clear_previous=True,
        #                          color='black')

        label = '{3}: Smoothed by {0} with parameters ({1}, {2})' \
                ''.format(smoother_type, param_n, param_order, smoothed_ws_name)
        self.plot_1d_diffraction(data_key=smoothed_ws_name, bank_id=self._currBank,
                                 label=label, title=label,
                                 clear_previous=False, color='red')

        return

    def signal_undo_strip_van_peaks(self):
        """
        undo the strip vanadium peak action, i.e., delete the previous result and remove the plot
        :return:
        """
        if self._vanStripPlotID is None:
            print '[INFO] There is no vanadium-peak-removed spectrum to remove from canvas.'
            return

        # remove the plot
        self.ui.graphicsView_mainPlot.remove_line(line_id=self._vanStripPlotID)
        self._vanStripPlotID = None

        # undo in the controller
        self._myController.undo_vanadium_peak_strip()

        return

    def signal_undo_smooth_vanadium(self):
        """
        undo the smoothing operation on the spectrum including
        1. delete the result
        2. remove the smoothed plot
        :return:
        """
        # return if there is no such action before
        if self._smoothedPlotID is None:
            print '[INFO] There is no smoothed spectrum to undo.'
            return

        # remove the plot
        self.ui.graphicsView_mainPlot.remove_line(self._vanStripPlotID)
        self._smoothedPlotID = None

        # undo in the controller
        self._myController.undo_vanadium_smoothing()

        return