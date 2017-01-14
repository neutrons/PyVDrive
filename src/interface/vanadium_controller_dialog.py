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
        self.connect(self.ui.pushButton_setPeakStripParamToDefaults, QtCore.SIGNAL('clicked()'),
                     self.do_restore_smooth_vanadium_parameters)
        self.connect(self.ui.pushButton_saveSmoothParamAsDefaults, QtCore.SIGNAL('clicked()'),
                     self.do_save_vanadium_smooth_parameters)

        self.connect()

        self.connect(self.ui.horizontalSlider_smoothN, QtCore.SIGNAL('valueChanged(int)'),
                     self.evt_smooth_param_changed)
        self.connect(self.ui.horizontalSlider_smoothOrder, QtCore.SIGNAL('valueChanged(int)'),
                     self.evt_smooth_param_changed)

        # define signal
        self.myStripPeakSignal.connect(self._myParent.signal_strip_vanadium_peaks)
        self.myUndoStripPeakSignal.connect(self._myParent.signal_undo_strip_van_peaks)
        self.mySmoothVanadiumSignal.connect(self._myParent.signal_smooth_vanadium)
        self.myUndoSmoothVanadium.connect(self._myParent.signal_smooth_vanadium)

        # stored default parameters
        self._defaultDict = dict()

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

        # set range of the sliders
        self.ui.horizontalSlider_smoothN.setRange(0, 50)
        self.ui.horizontalSlider_smoothOrder.setRange(0, 40)

        return

    def do_restore_peak_strip_parameters(self):
        """
        restore the vanadium peak striping parameters to defaults
        :return:
        """
        self.ui.lineEdit_vanPeakFWHM.setText(str(self._defaultDict['FWHM']))
        self.ui.lineEdit_stripPeakTolerance.setText(str(self._defaultDict['Tolerance']))

        return

    def do_restore_smooth_vanadium_parameters(self):
        """
        restore the vanadium smoothing parameters to defaults
        :return:
        """
        # parameter order and n
        self.ui.lineEdit_smoothParameterOrder.setText(str(self._defaultDict['Order']))
        self.ui.lineEdit_smoothParameterN.setText(str(self._defaultDict['n']))

        # type of smoothing algorithm
        if self._defaultDict['Smoother'] == 'Zeroing':
            self.ui.comboBox_smoothFilterTiype.setCurrentIndex(0)
        else:
            self.ui.comboBox_smoothFilterTiype.setCurrentIndex(1)

        return

    def do_save_peak_strip_parameters(self):
        """
        save current vanadium-peak-striping parameters as defaults
        :return:
        """
        self._defaultDict['FWHM'] = gutil.parse_integer(self.ui.lineEdit_vanPeakFWHM)
        self._defaultDict['Tolerance'] = gutil.parse_integer(self.ui.lineEdit_vanPeakFWHM)
        self._defaultDict['BackgroundType'] = str(self.ui.comboBox_vanPeakBackgroundType.currentText())
        self._defaultDict['IsHighBackground'] = self.ui.checkBox_isHighBackground.isChecked()

        return

    def do_save_vanadium_smooth_parameters(self):
        """
        save the vanadium smoothing parameters
        :return:
        """
        self._defaultDict['Order'] = gutil.parse_integer(self.ui.lineEdit_smoothParameterOrder)
        self._defaultDict['n'] = gutil.parse_integer(self.ui.lineEdit_smoothParameterN)
        self._defaultDict['Smoother'] = str(self.ui.comboBox_smoothFilterTiype.currentText())

        return

    def do_smooth_vanadium(self):
        """
        smooth vanadium data
        :return:
        """
        # get smoothing parameter
        try:
            smoother_type = str(self.ui.comboBox_smoothFilterTiype.currentIndex())
            smoother_n = gutil.parse_integer(self.ui.lineEdit_smoothParameterN, allow_blank=False)
            smoother_order = gutil.parse_integer(self.ui.lineEdit_smoothParameterOrder, allow_blank=False)
        except RuntimeError:
            gutil.pop_dialog_error(self, 'Smoothing parameter N or order is specified incorrectly.')
            return

        # emit signal
        self.mySmoothVanadiumSignal.emit(smoother_type, smoother_n, smoother_order)

        return

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
        undo the action to smooth vanadium
        :return:
        """
        self.myUndoSmoothVanadium.emit()

        return

    def do_undo_strip(self):
        """
        undo peak striping, i.e., ignore the previous peak strip result and restore the figure (vanadium run)
        :return:
        """
        self.myUndoStripPeakSignal.emit()

        return

    def evt_smooth_param_changed(self):
        """
        handling the event caused by value change  of smooth parameters
        :return:
        """
        # get the value
        smooth_n = self.ui.horizontalSlider_smoothN.value()
        self.ui.lineEdit_smoothParameterN.setText(str(smooth_n))

        smooth_order = self.ui.horizontalSlider_smoothOrder.value()
        self.ui.lineEdit_smoothParameterOrder.setText(str(smooth_order))

        return




