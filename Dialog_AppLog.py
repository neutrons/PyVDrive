####
# (Dialog) window for logs
####

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import ui.ui_AppLog

class MyAppLogDialog(QWidget):
    """
    """
    # Main
    def __init__(self, parent):
        """ Init
        """
        # Call base
        QWidget.__init__(self)

        # Parent
        self._myParent = parent

        # Set up widget
        self.ui = ui.ui_AppLog.Ui_Dialog()
        self.ui.setupUi(self)

        # Set up initial text
        self._myContent = "Welcome!\n\nHi, Dude!\n\n"
        self.ui.textBrowser_Log.setText(self._myContent)

    @QtCore.pyqtSlot(int)
    def setText(self, val):
        """
        """
        text = "Signal to add text:  Value = " + str(val) + "."

        self._myContent += text + "\n\n"

        # text = self._myParent.getLogText()
        self.ui.textBrowser_Log.setText(self._myContent)

        return


    def accept(self):
        """
        """
        self.close()


    def reject(self):
        """
        """
        self.close()

