########################################################################
#
# General-purposed plotting window
#
# pushButton_selectIPTS
# radioButton_useLoadFrame
# radioButton_useGenericDAQ
# radioButton_useLogFile
# pushButton_readLogFile
# pushButton_prevLog
# pushButton_nextLog
# pushButton_saveReturn
# pushButton_cancel

# comboBox_logNames
# graphicsView_main
# tableWidget_segments
# treeView_iptsRun
#
########################################################################
import sys

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import VdriveLogPicker


class WindowLogPicker(QtGui.QMainWindow):
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
        self.ui = VdriveLogPicker.Ui_MainWindow()
        self.ui.setupUi(self)

        return

    def setup(self):
        """ Set up from parent main window
        :return:
        """


def testmain(argv):
    """ Main method for testing purpose
    """
    parent = None

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = WindowLogPicker(parent)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)

    return

if __name__ == "__main__":
    testmain(sys.argv)
