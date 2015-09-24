from PyQt4 import QtGui
from gui.mplgraphicsview import MplGraphicsView 
import GuiUtility


class SnapGraphicsView(object):
    """ Snap graphics view in VDrivePlot (beta)
    """
    def __init__(self, graphicview, combox1, combox2, radio_button):
        """
        :param graphicview:
        :param combox1:
        :param combox2:
        :return:
        """
        # Check
        if isinstance(graphicview, MplGraphicsView) is False:
            raise NotImplementedError("Input is not a QGraphicsView instance, but %s" % str(type(graphicview)))
        if isinstance(combox1, QtGui.QComboBox) is False:
            raise NotImplementedError("Input combo1 is not a QComboBox instance.")
        if isinstance(combox2, QtGui.QComboBox) is False:
            raise NotImplementedError('Input combo2 is not a QComboBox instance.')

        self._graphicView = graphicview
        self._comboBox1 = combox1
        self._comboBox2 = combox2
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
        assert isinstance(self._radioButton, QtGui.QRadioButton)
        return self._radioButton.isChecked()

    def plot_data(self, vec_times, vec_log_value):
        """

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

        self._graphicView.setXYLimits(min_x - 0.1*dx, max_x + 0.1*dx,
                                      min_y - 0.1*dy, max_y + 0.1*dy)

        # Plot
        self._graphicView.add_plot_1d(vec_times, vec_log_value, marker='.', color='blue')

        return

    def set_combo_index(self, combo_index, item_index):
        """
        """
        combo_box = getattr(self, '_comboBox%d' % combo_index)
        assert isinstance(combo_box, QtGui.QComboBox)

        combo_box.setCurrentIndex(item_index)

        return

    def reset_combo_items(self, combo_index, item_list):
        """
        """
        combo_box = getattr(self, '_comboBox%d' % combo_index)
        assert isinstance(combo_box, QtGui.QComboBox)

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

    def plot_sample_log(self, num_sec_skipped):
        """
        :param num_skip_second:
        :return:
        """
        # Get log name from
        log_name = self.get_log_name()
        print '[DB] Re-plot log value %s' % log_name

        vec_times, vec_log_value = self._myParent.get_sample_log_value(log_name)
        # FIXME / TODO - make relative time
        vec_times -= vec_times[0]

        do_skip = False
        num_sec_skipped = None

        """
        if do_skip is True:
            vec_plot_times, vec_plot_value = \
                GuiUtility.skip_time(vec_times, vec_log_value, num_sec_skipped, 'second')
        else:
        """

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
