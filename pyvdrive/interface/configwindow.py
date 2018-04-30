try:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QMainWindow
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QMainWindow

import gui.ui_ConfigWindow as ui_ConfigWindow

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class ConfigWindow(QMainWindow):
    """ Pop up dialog window to add runs by IPTS
    """
    def __init__(self, parent):
        """
        Initialization
        :param parent:
        """
        QMainWindow.__init__(self)

        self.ui = ui_ConfigWindow.Ui_MainWindow()
        self.ui.setupUi(self)

        # Define event handling
        self.connect(self.ui.pushButton_applyIPTS, QtCore.SIGNAL('clicked()'),
                     self.do_apply_ipts_config)
        self.connect(self.ui.pushButton_cancelQuit, QtCore.SIGNAL('clicked()'),
                     self.do_quit)

        # class variables
        self._myController = None

        # configuration information (global)
        self._rootDataDir = None
        self._workingDir = None
        self._dataAccessPatten = None
        self._relativeGSASDir = None

        # configuration for IPTS
        self._currentIPTS = None
        self._iptsDataDir = None
        self._iptsGSSDir = None

        return

    def set_controller(self, controller):
        """
        Set controller for
        :return:
        """
        assert controller is not None

        self._myController = controller

        return

    def do_apply(self):
        """ Apply all the set up to the controller
        :return:
        """
        # get the data
        self._rootDataDir = str(self.ui.lineEdit_iptsDataDir.text())
        self._workingDir = str(self.ui.lineEdit_workDir.text())
        self._relativeGSASDir = str(self.ui.lineEdit_relativeBinned.text())

        # ipts related
        self._currentIPTS = int(self.ui.lineEdit_IPTS.text())
        self._iptsDataDir = str(self.ui.lineEdit_iptsDataDir.text())
        self._iptsGSSDir = str(self.ui.lineEdit_iptsGssDir.text())

        # set to controller
        if self._myController is not None:
            self._myController.set_working_dir(self._workingDir)
            self._myController.set_root_data_dir(self._rootDataDir)
            self._myController.set_relative_binned_dir(self._relativeGSASDir)

            self._myController.set_ipts_config(self._currentIPTS, self._iptsDataDir, self._iptsGSSDir)
        # END-IF

        return

    def do_apply_ipts_config(self):
        """ Apply IPTS configuration
        :return:
        """
        # TODO - check and make more rigorous

        #
        ipts_number = int(self.ui.lineEdit_IPTS.text())
        ipts_bin_dir = str(self.ui.lineEdit_iptsGssDir.text())

        self._myController.set_ipts_config(ipts_number, '', ipts_bin_dir)

        return

    def do_quit(self):
        """
        Quit
        :return:
        """
        self.close()
