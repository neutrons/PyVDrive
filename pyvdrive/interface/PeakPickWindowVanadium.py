from pyvdrive.lib import datatypeutility
from gui import GuiUtility


class PeakPickerWindowChildVanadium(object):
    """

    """
    def __init__(self, parent, ui_class):
        """

        :param ui_class:
        """
        self._parent = parent
        self.ui = ui_class

        self._myController = parent._myController

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

    def smooth_vanadium_peaks(self):

        bank_id = self.get_bank_id()


    def strip_vanadium_peaks(self, data_key, bank_id):
        """

        :return:
        """
        bank_id = self.get_bank_id()

        print ('Current: data key/workspace = {}, Bank ID = {}'.format(data_key, bank_id))

        self._myController.project.vanadium_processing_manager.init_session2(workspace_name=data_key)

        peak_fwhm = 4
        tolerance = 0.1
        background_type = 'Quadratic'
        is_high_background = True

        self._myController.project.vanadium_processing_manager.strip_v_peaks(bank_id, peak_fwhm,
                                                                           tolerance, background_type,
                                                                           is_high_background)

        return

