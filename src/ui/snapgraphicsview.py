from PyQt4 import QtGui
from mplgraphicsview import MplGraphicsView 

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

        self._graphicView = snapgraphicsview._graphicView
        self._comboBox1 = snapgraphicsview._comboBox1
        self._comboBox2 = snapgraphicsview._comboBox2

        return

    def set_current_log_name(self, log_index):
        """

        :param log_index:
        :return:
        """
        # TODO DOC
        assert isinstance(self._comboBox2, QtGui.QComboBox)

        self._comboBox2.setCurrentIndex(log_index)

        return

    def setLogNames(self, lognamelist):
        """

        :param lognamelist:
        :return:
        """
        self._comboBox1.clear()
        self._comboBox1.addItems(lognamelist)

        return

"""


    def __init__(self, graphicview, lognamecombobox, timecombobox):

        :return:

        SnapGraphicsView.__init__(self, graphicview, lognamecombobox, timecombobox)


"""