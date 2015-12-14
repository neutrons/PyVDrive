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
        self.connect(self.ui.pushButton_addCurrentPeak, QtCore.SIGNAL('clicked()'),
                     self.do_add_current_peak)

        self.connect(self.ui.pushButton_addAllPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_add_all_peaks)

        self.connect(self.ui.pushButton_loadCalibFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_calibration_file)

        self.connect(self.ui.pushButton_readData, QtCore.SIGNAL('clicked()'),
                     self.do_load_data)

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

        return

    def _init_widgets_setup(self):
        """

        :return:
        """
        self.ui.treeView_iptsRun.set_main_window(self)

        self.ui.tableWidget_peakParameter.setup()

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

    def do_add_current_peak(self):
        """
        Purpose:
            add current selected peak to table
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
        blabla

        # Gather information for calling
        try:
            peak_list = self._myController.find_peaks(pattern=self._currPattern, profile='Gaussian')
        except RuntimeError as re:
            GuiUtility.pop_dialog_error(self, str(re))
            return

        # Set the peaks to canvas
        peak_pos_list = retrieve_peak_positions(peak_list)
        self.ui.graphicsView_main.add_peak_indicators(peak_pos_list)

        # Set the peaks' parameters to table
        self.ui.tableWidget.append_peaks(peak_list)

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
        # Check requirements
        assert self._myController is not None

        # Get diffraction file
        load_chop_data = False
        load_run_data = False
        if len(str(self.ui.lineEdit_chopDataToLoad.text())) > 0:
            load_chop_data = True
        if len(str(self.ui.lineEdit_runToLoad.text())) > 0:
            load_run_data = True
        if load_chop_data and load_run_data:
            # Specify too many.  Unable to handle
            GuiUtility.pop_dialog_error('Both run and chopped are specified. Unable to handle.')
            return
        elif load_chop_data:
            # Load chopped data
            chop_data_name = str(self.ui.lineEdit_chopDataToLoad.text())
        elif load_run_data:
            # Load data via run
            run_data_name = str(self.ui.lineEdit_runToLoad.text())
        else:
            diff_file_name = str(QtGui.QFileDialog.getOpenFileName(self, 'Open GSAS File'))

        # Load data via parent
        try:
            data_key = self._myController.load_diffraction_file(diff_file_name, 'gsas')
        except RuntimeError as re:
            GuiUtility.pop_dialog_error(self, str(re))
            return

        # Plot data
        # FIXME/NOW : make this section more well-defined
        vecx, vecy = self._myController.get_diffraction_pattern(data_key, bank=1)
        self.ui.graphicsView_main.clear_all_lines()
        self.ui.graphicsView_main.plot_diffraction_pattern(vecx, vecy)

        self.ui.comboBox_bankNumbers.clear()
        self.ui.comboBox_bankNumbers.addItems(['1', '2'])

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

    def set_controller(self, controller):
        """
        """
        # TODO/NOW/Doc
        self._myController = controller

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

        # FIXME/TODO/NOW - Define the response event from mouse

        return

    def on_mouse_release_event(self, event):
        """ If the left button is released and prevoiusly in IN_PICKER_MOVING mode,
        then the mode is over
        """
        button = event.button

        if button == 1:
            # left button click
            pass

        elif button == 3:
            # right button click
            # Launch dynamic pop-out menu
            self.ui.menu = QtGui.QMenu(self)

            action1 = QtGui.QAction('Add Peak', self)
            action1.triggered.connect(self.menu_select_nearest_picker)
            self.ui.menu.addAction(action1)

            # add other required actions
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

        # TODO/NOW/FIXME

        return

    def action1(self):
        """
        """
        print 'Add Peak!'


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
            self._currWS = mantid.simpleapi.LoadGSS(Filename=file_name, OutputWorkspace='Temp')
            self._currWS = mantid.simpleapi.ConvertToPointData(InputWorkspace='Temp', OutputWorkspace='Temp')
        else:
            raise NotImplementedError('File type %s is not supported.' % file_type)

        return file_name

if __name__ == "__main__":
    main(sys.argv)
