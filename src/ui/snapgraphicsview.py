from PyQt4 import QtGui
from gui.mplgraphicsview import MplGraphicsView 
import GuiUtility

class SnapGraphicsView(object):
    """ Snap graphics view in VDrivePlot (beta)
    """
    def __init__(self, graphicview, combox1, combox2):
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

        return


class SampleLogView(SnapGraphicsView):
    """
    Snap graphics view for sample environment logs
    """
    def __init__(self, snapgraphicsview):
        """
        :param snapgraphicsview:
        :return:
        """
         # Check
        if isinstance(snapgraphicsview, SnapGraphicsView) is False:
            raise NotImplementedError('Input error!')

        SnapGraphicsView.__init__(self, snapgraphicsview._graphicView,
                                  snapgraphicsview._comboBox1,
                                  snapgraphicsview._comboBox1)

        #self._graphicView = snapgraphicsview._graphicView
        #self._comboBox1 = snapgraphicsview._comboBox1
        #self._comboBox2 = snapgraphicsview._comboBox2

        return

    def get_log_name(self):
        """ Get current log name
        :return:
        """
        assert isinstance(self._comboBox1, QtGui.QComboBox)
        return str(self._comboBox1.currentText())

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

        assert isinstance(self._graphicView, MplGraphicsView)

        self._graphicView.add_plot_1d(vec_plot_times, vec_plot_value)

        return

    def set_current_log_name(self, log_index):
        """
        Set current log's name
        :param log_index:
        :return:
        """
        assert isinstance(self._comboBox2, QtGui.QComboBox)

        self._comboBox2.setCurrentIndex(log_index)

        return

    def set_log_names(self, lognamelist):
        """
        Set log names to combo box 1
        :param lognamelist:
        :return:
        """
        self._comboBox1.clear()
        self._comboBox1.addItems(lognamelist)

        return
