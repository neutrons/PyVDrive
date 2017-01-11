# import PyQt modules
from PyQt4 import QtGui, QtCore

# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

import gui.GuiUtility as gutil
import gui.ui_ProcessVanadiumDialog as van_ui


class VanadiumProcessControlDialog(QtGui.QDialog):
    """ GUI (dialog) for process vanadium data
    """
    # Define signals
    myStripPeakSignal = QtCore.pyqtSignal(int, float, str, bool)  # signal to send out
    myUndoStripPeakSignal = QtCore.pyqtSignal()  # signal to undo the peak strip
    mySmoothVanadiumSignal = QtCore.pyqtSignal(str, int, int)  # signal to smooth vanadium spectra
    myUndoSmoothVanadium = QtCore.pyqtSignal()  # signal to undo vanadium peak smooth to raw data

    # mySelectSignal = QtCore.pyqtSignal(str, list) # list of int
    # myCancelSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        """ Set up main window
        """
        # Init & set up GUI
        super(VanadiumProcessControlDialog, self).__init__(parent)
        self._myParent = parent

        # other class variables
        self._inInteractiveMode = False  # flag for being in interactive vanadium smoothing mode

        # setup UI
        self.ui = van_ui.Ui_Dialog()
        self.ui.setupUi(self)

        # initialize the widgets' initial value
        self._init_widgets()

        # define event handling
        # tab for peak striping
        self.connect(self.ui.pushButton_stripVanadiumPeaks, QtCore.SIGNAL('clicked()'),
                     self.do_strip_vanadium_peaks)
        self.connect(self.ui.pushButton_undoPeakStrip, QtCore.SIGNAL('clicked()'),
                     self.do_undo_strip)
        self.connect(self.ui.pushButton_setPeakStripParamToDefaults, QtCore.SIGNAL('clicked()'),
                     self.do_restore_peak_strip_parameters)
        self.connect(self.ui.pushButton_savePeakStripParamAsDefaults, QtCore.SIGNAL('clicked()'),
                     self.do_save_peak_strip_parameters)

        # tab for smoothing vanadium
        self.connect(self.ui.pushButton_smoothVanadium, QtCore.SIGNAL('clicked()'),
                     self.do_smooth_vanadium)
        self.connect(self.ui.pushButton_undoSmooth, QtCore.SIGNAL('clicked()'),
                     self.do_undo_smooth_vanadium)

        # define signal
        self.myStripPeakSignal.connect(self._myParent.signal_strip_vanadium_peaks)
        self.myUndoStripPeakSignal.connect(self._myParent.signal_undo_strip_van_peaks)
        self.mySmoothVanadiumSignal.connect(self._myParent.signal_smooth_vanadium)
        self.myUndoSmoothVanadium.connect(self._myParent.signal_smooth_vanadium)

        return

    def _init_widgets(self):
        """
        initialize widgets
        :return:
        """
        # vanadium peak striping
        self.ui.comboBox_vanPeakBackgroundType.clear()
        self.ui.comboBox_vanPeakBackgroundType.addItem('Linear')
        self.ui.comboBox_vanPeakBackgroundType.addItem('Quadratic')

        # about smoothing
        self.ui.comboBox_smoothFilterTiype.clear()
        self.ui.comboBox_smoothFilterTiype.addItem('Zeroing')
        self.ui.comboBox_smoothFilterTiype.addItem('Butterworth')

        self._inInteractiveMode = self.ui.checkBox_interactiveSmoothing.isChecked()

        return

    def do_restore_peak_strip_parameters(self):
        """
        restore the vanadium peak striping parameters to defaults
        :return:
        """
        blabla

        return

    def do_save_peak_strip_parameters(self):
        """
        save current vanadium-peak-striping parameters as defaults
        :return:
        """
        blabla

        return

    def do_smooth_vanadium(self):
        """
        smooth vanadium data
        :return:
        """
        # get smoothing parameter
        smoother_type = str(self.ui.comboBox_smoothFilterTiype.currentIndex())


    def do_strip_vanadium_peaks(self):
        """
        strip vanadium peaks
        :return:
        """
        # collect the parameters from the UI
        try:
            peak_fwhm = gutil.parse_integer(self.ui.lineEdit_vanPeakFWHM, allow_blank=False)
            fit_tolerance = gutil.parse_float(self.ui.lineEdit_stripPeakTolerance, allow_blank=False)
        except RuntimeError:
            gutil.pop_dialog_error(self, 'Both FWHM and Tolerance must be specified.')
            return

        background_type = str(self.ui.comboBox_vanPeakBackgroundType.currentText())
        is_high_background = self.ui.checkBox_isHighBackground.isChecked()

        self.myStripPeakSignal.emit(peak_fwhm, fit_tolerance, background_type, is_high_background)

        return

    def do_undo_smooth_vanadium(self):
        """

        :return:
        """
        return

    def do_undo_strip(self):
        """
        undo peak striping, i.e., ignore the previous peak strip result and restore the figure (vanadium run)
        :return:
        """
        self.myUndoStripPeakSignal.emit()

        return


