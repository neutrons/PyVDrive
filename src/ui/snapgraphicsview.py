import PyQt4
import PyQt4.QtGui

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
        if isinstance(graphicview, PyQt4.QtGui.QGraphicsView) is False:
            raise NotImplementedError("Input is not a QGraphicsView instance.")
        if isinstance(combox1, PyQt4.QtGui.QComboBox) is False:
            raise NotImplementedError("Input combo1 is not a QComboBox instance.")
        if isinstance(combox2, PyQt4.QtGui.QComboBox) is False:
            raise NotImplementedError('Input combo2 is not a QComboBox instance.')

        self._graphicView = graphicview
        self._comboBox1 = combox1
        self._comboBox2 = combox2

        return


class SampleLogView(SnapGraphicsView):
    """
    Snap graphics view for sample environment logs
    """
    def __init__(self, graphicview, lognamecombobox, timecombobox):
        """ Init
        :return:
        """
        SnapGraphicsView.__init__(self, graphicview, lognamecombobox, timecombobox)

    def __init__(self, snapgraphicsview):
        """
        :param snapgraphicsview:
        :return:
        """
        if isinstance(snapgraphicsview, SnapGraphicsView) is False:
            raise NotImplementedError('Input error!')

        self._graphicView = snapgraphicsview._graphicView
        self._comboBox1 = snapgraphicsview._comboBox1
        self._comboBox1 = snapgraphicsview._comboBox2

    def setLogNames(self, lognamelist):
        """

        :param lognamelist:
        :return:
        """
        self._comboBox1.clear()
        self._comboBox1.addItems(lognamelist)

        return

