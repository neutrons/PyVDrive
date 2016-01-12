########################################################################
#
# Window for set up log slicing splitters
#
########################################################################
import sys
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import GuiUtility
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

    def set_phase_values(self, phase_value_list):
        """
        Purpose: set the phase values to the input list
        :param phase_value_list:
        :return:
        """

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
            raise RuntimeError('Lattice parameters a, b or c does not have correct value.')

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


class PeakWidthSetupDialog(QtGui.QDialog):
    """
    Class for set up dialog
    """
    # TODO/NOW/1st: Docs, assertions and implement!
    def __init__(self, parent):
        """
        Init ...
        :return:
        """
        import gui.ui_PeakWidthSetup as width_setup

        # Initialize
        QtGui.QDialog.__init__(self, parent)

        self.ui = width_setup.Ui_Dialog()
        self.ui.setupUi(self)

        # Define event handlers
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_quit)

        return

    def do_quit(self):
        """
        ... ...
        :return:
        """
        self.close()

    def get_peak_width(self):
        """
        ... ...
        :return:
        """
        return 1234.


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
        self.connect(self.ui.pushButton_findPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_find_peaks)

        self.connect(self.ui.pushButton_readPeakFile, QtCore.SIGNAL('clicked()'),
                     self.do_import_peaks_from_file)

        self.connect(self.ui.pushButton_claimOverlappedPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_claim_overlapped_peaks)

        self.connect(self.ui.pushButton_showPeaks, QtCore.SIGNAL('clicked()'),
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

        # load files
        self.connect(self.ui.pushButton_loadCalibFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_calibration_file)

        self.connect(self.ui.pushButton_readData, QtCore.SIGNAL('clicked()'),
                     self.do_load_data)

        self.connect(self.ui.comboBox_bankNumbers, QtCore.SIGNAL('currentIndexChanged(int)'),
                     self.do_load_bank)

        # save and quit
        self.connect(self.ui.pushButton_return, QtCore.SIGNAL('clicked()'),
                     self.do_quit)

        self.connect(self.ui.pushButton_save, QtCore.SIGNAL('clicked()'),
                     self.do_save_peaks)

        # Define canvas event hanlders
        # Event handling for pickers
        self.ui.graphicsView_main._myCanvas.mpl_connect('button_press_event',
                                                        self.on_mouse_press_event)
        self.ui.graphicsView_main._myCanvas.mpl_connect('button_release_event',
                                                        self.on_mouse_release_event)
        self.ui.graphicsView_main._myCanvas.mpl_connect('motion_notify_event',
                                                        self.on_mouse_motion)

        # Set up widgets
        self._phaseWidgetsGroupDict = dict()
        self._init_widgets_setup()

        # Define state variables
        self._isDataLoaded = False    # state flag that data is loaded
        self._currDataFile = None     # name of the data file that is currently loaded
        self._currentBankNumber = -1  # current bank number
        self._myController = None     # Reference to controller class
        self._dataDirectory = None    # default directory to load data
        self._currDataKey = None      # Data key to look up reduced data from controller

        # Peak selection mode
        self._peakSelectionMode = ''
        self._indicatorIDList = None
        self._indicatorPositionList = None
        self._inEditMode = False

        # Mouse position
        self._currMousePosX = 0
        self._currMousePosY = 0

        # Phases and initialize
        self._phaseDict = dict()
        for i in xrange(1, 4):
            self._phaseDict[i] = ['', '', 0., 0., 0.]

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
        assert self._isDataLoaded is True, 'No data is loaded.'

        # Get the rows that are selected. Find the next group ID.  Set these rows with same group ID
        row_index_list = self.ui.tableWidget_peakParameter.get_selected_rows()
        assert len(row_index_list) >= 2, 'At least 2 rows should be selected for grouping.'

        # Set the group ID to table
        group_id = self.ui.tableWidget_peakParameter.get_next_group_id()
        for row_index in row_index_list:
            self.ui.tableWidget_peakParameter.set_group_id(row_index, group_id)

        # Show the peak indicators
        peak_pos_list = self.ui.tableWidget_peakParameter.get_selected_peaks_position()
        for peak_pos in peak_pos_list:
            self.ui.graphicsView_main.add_peak_indicator(peak_pos)

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
        peak_pos_list = self.ui.tableWidget_peakParameter.get_selected_peaks_position()
        if len(peak_pos_list) == 0:
            GuiUtility.pop_dialog_error(self, 'No peak is selected.')
            return

        # Sort peak list
        peak_pos_list.sort()

        # Re-set the graph range
        x_min, x_max = self.ui.graphicsView_main.getXLimit()
        if peak_pos_list[0] < x_min or peak_pos_list[-1] > x_max:
            # resize! TODO/NOW/1st: IMPLEMENT
            raise NotImplementedError('ASAP')

        # Plot
        for peak_pos in peak_pos_list:
            self.ui.graphicsView_main.add_peak_indicator(peak_pos)

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
        # TODO/NOW/1st: make this right!

        # Get rows that are selected
        blabla()

        # Delete the selected rows
        self.ui.tableWidget_peakParameter.remove_rows(run_number_list)

        return

    def do_find_peaks(self):
        """
        Purpose:
            Find all peaks in the spectrum
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
        min_d, max_d = self.ui.graphicsView_main.getXLimit()
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

            # Calcuate peaks' positions
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
                reflection_list = self._myController.find_peaks(pattern=self._currPattern, profile='Gaussian')
            except RuntimeError as re:
                GuiUtility.pop_dialog_error(self, str(re))
                return

        # Return if no reflection can be found
        if len(reflection_list) == 0:
            # No reflection can be found
            GuiUtility.pop_dialog_error(self, 'Unable to find any reflection between %f and %f.' % (min_d, max_d))
            return

        # Set the peaks to canvas
        peak_pos_list = retrieve_peak_positions(reflection_list)
        for peak_pos in peak_pos_list:
            self.ui.graphicsView_main.add_peak_indicator(peak_pos)

        # Set the peaks' parameters to table
        for peak_tup in reflection_list:
            hkl = str(peak_tup[1])
            peak_pos = peak_tup[0]
            self.ui.tableWidget_peakParameter.add_peak(self._currentBankNumber, hkl, peak_pos, 0.03)

        return

    def do_switch_table_editable(self):
        """ Purpose: switch on/off the edit mode of the peak table
        Guarantees: the table is switched to editable or non-editable mode
        :return:
        """
        is_editable = self.ui.tableWidget_existingPeakFile.is_editable()
        self.ui.tableWidget_peakParameter.set_editable(is_editable)

        return

    def do_sort_peaks(self):
        """
        Purpose: sort peaks by peak position in either ascending or descending order.
        Requirements:
        Guarantees:
        :return:
        """
        import PyQt4.Qt as Qt
        # TODO/NOW/1st: IMPLEMENT IT!

        print 'Sorting is enabled?', self.ui.tableWidget_peakParameter.isSortingEnabled()
        # Here is prototype
        p_int = 2
        Qt_SortOrder=0
        self.ui.tableWidget_peakParameter.sortByColumn(p_int, Qt_SortOrder)

        return

    def do_hide_peaks(self):
        """
        Purpose: Highlight all peaks' indicators
        :return:
        """
        self.ui.graphicsView_main.remove_all_peak_indicators()

        return

    def do_import_peaks_from_file(self):
        """ Purpose: import peaks' IDs from peak file
        Requirements: my controller is set up
        :return:
        """
        # Check requirement
        assert self._myController is not None

        # Pop out dialog for file and import the file
        peak_file = str(QtGui.QFileDialog.getOpenFileName(self, 'Peak File', self._dataDirectory))
        try:
            peak_list = self._myController.import_gsas_peak_file(peak_file)
        except RuntimeError as err:
            GuiUtility.pop_dialog_error(self, str(err))

        # Set the peaks to table
        if self.ui.checkBox_clearPeakTable.isChecked():
            self.ui.tableWidget_peakParameter.remove_all_rows()
        self.ui.tableWidget_peakParameter.add_peaks(peak_list)

        return

    def do_load_bank(self):
        """
        Save the current selected peaks to a temporary file and load a new bank
        :return:
        """
        # Get new bank
        new_bank = int(self.ui.comboBox_bankNumbers.currentText())
        if new_bank == self._currentBankNumber:
            # same bank as before. no need to do anything
            return
        if self._isDataLoaded is False:
            # it is about to load new data, plotting will be called explicitly. no need to re-plot her
            return

        # Save the current peaks to memory and back up to disk
        self.ui.tableWidget_peakParameter.save(self._currentBankNumber)

        # Clear table and canvas
        self.ui.tableWidget_peakParameter.remove_all_rows()
        self.ui.graphicsView_main.clear_all_lines()

        # Re-plot
        vec_x, vec_y = self._myController.get_diffraction_pattern(self._currDataKey, bank=new_bank)
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
        cal_file_name = QtGui.QFileDialog.getOpenFileName(self, 'Calibration File')

        # Load
        self._myController.load_calibration_file(cal_file_name)

        return

    def do_load_data(self):
        """
        Purpose:
            Load GSAS data
        Requirements:
            Controller has been set to this object
        Requires:
        Guarantees:
        :return:
        """
        # FIXME/NOW/1st - Should move the MockController to VDriveAPI

        # Check requirements
        assert self._myController is not None

        # Get diffraction file
        load_chop_data = False
        load_run_data = False
        if len(str(self.ui.lineEdit_chopDataToLoad.text())) > 0:
            load_chop_data = True
        if len(str(self.ui.lineEdit_runToLoad.text())) > 0:
            load_run_data = True

        # Load data
        if load_chop_data and load_run_data:
            # Specify too many.  Unable to handle
            GuiUtility.pop_dialog_error('Both run and chopped are specified. Unable to handle.')
            return
        elif load_chop_data:
            # Load chopped data
            chop_data_name = str(self.ui.lineEdit_chopDataToLoad.text())
            raise RuntimeError('Implement ASAP to load chopped data %s' % chop_data_name)
        elif load_run_data:
            # Load data via run
            run_data_name = str(self.ui.lineEdit_runToLoad.text())
            raise RuntimeError('Implement ASAP to load reduced run %s.' % run_data_name)
        else:
            # Load GSAS file
            diff_file_name = str(QtGui.QFileDialog.getOpenFileName(self, 'Open GSAS File', self._dataDirectory))

            # Load data via parent
            try:
                data_key = self._myController.load_diffraction_file(diff_file_name, 'gsas')
            except RuntimeError as re:
                GuiUtility.pop_dialog_error(self, str(re))
                return
        # END-IF-ELSE

        # update widgets
        self._isDataLoaded = False

        run_number, num_banks = self._myController.get_diffraction_pattern_info(data_key)
        self.ui.comboBox_bankNumbers.clear()
        for i_bank in xrange(num_banks):
            self.ui.comboBox_bankNumbers.addItem(str(i_bank+1))
        self.ui.comboBox_bankNumbers.setCurrentIndex(0)
        self.ui.comboBox_runNumber.addItem(str(run_number))

        self.ui.label_diffractionMessage.setText('Run %d Bank %d' % (run_number, 1))

        # Plot data: load bank 1 as default
        vec_x, vec_y = self._myController.get_diffraction_pattern(data_key, bank=1)
        self.ui.graphicsView_main.clear_all_lines()
        self.ui.graphicsView_main.plot_diffraction_pattern(vec_x, vec_y)

        self._currentRunNumber = run_number
        self._currentBankNumber = 1
        self._currDataKey = data_key
        self._isDataLoaded = True

        return

    def do_quit(self):
        """
        Purpose:
            Close the dialog window without saving
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
        assert (self._myController is not None)

        selected_peaks = self.ui.tableWidget.get_peak(flag=True)
        if len(selected_peaks) == 0:
            GuiUtility.pop_dialog_error(self, 'No peak is selected.  Unable to execute saving peaks.')
            return

        # Set the selected peaks to controller
        self._myController.append_peaks(selected_peaks)

        return

    def do_select_all_peaks(self):
        """
        Purpose: select or de-select all peaks
        Requirements: None
        Guarantees: select or de-select all peaks according to check box selectPeaks
        :return:
        """
        print '[TODO/NOW!] Current state is ', self.ui.checkBox_selectPeaks.isChecked()

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
            self._phaseWidgetsGroupDict[i_phase].set_phase_values(self._phaseDict[i_phase])

        return

    def do_undo_phase_changes(self):
        """ Purpose: undo all the changes from last 'set phase'
        :return:
        """
        # TODO/FIXME/1st add this method
        blabla()

    def set_controller(self, controller):
        """
        """
        # TODO/NOW/Doc
        self._myController = controller

    def menu_add_peak(self):
        """ Add a peak to table
        Purpose: Add a peak under cursor in a simple way
        Requirements:
        Guarantees:
        :return:
        """
        # TODO/NOW  Assertion doc

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
        self.ui.tableWidget_peakParameter.add_peak(bank_number, peak_name, peak_pos, peak_width)

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

    def on_mouse_press_event(self, event):
        """ If in the picking up mode, as mouse's left button is pressed down,
        the indicator/picker
        is in the moving mode

        event.button has 3 values:
         1: left
         2: middle
         3: right
        """
        # Get event data
        x = event.xdata
        y = event.ydata
        button = event.button
        print "[DB] Button %d is (pressed) down at (%s, %s)." % (button, str(x), str(y))

        # Select situation
        if x is None or y is None:
            # mouse is out of canvas, return
            return

        # FIXME/NOW Make these 2 to init
        self._currMousePosX = x
        self._currMousePosY = y

        if button == 1:
            # left button
            if self._peakSelectionMode == 'MoveCentre' or self._peakSelectionMode == 'ChangeWidth':
                self._inEditMode = True

        elif button == 3:
            # right button
            pass

        # FIXME/TODO/NOW - Define the response event from mouse

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
    parent = None
    controller = MockController()

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = PeakPickerWindow(parent)
    myapp.set_data_dir('/home/wzz/Projects/PyVDrive/tests/reduction/')
    myapp.set_controller(controller)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return


class MockController(object):
    """

    """
    def __init__(self):
        """

        :return:
        """
        self._currWS = None

        return

    def calculate_peaks_position(self, phase, min_d, max_d):
        """
        Purpose: calculate the bragg peaks' position from

        Requirements:

        Guarantees:
          1. return a list of reflections
          2. each reflection is a tuple. first is a float for peak position. second is a list of list for HKLs

        :param phase: [name, type, a, b, c]
        :param min_d:
        :param max_d:
        :return: list of 2-tuples.  Each tuple is a float as d-spacing and a list of HKL's
        """
        import PyVDrive.vdrive.mantid_helper as mantid_helper

        # Check requirements
        assert isinstance(phase, list), 'Input Phase must be a list but not %s.' % (str(type(phase)))
        assert len(phase) == 5, 'Input phase  of type list must have 5 elements'

        # Get information
        phase_type = phase[1]
        lattice_a = phase[2]
        lattice_b = phase[3]
        lattice_c = phase[4]

        # Convert phase type to
        phase_type = phase_type.split()[0]
        if phase_type == 'BCC':
            phase_type = mantid_helper.UnitCell.BCC
        elif phase_type == 'FCC':
            phase_type = mantid_helper.UnitCell.FCC
        elif phase_type == 'HCP':
            phase_type = mantid_helper.UnitCell.HCP
        elif phase_type == 'Body-Center':
            phase_type = mantid_helper.UnitCell.BC
        elif phase_type == 'Face-Center':
            phase_type = mantid_helper.UnitCell.FC
        else:
            raise RuntimeError('Unit cell type %s is not supported.' % phase_type)

        # Get reflections
        # silicon = mantid_helper.UnitCell(mantid_helper.UnitCell.FC, 5.43)  #, 5.43, 5.43)
        unit_cell = mantid_helper.UnitCell(phase_type, lattice_a, lattice_b, lattice_c)
        reflections = mantid_helper.calculate_reflections(unit_cell, 1.0, 5.0)

        # Sort by d-space... NOT FINISHED YET
        num_ref = len(reflections)
        ref_dict = dict()
        for i_ref in xrange(num_ref):
            ref_tup = reflections[i_ref]
            assert isinstance(ref_tup, tuple)
            assert len(ref_tup) == 2
            pos_d = ref_tup[1]
            assert isinstance(pos_d, float)
            assert pos_d > 0
            # HKL should be an instance of mantid.kernel._kernel.V3D
            hkl_v3d = ref_tup[0]
            hkl = [hkl_v3d.X(), hkl_v3d.Y(), hkl_v3d.Z()]

            # pos_d has not such key, then add it
            if pos_d not in ref_dict:
                ref_dict[pos_d] = list()
            ref_dict[pos_d].append(hkl)
        # END-FOR

        # Merge all the peaks with peak position within tolerance
        TOL = 0.0001
        # sort the list again with peak positions...
        peak_pos_list = ref_dict.keys()
        peak_pos_list.sort()
        print '[DB] List of peak positions: ', peak_pos_list
        curr_list = None
        curr_pos = -1
        for peak_pos in peak_pos_list:
            if peak_pos - curr_pos < TOL:
                # combine the element (list)
                assert isinstance(curr_list, list)
                curr_list.extend(ref_dict[peak_pos])
                del ref_dict[peak_pos]
            else:
                curr_list = ref_dict[peak_pos]
                curr_pos = peak_pos
        # END-FOR

        # Convert from dictionary to list as 2-tuples

        print '[DB-BAT] List of final reflections:', type(ref_dict)
        d_list = ref_dict.keys()
        d_list.sort(reverse=True)
        reflection_list = list()
        for peak_pos in d_list:
            reflection_list.append((peak_pos, ref_dict[peak_pos]))
            print '[DB-BAT] d = %f\treflections: %s' % (peak_pos, str(ref_dict[peak_pos]))

        return reflection_list

    def does_exist_data(self, data_key):
        """
        TODO/NOW/1s: should be implemented in the workflow controller!
        :return:
        """
        return True

    def get_diffraction_pattern_info(self, data_key):
        """ Get information from a diffraction pattern, i.e., a loaded workspace
        Purpose: get run number from "data key" and number of banks
        Requirements: data_key is an existing key as a string and it is the path to the data file
                      where the run number can be extracted
        Requirements: find out the run number and bank number
        :return:
        """
        import os
        print 'Data key is %s of type %s' % (str(data_key), str(type(data_key)))

        # Check requirements
        assert isinstance(data_key, str), 'Data key must be a string.'

        # Key (temporary) is the file name
        run_number = int(os.path.basename(data_key).split('.')[0])
        #
        num_banks = self._currWS.getNumberHistograms()

        return run_number, num_banks

    def get_diffraction_pattern(self, data_key, bank, include_err=False):
        """
        Purpose: get diffraction pattern of a bank
        Requirements:
            1. date key exists
            2. bank is a valid integer
        Guarantees: returned a 2 or 3 vector
        :param data_key:
        :param bank:
        :param include_err:
        :return:
        """
        # Check requirements
        assert self.does_exist_data(data_key)
        assert isinstance(bank, int)
        assert bank > 0
        assert isinstance(include_err, bool)

        # Get data
        # FIXME/TODO/NOW - 1st: Make it True and implement for real workflow controller
        if False:
            ws_index = self.convert_bank_to_ws(bank)

            if self._currDataKey == data_key:
                vec_x = self._currWS.readX(ws_index)
                vec_y = self._currWS.readY(ws_index)
                if include_err:
                    vec_e = []
                    return vec_x, vec_y, vec_e
            else:
                raise RuntimeError('Current workspace is not the right data set!')
        else:
            ws_index = bank-1
            vec_x = self._currWS.readX(ws_index)
            vec_y = self._currWS.readY(ws_index)

        return vec_x, vec_y

    def import_gsas_peak_file(self, peak_file_name):
        """

        :param peak_file_name:
        :return:
        """
        # TODO/NOW/1st: Check requirements and finish the algorithm
        import PyVDrive.vdrive.io_peak_file as pio

        # Check requirements
        assert isinstance(peak_file_name, str)

        peak_manager = pio.GSASPeakFileManager()
        peak_manager.import_peaks(peak_file_name)

        return peaks

    def load_diffraction_file(self, file_name, file_type):
        """

        :param file_type:
        :return:
        """
        import sys
        sys.path.append('/Users/wzz/MantidBuild/debug/bin')
        import mantid.simpleapi

        if file_type.lower() == 'gsas':
            # load
            temp_ws = mantid.simpleapi.LoadGSS(Filename=file_name, OutputWorkspace='Temp')
            # set instrument geometry
            if temp_ws.getNumberHistograms() == 2:
                mantid.simpleapi.EditInstrumentGeometry(Workspace='Temp',
                                                        PrimaryFlightPath=43.753999999999998,
                                                        SpectrumIDs='1,2',
                                                        L2='2.00944,2.00944',
                                                        Polar='90,270')
            else:
                raise RuntimeError('It is not implemented for cases more than 2 spectra.')
            # convert unit
            mantid.simpleapi.ConvertUnits(InputWorkspace='Temp', OutputWorkspace='Temp',
                                          Target='dSpacing')

            self._currWS = mantid.simpleapi.ConvertToPointData(InputWorkspace='Temp', OutputWorkspace='Temp')
        else:
            raise NotImplementedError('File type %s is not supported.' % file_type)

        return file_name

if __name__ == "__main__":
    main(sys.argv)
