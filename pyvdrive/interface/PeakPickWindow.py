########################################################################
#
# Window for processing peaks
#
########################################################################
import os
try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5 import QtCore as QtCore
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5.QtWidgets import QMainWindow, QButtonGroup
    from PyQt5.QtWidgets import QFileDialog
except ImportError:
    from PyQt4 import QtCore as QtCore
    from PyQt4.QtGui import QVBoxLayout
    from PyQt4.uic import loadUi as load_ui
    from PyQt4.QtGui import QMainWindow, QButtonGroup
    from PyQt4.QtGui import QFileDialog
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
import pyvdrive.interface.gui.GuiUtility as GuiUtility
import pyvdrive.interface.gui.diffractionplotview as dv
from pyvdrive.interface.peak_processing_helper import GroupPeakDialog, PeakWidthSetupDialog
from pyvdrive.interface.peak_processing_helper import PhaseWidgets, UnitCellList
from pyvdrive.interface.gui.diffractionplotview import DiffractionPlotView
from pyvdrive.interface.gui.vdrivetablewidgets import PeakParameterTable
from pyvdrive.interface import vanadium_controller_dialog
import pyvdrive.core.peak_util as peak_util
from pyvdrive.core import datatypeutility
from pyvdrive.interface import PeakPickWindowVanadium


class PeakPickerMode(object):
    """ Enumerate
    """
    NoPick = 0
    SinglePeakPick = 1
    MultiPeakPick = 2
    AutoMode = 3


