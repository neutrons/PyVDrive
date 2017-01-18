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
        self.connect(self.ui.pushButton_setSmoothNRange, QtCore.SIGNAL('clicked()'),
                     self.do_set_smooth_n_range)
        self.connect(self.ui.pushButton_setSmoothOrderRange, QtCore.SIGNAL('clicked()'),
                     self.do_set_smooth_order_range)

        self.connect(self.ui.lineEdit_smoothParameterN, QtCore.SIGNAL('textChanged(QString)'),
                     self.evt_smooth_vanadium)
        self.connect(self.ui.horizontalSlider_smoothN, QtCore.SIGNAL('valueChanged(int)'),
                     self.evt_smooth_param_changed)
        self.connect(self.ui.horizontalSlider_smoothOrder, QtCore.SIGNAL('valueChanged(int)'),
                     self.evt_smooth_param_changed)

        # final
        self.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'),
                     self.do_quit)

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

        # initial value
        # self.ui.lineEdit_vanPeakFWHM.setText('7')
        # self.ui.lineEdit_stripPeakTolerance.setText('0.05')
        # self.ui.comboBox_vanPeakBackgroundType.setCurrentIndex(1)
        # self.ui.checkBox_isHighBackground.setChecked(True)

        # load setting
        self.load_settings()
        self.do_restore_peak_strip_parameters()
        self.do_restore_smooth_vanadium_parameters()

        return

    def do_quit(self):
        """
        close the dialog box
        :return:
        """
        self.save_settings()

        self.close()

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

    def do_set_smooth_n_range(self):
        """
        set the slider for smoothing parameter n's range
        :return:
        """
        try:
            min_value, max_value = gutil.parse_integer_list(self.ui.lineEdit_smoothNRange, 2, check_order=True,
                                                            increase=True)
        except RuntimeError:
            gutil.pop_dialog_error(self, 'Smoothing parameter N\'s range must have 2 integers'
                                         'in increase order.')
            return

        self.ui.horizontalSlider_smoothN.setRange(min_value, max_value)

        return

    def do_set_smooth_order_range(self):
        """
        set the slider for smoothing parameter order's range
        :return:
        """
        try:
            min_value, max_value = gutil.parse_integer_list(self.ui.lineEdit_smoothOrderRange, 2, check_order=True,
                                                            increase=True)
        except RuntimeError:
            gutil.pop_dialog_error(self, 'Smoothing parameter order\'s range must have 2 integers'
                                         'in increasing order.')
            return

        self.ui.horizontalSlider_smoothOrder.setRange(min_value, max_value)

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
        handling the event caused by value change  of smooth parameters via the slider
        :return:
        """
        # get the value
        smooth_n = self.ui.horizontalSlider_smoothN.value()
        self.ui.lineEdit_smoothParameterN.setText(str(smooth_n))

        smooth_order = self.ui.horizontalSlider_smoothOrder.value()
        self.ui.lineEdit_smoothParameterOrder.setText(str(smooth_order))

        return

    def evt_smooth_vanadium(self):
        """
        handle the event that the smoothing parameters are changed in the line edits
        if the smoothing operation is in the interactive mode, then it is same as
        pressing the 'smooth vanadium' button
        :return:
        """
        if self.ui.checkBox_interactiveSmoothing.isChecked():
            self.do_smooth_vanadium()

        return

    def load_settings(self):
        """
        Load QSettings from previous saved file
        :return:
        """
        settings = QtCore.QSettings()

        # strip vanadium peaks
        self._defaultDict['FWHM'] = load_setting_integer(settings, 'FWHM', 7)
        self._defaultDict['Tolerance'] = load_setting_float(settings, 'Tolerance', 0.05)
        self._defaultDict['BackgroundType'] = load_setting_str(settings, 'BackgroundType', 'Quadratic')
        self._defaultDict['IsHighBackground'] = load_setting_bool(settings, 'IsHightBackground', True)

        # smooth spectra
        self._defaultDict['Order'] = load_setting_integer(settings, 'Order', 2)
        self._defaultDict['n'] = load_setting_integer(settings, 'n', 10)
        self._defaultDict['Smoother'] = load_setting_str(settings, 'Smoother', 'Butterworth')

        return

    def save_settings(self):
        """
        Save settings (parameter set) upon quiting
        :return:
        """
        settings = QtCore.QSettings()

        # the default vanadium peak strip parameters
        for value_name in self._defaultDict.keys():
            settings.setValue(value_name, self._defaultDict[value_name])

        return


def load_setting_bool(qsettings, param_name, default_value):
    """
    load setting as an integer
    :param qsettings:
    :param param_name:
    :param default_value:
    :return:
    """
    # check
    assert isinstance(qsettings, QtCore.QSettings), 'Input settings must be a QSetting instance but not {0}.' \
                                                    ''.format(type(qsettings))

    value_str = qsettings.value(param_name, default_value)

    try:
        bool_value = bool(str(value_str))
    except TypeError:
        raise RuntimeError('QSetting cannot cast {0} with value {1} to a boolean.'.format(param_name, value_str))

    return bool_value


def load_setting_integer(qsettings, param_name, default_value):
    """
    load setting as an integer
    :param qsettings:
    :param param_name:
    :param default_value:
    :return:
    """
    # check
    assert isinstance(qsettings, QtCore.QSettings), 'Input settings must be a QSetting instance but not {0}.' \
                                                    ''.format(type(qsettings))

    value_str = qsettings.value(param_name, default_value)

    try:
        int_value = int(str(value_str))
    except TypeError:
        raise RuntimeError('QSetting cannot cast {0} with value {1} to integer.'.format(param_name, value_str))

    return int_value


def load_setting_float(qsettings, param_name, default_value):
    """
    load setting as an integer
    :param qsettings:
    :param param_name:
    :param default_value:
    :return:
    """
    # check
    assert isinstance(qsettings, QtCore.QSettings), 'Input settings must be a QSetting instance but not {0}.' \
                                                    ''.format(type(qsettings))

    value_str = qsettings.value(param_name, default_value)

    try:
        float_value = float(str(value_str))
    except TypeError:
        raise RuntimeError('QSetting cannot cast {0} with value {1} to a float.'.format(param_name, value_str))

    return float_value


def load_setting_str(qsettings, param_name, default_value):
    """
    load setting as an integer
    :param qsettings:
    :param param_name:
    :param default_value:
    :return:
    """
    # check
    assert isinstance(qsettings, QtCore.QSettings), 'Input settings must be a QSetting instance but not {0}.' \
                                                    ''.format(type(qsettings))

    value_str = qsettings.value(param_name, default_value)

    return value_str


