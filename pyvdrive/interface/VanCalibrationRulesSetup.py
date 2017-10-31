########################################################
# Beta Version: Set up automatic vanadium calibration run
#               location rules
########################################################
import os

from PyQt4 import QtGui, QtCore

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import DialogVanCalibRules as dlgrule


class SetupVanCalibRuleDialog(QtGui.QDialog):
    """ Pop up dialog window to add runs by IPTS
    """
    def __init__(self, parent):
        """ Init
        """
        QtGui.QDialog.__init__(self)

        # Parent
        self._myParent = parent
        self.quit = False

        # Set up widgets
        self.ui = dlgrule.Ui_Dialog()
        self.ui.setupUi(self)