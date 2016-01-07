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
    def __init__(self):
        """

        :return:
        """
        self._lineEdit_a = None
        self._lineEdit_b = None
        self._lineEdit_c = None

        self._lineEdit_name = None
        self._comboBox_type = None

        self._checkBox_selected = None

        return

    def set_widgets(self, edit_a, edit_b, edit_c, edit_name, combo_box_type, check_box_select):
        """

        :param edit_a:
        :param edit_b:
        :param edit_c:
        :param edit_name:
        :param combo_box_type:
        :param check_box_select:
        :return:
        """
        # TODO/NOW/1st: Assertion!

        self._lineEdit_a = edit_a
        self._lineEdit_b = edit_b
        self._lineEdit_c = edit_c
        self._lineEdit_name = edit_name
        self._comboBox_type = combo_box_type
        self._checkBox_selected = check_box_select

        return

    def is_selected(self):
        """

        :return:
        """
        # TODO/NOW/1st: Doc and ...
        assert isinstance(self._checkBox_selected, QtGui.QCheckBox)

        return self._checkBox_selected.isChecked()

    def get_phase(self):
        """

        :return: list as [name, type, a, b, c]
        """
        # TODO/NOW/1st: Doc and assertion

        name = str(self._lineEdit_name.text()).strip()
        assert len(name) > 0, 'bla bla'

        cell_type = str(self._comboBox_type.currentText()).split()[0]
        a = float(self._lineEdit_a.text())
        b = float(self._lineEdit_b.text())
        c = float(self._lineEdit_c.text())

        return [name, cell_type, a, b, c]


