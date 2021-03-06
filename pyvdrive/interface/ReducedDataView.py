########################################################################
#
# General-purposed plotting window
#
# NOTE: Bank ID should always start from 1 or positive
#
########################################################################
import os
import numpy
try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5.QtWidgets import QMainWindow
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5 import QtCore
except ImportError:
    from PyQt4.QtGui import QMainWindow
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4 import QtCore
from pyvdrive.interface.gui import GuiUtility
from pyvdrive.core import vulcan_util
from pyvdrive.core import file_utilities
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

from pyvdrive.interface.gui.generalrunview import GeneralRunView
import pyvdrive.core.datatypeutility
from pyvdrive.core import datatypeutility
from pyvdrive.interface.gui.samplelogview import LogGraphicsView
from pyvdrive.core import reduce_VULCAN
from pyvdrive.core import vdrive_constants
from pyvdrive.interface.atomic_data_viewers import PlotInformation, AtomicReduced1DViewer, AtomicReduction2DViewer,\
    AtomicReduction3DViewer


def generate_sample_log_list():
    """
    generate a list of sample logs for plotting
    :return:
    """
    time_series_sample_logs = list()
    for item_tup in reduce_VULCAN.RecordBase:
        if item_tup[2] in ['average', 'sum']:
            time_series_sample_logs.append(item_tup[1])

    return time_series_sample_logs


def generate_log_names_map():
    """ Generate a map (dictionary) to map from NeXus sample log name to MTS log name (in RECORD file)
    :return:
    """
    nexus_mts_map = dict()

    for mts_name, nexus_name in reduce_VULCAN.MTS_Header_List:
        if nexus_name.strip() == '':
            continue
        nexus_mts_map[nexus_name.strip()] = mts_name.strip()

    return nexus_mts_map


