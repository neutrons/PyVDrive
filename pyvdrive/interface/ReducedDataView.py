########################################################################
#
# General-purposed plotting window
#
# NOTE: Bank ID should always start from 1 or positive
#
########################################################################
import os
try:
    import qtconsole.inprocess
    from PyQt5.QtWidgets import QMainWindow, QFileDialog
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5 import QtCore
except ImportError:
    from PyQt4.QtGui import QMainWindow, QFileDialog
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4 import QtCore
import gui.GuiUtility as GuiUtility

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
from pyvdrive.interface.gui.generalrunview import GeneralRunView
import pyvdrive.lib.datatypeutility
from pyvdrive.lib import datatypeutility
import atomic_data_viewers

# BANK_GROUP_DICT = {90: [1, 2], 150: [3]}


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

        self._atomic_viewer_list = list()

        # list of loaded runs (single and chopped)
        self._loadedSingleRunList = list()
        self._loadedChoppedRunList = list()

        self._bankIDList = list()

        # workspace management dictionary
        self._choppedRunDict = dict()  # key: run number (key/ID), value: list of workspaces' names
        self._choppedSampleDict = dict()  # key: data workspace name. value: sample (NeXus) workspace name

        # Controlling data structure on lines that are plotted on graph
        self._currentPlotDataKeyDict = dict()  # (UI-key): tuple (data key, bank ID, unit); value: value = vec x, vec y
        # self._dataIptsRunDict = dict()  # key: workspace/run number, value: 2-tuple, IPTS/run number

        # A status flag to show whether the current plot is for sample log or diffraction data
        self._currentPlotSampleLogs = False

        # current status
        self._iptsNumber = None
        self._runNumberList = list()

        self._curr_data_key = None  # current (last loaded) workspace name as data key
        self._currRunNumber = None   # run number of single run reduced
        self._currSlicedRunNumber = None   # run number of sliced case
        self._currSlicedWorkspaces = list()   # an ordered list for the sliced (and maybe focused) workspace names

        self._currWorkspaceTag = None
        self._currBank = 1
        self._currUnit = str(self.ui.comboBox_unit.currentText())

        self._slicedRunsList = list()
        self._choppedSequenceList = None

        self._canvasDimension = 1
        self._plotType = None

        # range of X value to plot
        self._minX = 0
        self._maxX = 1E20

        # mutexes to control the event handling for changes in widgets
        self._mutexRunNumberList = False
        self._mutexChopRunList = False
        self._mutexChopSeqList = False
        self._mutexBankIDList = False

        # data structure to manage the fitting result
        self._stripBufferDict = dict()  # key = [run ID], i.e., [run ID (str)][bank ID (int, 1, 2, 3)] = workspace name
        self._lastVanPeakStripWorkspace = None
        self._smoothBufferDict = dict()
        self._lastVanSmoothedWorkspace = None
        self._vanStripPlotID = None
        self._smoothedPlotID = None

        # about vanadium process
        self._vanadiumFWHM = None

        # Event handling
        # section: load data

        self.ui.pushButton_loadSingleGSAS.clicked.connect(self.do_load_single_run)
        self.ui.pushButton_loadChoppedGSASSet.clicked.connect(self.do_load_chopped_gsas)
        self.ui.pushButton_browseAnyGSAS.clicked.connect(self.do_browse_local_gsas)
        self.ui.pushButton_refreshList.clicked.connect(self.do_refresh_existing_runs)
        self.ui.radioButton_fromArchive.toggled.connect(self.event_load_options)
        # TEST : whether the handling method is triggered?
        self.ui.radioButton_anyGSAS.toggled.connect(self.event_load_options)

        # section: choose to plot
        self.ui.pushButton_prevRun.clicked.connect(self.do_plot_prev_run)
        self.ui.pushButton_nextRun.clicked.connect(self.do_plot_next_run)
        self.ui.pushButton_prevChopped.clicked.connect(self.do_plot_prev_chopped)
        self.ui.pushButton_nextChopped.clicked.connect(self.do_plot_next_chopped)

        # section: plot
        self.ui.pushButton_plot.clicked.connect(self.do_plot_diffraction_data)
        self.ui.pushButton_allFillPlot.clicked.connect(self.do_plot_contour)
        self.ui.pushButton_plotSampleLog.clicked.connect(self.do_plot_sample_logs)
        self.ui.comboBox_runs.currentIndexChanged.connect(self.evt_select_new_run_number)
        self.ui.comboBox_runs.currentIndexChanged.connect(self.evt_select_new_run_number)
        self.ui.comboBox_chopSeq.currentIndexChanged.connect(self.evt_select_new_chopped_child)

        # radio buttons
        self.ui.radioButton_chooseSingleRun.toggled.connect(self.evt_toggle_run_type)

        # other
        self.ui.pushButton_clearCanvas.clicked.connect(self.do_clear_canvas)
        self.ui.pushButton_cancel.clicked.connect(self.do_close)

        # data processing
        self.ui.pushButton_normByCurrent.clicked.connect(self.do_normalise_by_current)
        self.ui.pushButton_apply_x_range.clicked.connect(self.apply_new_x_range)
        self.ui.pushButton_apply_y_range.clicked.connect(self.apply_new_y_range)

        # combo boxes
        self.ui.comboBox_spectraList.currentIndexChanged.connect(self.evt_bank_id_changed)
        self.ui.comboBox_unit.currentIndexChanged.connect(self.evt_unit_changed)

        # menu
        # TODO - 20181102 - Add Back!
        # lineEdit_binParams, lineEdit_binParams


        # self.ui.actionOpen_Preprocessed_NeXus.triggered.connect(self.do_load_preprocessed_nexus)
        # self.ui.actionRefresh_Runs_In_Mmemory.triggered.connect(self.do_refresh_existing_runs)

        # widgets to load reduced data

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

        return

    def _init_widgets(self):
        """
        Initialize some widgets
        :return:
        """
        # load data: default to load data from memory
        self.ui.radioButton_fromArchive.setChecked(True)
        self._set_load_from_archive_enabled(True)
        self._set_load_from_hdd_enabled(False)

        # select single run or chopped run
        self.ui.radioButton_chooseSingleRun.setChecked(True)
        self.ui.groupBox_plotSingleRun.setEnabled(True)
        self.ui.groupBox_plotChoppedRun.setEnabled(False)

        # set bank ID combobox
        self._bankIDList = [1, 2, 3]
        self.ui.comboBox_spectraList.clear()
        for bank_id in self._bankIDList:
            self.ui.comboBox_spectraList.addItem('{0}'.format(bank_id))
        self.ui.comboBox_spectraList.addItem('All Banks')

        return

    def _get_plot_x_range_(self):
        """ get the x range of current plot
        :return: 2-tuple.  min x, max x
        """
        # check current min/max for data
        min_x_str = str(self.ui.lineEdit_minX.text()).strip()
        try:
            min_x = float(min_x_str)
        except ValueError:
            min_x = None
        max_x_str = str(self.ui.lineEdit_maxX.text()).strip()
        try:
            max_x = float(max_x_str)
        except ValueError:
            max_x = None

        return min_x, max_x

    def _set_load_from_archive_enabled(self, enabled):
        """
        set the widgets to load data from archive to be enabled or disabled
        :param enabled:
        :return:
        """
        self.ui.lineEdit_iptsNumber.setEnabled(enabled)
        self.ui.lineEdit_run.setEnabled(enabled)

        return

    def _set_load_from_hdd_enabled(self, enabled):
        """
        enable or disable widgets for loading GSAs from HDD
        :param enabled:
        :return:
        """
        self.ui.lineEdit_gsasFileName.setEnabled(enabled)
        self.ui.pushButton_browseAnyGSAS.setEnabled(enabled)

        return

    def do_browse_local_gsas(self):
        """
        browse GSAS file or chopped GSAS files via local HDD
        :return:
        """
        # TODO - 20181103 - also deal with do_load_preprocessed_nexus
        # get setup
        # is_chopped_data = self.ui.checkBox_loadChoppedAny.isChecked()
        default_dir = self._myController.get_working_dir()

        gsas_filter = 'GSAS(*.gda);;GSAS (*.gsa);;All Files(*.*)'
        gsas_file_name = QFileDialog.getOpenFileName(self, 'GSAS file name', default_dir, gsas_filter)
        self.ui.lineEdit_gsasFileName.setText(gsas_file_name)

        return

    def do_clear_canvas(self):
        """
        clear canvas
        :return:
        """
        self.ui.graphicsView_mainPlot.reset_1d_plots()

        return

    def _is_run_in_memorty(self, run_number):
        return self._myController.project.reduction_manager.has_run_reduced(run_number)

    def do_load_chopped_runs(self, ipts_number=None, run_number=None, chopped_seq_list=None):
        """ Load a series chopped and reduced data to reduced data view
        :param ipts_number:
        :param run_number:
        :param chopped_seq_list:
        :return:
        """
        # read from input for IPTS and run number
        if ipts_number is None:
            ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, False)
        if run_number is None:
            run_number = GuiUtility.parse_integer(self.ui.lineEdit_run, False)

        # get data sets
        if run_number is not None and self._myController.has_chopped_data(run_number, reduced=True):
            # load from memory
            # FIXME - TOMORROW - NOT TEST YET! Need to be on analysis cluster!
            data_key_dict, run_number_str = self._myController.load_chopped_data(run_number, chopped_seq_list)
        elif ipts_number is not None and run_number is not None:
            # load data from archive
            chopped_data_dir = self._myController.get_archived_data_dir(self._iptsNumber, run_number,
                                                                        chopped_data=True)
            result = self._myController.project.load_chopped_binned_file(chopped_data_dir, chopped_seq_list,
                                                                         run_number)
            project_chop_key = result
        else:
            raise NotImplementedError('Not sure how to load from an arbitrary directory!')


        # self.plot_chopped_data_2d(run_number=processor.get_run_number(),
        #                                  chop_sequence=processor.get_chopped_sequence_range(),
        #                                  bank_id=1,
        #                                  bank_id_from_1=True,
        #                                  chopped_data_dir=processor.get_reduced_data_directory(),
        #                                  vanadium_run_number=van_run,
        #                                  proton_charge_normalization=pc_norm)

        return

    def do_load_single_run(self, ipts_number=None, run_number=None, plot=True):
        """
        Load a single run to reduced data view
        Note: this is a high level method
        :param ipts_number:
        :param run_number:
        :param plot:
        :return:
        """
        # read from input for IPTS and run number
        if ipts_number is None:
            ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, False)
        if run_number is None:
            run_number = GuiUtility.parse_integer(self.ui.lineEdit_run, False)

        if run_number is not None and self._is_run_in_memorty(run_number):
            # load from memory
            self._curr_data_key = self._myController.project.reduction_manager.get_reduced_workspace(run_number)
        elif ipts_number is not None and run_number is not None:
            # load data from archive
            reduced_file_name = self._myController.archive_manager.get_gsas_file(ipts_number, run_number,
                                                                                 check_exist=True)
            file_type = 'gsas'
            self._curr_data_key = self._myController.project.data_loading_manager.load_binned_data(reduced_file_name,
                                                                                                   file_type,
                                                                                                   max_int=99999)
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
                return

            if reduced_data_file.lower().endswith('nxs'):
                # processed NeXus
                try:
                    self._curr_data_key = self._myController.load_nexus_file(reduced_data_file)
                except RuntimeError as run_err:
                    GuiUtility.pop_dialog_error(self, 'Unable to load {} due to {}'.format(reduced_data_file, run_err))
                    return
            else:
                # gsas file
                reduced_file_name = self._myController.archive_manager.get_gsas_file(ipts_number, run_number,
                                                                                     check_exist=True)
                file_type = 'gsas'
                self._curr_data_key = self._myController.project.data_load_manager.load_binned_data(reduced_file_name,
                                                                                                    file_type)

        # END-IF-ELSE

        # add reduced run to ...
        data_bank_list = self._myController.project.get_reduced_run_information(data_key=self._curr_data_key)
        # self.add_reduced_run(self._curr_data_key, data_bank_list, plot_new=plot)

        return self._curr_data_key

    def do_load_single_gsas(self):
        """ Load a single GSAS file either from SNS archive (/SNS/VULCAN/...) or from local HDD
        :return:
        """
        is_chopped_data = False

        if self.ui.radioButton_fromArchive.isChecked():
            # load from archive


            try:
                data_key = self._myController.load_archived_gsas(ipts_number, run_number, is_chopped_data,
                                                                 data_key='{0}_G'.format(run_number))

            except RuntimeError as run_error:
                GuiUtility.pop_dialog_error(self, 'Unable to load run {0} from archive due to\n{1}.'
                                                  ''.format(run_number, run_error))
                return

        elif self.ui.radioButton_anyGSAS.isChecked():
            # load from HDD
            # input is a file: load a single GSAS file, get GSAS file path
            gsas_path = str(self.ui.lineEdit_gsasFileName.text())
            if len(gsas_path) == 0:
                # check
                GuiUtility.pop_dialog_information(self, 'No GSAS file is given')
                return

            # check whether it is a directory for a file
            if os.path.isdir(gsas_path):
                raise RuntimeError('User given GSAS file name {0} is a directory.'.format(gsas_path))
            else:
                data_key = os.path.basename(gsas_path).split('.')[0] + '_H'  # H stands for HDD

            # load the data file and returned as data key
            data_key = self._myController.load_diffraction_file(file_name=gsas_path, file_type='gsas',
                                                                data_key=data_key)
        else:
            raise RuntimeError('Neither from archive nor from HDD is selected.')

        # END-IF-ELSE

        # set spectra list
        try:
            data_bank_list = self._myController.get_reduced_data_info(data_key=data_key, info_type='bank')
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self,
                                        'Unable to get bank information from {} due to {}d'.format(data_key, run_err))
            return

        # add run number to run number list and plot
        self.add_reduced_run(data_key, data_bank_list, True)

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
            print ('[ERROR-POP] Unable to get bank list from {0}'.format(data_key))
            return
        print data_bank_list

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

    def do_load_chopped_gsas(self):
        """ load chopped GSAS data
        :return:
        """
        if self.ui.radioButton_fromArchive.isChecked():
            # load from archive
            # read from input for IPTS and run number
            ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber, False)
            run_number = GuiUtility.parse_integer(self.ui.lineEdit_run, False)

            try:
                is_chopped_data = True
                data_key = self._myController.load_archived_gsas(ipts_number, run_number, is_chopped_data)
            except RuntimeError as run_error:
                GuiUtility.pop_dialog_error(self, 'Unable to load run {0} from archive due to\n{1}.'
                                                  ''.format(run_number, run_error))
                return

            # process chopped data sequence
            seq_list = data_key['chopped sequence']
            self.add_chopped_data_set(ipts_number=ipts_number, run_number=run_number, controller_data_key=data_key)

        elif self.ui.radioButton_anyGSAS.isChecked():
            # load from HDD
            # input is a directory: load chopped data series
            raise RuntimeError('Figure out how to specify GSAS file path')
            data_key_dict, run_number = self._myController.load_chopped_diffraction_files(gsas_path, None, 'gsas')

            # a key as run number
            if run_number is None:
                run_number = gsas_path

            # get workspaces from data key dictionary and add to data management
            diff_ws_list = self.process_loaded_chop_suite(data_key_dict)
            self.add_chopped_workspaces(run_number, diff_ws_list, True)
            seg_list = diff_ws_list

            data_key = None


        else:
            # unsupported case
            raise RuntimeError('Neither from archive nor from HDD is selected.')

        # load and plot GSAS
        # add segments list
        self.ui.comboBox_chopSeq.clear()
        for segment_index in sorted(seg_list):
            self.ui.comboBox_chopSeq.addItem(segment_index)

        # plot the first workspace!
        raise RuntimeError('It is supposed to plot the first workspace in the chop list!')

        return

    # TEST - 20180723 - Just implemented
    def update_chopped_run_combo_box(self, item_name, remove_item):
        """ Update the combo-box recording all the chopped runs with new workspace/run number/data ID
        :param item_name: new item name
        :param remove_item: flag whether the current items in the combo box shall be cleared
        :return:
        """
        # check
        pyvdrive.lib.datatypeutility.check_string_variable('Chopped run item', item_name)
        pyvdrive.lib.datatypeutility.check_bool_variable('Flag to remove existing items in chopped run combo-box',
                                                         remove_item)

        # remove items if required
        if remove_item:
            # remove the specified item
            if item_name not in self._loadedChoppedRunList:
                GuiUtility.pop_dialog_error(self, 'Run number {0} is not in the combo-box to remove.'
                                                  ''.format(item_name))
                return

            # NOTE: _loadedChoppedRunList is always synchronized with comboBox_choppedRunNumber
            pos_index = self._loadedChoppedRunList.index(item_name)
            curr_pos = self.ui.comboBox_choppedRunNumber.currentIndex()

            self._mutexChopRunList = True
            self.ui.comboBox_choppedRunNumber.removeItem(pos_index)
            self._loadedChoppedRunList.pop(pos_index)

            # if necessary, reset the current position
            if pos_index <= curr_pos:
                self.ui.comboBox_choppedRunNumber.setCurrentIndex(curr_pos-1)
            self._mutexChopRunList = False
        else:
            # add item
            if item_name in self._loadedChoppedRunList:
                raise RuntimeError('Entry {0} has been in the combo box already.'.format(item_name))

            # insert and keep current position
            if self.ui.comboBox_choppedRunNumber.count() == 0:
                # first item, simply add
                self._loadedChoppedRunList.append(item_name)
                self._mutexChopRunList = True
                self.ui.comboBox_choppedRunNumber.addItem(item_name)
                self._mutexChopRunList = False
                insert_pos = 0
            else:
                # other item exits
                current_item = str(self.ui.comboBox_choppedRunNumber.currentText())
                print ('[DB..BAT] Current count = {0}, index = {1}, text = {2}'
                       ''.format(self.ui.comboBox_choppedRunNumber.count(),
                                 self.ui.comboBox_choppedRunNumber.currentIndex(),
                                 self.ui.comboBox_choppedRunNumber.currentText()))

                # add new item to list
                self._loadedChoppedRunList.append(item_name)
                self._loadedChoppedRunList.sort()

                # get position to insert and position to set
                insert_pos = self._loadedChoppedRunList.index(item_name)
                try:
                    curr_pos = self._loadedChoppedRunList.index(current_item)
                except ValueError as val_err:
                    raise RuntimeError('Loaded chopped runs ({}) doe not contain {}. FYI: {}'
                                       ''.format(self._loadedChoppedRunList, current_item, val_err))

                # insert and set
                self._mutexChopRunList = True
                self.ui.comboBox_choppedRunNumber.insert(insert_pos, item_name)
                self.ui.comboBox_choppedRunNumber.setCurrentIndex(curr_pos)
                self._mutexChopRunList = False
            # END-IF-ELSE
        # END-IF

        return

    def update_single_run_combo_box(self, run_key, remove_item, focus_to_new):
        """ update the combo box for single run (no chopped).
        Note: it will give out the signal whether a re-plot is necessary but it won't do the job
        :param run_key: a string serving as the key to the run. can be the run number or etc
        :param remove_item: flag for adding or removing item
        :param focus_to_new: flag to set the current index to newly added term
        :return:
        """
        # check inputs
        pyvdrive.lib.datatypeutility.check_string_variable('Single run number', run_key)
        pyvdrive.lib.datatypeutility.check_bool_variable('Flag to remove the specified run number', remove_item)

        # get current index
        start_combo_index = self.ui.comboBox_runs.currentIndex()
        start_run_key = str(self.ui.comboBox_runs.currentText())
        final_combo_index = start_combo_index

        if remove_item:
            # remove item
            print ('[DB...BAT...Update Combo (Remove): item name: {0} type {1}'.format(run_key, type(run_key)))

            try:
                item_index = self._runNumberList.index(run_key)
            except ValueError as value_err:
                raise RuntimeError('Unable to locate {0} in single run list due to {1}.'
                                   ''.format(run_key, value_err))
            # check again
            if not str(self.ui.comboBox_runs.itemText(item_index)) == run_key:
                err_msg = 'Run to remove with key {} must be equal to {}-th item in combo box (which is {} now)' \
                          ''.format(run_key, item_index, self.ui.comboBox_runs.itemText(item_index))
                raise NotImplementedError(err_msg)

            self._mutexRunNumberList = True
            self.ui.comboBox_runs.removeItem(item_index)
            self._runNumberList.pop(item_index)
            self._mutexRunNumberList = False

            # check re-focus: reduce 1 if necessary
            if start_combo_index <= item_index:
                final_combo_index = start_combo_index - 1
                re_plot = True

        else:
            # add the new item
            print ('[DB...BAT...Update Combo (Add): item name: {0} type {1}'.format(run_key, type(run_key)))

            # check existing?
            if run_key in self._runNumberList:
                raise RuntimeError('Entry {0} has been in the combo box already.'.format(run_key))

            # insert and find position
            self._runNumberList.append(run_key)
            self._runNumberList.sort()
            index_to_be = self._runNumberList.index(run_key)

            # add to combo box
            self._mutexRunNumberList = True
            self.ui.comboBox_runs.insertItem(index_to_be, run_key)
            self._mutexRunNumberList = False

            # optionally set current index to the new item
            if focus_to_new or start_run_key == '':  # new or previously empty combo box
                final_combo_index = index_to_be
            else:
                final_combo_index = self._runNumberList.index(start_run_key)
                self.ui.comboBox_runs.setCurrentIndex(index_to_be)
            # END-IF
        # END-IF-ELSE

        # focus the current index
        self._mutexRunNumberList = True
        self.ui.comboBox_runs.setCurrentIndex(final_combo_index)
        self._mutexRunNumberList = False
        re_plot = str(self.ui.comboBox_runs.currentText()) != start_run_key

        return re_plot

    # def add_data_set(self, ipts_number, run_number, controller_data_key, unit=None):
    #     """
    #     add a new data set to this data viewer window BUT without plotting including
    #     1. data management dictionary
    #     2. combo-box as data key
    #     :param ipts_number:
    #     :param run_number:
    #     :param controller_data_key:
    #     :param unit:
    #     :return:
    #     """
    #     # TODO ASAP -- merge with add_run_numbers
    #     raise RuntimeError('Refactor ASAP')
    #
    #     # return if the controller data key exist
    #     if controller_data_key in self._reducedDataDict:
    #         return
    #
    #     # self._dataIptsRunDict[controller_data_key] = ipts_number, run_number
    #
    #     # show on the list: turn or and off mutex locks around change of the combo box contents
    #     self._mutexRunNumberList = True
    #     # clear existing runs
    #     self.ui.comboBox_runs.addItem(str(controller_data_key))
    #     # release mutex lock
    #     self._mutexRunNumberList = False
    #
    #     # get reduced data set from controller
    #     if unit is not None:
    #         self._currUnit = unit
    #
    #     self.retrieve_loaded_reduced_data(run_number=controller_data_key, unit=self._currUnit)
    #
    #     return controller_data_key

    # TEST -20180730 - Newly Refactored
    def add_reduced_run(self, data_key, bank_id_list, plot_new):
        """ add a reduced run to this UI
        Usage:
            pyvdrive/interface/VDrivePlot.py  483:
            pyvdrive/interface/vcommand_processor.py
            self.do_load_single_gsas
        :param data_key:
        :param bank_id_list: the list of banks of the data key. it is only required when plotting is required
        :param plot_new: flag to focus the combo box to the newly added run and plot
        :return:
        """
        # check inputs
        pyvdrive.lib.datatypeutility.check_string_variable('Reduced data key', data_key)
        pyvdrive.lib.datatypeutility.check_bool_variable('Flag to plot newly added run', plot_new)

        # # set plot new : NOTE that it is not required to plot newly added data even it was empty before
        # if len(self._runNumberList) == 0:
        #     # first run to add
        #     plot_new = True

        # update run combo box without plotting
        self.update_single_run_combo_box(data_key, remove_item=False, focus_to_new=plot_new)
        # END-FOR

        # update bank ID box without plotting
        if plot_new:
            self.update_bank_id_combo(bank_id_list)
            pyvdrive.lib.datatypeutility.check_list('Bank ID list', bank_id_list)

            # register?
            # self._dataIptsRunDict[run_number] = ipts_number, run_number
            # self._dataIptsRunDict[controller_data_key] = ipts_number, run_number

        # END-FOR

        return

    def set_current_chopped_run(self, pos=None, name=None, chopped_children=None):
        """
        set current chopped run in the combo-box;
        plotting is required
        :param pos:
        :param name:
        :return:
        """
        if pos is None and name is None:
            raise RuntimeError('Both pos and name are None')
        elif pos is None:
            pos = self._loadedChoppedRunList.index(name)
        elif name is None:
            pos = pos
        else:
            raise RuntimeError('Neither pos nor name is None')

        # lock!
        self._mutexChopRunList = True
        self._mutexChopSeqList = True

        self.ui.comboBox_choppedRunNumber.setCurrentIndex(pos)

        self.ui.comboBox_chopSeq.clear()
        chopped_children.sort()
        for child_name in chopped_children:
            self.ui.comboBox_chopSeq.addItem(child_name)
        self.ui.comboBox_chopSeq.setCurrentIndex(0)

        # unlock
        self._mutexChopRunList = False
        self._mutexChopSeqList = False

        return

    def add_chopped_workspaces(self, workspace_key, workspace_name_list, focus_to_it):
        """
        add (CHOPPED) workspaces' names to the data viewer
        Note: It shall not trigger the event to plot any chopped data
        :param workspace_key: string or integer (run number)
        :param workspace_name_list:
        :param focus_to_it:
        :return:
        """
        # check inputs... TODO ASAP blabla
        print ('[DB...BAT] Add chopped run... key = {0} ({1}); workspace list = {2}'
               ''.format(workspace_key, type(workspace_key), workspace_name_list))

        if isinstance(workspace_key, int):
            # in case workspace key is a run number
            workspace_key = '{0}'.format(workspace_key)

        # register to current chopped runs
        new_item_pos = self.update_chopped_run_combo_box(workspace_key, remove_item=False)

        # focus on this one and plot
        self.ui.radioButton_chooseChopped.setChecked(True)
        self.ui.groupBox_plotSingleRun.setEnabled(False)
        self.ui.groupBox_plotChoppedRun.setEnabled(True)

        # set to plot
        if focus_to_it:
            self.set_current_chopped_run(pos=new_item_pos, name=None, chopped_children=workspace_name_list)
            self.do_plot_diffraction_data()

        return
        #
        #
        # # turn on the mutex
        # self._mutexRunNumberList = True
        # self._mutexChopSeqList = True
        #
        # # check input
        # assert workspace_key is not None, 'Workspace key (run number mostly) cannot be None'
        # # force work key to be string
        # workspace_key = '{0}'.format(workspace_key)
        #
        # # two cases to get list of chopped workspaces' names
        # if workspace_name_list is None:
        #     # the workspace key must have been loaded before
        #     assert workspace_key in self._choppedRunDict, 'Workspace key {0} cannot be found in chopped run ' \
        #                                                   'dictionary whose keys are {1}.' \
        #                                                   ''.format(workspace_key, self._choppedRunDict.keys())
        #     workspace_name_list = self._choppedRunDict[workspace_key]
        # else:
        #     # this sequence is set to this viewer first time
        #     assert isinstance(workspace_name_list, list), 'Workspaces names {0} must be given by list but not a ' \
        #                                                   '{1}.'.format(workspace_name_list,
        #                                                                 type(workspace_name_list))
        #     assert len(workspace_name_list) > 0, 'Workspaces name list cannot be empty'
        #
        #     # add to widgets and data managing dictionary
        #     self._choppedRunDict[workspace_key] = list()
        #     for workspace_name in workspace_name_list:
        #         self._choppedRunDict[workspace_key].append(workspace_name)
        #
        #     self.ui.comboBox_runs.addItem('{0}'.format(workspace_key))
        # # END-IF-ELSE
        #
        # # set check box
        # self.ui.checkBox_choppedDataMem.setChecked(True)
        #
        # # sort workspace names
        # workspace_name_list.sort()
        #
        # # add chopped workspaces to (1) _choppedSequenceList (current) and ui.comboBox_chopSeq
        # if clear_previous:
        #     self.ui.comboBox_chopSeq.clear()
        #     self._choppedSequenceList = list()
        # for workspace_name in workspace_name_list:
        #     self.ui.comboBox_chopSeq.addItem(workspace_name)
        #     self._choppedSequenceList.append(workspace_name)
        #
        # # release mutex lock
        # self._mutexRunNumberList = False
        # self._mutexChopSeqList = False
        #
        # return range(len(workspace_name_list))

    def apply_new_x_range(self):
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

    def apply_new_y_range(self):
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
            curr_min_x = float(new_min_y_str)

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

    def do_normalise_by_current(self):
        """
        Normalize by current/proton charge if the reduced run is not.
        :return:
        """
        # TEST - 20180730 - Refactored
        # Get run number
        run_number_st = self.ui.comboBox_runs.currentText()

        # Get reduction information from run number
        if run_number_st.endswith('G'):
            # from gsas file
            GuiUtility.pop_dialog_information(self, 'This is a data loaded from GSAS. Normailze by current'
                                                    ' cannot be applied to data loaded from GSAS')
            return

        # from reduced data
        run_number = int(run_number_st)
        # TODO/FIXME - 20180820 - get_reduced_run_info() gives the banks' list!
        status, ret_obj = self._myController.get_reduced_run_info(run_number)
        if status:
            reduction_info = ret_obj
        else:
            GuiUtility.pop_dialog_error(self, 'Unable to access reduced run {} due to {}'.format(run_number_st,
                                                                                                 ret_obj))
        # END-IF

        # check whether
        # TODO/FIXME - 20180820 - No method called is_noramalised_by_current in pyvdrive
        if reduction_info.is_noramalised_by_current() is True:
            GuiUtility.pop_dialog_information(self, 'Run %d has been normalised by current already.' % run_number)
            return

        # Normalize by current
        self._myController.normalise_by_current(run_number=run_number)

        # Re-plot
        bank_id = int(self.ui.comboBox_spectraList.currentText())
        over_plot = False

        self.plot_by_data_key(run_number_st, bank_id_list=[bank_id], over_plot=over_plot)

        return

    def do_plot_contour(self):
        """ plot Either (1) all the chopped data Or (2) all loaded single runs
        by contour plot
        :return:
        """
        data_key_list = list()

        if self.ui.radioButton_chooseChopped.isChecked():
            # plot chopped data
            run_number = str(self.ui.comboBox_choppedRunNumber.currentText())
            for p_int in range(self.ui.comboBox_chopSeq.count()):
                child_key = str(self.ui.comboBox_chopSeq.itemText(p_int))
                data_key_list.append((run_number, child_key))
            # END-FOR
        elif self.ui.radioButton_chooseSingleRun.isChecked():
            # plot all single runs
            for p_int in range(self.ui.comboBox_runs.count()):
                data_key = str(self.ui.comboBox_runs.itemText(p_int))
                data_key_list.append(data_key)
        else:
            # unsupported
            raise RuntimeError('Neither radio button to choose single run or chopped is checked.')

        # bank information and unit
        curr_bank = int(self.ui.comboBox_spectraList.currentText())
        curr_unit = str(self.ui.comboBox_unit.currentText())

        # plot
        self.plot_multiple_runs_2d(ws_key_list=data_key_list, bank_id=curr_bank,
                                   target_unit=curr_unit)

        return

    # TESTME - Shall find out how this breaks
    def do_plot_diffraction_data(self):
        """
        Plot the diffraction data in single run mode or chopped mode but 1D plot is the goal.
        Data will come from selected index of the combo box
        :return:
        """
        # get bank ID(s) selected
        bank_id_str = str(self.ui.comboBox_spectraList.currentText())
        if bank_id_str.isdigit():
            # single bank
            bank_id_list = [int(bank_id_str)]
        else:
            # plot all banks
            bank_id_list = self._bankIDList[:]

        # get range of data
        min_x, max_x = self._get_plot_x_range_()

        # get data key
        if self.ui.radioButton_chooseSingleRun.isChecked():
            # single run
            # determine the data to reduce
            curr_run_key = str(self.ui.comboBox_runs.currentText())
        elif self.ui.radioButton_chooseChopped.isChecked():
            # chopped run
            seq_index = self.ui.comboBox_chopSeq.currentIndex()
            curr_run_key = self._currSlicedWorkspaces[seq_index]

        else:
            raise RuntimeError('Neither radio button to choose single run or chopped is checked.')

        # plot
        self.plot_by_data_key(curr_run_key, bank_id_list=bank_id_list,
                              over_plot=False, x_limit=(min_x, max_x))

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

    def do_plot_prev_chopped(self):
        # TODO ASAP ASAP2  Implement
        return

    def do_plot_next_chopped(self):
        # TODO ASAP ASAP2  Implement
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

    def do_refresh_existing_runs(self, set_to=None, plot_selected=False):
        """ refresh the existing runs in the combo box
        :param set_to:
        :param plot_selected: if set_to is True, then plot the new data if True
        :return:
        """
        # Part 1: single runs
        single_runs_list = self._myController.get_loaded_runs(chopped=False)
        if len(single_runs_list) >= 0:
            # current selection
            current_single_run = str(self.ui.comboBox_runs.currentText()).strip()
            if current_single_run == '':
                current_single_run = None

            # single runs
            single_runs_list.sort()

            # update
            for run_number in single_runs_list:
                print ('[INFO] Loaded run {} ({})'.format(run_number, type(run_number)))
                # convert run  number from integer to string as the standard
                if isinstance(run_number, int):
                    run_number = '{0}'.format(run_number)
                # if not existed, then update the single run combo-box
                if run_number not in self._runNumberList:
                    self.update_single_run_combo_box(run_number, False, False)
                    # END-IF
            # END-IF

            # re-focus back to original one
            self._mutexRunNumberList = True
            if current_single_run is None:
                new_pos = 0
            elif set_to is not None:
                new_pos = self._runNumberList.index(set_to)
            else:
                new_pos = self._runNumberList.index(current_single_run)
            self.ui.comboBox_runs.setCurrentIndex(new_pos)
            self._mutexRunNumberList = False
        # END-IF

        # Part 2: chopped runs
        # TODO - FIXME - TONIGHT 1 - This does not sounds right!
        chopped_run_list = self._myController.get_loaded_runs(chopped=True)
        curr_index = self.ui.comboBox_choppedRunNumber.currentIndex()
        self._mutexChopRunList = True
        for run_number, slice_id in chopped_run_list:
            if (run_number, slice_id) in self._slicedRunsList:
                # it has been registered to ReductionWindow already
                continue
            # add the combobox
            self.ui.comboBox_choppedRunNumber.addItem('{}_{}'.format(run_number, slice_id))
            self._slicedRunsList.append((run_number, slice_id))
        # END-FOR
        self.ui.comboBox_choppedRunNumber.setCurrentIndex(curr_index)
        self._mutexChopRunList = False

        return

    def update_slice_sequence_widgets(self, mandatory_load=False):
        """
        select the run (data key) in comboBox_runs's current text as the current run to plot
        NOTE: this shall be the only method to update the slice sequence
        :return:
        """
        def sort_mantid_sliced_ws_names(ws_name_list):
            """
            sort the workspaces named from Mantid FilterEvents
            :param ws_name_list:
            :return: a list sorted by slicing/chopping index
            """
            # check
            datatypeutility.check_list('Workspace names', ws_name_list)

            # get the workspace name
            index_ws_name_dict = dict()
            try:
                for ws_name in ws_name_list:
                    parts = ws_name.split('_')
                    split_index = int(parts[-1])
                    index_ws_name_dict[split_index] = ws_name
                # END-FOR
            except ValueError:
                return None

            sorted_list = [index_ws_name_dict[index] for index in sorted(index_ws_name_dict.keys())]

            return sorted_list

        # no need to anything as this has already been imported
        if self._currSlicedRunNumber == str(self.ui.comboBox_choppedRunNumber.currentText()) and not mandatory_load:
            return

        try:
            sliced_run_index = self.ui.comboBox_choppedRunNumber.currentIndex()

            # return if there is no chopped and reduced workspace found in memory
            if sliced_run_index < 0:
                return

            run_number, slice_id = self._slicedRunsList[sliced_run_index]
        except IndexError as index_err:
            err_msg = 'Current index = {}.  Stored sliced runs list = {}: {}' \
                      ''.format(self.ui.comboBox_choppedRunNumber.currentIndex(),
                                self._slicedRunsList, index_err)
            raise IndexError(err_msg)

        if (run_number, slice_id) in self._choppedRunDict:
            # this particular run and slicing plan, then get the previous stored value from dictionary
            sliced_ws_names_list, bank_id_list, series_sample_log_list = self._choppedRunDict[(run_number, slice_id)]
        else:
            # first time: get workspaces first
            sliced_ws_names = self._myController.get_sliced_focused_workspaces(run_number, slice_id)

            print ('[DB...BAT] sliced workspace names: {}'.format(sliced_ws_names))

            # order the sliced workspace name as 1, ..., 9, 10, ...
            sliced_ws_names_list = sort_mantid_sliced_ws_names(sliced_ws_names)
            print ('[DB...BAT] sorted workspace names: {}'.format(sliced_ws_names_list))
            if sliced_ws_names_list is None:
                sliced_ws_names_list = sliced_ws_names

            # get the bank list
            print ('[DB...BAT] data key: {}'.format(sliced_ws_names_list[0]))
            status, ret_obj = self._myController.get_reduced_run_info(run_number=None, data_key=sliced_ws_names_list[0])
            if status:
                bank_id_list = ret_obj
            else:
                GuiUtility.pop_dialog_error(self, ret_obj)
                return

            # get the sample logs
            series_sample_log_list = self._myController.get_sample_log_names(run_number=sliced_ws_names_list[0],
                                                                             smart=True)
            self.set_sample_log_names(series_sample_log_list)

            # add the dictionary
            self._choppedRunDict[run_number, slice_id] = sliced_ws_names_list, bank_id_list, series_sample_log_list
        # END--IF-ELSE

        # set the current states and update the everything
        self._currSlicedWorkspaces = sliced_ws_names_list

        # update the chopping workspace list
        self._mutexChopSeqList = True
        self.ui.comboBox_chopSeq.clear()
        for i_seq in range(len(self._currSlicedWorkspaces)):
            self.ui.comboBox_chopSeq.addItem(self._currSlicedWorkspaces[i_seq])
        self._mutexChopSeqList = False

        # update the bank list
        self._mutexBankIDList = True
        self.ui.comboBox_spectraList.clear()
        for bank_id in bank_id_list:
            self.ui.comboBox_spectraList.addItem('{0}'.format(bank_id))
        self._mutexBankIDList = False

        # update the sample log ist
        self.set_sample_log_names(series_sample_log_list)

        # now trigger the event to plot
        self.ui.comboBox_spectraList.setCurrentIndex(0)

        # set the label
        self.label_loaded_data(self._currRunNumber, self._currSlicedRunNumber, self._currSlicedWorkspaces)

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
            self._set_load_from_archive_enabled(True)
            self._set_load_from_hdd_enabled(False)
        elif self.ui.radioButton_anyGSAS.isChecked():
            # enable group 3 widgets
            self._set_load_from_archive_enabled(False)
            self._set_load_from_hdd_enabled(True)
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
        self.do_plot_diffraction_data()

        return

    def evt_toggle_plot_options(self):
        """
        handling event as radioButton choose diffraction to plot or choose sample log to plot
        :return:
        """
        if self.ui.radioButton_chooseDiffraction.isChecked():
            plot_diffraction = True
        else:
            plot_diffraction = False

        self.ui.groupBox_plotREducedData.setEnabled(plot_diffraction)
        self.ui.groupBox_plotLog.setEnabled(not plot_diffraction)

        return

    def evt_toggle_run_type(self):
        """
        toggle the group boxes for reduced runs
        :return:
        """
        self.ui.groupBox_plotSingleRun.setEnabled(self.ui.radioButton_chooseSingleRun.isChecked())
        self.ui.groupBox_plotChoppedRun.setEnabled(self.ui.radioButton_chooseChopped.isChecked())

        # set the run number and etc
        if self.ui.radioButton_chooseChopped.isChecked():
            print ('Selected chopped run: {}'.format(self.ui.comboBox_choppedRunNumber.currentText()))
            print ('Current chopped data: {}'.format(self._currSlicedRunNumber))

            self.update_slice_sequence_widgets(mandatory_load=True)
        # END-IF

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

    def evt_unit_changed(self):
        """
        Purpose: Re-plot the current plots with new unit
        :return:
        """
        # Clear previous image and re-plot
        self.ui.graphicsView_mainPlot.clear_all_lines()

        # set unit
        self._currUnit = str(self.ui.comboBox_unit.currentText())

        # plot
        self.do_plot_diffraction_data()

        return

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

    def init_setup(self, controller):
        """ Set up the GUI from controller, and add reduced runs to SELF automatically
        :param controller:
        :return:
        """
        # Check
        # assert isinstance(controller, VDriveAPI)
        self._myController = controller

        # Set the reduced runs
        reduced_run_number_list = self._myController.get_loaded_runs(chopped=False)
        if len(reduced_run_number_list) > 0:
            reduced_run_number_list.sort()
            # set up the combo box
            self.ui.comboBox_runs.clear()
            for index, run_number in enumerate(reduced_run_number_list):
                data_key = '{0}'.format(run_number)
                print ('[DB...BAT] Added run: {0} ({1}) with data key {2}'
                       ''.format(run_number, type(run_number), data_key))
                self.update_single_run_combo_box(data_key, remove_item=False,
                                                 focus_to_new=(index == 0))
                self.update_bank_id_combo(data_key=data_key)
            # END-FOR

            # plot
            self.do_plot_diffraction_data()
        # END-IF

        # also load reduced chopped runs
        chopped_run_number_list = self._myController.get_loaded_runs(chopped=True)
        self._slicedRunsList = list()
        if len(chopped_run_number_list) > 0:
            chopped_run_number_list.sort()
            # set up the combo box
            self.ui.comboBox_choppedRunNumber.clear()
            for run_number, slice_key in chopped_run_number_list:
                self.ui.comboBox_choppedRunNumber.addItem('{}_{}'.format(run_number, slice_key))
                self._slicedRunsList.append((run_number, slice_key))
            # END-FOR

            # switch radio button if possible
            if len(reduced_run_number_list) == 0:
                self.ui.radioButton_chooseChopped.setChecked(True)
        # END-IF

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
            assert isinstance(chop_seq_list, list), 'If is chopped data, then neec to give chop sequence list.'
            chop_seq_list.sort()
            label_str += ': chopped sequence {0} - {1}'.format(chop_seq_list[0], chop_seq_list[-1])

        self.ui.label_currentRun.setText(label_str)

        return

    # FIXME - 20180822 - 2 calls of this method does not handle things correctly
    def retrieve_loaded_reduced_data(self, data_key, bank_id, unit):
        """
        Retrieve reduced data from workspace (via run number) to _reducedDataDict.
        Note: this method is used to talk with myController
        :param data_key: a run number (int or string) or data key (i..e, workspace name) or a tuple for chopped run
        :param bank_id:
        :param unit:
        :return:
        """
        print ('[DB...BAT] ReductionDataView: About to retrieve data from API with Data key = {}'.format(data_key))

        data_set = self._myController.get_reduced_data(run_id=data_key, target_unit=unit, bank_id=bank_id)
        # convert to 2 vectors
        vec_x = data_set[bank_id][0]
        vec_y = data_set[bank_id][1]

        return vec_x, vec_y

    # TODO - TONIGHT 3 - Quality
    def launch_single_run_view(self):

        view_window = atomic_data_viewers.AtomicReduced1DViewer(self)
        view_window.show()

        self._atomic_viewer_list.append(view_window)

        return view_window

    def load_sample_logs(self):
        """
        If the diffraction data is loaded from GSAS files, then you need to load the sample logs explicitly
        from associated NeXus files
        :return:
        """
        # TODO/ASAP ASAP2 - Implement!  What is the difference between this and do_plot_sample_logs() ???
        print '[IMPLEMENT] pushButton_loadSampleLogs'

        for gsas_ws_name in self._choppedSequenceList:
            self._choppedSampleDict

        return

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

    def plot_single_run(self, data_key, van_norm, van_run, pc_norm):
        # check existence of data

        bank_id = 1

        entry_key = data_key, bank_id, self._currUnit
        vec_x, vec_y = self.retrieve_loaded_reduced_data(data_key=data_key, bank_id=bank_id,
                                                         unit=self._currUnit)
        line_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y), unit=self._currUnit,
                                                                      over_plot=False,
                                                                      run_id=data_key, bank_id=bank_id,
                                                                      chop_tag=None,
                                                                      label='{}, {}'.format(data_key, bank_id))
        self.ui.graphicsView_mainPlot.set_title(title='whatever title')

        # deal with Y axis
        self.ui.graphicsView_mainPlot.auto_rescale()

        # pop the child atomic window
        for ibank in range(3):
            child_window = self.launch_single_run_view()
            vec_x, vec_y = self.retrieve_loaded_reduced_data(data_key=data_key, bank_id=ibank+1,
                                                             unit=self._currUnit)
            line_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y), unit=self._currUnit,
                                                                          over_plot=False,
                                                                          run_id=data_key, bank_id=bank_id,
                                                                          chop_tag=None,
                                                                          label='{}, {}'.format(data_key, bank_id))
            child_window.plot_data(vec_x, vec_y)

        return

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
        entry_key = data_key, bank_id, self._currUnit

        # synchronize the unit with combobox
        if self._currUnit == 'TOF' and self.ui.comboBox_unit.currentIndex() != 0:
            raise RuntimeError('Current unit {} and combo box unit {} is not synchronized'
                               ''.format(self._currUnit, str(self.ui.comboBox_unit.currentText())))
        elif self._currUnit == 'dSpacing' and self.ui.comboBox_unit.currentIndex() != 1:
            raise RuntimeError('Current unit {} and combo box unit {} is not synchronized'
                               ''.format(self._currUnit, str(self.ui.comboBox_unit.currentText())))

        if entry_key not in self._currentPlotDataKeyDict:
            vec_x, vec_y = self.retrieve_loaded_reduced_data(data_key=data_key, bank_id=bank_id,
                                                             unit=self._currUnit)
            self._currentPlotDataKeyDict[entry_key] = vec_x, vec_y
        else:
            # data already been loaded before
            vec_x, vec_y = self._currentPlotDataKeyDict[entry_key]
        # END-IF

        line_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y), unit=self._currUnit,
                                                                      over_plot=not clear_previous,
                                                                      run_id=data_key, bank_id=bank_id,
                                                                      chop_tag=None,
                                                                      label=label)
        self.ui.graphicsView_mainPlot.set_title(title=title)

        # deal with Y axis
        self.ui.graphicsView_mainPlot.auto_rescale()

        return line_id

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
            assert isinstance(vanadium_run_number, int), 'vanadium run number {0} must be an integer but not a {1}' \
                                                         ''.format(vanadium_run_number, type(vanadium_run_number))
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
        self.update_slice_sequence_widgets(run_number)
        self.ui.checkBox_plotallChoppedLog.setChecked(True)

        # plot
        if len(data_key_dict) == 1:
            # only 1 data: plot 1D
            self.do_plot_diffraction_data()
        else:
            # plot 2D
            self.do_plot_contour()

        return

    def plot_by_data_key(self, data_key, bank_id_list, over_plot, x_limit):
        """ plot reduced data including loaded GSAS or reduced in memory
        :param data_key: str (single run), tuple (chopped run)
        :param bank_id_list:
        :param over_plot:
        :param x_limit:
        :return:
        """
        # check input
        assert isinstance(data_key, str) or isinstance(data_key, tuple),\
            'Data key {0} must be a string or a tuple (for chopped) but not a {1}.'.format(data_key, str(data_key))

        print ('[DB...BAT] Reduction View:  Plot By Data Key = {} of Type {}'.format(data_key, type(data_key)))

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

        if x_limit is None:
            if self._currUnit == 'TOF':
                min_x = 3000.
                max_x = 30000.
            elif self._currUnit == 'dSpacing':
                min_x = 0.3
                max_x = 5.0
            else:
                print ('[ERROR] Unit {} is not defined to support default X-limit'.format(self._currUnit))
                min_x = None
                max_x = None
        else:
            min_x, max_x = x_limit
        self.ui.graphicsView_mainPlot.setXYLimit(xmin=min_x, xmax=max_x)

        self._currentPlotSampleLogs = False

        return

    # TESTME - This is refactored recently
    def plot_multiple_runs_2d(self, ws_key_list, bank_id, target_unit):
        """ Plot multiple runs, including the case for both chopped run and multiple single runs,
        to contour plot. 2D
        :param ws_key_list: list of workspace keys (from the UI's combo box widgets)
        :param bank_id:
        :param target_unit:
        :return:
        """
        # check inputs
        pyvdrive.lib.datatypeutility.check_int_variable('Bank ID', bank_id, (1, None))
        pyvdrive.lib.datatypeutility.check_list('Workspace keys/reference IDs', ws_key_list)
        pyvdrive.lib.datatypeutility.check_string_variable('Unit', target_unit,
                                                           ['dSpacing', 'TOF', 'MomentumTransfer'])

        # get the list of runs
        error_msg = ''
        run_number_list = list()
        data_set_list = list()

        # construct input for contour plot
        for index, data_key in enumerate(ws_key_list):
            # get index number
            if isinstance(data_key, str):
                if data_key.isdigit():
                    index_number = int(data_key)
                else:
                    index_number = index
            elif isinstance(data_key, tuple):
                # TODO FIXME ASAP: this is not a robust way to get index number
                index_number = int(data_key[1].split('_')[-1])
            else:
                raise NotImplementedError('Data key {} must be either a string or a 2-tuple but not a {}'
                                          ''.format(data_key, type(data_key)))

            # get data
            print ('[DB...BAT] Index {1} Run Index {2} Get data from {0}'.format(data_key, index, index_number))
            ret_obj = self._myController.get_reduced_data(data_key, self._currUnit, bank_id=bank_id)

            # re-format return
            vec_x = ret_obj[bank_id][0]
            vec_y = ret_obj[bank_id][1]

            # add to list
            run_number_list.append(index_number)
            data_set_list.append((vec_x, vec_y))
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
        # TODO FIXME ASAP --> make this work!
        # if len(run_number_list) != self._runNumberList:
        #     self._mutexRunNumberList = True
        #     self.ui.comboBox_runs.clear()
        #     for run_number in sorted(run_number_list):
        #         self.ui.comboBox_runs.addItem('{0}'.format(run_number))
        #     self._mutexRunNumberList = False
        # # END-IF

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
        pyvdrive.lib.datatypeutility.check_string_variable('Unit', unit)
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

    # def plot_by_run_number(self, run_number, bank_id, unit=None, over_plot=False):
    #     """
    #     Plot a run by RUN NUMBER (integer) on graph as the API to client method
    #     Requirements:
    #      1. run number is a positive integer
    #      2. bank id is a positive integer
    #     Guarantees:
    #     :param run_number: integer (run number) or string (workspace name/key)
    #     :param bank_id:
    #     :param over_plot:
    #     :param unit:  default (None) by using the current text in the unit-combo-box
    #     :return:
    #     """
    #     # check bank ID; leave the check for run_number to load_reduced_data
    #     assert isinstance(bank_id, int), 'Bank ID %s must be an integer, but not %s.' % (str(bank_id),
    #                                                                                      str(type(bank_id)))
    #     if bank_id <= 0:
    #         raise RuntimeError('Bank ID {0} must be positive.'.format(bank_id))
    #
    #     # Get data (run)
    #     if unit is None:
    #         unit = str(self.ui.comboBox_unit.currentText())
    #     status, error_message = self.retrieve_loaded_reduced_data(run_number, unit)
    #     if not status:
    #         GuiUtility.pop_dialog_error(self, 'Unable to load run {0} due to {1}'.format(run_number, error_message))
    #         return
    #
    #     # update information
    #     self._currRunNumber = run_number
    #     self._currBank = bank_id
    #
    #     # plot
    #     # FIXME/LATER/ line_id does not seems useful here.
    #     line_id = self.plot_1d_diffraction(data_key=run_number, bank_id=bank_id, clear_previous=not over_plot)
    #     self.label_loaded_data(run_number=run_number, is_chopped=False, chop_seq_list=None)
    #
    #     return

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
        """ set IPTS number
        :param ipts_number:
        :return:
        """
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, None))

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