class PeakPickerWindow(QMainWindow):
    """ Class for general-purposed plot window
    """
    # class

    def __init__(self, parent=None, controller=None):
        """ Init
        """
        # call base
        QMainWindow.__init__(self, parent)

        assert controller.__class__.__name__.count('VDriveAPI') == 1, \
            'Controller is not a valid VDriveAPI instance , but not %s.' % controller.__class__.__name__

        self._myController = controller
        self.set_data_dir(self._myController.get_working_dir())

        # about loaded runs
        self._loaded_runs = list()
        self._data_info_dict = dict()  # information dictionary: [data key] = (IPTS, Run, Filename)

        # parent
        self._myParent = parent

        # sub window
        self._groupPeakDialog = None

        # mutexes
        self._run_combo_mutex = False

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/VdrivePeakPicker.ui")
        self.ui = load_ui(ui_path, baseinstance=self)
        self._promote_widgets()
        # Set up widgets
        self._phaseWidgetsGroupDict = dict()
        self._init_widgets_setup()

        # child window controller
        self._subControllerVanadium = PeakPickWindowVanadium.PeakPickerWindowChildVanadium(
            self, self.ui)
        self._vanadiumProcessDialog = None

        # Define event handling methods
        # phase set up
        # self.ui.pushButton_setPhases.clicked.connect(self.do_set_phases)
        self.ui.pushButton_clearPhase.clicked.connect(self.do_clear_phases)
        # self.ui.pushButton_cancelPhaseChange.clicked.connect(self.do_undo_phase_changes)

        # peak processing
        self.ui.radioButton_pickModeQuick.toggled.connect(self.evt_switch_peak_pick_mode)
        self.ui.checkBox_pickPeak.stateChanged.connect(self.evt_switch_peak_pick_mode)

        self.ui.pushButton_findPeaks.clicked.connect(self.do_find_peaks)
        self.ui.pushButton_groupAutoPickPeaks.clicked.connect(self.do_group_auto_peaks)
        self.ui.pushButton_readPeakFile.clicked.connect(self.do_import_peaks_from_file)

        self.ui.pushButton_claimOverlappedPeaks.clicked.connect(self.do_claim_overlapped_peaks)

        self.ui.pushButton_showPeaksInTable.clicked.connect(self.do_show_peaks)

        self.ui.pushButton_hidePeaks.clicked.connect(self.do_hide_peaks)

        self.ui.pushButton_setPeakWidth.clicked.connect(self.do_set_peaks_width)

        self.ui.pushButton_sortPeaks.clicked.connect(self.do_sort_peaks)

        self.ui.checkBox_selectPeaks.stateChanged.connect(self.do_select_all_peaks)

        self.ui.pushButton_editTableContents.clicked.connect(self.do_switch_table_editable)

        self.ui.pushButton_deletePeaks.clicked.connect(self.do_delete_peaks)

        self.ui.pushButton_peakPickerMode.clicked.connect(self.do_set_pick_mode)

        self.ui.pushButton_clearGroup.clicked.connect(self.do_clear_groups)
        self.ui.pushButton_resetSelection.clicked.connect(self.do_clear_peak_selection)

        # phase: lattice structure constains
        self.ui.comboBox_structure1.currentIndexChanged.connect(self.evt_structure_1_changed)
        self.ui.comboBox_structure2.currentIndexChanged.connect(self.evt_structure_2_changed)
        self.ui.comboBox_structure3.currentIndexChanged.connect(self.evt_structure_3_changed)

        # vanadium
        self.ui.pushButton_launchVanProcessDialog.clicked.connect(self.do_launch_vanadium_dialog)
        self.ui.pushButton_stripVPeaks.clicked.connect(self.do_strip_vanadium_peaks)
        self.ui.pushButton_smoothVPeaks.clicked.connect(self.do_smooth_vanadium_spectra)
        self.ui.pushButton_resetVPeakProcessing.clicked.connect(self.do_reset_vanadium_processing)
        self.ui.pushButton_saveProcessVanadium.clicked.connect(self.do_save_vanadium_gsas)
        self.ui.pushButton_saveVanSettings.clicked.connect(self.do_save_vanadium_settings)

        self.ui.checkBox_vpeakShowRaw.toggled.connect(self.event_show_raw_van)
        # self.ui.checkBox_vpeakShowStripped.toggled.connect(self.event_show_peaks_striped_van)
        # self.ui.checkBox_vpeakShowSmoothed.toggled.connect(self.event_show_smoothed_van)
        self.ui.checkBox_vpeakShowPeakPos.toggled.connect(self.event_show_vpeaks)

        # load files
        self.ui.pushButton_loadCalibFile.clicked.connect(self.do_load_calibration_file)
        self.ui.pushButton_readData.clicked.connect(self.do_load_data)
        self.ui.comboBox_bankNumbers.currentIndexChanged.connect(self.evt_switch_bank)
        self.ui.comboBox_runNumber.currentIndexChanged.connect(self.evt_switch_run)

        # save_to_buffer
        self.ui.pushButton_save.clicked.connect(self.do_save_peaks)

        self.ui.tableWidget_peakParameter.itemSelectionChanged.connect(
            self.evt_table_selection_changed)

        # get terminal
        self.ui.actionLaunch_Terminal.triggered.connect(self.menu_launch_terminal)

        #
        self.ui.tableWidget_peakParameter.itemSelectionChanged.connect(
            self.evt_table_selection_changed)
        # self.connect(self.ui.tableWidget_peakParameter, QtCore.SIGNAL('itemSelectionChanged()'),
        #              self.evt_table_selection_changed)

        # Define canvas event handlers

        # Menu
        self.ui.actionLoad.triggered.connect(self.menu_load_phase)
        self.ui.actionExit.triggered.connect(self.menu_exit)

        # self.connect(self.ui.actionLoad, QtCore.SIGNAL('triggered()'),
        #              self.menu_load_phase)
        # self.connect(self.ui.actionExit, QtCore.SIGNAL('triggered()'),
        #              self.menu_exit)

        # Reaction to select different mode
        self.ui.comboBox_mode.currentIndexChanged.connect(self.event_change_mode)

        # Define state variables
        self._is_data_loaded = False     # state flag that data is loaded
        self._currentDataFile = None      # name of the data file that is currently loaded
        self._currentRunNumber = None  # current run number
        self._currentBankNumber = -1   # current bank number
        # current data as {bank1: (vecX, vecY, vecE); bank2: (vecX, vecY, vecE) ...}
        self._currentDataSet = dict()
        # disabled. leave to controller self._dataDirectory = None     # default directory to load data
        self._currGraphDataKey = None   # Data key of the current data plot on canvas
        self._dataKeyList = list()

        # Peak selection mode
        self._peakPickerMode = PeakPickerMode.NoPick
        self._peakSelectionMode = ''
        self._indicatorIDList = None
        self._indicatorPositionList = None

        # Mouse position
        self._currMousePosX = 0
        self._currMousePosY = 0

        self._currTableOrder = 0  # 0 for ascending, 1 for descending

        # Phases and initialize
        self._phaseDict = dict()   # keys are pre-set to 1, 2, 3
        for i in range(1, 4):
            self._phaseDict[i] = [None, None, 0., 0., 0.]   # name, type, a, b, c

        # Event handlers lock
        self._evtLockComboBankNumber = False

        # group
        self._autoPeakGroup = None

        # data directory
        self._dataDirectory = None

        self._set_widgets_post()

        return

    def _promote_widgets(self):
        # treeView_iptsRun_layout = QVBoxLayout()
        # self.ui.frame_treeView_iptsRun.setLayout(treeView_iptsRun_layout)
        # self.ui.treeView_iptsRun = SinglePeakFitManageTree(self)
        # treeView_iptsRun_layout.addWidget(self.ui.treeView_iptsRun)

        graphicsView_main_layout = QVBoxLayout()
        self.ui.frame_graphicsView_main.setLayout(graphicsView_main_layout)
        self.ui.graphicsView_main = DiffractionPlotView(self)
        graphicsView_main_layout.addWidget(self.ui.graphicsView_main)

        tableWidget_peakParameter_layout = QVBoxLayout()
        self.ui.frame_tableWidget_peakParameter.setLayout(tableWidget_peakParameter_layout)
        self.ui.tableWidget_peakParameter = PeakParameterTable(self)
        tableWidget_peakParameter_layout.addWidget(self.ui.tableWidget_peakParameter)

        return

    def _init_widgets_setup(self):
        """ Set up initial widget setup
        :return:
        """
        # Hide and disable widgets that are not used
        self.ui.pushButton_readPeakFile.hide()
        self.ui.pushButton_claimOverlappedPeaks.hide()
        self.ui.pushButton_showPeaksInTable.hide()
        self.ui.pushButton_hidePeaks.hide()
        self.ui.pushButton_setPeakWidth.hide()
        self.ui.pushButton_sortPeaks.hide()

        self.ui.tableWidget_peakParameter.setup()

        # Mode
        GuiUtility.set_combobox_items(self.ui.comboBox_mode, [
                                      'Single Peak Selection', 'Vanadium Processing'])

        # set up unit cell string list
        unit_cell_str_list = []
        for tup in UnitCellList:
            info_str = '%s (%s)' % (tup[0], tup[1])
            unit_cell_str_list.append(info_str)
        last_index = len(unit_cell_str_list) - 1
        self.ui.comboBox_structure1.clear()
        self.ui.comboBox_structure1.addItems(unit_cell_str_list)
        self.ui.comboBox_structure1.setCurrentIndex(last_index)
        self.ui.comboBox_structure2.clear()
        self.ui.comboBox_structure2.addItems(unit_cell_str_list)
        self.ui.comboBox_structure2.setCurrentIndex(last_index)
        self.ui.comboBox_structure3.clear()
        self.ui.comboBox_structure3.addItems(unit_cell_str_list)
        self.ui.comboBox_structure3.setCurrentIndex(last_index)

        # Set up the phase widget groups
        phase_widgets1 = PhaseWidgets(self, self.ui.lineEdit_a1, self.ui.lineEdit_b1, self.ui.lineEdit_c1,
                                      self.ui.lineEdit_phaseName1, self.ui.comboBox_structure1,
                                      self.ui.checkBox_usePhase1)
        self._phaseWidgetsGroupDict[1] = phase_widgets1

        phase_widgets2 = PhaseWidgets(self, self.ui.lineEdit_a2, self.ui.lineEdit_b2, self.ui.lineEdit_c2,
                                      self.ui.lineEdit_phaseName2, self.ui.comboBox_structure2,
                                      self.ui.checkBox_usePhase3)
        self._phaseWidgetsGroupDict[2] = phase_widgets2

        phase_widgets3 = PhaseWidgets(self, self.ui.lineEdit_a3, self.ui.lineEdit_b3, self.ui.lineEdit_c3,
                                      self.ui.lineEdit_phaseName3, self.ui.comboBox_structure3,
                                      self.ui.checkBox_usePhase3)
        self._phaseWidgetsGroupDict[3] = phase_widgets3

        # mode of various type of

        # Peak pick mode
        self.ui.peak_picker_mode_group = QButtonGroup(self)
        self.ui.peak_picker_mode_group.addButton(self.ui.radioButton_pickModePower)
        self.ui.peak_picker_mode_group.addButton(self.ui.radioButton_pickModeQuick)
        self.ui.radioButton_pickModeQuick.setChecked(True)
        self.ui.checkBox_pickPeak.setChecked(False)
        self.ui.pushButton_peakPickerMode.setText('Enter Multi-Peak')
        self._peakPickerMode = PeakPickerMode.NoPick
        self.ui.graphicsView_main.set_peak_selection_mode(dv.PeakAdditionState.NonEdit)

        # vanadium
        self.ui.radioButton_vpeakCurrentBank.setChecked(True)

        return

    def _set_widgets_post(self):
        # TODO - TONIGHT
        # set considering event handling
        self.ui.comboBox_structure1.setCurrentIndex(0)
        self.ui.comboBox_structure2.setCurrentIndex(0)
        self.ui.comboBox_structure3.setCurrentIndex(0)

    def do_launch_vanadium_dialog(self):
        """
        launch the vanadium run processing dialog
        :return:
        """
        # launch vanadium dialog window
        if self._vanadiumProcessDialog is None:
            self._vanadiumProcessDialog = vanadium_controller_dialog.VanadiumProcessControlDialog(self)
        self._vanadiumProcessDialog.show()

        return

    def add_grouped_peaks(self):
        """
        :return:
        """
        # check
        if self._autoPeakGroup is None:
            raise RuntimeError('_autoPeakGroup shall be set up before this method is called')

        # get information
        # get bank
        bank = int(self.ui.comboBox_bankNumbers.currentText())

        # get number of groups
        group_id_list = sorted(self._autoPeakGroup.get_group_ids())
        # num_groups = len(group_id_list)

        # clear table as there is NO PEAK ADDITION mode to the table and thus the nameing
        self.ui.tableWidget_peakParameter.clear_selected_peaks()

        # add peak to table
        for index, group_id in enumerate(group_id_list):
            peak_name = ''
            group_left_b, group_right_b = self._autoPeakGroup.get_fit_range(group_id)
            width = group_right_b - group_left_b

            peak_tup_list = self._autoPeakGroup.get_peaks(group_id)
            print('[DB...BAT] {}-group with ID {}: {}'.format(index, group_id, peak_tup_list))

            for peak_tup in peak_tup_list:
                peak_centre = peak_tup[1]
                self.ui.tableWidget_peakParameter.add_peak(bank=bank, name=peak_name,
                                                           centre=peak_centre,
                                                           width=width,
                                                           group_id=group_id)
            # END-FOR
        # END-FOR

        return

    def do_add_picked_peaks(self):
        """ Add the picked up peaks in canvas
        :return:
        """
        # get bank
        bank = int(self.ui.comboBox_bankNumbers.currentText())

        # get number of groups
        num_groups = self.ui.graphicsView_main.get_number_peaks_groups()

        for i_grp in range(num_groups):
            # get peak group
            group = self.ui.graphicsView_main.get_peaks_group(i_grp)

            # skip if group is not editable (in show-only mode)
            if not group.is_editable():
                continue

            peak_name = ''
            width = group.right_boundary - group.left_boundary

            peak_tup_list = group.get_peaks()

            # determine group ID
            if len(peak_tup_list) > 0:
                # single peak or multiple peaks, no group
                # group_id = self.ui.tableWidget_peakParameter
                group_id = group.get_id()
            else:
                # peak group without any peak
                return

            for peak_tup in peak_tup_list:
                peak_center = peak_tup[0]
                print('Peak center = ', peak_center, 'of type', type(peak_center))
                if isinstance(peak_center, tuple):
                    peak_center = peak_center[0]

                self.ui.tableWidget_peakParameter.add_peak(bank=bank, name=peak_name,
                                                           centre=peak_center,
                                                           width=width,
                                                           group_id=group_id)
            # END-IF
            # clone to PeakPickWindow
            # TODO/issue/NOW - shall I implement above?

            # make the group quit the edit mode
            self.ui.graphicsView_main.edit_group(group_id, False)
        # END-FOR

        # quit peak editing mode
        # TODO/FIXME/NOW/ISSUE/62 - this is a dirty solution.  need to have it solved by edit_group(...)
        self.ui.graphicsView_main._inEditGroupList = list()

        return

    def do_claim_overlapped_peaks(self):
        """
        Purpose:
            Claim several peaks to be overlapped according to observation
        Requires:
            Window has been set with parent controller
            data has been loaded;
            mouse is on canvas
            GUI is in peak selection mode
        Guarantees
            the peak under the cursor is added to table

        :return: None
        """
        # Check requirements
        assert self._myController is not None, 'Instance is not initialized.'

        # Get the rows that are selected. Find the next group ID.  Set these rows with same group ID
        row_index_list = self.ui.tableWidget_peakParameter.get_selected_rows()
        assert len(row_index_list) >= 2, 'At least 2 rows should be selected for grouping.'

        # Set the group ID to table
        group_id = self.ui.tableWidget_peakParameter.get_next_group_id()
        for row_index in row_index_list:
            self.ui.tableWidget_peakParameter.set_group_id(row_index, group_id)

        # Show the peak indicators
        peak_pos_list = self.ui.tableWidget_peakParameter.get_selected_peaks()
        for peak_tup in peak_pos_list:
            peak_pos = peak_tup[0]
            peak_width = peak_tup[1]
            self.ui.graphicsView_main.add_picked_peak(peak_pos, peak_width)

        return

    def do_show_peaks(self):
        """
        Purpose:
            Show the selected peaks' indicators
        Requires:
            There must be some peaks to be selected
        Guarantees
            Peaks indicator are shown
        :return:
        """
        # Get positions of the selected peaks
        peak_info_list = self.ui.tableWidget_peakParameter.get_selected_peaks()
        if len(peak_info_list) == 0:
            GuiUtility.pop_dialog_error(self, 'No peak is selected.')
            return

        # Sort peak list
        peak_info_list.sort()

        # Re-set the graph range
        x_min, x_max = self.ui.graphicsView_main.getXLimit()
        if peak_info_list[0][0] < x_min or peak_info_list[-1][0] > x_max:
            # resize the image.  extend the range by 5% of the x min
            new_x_min = min(peak_info_list[0][0], x_min)
            new_x_max = max(peak_info_list[-1][0], x_max)
            dx = new_x_max - new_x_min
            if new_x_min < x_min:
                x_min = new_x_min - dx * 0.05
            if new_x_max > x_max:
                x_max = new_x_max + dx * 0.05
            self.ui.graphicsView_main.setXYLimit(xmin=x_min, xmax=x_max)
        # END-IF

        # Plot
        for peak_info_tup in peak_info_list:
            peak_pos = peak_info_tup[0]
            # peak_width = peak_info_tup[1]
            self.ui.graphicsView_main.plot_peak_indicator(peak_pos)
        # END-FOR

        return

    def do_clear_phases(self):
        """
        Clear all phases
        :return:
        """
        # Clear phase list
        for i_phase in range(1, 4):
            self._phaseDict[i_phase] = ['', '', 0., 0., 0.]

        # Clear all the widgets
        for phase_widgets in self._phaseWidgetsGroupDict:
            phase_widgets.reset()

        return

    def do_clear_groups(self):
        """ Clean grouped peaks
        :return:
        """
        # clear table
        self.ui.tableWidget_peakParameter.clear_selected_peaks()

        # clear the indicators on the image
        self.ui.graphicsView_main.clear_highlight_data()

        return

    def do_clear_peak_selection(self):
        """
        clear picked peaks
        :return:
        """
        print('[DB...BAT] Clear groups first')
        self.do_clear_groups()

        # remove all from Diffraction Plot View
        self.ui.graphicsView_main.reset_selected_peaks()

        return

    def do_clear_peaks_fm_canvas(self):
        """
        Purpose:
          Clear all indicated peaks on canvas
        :return:
        """
        raise NotImplementedError('Add button to GUI')

    def do_delete_peak_fm_canvas(self):
        """
        Purpose:
            Remove the selected/current/highlighted peak from canvas
        :return:
        """
        raise NotImplementedError('Add button to GUI')

    def do_delete_peaks(self):
        """ Delete the selected peak from table and place holder and their indicators
        Requirements:
            At least one peak is selected in the table
        Guarantees:
            The selected peak is removed from both placeholder and table
        :return:
        """
        # Get the rows that contain the peaks to delete
        row_number_list = self.ui.tableWidget_peakParameter.get_selected_rows()
        if len(row_number_list) > 0:
            GuiUtility.pop_dialog_information(self, 'No peak is selected to delete')
            return

        # Delete the selected rows
        self.ui.tableWidget_peakParameter.remove_rows(row_number_list)

        return

    def do_find_peaks(self):
        """
        Purpose:
            Find all peaks in the spectrum by space group calculation
        Requirements:
            Data is loaded
            Peak profile is determined (such as Gaussian or etc)
        Guarantees:
            Find peaks
        :return:
        """
        # Check requirements
        if self._myController is None:
            raise RuntimeError('Controller must be set up.')

        if self._peakPickerMode != PeakPickerMode.AutoMode:
            GuiUtility.pop_dialog_error(self, 'Peak pick mode must be in auto-mode.')
            return

        # Get minimum and maximum d-spacing to calculate by the range in the graph
        min_d = GuiUtility.parse_float(self.ui.lineEdit_xMin)
        max_d = GuiUtility.parse_float(self.ui.lineEdit_xMax)
        if min_d is None:
            min_d = 1.0
            self.ui.lineEdit_xMin.setText('{}'.format(min_d))
        if max_d is None:
            max_d = 2.5
            self.ui.lineEdit_xMax.setText('{}'.format(max_d))
        if min_d >= max_d:
            GuiUtility.pop_dialog_error(
                self, 'Minimum D %f cannot be larger than Maximum D %f.' % (min_d, max_d))

        # List all peaks if any is selected
        num_phases_used = 0
        reflection_list = list()
        err_msg = ''

        # always: 1, 2, 3
        for i_phase in self._phaseDict.keys():  # same as [1, 2, 3]
            # Add all peaks calculated from this phase if it is selected

            # skip the phase if it is not selected
            if self._phaseWidgetsGroupDict[i_phase].is_selected() is False:
                continue

            num_phases_used += 1

            # get the valid phase from widgets
            try:
                phase = self._phaseWidgetsGroupDict[i_phase].get_phase()
            except AssertionError as e:
                err_msg += 'Phase %d cannot be used due to %s.' % (i_phase, str(e))
                continue

            # Calculate peaks' positions
            sub_list = self._myController.calculate_peaks_position(phase, min_d, max_d)
            # for peak_tup in sub_list:
            #     print peak_tup[1], peak_tup[0]
            reflection_list.extend(sub_list)
        # END-FOR

        # Check result
        if len(err_msg) > 0:
            # Phase selected but not valid
            GuiUtility.pop_dialog_error(
                self, 'Unable to calculate reflections due to %s.' % err_msg)
            return

        # other information
        curr_data = str(self.ui.comboBox_runNumber.currentText())

        # Try to find reflections in auto mode
        if num_phases_used == 0:
            peak_position_list = None
            hkl_list = None
            GuiUtility.pop_dialog_information(
                self, 'No phase is selected. Find peak automatically!')
        else:
            peak_position_list = [r[0] for r in reflection_list]
            hkl_list = [r[1] for r in reflection_list]
        # END-IF

        # Use algorithm to find peak automatically
        try:
            found_peaks_list = self._myController.project.find_diffraction_peaks(data_key=curr_data,
                                                                                 bank_number=self._currentBankNumber,
                                                                                 x_range=(
                                                                                     min_d, max_d),
                                                                                 profile='Gaussian',
                                                                                 peak_positions=peak_position_list,
                                                                                 hkl_list=hkl_list)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self, str(run_err))
            return

        #
        #         if status is False:
        #
        #             return
        #         else:
        #             peak_info_list = ret_obj
        #
        #         # Return if no reflection can be found
        #         if len(peak_info_list) == 0:
        #             # No reflection can be found
        #             GuiUtility.pop_dialog_error(self,
        #                                         'Unable to find any reflection between %f and %f.' % (min_d, max_d))
        #             return
        #
        #     except RuntimeError as re:
        #         GuiUtility.pop_dialog_error(self, str(re))
        #         return
        # else:
        #     # Use algorithm find peak with given peak positions to eliminate the non-existing peaks
        #     try:
        #         peak_info_list = self._myController.find_peaks(run_number=self._currentRunNumber,
        #                                                        x_range=(min_d, max_d),
        #                                                        peak_positions=reflection_list[0],
        #                                                        hkl_list=reflection_list[1],
        #                                                        profile='Gaussian')
        #     except RuntimeError as e:
        #         GuiUtility.pop_dialog_error(self, str(e))
        #         return

        # Set the peaks to canvas
        self.ui.graphicsView_main.sort_n_add_peaks(found_peaks_list)

        return

    def do_switch_table_editable(self):
        """ Purpose: switch on/off the edit mode of the peak table
        Guarantees: the table is switched to editable or non-editable mode
        :return:
        """
        # get selected columns
        column_number_list = self.ui.tableWidget_peakParameter.get_selected_columns()

        num_rows = self.ui.tableWidget_peakParameter.rowCount()
        for row_number in range(num_rows):
            for col_index in column_number_list:
                item_i = self.ui.tableWidget_peakParameter.item(row_number, col_index)
                item_i.setFlags(item_i.flags() | QtCore.Qt.ItemIsEditable)
                # self.ui.tableWidget_peakParameter.editItem(item_i)
        # END-FOR

        # get selected row
        # row_number_list = self.ui.tableWidget_peakParameter.get_selected_rows(True)
        # if len(row_number_list) == 0:
        #     GuiUtility.pop_dialog_information(self, 'No row is selected to edit!')

        # # set to editable
        # # FIXME - can we make this more flexible?
        # col_index = 1
        # for row_number in row_number_list:
        #     item_i = self.ui.tableWidget_peakParameter.item(row_number, col_index)

        #     # FIXME/TODO/NOW - Implement this to NTableWidget
        #     item_i.setFlags(item_i.flags() | QtCore.Qt.ItemIsEditable)
        #     self.ui.tableWidget_peakParameter.editItem(item_i)
        # # END-FOR

        # is_editable = self.ui.tableWidget_peakParameter.is_editable()
        # self.ui.tableWidget_peakParameter.set_editable(is_editable)
        # item = self.ui.tableWidget_peakParameter.item(0, 1)

        return

    def do_sort_peaks(self):
        """
        Purpose: sort peaks by peak position in either ascending or descending order.
        Requirements: At least more than 2 rows
        Guarantees: Rows are sorted by column 2 (3rd column)
        :return:
        """
        print('Sorting is enabled?', self.ui.tableWidget_peakParameter.isSortingEnabled())
        # Here is prototype
        p_int = self.ui.tableWidget_peakParameter.get_peak_pos_col_index()
        qt_sort_order = self._currTableOrder
        self.ui.tableWidget_peakParameter.sortByColumn(p_int, qt_sort_order)

        # Switch the sort order for table
        self._currTableOrder = 1 - self._currTableOrder

        return

    def do_group_auto_peaks(self):
        """
        Group all the auto-selected peaks, which are not grouped and added yet, from canvas
        by its position
        :return:
        """
        if self._groupPeakDialog is None:
            self._groupPeakDialog = GroupPeakDialog(self)
        self._groupPeakDialog.show()

        return

    def do_hide_peaks(self):
        """
        Purpose: Highlight all peaks' indicators
        :return:
        """
        self.ui.graphicsView_main.remove_show_only_peaks()

        return

    def do_import_peaks_from_file(self):
        """ Purpose: import peaks' IDs from peak file
        Requirements: my controller is set up
        :return:
        """
        # Check requirement
        assert self._myController is not None

        # get working directory for peak files
        work_dir = self._myController.get_working_dir()
        filters = "Text files (*.txt);; All files (*.*)"
        peak_file = str(QFileDialog.getOpenFileName(self, 'Peak File', work_dir, filters))
        try:
            peak_list = self._myController.import_gsas_peak_file(peak_file)
        except RuntimeError as err:
            GuiUtility.pop_dialog_error(self, str(err))
            return

        # Set the peaks to table
        # clear the previous peaks
        if self.ui.checkBox_keepPeaksInTable.isChecked() is False:
            self.ui.tableWidget_peakParameter.remove_all_rows()

        # Write peaks to table only for the current bank and store the rest to buffer
        for peak_info in peak_list:
            # check
            assert isinstance(peak_info, list)
            assert len(peak_info) == 5
            # parse
            bank = peak_info[0]
            name = peak_info[1]
            peak_pos = peak_info[2]
            peak_width = peak_info[3]
            if peak_info[4] is None:
                overlap_peak_pos_list = []
            else:
                overlap_peak_pos_list = peak_info[4]
                assert isinstance(overlap_peak_pos_list, list)

            if bank == self._currentBankNumber or self._currentBankNumber < 0:
                self.ui.tableWidget_peakParameter.add_peak(
                    bank, name, peak_pos, peak_width, overlap_peak_pos_list)
            else:
                self.ui.tableWidget_peakParameter.add_peak_to_buffer(bank, name, peak_pos, peak_width,
                                                                     overlap_peak_pos_list)
        # END-FOR (peak_info)

        # Check groups

        return

    def evt_structure_1_changed(self):
        # TODO
        self.constrain_structure(self.ui.comboBox_structure1, self.ui.lineEdit_a1, self.ui.lineEdit_b1,
                                 self.ui.lineEdit_c1)

        return

    def evt_structure_2_changed(self):
        # TODO
        self.constrain_structure(self.ui.comboBox_structure2, self.ui.lineEdit_a2, self.ui.lineEdit_b2,
                                 self.ui.lineEdit_c2)

        return

    def evt_structure_3_changed(self):
        # TODO
        self.constrain_structure(self.ui.comboBox_structure3, self.ui.lineEdit_a3, self.ui.lineEdit_b3,
                                 self.ui.lineEdit_c3)

        return

    def constrain_structure(self, combo_box, edit_a, edit_b, edit_c):
        crystal_structure = str(combo_box.currentText())
        if crystal_structure == '':
            GuiUtility.pop_dialog_error(self, 'Empty structure')
            return

        crystal_structure = crystal_structure.strip().split()[0]

        if crystal_structure in ['BCC', 'FCC']:
            edit_b.setText('')
            edit_c.setText('')
            edit_b.setEnabled(False)
            edit_c.setEnabled(False)
        elif crystal_structure == 'HCP':
            edit_b.setText('')
            edit_b.setEnabled(False)
            edit_c.setEnabled(True)
        else:
            edit_b.setEnabled(True)
            edit_c.setEnabled(True)

    def evt_switch_bank(self):
        """
        Save the current selected peaks to a temporary file and load a new bank
        :return:
        """
        # Check lock
        if self._evtLockComboBankNumber:
            return

        # Get new bank
        new_bank = int(self.ui.comboBox_bankNumbers.currentText())
        # check for non-plotting case
        if new_bank == self._currentBankNumber:
            # same bank as before. no need to do anything
            self.statusBar().showMessage('Newly selected bank %d is same as current bank %d.'
                                         '' % (new_bank, self._currentBankNumber))
            return

        # check mode
        curr_mode_index = self.ui.comboBox_mode.currentIndex()
        if curr_mode_index == 0:
            self.switch_peak_picker_bank(new_bank)
        elif curr_mode_index == 1:
            self._currentBankNumber = new_bank
            self._subControllerVanadium.switch_bank(new_bank)
        else:
            GuiUtility.pop_dialog_error(self, 'Function mode {} does not support switching bank'
                                              ''.format(self.ui.comboBox_mode.currentText()))

        return

    def switch_peak_picker_bank(self, new_bank):
        """
        switch to a new bank in peak picker mode
        :param new_bank:
        :return:
        """
        if self._is_data_loaded is False:
            # it is about to load new data, plotting will be called explicitly. no need to re-plot her
            self.statusBar().showMessage('Data is in loading stage. Change to bank %d won\'t have any effect.'
                                         '' % new_bank)
            return

        # Save the current peaks to memory and back up to disk
        # self.ui.tableWidget_peakParameter.save_to_buffer(self._currentBankNumber)

        # set the current ones to new bank
        self._currentBankNumber = new_bank
        # take care of the run number
        if self._currentRunNumber is None:
            self._currentRunNumber = str(self.ui.comboBox_runNumber.currentText())

        # Clear table and canvas
        # self.ui.tableWidget_peakParameter.remove_all_rows()
        self.ui.graphicsView_main.reset_peak_picker_mode()
        self.ui.graphicsView_main.clear_all_lines()

        # TODO/NOW/ISSUE/FUTURE - Need to make the table to add the buffered peaks back
        pass

        # Re-plot
        title = 'Run %s Bank %d' % (str(self._currentRunNumber), self._currentBankNumber)
        vec_x = self._currentDataSet[new_bank][0]
        vec_y = self._currentDataSet[new_bank][1]
        # TODO - NIGHT - Plotting bank pattern shall be refactored to 1 method
        if len(vec_x) == len(vec_y) + 1:
            vec_x = vec_x[:-1]

        self.ui.graphicsView_main.plot_diffraction_pattern(vec_x, vec_y, title=title)

        # TODO - FIXME - TONIGHT 5 - Reset the range of the canvas according last vector X

        return

    def evt_switch_peak_pick_mode(self):
        """
        Switch peak pick mode
        :return:
        """
        if self.ui.checkBox_pickPeak.isChecked():
            # enter the edit mode
            # self.ui.pushButton_addPeaks.setEnabled(True)
            self.ui.radioButton_pickModeQuick.setEnabled(True)
            self.ui.radioButton_pickModePower.setEnabled(True)

            # select the pick up mode
            if self.ui.radioButton_pickModeQuick.isChecked():
                # quick mode
                self._peakPickerMode = PeakPickerMode.AutoMode
                # button enable/disable
                self.ui.pushButton_findPeaks.setEnabled(True)
                self.ui.pushButton_groupAutoPickPeaks.setEnabled(True)
                self.ui.pushButton_peakPickerMode.setEnabled(False)
                # set the graphics view
                self.ui.graphicsView_main.set_peak_selection_mode(dv.PeakAdditionState.AutoMode)

            else:
                # power/manual mode
                self._peakPickerMode = PeakPickerMode.SinglePeakPick
                # button select
                self.ui.pushButton_findPeaks.setEnabled(False)
                self.ui.pushButton_groupAutoPickPeaks.setEnabled(False)
                self.ui.pushButton_peakPickerMode.setEnabled(True)
                # set the graphics view
                self.ui.graphicsView_main.set_peak_selection_mode(dv.PeakAdditionState.NormalMode)

        else:
            # leave the edit mode
            self.ui.graphicsView_main.set_peak_selection_mode(dv.PeakAdditionState.NonEdit)
            self.ui.radioButton_pickModeQuick.setEnabled(False)
            self.ui.radioButton_pickModePower.setEnabled(False)

            # disable all push buttons
            # self.ui.pushButton_addPeaks.setEnabled(False)
            self.ui.pushButton_findPeaks.setEnabled(False)
            self.ui.pushButton_groupAutoPickPeaks.setEnabled(False)
            self.ui.pushButton_peakPickerMode.setEnabled(False)

        return

    def evt_switch_run(self):
        """
        in the event that a new run is set up
        :return:
        """
        if self._run_combo_mutex:   # it disables event from plot_reduced_data
            return

        # get the new run number or workspace name
        new_run_str = str(self.ui.comboBox_runNumber.currentText())
        try:
            new_run_number = int(new_run_str)
            new_workspace_name = None
        except ValueError:
            new_run_number = None
            new_workspace_name = new_run_str
        # END-TRY-EXCEPTION

        # clear the current
        self.ui.graphicsView_main.reset_peak_picker_mode()

        # plot
        if new_workspace_name is None:
            # use run number
            self.plot_reduced_data(new_run_number)
        else:
            # use workspace name
            self.plot_reduced_data(new_workspace_name)

        return

    def do_load_calibration_file(self):
        """
        Purpose:
            Load calibration file
        Requires:
            None
        Guarantees:
            Calibration file is loaded and parsed

        :return:
        """
        # Check requirements
        if self._myController is None:
            raise RuntimeError('Controller has not been set up yet.')

        # Launch dialog box for calibration file name
        file_filter = 'Calibration (*.cal);;Text (*.txt);;All files (*.*)'
        cal_file_name = QFileDialog.getOpenFileName(
            self, 'Calibration File', self._dataDirectory, file_filter)

        # Load
        self._myController.load_calibration_file(cal_file_name)

        return

    # TODO - FUTURE - This method does not have an event to be associated with yet and
    # TODO - cont.  - to be fixed
    def do_load_multiple_gsas(self):
        """

        :return:
        """
        # Get the run numbers
        # FIXME - NIGHT - ...
        if False:
            start_run_number = GuiUtility.parse_integer(self.ui.lineEdit_startRunNumber)
            end_run_number = GuiUtility.parse_integer(self.ui.lineEdit_endRunNumber)
        else:
            start_run_number = None
            end_run_number = None

        # Get the GSAS file names
        gsas_file_list = list()
        if start_run_number is not None and end_run_number is not None:
            # FIXME - NIGHT - Use IPTS and run number and get default dir
            # complete range
            assert start_run_number <= end_run_number, 'End run %d must be larger than ' \
                                                       'or equal to start run %d.' % (end_run_number,
                                                                                      start_run_number)
            # get directory containing GSAS files
            default_dir = self._myController.get_binned_data_dir(
                range(start_run_number, end_run_number))
            gsas_dir = str(QFileDialog.getExistingDirectory(
                self, 'GSAS File Directory', default_dir))

            # form file names: standard VULCAN style
            error_message = ''
            for run_number in range(start_run_number, end_run_number+1):
                gsas_file_name = os.path.join(gsas_dir, '%d.gda' % run_number)
                if os.path.exists(gsas_file_name):
                    gsas_file_list.append(gsas_file_name)
                else:
                    error_message += '%s, ' % gsas_file_name
            # END-FOR

            # output error
            if len(error_message) > 0:
                GuiUtility.pop_dialog_error(self, 'GSAS file %s cannot be found.' % error_message)

        return

    def do_load_data(self):
        """
        Purpose:
            Load GSAS data or a list of GSAS data files
        Requirements:
            Controller has been set to this object
        Guarantees:
            Load data from start run to end run in line edits and plot the first run on canvas
            1. if the range of run numbers is given, then only the directory for all the files shall be specified;
            2. otherwise, a dialog will be popped for the file
        :return:
        """
        # Check requirements
        if self._myController is None:
            raise RuntimeError('Controller/VDriveAPI cannot be None. Initialize first')

        # get IPTS number and run number
        ipts_number = GuiUtility.parse_integer(self.ui.lineEdit_iptsNumber)
        run_number = GuiUtility.parse_integer(self.ui.lineEdit_runNumber)

        # Explicitly to load data if IPTS and run number are not sufficient
        if ipts_number is not None and run_number is not None:
            # well-defined: get data from archive automatically
            gsas_file_name = None
        else:
            # user to input
            if ipts_number:
                # Use IPTS number to determine binned data
                default_dir = '/SNS/VULCAN/IPTS-{}/shared/binned_data/'.format(ipts_number)
                if not os.path.exists(default_dir):
                    default_dir = '/SNS/VULCAN/IPTS-{}/shared'.format(ipts_number)
            else:
                default_dir = self._myController.get_binned_data_directory()

            filters = 'GSAS(*.gda);;All Files(*.*)'
            gsas_file_name = QFileDialog.getOpenFileName(
                self, 'Load GSAS File', default_dir, filters)
            if isinstance(gsas_file_name, tuple):
                gsas_file_name = gsas_file_name[0]
            gsas_file_name = str(gsas_file_name)

            # operation cancelled
            if gsas_file_name == '':
                return
        # END-IF

        self.load_reduced_data(ipts_number, run_number, gsas_file_name)

        # # plot: switch run number will plot the data automatically
        # if data_key:
        #     self.plot_reduced_data(data_key)

        return

    def load_reduced_data(self, ipts_number, run_number, gsas_file_name):
        """
        Load reduced data
        :return:
        """
        # search archive
        if gsas_file_name is None:
            assert ipts_number is not None and run_number is not None, 'Cannot happen'
            gsas_file_name = self._myController.archive_manager.locate_gsas(ipts_number, run_number)
            if gsas_file_name is None:
                GuiUtility.pop_dialog_error(self, 'Unable to find reduced GSAS file for IPTS-{} Run {}'
                                            ''.format(ipts_number, run_number))
                return

        # Load data from GSAS file
        try:
            data_key = self._myController.project.data_loading_manager.load_binned_data(gsas_file_name, 'gsas',
                                                                                        prefix='',
                                                                                        max_int=100, data_key=None,
                                                                                        target_unit='dSpacing')
            self._data_info_dict[data_key] = ipts_number, run_number, gsas_file_name
            # add to tree: self.ui.treeView_iptsRun.add_child_current_item(data_key)

            # set label
            self.ui.label_loadedDataInfo.setText('Loaded {}'.format(gsas_file_name))
        except RuntimeError as re:
            GuiUtility.pop_dialog_error(
                self, 'Failed to load GSAS {}: {}'.format(gsas_file_name, str(re)))
            return None

        # add the new data to combo box
        # determine that the run number is not a new one
        if gsas_file_name is not None:
            # gsas file mode
            combo_item_name = str(data_key)
            # title_message = 'File %s Bank %d' % (data_key, 1)
            # self.ui.label_diffractionMessage.setText('File %s Bank %d' % (data_key, 1))
        else:
            # memory mode (just reduced)
            combo_item_name = str(run_number)
            # title_message = 'Run %d Bank %d' % (run_number, 1)
            # self.ui.label_diffractionMessage.setText('Run %d Bank %d' % (run_number, 1))

        # register this run to the record to avoid adding same item twice
        if combo_item_name not in self._loaded_runs:
            first_flag = len(self._loaded_runs) == 0
            if not first_flag:
                self._run_combo_mutex = True   # lock event triggered from add value to combo box
            self.ui.comboBox_runNumber.addItem(combo_item_name)
            self._run_combo_mutex = False
            self._loaded_runs.append(combo_item_name)

            self.ui.comboBox_runNumber.setCurrentIndex(len(self._loaded_runs) - 1)
            # print ('[DB...BAT] Run number box add {}..of type {}. Load Runs: {}'
            #        ''.format(combo_item_name, type(combo_item_name), self._loaded_runs))

        # self._ipts_number = ipts_number
        # self._run_number = run_number
        #
        # gsas_file_name = None
        # default_dir = None
        # if ipts_number and run_number:
        #     # both are there: load data directly
        #     if not os.path.exists(gsas_file_name):
        #         gsas_file_name = None
        # # END-IF

        return data_key

    def plot_reduced_data(self, data_key):
        """ Load a run from memory and set it correctly to the UI (all the widgets)
        Purpose: Load and plot a run by its data key
        Requirements: Input data key must be either an integer (run number) or a string (data file name)
        Guarantees: Reduced run (run number) or loaded file shall be loaded and plot
        :param data_key: key to the reduced data.  It can be string key or integer key (run number)
        :return:
        """
        # Get run number if data key is recorded in run number
        if isinstance(data_key, int):
            run_number = data_key
        else:
            datatypeutility.check_string_variable('Data key/Workspace', data_key)
            if data_key.isdigit():
                run_number = int(data_key)
            else:
                run_number = None
            # END-IF-ELSE
        # END-IF-ELSE

        # Get reduced run information: list of BANKs
        if run_number is None:
            # in case of a loaded data file (gsas, fullprof..)
            status, ret_obj = self._myController.get_reduced_run_info(
                run_number=None, data_key=data_key)
        else:
            # in case of a previously reduced run
            status, ret_obj = self._myController.get_reduced_run_info(run_number)
        # END-IF-ELSE
        if status:
            bank_id_list = ret_obj
        else:
            GuiUtility.pop_dialog_error(self, str(ret_obj))
            return

        # Set the mutex flag
        self._is_data_loaded = False

        # Update widgets, including run number, bank IDs (bank ID starts from 1)
        self._evtLockComboBankNumber = True
        self.ui.comboBox_bankNumbers.clear()
        for i_bank in bank_id_list:
            assert isinstance(i_bank, int), 'Bank index %s should be integer but not %s.' \
                                            '' % (str(i_bank), str(type(i_bank)))
            self.ui.comboBox_bankNumbers.addItem(str(i_bank))
        self.ui.comboBox_bankNumbers.setCurrentIndex(0)
        self._evtLockComboBankNumber = False

        # self.ui.comboBox_runNumber.clear()

        # # determine that the run number is not a new one
        if run_number is None:
            # combo_item_name = str(data_key)
            title_message = 'File %s Bank %d' % (data_key, 1)
            # self.ui.label_diffractionMessage.setText('File %s Bank %d' % (data_key, 1))
        else:
            # combo_item_name = str(run_number)
            title_message = 'Run %d Bank %d' % (run_number, 1)
            # self.ui.label_diffractionMessage.setText('Run %d Bank %d' % (run_number, 1))
        #
        # # register this run to the record to avoid adding same item twice
        # if combo_item_name not in self._loaded_runs:
        #     self._run_combo_mutex = True   # lock event triggered from add value to combo box
        #     self.ui.comboBox_runNumber.addItem(combo_item_name)
        #     self._loaded_runs.append(combo_item_name)
        #     self.ui.comboBox_runNumber.setCurrentIndex(len(self._loaded_runs) - 1)
        #     self._run_combo_mutex = False
        #     # print ('[DB...BAT] Run number box add {}..of type {}. Load Runs: {}'
        #     #        ''.format(combo_item_name, type(combo_item_name), self._loaded_runs))

        # Plot data: load bank 1 as default
        try:
            if run_number is None:
                data_set_dict = self._myController.get_reduced_data(data_key, 'dSpacing')
            else:
                data_set_dict = self._myController.get_reduced_data(run_number, 'dSpacing')
        except RuntimeError as run_err:
            err_msg = 'Unable to retrieve reduced data in dSpacing from {}/{} due to {}' \
                      ''.format(run_number, data_key, run_err)
            GuiUtility.pop_dialog_error(self, err_msg)
            return
        # get spectrum 0, i.e, bank 1
        self._currentDataSet = data_set_dict

        data_bank_1 = self._currentDataSet[1]
        vec_x = data_bank_1[0]
        vec_y = data_bank_1[1]
        if len(vec_x) == len(vec_y) + 1:
            vec_x = vec_x[:-1]

        # reset the current view including all the indicators
        self.ui.graphicsView_main.reset_peak_picker_mode()
        # plot loaded diffraction data
        self.ui.graphicsView_main.plot_diffraction_pattern(vec_x, vec_y, title=title_message)

        # Set up class variables
        self._currentRunNumber = run_number
        self._currentBankNumber = 1
        self._currGraphDataKey = data_key

        # Release the mutex flag
        self._is_data_loaded = True

        return

    def do_set_pick_mode(self):
        """ Enter for leave peak picker mode
        :return:
        """
        # check validity
        assert self._peakPickerMode != PeakPickerMode.NoPick, 'Peak-picking mode cannot be NoPick if ' \
                                                              'button peak mode selection is pushed.'

        # select the peak pick mode and change the text of push button for next selection
        if self._peakPickerMode == PeakPickerMode.SinglePeakPick:
            # current is multiple peak mode, switch single-peak mode
            self._peakPickerMode = PeakPickerMode.MultiPeakPick
            self.ui.graphicsView_main.set_peak_selection_mode(dv.PeakAdditionState.MultiMode)
            # change UI indications
            self.ui.graphicsView_main.canvas().set_title('Multi-Peaks Selection', color='red')
            # next will be multi-peak mode again
            self.ui.pushButton_peakPickerMode.setText('Enter Single-Peak Mode')

        elif self._peakPickerMode == PeakPickerMode.MultiPeakPick:
            # current is multiple peak mode, switch single-peak mode
            self._peakPickerMode = PeakPickerMode.SinglePeakPick
            self.ui.graphicsView_main.set_peak_selection_mode(dv.PeakAdditionState.NormalMode)
            # change UI indications
            self.ui.graphicsView_main.canvas().set_title('Single-Peak Selection', color='blue')
            # next will be multi-peak mode again
            self.ui.pushButton_peakPickerMode.setText('Enter Multi-Peak Mode')

        else:
            raise RuntimeError('Mode %s is not supported.' % str(self._peakPickerMode))

        return

    def do_quit(self):
        """
        Purpose:
            Close the dialog window without savinge
        Requires:
            None
        Guarantees:
            Nothing.  All current information will be lost
        :return:
        """
        self.close()

        return

    def do_save_peaks(self):
        """
        Purpose:
            Save peaks selected by user
        Requires:
            At least one peak is selected
        Guarantees:
            Save the peak positions and other parameters to controller
        :return:
        """
        # Check requirements
        assert self._myController is not None, 'My controller cannot be None'

        # Get the output file
        file_filter = 'Text (*.txt);;All files (*.*)'
        default_dir = self._dataDirectory
        out_file_name = GuiUtility.get_save_file_by_dialog(parent=self,
                                                           title='Save peaks to GSAS peak file',
                                                           default_dir=default_dir,
                                                           file_filter=file_filter)

        # out_file_name = QFileDialog.getSaveFileName(self, 'Save peaks to GSAS peak file',
        #                                             self._dataDirectory, file_filter)
        # if isinstance(out_file_name, tuple):
        #     out_file_name = out_file_name[0]
        # out_file_name = str(out_file_name).strip()
        if out_file_name == '':
            return   # return for cancellation

        # Get the peaks from buffer
        print('Get buffered peaks of bank %d' % self._currentBankNumber)
        peak_bank_dict = self.ui.tableWidget_peakParameter.get_buffered_peaks(
            excluded_banks=[self._currentBankNumber])

        # Get the peaks from table
        num_peaks = self.ui.tableWidget_peakParameter.rowCount()
        peak_list = list()
        for i_peak in range(num_peaks):
            # get a list from the peak
            peak_i = self.ui.tableWidget_peakParameter.get_peak(i_peak)
            peak_list.append(peak_i)
        peak_bank_dict[self._currentBankNumber] = peak_list

        # Check
        total_peaks = 0
        for peak_list in peak_bank_dict.values():
            total_peaks += len(peak_list)
        if total_peaks == 0:
            GuiUtility.pop_dialog_error(
                self, 'No peak is selected.  Unable to execute saving peaks.')
            return

        # Set the selected peaks to controller
        self._myController.export_gsas_peak_file(peak_bank_dict, out_file_name)

        return

    def do_select_all_peaks(self):
        """
        Purpose: select or de-select all peaks
        Requirements: None
        Guarantees: select or de-select all peaks according to check box selectPeaks
        :return:
        """
        select_all_peaks = self.ui.checkBox_selectPeaks.isChecked()
        self.ui.tableWidget_peakParameter.select_all_rows(select_all_peaks)

        return

    def do_set_peaks_width(self):
        """
        Purpose: set selected peaks' width to same value
        Requirements: ... ...
        Guarantees: ... ...
        :return:
        """
        # Create the dialog
        peak_width_dialog = PeakWidthSetupDialog(self)
        peak_width_dialog.exec_()

        try:
            peak_width = peak_width_dialog.get_peak_width()
            # TODO - WHAT TO DO WITH SET PEAKS WITH?
            print('Peaks width is set to {}'.format(peak_width))
        except AssertionError:
            pass

        return

    def do_set_phases(self):
        """ Set the parameters value of phases to
        Purpose: Read the parameter values from GUI and set them up in list
        Requirements: if any input have a value set up, then it must be correct!
        Guarantees: the values are set
        :return:
        """
        # Check whether phase dictionary that have been set up.
        assert len(self._phaseDict) == 3

        # Set the values
        for i_phase in self._phaseWidgetsGroupDict.keys():
            self._phaseWidgetsGroupDict[i_phase].get_phase_value(self._phaseDict[i_phase])

        return

    def do_undo_phase_changes(self):
        """ Purpose: undo all the changes from last 'set phase' by get the information from
        the save_to_buffer phase parameters
        Requirements: None
        Guarantees:
        :return:
        """
        for i_phase in range(1, 4):
            self._phaseWidgetsGroupDict[i_phase].set_values(self._phaseDict[i_phase])

        return

    def evt_table_selection_changed(self):
        """
        Event handling as the selection of the row changed
        Used to be linked to
        self.ui.tableWidget_peakParameter.itemSelectionChanged.connect(self.evt_table_selection_changed)

        :return:
        """
        print('[Prototype] current row is ', self.ui.tableWidget_peakParameter.currentRow(),
              self.ui.tableWidget_peakParameter.currentColumn())

        """
        print type(self.ui.tableWidget_peakParameter.selectionModel().selectedRows())
        model_selected_rows = self.ui.tableWidget_peakParameter.selectionModel().selectedRows()
        print self.ui.tableWidget_peakParameter.selectionModel().selectedRows()

        mode_index = model_selected_rows[0]
        print mode_index.row
        print mode_index.row()
        print type(mode_index.row())
        """

        return

    def clear_group_highlight(self):
        """

        :return:
        """
        self.ui.graphicsView_main.clear_highlight_data()

        return

    # TODO - NIGHT - Clean
    def group_peaks(self, resolution, num_fwhm):
        """
        Group a list of peaks for fitting
        :param resolution:
        :param num_fwhm:
        :return:
        """
        # get single peaks from canvas
        raw_peak_pos_list = self.ui.graphicsView_main.get_ungrouped_peaks()
        # TODO/DEBUG/FIXME/ - Find out why do grouping a few time can cause duplicate peaks in table
        print('[DB...#33] Number of raw peaks = {0} with peak positions: {1}.'
              ''.format(len(raw_peak_pos_list), raw_peak_pos_list))

        # call controller method to set group boundary
        peak_group = peak_util.group_peaks_to_fit(raw_peak_pos_list, resolution, num_fwhm)
        assert isinstance(peak_group, peak_util.PeakGroupCollection),\
            'Peak group {0} must be a PeakGroupCollection instance but not a {1}.'.format(
                peak_group, type(peak_group))

        # clear previous grouped peaks' presentation on PLOT
        self.clear_group_highlight()

        # reflect the grouped peak to GUI
        group_color = 'blue'
        for group_id in sorted(peak_group.get_group_ids()):
            # get the group's fit range
            left_range, right_range = peak_group.get_fit_range(group_id)
            # highlight the data
            self.ui.graphicsView_main.highlight_data(left_range, right_range, group_color)

            # set to next color
            if group_color == 'blue':
                group_color = 'green'
            else:
                group_color = 'blue'
        # END-FOR

        # set the returned peak group to class variable for future
        self._autoPeakGroup = peak_group

        return

    def load_runs(self, run_id_list):
        """
        Load runs and called from tree!
        :param run_id_list:
        :return:
        """
        # Return error message
        if len(run_id_list) == 0:
            GuiUtility.pop_dialog_error(self, 'No run is given!')
            return

        # Plot
        self.plot_reduced_data(run_id_list[0])

        return

    # def set_controller(self, controller):
    #     """ Set up workflow controller to this window object
    #     Purpose: Set the workflow controller to this window object
    #     Requirement: controller must be VDriveAPI or Mock
    #     Guarantees: controller is set up. Reduced runs are get from controller and set to
    #     :param controller:
    #     :return:
    #     """
    #     assert controller.__class__.__name__.count('VDriveAPI') == 1, \
    #         'Controller is not a valid VDriveAPI instance , but not %s.' % controller.__class__.__name__
    #
    #     self._myController = controller
    #     self.set_data_dir(self._myController.get_working_dir())
    #
    #     # Get reduced data
    #     reduced_run_number_list = self._myController.get_loaded_runs(chopped=False)
    #     ipts = 1
    #
    #     # Set
    #     # self.ui.treeView_iptsRun.add_ipts_runs(ipts_number=ipts, run_number_list=reduced_run_number_list)
    #
    #     return

    def menu_add_peak(self):
        """ Add a peak to table
        Purpose: Add a peak under cursor in a simple way
        Requirements:
        Guarantees: add peak from graphic view's pop-up menu
        :return:
        """
        # Get common information
        bank_number = int(self.ui.comboBox_bankNumbers.currentText())
        peak_name = 'new'

        # 2 situation
        if self._indicatorPositionList is None:
            # simple peak adding mode
            peak_pos = self._currMousePosX
            peak_width = 0.03
        else:
            # read from GUI
            peak_pos = self._indicatorPositionList[0]
            peak_width = abs(self._indicatorPositionList[0] - self._indicatorPositionList[1])

        # Add peak to table
        overlapped_peaks_list = []
        self.ui.tableWidget_peakParameter.add_peak(bank_number, peak_name, peak_pos, peak_width,
                                                   overlapped_peaks_list)

        # Quit selection mode
        self.menu_cancel_selection()

        return

    def menu_cancel_selection(self):
        """ Abort the operation to select peak
        Purpose:
        Guarantees: all 3 indicator line will be deleted; peak selection mode will be reset
        :return:
        """
        # Delete all 3 indicators line
        for indicator_id in self._indicatorIDList:
            self.ui.graphicsView_main.remove_indicator(indicator_id)

        # Reset all the variables
        self._indicatorIDList = None
        self._indicatorPositionList = None
        self._peakSelectionMode = ''

        return

    def menu_exit(self):
        """
        Quit the window
        :return:
        """
        self.close()

        return

    def menu_launch_terminal(self):
        """
        Launch terminal window
        :return:
        """
        self._myParent.menu_workspaces_view()

        return

    def menu_load_phase(self):
        """
        Load a file with phase information
        :return:
        """
        # Get the file name
        file_filter = 'Text (*.txt);;All files (*.*)'
        phase_file_name = QFileDialog.getOpenFileName(self, 'Import phase information', self._dataDirectory,
                                                            file_filter)

        # return if action is cancelled
        if phase_file_name is None:
            return
        phase_file_name = str(phase_file_name)
        if len(phase_file_name.strip()) == 0:
            return

        # TODO/NOW/1st: import phase file and set widgets
        print('Importing phase information file!')

        return

    def menu_select_peak(self):
        """ Select a peak including specifying its width and position
        Purpose:
        Requirements:
        Guarantees:
            1. Add 3 vertical indicators at the same Y
            2. The graph mode is in peak selecting
        :return:
        """
        x = self._currMousePosX
        id_centre = self.ui.graphicsView_main.add_vertical_indicator(x, color='red')
        id_left = self.ui.graphicsView_main.add_vertical_indicator(x, color='red')
        id_right = self.ui.graphicsView_main.add_vertical_indicator(x, color='red')

        self._peakSelectionMode = 'MoveCentre'
        self._indicatorIDList = [id_centre, id_left, id_right]
        self._indicatorPositionList = [x, x, x]

    def menu_switch_mode(self):
        """ Switch peak selection mode
        :return:
        """
        if self._peakSelectionMode == 'MoveCentre':
            self._peakSelectionMode = 'ChangeWidth'
        elif self._peakSelectionMode == 'ChangeWidth':
            self._peakSelectionMode = 'MoveCentre'
        else:
            raise RuntimeError('Peak selection mode %s is not switchable.' %
                               self._peakSelectionMode)

        return

    def on_mouse_motion(self, event):
        """ Event handling in case mouse is moving
        """
        new_x = event.xdata
        new_y = event.ydata

        # Outside of canvas, no response
        if new_x is None or new_y is None:
            return

        # no need to respond to any moving if not in edit mode or quick-pick mode
        if not self._inEditMode or self._peakPickerMode != PeakPickerMode.AutoMode:
            # just return as no operation is required
            return

        # Determine resolution dynamically
        min_x, max_x = self.ui.graphicsView_main.getXLimit()
        resolution = (max_x - min_x) * 0.001

        # Ignore moving with small step
        dx = new_x - self._currMousePosX
        if abs(dx) < resolution:
            # operation is required. just return
            return

        not_update = False
        if self._inEditMode and self._peakSelectionMode == 'MoveCentre':
            self.move_peak_position(new_x)
        elif self._inEditMode and self._peakSelectionMode == 'ChangeWidth':
            self.move_peak_boundary(new_x)
            not_update = True
        else:
            err_msg = 'It is not right such that InEditMode is %s and SelectionMode is %s.' % (
                str(self._inEditMode), self._peakSelectionMode)
            raise RuntimeError(err_msg)

        # Update
        if not_update is False:
            self._currMousePosX = new_x
            self._currMousePosY = new_y

        return

    def move_peak_boundary(self, pos_x):
        """ Move the boundary of the peak to position
        :param pos_x:
        :return:
        """
        # check inputs
        datatypeutility.check_float_variable('Peak boundary', pos_x, (None, None))

        # Find out how to expand
        if pos_x < self._currMousePosX:
            left_bound = pos_x
            right_bound = 2*self._currMousePosX - pos_x
        else:
            right_bound = pos_x
            left_bound = 2*self._currMousePosX - pos_x

        # left peak (indicator) to x-position
        left_id = self._indicatorIDList[1]
        dx = left_bound - self._indicatorPositionList[1]
        self.ui.graphicsView_main.move_indicator(left_id, dx, 0)

        # right peak (indicator) to x-position
        right_id = self._indicatorIDList[2]
        dx = right_bound - self._indicatorPositionList[2]
        self.ui.graphicsView_main.move_indicator(right_id, dx, 0)

        # update
        self._indicatorPositionList[1] = left_bound
        self._indicatorPositionList[2] = right_bound

        return

    def move_peak_position(self, pos_x):
        """
        Purpose: move peak's position including its indicators
        :param pos_x:
        :return:
        """
        # Check
        assert isinstance(
            pos_x, float), 'X-position {0} must be a float but not a {1}.'.format(pos_x, type(pos_x))

        # Find dx
        dx = pos_x - self._currMousePosX

        # Update indicator positions
        for i in range(3):
            self._indicatorPositionList[i] += dx

        # Move indicators
        for i in range(3):
            indicator_id = self._indicatorIDList[i]
            self.ui.graphicsView_main.move_indicator(indicator_id, dx, 0)
        # END-FOR

        return

    def set_data_dir(self, data_dir):
        """
        Set default data directory
        :param data_dir:
        :return:
        """
        # check inputs
        assert isinstance(data_dir, str), 'Input data directory {0} must be a string but not a {1}.' \
                                          ''.format(data_dir, type(data_dir))
        assert os.path.exists(data_dir), 'Data directory {0} cannot be found.'.format(data_dir)

        # set up
        self._dataDirectory = data_dir

        return

    def event_change_mode(self):
        """
        Change function mode among: peak picking, vanadium processing and future options
        :return:
        """
        new_mode_index = self.ui.comboBox_mode.currentIndex()

        for tab_index in range(3):
            self.ui.tabWidget_functionControl.setTabEnabled(tab_index, tab_index == new_mode_index)

        if new_mode_index == 0:
            # process peaks for single peak fitting (VDRIVE)
            self._subControllerVanadium.reset_processing()
            # TODO - TONIGHT 1 - Implement a method to plot current data
        elif new_mode_index == 1:
            # process vanadium peaks
            ipts_number, run_number, gsas_file_name = self._data_info_dict[self._currGraphDataKey]
            # if previous is 1   FIXME TODO - TOMORROW - If there are more than 2. This is redundant
            self.reset_plot_session()
            self.ui.checkBox_pickPeak.setChecked(False)
            #
            self._subControllerVanadium.set_vanadium_info(ipts_number, run_number)
            self._subControllerVanadium.init_session(self._currGraphDataKey)
            self._subControllerVanadium.plot_raw_dspace(self._currentBankNumber)
            self.ui.checkBox_vpeakShowPeakPos.setChecked(False)
        # END-IF-ELSE

        return

    def do_strip_vanadium_peaks(self):
        """ Strip vanadium peaks
        :return:
        """
        self._subControllerVanadium.strip_vanadium_peaks(None)

        return

    def do_smooth_vanadium_spectra(self):
        """ Smooth vanadium spectra
        :return:
        """
        self._subControllerVanadium.smooth_vanadium_peaks(None, None, None, None)

        return

    def do_reset_vanadium_processing(self):
        """ Reset vanadium processing to beginning
        :return:
        """
        self._subControllerVanadium.reset_processing()

    def do_save_vanadium_gsas(self):
        """
        save current processed vanadium to GSAS and also saved the configuration
        :return:
        """
        self._subControllerVanadium.save_processing_result()

    def do_save_vanadium_settings(self):
        """
        Save the vanadium processing parameters to file
        :return:
        """
        self._subControllerVanadium.save_vanadium_process_parameters()

    def reset_plot_session(self):
        """ Reset plot
        :return:
        """
        # plots shall be reset and re-load data
        self.ui.graphicsView_main.reset_peak_picker_mode(remove_diffraction_data=True)
        self._peakPickerMode = PeakPickerMode.NoPick
        self._peakSelectionMode = ''

        print('[DB...BAT] Reset self._indicatorIDList (\n{}\n) to None'.format(self._indicatorIDList))
        self._indicatorIDList = None
        print('[DB...BAT] Reset self._indicatorPositionList (\n{}\n) to None'.format(
            self._indicatorPositionList))
        self._indicatorPositionList = None

        return

    # TODO - TONIGHT 3 - Complete rewrite the signal handling methods including plotting data!
    def signal_save_processed_vanadium(self, output_file_name, run_number):
        """
        save GSAS file from GUI
        :param output_file_name:
        :param run_number:
        :return:
        """
        # convert string
        output_file_name = str(output_file_name)

        self._myController.project.vanadium_processing_manager.save_to_gsas(
            run_number, output_file_name)

        return

    def signal_strip_vanadium_peaks(self, bank_group_index, peak_fwhm, tolerance, background_type, is_high_background):
        """ Process the signal to strip vanadium peaks
        :param bank_group_index:
        :param peak_fwhm: integer
        :param tolerance:
        :param background_type:
        :param is_high_background:
        :return:
        """
        self._subControllerVanadium.strip_vanadium_peaks(None,
                                                         peak_fwhm, tolerance, str(background_type),
                                                         is_high_background)

        return

    def signal_smooth_vanadium(self, flag, smoother_type, param_n, param_order):
        """
        process the signal to smooth vanadium spectra
        :param smoother_type:
        :param param_n:
        :param param_order:
        :return:
        """
        # convert smooth_type to string from unicode
        smoother_type = str(smoother_type)
        print('[DB...BAT] Signal received: Smooth type = {}, n = {}, order = {}'
              ''.format(smoother_type, param_n, param_order))

        self._subControllerVanadium.smooth_vanadium_peaks(None, smoother_type, param_n,
                                                          param_order)

        return

    def signal_undo_strip_van_peaks(self):
        """
        undo the strip vanadium peak action, i.e., delete the previous result and remove the plot
        :return:
        """
        if self._vanStripPlotID is None:
            print('[INFO] There is no vanadium-peak-removed spectrum to remove from canvas.')
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
            print('[INFO] There is no smoothed spectrum to undo.')
            return

        # remove the plot
        self.ui.graphicsView_mainPlot.remove_line(self._vanStripPlotID)
        self._smoothedPlotID = None

        # undo in the controller
        self._myController.undo_vanadium_smoothing()

        return

    def event_show_raw_van(self):
        """
        Show or hide raw vanadium run on canvas
        :return:
        """
        self._subControllerVanadium.show_hide_raw_data(self.ui.checkBox_vpeakShowRaw.isChecked())
        return

    def event_show_vpeaks(self):
        """ Show or hide vanadium peaks' indicators
        :return:
        """
        self._subControllerVanadium.show_hide_v_peaks(self.ui.checkBox_vpeakShowPeakPos.isChecked())
        return
