########################################################################
#
# General-purposed plotting window
#
########################################################################
import sys
import os
import numpy

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import ui_LogSnapView


class DialogLogSnapView(QtGui.QDialog):
    """ Class for general-puposed plot window
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QtGui.QMainWindow.__init__(self)

        # parent
        self._myParent = parent

        # set up UI
        self.ui = ui_LogSnapView.Ui_Dialog()
        self.ui.setupUi(self)

        # Event handling
        self.connect(self.ui.pushButton_apply, QtCore.SIGNAL('clicked()'),
                     self.do_apply_change)

        self.connect(self.ui.pushButton_saveQuit, QtCore.SIGNAL('clicked()'),
                     self.do_save_quit)

        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_quit_no_save)

        return

    def do_apply_change(self):
        return

    def do_quit_no_save(self):
        """

        :return:
        """
        self.close()

        return

    def do_save_quit(self):
        return

    def setup(self, workflow_controller, sample_log_name):
        """ Set up from parent main window
        :return:
        """


def testmain(argv):
    """ Main method for testing purpose
    """
    parent = None

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = DialogLogSnapView(parent)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return

if __name__ == "__main__":
    testmain(sys.argv)
