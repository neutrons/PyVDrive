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

        # init widgets
        self.ui.lineEdit_numRowsInPreview.setText('20')

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
        self._iptsNumber = ipts_number
        self._dataDir = None

        # format
        self._blockStartFlag = None
        self._unitList = None
        self._headerList = None
        self._comments = ''

        # summary
        self._blockLineDict = dict()

        return

    def do_scan_file(self):
        """ Set and scan MTS file
        :return:
        """
        # get default value
        if self.ui.radioButton_browseArchive.isChecked():
            # default from archive
            if self._iptsNumber is None:
                ipts_number_str = str(self.ui.lineEdit_ipts.text()).strip()
                if len(ipts_number_str) > 0:
                    ipts_number = int(ipts_number_str)
            else:
                ipts_number = self._iptsNumber

            if isinstance(ipts_number, int):
                working_dir = '/SNS/VULCAN/IPTS-%d/shared/' % ipts_number
            else:
                working_dir = '/SNS/VULCAN/'
        elif self.ui.radioButton_browseLocal.isChecked():
            if self._dataDir is None:
                working_dir = os.getcwd()
            else:
                working_dir = self._dataDir
        else:
            raise RuntimeError('Programming error for neither radio buttons is selected.')

        # get file name
        log_file_name = str(QtGui.QFileDialog.getOpenFileName(self, 'Get Log File', working_dir))
        if log_file_name is None or len(log_file_name) == 0:
            return
        else:
            self._logFileName = log_file_name
            self.ui.lineEdit_mtsFileName.setText(self._logFileName)

        # scan file
        self.scan_log_file(self._logFileName)

        return

    def do_check_time(self):
        """ Check the time in the log to be compatible to the run number related
        :return:
        """
        # get run number
        run_number_str = str(self.ui.lineEdit_runNumber.text()).strip()
        if not run_number_str.isdigit():
            GUtil.pop_dialog_error(self, 'Run number is not set up right.')
            return
        else:
            run_number = int(run_number_str)

        # get the run number
        


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
        status, ret_obj = self.ui.tableWidget_preview.retrieve_format_dict()

        # check
        assert status, str(ret_obj)

        # set to dictionary
        format_dict = ret_obj
        print '[DB...BAT] Format dictionary: ', format_dict

        # parse
        self.set_format(format_dict)

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

        assert self._blockStartFlag is not None, 'Block start is not set up yet'

        # set up summary parameters
        num_line_to_record = 4

        # open file and search block starter
        block_key = None
        num_lines_recorded = 0
        block_line_list = None
        with open(self._logFileName, 'r') as log_file:
            for line_number, line in enumerate(log_file):
                line = line.strip()

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
                    block_line_list = [line.strip]
                    self._blockLineDict[line_number] = block_line_list
                    block_key = line_number
                    num_lines_recorded += 1
                # END-IF
            # END-FOR
        # END-WITH

        # prepare the summary
        sum_str = ''
        # sum_str += 'comments: \n'
        sum_str += '    %s\n\n' % self._comments
        for block_index, block_start_line_number in enumerate(self._blockLineDict.keys()):
            sum_str += 'block %d\n' % block_index
            for index, line in enumerate(self._blockLineDict[block_start_line_number]):
                sum_str += '%-10d: %s\n' % (index+block_start_line_number,
                                            line.strip())
            sum_str += '\n'
            # END-FOR

        # set to summary view
        self.ui.plainTextEdit_summaryView.setPlainText(sum_str)

        return

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
        num_lines = int(self.ui.lineEdit_numRowsInPreview.text())
        assert 0 < num_lines < 10000, 'Number of lines to preview cannot be 0 or too large!'

        # open file
        mts_file = open(file_name, 'r')
        lines = list()
        for i_line in range(num_lines):
            lines.append(mts_file.readline())
            print lines[-1]
        mts_file.close()

        # write the line to table
        for row_number, line in enumerate(lines):
            self.ui.tableWidget_preview.append_line(row_number, line.strip())

        return

    def set_format(self, format_dict):
        """
        Set up all the format
        :param format_dict:
        :return:
        """
        # check
        assert isinstance(format_dict, dict)

        # get the line information
        block_start_line_num = format_dict['blockstart']
        header_line_num = format_dict['header']
        unit_line_num = format_dict['unit']
        comment_lines = format_dict['comment']

        # open file
        log_file = open(self._logFileName, 'r')
        for line_index in range(100):
            line = log_file.readline().strip()

            if line_index == block_start_line_num:
                # block start
                self._blockStartFlag = line.split()[0]
            elif line_index == header_line_num:
                # header
                self._headerList = line.split()
            elif line_index == unit_line_num:
                # unit
                self._unitList = line.split()
            elif line_index in comment_lines:
                # comment lines
                self._comments += '%s\n' % line
        # END-FOR

        log_file.close()

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
