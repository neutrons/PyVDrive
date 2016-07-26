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
    def __init__(self, parent, ipts_number=None):
        """
        :param parent:
        :return:
        """
        # check input
        assert ipts_number is None or (isinstance(ipts_number, int) and ipts_number > 0)

        QtGui.QMainWindow.__init__(self)

        # set up parent
        self._myParent = parent

        # set up widgets from ui file
        self.ui = LoadUI.Ui_MainWindow()
        self.ui.setupUi(self)

        # more set up
        self.ui.tableWidget_preview.setup()
        self.ui.radioButton_browseArchive.setChecked(True)

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
        self.connect(self.ui.pushButton_checkTime, QtCore.SIGNAL('clicked()'),
                     self.do_check_time)

        # class variables
        self._logFileName = None
        self._formatDict = None
        self._iptsNumber = ipts_number

        return

    def do_scan_file(self):
        """ Set and scan MTS file
        :return:
        """
        # get default value
        if self.ui.radioButton_browseArchive.isChecked():
            working_dir = '/SNS/VULCAN/IPTS-%d/shared/' % self._iptsNumber
        elif self.ui.radioButton_browseLocal.isChecked():
            working_dir = os.getcwd()
        else:
            raise RuntimeError('Programming error for neither radio buttons is selected.')

        self._logFileName = str(QtGui.QFileDialog.getOpenFileName(self, 'Get Log File',
                                                                  working_dir))

        # scan file
        self.scan_log_file(self._logFileName)

        return

    def do_check_time(self):
        """ Check the time in the log to be compatible to the run number related
        :return:
        """
        # check whether the scan has been done for the time
        blabla

        # get the run start and run stop time of the
        run_start_time = blabla
        run_stop_time = blabla

        # get the start and stop time


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
        # check
        if self._logFileName is None:
            GUtil.pop_dialog_error('MTS log file name has not been set.')
            return

        assert self._blockStartFlag is not None, 'Block start flag is not set up yet.'
        assert self._sizeBlockHeaders > 0, 'Block header size is not defined.'

        # set up summary parameters
        block_lines_dict = dict()
        num_line_to_record = 4

        # open file and search block starter
        block_key = None
        num_lines_recorded = 0
        block_line_list = None
        with open(self._logFileName, 'r') as log_file:
            for line_number, line in enumerate(log_file):
                if block_key is not None:
                    # in a recording stage
                    block_line_list.append(line)
                    num_lines_recorded += 1
                    # check quit condition
                    if num_lines_recorded == num_line_to_record:
                        block_key = None
                        num_lines_recorded = 0

                elif self._blockStartFlag in line:
                    # not in recording stage but it is a start of a block
                    block_line_list = list()
                    block_lines_dict[line_number] = block_line_list
                    block_key = line_number
                    num_lines_recorded += 1
                # END-IF
            # END-FOR
        # END-WITH

        # prepare the summary
        sum_str = ''
        # sum_str += 'comments: \n'
        # for i_line in self._formatDict['comment']:
        #    sum_str += '%-4d  %s\n' % (i_line, lines[i_line])
        for block_index, block_start_line_number in enumerate(block_lines_dict.keys()):
            sum_str += 'block %d\n' % block_index
            for index, line in enumerate(block_lines_dict[block_start_line_number]):
                sum_str += '%-4d  %s\n' % (index+block_start_line_number,
                                           line)
            # END-FOR

        GUtil.pop_dialog_information(sum_str)

        return block_lines_dict.keys()

    def scan_log_file(self, file_name):
        """
        Scan log file for the blocks with 'Data Acquisition'
        :param file_name:
        :return:
        """
        # check
        assert isinstance(file_name, str) and os.path.exists(file_name), \
            'File name %s is either not a string (but a %s) or does not exist.' % (str(file_name),
                                                                                   str(type(file_name)))

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

    def set_ipts_number(self, ipts_number):
        """
        Set IPTS number
        :param ipts_number:
        :return:
        """
        # check
        assert isinstance(ipts_number, int) and ipts_number > 0

        self._iptsNumber = ipts_number

        return