class GeneralPurposedDataViewWindow(QMainWindow):
    """ Class for general-purposed plot window to view reduced data
    """
    # class

    def __init__(self, parent=None):
        """ Init
        """
        # base class initialization
        super(GeneralPurposedDataViewWindow, self).__init__(parent)

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/ReducedDataView.ui")
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()

        # initialize widgets
        self._init_widgets()

        # Parent & others
        self._myParent = parent
        self._myController = None

        self._atomic_viewer_list = list()   # list of plots for single bank

        # common
        self._iptsNumber = None  # IPTS number last set
        self._bankIDList = list()  # synchronized with comboBox_spectraList
        self._currBank = 1
        self._currUnit = str(self.ui.comboBox_unit.currentText())

        # normalization
        self._curr_pc_norm = False
        self._vanadium_dict = dict()

        # single runs
        self._curr_data_key = None  # current (last loaded) workspace name as data key
        self._currRunNumber = None   # run number of single run reduced
        # single runs: single run combo box items and other information
        # [single run combo box name] = run number (aka data key)
        self._single_combo_data_key_dict = dict()
        self._single_combo_name_list = list()  # single run combo box name list with orders sync with combo box
        # [data key] = dict() such as van_norm, van_run, pc_norm...
        self._single_run_plot_option = dict()
        self._single_run_data_dict = dict()  # [run number/reduced file name] = data key
        self._data_key_run_seq = dict()  # [data key] = run number, chop-seq

        # chopped runs: chop run combo box items and other information
        # [chop run combo box name] = run number, slicer key;
        self._chop_combo_data_key_dict = dict()
        # sync with comboBox_choppedRunNumber
        self._chop_combo_name_list = list()  # chop run combo box names with orders sync with combo box
        self._chop_seq_combo_name_list = list()   # chop sequence combo box names with orders sync with combo box
        # [chop key] = dict() such as van_norm, van_run, pc_norm...
        self._chop_run_plot_option = dict()
        # [run number] = [seq index]: run + seq = key to find the data
        self._chopped_run_data_dict = dict()
        # self._curr_chop_data_key = None   # run number of sliced case

        # record of X value range
        self._xrange_dict = {'TOF': (1000, 70000),
                             'dSpacing': (None, None)}

        # sample log runs and logs
        self._log_data_key = None
        self._log_display_name_dict = dict()   # [log display name] = log full name (to look up)
        self._sample_log_dict = dict()  # [IPTS][RUN] = {'ProtonCharge': xxx, 'MTS': xxx, ...}
        # [RUN] = {'start': ..., 'mean': ..., 'end': ..., 'IPTS': xxx}
        self._sliced_log_dict = dict()
        # [RUN] = {[CHOP-INDEX]: dict(1) , [CHOP-INDEX]:dict(2)...}
        self._sliced_h5_log_dict = dict()
        # dict(i):  {'ProtonCharge': (vec Time, vec Value), ...}
        self._sample_log_name_list = generate_sample_log_list()  # list of sample logs that are viable to plot
        self._sample_log_info_dict = dict()  # [meta_data_key] = ipts, run number

        self._curr_log_raw_plot_id = None   # Plot ID for the raw sample log
        self._curr_log_x_name = None   # log X-axis name
        self._curr_log_y_name = None   # log Y-axis name
        self._curr_log_sliced_dict = dict()  # [slice ID] = Plot ID
        self._chopped_start_log_id = None
        self._nexus_mtd_log_name_map = generate_log_names_map()

        # FIND OUT: self._choppedSampleDict = dict()  # key: data workspace name. value: sample (NeXus) workspace name

        # Controlling data structure on lines that are plotted on graph
        # (UI-key): tuple (data key, bank ID, unit); value: value = vec x, vec y
        self._currentPlotDataKeyDict = dict()
        self._currentPlotID = None   # ID of current plot
        # this is a temporary storage of reduced data loaded and cached

        # mutexes to control the event handling for changes in widgets
        self._mutexRunNumberList = False
        self._mutexChopRunList = False
        self._mutexChopSeqList = False
        self._mutexBankIDList = False
        self._mutex_sample_logs = False

        # about vanadium process
        self._vanadiumFWHM = None

        # Event handling
        # section: load data
        self.ui.pushButton_loadSingleGSAS.clicked.connect(self.do_load_single_run)
        self.ui.pushButton_loadChoppedGSASSet.clicked.connect(self.do_load_chopped_runs)
        self.ui.radioButton_fromArchive.toggled.connect(self.evt_change_data_source)  # combo
        self.ui.radioButton_anyGSAS.toggled.connect(self.evt_change_data_source)  # combo

        self.ui.pushButton_refreshList.clicked.connect(self.do_refresh_existing_runs)  # refresh

        # what to plot
        self.ui.radioButton_chooseSingleRun.toggled.connect(
            self.evt_toggle_run_type)   # w/ radioButton_chooseChopped

        # section: plot single run
        self.ui.pushButton_prevRun.clicked.connect(self.do_plot_prev_single_run)
        self.ui.pushButton_nextRun.clicked.connect(self.do_plot_next_single_run)
        # self.ui.pushButton_plot.clicked.connect(self.do_plot_diffraction_data)
        self.ui.comboBox_runs.currentIndexChanged.connect(self.evt_plot_different_single_run)

        # section: plot chopped run
        self.ui.pushButton_prevChopped.clicked.connect(self.do_plot_prev_chopped_sequence)
        self.ui.pushButton_nextChopped.clicked.connect(self.do_plot_next_chopped_sequence)
        self.ui.comboBox_choppedRunNumber.currentIndexChanged.connect(
            self.evt_plot_different_chopped_run)
        self.ui.comboBox_chopSeq.currentIndexChanged.connect(
            self.evt_plot_different_chopped_sequence)

        # section: plot sample log
        self.ui.pushButton_loadLogs.clicked.connect(self.do_load_sample_log)
        self.ui.pushButton_plotSampleLog.clicked.connect(self.do_plot_sample_log_raw)
        self.ui.pushButton_plotSlicedLog.clicked.connect(self.do_plot_sample_log_sliced)

        # plot related
        self.ui.pushButton_clearCanvas.clicked.connect(self.do_clear_canvas)

        # data processing
        self.ui.pushButton_apply_x_range.clicked.connect(self.do_set_x_range)
        self.ui.pushButton_apply_y_range.clicked.connect(self.do_apply_y_range)
        self.ui.comboBox_spectraList.currentIndexChanged.connect(self.evt_change_bank)
        self.ui.comboBox_unit.currentIndexChanged.connect(self.evt_change_unit)

        self.ui.pushButton_cancel.clicked.connect(self.do_close)

        self._init_widgets_post()

        # sub window
        self._vanadiumProcessDialog = None

        return

    def _promote_widgets(self):
        """
        promote widgets
        :return:
        """
        graphicsView_mainPlot_layout = QVBoxLayout()
        self.ui.frame_graphicsView_mainPlot.setLayout(graphicsView_mainPlot_layout)
        self.ui.graphicsView_mainPlot = GeneralRunView(self)
        graphicsView_mainPlot_layout.addWidget(self.ui.graphicsView_mainPlot)

        # sample log view
        temp_layout = QVBoxLayout()
        self.ui.frame_graphicsView_sampleLogs.setLayout(temp_layout)
        self.ui.graphicsView_logPlot = LogGraphicsView(self)
        temp_layout.addWidget(self.ui.graphicsView_logPlot)

        return

    def _init_widgets(self):
        """
        Initialize some widgets
        :return:
        """
        # select single run or chopped run
        self.ui.radioButton_chooseSingleRun.setChecked(True)
        self.ui.groupBox_plotSingleRun.setEnabled(True)
        self.ui.groupBox_plotChoppedRun.setEnabled(False)

        # set bank ID combobox
        self._bankIDList = [1, 2, 3]
        self.ui.comboBox_spectraList.clear()
        for bank_id in self._bankIDList:
            self.ui.comboBox_spectraList.addItem('{0}'.format(bank_id))

        # read-only line edit
        self.ui.lineEdit_gsasFileName.setEnabled(False)

        # sample log
        self.ui.radioButton_plotSlicedLogSimple.setChecked(False)
        self.ui.radioButton_plotDetailedSlicedLog.setChecked(True)

        return

    def _init_widgets_post(self):
        """
        Init widgets considering the event handling method triggered
        :return:
        """
        # load data: default to load data from memory
        # self._set_load_from_archive_enabled(True)
        # self._set_load_from_hdd_enabled(False)
        self.ui.radioButton_fromArchive.setChecked(True)

        return

    def _get_plot_x_range_(self, default_x, default_y):
        """ get the x range of current plot
        :return: 2-tuple.  min x, max x  (if not set, then None)
        """
        # check current min/max for data
        min_x_str = str(self.ui.lineEdit_minX.text()).strip()
        try:
            min_x = float(min_x_str)
        except ValueError:
            min_x = default_x
        max_x_str = str(self.ui.lineEdit_maxX.text()).strip()
        try:
            max_x = float(max_x_str)
        except ValueError:
            max_x = default_y

        return min_x, max_x

    def _is_run_in_memory(self, run_number):
        """
        Check whether a run has been reduced
        :param run_number:
        :return:
        """
        return self._myController.project.reduction_manager.has_run_reduced(run_number)

    def do_clear_canvas(self):
        """
        clear canvas
        :return:
        """
        self.ui.graphicsView_mainPlot.reset_1d_plots()
        self._currentPlotID = None

        return

    # TODO - TONIGHT 0 - Shall mimic what _process_view() does!
    def do_load_chopped_runs(self, ipts_number=None, run_number=None, chopped_seq_list=None):
        """ Load a series chopped and reduced data to reduced data view
        :param ipts_number:
        :param run_number:
        :param chopped_seq_list:
        :return: chopped data key (run number as integer)
        """
        # read from input for IPTS and run number
        if ipts_number is None or ipts_number is False:
            ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, False)
        else:
            self.ui.lineEdit_iptsNumber.setText('{}'.format(ipts_number))
        if run_number is None or ipts_number is False:
            run_number = GuiUtility.parse_integer(self.ui.lineEdit_run, False)
        else:
            self.ui.lineEdit_run.setText('{}'.format(run_number))

        # get data sets
        if run_number is not None and self._myController.has_native_sliced_reduced_workspaces(run_number) and False:
            # TODO - TONIGHT 196 - Disabled to load data from memory
            # load from memory
            # FIXME - TOMORROW - NOT TEST YET! Need to be on analysis cluster!
            data_key_dict, run_number_str = self._myController.something.load_chopped_data(
                run_number, chopped_seq_list)
            raise NotImplementedError('ASAP: What shall be chop key?')
        elif ipts_number is not None and run_number is not None:
            # load data from archive
            data_key, loaded_seq_list = self.load_reduced_data(
                ipts_number, run_number, chopped_seq_list)
        else:
            raise NotImplementedError('Not sure how to load from an arbitrary directory!')

        return loaded_seq_list

    def do_load_single_run(self, ipts_number=None, run_number=None, plot=True):
        """
        Load a single run to reduced data view. But not update anything
        Note: this is a high level method
        :param ipts_number:
        :param run_number:
        :param plot:
        :return:
        """
        # read from input for IPTS and run number
        if ipts_number is None or ipts_number is False:
            ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, False)
        else:
            self.ui.lineEdit_iptsNumber.setText('{}'.format(ipts_number))
        if run_number is None or run_number is False:
            run_number = GuiUtility.parse_integer(self.ui.lineEdit_run, False)
        else:
            self.ui.lineEdit_run.setText('{}'.format(run_number))

        # loaded reduced data or set in-memory reduced workspaces
        if run_number is not None and (self._is_run_in_memory(run_number) or ipts_number is not None):
            # load runs from memory or from disk
            try:
                data_key, no_use = self.load_reduced_data(ipts_number, run_number, None)
            except RuntimeError as run_err:
                GuiUtility.pop_dialog_error(self, 'Unable to find GSAS: {}'.format(run_err))
                return False

        else:
            # load from disk by users' choice
            if ipts_number is not None:
                default_dir = '/SNS/VULCAN/IPTS-{}/shared/'.format(ipts_number)
            else:
                default_dir = self._myController.get_working_dir()

            file_filter = 'GSAS File (*.gda);;GSAS File (*.gsa);;NeXus File (*.nxs)'

            reduced_data_file = GuiUtility.browse_file(self, 'Select a reduced file',
                                                       default_dir=default_dir,
                                                       file_filter=file_filter,
                                                       file_list=False, save_file=False)
            # check whether user cancels the operation
            if reduced_data_file is None or reduced_data_file == '':
                return False

            try:
                if reduced_data_file.lower().endswith('nxs'):
                    # processed NeXus
                    data_key = self._myController.load_meta_data(reduced_data_file)
                else:
                    # gsas file
                    file_type = 'gsas'
                    data_key = self._myController.project.data_load_manager.load_binned_data(reduced_data_file,
                                                                                             file_type)
                # END-IF-ELSE
                self._single_run_data_dict[reduced_data_file] = data_key
                self._data_key_run_seq[data_key] = reduced_data_file, None
            except RuntimeError as run_err:
                GuiUtility.pop_dialog_error(
                    self, 'Unable to load {} due to {}'.format(reduced_data_file, run_err))
                return
        # END-IF-ELSE

        # next step
        if plot:
            # refresh
            self.do_refresh_existing_runs()
            # TODO - TONIGHT 191 - Implement set_single_run(name, key, blabla)
            # TODO - TONIGHT 191 - Implement plot_current_data()

        return data_key

    def do_load_sample_log(self):
        """
        Load sample logs (it refers to VDrivePlot.load_sample_run()
        :return:
        """
        try:
            ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, False)
            run_number = GuiUtility.parse_integer(self.ui.lineEdit_run, False)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self,
                                        'IPTS and run number must be specified for viewing sample logs: {}'
                                        ''.format(run_err))
            return

        # Load NeXus (meta only)
        try:
            # load workspace with meta data only (return workspace name)
            meta_data_key = self._myController.load_meta_data(ipts_number=ipts_number, run_number=run_number,
                                                              file_name=None)
            self._log_data_key = meta_data_key
            self._sample_log_info_dict[meta_data_key] = ipts_number, run_number
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self, 'Unable to load Meta data due to {}'.format(run_err))
            return

        # get samples
        log_name_list = self._myController.get_sample_log_names(run_number, True,
                                                                limited=True)

        # convert the log name to a short one for display
        self._log_display_name_dict.clear()
        for log_name in log_name_list:
            if ':' in log_name:
                display_name = log_name.split(':')[-1]
            else:
                display_name = log_name
            self._log_display_name_dict[display_name] = log_name.split()[0]  # remove "(#entries)}"
        # END-FOR

        # update
        self.update_sample_log_list(sorted(self._log_display_name_dict.keys()), reset_plot=True)
        self.ui.label_loadedSampleLogRun.setText('Currently Loaded: IPTS = {}, Run = {} (Log data ID: {}'
                                                 ''.format(ipts_number, run_number, self._sample_log_info_dict))

        return

    # TODO - TODAY 190 - Add UI widget to enable this!
    def do_load_sliced_logs(self):
        """
        Load sliced sample logs
        :return:
        """
        try:
            ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, False)
            run_number = GuiUtility.parse_integer(self.ui.lineEdit_run, False)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self,
                                        'IPTS and run number must be specified for viewing sample logs: {}'
                                        ''.format(run_err))
            return
        # END-TRY

        # load log
        if self._myController.has_native_sliced_reduced_workspaces(ipts_number, run_number, in_memory=True):
            # data sliced in memory: simply need workspaces
            sample_log_names = self._sample_log_name_list
        else:
            try:
                log_files = self._myController.archive_manager.locate_sliced_h5_logs(
                    ipts_number, run_number)
            except RuntimeError as any_err:
                GuiUtility.pop_dialog_error(self, 'Unable to load log files of IPTS-{} Run-{} due to {}'
                                                  ''.format(ipts_number, run_number, any_err))
                return
            whatever = self._myController.load_chopped_logs(log_files)
            sample_log_names = whatever.get_sample_logs()
        # END-IF-ELSE

        # Referene of old design
        """
        # load a record file containing all the chopped data information
        record_name = GuiUtility.get_load_file_by_dialog(self, 'Chopped sample log record file',
                                                         self._myController.get_working_dir(),
                                                         'Text file (*.txt)')

        if record_name == '':
            # cancel the operation
            return

        # load
        chopped_log_dict = vulcan_util.load_chopped_log_files(record_name)

        self.load_chopped_logs(chopped_log_dict)
        """

        # set combo boxes
        self._set_sample_log_combo_box(self.ui.comboBox_sampleLogsList_y, sample_log_names)
        sample_log_names.insert(0, 'Time')
        self._set_sample_log_combo_box(self.ui.comboBox_sampleLogsList_x, sample_log_names)

        # plot current sample log
        self.do_plot_sample_log_raw()

        return

    def update_sample_log_list(self, log_name_list, reset_plot=True):
        """
        update (or say, reset) the sample log list
        :param log_name_list:
        :return:
        """
        # lock the event handling
        self._mutex_sample_logs = True  # lock

        # clear previous
        self.ui.comboBox_sampleLogsList_x.clear()
        self.ui.comboBox_sampleLogsList_y.clear()

        # clear image
        self.ui.graphicsView_logPlot.reset()

        # add log names
        self.ui.comboBox_sampleLogsList_x.addItem('Time (s)')   # add time for X

        for sample_log_name in log_name_list:
            self.ui.comboBox_sampleLogsList_x.addItem(sample_log_name)
            self.ui.comboBox_sampleLogsList_y.addItem(sample_log_name)

        self._mutex_sample_logs = False  # unlock

        return

    def update_bank_id_combo(self, data_key):
        """ Update the bank ID combo box.
        Updating the figure accordingly is not within the scope of this method
        :param data_key: key to find out the bank IDs
        :return:
        """
        # get bank ID list
        if data_key.isdigit():
            run_number = int(data_key)
            data_key_temp = None
        else:
            run_number = None
            data_key_temp = data_key
        status, data_bank_list = self._myController.get_reduced_run_info(run_number=run_number,
                                                                         data_key=data_key_temp)  # , info_type='bank')
        if not status:
            print('[ERROR-POP] Unable to get bank list from {0}'.format(data_key))
            return
        print(data_bank_list)

        # number of banks are same
        if len(data_bank_list) == len(self._bankIDList):
            return

        # lock the event handling, set the bank IDs and focus to first bank
        self._mutexBankIDList = True
        self.ui.comboBox_spectraList.clear()
        for bank_id in data_bank_list:
            self.ui.comboBox_spectraList.addItem('{}'.format(bank_id))
        self.ui.comboBox_spectraList.setCurrentIndex(0)
        self._bankIDList = data_bank_list[:]
        self._mutexBankIDList = False

        return

    def update_chopped_run_combo_box(self):
        """ Update the chopped run's combo box
        :return:
        """
        assert self._mutexChopRunList, 'Mutex on combo-box chopped run must be turned on'
        assert self._mutexChopSeqList, 'Mutex on combo-box chopped sequence must be turned on'

        # current run
        curr_chopped_run_name = str(self.ui.comboBox_choppedRunNumber.currentText())
        # preserve previously chopped runs' names
        previous_chopped_names = set(self._chop_combo_name_list)

        # get chopped runs in the memory (loaded or real time reduced)
        # FIXME TODO - TODAY 196 - only runs loaded from GSASs
        chopped_run_list = self._myController.get_focused_runs(
            chopped=True)  # chop keys: list of tuples

        # FIXME - delete after #191
        # # get the current (chopped) run's name
        # if len(self._chop_combo_name_list) == 0:
        #     curr_chop_name = None
        # else:
        #     curr_chop_name = str(self.ui.comboBox_choppedRunNumber.currentText())  # whatever shown in the combo box

        # reset the combo box anyway
        self.ui.comboBox_choppedRunNumber.clear()
        self._chop_combo_name_list = list()

        if len(chopped_run_list) > 0:
            chopped_run_list.sort()

            # add chop "runs" to combo box
            for chop_run_tuple_i in chopped_run_list:
                if isinstance(chop_run_tuple_i, tuple):
                    # chopped run in memory
                    run_number_i, slicer_key_i = chop_run_tuple_i
                elif isinstance(chop_run_tuple_i, int):
                    # chopped run loaded from Vulcan archive
                    run_number_i = chop_run_tuple_i
                    slicer_key_i = None
                else:
                    raise NotImplementedError('Chop run tuple {} of type {} is not supported. Contact developer'
                                              ''.format(chop_run_tuple_i, type(chop_run_tuple_i)))
                # name shown in combo-box and chop key
                if slicer_key_i:
                    # chopped run in memory
                    chop_run_name = '{}: {}' \
                                    ''.format(run_number_i, slicer_key_i.lower().split(
                                        '_')[0].replace('slicer', ''))
                    chop_key = run_number_i, slicer_key_i
                else:
                    # chopped run from GSAS
                    chop_run_name = '{}: GSAS'.format(run_number_i)
                    chop_key = run_number_i
                self.ui.comboBox_choppedRunNumber.addItem(chop_run_name)
                self._chop_combo_name_list.append(chop_run_name)
                self._chop_combo_data_key_dict[chop_run_name] = chop_key
            # END-FOR
        # END-FOR

        # if False:  # TODO FIXME - TODAY 191 - Leave to other methods
        #     # handle the new index to the chop run combo box
        #     if curr_chop_name in self._chop_combo_name_list:
        #         # focus to the original one and no need to change the sequential number
        #         combo_index = self._chop_combo_name_list.index(curr_chop_name)
        #         chop_run_key = self._chop_combo_data_key_dict[curr_chop_name]
        #         self.ui.comboBox_choppedRunNumber.setCurrentIndex(combo_index)
        #         current_seq_item = str(self.ui.comboBox_chopSeq.currentText())
        #     else:
        #         # need to refresh: set to first one
        #         self.ui.comboBox_choppedRunNumber.setCurrentIndex(0)
        #         new_chop_run_name = self._chop_combo_name_list[0]
        #         chop_run_key = self._chop_combo_data_key_dict[new_chop_run_name]
        #         current_seq_item = None
        #     # END-IF-ELSE
        #
        #     # refresh the list
        #     seq_list = self._myController.project.get_chopped_sequence(chop_run_key)
        #     print ('[DB...BAT] Reduced View Chopped sequence of {}: {}'.format(chop_run_key, seq_list))
        #     if len(seq_list) > 0:
        #         self._mutexChopSeqList = True  # lock
        #
        #         # update to the chop-sequences
        #         self.ui.comboBox_chopSeq.clear()
        #         set_to_index = 0
        #         self._chop_seq_combo_name_list = list()  # clear
        #         for item_index, seq_i in enumerate(seq_list):
        #             seq_item_i = '{}'.format(seq_i)
        #             self.ui.comboBox_chopSeq.addItem(seq_item_i)
        #             self._chop_seq_combo_name_list.append(seq_item_i)
        #             if '{}'.format(seq_i) == current_seq_item:
        #                 set_to_index = item_index
        #         self.ui.comboBox_chopSeq.setCurrentIndex(set_to_index)
        #
        #         self._mutexChopSeqList = False  # unlock
        #     # END-IF (set chopped sequence)
        # # END-IF-ELSE

        # After combo box update operation
        if curr_chopped_run_name not in self._chop_combo_name_list:
            # no chopped run: reset image
            self.ui.graphicsView_mainPlot.reset_1d_plots()
            self._currentPlotID = None
            self.ui.graphicsView_logPlot.reset()

            # TODO - TONIGHT 191.1 - May need to clear the chop sequence combo box...
            # TODO - But there are other variables to set
        else:
            # set the chop run to 'current'/previous chopped name
            combo_index = self._chop_combo_name_list.index(curr_chopped_run_name)
            self.ui.comboBox_choppedRunNumber.setCurrentIndex(combo_index)
        # END-IF

        return set(self._chop_combo_name_list), previous_chopped_names

    def update_single_run_combo_box(self):
        """ Update the single run combo-box with current single runs in the memory
        Changes will be made to
        (1) run combo box
        (2) single_run_list
        :return: set of current single run list, set of previous single run list
        """
        assert self._mutexRunNumberList, 'Mutex for run number combo box must be turned on before called'

        # register
        prev_runs_names = set(self._single_combo_name_list)
        curr_run_name = str(self.ui.comboBox_runs.currentText())

        # refresh
        single_runs_list = self._myController.get_focused_runs(chopped=False)
        self.ui.comboBox_runs.clear()

        self._single_combo_name_list = list()
        if len(single_runs_list) > 0:
            single_runs_list.sort()

            for run_number, data_key in single_runs_list:
                print('[INFO] Add loaded run {} (type = {}) data key = {}'
                      ''.format(run_number, type(run_number), data_key))

                # come up an entry name
                # convert run  number from integer to string as the standard
                item_name_i = '{0}'.format(run_number)

                # add to combo box as the data key that can be used to refer
                self.ui.comboBox_runs.addItem(item_name_i)
                # synchronize single_run_list with combo box
                self._single_combo_name_list.append(item_name_i)
                self._single_combo_data_key_dict[item_name_i] = data_key
            # END-FOR
        # END-IF

        # after update operation
        if curr_run_name != '' and curr_run_name in self._single_combo_name_list:
            # re-focus to the previous one
            combo_index = self._single_combo_name_list.index(curr_run_name)
            self.ui.comboBox_runs.setCurrentIndex(combo_index)
        elif self.ui.radioButton_chooseSingleRun.isChecked():
            # previously plotting a single run: reset
            self.ui.graphicsView_mainPlot.reset_1d_plots()

        #
        #
        #
        #
        #
        # if len(single_runs_list) == 0:
        #     # no runs: clear image
        #     self.ui.graphicsView_mainPlot.reset_1d_plots()
        # else:
        #     # current selection
        #     current_single_run_name = str(self.ui.comboBox_runs.currentText()).strip()
        #     if current_single_run_name == '':
        #         current_single_run_name = None
        #
        #     # single runs
        #
        #     # update
        #     self.ui.comboBox_runs.clear()
        #     # for run_number, data_key in single_runs_list:
        #     #     print ('[INFO] Add loaded run {} (type = {}) data key = {}'
        #     #            ''.format(run_number, type(run_number), data_key))
        #     #
        #     #     # come up an entry name
        #     #     # convert run  number from integer to string as the standard
        #     #     if isinstance(run_number, int):
        #     #         run_number = '{0}'.format(run_number)
        #     #
        #     #     # add to combo box as the data key that can be used to refer
        #     #     self.ui.comboBox_runs.addItem(run_number)
        #     #     self._single_combo_name_list.append(run_number)  # synchronize single_run_list with combo box
        #     #     self._single_combo_data_key_dict[run_number] = data_key
        #     # # END-FOR
        #
        #     # re-focus to the previous one
        #     if current_single_run_name != '' and current_single_run_name in self._single_combo_name_list:
        #         combo_index = self._single_combo_name_list.index(current_single_run_name)
        #         self.ui.comboBox_runs.setCurrentIndex(combo_index)
        # # END-IF-ELSE
        #
        # # loose it
        # self._mutexRunNumberList = False

        return prev_runs_names, set(self._single_combo_name_list)

    def do_set_x_range(self):
        """ Apply new data range to the plots on graph
        Purpose: Change the X limits of the figure
        Requirements: min X and max X are valid float
        Guarantees: figure is re-plot
        :return: None
        """
        # Get new x range
        curr_min_x, curr_max_x = self.ui.graphicsView_mainPlot.getXLimit()
        new_min_x, new_max_x = self._get_plot_x_range_(curr_min_x, curr_max_x)

        if new_min_x >= new_max_x:
            GuiUtility.pop_dialog_error(self, 'Minimum X %f is equal to or larger than maximum X %f!'
                                              '' % (new_min_x, new_max_x))
            new_min_x = curr_min_x
            new_max_x = curr_max_x
        else:
            # Set new X range
            self.ui.graphicsView_mainPlot.setXYLimit(xmin=new_min_x, xmax=new_max_x)

        return new_min_x, new_max_x

    def do_apply_y_range(self):
        """ Apply new data range to the plots on graph
        Purpose: Change the X limits of the figure
        Requirements: min X and max X are valid float
        Guarantees: figure is re-plot
        :return: None
        """
        # current min and max Y
        curr_min_y, curr_max_y = self.ui.graphicsView_mainPlot.getYLimit()

        # Get new Y range
        new_min_y_str = str(self.ui.lineEdit_minY.text()).strip()
        if len(new_min_y_str) != 0:
            curr_min_y = float(new_min_y_str)

        new_max_y_str = str(self.ui.lineEdit_maxY.text()).strip()
        if len(new_max_y_str) != 0:
            curr_max_y = float(new_max_y_str)

        if curr_max_y <= curr_min_y:
            GuiUtility.pop_dialog_error(self, 'Minimum X %f is equal to or larger than maximum X %f!'
                                              '' % (curr_min_y, curr_max_y))
            return

        # Set new X range
        self.ui.graphicsView_mainPlot.setXYLimit(ymin=curr_min_y, ymax=curr_max_y)

        return

    def do_close(self):
        """ Close the window
        :return:
        """
        # close child widows
        for i_window in range(len(self._atomic_viewer_list)):
            self._atomic_viewer_list[i_window].close()

        self.close()

    def do_plot_diffraction_data(self, main_only):
        """
        Launch N (number of banks) plot window for each bank of the single run
        :param main_only: If true, only plot current at main only
        :return:
        """
        # reset
        self.ui.graphicsView_mainPlot.reset_1d_plots()
        self._currentPlotID = None

        # plot
        run_number = str(self.ui.comboBox_runs.currentText())
        data_key = self._single_combo_data_key_dict[run_number]
        bank_id = int(self.ui.comboBox_spectraList.currentText())

        # get the previous setup for vanadium and proton charge normalization or default
        if data_key in self._single_run_plot_option:
            van_run = self._single_run_plot_option[data_key]['van_run']
            van_norm = self._single_run_plot_option[data_key]['van_norm']
            pc_norm = self._single_run_plot_option[data_key]['pc_norm']
        else:
            van_run = None
            van_norm = pc_norm = False

        try:
            self.plot_single_run(data_key, van_norm=van_norm, van_run=van_run, pc_norm=pc_norm, bank_id=bank_id,
                                 main_only=True)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self, 'Unable to plot {} (bank {}) due to {}'
                                              ''.format(data_key, bank_id, run_err))

        return

    def do_plot_next_single_run(self):
        """
        Purpose: plot the next single run in the list and update the run list
        :return:
        """
        current_run_index = self.ui.comboBox_runs.currentIndex()
        current_run_index += 1
        if current_run_index >= self.ui.comboBox_runs.count():
            # already the last one. cyclic to first
            current_run_index = 0
        # reset the combo index. It will trigger an event
        self.ui.comboBox_runs.setCurrentIndex(current_run_index)

        return

    def do_plot_prev_single_run(self):
        """
        Purpose: plot the previous run in the list and update the run list
        If the current plot is chopped data, advance to previous chopped child workspace; (cyclic is supported)
        otherwise, advance to previously loaded/imported workspace.
        bank_id will be preserved
        :return:
        """
        current_run_index = self.ui.comboBox_runs.currentIndex()
        current_run_index -= 1
        if current_run_index < 0:
            # already the last one. cyclic to first
            current_run_index = self.ui.comboBox_runs.count() - 1
        # reset the combo index. It will trigger an event
        self.ui.comboBox_runs.setCurrentIndex(current_run_index)

        return

    def do_plot_prev_chopped_sequence(self):
        """
        Plot previous chopped sequence
        :return:
        """
        current_chop_index = self.ui.comboBox_chopSeq.currentIndex()
        current_chop_index -= 1
        if current_chop_index < 0:
            # already the first one in the list, go back to last o ne
            current_chop_index = self.ui.comboBox_chopSeq.count() - 1

        # reset the combobox index. It will trigger an event
        self.ui.comboBox_chopSeq.setCurrentIndex(current_chop_index)

        return

    def do_plot_next_chopped_sequence(self):
        """
        Plot the next chopped sequence reduced data
        :return:
        """
        current_chop_index = self.ui.comboBox_chopSeq.currentIndex()
        current_chop_index += 1
        if current_chop_index >= self.ui.comboBox_chopSeq.count():
            # already the last one in the list, go back to first one
            current_chop_index = 0

        # reset the combobox index. It will trigger an event
        self.ui.comboBox_chopSeq.setCurrentIndex(current_chop_index)

        return

    def do_plot_sample_log_sliced(self):
        """ Plot sliced sample logs from (1) archived ASCII (2) archived h5 (3) memory
        :return:
        """
        # get log name to plot
        x_log_name, y_log_name = self.get_sample_logs_to_plot()
        if x_log_name != self._curr_log_x_name or y_log_name != self._curr_log_y_name:
            # different
            self.reset_raw_log()
            self.reset_sliced_log()
            # set again to the current
            self._curr_log_x_name, self._curr_log_y_name = x_log_name, y_log_name
        # END-IF

        # Get IPTS and run number of the current plot data
        try:
            # use IPTS and run to locate the loaded sample logs
            ipts_number, run_number = self._sample_log_info_dict[self._log_data_key]
        except KeyError as key_err:
            GuiUtility.pop_dialog_error(self, 'Log key {} does not exist (sample log info dict): {}'
                                              ''.format(self._log_data_key, key_err))
            return

        # plot label
        base_plot_label = 'Run {}: {} - {}'.format(run_number, x_log_name, y_log_name)

        # Plot according to user's choice
        if self.ui.radioButton_plotSlicedLogSimple.isChecked():
            # Plot in simple (start/stop only) style: the data must be from archived ASCII CVS log file
            # load data if not loaded yet
            if run_number not in self._sliced_log_dict:
                log_header, log_set = vulcan_util.import_sample_log_record(ipts_number, run_number, is_chopped=True,
                                                                           record_type='start')
                self.set_chopped_logs(ipts_number, run_number, log_header, log_set, 'start')
            # END-IF

            # convert log name from display name to MTS log name
            print('[DB...BAT] Display Y name: {}'.format(y_log_name))
            y_log_name = self._nexus_mtd_log_name_map[y_log_name]
            print('[DB...BAT] Mapped to {}'.format(y_log_name))
            if x_log_name != 'Time':
                x_log_name = self._nexus_mtd_log_name_map[x_log_name]

            # get data: X and Y
            if x_log_name == 'Time':
                start_vec_x = self._sliced_log_dict[run_number]['start'][1]['Time [sec]'].values
            else:
                start_vec_x = self._sliced_log_dict[run_number]['start'][1][x_log_name].values
            # END-IF-ELSE
            start_vec_y = self._sliced_log_dict[run_number]['start'][1][y_log_name].values

            # plot 1 line for all
            plot_label = '{}: Start'.format(base_plot_label)
            self._chopped_start_log_id = self.ui.graphicsView_logPlot.plot_chopped_log(start_vec_x, start_vec_y,
                                                                                       x_log_name, y_log_name,
                                                                                       plot_label)

        elif self.ui.radioButton_plotDetailedSlicedLog.isChecked() and True:  # Data not in memory
            # Plot sliced sample logs in details (all data points)
            try:
                log_file_tuples = self._myController.archive_manager.locate_sliced_h5_logs(
                    ipts_number, run_number)
                log_value_dict = self.load_chopped_h5_logs(log_file_tuples)
                self.set_sliced_h5_logs(log_value_dict)
            except RuntimeError as run_err:
                GuiUtility.pop_dialog_error(self, 'IPTS-{} Run-{} is not sliced with supported to h5-log files'
                                                  ': {}.'
                                                  ''.format(ipts_number, run_number, run_err))
                return

            # Note: there is no need to convert name as the display name is same as sample log name (nexus name)

            COLORS = ['red', 'black', 'green', 'yellow', 'black', 'magenta', 'cyan']
            COLORSNUM = len(COLORS)

            for chop_index in sorted(self._sliced_h5_log_dict.keys()):
                # get data
                vec_y = self._sliced_h5_log_dict[chop_index][y_log_name][1]

                if x_log_name == 'Time':
                    vec_time = self._sliced_h5_log_dict[chop_index][y_log_name][0]
                    vec_splitter_time, vec_splitter_value = self._sliced_h5_log_dict[chop_index]['splitter']
                    vec_x, vec_y = self.process_sliced_log(
                        vec_time, vec_y, vec_splitter_time, vec_splitter_value)

                    # add a vector along with splitter
                    num_splitters = vec_splitter_time.shape[0] - 1
                    # for step function
                    max_y = vec_y.max()
                    min_y = vec_y.min()
                    step_vec_x = numpy.ndarray(
                        shape=(num_splitters * 2 + 1,), dtype=vec_splitter_time.dtype)
                    step_vec_y = numpy.ndarray(shape=step_vec_x.shape, dtype='float')

                    # set up step function: times
                    step_vec_x[::2] = vec_splitter_time  # original splitter time
                    # shorter than a pulse... good enough
                    step_vec_x[1::2] = step_vec_x[2::2] - 0.001
                    step_vec_y[0::4] = step_vec_y[1::4] = min_y
                    step_vec_y[2::4] = step_vec_y[3::4] = max_y

                else:
                    # plot log vs log
                    vec_x = self._sliced_h5_log_dict[chop_index][y_log_name][1]
                    vec_time_x = self._sliced_h5_log_dict[chop_index][y_log_name][0]
                    vec_time_y = self._sliced_h5_log_dict[chop_index][y_log_name][0]
                    vec_x, vec_y = vulcan_util.map_2_logs(vec_time_x, vec_x, vec_time_y, vec_y)

                    step_vec_x = step_vec_y = None
                # END-IF-ELSE

                # plot 1 line for all
                plot_label = '{}: Slice-index = {}'.format(base_plot_label, chop_index)
                color_i = COLORS[chop_index % COLORSNUM]
                if step_vec_x is None:
                    log_plot_id_i = self.ui.graphicsView_logPlot.plot_chopped_log(vec_x, vec_y,
                                                                                  x_log_name, y_log_name,
                                                                                  plot_label,
                                                                                  color_i)
                else:
                    log_plot_id_i = self.ui.graphicsView_logPlot.add_plot_1d(step_vec_x, step_vec_y,
                                                                             label=plot_label, show_legend=True,
                                                                             color=color_i, line_style='--')
                # END-IF-ELSE
                self._curr_log_sliced_dict[chop_index] = log_plot_id_i

            # END-FOR

        else:
            # From memory:
            raise NotImplementedError(
                'It has not been implemented to load sliced logs from memory/workspaces')

            # workspace_key = str(self.ui.comboBox_chopSeq.currentText())
            # workspace_key_list = [workspace_key]
            #
            # for workspace_key in workspace_key_list:
            #     # get the name of the workspace containing sample logs
            #     if workspace_key in self._choppedSampleDict:
            #         # this is for loaded GSAS and NeXus file
            #         sample_key = self._choppedSampleDict[workspace_key]
            #     else:
            #         # just reduced workspace
            #         sample_key = workspace_key
            #
            #     # get the sample log time and value
            #     vec_times, vec_value = self._myController.get_sample_log_values(
            #         sample_key, sample_name, relative=True)
            #
            #     # plot
            #     self.ui.graphicsView_logPlot.plot_sample_data(
            #         vec_times, vec_value, workspace_key, sample_name)
            #     # END-FOR
        # END-FOR

        return

    # TODO - TODAY - TEST!
    def do_plot_sample_log_raw(self):
        """ Plot selected sample logs:
        Workflow:
        1. get log X and Y;
        2. if single: ...
        3. if chopped: (1) plot original (2) plot the selected section
        :return:
        """
        # get log name to plot and reset the sliced log if necessary
        x_log_name, y_log_name = self.get_sample_logs_to_plot()
        if x_log_name != self._curr_log_x_name or y_log_name != self._curr_log_y_name:
            # different
            self.reset_sliced_log()

        # case for single run or original of chopped runs
        if x_log_name == 'Time':
            # get vec times (i.e., vec_log_x)
            vec_log_x, vec_log_y = self._myController.get_sample_log_values(data_key=self._log_data_key,
                                                                            log_name=y_log_name,
                                                                            start_time=None, stop_time=None,
                                                                            relative=True)
        else:
            vec_times, vec_log_x, vec_log_y = self._myController.get_2_sample_log_values(data_key=self._log_data_key,
                                                                                         log_name_x=x_log_name,
                                                                                         log_name_y=y_log_name,
                                                                                         start_time=None,
                                                                                         stop_time=None)
        # END-IF-ELSE

        # plot
        plot_label = '{} {}'.format(self._iptsNumber, self._currRunNumber)
        self._curr_log_raw_plot_id = self.ui.graphicsView_logPlot.plot_sample_log(vec_log_x, vec_log_y,
                                                                                  plot_label=plot_label,
                                                                                  sample_log_name_x=x_log_name,
                                                                                  sample_log_name=y_log_name)
        self._curr_log_x_name = x_log_name
        self._curr_log_y_name = y_log_name

        return

    def get_sample_logs_to_plot(self):
        # get sample logs: from display name to log name in workspace.run()
        # convert from display name to log name
        display_name_x = str(self.ui.comboBox_sampleLogsList_x.currentText()).strip()
        if display_name_x == '':
            GuiUtility.pop_dialog_error(self, 'Log not loaded yet')
            return
        elif display_name_x.startswith('Time'):
            curr_x_log_name = 'Time'
        else:
            curr_x_log_name = self._log_display_name_dict[display_name_x]

        display_name_y = str(self.ui.comboBox_sampleLogsList_y.currentText()).strip()
        curr_y_log_name = self._log_display_name_dict[display_name_y]

        return curr_x_log_name, curr_y_log_name

    @staticmethod
    def process_sliced_log_v2(vec_time, vec_y, vec_splitter_time, vec_splitter_value):
        # TODO - TONIGHT 0 -
        # TODO ... (1) plot a step function of splitter with height as start/stop data sample logs!

        return

    @staticmethod
    def process_sliced_log(vec_time, vec_y, vec_splitter_time, vec_splitter_value):
        """
        Split log from Mantid will have 1 entry before split start time and 1 entry after split stop time.
        It has a bad effect on plotting especially when there are very few data points, because
        a large portion of sample points overlap between two sliced data sets.
        Therefore, use the True/False from splitter (log) to clearly define the first and last value of the splitter
        :param vec_time:
        :param vec_y:
        :param vec_splitter_time:
        :param vec_splitter_value:
        :return:
        """
        # filter out the cases that are not considered
        if vec_splitter_value.shape[0] % 2 != 1 or vec_splitter_value[0] > 0.1:
            raise NotImplementedError('Case not considered')

        for i_splitter in range(vec_splitter_time.shape[0]/2):
            # splitter start time
            start_time_i = vec_splitter_time[i_splitter*2+1]
            stop_time_i = vec_splitter_time[i_splitter*2+2]

            log_t0_index, log_tf_index = numpy.searchsorted(vec_time, [start_time_i, stop_time_i])
            if log_t0_index > 0:
                log_t0_index -= 1  # start one shall be on the left side of found index
            # print ('[...................DB DAT] Index {} Time {} --> {}'.format(log_t0_index, vec_time[log_t0_index],
            #                                                                     start_time_i))
            # print ('[...................DB DAT] Index {} Time {} --> {}'.format(log_tf_index, vec_time[log_tf_index],
            #                                                                     stop_time_i))
            vec_time[log_t0_index] = start_time_i
            vec_time[log_tf_index] = stop_time_i
            vec_y[log_tf_index] = vec_y[log_tf_index-1]  # shall extend from REAL last value
        # END-FOR

        return vec_time, vec_y

    def reset_raw_log(self):
        if self._curr_log_raw_plot_id is not None:
            self.ui.graphicsView_logPlot.remove_line(self._curr_log_raw_plot_id)
            self._curr_log_raw_plot_id = None

        return

    def reset_sliced_log(self):
        for slice_id in self._curr_log_sliced_dict:
            if self._curr_log_sliced_dict[slice_id] is not None:
                self.ui.graphicsView_logPlot.remove_line(self._curr_log_sliced_dict[slice_id])
                del self._curr_log_raw_plot_id[slice_id]
        return

    def do_refresh_existing_runs(self):
        """ Refresh the existing runs in both of the combo box
        The original set up will be preserved.
        There won't be any operation to plot
        :return:
        """
        # single runs
        self._mutexRunNumberList = True

        # Update single runs
        curr_single_names, prev_single_names = self.update_single_run_combo_box()

        # release
        self._mutexRunNumberList = False

        # make sure nothing will be plot
        self._mutexChopRunList = True
        self._mutexChopSeqList = True

        # Update chopped runs
        curr_chop_names, prev_chop_names = self.update_chopped_run_combo_box()

        # release
        self._mutexChopRunList = False
        self._mutexChopSeqList = False

        # # could be an integer as run number: convert to string
        # if isinstance(set_to, int):
        #     set_to = str(set_to)
        # if isinstance(set_to_seq, int):
        #     set_to_seq = '{}'.format(set_to_seq)
        #
        # datatypeutility.check_bool_variable('Flag to indicate whether the next will be set to chopped runs'
        #                                     'single run', is_chopped)

        # TODO - TONIGHT 191 - ....
        # .. get current name

        # TODO - TONIGHT 191 - ....
        # .. set back to current name (if existed)

        # # focus on
        # if set_to is not None and not is_chopped:
        #     # need to set the combo index to the specified SINGLE run
        #     self.ui.radioButton_chooseSingleRun.setChecked(True)
        #     if is_data_key:
        #         for combo_name in self._single_combo_data_key_dict.keys():
        #             if self._single_combo_data_key_dict[combo_name] == set_to:
        #                 set_to = combo_name
        #                 break
        #     new_single_index = self._single_combo_name_list.index(set_to)
        #     self.ui.comboBox_runs.setCurrentIndex(new_single_index)  # this will trigger the event to plot!
        #
        # elif set_to is not None and is_chopped:
        #     # need to update the focus to chopped run and plot
        #     self.ui.radioButton_chooseChopped.setChecked(True)
        #     # NOTE: be careful about non-existing chop name and seq name
        #     if set_to in self._chop_combo_name_list:
        #         new_chop_index = self._chop_combo_name_list.index(set_to)
        #         self.ui.comboBox_choppedRunNumber.setCurrentIndex(new_chop_index)
        #         # this will trigger the event to plot
        #         if set_to_seq in self._chop_seq_combo_name_list:
        #             new_seq_index = self._chop_seq_combo_name_list.index(set_to_seq)
        #             self.ui.comboBox_chopSeq.setCurrentIndex(new_seq_index)
        #         else:
        #             GuiUtility.pop_dialog_error(self, 'Failed to set chopped run {} to seq {}. Reason: {}'
        #                                               ' does not exist in chopped sequences'
        #                                               ''.format(set_to, set_to_seq, set_to_seq))
        #             # self._mutexChopRunList = False
        #             # self._mutexChopSeqList = False
        #             return
        #     else:
        #         GuiUtility.pop_dialog_error(self, '{} does not exist in chopped runs'.format(set_to))
        #         self._mutexChopRunList = False
        #         self._mutexChopSeqList = False
        #         return

        # END

        return curr_single_names, prev_single_names, curr_chop_names, prev_chop_names

    def set_chopped_run(self, chop_run_name, slice_sequence_name):
        """ Set the chopped run (name) to a specified value.
        NO PLOT! SO client needs to call plot explicitly
        :param chop_run_name: If None, then, current one
        :param slice_sequence_name:
        :return:
        """
        datatypeutility.check_string_variable('Slice sequence name', slice_sequence_name)

        # lock
        self._mutexChopRunList = True

        # set radio button
        # TODO - TONIGHT 191 - Need event handler for changing radio button (mutex too)
        self.ui.radioButton_chooseChopped.setChecked(True)

        if chop_run_name is None:
            # use the current name
            chop_run_name = str(self.ui.comboBox_choppedRunNumber.currentText())
            print('[.....] current name = {} / {}'
                  ''.format(chop_run_name, self.ui.comboBox_choppedRunNumber.currentIndex()))

            # exception for empty box
            if chop_run_name == '':
                self._mutexChopRunList = False
                raise RuntimeError('Chopped run number (combo box) is empty')

        elif chop_run_name in self._chop_combo_name_list:
            # focus to the new one
            item_index = self._chop_combo_name_list.index(chop_run_name)

            print('[.....] target name = {}, focus to {}... combo name list: {}'
                  ''.format(chop_run_name, item_index, self._chop_combo_name_list))

            self.ui.comboBox_choppedRunNumber.setCurrentIndex(item_index)

        else:
            # exception for wrong chop run name
            self._mutexChopRunList = False
            raise RuntimeError('Chopped run {} does not exist.  Available: {}'
                               ''.format(chop_run_name, self._chop_combo_name_list))

        # END-IF

        # unlock
        self._mutexChopRunList = False

        # sequences
        self._mutexChopSeqList = True  # lock

        chop_run_key = self._chop_combo_data_key_dict[chop_run_name]
        seq_list = self._myController.project.get_chopped_sequence(chop_run_key)
        print('[DB...BAT] Reduced View Chopped sequence of {}: {}'.format(chop_run_key, seq_list))

        # clean combo box
        self.ui.comboBox_chopSeq.clear()

        if len(seq_list) > 0:
            seq_list.sort()

            # update to the chop-sequences
            self._chop_seq_combo_name_list = list()  # clear
            for item_index, seq_i in enumerate(seq_list):
                seq_item_i = '{}'.format(seq_i)
                self.ui.comboBox_chopSeq.addItem(seq_item_i)
                self._chop_seq_combo_name_list.append(seq_item_i)
            # END-FOR
        # END-IF (set chopped sequence)

        if slice_sequence_name in self._chop_seq_combo_name_list:
            seq_index = self._chop_seq_combo_name_list.index(slice_sequence_name)
            self.ui.comboBox_chopSeq.setCurrentIndex(seq_index)
        else:
            print('[WARNING] Unable to focus chop run {} to sequence {}'.format(
                chop_run_name, slice_sequence_name))
            # focus sequence
            # for name in self._chop_seq_combo_name_list:
            #     print (name, type(name))
            # print (slice_sequence_name, type(slice_sequence_name))

        self._mutexChopSeqList = False  # unlock

        # if False:  # TODO FIXME - TODAY 191 - Leave to other methods
        #     # handle the new index to the chop run combo box
        #     if curr_chop_name in self._chop_combo_name_list:
        #         # focus to the original one and no need to change the sequential number
        #         combo_index = self._chop_combo_name_list.index(curr_chop_name)
        #         chop_run_key = self._chop_combo_data_key_dict[curr_chop_name]
        #         self.ui.comboBox_choppedRunNumber.setCurrentIndex(combo_index)
        #         current_seq_item = str(self.ui.comboBox_chopSeq.currentText())
        #     else:
        #         # need to refresh: set to first one
        #         self.ui.comboBox_choppedRunNumber.setCurrentIndex(0)
        #         new_chop_run_name = self._chop_combo_name_list[0]
        #         chop_run_key = self._chop_combo_data_key_dict[new_chop_run_name]
        #         current_seq_item = None
        #     # END-IF-ELSE
        #
        #     # refresh the list
        #
        # # END-IF-ELSE

        return chop_run_key

    # TODO - TODAY 191 - Evaluate whether this method is useful
    def set_general_view(self, set_to=None, set_to_seq=None, is_chopped=False, is_data_key=True):
        """
        :param set_to: run number / combo item name to set to
        :param set_to_seq: sequence index/name to set to
        :param is_chopped: Flag whether it is good to set to chopped data
        :param is_data_key: Flag to indicate that 'set_to' is a data key or a run number/sequence number
        :return:
        """

        # could be an integer as run number: convert to string
        if isinstance(set_to, int):
            set_to = str(set_to)
        if isinstance(set_to_seq, int):
            set_to_seq = '{}'.format(set_to_seq)

        datatypeutility.check_bool_variable('Flag to indicate whether the next will be set to chopped runs'
                                            'single run', is_chopped)

        # focus on
        if set_to is not None and not is_chopped:
            # need to set the combo index to the specified SINGLE run
            self.ui.radioButton_chooseSingleRun.setChecked(True)
            if is_data_key:
                for combo_name in self._single_combo_data_key_dict.keys():
                    if self._single_combo_data_key_dict[combo_name] == set_to:
                        set_to = combo_name
                        break
            new_single_index = self._single_combo_name_list.index(set_to)
            # this will trigger the event to plot!
            self.ui.comboBox_runs.setCurrentIndex(new_single_index)

        elif set_to is not None and is_chopped:
            # need to update the focus to chopped run and plot
            self.ui.radioButton_chooseChopped.setChecked(True)
            # NOTE: be careful about non-existing chop name and seq name
            if set_to in self._chop_combo_name_list:
                new_chop_index = self._chop_combo_name_list.index(set_to)
                self.ui.comboBox_choppedRunNumber.setCurrentIndex(
                    new_chop_index)  # this will trigger the event to plot
                if set_to_seq in self._chop_seq_combo_name_list:
                    new_seq_index = self._chop_seq_combo_name_list.index(set_to_seq)
                    self.ui.comboBox_chopSeq.setCurrentIndex(new_seq_index)
                else:
                    GuiUtility.pop_dialog_error(self, 'Failed to set chopped run {} to seq {}. Reason: {}'
                                                      ' does not exist in chopped sequences'
                                                      ''.format(set_to, set_to_seq, set_to_seq))
                    # self._mutexChopRunList = False
                    # self._mutexChopSeqList = False
                    return
            else:
                GuiUtility.pop_dialog_error(
                    self, '{} does not exist in chopped runs'.format(set_to))
                # self._mutexChopRunList = False
                # self._mutexChopSeqList = False
                return

        return

    def evt_change_bank(self):
        """
        Handling the event that the bank ID is changed: the figure should be re-plot.
        It should be avoided to plot the same data twice against evt_select_new_run_number
        :return:
        """
        # skip if it is locked
        if self._mutexBankIDList:
            return

        # new bank ID
        next_bank = int(self.ui.comboBox_spectraList.currentText())
        plot_data_key = 'NOT SET'

        try:
            if self.ui.radioButton_chooseSingleRun.isChecked():
                # plot single run: as it is a change of bank. no need to re-process data
                plot_data_key = self._curr_data_key
                if plot_data_key in self._single_combo_data_key_dict:
                    pass

                # get the previous setup for vanadium and proton charge normalization or default
                if plot_data_key in self._single_run_plot_option:
                    van_run = self._single_run_plot_option[plot_data_key]['van_run']
                    van_norm = self._single_run_plot_option[plot_data_key]['van_norm']
                    pc_norm = self._single_run_plot_option[plot_data_key]['pc_norm']
                else:
                    van_run = None
                    van_norm = pc_norm = False

                self.plot_single_run(data_key=plot_data_key, bank_id=next_bank,
                                     van_norm=van_norm, van_run=van_run, pc_norm=pc_norm, main_only=True)

            else:
                # chopped data
                curr_chop_name = str(self.ui.comboBox_choppedRunNumber.currentText())
                plot_data_key = self._chop_combo_data_key_dict[curr_chop_name]

                # retrieve previous setup
                if plot_data_key in self._chop_run_plot_option:
                    pc_norm = self._chop_run_plot_option[plot_data_key]['pc_norm']
                    van_norm = self._chop_run_plot_option[plot_data_key]['norm_van']
                    van_run = self._chop_run_plot_option[plot_data_key]['van_run']
                else:
                    pc_norm = van_norm = van_run = None

                # plot
                # TODO - FIXME - TONIGHT - Nothing changed!
                self.plot_chopped_run(chop_key=plot_data_key, bank_id=next_bank,
                                      seq_list=None, main_only=True,
                                      van_norm=van_norm, van_run=van_run, pc_norm=pc_norm, plot3d=False)
            # END-IF-ELSE
        except RuntimeError as run_err:
            # reset to previous state
            self._mutexBankIDList = True
            GuiUtility.set_combobox_current_item(self.ui.comboBox_spectraList, '{}'.format(self._currBank),
                                                 False)
            self._mutexBankIDList = False
            GuiUtility.pop_dialog_error(self, 'Unable to switch to bank {1} (data key {0} exists) due to {2}'
                                              ''.format(plot_data_key, next_bank, run_err))
            return

        # successful and set current bank to new/next bank
        self._currBank = next_bank

        return

    def evt_change_unit(self):
        """
        Purpose: Re-plot the current plots with new unit in Main graphics view
        :return:
        """
        # # Clear previous image and re-plot
        # self.ui.graphicsView_mainPlot.reset_1d_plots()

        # about X range: save current X range setup
        curr_x_min = GuiUtility.parse_float(self.ui.lineEdit_minX, True)
        curr_x_max = GuiUtility.parse_float(self.ui.lineEdit_maxX, True)
        self._xrange_dict[self._currUnit] = curr_x_min, curr_x_max

        # set new unit and X range of new unit
        self._currUnit = str(self.ui.comboBox_unit.currentText())
        if self._currUnit in self._xrange_dict:
            next_x_min, next_x_max = self._xrange_dict[self._currUnit]
        else:
            next_x_min = next_x_max = None

        if next_x_min:
            self.ui.lineEdit_minX.setText('{}'.format(next_x_min))
        else:
            self.ui.lineEdit_minX.setText('')

        if next_x_max:
            self.ui.lineEdit_maxX.setText('{}'.format(next_x_max))
        else:
            self.ui.lineEdit_maxX.setText('')

        # plot
        if self.ui.radioButton_chooseSingleRun.isChecked():
            # single run
            if self._curr_data_key:
                # get the previous setup for vanadium and proton charge normalization or default
                if self._curr_data_key in self._single_run_plot_option:
                    van_run = self._single_run_plot_option[self._curr_data_key]['van_run']
                    van_norm = self._single_run_plot_option[self._curr_data_key]['van_norm']
                    pc_norm = self._single_run_plot_option[self._curr_data_key]['pc_norm']
                else:
                    van_run = None
                    van_norm = pc_norm = False

                self.plot_single_run(self._curr_data_key, van_norm=van_norm, van_run=van_run,
                                     pc_norm=pc_norm, bank_id=self._currBank, main_only=False)

        else:
            # chopped data
            curr_chop_name = str(self.ui.comboBox_choppedRunNumber.currentText())
            if curr_chop_name != '':
                plot_data_key = self._chop_combo_data_key_dict[curr_chop_name]
                # retrieve previous setup
                if plot_data_key in self._chop_run_plot_option:
                    pc_norm = self._chop_run_plot_option[plot_data_key]['pc_norm']
                    van_norm = self._chop_run_plot_option[plot_data_key]['norm_van']
                    van_run = self._chop_run_plot_option[plot_data_key]['van_run']
                else:
                    pc_norm = van_norm = van_run = None

                self.plot_chopped_run(chop_key=plot_data_key, bank_id=self._currBank,
                                      seq_list=None, main_only=True,
                                      van_norm=van_norm, van_run=van_run, pc_norm=pc_norm, plot3d=False)
                # END-IF-ELSE
        # END-IF-ELSE

        return

    def evt_change_data_source(self):
        """
        handling event that the location of reduced data to load from is changed
        :return:
        """
        def set_load_from_archive_enabled(enabled):
            """
            set the widgets to load data from archive to be enabled or disabled
            :param enabled:
            :return:
            """
            self.ui.lineEdit_iptsNumber.setEnabled(enabled)
            self.ui.lineEdit_run.setEnabled(enabled)

            return

        def set_load_from_hdd_enabled(enabled):
            """
            enable or disable widgets for loading GSAs from HDD
            :param enabled:
            :return:
            """
            self.ui.lineEdit_gsasFileName.setEnabled(enabled)
            # TODO FIXME - TONIGHT - where is this button?   self.ui.pushButton_browseAnyGSAS.setEnabled(enabled)

            return

        set_load_from_archive_enabled(self.ui.radioButton_fromArchive.isChecked())
        set_load_from_hdd_enabled(self.ui.radioButton_anyGSAS.isChecked())

        return

    def evt_plot_different_single_run(self):
        """ Event handling the case that a new run number is selected in combobox_run
        :return:
        """
        # skip if it is locked
        if self._mutexRunNumberList:
            return

        # plot diffraction data same as
        self.do_plot_diffraction_data(True)

        return

    def evt_toggle_plot_options(self):
        """
        handling event as radioButton choose diffraction to plot or choose sample log to plot
        :return:
        """
        if self.ui.radioButton_chooseSingleRun.isChecked():
            plot_diffraction = True
        else:
            plot_diffraction = False

        self.ui.groupBox_plotREducedData.setEnabled(plot_diffraction)
        self.ui.groupBox_plotLog.setEnabled(not plot_diffraction)

        return

    def evt_toggle_run_type(self):
        """ Change between plotting single run or chopped run
        :return:
        """
        self.ui.groupBox_plotSingleRun.setEnabled(self.ui.radioButton_chooseSingleRun.isChecked())
        self.ui.groupBox_plotChoppedRun.setEnabled(self.ui.radioButton_chooseChopped.isChecked())

        return

    def evt_plot_different_chopped_run(self):
        """
        Handle the event if there is a change in chopped run to plot
        :return:
        """
        print('[DB.............BAT] Chopped run is changed... size = {}'
              ''.format(self.ui.comboBox_choppedRunNumber.size()))

        # skip if mutex is on
        if self._mutexChopRunList is True:
            return

        # get current chop name
        curr_chop_name = str(self.ui.comboBox_choppedRunNumber.currentText())
        if curr_chop_name == '':
            print('[DB...BAT] Is ChoppedRun combo box empty? {}'
                  ''.format(self.ui.comboBox_choppedRunNumber.size()))
            return

        curr_data_key = self._chop_combo_data_key_dict[curr_chop_name]

        chopped_sequence_list = self._myController.project.get_chopped_sequence(curr_data_key)

        # clear
        self._mutexChopSeqList = True
        self.ui.comboBox_chopSeq.clear()
        self._chop_seq_combo_name_list = list()
        self._mutexChopSeqList = False

        # plot the first one
        print('[DB...BAT] Tending to update/plot run {} chop-seq {}'.format(curr_chop_name,
                                                                            chopped_sequence_list[0]))
        if len(chopped_sequence_list) > 0:
            seq_name_0 = '{}'.format(chopped_sequence_list[0])
            self.ui.comboBox_chopSeq.addItem(seq_name_0)
        # END-IF-ELSE

        # plot the others
        self._mutexChopSeqList = True
        for item_index in range(1, len(chopped_sequence_list)):
            seq_name_i = '{}'.format(chopped_sequence_list[item_index])
            self.ui.comboBox_chopSeq.addItem(seq_name_i)
            self._chop_seq_combo_name_list.append(seq_name_i)
        self._mutexChopSeqList = False

        return

    def evt_plot_different_chopped_sequence(self):
        """
        Handle the event if there is change in chopped sequence list
        :return:
        """
        if self._mutexChopSeqList:
            return

        # chopped data
        curr_chop_name = str(self.ui.comboBox_choppedRunNumber.currentText())
        chop_data_key = self._chop_combo_data_key_dict[curr_chop_name]
        # retrieve previous setup
        if chop_data_key in self._chop_run_plot_option:
            pc_norm = self._chop_run_plot_option[chop_data_key]['pc_norm']
            van_norm = self._chop_run_plot_option[chop_data_key]['norm_van']
            van_run = self._chop_run_plot_option[chop_data_key]['van_run']
        else:
            pc_norm = van_norm = van_run = None

        self.plot_chopped_run(chop_key=chop_data_key, bank_id=self._currBank,
                              seq_list=None, main_only=True,
                              van_norm=van_norm, van_run=van_run, pc_norm=pc_norm, plot3d=False)
        return

    def get_data_key(self, run_number, chop_seq):
        """
        Get the data-key for a run and chop sequence
        :param run_number:
        :param chop_seq:
        :return: data key
        """
        if chop_seq is None:
            if run_number not in self._single_run_data_dict:
                raise KeyError('{} not among self._single_run_data_dict keys {}'
                               ''.format(run_number, self._single_run_data_dict.keys()))
            data_key = self._single_run_data_dict[run_number]
        else:
            # for chopped run, run number + chop sequence index is the key
            if run_number not in self._chopped_run_data_dict:
                raise KeyError('{} not among self._chopped_run_data_dict keys {}'
                               ''.format(run_number, self._chopped_run_data_dict.keys()))
            if chop_seq not in self._chopped_run_data_dict[run_number]:
                raise KeyError('{} not among self._chopped_run_data_dict[{}] {}'
                               ''.format(chop_seq, run_number, self._chopped_run_data_dict[run_number]))
            data_key = run_number
        # END-IF-ELSE

        return data_key

    def get_proton_charge(self, ipts_number, run_number, chop_seq):
        """ get proton charge (summed) of a run
        :param ipts_number:
        :param run_number:
        :param chop_seq:
        :return:
        """
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 999999))
        datatypeutility.check_int_variable('Run number', run_number, (1, 99999999))

        if chop_seq is None:
            # single run
            try:
                log_data_set = self._sample_log_dict[ipts_number][run_number]
                pc_vec = log_data_set['ProtonCharge']
                run_vec = log_data_set['RUN']
            except KeyError as key_err:
                GuiUtility.pop_dialog_error(self, 'Unable to retrieve sample log IPTS-{} Run-{}. FYI: {}'
                                                  ''.format(ipts_number, run_number, key_err))
                return

            row_index = numpy.where(run_vec == run_number)
            row_index = row_index[0][0]

            total_pc = pc_vec[row_index]
        else:
            chop_index = chop_seq - 1
            total_pc = self._sliced_log_dict[run_number]['start'][1]['ProtonCharge'][chop_index]

        return total_pc

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

    def has_data_loaded(self, run_number, chop_seq_index):
        """ Check whether a data set has been loaded from GSAS or not
        :param run_number:
        :param chop_seq_index:
        :return:
        """
        if chop_seq_index is None:
            # original run
            return run_number in self._single_run_data_dict
        elif run_number not in self._chopped_run_data_dict:
            # chopped run
            return False

        # chopped run
        datatypeutility.check_int_variable('Chop sequence index', chop_seq_index, (0, None))

        return chop_seq_index in self._chopped_run_data_dict[run_number]

    def init_setup(self, controller):
        """ Set up the GUI from controller, and add reduced runs to SELF automatically
        :param controller:
        :return:
        """
        # Check
        # assert isinstance(controller, VDriveAPI)
        self._myController = controller
        self.do_refresh_existing_runs()

        return

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
            assert isinstance(
                chop_seq_list, list), 'If is chopped data, then neec to give chop sequence list.'
            chop_seq_list.sort()
            label_str += ': chopped sequence {0} - {1}'.format(chop_seq_list[0], chop_seq_list[-1])

        self.ui.label_currentRun.setText(label_str)

        return

    def load_reduced_data(self, ipts_number, run_number, chop_seq_index_list):
        """
        Load reduced data
        :param ipts_number:
        :param run_number: can (1) run number (int) or None (loading explicitly)
        :param chop_seq_index_list:
        :return: 2-tuple (1) data key  or  dictionary of keys  (2) loaded chop-sequence indexes
        """
        if chop_seq_index_list is None:
            # original run
            if run_number is not None and self._is_run_in_memory(run_number):
                # load from memory
                data_key = self._myController.project.reduction_manager.get_reduced_workspace(
                    run_number)
            else:
                # load from archived disk
                reduced_file_name = self._myController.archive_manager.get_gsas_file(ipts_number, run_number,
                                                                                     check_exist=True)
                file_type = 'gsas'
                data_key = self._myController.project.data_loading_manager.load_binned_data(reduced_file_name,
                                                                                            file_type,
                                                                                            max_int=99999)
            # END-IF-ELSE

            # register
            self._single_run_data_dict[run_number] = data_key
            self._data_key_run_seq[data_key] = run_number, None

            load_seq_list = None

        else:
            # chopped run
            datatypeutility.check_list('Chopped sequence indexes', chop_seq_index_list)
            chopped_data_dir = self._myController.get_archived_data_dir(ipts_number, run_number,
                                                                        chopped_data=True)
            file_loading_manager = self._myController.project.data_loading_manager
            data_set_dict, load_seq_list = file_loading_manager.load_chopped_binned_data(run_number, chopped_data_dir,
                                                                                         chop_seq_index_list,
                                                                                         'gsas')

            # record
            if run_number not in self._chopped_run_data_dict:
                # if never been added: add a new list considering the case of loading chop indexes a few at a time
                # but for many times
                self._chopped_run_data_dict[run_number] = list()
            self._chopped_run_data_dict[run_number].extend(
                data_set_dict.keys())  # run number + seq index --> find it!

            for key in self._chopped_run_data_dict[run_number]:
                print(key, type(key))

            data_key = data_set_dict
        # END-IF-ELSE

        # # register
        # vdrive_constants.run_ipts_dict[run_number] = ipts_number

        return data_key, load_seq_list

    @staticmethod
    def load_chopped_h5_logs(log_h5_gda_tuples):
        """ Load a list of chopped files
        :param log_h5_gda_tuples:
        :return:
        """
        datatypeutility.check_list('Sample log (h5) and gda file tuples', log_h5_gda_tuples)

        sample_log_dict = dict()
        for log_file, gda_file in log_h5_gda_tuples:
            base_gda = gda_file.split('.')[0]
            if base_gda.isdigit():
                chop_index = int(base_gda)
            else:
                chop_index = base_gda

            log_dict_i = file_utilities.load_sample_logs_h5(log_file, None)

            sample_log_dict[chop_index] = log_dict_i
        # END-FOR

        return sample_log_dict

    def retrieve_loaded_reduced_data(self, data_key, ipts_number, run_number, chop_seq_index,
                                     bank_id, unit, pc_norm, van_run):
        """
        Retrieve reduced data from workspace (via run number) to _reducedDataDict.
        Note: this method is used to talk with myController
        :param data_key: a run number (int or string) or data key (i..e, workspace name) or a tuple for chopped run
        :param bank_id:
        :param unit:
        :return:
        """
        assert data_key is not None, 'Data key must be initialized'

        # vanadium or PC
        if pc_norm:
            pc_seq = self.get_proton_charge(ipts_number, run_number, chop_seq_index)
        else:
            pc_seq = 1

        # vanadium
        if van_run is None:
            van_vec_y = None
        else:
            van_vec_y = self.get_vanadium_spectrum(van_run, bank_id)

        # plot on the main figure
        if chop_seq_index is not None:
            vec_x, vec_y = self._myController.project.get_chopped_sequence_data(data_key, chop_seq_index,
                                                                                bank_id, unit)
        else:
            # raw GSAS
            print(type(data_key))
            print(data_key)
            data_set = self._myController.get_reduced_data(
                run_id=data_key, target_unit=unit, bank_id=bank_id)
            # convert to 2 vectors
            vec_x = data_set[bank_id][0]
            vec_y = data_set[bank_id][1]
        # END-IF-ELSE

        vec_y /= pc_seq
        if van_vec_y is not None:
            vec_y /= van_vec_y

        return vec_x, vec_y

    def launch_single_run_view(self):
        """ Launch a reduced data view window for single run
        :return:
        """
        view_window = AtomicReduced1DViewer(self)
        view_window.show()

        self._atomic_viewer_list.append(view_window)

        return view_window

    def launch_contour_view(self):
        """ Launch a reduced data view window for multiple runs (chopped or single) in contour plot
        :return:
        """
        view_window = AtomicReduction2DViewer(self)
        view_window.show()

        self._atomic_viewer_list.append(view_window)

        return view_window

    def launch_3d_view(self):
        """ Launch a reduced data view window for multiple runs (chopped or single) in 3d line plot
        :return:
        """
        view_window = AtomicReduction3DViewer(self)
        view_window.show()

        self._atomic_viewer_list.append(view_window)

        return view_window

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

    def get_vanadium_spectrum(self, van_run, bank_id):

        from pyvdrive.core import mantid_helper
        print('[DB...BAT] Vanadium workspace = {}'.format(self._vanadium_dict[van_run]))
        van_ws_name = self._vanadium_dict[van_run]
        mantid_helper.mtd_convert_units(van_ws_name, 'dSpacing')
        van_ws = mantid_helper.retrieve_workspace(van_ws_name, True)
        if van_ws.id() == 'WorkspaceGroup':
            van_vec_y = van_ws[bank_id - 1].readY(0)
        else:
            van_vec_y = van_ws.readY(bank_id - 1)

        return van_vec_y

    def plot_single_run(self, data_key, van_norm, van_run, pc_norm, bank_id=1, main_only=False):
        """
        Plot a single run
        :param data_key:
        :param bank_id:
        :param van_norm:
        :param van_run:
        :param pc_norm:
        :param main_only:
        :return:
        """
        # check inputs
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 99))

        # set current data key
        self._curr_data_key = data_key
        if van_norm:
            van_run_temp = van_run
        else:
            van_run_temp = None

        # get the entry index for the data
        # entry_key = data_key, bank_id, self._currUnit
        vec_x, vec_y = self.retrieve_loaded_reduced_data(data_key=data_key, ipts_number=self._iptsNumber,
                                                         run_number=self._currRunNumber,
                                                         chop_seq_index=None,
                                                         bank_id=bank_id,
                                                         unit=self._currUnit, pc_norm=pc_norm,
                                                         van_run=van_run_temp)
        # if pc_norm:
        #     # proton charge normalization
        #     pc_norm = self.get_proton_charge(self._iptsNumber, self._currRunNumber, None)
        #     vec_y /= pc_norm
        # if van_norm:
        #     # vanadium spectrum normalization
        #     van_vec_y = self.get_vanadium_spectrum(van_run, bank_id)
        #     vec_y /= van_vec_y
        #     # END-IF

        self._single_run_plot_option[data_key] = {'pc_norm': pc_norm,
                                                  'van_run': van_run,
                                                  'van_norm': van_norm}

        # clear existing line
        if self._currentPlotID:
            self.ui.graphicsView_mainPlot.remove_line(self._currentPlotID)
            self._currentPlotID = None

        line_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y), unit=self._currUnit,
                                                                      over_plot=False,
                                                                      run_id=data_key, bank_id=bank_id,
                                                                      chop_tag=None,
                                                                      label='{}, {}'.format(data_key, bank_id))
        self.ui.graphicsView_mainPlot.set_title(title='{}'.format(data_key))
        self._currentPlotID = line_id

        # deal with Y axis
        self.ui.graphicsView_mainPlot.auto_rescale()
        # about X
        curr_min_x, curr_max_x = self.do_set_x_range()

        # pop the child atomic window
        if not main_only:
            status, bank_ids = self._myController.get_reduced_run_info(
                run_number=None, data_key=data_key)
            if not status:
                raise NotImplementedError('It is not possible to unable to get reduced run info!')

            run_number, none = self._data_key_run_seq[data_key]
            # FIXME TODO FUTURE - This could be an issue for Not-3 bank data
            for bank_id_i in sorted(bank_ids):
                child_window = self.launch_single_run_view()
                vec_x, vec_y = self.retrieve_loaded_reduced_data(data_key=data_key, ipts_number=self._iptsNumber,
                                                                 run_number=self._currRunNumber,
                                                                 chop_seq_index=None,
                                                                 bank_id=bank_id_i,
                                                                 unit=self._currUnit, pc_norm=pc_norm,
                                                                 van_run=van_run_temp)
                # if pc_norm:
                #     # proton charge normalization
                #     pc_norm = self.get_proton_charge(self._iptsNumber, self._currRunNumber, None)
                #     vec_y /= pc_norm
                # if van_norm:
                #     # vanadium normalization
                #     van_vec_y = self.get_vanadium_spectrum(van_run, bank_id)
                #     vec_y /= van_vec_y
                #     # END-IF

                child_window.set_x_range(curr_min_x, curr_max_x)
                plot_information = PlotInformation(
                    self._iptsNumber, run_number, None, pc_norm, van_run_temp)
                child_window.plot_data(vec_x, vec_y, data_key, self._currUnit,
                                       bank_id_i, plot_information)
            # END-FOR
        # END-IF

        return

    def plot_chopped_run(self, chop_key, bank_id, seq_list, van_norm, van_run, pc_norm, main_only, plot3d):
        """
        plot chopped runs
        :param chop_key: (1) integer for loaded run  (2) 2-tuple for in-memory
        :param bank_id: only used for plotting main UI
        :param seq_list:
        :param van_norm:
        :param van_run:
        :param pc_norm:
        :param main_only:
        :return:
        """
        def construct_chopped_data(chop_data_key, chop_sequences, bank_index, do_pc_norm,
                                   do_van_norm, vanadium_vector):
            """
            construct the chopped data into MATRIX to plot contour and 3D
            :param chop_data_key: get_chopped_sequence_data(chop_data_key, seq)
            :param chop_sequences:
            :param bank_index:
            :param do_pc_norm:
            :param do_van_norm:
            :param vanadium_vector:
            :return: 2-tuple: chopped sequence list and data set list
            """
            # construct input for contour plot
            data_sets = list()
            new_seq_list = list()
            error_msg = ''
            for chop_seq_i in chop_sequences:
                try:
                    data = self._myController.project.get_chopped_sequence_data(chop_data_key, chop_seq_i,
                                                                                bank_index)
                    vec_x_i, vec_y_i = data

                    # normalize by proton charge
                    if do_pc_norm:
                        p_charge_i = self.get_proton_charge(
                            self._iptsNumber, self._currRunNumber, chop_seq_i)
                        vec_y_i /= p_charge_i
                    # normalize by vanadium spectrum
                    if do_van_norm:
                        vec_y_i /= vanadium_vector

                    data_sets.append((vec_x_i, vec_y_i))
                    new_seq_list.append(chop_seq_i)
                except (RuntimeError, KeyError) as run_err_i:
                    error_msg += 'Unable to load chopped sequence {}: {}\n'.format(
                        chop_seq_i, run_err_i)
            # END-FOR

            if len(new_seq_list) == 0:
                raise RuntimeError('There is no available data from {}:\n{}'.format(
                    chop_data_key, error_msg))
            if error_msg != '':
                GuiUtility.pop_dialog_error(self, error_msg)

            # check ... FIXME TODO - TONIGHT 0 - delete this session after debugging/problem being fixed
            for data_set in data_sets:
                print('min = {} @ {},  max = {} @ {}'
                      ''.format(data_set[1].min(), numpy.argmin(data_set[1]),
                                data_set[1].max(), numpy.argmax(data_set[1])))

            return new_seq_list, data_sets

        def get_single_bank_data(chop_run_key, curr_seq_index, bank_id_i, do_pc_norm, proton_charge,
                                 do_van_norm, van_vector_bank_i):
            """ retrieve data for a single bank
            :return:
            """
            # TODO - FIXME - TONIGHT 0 - unit as TOF shall be passed to this level with evt_unit_changed...
            vec_data_x, vec_data_y = self._myController.project.get_chopped_sequence_data(chop_run_key,
                                                                                          curr_seq_index,
                                                                                          bank_id_i,
                                                                                          unit='dSpacing')

            # normalization
            if do_pc_norm:
                # normalize by proton charge
                vec_data_y /= proton_charge

            if do_van_norm:
                # vanadium normalization
                vec_data_y /= van_vector_bank_i

            return vec_data_x, vec_data_y

        print('[DB....................BAT.................LOOK] chop data key: {} of type {}'
              ''.format(chop_key, type(chop_key)))
        # check inputs
        datatypeutility.check_int_variable('Bank ID', bank_id, (None, None))
        if pc_norm is None:
            # default
            pc_norm = self._curr_pc_norm
        else:
            datatypeutility.check_bool_variable('Normalize by proton charge', pc_norm)
            self._curr_pc_norm = pc_norm

        # record option
        self._chop_run_plot_option[chop_key] = {'pc_norm': pc_norm,
                                                'norm_van': van_norm,
                                                'van_run': van_run}

        # record the current chopped-sequence
        # TODO - TODAY-TEST 0.191.2 - Implement a method to filter seq_list with get_chopped_sequences()
        existing_seq_list = self._myController.project.get_chopped_sequence(chop_key)

        # check whether any sequence exists
        if len(existing_seq_list) == 0:
            GuiUtility.pop_dialog_error(
                self, 'There is no chopped sequences for (chop key) {}'.format(chop_key))
            return

        if seq_list is None:
            # default is to use all the chopped sequences
            seq_list = existing_seq_list[:]
        else:
            # check whether user-specified sequences do exist
            filtered_seq_list = list()
            non_exist_seqs = list()

            for user_seq in seq_list:
                if user_seq in existing_seq_list:
                    filtered_seq_list.append(user_seq)
                else:
                    non_exist_seqs.append(user_seq)
            # END-FOR
            if len(non_exist_seqs) == len(seq_list):
                GuiUtility.pop_dialog_error(self, 'For (chop key) {}, none of the users specified sequence\n{}\n'
                                                  'exists. \nAvailable sequences are \n{}'
                                                  ''.format(chop_key, seq_list, existing_seq_list))
                return
            elif len(non_exist_seqs) > 0:
                GuiUtility.pop_dialog_error(self, 'For (chop key) {}, the following chopped sequences do not exist:'
                                                  '\n{}'.format(chop_key, non_exist_seqs))
            # assign
            seq_list = filtered_seq_list[:]
        # END-IF-ELSE

        # set current sequence to plot as single pattern
        # NOTE: maybe over-engineered.  But safe is the highest priority
        try:
            # loaded GSAS file... possible non-consecutive integers
            curr_seq = int(str(self.ui.comboBox_chopSeq.currentText()))
            if curr_seq not in seq_list:
                curr_seq = seq_list[0]
        except ValueError:
            # just-reduced run
            curr_seq = seq_list[0]
        # END-TRY

        # vanadium or PC
        if pc_norm:
            pc_seq = self.get_proton_charge(self._iptsNumber, self._currRunNumber, curr_seq)
        else:
            pc_seq = 1

        van_vec_y_dict = {1: None, 2: None, 3: None}
        if van_norm:
            # vanadium normalization
            for bank_id in range(1, 3+1):
                van_vec_y = self.get_vanadium_spectrum(van_run, bank_id)
                van_vec_y_dict[bank_id] = van_vec_y
        # END-IF-ELSE

        # plot on the main figure
        vec_x, vec_y = get_single_bank_data(chop_run_key=chop_key,
                                            curr_seq_index=curr_seq,
                                            bank_id_i=bank_id,
                                            do_pc_norm=pc_norm,
                                            proton_charge=pc_seq,
                                            do_van_norm=van_norm,
                                            van_vector_bank_i=van_vec_y_dict[bank_id])

        plot_label = 'Run {} - {} Bank {}'.format(chop_key, curr_seq, bank_id)

        # clear
        if self._currentPlotID is not None:
            self.ui.graphicsView_mainPlot.remove_line(self._currentPlotID)
            self._currentPlotID = None

        # plot 1D chopped data
        plot_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y), unit=self._currUnit,
                                                                      over_plot=True,
                                                                      run_id=chop_key,
                                                                      bank_id=bank_id,
                                                                      chop_tag='{}'.format(
                                                                          curr_seq),
                                                                      label=plot_label,
                                                                      line_color='black')
        self._currentPlotID = plot_id

        # rescale
        min_x, max_x = self.do_set_x_range()

        # Plot 1D, 2D and/or 3D
        if not main_only:
            # vanadium run?
            if van_norm:
                van_run_tmp = van_run
            else:
                van_run_tmp = None
            # plot 1Ds
            # TODO - FUTURE - This could be an issue for Not-3 bank data
            MAX_BANK = 3
            for bank_id in range(1, MAX_BANK+1):
                child_window = self.launch_single_run_view()
                vec_x, vec_y = get_single_bank_data(chop_run_key=chop_key,
                                                    curr_seq_index=curr_seq,
                                                    bank_id_i=bank_id,
                                                    do_pc_norm=pc_norm,
                                                    proton_charge=pc_seq,
                                                    do_van_norm=van_norm,
                                                    van_vector_bank_i=van_vec_y_dict[bank_id])

                # run number
                if isinstance(chop_key, tuple):
                    run_number = chop_key[0]
                else:
                    run_number = chop_key
                child_window.set_title(
                    'Run {} Chop-index {} Bank {}'.format(run_number, curr_seq, bank_id))
                child_window.set_x_range(min_x, max_x)
                ipts_number = vdrive_constants.run_ipts_dict[run_number]
                plot_information = PlotInformation(
                    ipts_number, run_number, curr_seq, pc_norm, van_run_tmp)
                child_window.plot_data(vec_x, vec_y, chop_key, self._currUnit,
                                       bank_id, plot_information)
            # END-FOR
        # END-IF-NOT (main)

        # set sequence
        if not main_only and len(seq_list) > 1:
            # launch windows for contour plots and 3D line plots
            for bank_id in range(1, 4):  # FIXME TODO FUTURE - This could be an issue for Not-3 bank data
                # data sets
                if van_norm:
                    # vanadium normalization
                    van_vec_y_i = self.get_vanadium_spectrum(van_run, bank_id)
                else:
                    van_vec_y_i = None
                # END-IF
                try:
                    seq_list, data_set_list = construct_chopped_data(chop_key, seq_list, bank_id, pc_norm,
                                                                     van_norm, van_vec_y_i)
                except RuntimeError as run_err:
                    GuiUtility.pop_dialog_error(
                        self, 'Unable to plot chopped data due to {}'.format(run_err))
                    return

                # 2D Contours
                child_2d_window = self.launch_contour_view()
                child_2d_window.set_x_range(min_x, max_x)
                child_2d_window.plot_contour(seq_list, data_set_list)

                # 3D Line
                if plot3d:
                    child_3d_window = self.launch_3d_view()
                    child_3d_window.plot_runs_3d(seq_list, data_set_list)
            # END-FOR
        # END-IF

        return

    def set_logs(self, ipts_number, run_number, log_set):
        """
        set log set (list of log names) to IPTS/RUN
        :param ipts_number:
        :param run_number:
        :param log_set:
        :return:
        """
        if ipts_number not in self._sample_log_dict:
            self._sample_log_dict[ipts_number] = dict()
        self._sample_log_dict[ipts_number][run_number] = log_set  # with head included

        return

    def set_chopped_logs(self, ipts_number, run_number, log_header, log_set, log_id='start'):
        # TODO - TONIGHT 0 - Document! & consider the case of hdf5 logs!
        if run_number not in self._sliced_log_dict[ipts_number]:
            self._sliced_log_dict[run_number] = {'start': None,
                                                 'mean': None, 'end': None, 'IPTS': ipts_number}
        self._sliced_log_dict[run_number][log_id] = log_header, log_set

        return

    def set_sliced_h5_logs(self, sliced_sample_log_dict):
        """

        :param sliced_sample_log_dict:
        :return:
        """
        self._sliced_h5_log_dict = sliced_sample_log_dict

        return

    def set_unit(self, unit):
        """ set unit from external scripts
        This provides a flexible way to set unit from external script.
        Being flexible means that it is not case sensitive and multiple terms (d, dspacing and etc) are
        supported.
        :param unit:
        :return:
        """
        # check inputs
        pyvdrive.core.datatypeutility.check_string_variable('Unit', unit)
        unit = unit.lower()

        ui_supported_units = list()
        for i_text in range(self.ui.comboBox_unit.count()):
            ui_supported_units.append(str(self.ui.comboBox_unit.itemText(i_text)))

        if unit.count('tof') > 0:
            index = ui_supported_units.index('TOF')
        elif unit.startswith('d') or unit.count('spac') > 0:  # consider space or spacing both
            index = ui_supported_units.index('dSpacing')
        elif unit.lower().count('q') > 0 or unit.lower().count('momentum'):
            index = ui_supported_units.index('Q')
        else:
            raise RuntimeError('Unsupported unit {0}'.format(unit))

        # focus the combo box to the correct unit
        self.ui.comboBox_unit.setCurrentIndex(index)

        # also set the current unit in strict/correct term
        set_unit = str(self.ui.comboBox_unit.currentText())

        return set_unit

    def set_vanadium_ws(self, van_run_number, van_ws_name):
        self._vanadium_dict[van_run_number] = van_ws_name

    def resize_canvas(self):
        """
        Resize the canvas if it is necessary
        :return:
        """
        # Init
        min_x = 1.E20
        max_x = -1.E20

        # Find minimum x and maximum x
        for run_number in self._currentPlotDataKeyDict.keys():
            run_data_dict = self._currentPlotDataKeyDict[run_number]
            assert isinstance(run_data_dict, dict)
            for spec_id in run_data_dict.keys():
                vec_x = run_data_dict[spec_id][0]
                min_x = min(min_x, vec_x[0])
                max_x = max(max_x, vec_x[-1])
        # END-FOR

        # Resize the canvas
        self.ui.graphicsView_mainPlot.setXYLimit(xmin=min_x, xmax=max_x)

        return

    def set_ipts_number(self, ipts_number):
        """ set IPTS number
        :param ipts_number:
        :return:
        """
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))

        self._iptsNumber = ipts_number

        return

    def set_run_number(self, run_number):
        self._currRunNumber = run_number

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
                                                                              ''.format(
                                                                                  fwhm, type(fwhm))

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
        if min_x is not None:
            datatypeutility.check_float_variable('Min X', min_x, (None, None))
        if max_x is not None:
            datatypeutility.check_float_variable('Max X', max_x, (None, None))
        if min_x is not None and max_x is not None and min_x >= max_x:
            raise RuntimeError('Min X {} cannot be equal or larger than Max X {}'
                               ''.format(min_x, max_x))

        if min_x is not None:
            self.ui.lineEdit_minX.setText('{}'.format(min_x))
        if max_x is not None:
            self.ui.lineEdit_maxX.setText('{}'.format(max_x))

        # set X range
        # self.do_set_x_range()

        return
