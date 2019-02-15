from pyvdrive.lib import datatypeutility
from gui import GuiUtility
import os


# TODO - TONIGHT 4 - Code Quality for Class
class PeakPickerWindowChildVanadium(object):
    """
    """
    def __init__(self, parent, ui_class):
        """

        :param ui_class:
        """
        self._parent = parent
        self.ui = ui_class

        self._ipts_number = None
        self._run_number = None

        self._myController = parent._myController

        self._no_peak_van_line = None
        self._smoothed_van_line = None

        return

    def set_vanadium_info(self, ipts_number, van_run_number):
        self._ipts_number = ipts_number
        self._run_number = van_run_number

    def event_show_hide_v_peaks(self, show_v_peaks):
        """
        handling event that show or hide vanadium peaks on the figure
        :return:
        """
        datatypeutility.check_bool_variable('Flag to indicate show or hide vanadium peaks', show_v_peaks)

        # TODO - 20181110 - Implement!
        if True:
            GuiUtility.pop_dialog_error(self, 'Not Implemented Yet for Showing Vanadium Peaks')
            return

        if show_v_peaks:
            self.ui.graphicsView_mainPlot.add_indicators(vanadium_peaks)
        else:
            self.ui.graphicsView_mainPlot.hide_indicators()

        return

    def get_bank_id(self):
        if self.ui.radioButton_vpeakCurrentBank.isChecked():
            bank_id = GuiUtility.parse_integer(self.ui.comboBox_bankNumbers, False)
        else:
            bank_id = None   # all banks

        return bank_id

    def reset_processing(self):

        return

    def save_processing_result(self):

        return

    def init_session(self, data_key):
        print ('Current: data key/workspace = {}, Bank ID = {}'.format(data_key, 'No need to care'))

        temp_out_gda_name = os.path.join(os.getcwd(), '{}-s.gda'.format(self._run_number))

        log_ws_name = self._myController.load_nexus_file(self._ipts_number, self._run_number, None, True)

        self._myController.project.vanadium_processing_manager.init_session(workspace_name=data_key,
                                                                            ipts_number=self._ipts_number,
                                                                            van_run_number=self._run_number,
                                                                            out_gsas_name=temp_out_gda_name,
                                                                            sample_log_ws_name=log_ws_name)

        return

    def strip_vanadium_peaks(self, bank_id, peak_fwhm=4.,
                             tolerance=0.1, background_type = 'Quadratic', is_high_background = True):
        """

        :return:
        """
        bank_id = self.get_bank_id()
        print ('Current: data key/workspace = {}, Bank ID = {}'.format('Already set', bank_id))

        # peak_fwhm = 4
        # tolerance = 0.1
        # background_type = 'Quadratic'
        # is_high_background = True

        self._myController.project.vanadium_processing_manager.strip_v_peaks(bank_id, peak_fwhm,
                                                                           tolerance, background_type,
                                                                           is_high_background)

        self.plot_strip_peak_vanadium(bank_id)

        return

    def smooth_vanadium_peaks(self, bank_id, smoother_type, param_n, param_order):

        bank_id = self.get_bank_id()

        van_processor = self._myController.project.vanadium_processing_manager
        van_processor.smooth_v_spectrum(bank_id=bank_id, smoother_filter_type=smoother_type,
                                        param_n=param_n, param_order=param_order)

        self.plot_smoothed_peak_vanadium(bank_id)

        # self._myController.project.vanadium_processing_manager.smooth_spectra(bank_group_index, smoother_type,
        #                                                                       param_n, param_order,
        #                                                                       smooth_original=False)
        #
        # self.plot_1d_vanadium(run_id=self._vanadiumProcessDialog.get_run_id(),
        #                       bank_id=BANK_GROUP_DICT[bank_group_index][0], is_smoothed_data=True)

        return

    def plot_strip_peak_vanadium(self, bank_id):

        vec_x, vec_y = self._myController.project.vanadium_processing_manager.get_peak_striped_data(bank_id)

        if self._no_peak_van_line is not None:
            self.ui.graphicsView_main.remove_line(self._smoothed_van_line)
            self._no_peak_van_line = None

        self._no_peak_van_line = self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, color='red', marker='.')
        print ('[DB...BAT] Add No-Peak-Van Line: {}'.format(self._no_peak_van_line))


    def plot_smoothed_peak_vanadium(self, bank_id):

        vec_x, vec_y = self._myController.project.vanadium_processing_manager.get_peak_smoothed_data(bank_id)

        if self._smoothed_van_line is not None:
            self.ui.graphicsView_main.remove_line(self._smoothed_van_line)
            self._smoothed_van_line = None

        self._smoothed_van_line = self.ui.graphicsView_main.add_plot_1d(vec_x, vec_y, color='blue')
        print ('[DB...BAT] Add Smoothed-Van Line: {}'.format(self._smoothed_van_line))
