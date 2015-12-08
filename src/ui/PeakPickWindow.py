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

        # Set up widgets
        self._init_widgets_setup()

        # Define state variables
        self._dataLoaded = False  # state flag that data is loaded
        self._currDataFile = None  # name of the data file that is currently loaded
        self._myController = None  # Reference to controller class

        return

    def _init_widgets_setup(self):
        """

        :return:
        """
        self.ui.treeView_iptsRun.set_main_window(self)

        return

    def initialize(self, controller):
        """
        Purpose:
        Requires:
        Guarantees:
        :param controller:
        :return:
        """

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
        blabla

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
        blabla

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
        :return:
        """
        raise NotImplemented('Add button to GUI')

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

        return

    def do_quit(self):
        """
        Purpose:
        Requires:
        Guarantees:
        :return:
        """
        return

    def do_save_peaks(self):
        """
        Purpose:
            Save peaks selected by user
        Requires:
            At least one peak is selected
        Guarantees:
        :return:
        """
        return

def main(argv):
    """ Main method for testing purpose
    """
    parent = None

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = PeakPickerWindow(parent)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return

if __name__ == "__main__":
    main(sys.argv)
