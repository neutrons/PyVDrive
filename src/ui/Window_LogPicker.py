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

        # Defining widget handling methods
        self.connect(self.ui.pushButton_selectIPTS, QtCore.SIGNAL('clicked()'),
                     self.do_select_ipts)
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_quit_no_save)
        self.connect(self.ui.pushButton_saveReturn, QtCore.SIGNAL('clicked()'),
                     self.do_quit_with_save)
        self.connect(self.ui.pushButton_prevLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_prev_log)
        self.connect(self.ui.pushButton_nextLog, QtCore.SIGNAL('clicked()'),
                     self.do_load_next_log)
        self.connect(self.ui.pushButton_readLogFile, QtCore.SIGNAL('clicked()'),
                     self.do_read_log_file)

        self.connect(self.ui.radioButton_useGenericDAQ, QtCore.SIGNAL(''),
                     self.do_set_log_options)
        self.connect(self.ui.radioButton_useLoadFrame, QtCore.SIGNAL(''),
                     self.do_set_log_options)

        self.connect(self.ui.radioButton_useLogFile, QtCore.SIGNAL(''),
                     self.do_set_log_options)

        # Class variables
        self._currentLogIndex = 0
        self._logNameList = list()

        return

    def do_load_next_log(self):
        """ Load next log
        :return:
        """
        self._currentLogIndex += 1
        if self._currentLogIndex > len(self._logNameList):
            self._currentLogIndex = 0
        sample_log_name = self._logNameList[self._currentLogIndex]

        self._load_sample_log(sample_log_name)

        return

    def do_load_prev_log(self):
        """ Load previous log
        :return:
        """
        self._currentLogIndex -= 1
        if self._currentLogIndex < 0:
            self._currentLogIndex = len(self._logNameList) - 1
        sample_log_name = self._logNameList[self._currentLogIndex]

        self._load_sample_log(sample_log_name)

        return

    def do_quit_no_save(self):
        """
        Cancelled
        :return:
        """
        self.close()

        return

    def do_quit_with_save(self):
        """ Save selected segment and quit
        :return:
        """
        self.close()

        return

    def get_splitters(self):
        """ Get splitters set up by user.  Called by parent algorithm
        :return:
        """

    def setup(self):
        """ Set up from parent main window
        :return:
        """
        return

    def _load_sample_log(self, sample_log_name):
        """

        :param sample_log_name:
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
