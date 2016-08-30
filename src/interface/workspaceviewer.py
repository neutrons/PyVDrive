########################################################################
#
# General-purposed plotting window
#
########################################################################
from PyQt4 import QtCore, QtGui

import gui.GuiUtility as GuiUtility


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import gui.ui_WorkspacesView


class WorkspacesView(QtGui.QMainWindow):
    """ Class for general-purposed plot window
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QtGui.QMainWindow.__init__(self)

        # Parent & others
        self._myParent = parent
        self._myController = None

        # set up UI
        self.ui = gui.ui_WorkspacesView.Ui_Form()
        self.ui.setupUi(self)

        return

