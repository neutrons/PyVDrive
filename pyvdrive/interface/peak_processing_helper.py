import os
try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QDialog, QLineEdit, QComboBox, QCheckBox
    from PyQt5.uic import loadUi as load_ui
except ImportError:
    from PyQt4.QtGui import QMainWindow, QVBoxLayout, QDialog, QLineEdit, QComboBox, QCheckBox  # noqa: F401
    from PyQt4.uic import loadUi as load_ui
from pyvdrive.interface.gui import GuiUtility

# List of supported unit cell
UnitCellList = [('BCC', 'I m -3 m'),
                ('FCC', 'F d -3 m'),
                ('HCP', 'P 63/m m c'),
                ('Body-Center', 'I m m m'),
                ('Face-Center', 'F m m m'),
                ('Primitive', 'P m m m')]


class GroupPeakDialog(QMainWindow):
    """
    Main window class to group peak with user interaction
    """

    def __init__(self, parent):
        """
        Initialization
        :param parent:
        """
        # check
        assert parent is not None, 'Parent (window) cannot be None!'
        # call base class init
        super(GroupPeakDialog, self).__init__(parent)
        # set up parent window
        self._parentWindow = parent

        # set up UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/GroupPeakDialog.ui")
        self.ui = load_ui(ui_path, baseinstance=self)

        # init set up of widgets
        self.ui.radioButton_highIntensity.setChecked(True)
        self.ui.lineEdit_numberFWHM.setText('6')

        # line event handlers
        self.ui.pushButton_groupPeaks.clicked.connect(self.do_group_peaks)
        self.ui.pushButton_addPeakReturn.clicked.connect(self.do_add_peak_return)
        self.ui.pushButton_cancel.clicked.connect(self.do_cancel_return)

        # hide widgets that is unused but may be needed in future
        self.ui.pushButton_clearGroup.hide()

        return

    def do_add_peak_return(self):
        """
        add grouped peaks and then close window
        :return:
        """
        self._parentWindow.add_grouped_peaks()

        self.close()

        return

    def do_cancel_return(self):
        """
        do not record the result of peak picking and close the window
        :return:
        """
        self._parentWindow.clear_group_highlight()

        self.close()

        return

    def do_group_peaks(self):
        """
        group selected peaks
        :return:
        """
        # get the resolution
        if self.ui.radioButton_highResolution.isChecked():
            resolution = 0.0025
        elif self.ui.radioButton_highIntensity.isChecked():
            resolution = 0.0045
        else:
            resolution = float(str(self.ui.lineEdit_userResolution))

        # get number of FWHM
        num_fwhm = int(str(self.ui.lineEdit_numberFWHM.text()))

        # group peak
        self._parentWindow.group_peaks(resolution, num_fwhm)

        return


class PeakWidthSetupDialog(QDialog):
    """
    Class for set up dialog
    """

    def __init__(self, parent):
        """
        Init ...
        :return:
        """

        # Initialize
        QDialog.__init__(self, parent)

        ui_path = os.path.join(os.path.dirname(__file__), 'gui/PeakWidthSetup.ui')
        self.ui = load_ui(ui_path, baseinstance=self)

        # Define event handlers
        self.ui.pushButton_cancel.clicked.connect(self.do_quit)
        self.ui.pushButton_set.clicked.connect(self.do_set_width)

        # self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
        #              self.do_quit)
        # self.connect(self.ui.pushButton_set, QtCore.SIGNAL('clicked()'),
        #              self.do_set_width)

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
        assert isinstance(parent, QMainWindow)
        assert isinstance(edit_a, QLineEdit)
        assert isinstance(edit_b, QLineEdit)
        assert isinstance(edit_c, QLineEdit)
        assert isinstance(edit_name, QLineEdit)
        assert isinstance(combo_box_type, QComboBox)
        assert isinstance(check_box_select, QCheckBox)

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

        combo_box_type.currentIndexChanged.connect(self.event_space_group_changed)
        # parent.connect(combo_box_type, QtCore.SIGNAL('currentIndexChanged(int)'),
        #                self.event_space_group_changed)

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
        assert isinstance(phase_value_list, list), 'Phase value list %s must be a list but not of type %s.' \
                                                   '' % (str(phase_value_list),
                                                         type(phase_value_list))
        assert len(phase_value_list) == 5, 'Phase value list %s must be 5 elements.' % str(
            phase_value_list)

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
        :return: list as [phase name, crystal structure type, a, b, c]
        """
        phase_name = str(self._lineEdit_name.text()).strip()
        assert len(phase_name) > 0, 'Phase name must be given!'

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
            raise RuntimeError(
                'Lattice parameters a, b or c does not have correct value. Error: %s.' % str(e))

        print('[DB...BAT] Phase {} of {}: a = {}, b = {}, c = {}'
              ''.format(phase_name, cell_type, a, b, c))

        return [phase_name, cell_type, a, b, c]

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
        assert isinstance(unit_cell_value, list), 'Unit cell value %s must be given in list but not %s.' \
                                                  '' % (str(unit_cell_value), type(unit_cell_value))
        assert len(unit_cell_value) == 5, 'Unit cell value %s must have 5 elements.' % str(
            unit_cell_value)

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
        for index in range(len(UnitCellList)):
            if unit_cell_value[1] == UnitCellList[index][0]:
                new_index = index
                break
        if new_index == -1:
            raise RuntimeError(
                'Impossible to find unit cell type %s not in the list.' % unit_cell_value[1])
        else:
            self._comboBox_type.setCurrentIndex(new_index)

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
    assert isinstance(peak_tup_list, list), 'Peak tuple list should be a list but not of type ' \
                                            '%s.' % str(type(list))

    peak_pos_list = list()
    for peak in peak_tup_list:
        peak_info_tup = peak[0]
        peak_pos = peak_info_tup[0]
        peak_pos_list.append(peak_pos)
    # END-FOR(peak)

    return peak_pos_list
