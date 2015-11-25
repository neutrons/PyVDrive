########################################################################
#
# Window for set up log slicing splitters
#
########################################################################
import sys

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import GuiUtility
import gui.VdrivePeakPicker as VdrivePeakPicker


class PeakPickerWindow(QtGui.QMainWindow):
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
        self.ui = VdrivePeakPicker.Ui_MainWindow()
        self.ui.setupUi(self)

        # Define event handling methods
        """
        pushButton_addCurrentPeak
        pushButton_addAllPeaks
        pushButton_loadCalibFile
        pushButton_readData
        pushButton_return
        pushButton_save
        """

        raise NotImplementedError('Work on UI')

        # Set up widgets
        self._init_widgets_setup()

        return

    def _init_widgets_setup(self):
        """

        :return:
        """
        self.ui.treeView_iptsRun.set_main_window(self)

        return


def testmain(argv):
    """ Main method for testing purpose
    """
    parent = None

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = PeakPickerWindow(parent)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return

if __name__ == "__main__":
    testmain(sys.argv)
