########################################################################
#
# General-purposed plotting window
#
########################################################################

from mantidipythonwidget import MantidIPythonWidget
from PyQt4 import QtCore, QtGui

import GuiUtility as GuiUtility


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import ui_WorkspacesView


class WorkspaceViewer(QtGui.QWidget):
    """ Class for general-purposed plot window
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QtGui.QWidget.__init__(self)

        # Parent & others
        self._myParent = parent
        self._myController = None

        # set up UI
        self.ui = ui_WorkspacesView.Ui_Form()
        self.ui.setupUi(self)

        return

