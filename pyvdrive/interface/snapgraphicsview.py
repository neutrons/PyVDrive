import numpy as np
try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5.QtWidgets import QComboBox, QRadioButton
except ImportError:
    from PyQt4.QtGui import QComboBox, QRadioButton
from pyvdrive.interface.gui.mplgraphicsview import MplGraphicsView


class SnapGraphicsView(object):
    """ Snap graphics view in VDrivePlot (beta)
    """

    def __init__(self, graphic_view_widget, combo_box1, combo_box2, radio_button):
        """
        :param graphic_view_widget:
        :param combo_box1:
        :param combo_box2:
        :return:
        """
        # Check
        if isinstance(graphic_view_widget, MplGraphicsView) is False:
            raise NotImplementedError(
                "Input is not a QGraphicsView instance, but %s" % str(type(graphic_view_widget)))
        if isinstance(combo_box1, QComboBox) is False:
            raise NotImplementedError("Input combo1 is not a QComboBox instance.")
        if isinstance(combo_box2, QComboBox) is False:
            raise NotImplementedError('Input combo2 is not a QComboBox instance.')

        self._graphicView = graphic_view_widget
        self._comboBox1 = combo_box1
        self._comboBox2 = combo_box2
        self._radioButton = radio_button

        return

    def canvas(self):
        """
        """
        return self._graphicView

    def combo_box1_value(self):
        """
        """
        return str(self._comboBox1.currentText())

    def combo_box2_value(self):
        """
        """
        return str(self._comboBox2.currentText())

    def is_selected(self):
        """
        """
        assert isinstance(self._radioButton, QRadioButton)
        return self._radioButton.isChecked()

    def plot_data(self, vec_times, vec_log_value):
        """
        Plot data
        :param vec_times:
        :param vec_log_value:
        :param do_skip:
        :param num_sec_skipped:
        :return:
        """
        # Clear
        self._graphicView.clear_all_lines()

        # X and Y's limits
        min_x = vec_times[0]
        max_x = vec_times[-1]
        if len(vec_times) == 1:
            dx = 1.0
        else:
            dx = max_x - min_x

        min_y = min(vec_log_value)
        max_y = max(vec_log_value)
        if len(vec_log_value) <= 2 and abs(max_y - min_y) < 1.E-10:
            dy = 1.
        else:
            dy = max_y - min_y

        self._graphicView.setXYLimit(min_x - 0.1*dx, max_x + 0.1*dx,
                                     min_y - 0.1*dy, max_y + 0.1*dy)

        # Plot
        self._graphicView.add_plot_1d(vec_times, vec_log_value, marker='.', color='blue')

        return

    def set_combo_index(self, combo_index, item_index):
        """
        """
        combo_box = getattr(self, '_comboBox%d' % combo_index)
        assert isinstance(combo_box, QComboBox)

        combo_box.setCurrentIndex(item_index)

        return

    def reset_combo_items(self, combo_index, item_list):
        """
        """
        combo_box = getattr(self, '_comboBox%d' % combo_index)
        assert isinstance(combo_box, QComboBox)

        combo_box.clear()
        combo_box.addItems(item_list)

        return


class SampleLogView(object):
    """
    Snap graphics view for sample environment logs
    """

    def __init__(self, snapgraphicsview, parent):
        """
        :param snapgraphicsview:
        :return:
        """
        # Check
        if isinstance(snapgraphicsview, SnapGraphicsView) is True:
            self._snapGraphicsView = snapgraphicsview
        else:
            raise NotImplementedError('Input error!')

        self._myParent = parent

        return

    def get_log_name(self):
        """ Get current log name
        :return:
        """
        log_name = str(self._snapGraphicsView.combo_box1_value())

        log_name = log_name.split(' (')[0]

        return log_name

    def plot_sample_log(self, max_resolution):
        """
        :param max_resolution:
        :return:
        """
        # check
        assert isinstance(max_resolution, int) and max_resolution > 0

        # Get log name from
        log_name = self.get_log_name()

        vec_times, vec_log_value = self._myParent.get_sample_log_value(run_number=None,
                                                                       log_name=log_name,
                                                                       time_range=None,
                                                                       relative=True)

        if len(vec_times) > max_resolution:
            skip = len(vec_times)/max_resolution
            if skip > 1:
                vec_times = vec_times[::skip]
                vec_log_value = vec_log_value[::skip]

        assert isinstance(vec_times, np.ndarray)
        assert isinstance(vec_log_value, np.ndarray)

        self._snapGraphicsView.plot_data(vec_times, vec_log_value)

        return

    def set_current_log_name(self, log_index):
        """
        Set current log's name
        :param log_index:
        :return:
        """
        self._snapGraphicsView.set_combo_index(1, log_index)

        return

    def reset_log_names(self, lognamelist):
        """
        Set log names to combo box 1
        :param lognamelist:
        :return:
        """
        assert isinstance(lognamelist, list)
        self._snapGraphicsView.reset_combo_items(1, lognamelist)

        return
