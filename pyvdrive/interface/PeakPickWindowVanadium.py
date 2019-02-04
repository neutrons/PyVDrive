from pyvdrive.lib import datatypeutility
import gui.GuiUtility


class PeakPickerWindowChildVanadium(object):
    """

    """
    def __init__(self, parent, ui_class):
        """

        :param ui_class:
        """
        self._parent = parent
        self.ui = ui_class

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
