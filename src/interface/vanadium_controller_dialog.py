# import PyQt modules
from PyQt4 import QtGui, QtCore

# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

import gui.GuiUtility as gutil
import gui.ui_ProcessVanadiumDialog as van_ui


class VanadiumProcessControlDialog(QtGui.QDialog):
    """ GUI (dialog) for process vanadium data
    """
    # Define signals
    # mySelectSignal = QtCore.pyqtSignal(str, list) # list of int
    # myCancelSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        """ Set up main window
        """
        # Init & set up GUI
        super(VanadiumProcessControlDialog, self).__init__(parent)

        # setup UI
        self.ui = van_ui.Ui_Dialog()
        self.ui.setupUi(self)

        return
