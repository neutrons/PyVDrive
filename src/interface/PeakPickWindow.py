########################################################################
#
# Window for set up log slicing splitters
#
########################################################################
import sys
import os
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.GuiUtility as GuiUtility
import gui.VdrivePeakPicker as VdrivePeakPicker


# List of supported unit cell
UnitCellList = [('BCC', 'I m -3 m'),
                ('FCC', 'F d -3 m'),
                ('HCP', 'P 63/m m c'),
                ('Body-Center', 'I m m m'),
                ('Face-Center', 'F m m m'),
                ('Primitive', 'P m m m')]


class PhaseWidgets(object):
    """
    A set of widgets to define a phase
    """
    def __init__(self, parent, edit_a, edit_b, edit_c, edit_name, combo_box_type, check_box_select):
        """
        Initialize the phase widgets group
        Requirements: all the inputs should be the proper PyQt widgets
        :return:
        """
        # Check requirements
        assert isinstance(parent, QtGui.QMainWindow)
        assert isinstance(edit_a, QtGui.QLineEdit)
        assert isinstance(edit_b, QtGui.QLineEdit)
        assert isinstance(edit_c, QtGui.QLineEdit)
        assert isinstance(edit_name, QtGui.QLineEdit)
        assert isinstance(combo_box_type, QtGui.QComboBox)
        assert isinstance(check_box_select, QtGui.QCheckBox)

        # Lattice parameters
        self._lineEdit_a = edit_a
        self._lineEdit_b = edit_b
        self._lineEdit_c = edit_c
        # Phase' name
        self._lineEdit_name = edit_name
        # Phase' type
        self._comboBox_type = combo_box_type
        # Phase selected or not
        self._checkBox_selected = check_box_select

        # set up the unit cell dictionary
        self._cellTypeList = list()
        for type_tup in UnitCellList:
            self._cellTypeList.append(type_tup[0])

        parent.connect(combo_box_type, QtCore.SIGNAL('currentIndexChanged(int)'),
                       self.event_space_group_changed)

        return

    def enable_widgets(self, enabled):
        """

        :param enabled:
        :return:
        """
        assert isinstance(enabled, bool)

        self._lineEdit_a.setEnabled(enabled)
        self._lineEdit_b.setEnabled(enabled)
        self._lineEdit_c.setEnabled(enabled)
        self._comboBox_type.setEnabled(enabled)
        self._lineEdit_name.setEnabled(enabled)

        return

    def event_space_group_changed(self):
        """
        Purpose: handle the change of space group
        Requirements:
        :return:
        """
        curr_space_group = str(self._comboBox_type.currentText())

        cell_type = curr_space_group.split()[0]

        self.set_unit_cell_type(cell_type)

        return

    def get_phase_value(self, phase_value_list):
        """
        Purpose: set the phase values to the input list. It is used for save_to_buffer the values of phase temporarily.
            if value is not set up, then it will ignored;
        Requirements:  if the value is set, then it must be valid

        :param phase_value_list:
        :return:
        """
        # Check requirements:
        assert isinstance(phase_value_list, list), 'bla bla'
        assert len(phase_value_list) == 5

        # Set name
        phase_value_list[0] = str(self._lineEdit_name.text()).strip()
        # Set phase
        phase_value_list[1] = str(self._comboBox_type.currentText()).split()[0]
        # Set a, b and c
        a = GuiUtility.parse_float(self._lineEdit_a)
        phase_value_list[2] = a
        b = GuiUtility.parse_float(self._lineEdit_b)
        phase_value_list[3] = b
        c = GuiUtility.parse_float(self._lineEdit_c)
        phase_value_list[4] = c

        return

    def get_phase(self):
        """
        Get the phase's parameters
        Requirements:
        1. a, b and c are positive floats
        2. phase name must be given
        :return: list as [name, type, a, b, c]
        """
        name = str(self._lineEdit_name.text()).strip()
        assert len(name) > 0, 'Phase name must be given!'

        cell_type = str(self._comboBox_type.currentText()).split()[0]
        try:
            a = float(self._lineEdit_a.text())
            if self._lineEdit_b.isEnabled():
                b = float(self._lineEdit_b.text())
            else:
                b = a
            if self._lineEdit_c.isEnabled():
                c = float(self._lineEdit_c.text())
            else:
                c = a
        except TypeError as e:
            raise RuntimeError('Lattice parameters a, b or c does not have correct value. Error: %s.' % str(e))

        return [name, cell_type, a, b, c]

    def is_selected(self):
        """
        Return the flag whether this phase is selected
        :return:
        """
        return self._checkBox_selected.isChecked()

    def reset(self):
        """
        Reset the widgets
        :return:
        """
        # Clear name, a, b, c
        self._lineEdit_a.setText('')
        self._lineEdit_b.setText('')
        self._lineEdit_c.clear()
        self._lineEdit_name.setText('')

        # Set the unit type to primitive
        self.set_unit_cell_type('Primitive')

        return

    def set_lattice_widgets_values(self, cell_type):
        """
        Purpose:
            enable or disabled some widgets according to unit cell type
            set the values to disabled lattice parameters
        :param cell_type:
        :return:
        """
        assert cell_type in self._cellTypeList, 'Unit cell type %s is not supported.' % cell_type

        if cell_type in ['BCC', 'FCC']:
            # Disable inputs for b and c
            self._lineEdit_b.setEnabled(False)
            self._lineEdit_c.setEnabled(False)
            self._lineEdit_b.setText('')
            self._lineEdit_c.setText('')
        elif cell_type in ['HCP']:
            # Disable b and enable c
            self._lineEdit_b.setEnabled(False)
            self._lineEdit_c.setEnabled(True)
            self._lineEdit_b.setText('')
        else:
            # enable all
            self._lineEdit_b.setEnabled(True)
            self._lineEdit_c.setEnabled(True)

        return

    def set_unit_cell_type(self, cell_type):
        """
        Set unit cell type and enable/disable the line edits for a, b and c
        :param cell_type:
        :return:
        """
        # Check
        assert isinstance(cell_type, str)
        assert cell_type in self._cellTypeList, 'Unit cell type %s is not supported.' % cell_type

        # Set
        list_index = self._cellTypeList.index(cell_type)
        self._comboBox_type.setCurrentIndex(list_index)

        # Disable some
        self.set_lattice_widgets_values(cell_type)

        return

    def set_value(self, unit_cell_value):
        """ Set value to unit cell (usually for undo)
        Purpose: set the values of unit cell (stored in list) to widgets
        Requirements: unit cell value should be stored in a list with 5 elements
        Guarantees: unit cell values are set up
        :param unit_cell_value: 5-element list
        :return:
        """
        # Check requirements
        assert isinstance(unit_cell_value, list), 'blabla'
        assert len(unit_cell_value) == 5

        # Set phase name
        self._lineEdit_name.setText(unit_cell_value[0])
        # Set a, b and c
        if unit_cell_value[2] is None:
            self._lineEdit_a.clear()
        else:
            self._lineEdit_a.setText(str(unit_cell_value[2]))
        if unit_cell_value[3] is None:
            self._lineEdit_a.clear()
        else:
            self._lineEdit_a.setText(str(unit_cell_value[3]))
        if unit_cell_value[4] is None:
            self._lineEdit_a.clear()
        else:
            self._lineEdit_a.setText(str(unit_cell_value[4]))
        # Set unit cell type
        new_index = -1
        for index in xrange(len(UnitCellList)):
            if unit_cell_value[1] == UnitCellList[index][0]:
                new_index = index
                break
        if new_index == -1:
            raise RuntimeError('Impossible to find unit cell type %s not in the list.' % unit_cell_value[1])
        else:
            self._comboBox_type.setCurrentIndex(new_index)

        return


