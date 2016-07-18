import os
from PyQt4 import QtGui, QtCore
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.ui_loadVulcanMTSLogFile as LoadUI
import gui.GuiUtility as GUtil

__author__ = 'wzz'


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
        self.connect(self.ui.pushButton_formatSet, QtCore.SIGNAL('clicked()'),
                     self.do_set_format)
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_quit)
        self.connect(self.ui.pushButton_loadReturn, QtCore.SIGNAL('clicked()'),
                     self.do_load_return)
        self.connect(self.ui.pushButton_scanInfo, QtCore.SIGNAL('clicked()'),
                     self.do_sum_info)

        # class variables
        self._logFileName = None
        self._formatDict = None

        return

    def do_scan_file(self):
        """ Set and scan MTS file
        :return:
        """
        # Pop dialog for log file
        # TODO/NOW - make selection of data source (work_dir)
        # radioButton_browseArchive, radioButton_browseLocal
        if True:
            working_dir = os.getcwd()
        else:
            working_dir = os.getcws()

        self._logFileName = str(QtGui.QFileDialog.getOpenFileName(self, 'Get Log File',
                                                                  working_dir))

        # scan file
        self.scan_log_file(self._logFileName)

        return

    def do_load_return(self):
        """

        :return:
        """
        # check
        if self._logFileName is None or self._formatDict is None:
            GUtil.pop_dialog_error(self, 'MTS log file is not given AND/OR log file format is not set!')
            return

        # close
        self.close()

        # check
        # TODO/NOW - send signal other than call!
        self._myParent.load_mts_log(self._logFileName, self._formatDict)

        return

    def do_set_format(self):
        """

        :return:
        """
        self._formatDict = self.ui.tableWidget_preview.retrieve_format_dict()

        return

    def do_quit(self):
        """

        :return:
        """
        self.close()

        return

    def do_sum_info(self):
        """
        Task list:
        1. enable 'return' button
        2. scan for summary including
          a) number of blocks
          b) size of each block
          c) ... ...
        :return:
        """
        raise NotImplementedError('ASAP TODO/NOW')

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

        # write the line to table
        for row_number, line in enumerate(lines):
            self.ui.tableWidget_preview.append_line(row_number, line.strip())

        return
