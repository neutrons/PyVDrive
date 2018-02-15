try:

    from PyQt5.QtWidgets import QMainWindow
except ImportError:
    from PyQt4.QtGui import QMainWindow
import gui.ui_GroupPeakDialog_ui


class GroupPeakDialog(QMainWindow):
    """
    Main window class to group peak with user interaction
    """
    def __init__(self, parent):
        """
        Initialization
        :param parent:
        """
        # check
        assert parent is not None, 'Parent (window) cannot be None!'
        # call base class init
        super(GroupPeakDialog, self).__init__(parent)
        # set up parent window
        self._parentWindow = parent

        # set up UI
        self.ui = gui.ui_GroupPeakDialog_ui.Ui_MainWindow()
        self.ui.setupUi(self)

        # init set up of widgets
        self.ui.radioButton_highIntensity.setChecked(True)
        self.ui.lineEdit_numberFWHM.setText('6')

        # line event handlers
        self.ui.pushButton_groupPeaks.clicked.connect(self.do_group_peaks)

        self.ui.pushButton_addPeakReturn.clicked.connect(self.do_add_peak_return)

        self.ui.pushButton_cancel.clicked.connect(self.do_cancel_return)

        # self.connect(self.ui.pushButton_groupPeaks, QtCore.SIGNAL('clicked()'),
        #              self.do_group_peaks)
        #
        # self.connect(self.ui.pushButton_addPeakReturn, QtCore.SIGNAL('clicked()'),
        #              self.do_add_peak_return)
        #
        # self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
        #              self.do_cancel_return)

        return

    def do_add_peak_return(self):
        """
        add grouped peaks and then close window
        :return:
        """
        self._parentWindow.add_grouped_peaks()

        self.close()

        return

    def do_cancel_return(self):
        """
        do not record the result of peak picking and close the window
        :return:
        """
        self._parentWindow.clear_group_highlight()

        self.close()

        return

    def do_group_peaks(self):
        """
        group selected peaks
        :return:
        """
        # get the resolution
        if self.ui.radioButton_highResolution.isChecked():
            resolution = 0.0025
        elif self.ui.radioButton_highIntensity.isChecked():
            resolution = 0.0045
        else:
            resolution = float(str(self.ui.lineEdit_userResolution))

        # get number of FWHM
        num_fwhm = int(str(self.ui.lineEdit_numberFWHM.text()))

        # group peak
        self._parentWindow.group_peaks(resolution, num_fwhm)

        return
