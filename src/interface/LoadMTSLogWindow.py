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

    mtsLogReturnSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent, ipts_number=None):
        """
        :param parent:
        :return:
        """
        # GUI window
        QtGui.QMainWindow.__init__(self)

        # check input
        assert ipts_number is None or (isinstance(ipts_number, int) and ipts_number > 0)

        # signal
        self.mtsLogReturnSignal.connect(parent.signal_scanned_mts_log)

        # set up parent
        self._myParent = parent

        # set up widgets from ui file
        self.ui = LoadUI.Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize values of widgets
        self._init_widgets()

        # set up event handling for widgets
        self.connect(self.ui.pushButton_browseLoadFile, QtCore.SIGNAL('clicked()'),
                     self.do_peek_log_file)
        self.connect(self.ui.pushButton_formatSet, QtCore.SIGNAL('clicked()'),
                     self.do_set_init_format)
        self.connect(self.ui.pushButton_setBlocks, QtCore.SIGNAL('clicked()'),
                     self.do_correct_blocks)
        self.connect(self.ui.pushButton_setExpTime, QtCore.SIGNAL('clicked()'),
                     self.do_set_exp_time)

        self.connect(self.ui.pushButton_checkTime, QtCore.SIGNAL('clicked()'),
                     self.do_check_time)

        self.connect(self.ui.pushButton_loadReturn, QtCore.SIGNAL('clicked()'),
                     self.do_accept_return)
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                     self.do_quit)

        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'),
                     self.do_quit)
        self.connect(self.ui.actionReset, QtCore.SIGNAL('triggered()'),
                     self.do_reset_gui)

        # class variables
        self._logFileName = None
        self._iptsNumber = ipts_number
        self._dataDir = None
        self._logFileSize = 0

        # format
        self._logFormatDict = dict()  # keys: block (dictionary of block index and start/stop line number)
        self._blockStartFlag = None
        self._unitList = None
        self._headerList = None
        self._comments = ''

        # summary
        self._summaryDict = None

        return

    def _init_widgets(self):
        """
        Initialize widgets' value
        :return:
        """

        # more set up
        self.ui.tableWidget_preview.setup()
        self.ui.radioButton_browseArchive.setChecked(True)

        # init widgets
        self.ui.lineEdit_numRowsInPreview.setText('20')

    def do_accept_return(self):
        """
        Return from the MTS peek-scan window
        :return:
        """
        # check
        if self._logFileName is None or self._summaryDict is None:
            GUtil.pop_dialog_error(self, 'MTS log file is not given AND/OR log file format is not scanned!')
            return

        # send signal
        self.mtsLogReturnSignal.emit(1)

        # close window
        self.close()

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

    def do_correct_blocks(self):
        """
        Correct the line set up of blocks from previously (maybe) wrong guess
        :return:
        """
        self.reset_log_format()

        return

    def do_peek_log_file(self):
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
                    GUtil.pop_dialog_error(self, 'IPTS number is not given! Unable to locate archive.')
                    return
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
        self.peek_log_file(self._logFileName)

        return

    def do_quit(self):
        """

        :return:
        """
        self.close()

        return

    def do_reset_gui(self):
        """
        Clear everything to reset the GUI
        :return:
        """
        # TODO/NOW/ISSUE-48: ASAP

        return

    def do_set_exp_time(self):
        """
        Set up experimental time
        :return:
        """
        import gui.dialogwidgets as cdw

        # app = QtGui.QApplication([])
        date, time, ok = cdw.DateDialog.getDateTime()
        print("{} {} {}".format(date, time, ok))
        # app.exec_()

        return

    def do_set_init_format(self):
        """ Set the MTS log's format and set to a dictionary
        0. set format
        1. enable 'return' button
        2. scan for summary including
          a) number of blocks
          b) size of each block
          c) ... ...
        :return:
        """
        # get the format dictionary from preview table
        status, ret_obj = self.ui.tableWidget_preview.retrieve_format_dict()

        # check
        assert status, str(ret_obj)

        # set to dictionary
        format_dict = ret_obj
        print '[DB...BAT] Format dictionary: ', format_dict

        # parse
        self.set_format(format_dict)

        # check
        if self._logFileName is None:
            GUtil.pop_dialog_error('MTS log file name has not been set.')
            return

        assert self._blockStartFlag is not None, 'Block start is not set up yet'

        # scan file
        self._summaryDict = self.scan_log_file(self._logFileName, self._blockStartFlag)

        # process scanned information
        block_key_list = sorted(self._summaryDict.keys())

        # form scan information
        sum_str = ''
        for block_key in block_key_list:
            sum_str += 'Block %d\n' % block_key
            for line_number, line in self._summaryDict[block_key]:
                sum_str += '\t%d: %s\n' % (line_number, line)
            # END-FOR
        # END-FOR

        # set to summary view
        self.ui.plainTextEdit_summaryView.setPlainText(sum_str)

        # clear the table and reset the summary dictionary to the table with proper check up the
        self.ui.tableWidget_preview.remove_all_rows()
        for block_key in block_key_list:
            start_line_number = int(block_key)
            for line_index, line in self._summaryDict[block_key]:
                row_number = line_index
                self.ui.tableWidget_preview.append_line(row_number=row_number, mts_line=line)
                table_row_number = self.ui.tableWidget_preview.rowCount()-1

                # define the function of the line, i.e., header, block start, unit or data
                if line.startswith(self._blockStartFlag):
                    # this is a block start
                    self.ui.tableWidget_preview.set_block_start(table_row_number, True)
                elif line.startswith(self._headerList[0]):
                    # this is a header
                    self.ui.tableWidget_preview.set_header_line(table_row_number, True)
                elif line.startswith(self._unitList[0]):
                    # this is a unit line
                    self.ui.tableWidget_preview.set_unit_line(table_row_number, True)
                else:
                    # this is a data line or empty line
                    self.ui.tableWidget_preview.set_data_line(table_row_number, True)
            # END-FOR (block)
        # END-FOR (block)

        # assume the previous setup is correct.  reset log format
        self.reset_log_format()

        return

    def reset_log_format(self):
        """
        Reset log information
        :return:
        """
        # dictionary to return
        self._logFormatDict.clear()
        self._logFormatDict['block'] = dict()  # block start information
        self._logFormatDict['header'] = dict() # header item list
        self._logFormatDict['unit'] = dict()   # unit item list
        self._logFormatDict['data'] = dict()   # data range (list with 2 items)
        self._logFormatDict['duration'] = dict()

        # check whether the log format has been set up
        row_number = self.ui.tableWidget_preview.rowCount()

        block_index = -1
        block_data_start_line = None
        block_data_stop_line = None
        for i_row in range(row_number):
            # read the line content anyway
            # UNIT LINE IS AN EXCEPTION ... TODO/FIXME
            if not self.ui.tableWidget_preview.is_unit(i_row):
                log_line = self.ui.tableWidget_preview.get_content(i_row)
                if len(log_line) == 0:
                    continue
            else:
                log_line = ''
            # END-IF-ELSE

            if self.ui.tableWidget_preview.is_block_start(i_row):
                # block header. set block index and start the new list
                block_index += 1
                self._logFormatDict['block'][block_index] = self.ui.tableWidget_preview.get_content(i_row)
                self._logFormatDict['data'][block_index] = None
                self._logFormatDict['duration'][block_index] = None

            elif self.ui.tableWidget_preview.is_header(i_row):
                # header line
                header_line = log_line
                # FIXME/TODO/ : use tab is a convention, but ... not a safe way to do so!
                self._logFormatDict['header'][block_index] = header_line.split('\t')

            elif self.ui.tableWidget_preview.is_unit(i_row):
                # unit line
                # FIXME - need to deal with unicode
                # unit_line = self.ui.tableWidget_preview.get_content(i_row)
                line_number = self.ui.tableWidget_preview.get_log_line_number(i_row)
                self._logFormatDict['unit'][block_index] = line_number

            elif self.ui.tableWidget_preview.is_data(i_row):
                # data line
                data = log_line
                time = float(data.split()[0])
                line_number = self.ui.tableWidget_preview.get_log_line_number(i_row)
                if self._logFormatDict['data'][block_index] is None:
                    # value is None, i.e., not initialized
                    self._logFormatDict['data'][block_index] = [line_number, -1]
                    self._logFormatDict['duration'][block_index] = [time, -1]
                else:
                    # update the ending block
                    self._logFormatDict['data'][block_index][1] = line_number
                    self._logFormatDict['duration'][block_index][1] = time
                # END-IF
            # END-IF-ELSE (row type)
        # END-FOR

        # debug output for debugging
        for field in self._logFormatDict:
            for block_index in self._logFormatDict[field]:
                print '%s: block %s : %s' % (str(field), str(block_index), str(self._logFormatDict[field][block_index]))
            print
        # FIXMe: DELETE THE SECTION

        return

    def get_log_file(self):
        """

        :return:
        """
        return self._logFileName

    def get_log_format(self):
        """
        Get the format of the log file and other information.
        This is a complete information dictionary forthe log file
        :return:
        """

        return self._logFormatDict

    def peek_log_file(self, file_name):
        """
        Scan log file for the blocks with 'Data Acquisition'
        :param file_name:
        :return:
        """
        # check
        assert isinstance(file_name, str) and os.path.exists(file_name), \
            'File name %s is either not a string (but a %s) or does not exist.' % (str(file_name),
                                                                                   str(type(file_name)))

        # get number of lines to peek
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

    def scan_log_file(self, log_file_name, block_start_flag):
        """ Scan whole log file and set up the log dictionary and a summary dictionary for viewing
        Example of log format dictionary:
          self._logFormatDict['block'] = {1: (10, 9990), 2: (10000, 20000), 3: (199999, 3000000)}
        Task list: scan for summary including
          a) number of blocks
          b) size of each block
          c) ... ...
        :return:
        """
        # check
        assert isinstance(log_file_name, str), 'Log file name must be a string.'
        assert isinstance(block_start_flag, str) and len(block_start_flag) > 0

        # create summary dictionaries
        sum_dict = dict()
        self._logFormatDict['block'] = dict()

        # set up summary parameters
        buffer_size = 6
        buffer_lines = list()

        # open file and search block starter
        block_key = None
        last_block_key = None
        num_lines_recorded = 0
        last_line_number = -1

        with open(log_file_name, 'r') as log_file:
            for line_number, line in enumerate(log_file):
                # parse the line
                line = line.strip()
                last_line_number = line_number

                # fill buffer
                buffer_lines.append((line_number, line))
                if len(buffer_lines) > buffer_size:
                    buffer_lines.pop(0)

                # check the line
                if block_key is not None:
                    # in a recording stage
                    num_lines_recorded += 1
                    # check quit condition
                    if num_lines_recorded == buffer_size:
                        # finished recording job
                        # record
                        sum_dict[block_key] = buffer_lines[:]
                        # reset block key
                        last_block_key = block_key
                        block_key = None
                        num_lines_recorded = 0

                elif line.startswith(block_start_flag):
                    # not in recording stage but it is a start of a block
                    block_key = line_number

                    num_lines_recorded = 1
                    if last_block_key is not None:
                        sum_dict[last_block_key].extend(buffer_lines[:-1])

                    # END-IF

                else:
                    # no operation
                    pass
                # END-IF-ELSE (line_number)
            # END-FOR
        # END-WITH

        # list lines
        if block_key is None:
            block_key = last_block_key
            if block_key is None:
                raise ValueError
        if block_key in sum_dict:
            sum_dict[block_key].extend(buffer_lines[:])
        else:
            sum_dict[block_key] = buffer_lines[:]

        # get format dictionary from summary dictionary
        block_key_list = sum_dict.keys()
        assert len(block_key_list) > 0, 'No block is found in the MTS log file %s.' % log_file_name
        for block_index, start_line_number in enumerate(block_key_list):
            self._logFormatDict['block'][block_index] = [start_line_number]
            if block_index > 0:
                self._logFormatDict['block'][block_index-1].append(start_line_number-1)
            # END-IF
        # END-FOR
        self._logFormatDict['block'][len(block_key_list)-1].append(last_line_number)

        self._logFileSize = last_line_number + 1

        return sum_dict

    def set_format(self, format_dict):
        """
        Set up the format and store the result to _blockStartFlag, _headerList, _unitList and _comment
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
