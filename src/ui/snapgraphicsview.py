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
        return self._comboBox1.currentText()

    def combo_box2_value(self):
        """
        """
        return self._comboBox2.currentText()

    def is_selected(self):
        """
        """
        assert isinstance(self._radioButton, QtGui.QRadioButton)
        return self._radioButton.isChecked()


class SampleLogView(object):
    """
    Snap graphics view for sample environment logs
    """
    def __init__(self, snapgraphicsview):
        """
        :param snapgraphicsview:
        :return:
        """
        # Check
        if isinstance(snapgraphicsview, SnapGraphicsView) is True:
            self._snapGraphicsView = snapgraphicsview
        else:
            raise NotImplementedError('Input error!')

        return

    def get_log_name(self):
        """ Get current log name
        :return:
        """
        return str(self._snapGraphicsView.combo_box1_value())

    def plot_data(self, vec_times, vec_log_value, do_skip, num_sec_skipped):
        """

        :param vec_times:
        :param vec_log_value:
        :param do_skip:
        :param num_sec_skipped:
        :return:
        """
        if do_skip is True:
            vec_plot_times, vec_plot_value = \
                GuiUtility.skip_time(vec_times, vec_log_value, num_sec_skipped, 'second')
        else:
            vec_plot_times = vec_times
            vec_plot_value = vec_log_value

        self._snapGraphicsView.canvas().add_plot_1d(vec_plot_times, vec_plot_value)

        return

    def set_current_log_name(self, log_index):
        """
        Set current log's name
        :param log_index:
        :return:
        """
        self._snapGraphicsView.set_combo1_index(log_index)

        return

    def reset_log_names(self, lognamelist):
        """
        Set log names to combo box 1
        :param lognamelist:
        :return:
        """
        assert isinstance(lognamelist, list)
        self._snapGraphicsView.reset_combo1_items(lognamelist)

        return
