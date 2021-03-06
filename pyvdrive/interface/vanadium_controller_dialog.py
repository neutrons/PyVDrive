# import PyQt modules
import os
try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5 import QtCore
    from PyQt5.Qt import QVariant
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.uic import loadUi as load_ui
    from PyQt5.QtWidgets import QDialog, QFileDialog
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.Qt import QVariant
    from PyQt4.QtGui import QVBoxLayout  # noqa: F401
    from PyQt4.uic import loadUi as load_ui
    from PyQt4.QtGui import QDialog, QFileDialog

# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s): return s

from pyvdrive.interface.gui import GuiUtility
from pyvdrive.core import datatypeutility


class VanadiumProcessControlDialog(QDialog):
    """ GUI (dialog) for process vanadium data
    """
    # Define signals
    myStripPeakSignal = QtCore.pyqtSignal(int, int, float, str, bool)  # signal to send out
    myUndoStripPeakSignal = QtCore.pyqtSignal()  # signal to undo the peak strip
    mySmoothVanadiumSignal = QtCore.pyqtSignal(
        int, str, int, int)  # signal to smooth vanadium spectra
    myUndoSmoothVanadium = QtCore.pyqtSignal()  # signal to undo vanadium peak smooth to raw data
    myApplyResultSignal = QtCore.pyqtSignal(str, int)  # signal to apply/save the smoothed vanadium
    myShowVPeaksSignal = QtCore.pyqtSignal(bool, name='ShowVanPeaks')

    def __init__(self, parent):
        """ Set up main window
        """
        # Init & set up GUI
        super(VanadiumProcessControlDialog, self).__init__(parent)
        self._myParent = parent

        # stored default parameters
        self._defaultDict = dict()

        # other class variables
        self._inInteractiveMode = False  # flag for being in interactive vanadium smoothing mode

        # mutex
        self._slidersMutex = False  # mutex for sliders

        # class variables
        self._min_smooth_n = 2  # 1 is the lower boundary for minimum smooth N
        self._max_smooth_n = None
        self._min_smooth_order = 1  # 1 is the lower boundary for minimum smooth order
        self._max_smooth_order = None

        # setup UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui/ProcessVanadiumDialog.ui")
        self.ui = load_ui(ui_path, baseinstance=self)

        # initialize the widgets' initial value
        self._init_widgets()

        # define event handling
        # tab for peak striping
        self.ui.pushButton_stripVanadiumPeaks.clicked.connect(self.do_strip_vanadium_peaks)
        self.ui.pushButton_undoPeakStrip.clicked.connect(self.do_undo_strip)
        self.ui.pushButton_setPeakStripParamToDefaults.clicked.connect(
            self.do_restore_peak_strip_parameters)
        self.ui.pushButton_savePeakStripParamAsDefaults.clicked.connect(
            self.do_save_peak_strip_parameters)

        # self.ui.pushButton_showVPeaks.clicked.connect(self.do_show_vanadium_peaks)
        self.ui.pushButton_nDecrease.clicked.connect(self.do_decrease_smooth_n)
        self.ui.pushButton_nIncrease.clicked.connect(self.do_increase_smooth_n)
        self.ui.pushButton_orderDecrease.clicked.connect(self.do_decrease_smooth_order)
        self.ui.pushButton_orderIncrease.clicked.connect(self.do_increase_smooth_order)

        # TODO - 20181103 - Implement: self.ui.comboBox_banks  currentIndexChange: re-plot

        # tab for smoothing vanadium
        self.ui.pushButton_smoothVanadium.clicked.connect(self.do_smooth_vanadium)
        self.ui.pushButton_undoSmooth.clicked.connect(self.do_undo_smooth_vanadium)
        self.ui.pushButton_setPeakStripParamToDefaults.clicked.connect(
            self.do_restore_smooth_vanadium_parameters)
        self.ui.pushButton_saveSmoothParamAsDefaults.clicked.connect(
            self.do_save_vanadium_smooth_parameters)
        self.ui.pushButton_setSmoothNRange.clicked.connect(self.do_set_smooth_n_range)
        self.ui.pushButton_setSmoothOrderRange.clicked.connect(self.do_set_smooth_order_range)

        self.ui.lineEdit_smoothParameterN.textChanged.connect(self.evt_smooth_vanadium)
        self.ui.lineEdit_smoothParameterOrder.textChanged.connect(self.evt_smooth_vanadium)
        self.ui.horizontalSlider_smoothN.valueChanged.connect(self.evt_smooth_param_changed)
        self.ui.horizontalSlider_smoothOrder.valueChanged.connect(self.evt_smooth_param_changed)

        # final
        self.ui.pushButton_applyVanProcessResult.clicked.connect(self.do_save_result)
        self.ui.pushButton_quit.clicked.connect(self.do_quit)

        # define signal
        self.myStripPeakSignal.connect(self._myParent.signal_strip_vanadium_peaks)
        self.myUndoStripPeakSignal.connect(self._myParent.signal_undo_strip_van_peaks)
        self.mySmoothVanadiumSignal.connect(self._myParent.signal_smooth_vanadium)
        self.myUndoSmoothVanadium.connect(self._myParent.signal_smooth_vanadium)
        self.myApplyResultSignal.connect(self._myParent.signal_save_processed_vanadium)
        self.myShowVPeaksSignal.connect(self._myParent._subControllerVanadium.show_hide_v_peaks)

        # TODO - TONIGHT 1 - self.ui.pushButton_bfSearchSmooth.connect(self.do_smooth_bf)

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
        self.ui.horizontalSlider_smoothN.setRange(2, 50)
        self._min_smooth_n = 2
        self._max_smooth_n = 50
        self.ui.horizontalSlider_smoothOrder.setRange(1, 40)
        self._min_smooth_order = 1
        self._max_smooth_order = 40

        # initial value
        # self.ui.lineEdit_vanPeakFWHM.setText('7')
        # self.ui.lineEdit_stripPeakTolerance.setText('0.05')
        # self.ui.comboBox_vanPeakBackgroundType.setCurrentIndex(1)
        # self.ui.checkBox_isHighBackground.setChecked(True)

        # load setting
        self.load_settings()
        self.do_restore_peak_strip_parameters()
        self.do_restore_smooth_vanadium_parameters()

        # check box
        self.ui.checkBox_isHighBackground.setChecked(True)

        # hide
        self.ui.pushButton_undoPeakStrip.hide()
        self.ui.pushButton_setPeakStripParamToDefaults.hide()
        self.ui.pushButton_savePeakStripParamAsDefaults.hide()
        self.ui.pushButton_undoSmooth.hide()
        self.ui.pushButton_setSmoothParamToDefaults.hide()
        self.ui.pushButton_saveSmoothParamAsDefaults.hide()
        self.ui.pushButton_bfSearchSmooth.hide()
        self.ui.pushButton_applyVanProcessResult.hide()

        return

    def do_increase_smooth_n(self):
        """
        increase the n value of smooth parameter by 1
        :return:
        """
        curr_value = self.ui.horizontalSlider_smoothN.value()

        # stop at maximum
        if curr_value == self._max_smooth_n:
            return
        self.ui.horizontalSlider_smoothN.setValue(curr_value + 1)

        return

    def do_decrease_smooth_n(self):
        """
        decrease the n value of smooth parameter by 1
        :return:
        """
        curr_value = self.ui.horizontalSlider_smoothN.value()

        # stop at maximum
        if curr_value == self._min_smooth_n:
            return
        self.ui.horizontalSlider_smoothN.setValue(curr_value - 1)

        return

    def do_increase_smooth_order(self):
        """
        increase the order's value of smooth parameter by 1
        :return:
        """
        curr_value = self.ui.horizontalSlider_smoothOrder.value()

        # stop at maximum
        if curr_value == self._max_smooth_order:
            return
        self.ui.horizontalSlider_smoothOrder.setValue(curr_value + 1)

        return

    def do_decrease_smooth_order(self):
        """
        decrease the order's value of smooth parameter by 1
        :return:
        """
        curr_value = self.ui.horizontalSlider_smoothOrder.value()
        # stop at maximum
        if curr_value == self._min_smooth_order:
            return
        self.ui.horizontalSlider_smoothOrder.setValue(curr_value - 1)

        return

    def do_plot_vanadiums(self):
        """

        :return:
        """
        bank_id = int(str(self.ui.comboBox_plotBanks.currentText()))
        if self.ui.tabWidget.currentIndex() == 0:
            plot_smoothed = False
        else:
            plot_smoothed = True

        run_id = str(self.ui.lineEdit_runNumber.text())
        self._myParent.plot_1d_vanadium(run_id, bank_id, is_smoothed_data=plot_smoothed)

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
        self._defaultDict['FWHM'] = GuiUtility.parse_integer(self.ui.lineEdit_vanPeakFWHM)
        self._defaultDict['Tolerance'] = GuiUtility.parse_integer(self.ui.lineEdit_vanPeakFWHM)
        self._defaultDict['BackgroundType'] = str(
            self.ui.comboBox_vanPeakBackgroundType.currentText())
        self._defaultDict['IsHighBackground'] = self.ui.checkBox_isHighBackground.isChecked()

        return

    def do_save_result(self):
        """
        apply the result to controller
        :return:
        """
        # get IPTS number and run number
        try:
            run_number = GuiUtility.parse_integer(self.ui.lineEdit_runNumber, allow_blank=False)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(
                self, 'IPTS and run number must be specified in order to save for GSAS. {}.'.format(run_err))
            return

        # get default directory
        default_dir = '/SNS/VULCAN/shared/CalibrationFiles/Instrument/Standards/Vanadium'
        if not os.access(default_dir, os.W_OK):
            default_dir = os.getcwd()

        file_filter = 'GSAS (*.gda);;All (*.*)'
        van_file_name = str(QFileDialog.getSaveFileName(self, 'Smoothed Vanadium File',
                                                              default_dir, file_filter))
        if len(van_file_name) == 0:
            return

        self.myApplyResultSignal.emit(van_file_name, run_number)

        return

    def do_save_vanadium_smooth_parameters(self):
        """
        save the vanadium smoothing parameters
        :return:
        """
        self._defaultDict['Order'] = GuiUtility.parse_integer(self.ui.lineEdit_smoothParameterOrder)
        self._defaultDict['n'] = GuiUtility.parse_integer(self.ui.lineEdit_smoothParameterN)
        self._defaultDict['Smoother'] = str(self.ui.comboBox_smoothFilterTiype.currentText())

        return

    def do_set_smooth_n_range(self):
        """
        set the slider for smoothing parameter n's range
        :return:
        """
        try:
            min_value, max_value = GuiUtility.parse_integer_list(self.ui.lineEdit_smoothNRange, 2, check_order=True,
                                                                 increase=True)
        except RuntimeError:
            GuiUtility.pop_dialog_error(self, 'Smoothing parameter N\'s range must have 2 integers '
                                              'in increase order.')
            return

        self.ui.horizontalSlider_smoothN.setRange(min_value, max_value)
        self._min_smooth_n = min(2, min_value)
        self._max_smooth_n = max_value

        return

    def do_set_smooth_order_range(self):
        """
        set the slider for smoothing parameter order's range
        :return:
        """
        try:
            min_value, max_value = GuiUtility.parse_integer_list(self.ui.lineEdit_smoothOrderRange, 2,
                                                                 check_order=True, increase=True)
        except RuntimeError:
            GuiUtility.pop_dialog_error(self, 'Smoothing parameter order\'s range must have 2 integers '
                                              'in increasing order.')
            return

        self.ui.horizontalSlider_smoothOrder.setRange(min_value, max_value)
        self._min_smooth_order = min(1, min_value)
        self._max_smooth_order = max_value

        return

    def do_smooth_bf(self):
        """
        Use brute force to
        :return:
        """

    def _get_banks_group(self):
        # append the banks
        bank_group = str(self.ui.comboBox_banks.currentText())
        if bank_group.count('East') > 0:
            bank_group_index = 90
        elif bank_group.count('High') > 0:
            bank_group_index = 150
        else:
            raise NotImplementedError('Bank group {} is not supported.'.format(bank_group))

        return bank_group_index

    def do_show_vanadium_peaks(self):
        """ show or hide vanadium peaks in d-spacing on main canvas
        i.e., add indicators for vanadium peaks (theory)
        :return:
        """
        # check whether it shall show or hide
        button_state = str(self.ui.pushButton_showVPeaks.text())
        if button_state.lower().count('show'):
            # show
            self.myShowVPeaksSignal.emit(True)
            self.ui.pushButton_showVPeaks.setText('Hide V Peaks')
        else:
            # hide
            self.myShowVPeaksSignal.emit(False)
            self.ui.pushButton_showVPeaks.setText('Show V Peaks')

        return

    def do_smooth_vanadium(self):
        """
        smooth vanadium data
        :return:
        """
        # bank_group_index = self._get_banks_group()

        # get smoothing parameter
        try:
            smoother_type = str(self.ui.comboBox_smoothFilterTiype.currentText())
            smoother_n = GuiUtility.parse_integer(self.ui.lineEdit_smoothParameterN, allow_blank=False)
            smoother_order = GuiUtility.parse_integer(
                self.ui.lineEdit_smoothParameterOrder, allow_blank=False)
        except RuntimeError:
            GuiUtility.pop_dialog_error(self, 'Smoothing parameter N or order is specified incorrectly.')
            return

        # emit signal
        print('[DB...BAT] Smooth type = {}, n = {}, order = {}'.format(smoother_type, smoother_n,
                                                                       smoother_order))
        self.mySmoothVanadiumSignal.emit(1, smoother_type, smoother_n, smoother_order)

        return

    def do_strip_vanadium_peaks(self):
        """
        strip vanadium peaks
        :return:
        """
        # collect the parameters from the UI
        try:
            peak_fwhm = GuiUtility.parse_integer(self.ui.lineEdit_vanPeakFWHM, allow_blank=False)
            fit_tolerance = GuiUtility.parse_float(
                self.ui.lineEdit_stripPeakTolerance, allow_blank=False)
        except RuntimeError:
            GuiUtility.pop_dialog_error(self, 'Both FWHM and Tolerance must be specified.')
            return

        # append the banks
        # bank_group = str(self.ui.comboBox_banks.currentText())
        # if bank_group.count('East') > 0:
        #     bank_group_index = 90
        # elif bank_group.count('High') > 0:
        #     bank_group_index = 150
        # else:
        #     raise NotImplementedError('Bank group {} is not supported.'.format(bank_group))
        # bank_group_index = self._get_banks_group()

        background_type = str(self.ui.comboBox_vanPeakBackgroundType.currentText())
        is_high_background = self.ui.checkBox_isHighBackground.isChecked()

        self.myStripPeakSignal.emit(1, peak_fwhm, fit_tolerance,
                                    background_type, is_high_background)

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
        # change parameters
        self._slidersMutex = True
        param_n = GuiUtility.parse_integer(self.ui.lineEdit_smoothParameterN, allow_blank=False)
        if param_n is None or param_n == 0:
            param_n = 1
        self.ui.horizontalSlider_smoothN.setValue(param_n)

        param_order = GuiUtility.parse_integer(self.ui.lineEdit_smoothParameterOrder, allow_blank=False)
        if param_order is None or param_order == 0:
            param_order = 1
        self.ui.horizontalSlider_smoothOrder.setValue(param_order)

        self._slidersMutex = False

        # smooth vanadium
        if self.ui.checkBox_interactiveSmoothing.isChecked():
            self.do_smooth_vanadium()

        return

    def get_run_id(self):
        return str(self.ui.lineEdit_runNumber.text())

    def load_settings(self):
        """
        Load QSettings from previous saved file
        :return:
        """
        settings = QtCore.QSettings()

        # strip vanadium peaks
        self._defaultDict['FWHM'] = load_setting_integer(settings, 'FWHM', 7)
        self._defaultDict['Tolerance'] = load_setting_float(settings, 'Tolerance', 0.05)
        self._defaultDict['BackgroundType'] = load_setting_str(
            settings, 'BackgroundType', 'Quadratic')
        self._defaultDict['IsHighBackground'] = load_setting_bool(
            settings, 'IsHightBackground', True)

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

    def set_peak_fwhm(self, peak_fwhm):
        """
        set vanadium peak's FWHM
        :param peak_fwhm:
        :return:
        """
        self.ui.lineEdit_vanPeakFWHM.setText('{0}'.format(peak_fwhm))

        return

    # TODO - TONIGHT 101 - This method may be replaced by others
    def plot_1d_vanadium(self, run_id, bank_id, is_smoothed_data=False):
        """

        :param run_id:
        :param bank_id:
        :return:
        """
        # check input
        datatypeutility.check_string_variable('Run ID', run_id)
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 100))

        # clear previous image
        self.ui.graphicsView_mainPlot.clear_all_lines()
        # change unit
        self.ui.comboBox_unit.setCurrentIndex(1)

        # plot original run
        # raw_van_key = run_id, bank_id, self._currUnit
        # if raw_van_key in self._currentPlotDataKeyDict:
        #     # data already been loaded before
        #     vec_x, vec_y = self._currentPlotDataKeyDict[raw_van_key]
        # else:
        #     vec_x, vec_y = self.retrieve_loaded_reduced_data(data_key=run_id, bank_id=bank_id,
        #                                                      unit=self._currUnit)
        #     self._currentPlotDataKeyDict[raw_van_key] = vec_x, vec_y

        if is_smoothed_data:
            plot_unit = 'TOF'
        else:
            plot_unit = 'dSpacing'

        # get the original raw data
        ws_name = self._myController.project.vanadium_processing_manager.get_raw_vanadium()[bank_id]
        vec_x, vec_y = self.retrieve_loaded_reduced_data(
            data_key=ws_name, bank_id=1, unit=plot_unit)

        # plot
        self._raw_van_plot_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y),
                                                                                    unit=plot_unit,
                                                                                    over_plot=False,
                                                                                    run_id=run_id, bank_id=bank_id,
                                                                                    chop_tag=None,
                                                                                    line_color='black',
                                                                                    label='Raw vanadium {}'
                                                                                          ''.format(run_id))

        if is_smoothed_data:
            ws_name = self._myController.project.vanadium_processing_manager.get_smoothed_vanadium()[
                bank_id]
        else:
            ws_name = self._myController.project.vanadium_processing_manager.get_peak_striped_vanadium()[
                bank_id]
        vec_x, vec_y = self.retrieve_loaded_reduced_data(
            data_key=ws_name, bank_id=1, unit=plot_unit)
        # plot vanadium
        self._strip_van_plot_id = self.ui.graphicsView_mainPlot.plot_diffraction_data((vec_x, vec_y),
                                                                                      unit=plot_unit,
                                                                                      over_plot=True,
                                                                                      run_id=run_id, bank_id=bank_id,
                                                                                      chop_tag=None,
                                                                                      line_color='red',
                                                                                      label='Peak striped vanadium {}'
                                                                                            ''.format(run_id))

        return
    # END-CLASS


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
        raise RuntimeError(
            'QSetting cannot cast {0} with value {1} to a boolean.'.format(param_name, value_str))

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
    datatypeutility.check_int_variable('Default integer setting', default_value, (None, None))

    int_value_str = qsettings.value(param_name, default_value)
    if isinstance(int_value_str, QVariant):
        int_value = int_value_str.toInt()
    else:
        # case as Unicode
        print('[DB...BAT] QSetting {}: {} is of type {}'.format(
            param_name, int_value_str, type(int_value_str)))
        try:
            int_value = int(str(int_value_str))
        except (TypeError, ValueError):
            int_value = None

    # use default
    if int_value is None:
        int_value = default_value

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
    datatypeutility.check_float_variable('Default float setting', default_value, (None, None))

    float_value_str = qsettings.value(param_name, default_value)
    if isinstance(float_value_str, QVariant):
        float_value = float_value_str.toFloat()
    else:
        # case as Unicode
        print('[DB...BAT] QSetting {}: {} is of type {}'.format(
            param_name, float_value_str, type(float_value_str)))
        try:
            float_value = int(str(float_value_str))
        except (TypeError, ValueError):
            float_value = None

    # use default
    if float_value is None:
        float_value = default_value

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