class PeakPickerWindow(QtGui.QMainWindow):
    """ Class for general-puposed plot window
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
                     # TODO/FIXME/1st add this method
                     self.do_clear_phases)

        self.connect(self.ui.pushButton_cancelPhaseChange, QtCore.SIGNAL('clicked()'),
                     # TODO/FIXME/1st add this method
                     self.do_undo_phase_changes)

        # peak processing
        self.connect(self.ui.pushButton_addAllPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_add_all_peaks)

        self.connect(self.ui.pushButton_findPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_find_peaks)

        self.connect(self.ui.pushButton_claimOverlappedPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_claim_overlapped_peaks)

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
        self._init_widgets_setup()

        # Define state variables
        self._isInitialized = False

        self._dataLoaded = False  # state flag that data is loaded
        self._currDataFile = None  # name of the data file that is currently loaded
        self._myController = None  # Reference to controller class
        self._dataDirectory = None

        # Peak selection mode
        self._peakSelectionMode = ''
        self._indicatorIDList = None
        self._indicatorPositionList = None
        self._inEditMode = False

        # Mouse position
        self._currMousePosX = 0
        self._currMousePosY = 0

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

        # TODO/1st set up the box 2 and 3

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
        assert self._isInitialized is False
        assert isinstance(controller, vapi.VDriveAPI)

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
        assert self._isInitialized is True, 'Instance is not initialized.'
        assert self._dataLoaded is True, 'No data is loaded.'

        # Find out the highlighted (i.e., current) peak from canvas
        try:
            pos_x, pos_y = self.ui.graphicsView_main.get_highlight_peak()
        except RuntimeError as re:
            GuiUtility.pop_dialog_error(str(re))
            return
        if pos_x is None or pos_y is None:
            GuiUtility.pop_dialog_error('Unable to find highlighted peak in canvas.')
            return

        # Add the peak to both the placeholder and table
        try:
            diff_peak = self._myController.fit_peak(self._currDataFile, pos_x)
        except RuntimeError as e:
            GuiUtility.pop_dialog_error(self, 'Unable to add peak at x = %f due to %s' % (pos_x, str(e)))
            return

        return

    def do_add_all_peaks(self):
        """
        Purpose:
            add all peaks that can be found in the data or on the canvas to table
        Requires:
            Window has been set with parent controller
            data has been loaded;
            GUI is in peak selection mode;
        Guarantees
        :return:
        """
        # Check requirements
        assert self._currDataFile is not None
        assert self._myController is not None
        blabla

        # Get all peaks from canvas, i.e., all peak indicators in canvas
        peak_pos_list = self.ui.graphicsView_main.get_peaks_pos()

        # Set the peaks' position to placeholder and table
        blabla

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

    def do_delete_peaks_fm_table(self):
        """
        Purpose:
            Delete the added peak from table and place holder
        Requirements:
            At least one peak is selected in the table
        Guarantees:
            The selected peak is removed from both placeholder and table
        :return:
        """
        raise NotImplemented('Add button to GUI')

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

        # FIXME/NOW/1st - how to define minD and maxD???
        min_d = 0.5
        max_d = 5.0

        # List all peaks according to
        if len(self._phaseList) > 0:
            # At least 1 phase should be defined.
            reflection_list = list()
            for phase in self._phaseList:
                print phase
                sub_list = self._myController.calculate_peaks_position(phase, min_d, max_d)
                for peak_tup in sub_list:
                    print peak_tup[1], peak_tup[0]
                reflection_list.extend(sub_list)

        else:
            # Use algorithm to find peak automatically
            try:
                reflection_list = self._myController.find_peaks(pattern=self._currPattern, profile='Gaussian')
            except RuntimeError as re:
                GuiUtility.pop_dialog_error(self, str(re))
                return

        # Set the peaks to canvas
        peak_pos_list = retrieve_peak_positions(reflection_list)
        self.ui.graphicsView_main.add_peak_indicators(peak_pos_list)

        # Set the peaks' parameters to table
        self.ui.tableWidget_peakParameter.append_peaks(reflection_list)

        return

    def do_load_bank(self):
        """

        :return:
        """
        print 'Load another bank!'

    def do_clear_phases(self):
        pass

    def do_undo_phase_changes(self):
        pass

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

        # Plot data
        run_number, num_banks = self._myController.get_diffraction_pattern_info(data_key)

        # update widgets
        self.ui.comboBox_runNumber.addItem(str(run_number))
        self.ui.comboBox_bankNumbers.clear()
        for i_bank in xrange(num_banks):
            self.ui.comboBox_bankNumbers.addItem(str(i_bank+1))
        self.ui.label_diffractionMessage.setText('Run %d Bank %d' % (run_number, 1))

        # load bank 1 as default
        vec_x, vec_y = self._myController.get_diffraction_pattern(data_key, bank=1)
        self.ui.graphicsView_main.clear_all_lines()
        self.ui.graphicsView_main.plot_diffraction_pattern(vec_x, vec_y)

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

    def do_set_phases(self):
        """ Set phases from GUI
        Purpose:
        Requirements:
        Guarantees:
        :return:
        """
        # TODO/NOW/1st: doc and assertion, and add phase 2 and 3

        # Phase 1

        for i_phase in xrange(3):
            pass

        # TODO/FIXME/1st: this is a prototype. after testing, make it good for up to 3 phases
        self._phaseList = list()
        phase_widgets = PhaseWidgets()
        phase_widgets.set_widgets(self.ui.lineEdit_a1, self.ui.lineEdit_b1, self.ui.lineEdit_c1,
                                  self.ui.lineEdit_phaseName1, self.ui.comboBox_structure1,
                                  self.ui.checkBox_usePhase1)
        phase = phase_widgets.get_phase()
        self._phaseList.append(phase)

        return

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


def retrieve_peak_positions(peak_list):
    """
    Purpose:
        Retrieve peak positions from peaks in given list
    Requirements:
        Input is a list of DiffractionPeak object
    Guarantees:
        Retrieve the peaks' positions out
    :param peak_list:
    :return: a list of
    """
    assert isinstance(peak_list, list)

    peak_pos_list = list()
    for peak in peak_list:
        assert isinstance(peak, df.DiffractionPeak)
        peak_pos = peak.centre
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

        :param phase:
        :param min_d:
        :param max_d:
        :return:
        """
        # FIXME/TODO/NOW/1st - Doc, Assertion and Implement from prototype
        import PyVDrive.vdrive.mantid_helper as mantid_helper

        silicon = mantid_helper.UnitCell(mantid_helper.UnitCell.FC, 5.43) #, 5.43, 5.43)
        reflections = mantid_helper.calculate_reflections(silicon, 1.0, 5.0)

        # Sort by d-space... NOT FINISHED YET
        num_ref = len(reflections)
        ref_dict = dict()
        for i_ref in xrange(num_ref):
            ref_tup = reflections[i_ref]
            pos_d = ref_tup[1]
            hkl = ref_tup[0]
            if pos_d not in ref_dict:
                ref_dict[pos_d] = list()
            ref_dict[pos_d].append(hkl)

        return reflections

    def get_diffraction_pattern_info(self, data_key):
        """
        :return:
        """
        import os
        # TODO/NOW: Doc and assertion
        print 'Data key is %s of type %s' % (str(data_key), str(type(data_key)))

        # Key (temporary) is the file name
        run_number = int(os.path.basename(data_key).split('.')[0])
        #
        num_banks = self._currWS.getNumberHistograms()

        return run_number, num_banks

    def get_diffraction_pattern(self, data_key, bank):
        """

        :param data_key:
        :param bank:
        :return:
        """
        ws_index = bank-1
        vec_x = self._currWS.readX(ws_index)
        vec_y = self._currWS.readY(ws_index)

        return vec_x, vec_y

    def load_diffraction_file(self, file_name, file_type):
        """

        :param file_type:
        :return:
        """
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
