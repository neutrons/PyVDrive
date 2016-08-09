from PyQt4 import QtGui, QtCore
import mplgraphicsview


class LogGraphicsView(mplgraphicsview.MplGraphicsView):
    """
    Class ... extends ...
    for specific needs of the graphics view for interactive plotting of sample log,
    """
    def __init__(self, parent):
        """
        Purpose
        :return:
        """
        # Base class constructor
        mplgraphicsview.MplGraphicsView.__init__(self, parent)

        return


    # TODO/NOW/ISSUE-48: move all the methods related to this class