__author__ = 'wzz'

import os
from PyQt4 import QtGui, QtCore
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.ui_loadVulcanMTSLogFile as LoadUI


class LoadMTSLogFileWindow(QtGui.QMainWindow):
    """
    Pop-up dialog (window) to load an MTS log file with customized format and csv file alike.
    """
    def __init__(self, parent):
        """
        :param parent:
        :return:
        """
        QtGui.QMainWindow.__init__(self)

        # set up parent
        self._myParent = parent

        # set up widgets from ui file
        self.ui = LoadUI.Ui_MainWindow()
        self.ui.setupUi(self)

        # more set up
        self.ui.tableWidget_preview.setup()

        # set up event handling for widgets
        self.connect(self.ui.pushButton_browseLoadFile, QtCore.SIGNAL('clicked()'),
                     self.do_scan_file)

        return

    def do_scan_file(self):
        """ Set and scan MTS file
        :return:
        """
        # Pop dialog for log file
        working_dir = os.getcwd()
        log_file_name = str(QtGui.QFileDialog.getOpenFileName(self, 'Get Log File',
                                                              working_dir))

        # scan file
        self.scan_log_file(log_file_name)

        return

    def scan_log_file(self, file_name):
        """

        :param file_name:
        :return:
        """
        # TODO/NOW - Doc and check

        # FIXME/TODO/NOW - pass in
        num_lines = 10

        # open file
        mts_file = open(file_name, 'r')
        lines = list()
        for i_line in range(num_lines):
            lines.append(mts_file.readline())
        mts_file.close()

        for l in lines:
            print l.strip()

        # set up lines to table

        return