class PeakWidthSetupDialog(QtGui.QDialog):
    """
    Class for set up dialog
    """
    def __init__(self, parent):
        """
        Init ...
        :return:
        """
        import gui.ui_PeakWidthSetup as widthSetupWindow

        # Initialize
        QtGui.QDialog.__init__(self, parent)

        self.ui = widthSetupWindow.Ui_Dialog()
        self.ui.setupUi(self)

        # Define event handlers
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_quit)
        self.connect(self.ui.pushButton_set, QtCore.SIGNAL('clicked()'),
                     self.do_set_width)

        # Class variables
        self._peakWidth = None

        return

    def do_quit(self):
        """
        Return without doing anything
        :return:
        """
        self.close()

    def do_set_width(self):
        """
        Set peak width
        :return:
        """
        peak_width = GuiUtility.parse_float(self.ui.lineEdit_peakWidth)
        if peak_width is None:
            GuiUtility.pop_dialog_error(self, 'Peak width is not set up!')
            return
        if peak_width <= 0.:
            GuiUtility.pop_dialog_error(self, 'Peak width %f cannot be 0 or negative!' % peak_width)
            return

        self._peakWidth = peak_width

        # Close
        self.close()

        return

    def get_peak_width(self):
        """ Get peak width
        Purpose: Get the stored peak width from the window object
        Requirements: it must be set up
        Guarantees: the peak width is given if it is set up
        :return:
        """
        assert self._peakWidth

        return self._peakWidth


class PeakPickerMode(object):
    """ Enumerate
    """
    Normal = 0
    QuickPick = 1
    MultiPeakPick = 2


