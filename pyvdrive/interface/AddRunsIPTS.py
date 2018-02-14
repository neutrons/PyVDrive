########################################################
# Beta Version: Add runs
########################################################
import os
import datetime

try:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QDialog, QFileDialog
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QDialog, QFileDialog

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.GuiUtility as gutil
import gui.ui_DialogAddRunsIPTS_ui as dlgrun


class AddRunsByIPTSDialog(QDialog):
    """ Pop up dialog window to add runs by IPTS
    """
    def __init__(self, parent):
        """
        Initialization
        :param parent: main GUI window for controller
        """
        QDialog.__init__(self)

        # Parent
        assert getattr(parent, 'get_controller', None) is not None, 'Parent method' \
                                                                    'has not method get_controller()'
        self._myParent = parent

        # other parameters
        self.quit = False

        # Set up widgets
        self.ui = dlgrun.Ui_Dialog()
        self.ui.setupUi(self)

        # Initialize widgets
        self._init_widgets()

        # Set event handler
        # group to add archive IPTS
        self.ui.radioButton_useNumber.toggled.connect(self.evt_change_data_access_mode)
        self.ui.radioButton_useDir.toggled.connect(self.evt_change_data_access_mode)
        self.ui.pushButton_browse.clicked.connect(self.do_browse_data_directory)
        self.ui.pushButton_addArchiveIPTS.clicked.connect(self.do_add_archive_ipts)

        # self.connect(self.ui.radioButton_useNumber, QtCore.SIGNAL('toggled(bool)'),
        #              self.evt_change_data_access_mode)
        # self.connect(self.ui.radioButton_useDir, QtCore.SIGNAL('toggled(bool)'),
        #              self.evt_change_data_access_mode)
        # QtCore.QObject.connect(self.ui.pushButton_browse, QtCore.SIGNAL('clicked()'),
        #                        self.do_browse_data_directory)
        # QtCore.QObject.connect(self.ui.pushButton_addArchiveIPTS, QtCore.SIGNAL('clicked()'),
        #                        self.do_add_archive_ipts)

        # group to add local HDD data
        self.ui.pushButton_addLocalHDDDir.clicked.connect(self.do_add_hdd_data)
        self.ui.pushButton_browseLogFile.clicked.connect(self.do_browse_record_file)

        # group to add runs
        self.ui.pushButton_AddRuns.clicked.connect(self.do_add_runs)
        self.ui.radioButton_filterByRun.toggled.connect(self.evt_change_filter_mode)
        self.ui.radioButton_filterByDate.toggled.connect(self.evt_change_filter_mode)

        # controllers
        self.ui.pushButton_return.clicked.connect(self.do_quit_app)

        # self.connect(self.ui.pushButton_addLocalHDDDir, QtCore.SIGNAL('clicked()'),
        #              self.do_add_hdd_data)
        # self.connect(self.ui.pushButton_browseLogFile, QtCore.SIGNAL('clicked()'),
        #              self.do_browse_record_file)
        #
        # # group to add runs
        # QtCore.QObject.connect(self.ui.pushButton_AddRuns, QtCore.SIGNAL('clicked()'),
        #                        self.do_add_runs)
        # self.connect(self.ui.radioButton_filterByRun, QtCore.SIGNAL('toggled(bool)'),
        #              self.evt_change_filter_mode)
        # self.connect(self.ui.radioButton_filterByDate, QtCore.SIGNAL('toggled(bool'),
        #              self.evt_change_filter_mode)
        #
        # # controllers
        # QtCore.QObject.connect(self.ui.pushButton_return, QtCore.SIGNAL('clicked()'),
        #                        self.do_quit_app)

        # Init setup for starting date and run
        self._beginDate = '01/01/2000'
        today = datetime.date.today()
        self._endDate = '%02d/%02d/%02d' % (today.month, today.day, today.year)

        self._beginRunNumber = 0
        self._endRunNumber = 999999999999

        # Data set
        self._iptsNumber = 0
        self._iptsDir = None
        self._iptsDirFromNumber = ''
        self._iptsDirFromDir = ''

        self._dataDir = None
        self._homeDir = os.path.expanduser('~')
        self._isArchiveAccessible = False

        # key to access IPTS from archive
        self._archiveKey = None

        self._skipScanData = False

        return

    def _init_widgets(self):
        """ Initialize the values of some widgets
        """
        # group box set up (SNS archive or local HDD)
        self.ui.radioButton_useNumber.setChecked(True)
        self.ui.groupBox_snsArchive.setEnabled(True)

        self.ui.groupBox_localHDD.setDisabled(True)

        # SNS archive options
        self.ui.radioButton_scanAutoRecord.setChecked(True)

        # local HDD options
        self.ui.radioButton_scanHD.setChecked(True)

        # add runs
        self.ui.radioButton_filterByRun.setChecked(True)

        return

    def _search_logs(self, auto_record_data):
        """
        Search log files such as AutoRecord.txt
        :param auto_record_data: flag to return AutoRecordData.txt
        :return: (bool, str): (1) True, auto record file path; (2) False, error message
        """
        # get shared folder
        shared_dir = '/SNS/VULCAN/IPTS-%d/shared/' % self._iptsNumber
        if not os.path.exists(shared_dir):
            return False, 'Directory {0} does not exist!'.format(shared_dir)

        # get file name
        log_path = None
        if auto_record_data:
            file_name = 'AutoRecordData.txt'
            log_path = os.path.join(shared_dir, file_name)
        # END-IF

        if log_path is None or os.path.exists(log_path) is False:
            # unable to locate AutoRecordData or AutoRecord is required
            file_name = 'AutoRecord.txt'
            log_path = os.path.join(shared_dir, file_name)
        # END-IF

        # last check
        if not os.path.exists(log_path):
            return False, 'Unable to locate record file {0}'.format(log_path)

        return True, log_path

    def add_runs_by_date(self):
        """
        Add runs by date of runs
        :return:
        """
        # add runs by date and time
        assert self.ui.dateEdit_begin.isEnabled() and self.ui.dateEdit_end.isEnabled()

        # get workflow controller
        workflow_controller = self._myParent.get_controller()

        # get start date
        begin_date = self.ui.dateEdit_begin.date()
        assert(isinstance(begin_date, QtCore.QDate))
        begin_date_str = '%02d/%02d/%02d' % (begin_date.month(), begin_date.day(), begin_date.year())

        # get end date
        end_date = self.ui.dateEdit_end.date()
        assert(isinstance(end_date, QtCore.QDate))
        end_date_str = '%02d/%02d/%02d' % (end_date.month(), end_date.day(), end_date.year())

        # get the complete list of run (tuples) as it is filtered by date
        status, ret_obj = workflow_controller.get_ipts_info(self._iptsDir, None, None)
        if status is True:
            run_tup_list = ret_obj
        else:
            error_message = ret_obj
            gutil.pop_dialog_error(self, error_message)
            return

        # filter by date
        status, ret_obj = general_util.filter_runs_by_date(run_tup_list, begin_date_str, end_date_str,
                                                           include_end_date=True)
        if status is True:
            run_tup_list = ret_obj
        else:
            #  pop error
            error_message = ret_obj
            gutil.pop_dialog_error(self, error_message)
            return
        # END-IF

        return run_tup_list

    def get_runs_by_number(self):
        """
        Call the method in parent class to add runs
        :return:
        """
        # get workflow
        workflow_controller = self._myParent.get_controller()

        # get start run and end run
        begin_run = gutil.parse_integer(self.ui.lineEdit_begin)
        end_run = gutil.parse_integer(self.ui.lineEdit_end)

        # two ways to add date by run numbers
        if self._skipScanData:
            # easy to add run numbers
            if begin_run is None:
                gutil.pop_dialog_error(self, 'In skip scanning mode, first run must be given!')
                return False
            # if end run is not given, just add 1 run
            if end_run is None:
                end_run = begin_run

            # get run information in quick mode
            assert isinstance(self._iptsNumber, int) and self._iptsNumber > 0, 'IPTS number must be verified ' \
                                                                               'for quick-filter-run mode.'
            run_info_dict_list = workflow_controller.scan_ipts_runs(self._iptsNumber, begin_run, end_run)

        else:
            # it is impossible to have an empty end run because the non-skip option always specifies one
            assert end_run is not None and begin_run is not None, 'Begin run and end run must be given ' \
                                                                  'in non-skip-scan case.'

            if self._iptsNumber >  0:
                # valid archiving system
                status, ret_obj = workflow_controller.get_archived_runs(self._archiveKey, begin_run,
                                                                        end_run)
            else:
                # add local data files
                status, ret_obj = workflow_controller.get_local_runs(self._archiveKey, self._iptsDir,
                                                                     begin_run, end_run, standard_sns_file=True)
            # get the complete list of run (tuples) as it is filtered by date
            if status is True:
                run_info_dict_list = ret_obj
            else:
                error_message = ret_obj
                gutil.pop_dialog_error(self, error_message)
                return False
        # END-IF-ELSE

        return run_info_dict_list

    def do_browse_data_directory(self):
        """ Browse data directory if it is set up to use IPTS directory other than number
        :return:
        """
        # get the data directory from text line or from default
        if str(self.ui.lineEdit_iptsDir.text()).strip() != '':
            # from IPTS Directory
            default_dir = str(self.ui.lineEdit_iptsDir.text()).strip()
        else:
            # from default
            default_dir = self._homeDir

        # user-specified data directory
        data_dir = str(QFileDialog.getExistingDirectory(self, 'Get Directory',
                                                              default_dir))
        self.ui.lineEdit_iptsDir.setText(data_dir)
        self._iptsDir = data_dir
        self._iptsDirFromDir = data_dir
        self._iptsNumber = None

        # Enable next step
        self.ui.groupBox_scanIptsInfo.setEnabled(True)

        return

    def do_browse_record_file(self):
        """
        Browse user record file and add the line edit for user specified VULCAN record file
        :return:
        """
        # open file
        if self._dataDir is not None:
            default_dir = self._dataDir
        elif self._iptsDir is not None:
            default_dir = self._iptsDir
        else:
            default_dir = os.getcwd()

        file_filter = 'Text Files (*.txt);;Data Files (*.dat);;All Files (*.*)'

        record_file_name = str(QFileDialog.getOpenFileName(self, 'VULCAN record file', default_dir,
                                                                 file_filter))
        if record_file_name is None or len(record_file_name) == 0:
            # user cancels operation
            pass
        else:
            # set
            self.ui.lineEdit_logFilePath.setText(record_file_name)

        return

    def do_add_hdd_data(self):
        """
        List runs including run numbers, creation time and full path file names
        of one IPTS directory
        :return:
        """
        # retrieve information about the selected ITPS in 3 approaches
        if self.ui.radioButton_noScan.isChecked():
            # no scan
            self._skipScanData = True

        elif self.ui.radioButton_scanLogFile.isChecked():
            # scan the log file
            self._skipScanData = False
            self.scan_record_file()

        else:
            # scan the HD
            self._skipScanData = False
            status = self.scan_archive()
            if not status:
                return

        # enable the group to add IPTS
        self.ui.groupBox_selectRuns.setEnabled(True)
        self.set_filter_mode(by_run_number=True)

        return

    def do_add_archive_ipts(self):
        """
        add from archive
        :return:
        """
        # Get IPTS number
        ipts_number = gutil.parse_integer(self.ui.lineEdit_iptsNumber)
        if ipts_number is None:
            gutil.pop_dialog_error(self, 'IPTS number must be given!')
            return
        self._iptsNumber = ipts_number

        # set IPTS number to parent
        self._myParent.set_ipts_number(self._iptsNumber)

        # Get and check IPTS directory
        if self._dataDir is None:
            gutil.pop_dialog_error(self, 'Data directory is not set up!')
            return

        # build IPTS directory and check existence of data
        ipts_dir_1 = os.path.join(self._dataDir, 'IPTS-%d/data/' % ipts_number)
        ipts_dir_2 = os.path.join(self._dataDir, 'IPTS-%d/nexus/' % ipts_number)
        if not os.path.exists(ipts_dir_1) and not os.path.exists(ipts_dir_2):
            gutil.pop_dialog_error(self, 'IPTS number %d cannot be found under %s or %s. ' % (
                ipts_number, ipts_dir_1, ipts_dir_2))
            self.ui.lineEdit_iptsNumber.setStyleSheet('color:red')
            return
        else:
            self.ui.lineEdit_iptsNumber.setStyleSheet('color:green')

        if os.path.exists(ipts_dir_1):
            self._iptsDir = ipts_dir_1
            self._iptsDirFromNumber = ipts_dir_1
        else:
            self._iptsDir = ipts_dir_2
            self._iptsDirFromNumber = ipts_dir_2

        # browse log files
        self.ui.comboBox_existingIPTS.addItem('{0}'.format(ipts_number))

        # scan files
        if self.ui.radioButton_scanAutoRecord.isChecked():
            record_data_only = self.ui.checkBox_autoRecordDataOnly.isChecked()
            self.scan_record_file(record_data_only, True)
        else:
            # scan the HD
            self.scan_archive()

        # signal parent TODO ASAP ASAP2 - (1) add IPTS to tree without runs  (2) set IPTS to parent
        # blabla

        return

    def do_add_runs(self):
        """
        Add runs to parent (but not quit)
        :return:
        """
        # Access parent's workflow controller
        workflow_controller = self._myParent.get_controller()
        assert workflow_controller is not None

        # Check whether it is fine to leave with 'OK'
        if self._iptsDir is None:
            # error message and return: data directory must be given!
            gutil.pop_dialog_error(self, 'IPTS or data directory has not been set up.'
                                   'Unable to add runs.')
            return

        # try to get the IPTS from IPTS directory
        if self._iptsNumber is None:
            # get the ipts number for IPTS directory
            status, ret_obj = workflow_controller.get_ipts_number_from_dir(self._iptsDir)
            if status is False:
                # use IPTS = 0 for no-IPTS
                message = 'Unable to get IPTS number due to %s. Using user directory.' % ret_obj
                gutil.pop_dialog_error(self, message)
                self._iptsNumber = 0
            else:
                # good IPTS
                self._iptsNumber = ret_obj
        # END-IF-ELSE

        # # set IPTS number of controller
        # workflow_controller.set_ipts(self._iptsNumber)

        # get the list of runs by run number of date
        if self.ui.radioButton_filterByDate.isChecked():
            # add runs by date
            run_tup_list = self.add_runs_by_date()
        elif self.ui.radioButton_filterByRun.isChecked():
            # add runs by run numbers
            run_tup_list = self.get_runs_by_number()
        else:
            # exception
            raise RuntimeError('Neither radio button to filter by date or run number is selected.')

        # return with error
        if run_tup_list is False:
            gutil.pop_dialog_error(self, 'Unable to get runs with information.')
            return

        # add runs to workflow
        status, error_message = workflow_controller.add_runs_to_project(run_tup_list)
        if status is False:
            return False, error_message

        status, err_msg = self._myParent.add_runs_trees(self._iptsNumber, self._iptsDir, run_tup_list)
        if not status:
            gutil.pop_dialog_error(self, error_message)

        return

    def do_quit_app(self):
        """ Quit and abort the operation
        """
        self.quit = True
        self.close()

        return

    def evt_change_filter_mode(self):
        """
        change the data filtering mode
        :return:
        """
        by_run = self.ui.radioButton_filterByRun.isChecked()

        self.set_filter_mode(by_run_number=by_run)

    def evt_change_data_access_mode(self):
        """
        Toggle between 2 approaches to get IPTS directory: from IPTS number of directory
        :return:
        """
        if self.ui.radioButton_useNumber.isChecked():
            self.ui.groupBox_snsArchive.setEnabled(True)

        elif self.ui.radioButton_useDir.isChecked():
            # TODO FIXME - Enable local HDD data access in future
            # self.ui.groupBox_localHDD.setEnabled(True)
            pass

        else:
            self.ui.groupBox_snsArchive.setEnabled(True)

        return

    def get_date_run_range(self):
        """
        Get range of date and run that user sets up
        :return: 4-tuple as start date, end date, start run and end run.
                 dates are of type string in format 'month/day/year'
        """
        # Get date and run range
        return self._beginDate, self._endDate, self._beginRunNumber, self._endRunNumber

    def get_ipts_dir(self):
        """
        Get directory for IPTS
        :return:
        """
        return self._iptsDir

    def get_ipts_number(self):
        """ Get IPTS number
        :return: integer (set up) or None (set up via directory)
        """
        if self._iptsNumber > 0:
            return self._iptsNumber

        return None

    def scan_archive(self):
        """
        Scan data archive
        :return:
        """
        # scan file
        status, ret_obj = self._myParent.get_controller().scan_ipts_archive(self._iptsDir)
        if not status:
            gutil.pop_dialog_error(self, 'Unable to get IPTS information due to %s.' % ret_obj)
            self.ui.label_loadingStatus.setText('Failed to access %s.' % self._iptsDir)
            return False
        else:
            ipts_key = ret_obj

        # get information
        start_run, end_run = self._myParent.get_controller().get_ipts_run_range(ipts_key)
        run_info_list = [start_run, end_run]

        # set information to GUI
        self.set_retrieved_information(run_info_list)

        self._archiveKey = ipts_key

        return True

    def scan_record_file(self, record_data_only, is_archive=True):
        """
        Scan record log file
        :param record_data_only: flag to read AutoRecordData
        :param is_archive: locate file in archive
        :return: boolean
        """
        if is_archive:
            # in archive
            status, ret_str = self._search_logs(record_data_only)
        else:
            # get log file: the higher priority is the log file name that is browsed
            log_file_path = str(self.ui.lineEdit_logFilePath.text())
            if len(log_file_path.strip()) == 0:
                status = False
                ret_str = 'User must specify path to "Auto Record" file.'
            elif os.path.exists(log_file_path):
                status = True
                ret_str = log_file_path
            else:
                status = False
                ret_str = 'User specified "Auto Record" file {0} does not exist.'.format(log_file_path)
        # END-IF-ELSE

        if status:
            # scan record file
            log_file_path = ret_str
            scan_status, ret_obj = self._myParent.get_controller().scan_vulcan_record(log_file_path)
            if scan_status:
                # set record key as current archive key and get the range of the run
                record_key = ret_obj
                self._archiveKey = record_key
                start_run, end_run = self._myParent.get_controller().get_ipts_run_range(record_key)
                run_info_list = [start_run, end_run]
                self.set_retrieved_information(run_info_list)
            else:
                # error in retrieving
                error_message = ret_obj
                gutil.pop_dialog_error(self, 'Unable to get IPTS information from log file %s due to %s.' % (
                    log_file_path, error_message))
                self.ui.label_loadingStatus.setText('Failed to access %s.' % log_file_path)
                return False

        else:
            error_message = ret_str
            gutil.pop_dialog_error(self, error_message)

        return True

    def set_retrieved_information(self, run_tup_list):
        """
        Assumption: sort by time and date should have the exactly same result
        :param run_tup_list: sorted run tuple list
        :return:
        """
        assert (isinstance(run_tup_list, list)) and len(run_tup_list) > 0

        if len(run_tup_list) == 1:
            gutil.pop_dialog_information(self, 'Only 1 run is given!')

        # set up run information
        first_run = run_tup_list[0][0]
        last_run = run_tup_list[-1][0]

        self.ui.lineEdit_begin.setText(str(first_run))
        self.ui.lineEdit_end.setText(str(last_run))

        # Sort by date
        first_run_time = run_tup_list[0][1]
        last_run_time = run_tup_list[-1][1]

        date_begin = gutil.convert_to_qdate(first_run_time)
        self.ui.dateEdit_begin.setDate(date_begin)

        date_end = gutil.convert_to_qdate(last_run_time)
        self.ui.dateEdit_end.setDate(date_end)

        self.ui.label_loadingStatus.setText('IPTS directory %s: Run %d - %d.'
                                            '' % (self._iptsDir, first_run, last_run))

        return

    def set_data_root_dir(self, root_dir):
        """
        Set root data dir
        :param root_dir:
        :return:
        """
        self._dataDir = root_dir

    def set_filter_mode(self, by_run_number):
        """
        Set filter mode by run number or by date
        :param by_run_number: otherwise, by date
        :return:
        """
        if by_run_number:
            # set to filter by run number
            self.ui.radioButton_filterByRun.setChecked(True)
            self.ui.radioButton_filterByDate.setChecked(False)
            self.ui.lineEdit_begin.setEnabled(True)
            self.ui.lineEdit_end.setEnabled(True)
            self.ui.dateEdit_begin.setEnabled(False)
            self.ui.dateEdit_end.setEnabled(False)
        else:
            # set to filter by date
            self.ui.radioButton_filterByRun.setChecked(False)
            self.ui.radioButton_filterByDate.setChecked(True)
            self.ui.lineEdit_begin.setEnabled(False)
            self.ui.lineEdit_end.setEnabled(False)
            self.ui.dateEdit_begin.setEnabled(True)
            self.ui.dateEdit_end.setEnabled(True)

        return

    def set_ipts_number(self, ipts_number):
        """
        Set starting IPTS number
        :param ipts_number:
        :return:
        """
        self.ui.lineEdit_iptsNumber.setText(str(ipts_number))

        return

