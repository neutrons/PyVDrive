from pyvdrive.core import datatypeutility
from pyvdrive.interface.gui import GuiUtility
import os
import numpy


VANADIUM_PEAKS_D = [0.5044, 0.5191, 0.5350, 0.5526, 0.5936, 0.6178, 0.6453, 0.6768, 0.7134, 0.7566, 0.8089,
                    0.8737, 0.9571, 1.0701, 1.2356, 1.5133, 2.1401]
UNIT = {'d': 'dSpacing', 'tof': 'TOF'}


class PeakPickerWindowChildVanadium(object):
    """ Class to handle all the vanadium processing related issues in the peak processing window
    """

    def __init__(self, parent, ui_class):
        """ Init
        :param ui_class:
        """
        assert parent is not None, 'Parent class (Peak processing) cannot be None'
        assert ui_class is not None, 'UI class cannot be None'

        self._parent = parent

        # inherit from parent
        self._myController = parent._myController
        self.ui = ui_class

        # init widgets
        self.ui.checkBox_vpeakShowRaw.setChecked(True)

        self._ipts_number = None
        self._run_number = None

        # 4 lines that are allowed
        self._no_peak_van_line = None   # d-space
        self._smoothed_van_line = None  # TOF
        self._raw_van_dspace_line = None   # d-space
        self._raw_van_tof_line = None  # TOF

        # flag about V-PEAK indicators
        self._is_v_peaks_shown = False  # flag whether the vanadium peaks' positions are plotted
        self._curr_bank = 0
        self._curr_unit = UNIT['d']     # unit on the figure
        self._vpeak_indicators = None   # indicator IDs for vanadium

        # process UIs
        self.ui.checkBox_vpeakShowStripped.hide()
        self.ui.checkBox_vpeakShowSmoothed.hide()
        # self.ui.checkBox_vpeakShowRaw.hide()
        self.ui.pushButton_stripVPeaks.hide()
        self.ui.pushButton_smoothVPeaks.hide()
        self.ui.pushButton_resetVPeakProcessing.hide()

        # vanadium processing parameters history
        self._smooth_n_dict = dict()
        self._smooth_order_dict = dict()
        self._peak_fwhm_dict = dict()

        return

    def show_hide_raw_data(self, show_raw_vanadium):
        """
        Show or delete the raw vanadium data
        :param show_raw_vanadium:
        :return:
        """
        if self._curr_bank == 0:
            print('[DB...BAT] Nothing to plot/show')
            return

        print('[DB...BAT] show/hide: current bank = {}, current unit = {}'.format(self._curr_bank, self._curr_unit))

        if show_raw_vanadium:
            # show
            if self._curr_unit == UNIT['d']:
                self.plot_raw_dspace(self._curr_bank)
            else:
                self.plot_raw_tof(self._curr_bank)
        else:
            # hide
            if self._curr_unit == UNIT['d']:
                self._remove_raw_dspace_line()
            else:
                self._remove_raw_tof_line()

        return

    def show_hide_v_peaks(self, show_v_peaks):
        """ Handling event that show or hide vanadium peaks on the figure (the dashed indicators)
        :return:
        """
        datatypeutility.check_bool_variable(
            'Flag to indicate show or hide vanadium peaks', show_v_peaks)

        if show_v_peaks and self._is_v_peaks_shown is False:
            # show peaks
            if self._curr_unit != UNIT['d']:
                GuiUtility.pop_dialog_error(
                    self._parent, 'Vanadium peaks can only been shown when unit is dSpacing')
                self.ui.checkBox_vpeakShowPeakPos.setChecked(False)
                return
            else:
                # show!:
                self._vpeak_indicators = self.ui.graphicsView_main.add_vanadium_peaks(
                    VANADIUM_PEAKS_D)
                self._is_v_peaks_shown = True
        elif not show_v_peaks and self._is_v_peaks_shown:
            # hide/delete vanadium peaks
            self.ui.graphicsView_main.remove_vanadium_peaks(self._vpeak_indicators)
            self._vpeak_indicators = None
            self._is_v_peaks_shown = False

        return

    def set_vanadium_info(self, ipts_number, van_run_number):
        """
        Set the information about vanadium run
        :param ipts_number:
        :param van_run_number:
        :return:
        """
        datatypeutility.check_int_variable('IPTS number', ipts_number, (1, 99999))
        datatypeutility.check_int_variable('Vanadium run number', van_run_number, (1, 9999999))

        self._ipts_number = ipts_number
        self._run_number = van_run_number

        return

    def get_bank_id(self):
        """
        Get the current bank ID from UI
        :return: integer or None
        """
        if self.ui.radioButton_vpeakCurrentBank.isChecked():
            bank_id = GuiUtility.parse_integer(self.ui.comboBox_bankNumbers, False)
        else:
            bank_id = None   # all banks

        print('[DB...BAT] Current bank: {}'.format(bank_id))

        return bank_id

    def reset_processing(self):
        """
        Reset including all the indicators and etc...
        :return:
        """
        # hide indicators and raw
        self.ui.checkBox_vpeakShowRaw.setChecked(False)
        self.ui.checkBox_vpeakShowPeakPos.setChecked(False)

        self._ipts_number = None
        self._run_number = None

        # remove all the lines
        self._remove_raw_tof_line()
        self._remove_raw_dspace_line()
        self._remove_striped_peaks_line()
        self._remove_smoothed_line()

        # flag about V-PEAK indicators
        self._curr_bank = 0
        self._curr_unit = UNIT['d']     # unit on the figure

        return

    def save_processing_result(self):
        """
        Get saved file directory
        :return:
        """
        try:
            message = self._myController.project.vanadium_processing_manager.save_vanadium_to_file()
            GuiUtility.pop_dialog_information(self._parent, message)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self._parent, '{}'.format(run_err))

        return

    def init_session(self, data_key):
        """
        Init a vanadium processing session including
        (1) laod meta data
        :param data_key:
        :return:
        """
        print('[DB...BAT] Init vanadium session with data key (workspace) {}'.format(data_key))

        # generate a temporary gsas file name
        gsas_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'
        if not os.path.exists(gsas_dir) or not os.access(gsas_dir, os.W_OK):
            GuiUtility.pop_dialog_information(
                self._parent, 'User cannot write GSAS file to {}'.format(gsas_dir))
            gsas_dir = os.path.expanduser('~')
        temp_out_gda_name = os.path.join(gsas_dir, '{}-s.gda'.format(self._run_number))

        # load sample log workspace
        # TODO - TODAY 9 - Load meta data can take up to 3 seconds.  Make it on a separate thread
        log_ws_name = self._myController.load_meta_data(self._ipts_number, self._run_number, None)

        # call
        processor = self._myController.project.vanadium_processing_manager
        try:
            processor.init_session(workspace_name=data_key, ipts_number=self._ipts_number,
                                   van_run_number=self._run_number,
                                   out_gsas_name=temp_out_gda_name,
                                   sample_log_ws_name=log_ws_name)
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self._parent, 'Unable to initialize a vanadium processing sesson due to {}'
                                        ''.format(run_err))

        return

    def strip_vanadium_peaks(self, bank_id, peak_fwhm=4,
                             tolerance=0.1, background_type='Quadratic', is_high_background=True):
        """ Strip vanadium peaks of a certain bank
        :return:
        """
        if bank_id is None:
            bank_id = self.get_bank_id()

        try:
            processor = self._myController.project.vanadium_processing_manager
            processor.strip_v_peaks(bank_id, peak_fwhm, tolerance,
                                    background_type, is_high_background)
            self._peak_fwhm_dict[bank_id] = peak_fwhm
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self._parent, 'Unable to strip vanadium peaks on bank {} due to {}'
                                                      ''.format(bank_id, run_err))
            return

        # plot
        self.plot_strip_peak_vanadium(bank_id)

        return

    def smooth_vanadium_peaks(self, bank_id, smoother_type=None, param_n=None, param_order=None):
        """
        Smooth vanadium peaks
        :param bank_id:
        :param smoother_type:
        :param param_n:
        :param param_order:
        :return:
        """
        # get bank ID
        if bank_id is None:
            bank_id = self.get_bank_id()
            if bank_id is None:
                GuiUtility.pop_dialog_error(self._parent, 'Bank ID  is not given!')

        # set default number
        van_processor = self._myController.project.vanadium_processing_manager

        if smoother_type is None:
            smoother_type = 'Butterworth'
            param_n = van_processor.get_default_smooth_n(smoother_type, bank_id)
            param_order = van_processor.get_default_smooth_order(smoother_type, bank_id)

        # smooth!
        try:
            van_processor.smooth_v_spectrum(bank_id=bank_id, smoother_filter_type=smoother_type,
                                            param_n=param_n, param_order=param_order)
            self._smooth_n_dict[bank_id] = param_n
            self._smooth_order_dict[bank_id] = param_order
        except RuntimeError as run_err:
            GuiUtility.pop_dialog_error(self._parent, 'Unable to smooth vanadium for bank {} due to {}'
                                                      ''.format(bank_id, run_err))
            return

        self.plot_smoothed_peak_vanadium(bank_id, with_raw=self.ui.checkBox_vpeakShowRaw.isChecked(),
                                         label='{}: {}/{}'.format(smoother_type, param_n, param_order))

        return

    def plot_raw_dspace(self, bank_id):
        """
        Plot raw vanadium spectrum data in d-spacing
        :param bank_id:
        :return:
        """
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 100))

        # Note: there is no need to plot runs in the complicated logic as its parent class
        # remove previously plot line
        if self._raw_van_dspace_line:
            self.ui.graphicsView_main.remove_line(self._raw_van_dspace_line)
        # draw a new raw vanadium line in dSpacing
        vec_x, vec_y = self._myController.project.vanadium_processing_manager.get_raw_data(
            bank_id, UNIT['d'])
        self._raw_van_dspace_line = self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, color='black',
                                                                          label='Raw Vanadium Bank {}'.format(
                                                                              bank_id),
                                                                          x_label='dSpacing')
        # set unit and bank
        self._curr_unit = UNIT['d']
        self._curr_bank = bank_id
        self.ui.checkBox_vpeakShowRaw.setChecked(True)

        return vec_x, vec_y

    def plot_raw_tof(self, bank_id):
        """
        Plot raw vanadium spectrum data in d-spacing
        :param bank_id:
        :return:
        """
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 100))

        # Note: there is no need to plot runs in the complicated logic as its parent class
        # remove the previously plot line for vanadium TOF
        if self._raw_van_tof_line:
            self.ui.graphicsView_main.remove_line(self._raw_van_tof_line)

        # Set up class variables
        vec_x, vec_y = self._myController.project.vanadium_processing_manager.get_raw_data(
            bank_id, UNIT['tof'])
        self._raw_van_tof_line = self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, color='black',
                                                                       x_label='TOF',
                                                                       label='Raw Vanadium Bank {}'.format(bank_id))
        # set unit
        self._curr_unit = UNIT['tof']
        self._curr_bank = bank_id
        self.ui.checkBox_vpeakShowRaw.setChecked(True)

        return vec_x, vec_y

    def plot_strip_peak_vanadium(self, bank_id):
        """
        Plot the vanadium spectrum with peak striped
        :param bank_id:
        :return:
        """
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 100))

        # get vector X and Y
        vec_x, vec_y = self._myController.project.vanadium_processing_manager.get_peak_striped_data(
            bank_id)

        self._remove_smoothed_line()
        self._remove_striped_peaks_line()
        self._remove_raw_tof_line()

        # for resizing
        vec_x_list = [vec_x]
        vec_y_list = [vec_y]

        # original dspacing
        if self._raw_van_dspace_line is None:
            # plot original van
            raw_vec_x, raw_vec_y = self.plot_raw_dspace(bank_id)
            vec_x_list.append(raw_vec_x)
            vec_y_list.append(raw_vec_y)

        # plot v-line
        self._no_peak_van_line = self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, color='red',
                                                                       label='Bank {} Peak Striped'.format(
                                                                           bank_id),
                                                                       x_label='dSpacing')

        # reset X Y limit
        self._reset_figure_range(vec_x_list, vec_y_list)

        # set unit
        self._curr_unit = UNIT['d']
        self._curr_bank = bank_id

        return

    def plot_smoothed_peak_vanadium(self, bank_id, with_raw=True, label=''):
        """
        Plot vanadium spectrum after vanadium peak removed and smoothed
        :param bank_id:
        :return:
        """
        datatypeutility.check_int_variable('Bank ID', bank_id, (1, 100))

        # remove the previously plot smoothed vanadium line
        self._remove_smoothed_line()
        self._remove_striped_peaks_line()
        self._remove_raw_dspace_line()
        self.show_hide_v_peaks(show_v_peaks=False)  # hide vanadium peaks indicators

        # get vector X and Y
        vec_x, vec_y = self._myController.project.vanadium_processing_manager.get_peak_smoothed_data(
            bank_id)
        vec_x_list = [vec_x]
        vec_y_list = [vec_y]

        if with_raw:
            vec_raw_x, vec_raw_y = self.plot_raw_tof(bank_id)
            vec_x_list.append(vec_raw_x)
            vec_y_list.append(vec_raw_y)

        self._smoothed_van_line = self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, color='red', x_label='TOF',
                                                                        label='Bank {} {}'.format(bank_id, label))

        #
        # reset X Y limit
        self._reset_figure_range(vec_x_list, vec_y_list)

        # set unit
        self._curr_unit = UNIT['tof']
        self._curr_bank = bank_id

        return

    def _reset_figure_range(self, vec_x, vec_y):
        """
        reset figure range
        :param vec_x:
        :param vec_y:
        :return:
        """
        # X
        if isinstance(vec_x, numpy.ndarray):
            vec_x_list = [vec_x]
        else:
            vec_x_list = vec_x

        # set range
        min_x_list = sorted([array_x[0] for array_x in vec_x_list])
        max_x_list = sorted([array_x[-1] for array_x in vec_x_list])

        # Y
        if isinstance(vec_y, numpy.ndarray):
            vec_y_list = [vec_y]
        else:
            vec_y_list = vec_y

        # set range
        min_y_list = sorted([array_y.min() for array_y in vec_y_list])
        max_y_list = sorted([array_y.max() for array_y in vec_y_list])
        delta_y = max_y_list[-1] - min_y_list[0]
        lower_y = min_y_list[0] - delta_y * 0.01
        upper_y = max_y_list[-1] + delta_y * 0.001

        self.ui.graphicsView_main.setXYLimit(min_x_list[0], max_x_list[-1], lower_y, upper_y)
        if self._vpeak_indicators is not None:
            self.ui.graphicsView_main.adjust_indiators(self._vpeak_indicators, x_range=None,
                                                       y_range=(lower_y, upper_y))

        return

    def reset_image(self):
        """
        remove all the plots on the image
        :return:
        """
        self._remove_striped_peaks_line()
        self._remove_smoothed_line()
        self._remove_raw_tof_line()
        self._remove_raw_dspace_line()
        self.show_hide_v_peaks(False)
        self.ui.checkBox_vpeakShowRaw.setChecked(False)

        return

    def _remove_raw_dspace_line(self):
        """
        remove raw vanadium line in dSpacing
        :return:
        """
        if self._raw_van_dspace_line is not None:
            self.ui.graphicsView_main.remove_line(self._raw_van_dspace_line)
            self._raw_van_dspace_line = None

        return

    def _remove_raw_tof_line(self):
        """
        remove raw vanadium spectrum plotted in TOF
        :return:
        """
        if self._raw_van_tof_line:
            self.ui.graphicsView_main.remove_line(self._raw_van_tof_line)
            self._raw_van_tof_line = None

        return

    def _remove_smoothed_line(self):
        """
        remove the smoothed vanadium line
        :return:
        """
        if self._smoothed_van_line is not None:
            self.ui.graphicsView_main.remove_line(self._smoothed_van_line)
            self._smoothed_van_line = None

        return

    def _remove_striped_peaks_line(self):
        """
        remove the spectrum plot with peak removed
        :return:
        """
        if self._no_peak_van_line is not None:
            self.ui.graphicsView_main.remove_line(self._no_peak_van_line)
            self._no_peak_van_line = None

        return

    def save_vanadium_process_parameters(self):
        """ Save vanadium process parameters
        :return:
        """
        # TODO - TONIGHT 2 - Shall be moved to pyvdrive.core

        setting_dir = '/SNS/VULCAN/shared/Calibrationfiles/Instrument/Standard/Vanadium'
        if not os.path.exists(setting_dir) or not os.access(setting_dir, os.W_OK):
            GuiUtility.pop_dialog_information(
                self._parent, 'User cannot write file to {}'.format(setting_dir))
            setting_dir = os.path.expanduser('~')

        setting_name = os.path.join(setting_dir, 'vanadium_setting.txt')

        set_buffer = ''
        for bank_id in range(1, 4):
            try:
                set_buffer += '[BANK {}]\n'.format(bank_id)
                set_buffer += 'FWHM         = {}\n'.format(self._peak_fwhm_dict[bank_id])
                set_buffer += 'Smooth n     = {}\n'.format(self._smooth_n_dict[bank_id])
                set_buffer += 'Smooth order = {}\n'.format(self._smooth_order_dict[bank_id])
            except KeyError as key_err:
                GuiUtility.pop_dialog_error(
                    self._parent, 'Bank {} has not been processed: {}'.format(bank_id, key_err))
                return

        setting_file = open(setting_name, 'w')
        setting_file.write(set_buffer)
        setting_file.close()

        GuiUtility.pop_dialog_information(
            self._parent, 'Vanadium process setting is saved to {}'.format(setting_name))

        return

    def switch_bank(self, bank_id):
        """
        switch the bank
        :param bank_id:
        :return:
        """
        self.reset_image()

        try:
            # if smoothed then plot smoothed value
            self._myController.project.vanadium_processing_manager.get_peak_smoothed_data(bank_id)
            self.plot_smoothed_peak_vanadium(bank_id, True, 'Smoothed')
            # show raw
            self.ui.checkBox_vpeakShowRaw.setChecked(True)  # trigger events handling
            return
        except RuntimeError:
            pass

        try:
            # if peak striped
            self._myController.project.vanadium_processing_manager.get_peak_striped_data(bank_id)
            self.plot_strip_peak_vanadium(bank_id)
            # show raw
            self.ui.checkBox_vpeakShowRaw.setChecked(True)  # trigger events handling
            return
        except RuntimeError:
            pass

        # show raw
        self.ui.checkBox_vpeakShowRaw.setChecked(True)  # trigger events handling
        # just plot raw dSpacing
        vec_x, vec_y = self.plot_raw_dspace(bank_id)
        self._reset_figure_range([vec_x], [vec_y])

        return