class PeakPickerWindow(QtGui.QMainWindow):
    """ Class for general-purposed plot window
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QtGui.QMainWindow.__init__(self)

        # parent
        self._myParent = parent

        # set up UI
        self.ui = VdrivePeakPicker.Ui_MainWindow()
        self.ui.setupUi(self)

        # Define event handling methods
        # phase set up
        self.connect(self.ui.pushButton_setPhases, QtCore.SIGNAL('clicked()'),
                     self.do_set_phases)

        self.connect(self.ui.pushButton_clearPhase, QtCore.SIGNAL('clicked()'),
                     self.do_clear_phases)

        self.connect(self.ui.pushButton_cancelPhaseChange, QtCore.SIGNAL('clicked()'),
                     self.do_undo_phase_changes)

        # peak processing
        self.connect(self.ui.pushButton_addPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_add_picked_peaks)

        self.connect(self.ui.pushButton_findPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_find_peaks)

        self.connect(self.ui.pushButton_readPeakFile, QtCore.SIGNAL('clicked()'),
                     self.do_import_peaks_from_file)

        self.connect(self.ui.pushButton_claimOverlappedPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_claim_overlapped_peaks)

        self.connect(self.ui.pushButton_showPeaksInTable, QtCore.SIGNAL('clicked()'),
                     self.do_show_peaks)

        self.connect(self.ui.pushButton_hidePeaks, QtCore.SIGNAL('clicked()'),
                     self.do_hide_peaks)

        self.connect(self.ui.pushButton_setPeakWidth, QtCore.SIGNAL('clicked()'),
                     self.do_set_peaks_width)

        self.connect(self.ui.pushButton_sortPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_sort_peaks)

        self.connect(self.ui.checkBox_selectPeaks, QtCore.SIGNAL('stateChanged(int)'),
                     self.do_select_all_peaks)

        self.connect(self.ui.pushButton_editTableContents, QtCore.SIGNAL('clicked()'),
                     self.do_switch_table_editable)

        self.connect(self.ui.pushButton_deletePeaks, QtCore.SIGNAL('clicked()'),
                     self.do_delete_peaks)

        self.connect(self.ui.pushButton_peakPickerMode, QtCore.SIGNAL('clicked()'),
                     self.do_process_pick_mode)

        # load files
        self.connect(self.ui.pushButton_loadCalibFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_calibration_file)

        self.connect(self.ui.pushButton_readData, QtCore.SIGNAL('clicked()'),
                     self.do_load_data)

        self.connect(self.ui.comboBox_bankNumbers, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.evt_switch_bank)

        # save_to_buffer
        self.connect(self.ui.pushButton_save, QtCore.SIGNAL('clicked()'),
                     self.do_save_peaks)

        self.connect(self.ui.tableWidget_peakParameter, QtCore.SIGNAL('itemSelectionChanged()'),
                     self.evt_table_selection_changed)

        # Define canvas event handlers

        # Menu
        self.connect(self.ui.actionLoad, QtCore.SIGNAL('triggered()'),
                     self.menu_load_phase)
        self.connect(self.ui.actionExit, QtCore.SIGNAL('triggered()'),
                     self.menu_exit)

        # Set up widgets
        self._phaseWidgetsGroupDict = dict()
        self._init_widgets_setup()

        # Define state variables
        self._isDataLoaded = False     # state flag that data is loaded
        self._currentDataFile = None      # name of the data file that is currently loaded
        self._currentRunNumber = None  # current run number
        self._currentBankNumber = -1   # current bank number
        self._currentDataSet = dict()  # current data as {bank1: (vecX, vecY, vecE); bank2: (vecX, vecY, vecE) ...}
        self._myController = None      # Reference to controller class
        # disabled. leave to controller self._dataDirectory = None     # default directory to load data
        self._currGraphDataKey = None   # Data key of the current data plot on canvas
        self._dataKeyList = list()

        # Peak selection mode
        self._peakPickerMode = PeakPickerMode.Normal
        self._peakSelectionMode = ''
        self._indicatorIDList = None
        self._indicatorPositionList = None
        self._inEditMode = False

        # Mouse position
        self._currMousePosX = 0
        self._currMousePosY = 0

        self._currTableOrder = 0  # 0 for ascending, 1 for descending

        # Phases and initialize
        self._phaseDict = dict()
        for i in xrange(1, 4):
            self._phaseDict[i] = ['', '', 0., 0., 0.]

        return

    def evt_table_selection_changed(self):
        """
        Event handling as the selection of the row changed
        :return:
        """
        print '[Prototype] current row is ', self.ui.tableWidget_peakParameter.currentRow(), \
            self.ui.tableWidget_peakParameter.currentColumn()

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

    def _init_widgets_setup(self):
        """

        :return:
        """
        self.ui.treeView_iptsRun.set_main_window(self)

        self.ui.tableWidget_peakParameter.setup()

        # set up unit cell string list
        unit_cell_str_list = []
        for tup in UnitCellList:
            info_str = '%s (%s)' % (tup[0], tup[1])
            unit_cell_str_list.append(info_str)

        self.ui.comboBox_structure1.clear()
        self.ui.comboBox_structure1.addItems(unit_cell_str_list)
        self.ui.comboBox_structure2.clear()
        self.ui.comboBox_structure2.addItems(unit_cell_str_list)
        self.ui.comboBox_structure3.clear()
        self.ui.comboBox_structure3.addItems(unit_cell_str_list)

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

        return

    def initialize(self, controller):
        """
        Purpose:
            Set up controller instance
        Requires:
            It is not initialised before
        Guarantees:
            All function call to do with controller will work
        :param controller:
        :return:
        """
        # Check requirements
        assert self._myController is None, 'Workflow controller has been already set up.'
        assert isinstance(controller, vdapi.VDriveAPI)

        # Set up
        self._myController = controller

        return

    def do_add_picked_peaks(self):
        """ Add the picked up peaks in canvas
        :return:
        """
        # get bank
        bank = int(self.ui.comboBox_bankNumbers.currentText())

        # get number of groups
        num_groups = self.ui.graphicsView_main.get_number_peaks_groups()
        for i_grp in xrange(num_groups):
            # get peak group
            group = self.ui.graphicsView_main.get_peaks_group(i_grp)
            name = ''
            width = group.right_boundary - group.left_boundary

            peak_tup_list = group.get_peaks()

            # determine group ID
            if len(peak_tup_list) > 0:
                # single peak or multiple peaks, no group
                group_id = self.ui.tableWidget_peakParameter.get_next_group_id()
            else:
                # peak group without any peak
                return

            for peak_tup in peak_tup_list:
                peak_center = peak_tup[0]
                self.ui.tableWidget_peakParameter.add_peak(bank, name, peak_center, width, group_id)

            # clone to PeakPickWindow's
            print '[DB] It is about to store peaks group to somewhere!'

        # END-FOR

        # clear the picked up peaks from canvas
        self.ui.graphicsView_main.remove_all_in_pick_peaks()

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
            peak_width = peak_info_tup[1]
            self.ui.graphicsView_main.plot_peak_indicator(peak_pos)

        return

    def do_clear_phases(self):
        """
        Clear all phases
        :return:
        """
        # Clear phase list
        for i_phase in xrange(1, 4):
            self._phaseDict[i_phase] = ['', '', 0., 0., 0.]

        # Clear all the widgets
        for phase_widgets in self._phaseWidgetsGroupDict:
            phase_widgets.reset()

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
        """
        Purpose:
            Delete the selected peak from table and place holder and their indicators
        Requirements:
            At least one peak is selected in the table
        Guarantees:
            The selected peak is removed from both placeholder and table
        :return:
        """
        # Get the rows that contain the peaks to delete
        row_number_list = self.ui.tableWidget_peakParameter.get_selected_rows()
        assert len(row_number_list) > 0, 'No peak is selected to delete.'

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
        assert self._myController

        # Get minimum and maximum d-spacing to calculate by the range in the graph
        min_d = GuiUtility.parse_float()
        max_d = GuiUtility.parse_float()
        if min_d is None:
            min_d = self.ui.graphicsView_main.getXLimit()[0]
        if max_d is None:
            max_d = self.ui.graphicsView_main.getXLimit()[1]
        print '[DB] Get d-range: %f, %f' % (min_d, max_d)

        # List all peaks if any is selected
        num_phases_used = 0
        reflection_list = list()
        err_msg = ''
        for i_phase in self._phaseDict.keys():
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
            GuiUtility.pop_dialog_error(self, 'Unable to calculate reflections due to %s.' % err_msg)
            return

        # Try to find reflections in auto mode
        if num_phases_used == 0:
            # Use algorithm to find peak automatically
            GuiUtility.pop_dialog_information(self, 'No phase is selected. Find peak automatically!')
            try:
                peak_pos_list, peak_width_list = self._myController.find_peaks(run_number=self._currentRunNumber,
                                                                               bank_number=self._currentBankNumber,
                                                                               x_range=(min_d, max_d),
                                                                               profile='Gaussian',
                                                                               auto=True)
                hkl = [(0, 0, 0)] * len(peak_pos_list)
                reflection_list = (peak_pos_list, hkl)
            except RuntimeError as re:
                GuiUtility.pop_dialog_error(self, str(re))
                return
        else:
            # Use algorithm find peak with given peak positions to eliminate the non-existing peaks
            try:
                peak_pos_list, peak_width_list = self._myController.find_peaks(run_number=self._currentRunNumber,
                                                                               bank_number=self._currentBankNumber,
                                                                               x_range=(min_d, max_d),
                                                                               peak_positions=reflection_list[0],
                                                                               hkl_list=reflection_list[1],
                                                                               profile='Gaussian')
            except RuntimeError as e:
                GuiUtility.pop_dialog_error(self, str(e))
                return

        # Return if no reflection can be found
        if len(reflection_list) == 0:
            # No reflection can be found
            GuiUtility.pop_dialog_error(self, 'Unable to find any reflection between %f and %f.' % (min_d, max_d))
            return

        # Set the peaks to canvas
        peak_pos_list = retrieve_peak_positions(reflection_list)
        for peak_pos in peak_pos_list:
            self.ui.graphicsView_main.add_in_pick_peak(peak_pos)

        # Set the peaks' parameters to table
        for i_peak in xrange(len(peak_pos_list)):
            hkl = hkl[i_peak]  # reflection list???
            peak_pos = peak_pos_list[i_peak]
            peak_width = peak_width_list[i_peak]
            assert len(hkl) == 3, 'HKL is not a 3-item list but %s of type %s.' % (str(hkl), str(type(hkl)))
            temp_name = '%d%d%d' % (hkl[0], hkl[1], hkl[2])
            self.ui.tableWidget_peakParameter.add_peak(self._currentBankNumber, temp_name, peak_pos, peak_width, [])
        # END-FOR

        return

    def do_switch_table_editable(self):
        """ Purpose: switch on/off the edit mode of the peak table
        Guarantees: the table is switched to editable or non-editable mode
        :return:
        """
        # get selected row
        row_number_list = self.ui.tableWidget_peakParameter.get_selected_rows(True)
        if len(row_number_list) == 0:
            GuiUtility.pop_dialog_information(self, 'No row is selected to edit!')

        # set to editable
        # FIXME - can we make this more flexible?
        col_index = 1
        for row_number in row_number_list:
            item_i = self.ui.tableWidget_peakParameter.item(row_number, col_index)

            # FIXME/TODO/NOW - Implement this to NTableWidget
            item_i.setFlags(item_i.flags() | QtCore.Qt.ItemIsEditable)
            self.ui.tableWidget_peakParameter.editItem(item_i)
        # END-FOR

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
        print 'Sorting is enabled?', self.ui.tableWidget_peakParameter.isSortingEnabled()
        # Here is prototype
        p_int = self.ui.tableWidget_peakParameter.get_peak_pos_col_index()
        qt_sort_order = self._currTableOrder
        self.ui.tableWidget_peakParameter.sortByColumn(p_int, qt_sort_order)

        # Switch the sort order for table
        self._currTableOrder = 1 - self._currTableOrder

        return

    def do_hide_peaks(self):
        """
        Purpose: Highlight all peaks' indicators
        :return:
        """
        self.ui.remove_picked_peaks_indicators()

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
        peak_file = str(QtGui.QFileDialog.getOpenFileName(self, 'Peak File', work_dir, filters))
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
        print '[DB] There are %d peaks to add to current bank %s.' % (len(peak_list), str(self._currentBankNumber))
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
                self.ui.tableWidget_peakParameter.add_peak(bank, name, peak_pos, peak_width, overlap_peak_pos_list)
            else:
                self.ui.tableWidget_peakParameter.add_peak_to_buffer(bank, name, peak_pos, peak_width,
                                                                     overlap_peak_pos_list)
        # END-FOR (peak_info)

        # Check groups

        return

    def evt_switch_bank(self):
        """
        Save the current selected peaks to a temporary file and load a new bank
        :return:
        """
        # Get new bank
        new_bank = int(self.ui.comboBox_bankNumbers.currentText())
        if new_bank == self._currentBankNumber:
            # same bank as before. no need to do anything
            print '[DB] Newly selected bank %d is same as current bank %d.' % (new_bank, self._currentBankNumber)
            return
        if self._isDataLoaded is False:
            # it is about to load new data, plotting will be called explicitly. no need to re-plot her
            print '[DB] Data is in loading stage. Change to bank %d won\'t have any effect.' % new_bank
            return

        # Save the current peaks to memory and back up to disk
        self.ui.tableWidget_peakParameter.save_to_buffer(self._currentBankNumber)

        # Clear table and canvas
        self.ui.tableWidget_peakParameter.remove_all_rows()
        self.ui.graphicsView_main.clear_all_lines()

        # Re-plot
        # vec_x, vec_y = self._myController.get_diffraction_pattern(self._currDataKey, bank=new_bank)
        new_spec = new_bank-1
        vec_x = self._currentDataSet[new_spec][0]
        vec_y = self._currentDataSet[new_spec][1]
        self.ui.graphicsView_main.clear_all_lines()
        self.ui.graphicsView_main.plot_diffraction_pattern(vec_x, vec_y)

        self._currentBankNumber = new_bank
        self.ui.label_diffractionMessage.setText('Run %d Bank %d' % (
            self._currentRunNumber, self._currentBankNumber))

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
        assert self._myController is not None

        # Launch dialog box for calibration file name
        file_filter = 'Calibration (*.cal);;Text (*.txt);;All files (*.*)'
        cal_file_name = QtGui.QFileDialog.getOpenFileName(self, 'Calibration File', self._dataDirectory, file_filter)

        # Load
        self._myController.load_calibration_file(cal_file_name)

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
        assert self._myController is not None

        # Get the run numbers
        start_run_number = GuiUtility.parse_integer(self.ui.lineEdit_startRunNumber)
        end_run_number = GuiUtility.parse_integer(self.ui.lineEdit_endRunNumber)

        # Get the GSAS file names
        gsas_file_list = list()
        if start_run_number is not None and end_run_number is not None:
            # complete range
            assert start_run_number <= end_run_number, 'End run %d must be larger than ' \
                                                       'or equal to start run %d.' % (end_run_number,
                                                                                      start_run_number)
            # get directory containing GSAS files
            default_dir = self._myController.get_binned_data_dir(range(start_run_number, end_run_number))
            gsas_dir = str(QtGui.QFileDialog.getExistingDirectory(self, 'GSAS File Directory', default_dir))

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

        else:
            # get single GSAS file
            filters = 'GSAS files (*.gda);; All files (*.*)'
            default_dir = self._myController.get_binned_data_directory()
            # TODO/NOW - consider self._myController.get_ipts_config()

            gsas_file_name = str(QtGui.QFileDialog.getOpenFileName(self, 'Load GSAS File',
                                                                   default_dir, filters))
            gsas_file_list.append(gsas_file_name)
        # END-IF-ELSE

        # Load data from GSAS file
        for gsas_file_name in gsas_file_list:
            # Load data via parent
            try:
                data_key = self._myController.load_diffraction_file(gsas_file_name, 'gsas')
                self._dataKeyList.append(data_key)
                # add to tree
                self.ui.treeView_iptsRun.add_child_current_item(data_key)
            except RuntimeError as re:
                GuiUtility.pop_dialog_error(self, str(re))
                return
        # END-FOR

        # Plot data if there is only one GSAS file
        if len(gsas_file_list) > 0:
            self.load_plot_run(self._dataKeyList[0])

        return

    def load_plot_run(self, data_key):
        """ Load and plot a run
        Purpose: Load and plot a run by its data key
        Requirements: Input data key must be either an integer (run number) or a string (data file name)
        Guarantees: Reduced run (run number) or loaded file shall be loaded and plot
        :param data_key: key to the reduced data.  It can be string key or integer key (run number)
        :return:
        """
        # Get run number
        if isinstance(data_key, int):
            run_number = data_key
        else:
            assert isinstance(data_key, str), 'data key must be a string but not %s.' % str(type(data_key))
            if data_key.isdigit():
                run_number = int(data_key)
            else:
                run_number = None
            # END-IF-ELSE
        # END-IF-ELSE

        # Get reduced run information
        if run_number is None:
            # in case of a loaded data file (gsas, fullprof..)
            status, bank_id_list = self._myController.get_reduced_run_info(run_number=None, data_key=data_key)
        else:
            # in case of a previously reduced run
            status, ret_obj = self._myController.get_reduced_run_info(run_number)
            assert status, ret_obj
            bank_id_list = ret_obj

        # Set the mutex flag
        self._isDataLoaded = False

        # Update widgets, including run number, bank IDs (bank ID starts from 1)
        self.ui.comboBox_bankNumbers.clear()
        for i_bank in bank_id_list:
            self.ui.comboBox_bankNumbers.addItem(str(i_bank + 1))
        self.ui.comboBox_bankNumbers.setCurrentIndex(0)

        self.ui.comboBox_runNumber.clear()
        if run_number is None:
            self.ui.comboBox_runNumber.addItem(str(data_key))
            self.ui.label_diffractionMessage.setText('File %s Bank %d' % (data_key, 1))
        else:
            self.ui.comboBox_runNumber.addItem(str(run_number))
            self.ui.label_diffractionMessage.setText('Run %d Bank %d' % (run_number, 1))

        # Plot data: load bank 1 as default
        if run_number is None:
            status, ret_obj = self._myController.get_reduced_data(data_key, 'dSpacing')
        else:
            status, ret_obj = self._myController.get_reduced_data(run_number, 'dSpacing')
        if status is False:
            GuiUtility.pop_dialog_error(self, ret_obj)
            return
        # get spectrum 0, i.e, bank 1
        assert isinstance(ret_obj, dict)
        self._currentDataSet = ret_obj
        data_bank_1 = self._currentDataSet[0]
        # FIXME - It might return vec_x, vec_y AND vec_e
        vec_x = data_bank_1[0]
        vec_y = data_bank_1[1]
        self.ui.graphicsView_main.clear_all_lines()
        self.ui.graphicsView_main.plot_diffraction_pattern(vec_x, vec_y)

        # Set up class variables
        self._currentRunNumber = run_number
        self._currentBankNumber = 1
        self._currGraphDataKey = data_key

        # Release the mutex flag
        self._isDataLoaded = True

        return

    def load_chop_data(self):
        """
        Load chopped data... prototype
        :return:
        """
        # FIXME/NOW/1st: Need to find out how to integrate this to GUI

        # Get diffraction file
        load_chop_data = False
        if len(str(self.ui.lineEdit_chopDataToLoad.text())) > 0:
            load_chop_data = True

        chop_data_name = str(self.ui.lineEdit_chopDataToLoad.text())
        raise RuntimeError('Implement ASAP to load chopped data %s' % chop_data_name)

    def do_process_pick_mode(self):
        """ Enter for leave peak picker mode
        :return:
        """
        if self._peakPickerMode == PeakPickerMode.Normal:
            # enter normal mode to quick-pick mode (for single peak)
            self._peakPickerMode = PeakPickerMode.QuickPick
            self.ui.pushButton_peakPickerMode.setText('Select Multi-Peaks')
            self.ui.graphicsView_main.set_peak_selection_mode(single_mode=True, multi_mode=False)
            self.ui.label_peakSelectionMode.setText('Single-Peak Selection Mode')
            self.ui.pushButton_addPeaks.setEnabled(False)

        elif self._peakPickerMode == PeakPickerMode.QuickPick:
            # enter multiple peaks-pick mode from quick mode
            self._peakPickerMode = PeakPickerMode.MultiPeakPick
            self.ui.pushButton_peakPickerMode.setText('Quit Peak Selection')
            self.ui.graphicsView_main.set_peak_selection_mode(single_mode=False, multi_mode=True)
            self.ui.label_peakSelectionMode.setText('Multiple-Peaks Selection Mode')
            self.ui.pushButton_addPeaks.setEnabled(False)

        else:
            # non-selection mode
            self._peakPickerMode = PeakPickerMode.Normal
            self.ui.pushButton_peakPickerMode.setText('Select Single-Peaks')
            self.ui.graphicsView_main.set_peak_selection_mode(False, False)
            self.ui.label_peakSelectionMode.setText('')
            self.ui.pushButton_addPeaks.setEnabled(True)

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
        assert self._myController is not None

        # Get the output file
        file_filter = 'Text (*.txt);;All files (*.*)'
        out_file_name = str(QtGui.QFileDialog.getSaveFileName(self, 'Save peaks to GSAS peak file',
                                                              self._dataDirectory, file_filter))

        # Get the peaks from buffer
        peak_bank_dict = self.ui.tableWidget_peakParameter.get_buffered_peaks([self._currentBankNumber])

        # Get the peaks from table
        num_peaks = self.ui.tableWidget_peakParameter.rowCount()
        peak_list = list()
        for i_peak in xrange(num_peaks):
            # get a list from the peak
            peak_i = self.ui.tableWidget_peakParameter.get_peak(i_peak)
            peak_list.append(peak_i)
            print '[DB-BAT-22527]', type(peak_i), peak_i
        peak_bank_dict[self._currentBankNumber] = peak_list

        # Check
        total_peaks = 0
        for peak_list in peak_bank_dict.values():
            total_peaks += len(peak_list)
        if total_peaks == 0:
            GuiUtility.pop_dialog_error(self, 'No peak is selected.  Unable to execute saving peaks.')
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

        peak_width = peak_width_dialog.get_peak_width()
        print 'Get log value = ', peak_width

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
        self.load_plot_run(run_id_list[0])

        return

    def set_controller(self, controller):
        """ Set up workflow controller to this window object
        Purpose: Set the workflow controller to this window object
        Requirement: controller must be VDriveAPI or Mock
        Guarantees: controller is set up. Reduced runs are get from controller and set to
        :param controller:
        :return:
        """
        assert controller.__class__.__name__.count('VDriveAPI') == 1, \
            'Controller is not a valid VDriveAPI instance , but not %s.' % controller.__class__.__name__

        self._myController = controller
        self.set_data_dir(self._myController.get_working_dir())

        # Get reduced data
        reduced_run_number_list = self._myController.get_reduced_runs()
        ipts = 1

        # Set
        self.ui.treeView_iptsRun.add_ipts_runs(ipts_number=ipts, run_number_list=reduced_run_number_list)

        return

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
        # TODO/NOW - Doc and assertion
        # Check requirements

        # Delete all 3 indicators line
        for indicator_id in self._indicatorIDList:
            self.ui.graphicsView_main.remove_indicator(indicator_id)

        # Reset all the variables
        self._indicatorIDList = None
        self._indicatorPositionList = None
        self._peakSelectionMode = ''
        self._inEditMode = False

        return

    def menu_delete_peak(self):
        """
        TODO/NOW: Implement and Doc
        :return:
        """
        print 'bla bla ...', 'Delete peak around x = %f' % self._currMousePosX

    def menu_exit(self):
        """
        Quit the window
        :return:
        """
        self.close()

        return

    def menu_load_phase(self):
        """
        Load a file with phase information
        :return:
        """
        # Get the file name
        file_filter = 'Text (*.txt);;All files (*.*)'
        phase_file_name = QtGui.QFileDialog.getOpenFileName(self, 'Import phase information', self._dataDirectory,
                                                            file_filter)

        # return if action is cancelled
        if phase_file_name is None:
            return
        phase_file_name = str(phase_file_name)
        if len(phase_file_name.strip()) == 0:
            return

        # TODO/NOW/1st: import phase file and set widgets
        print 'Importing phase information file!'

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
            raise RuntimeError('Peak selection mode %s is not switchable.' % self._peakSelectionMode)

        return

    def on_mouse_release_event(self, event):
        """ If the left button is released and previously in IN_PICKER_MOVING mode,
        then the mode is over
        """
        button = event.button

        if button == 1:
            # left button click
            if self._inEditMode:
                # quit edit mode
                self._inEditMode = False

        elif button == 3:
            # right button click: pop out menu
            self.ui.menu = QtGui.QMenu(self)

            action_add = QtGui.QAction('Add Peak', self)
            action_add.triggered.connect(self.menu_add_peak)
            self.ui.menu.addAction(action_add)

            if self._peakSelectionMode == 'MoveCentre':
                # in peak centre moving mode
                action_switch = QtGui.QAction('Change Peak Width', self)
                action_switch.triggered.connect(self.menu_switch_mode)
                self.ui.menu.addAction(action_switch)

                action_cancel = QtGui.QAction('Cancel', self)
                action_cancel.triggered.connect(self.menu_cancel_selection)
                self.ui.menu.addAction(action_cancel)

            elif self._peakSelectionMode == 'ChangeWidth':
                # in peak width determining  mode
                action_switch = QtGui.QAction('Move Peak Centre', self)
                action_switch.triggered.connect(self.menu_switch_mode)
                self.ui.menu.addAction(action_switch)

                action_cancel = QtGui.QAction('Cancel', self)
                action_cancel.triggered.connect(self.menu_cancel_selection)
                self.ui.menu.addAction(action_cancel)

            else:
                # others
                action_select = QtGui.QAction('Select Peak', self)
                action_select.triggered.connect(self.menu_select_peak)
                self.ui.menu.addAction(action_select)

                action_delete = QtGui.QAction('Delete Peak', self)
                action_delete.triggered.connect(self.menu_delete_peak)
                self.ui.menu.addAction(action_delete)

            # pop up menu at cursor
            self.ui.menu.popup(QtGui.QCursor.pos())

        return

    def on_mouse_motion(self, event):
        """ Event handling in case mouse is moving
        """
        new_x = event.xdata
        new_y = event.ydata

        # Outside of canvas, no response
        if new_x is None or new_y is None:
            return

        # Determine resolution
        min_x, max_x = self.ui.graphicsView_main.getXLimit()
        resolution = (max_x - min_x) * 0.001

        # Ignore moving with small step
        dx = new_x - self._currMousePosX
        if abs(dx) < resolution:
            return

        not_update = False
        if self._inEditMode and self._peakSelectionMode == 'MoveCentre':
            self.move_peak_position(new_x)
        elif self._inEditMode and self._peakSelectionMode == 'ChangeWidth':
            self.move_peak_boundary(new_x)
            not_update = True
        elif self._inEditMode:
            err_msg = 'It is not right such that InEditMode is %s and SelectionMode is %s.' % (
                str(self._inEditMode), self._peakSelectionMode)
            raise RuntimeError(err_msg)

        # Update
        if not_update is False:
            self._currMousePosX = new_x
            self._currMousePosY = new_y

        return

    def move_peak_boundary(self, pos_x):
        """ Move the boundary of the peak
        :param pos_x:
        :return:
        """
        # TODO/NOW - Doc and assertion

        # Find out how to expand
        if pos_x < self._currMousePosX:
            left_bound = pos_x
            right_bound = 2*self._currMousePosX - pos_x
        else:
            right_bound = pos_x
            left_bound = 2*self._currMousePosX - pos_x

        # Left
        left_id = self._indicatorIDList[1]
        dx = left_bound - self._indicatorPositionList[1]
        self.ui.graphicsView_main.move_indicator(left_id, dx, 0)

        right_id = self._indicatorIDList[2]
        dx = right_bound -  self._indicatorPositionList[2]
        self.ui.graphicsView_main.move_indicator(right_id, dx, 0)

        self._indicatorPositionList[1] = left_bound
        self._indicatorPositionList[2] = right_bound

        return

    def move_peak_position(self, pos_x):
        """
        Purpose: move peak's position including its indicators
        :param pos_x:
        :return:
        """
        # TODO/NOW - doc and assertion
        # Check

        # Find dx
        dx = pos_x - self._currMousePosX

        # Update indicator positions
        for i in xrange(3):
            self._indicatorPositionList[i] += dx

        # Move indicators
        for i in xrange(3):
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
        # TODO/NOW: Doc, Assertion, ...

        self._dataDirectory = data_dir

        return


def retrieve_peak_positions(peak_tup_list):
    """
    Purpose:
        Retrieve peak positions from peaks in given list
    Requirements:
        Input is a list of 2-tuples as HKL and d-spacing
    Guarantees:
        Retrieve the peaks' positions out
    :param peak_tup_list:
    :return: a list of
    """
    assert isinstance(peak_tup_list, list)

    peak_pos_list = list()
    for peak in peak_tup_list:
        peak_pos = peak[0]
        print peak_pos
        peak_pos_list.append(peak_pos)
    # END-FOR(peak)

    return peak_pos_list


def main(argv):
    """ Main method for testing purpose
    """
    import mocks.mockvdriveapi as mocks

    parent = None
    controller = mocks.MockVDriveAPI()

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = PeakPickerWindow(parent)
    myapp.set_data_dir('/home/wzz/Projects/PyVDrive/tests/reduction/')
    myapp.set_controller(controller)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)


if __name__ == "__main__":
    main(sys.argv)
