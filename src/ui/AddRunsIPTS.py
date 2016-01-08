########################################################
# Beta Version: Add runs
########################################################
import os
import datetime
import time

from PyQt4 import QtGui, QtCore
import GuiUtility as gutil

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

import gui.ui_DialogAddRunsIPTS as dlgrun


class AddRunsByIPTSDialog(QtGui.QDialog):
    """ Pop up dialog window to add runs by IPTS
    """
    def __init__(self, parent):
        """ Init
        """
        QtGui.QDialog.__init__(self)

        # Parent
        self._myParent = parent
        self.quit = False

        # Set up widgets
        self.ui = dlgrun.Ui_Dialog()
        self.ui.setupUi(self)

        # Init set up
        self.ui.radioButton_useNumber.setChecked(True)
        self.ui.lineEdit_iptsDir.setDisabled(True)
        self.ui.pushButton_browse.setDisabled(True)

        # Set event handler
        self.connect(self.ui.radioButton_useNumber, QtCore.SIGNAL('toggled(bool)'),
                     self.do_change_data_access_mode)
        self.connect(self.ui.radioButton_useDir, QtCore.SIGNAL('toggled(bool)'),
                     self.do_change_data_access_mode)

        QtCore.QObject.connect(self.ui.pushButton_browse, QtCore.SIGNAL('clicked()'),
                               self.do_browse_ipts_folder)

        QtCore.QObject.connect(self.ui.pushButton_verify, QtCore.SIGNAL('clicked()'),
                               self.do_set_ipts_dir)

        self.connect(self.ui.pushButton_iptsInfo, QtCore.SIGNAL('clicked()'),
                     self.do_list_ipts_info)

        QtCore.QObject.connect(self.ui.pushButton_OK_2, QtCore.SIGNAL('clicked()'),
                               self.do_save_quit)

        QtCore.QObject.connect(self.ui.pushButton_cancel_2, QtCore.SIGNAL('clicked()'),
                               self.do_reject_quit)

        self.connect(self.ui.checkBox_skipScan, QtCore.SIGNAL('stateChanged(int)'),
                     self.evt_skip_scan_data)

        # Disable some unused widget until 'browse' or 'set' is pushed.
        self.ui.pushButton_iptsInfo.setDisabled(True)
        self.ui.dateEdit_begin.setDisabled(True)
        self.ui.dateEdit_end.setDisabled(True)
        self.ui.lineEdit_begin.setDisabled(True)
        self.ui.lineEdit_end.setDisabled(True)
        self.ui.pushButton_OK_2.setDisabled(True)

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

        self._dataDir = '/SNS/VULCAN'

        self._homeDir = os.path.expanduser('~')

        return

    def do_browse_ipts_folder(self):
        """ Browse IPTS directory
        :return:
        """
        if str(self.ui.lineEdit_iptsDir.text()).strip() != '':
            home_dir = str(self.ui.lineEdit_iptsDir.text()).strip()
        else:
            home_dir = self._homeDir
        ipts_dir = str(QtGui.QFileDialog.getExistingDirectory(self, 'Get Directory',
                                                              home_dir))
        self.ui.lineEdit_iptsDir.setText(ipts_dir)
        self._iptsDir = ipts_dir
        self._iptsDirFromDir = ipts_dir

        # Enable next step
        self.ui.pushButton_iptsInfo.setEnabled(True)
        # self.ui.dateEdit_begin.setEnabled(True)
        # self.ui.dateEdit_end.setEnabled(True)

        return

    def do_change_data_access_mode(self):
        """
        Toggle between 2 approaches to get ITPS directory: from ITPS number of directory
        :return:
        """
        if self.ui.radioButton_useNumber.isChecked() is True:
            self.ui.lineEdit_iptsNumber.setEnabled(True)
            self.ui.pushButton_verify.setEnabled(True)
            self.ui.lineEdit_iptsDir.setDisabled(True)
            self.ui.pushButton_browse.setDisabled(True)
            self._iptsDir = self._iptsDirFromNumber
        else:
            self.ui.lineEdit_iptsNumber.setEnabled(False)
            self.ui.pushButton_verify.setEnabled(False)
            self.ui.lineEdit_iptsDir.setDisabled(False)
            self.ui.pushButton_browse.setDisabled(False)
            self._iptsDir = self._iptsDirFromDir

        return

    def do_list_ipts_info(self):
        """
        List runs including run numbers, creation time and full path file names
        of one IPTS directory
        :return:
        """
        # Show the status of processing...Just change the background color...
        # blinking is not easy
        self.ui.label_loadingStatus.setText('Inspecting data directory %s... ...' %
                                            self._iptsDir)
        time.sleep(0.1)

        # Get basic information
        try:
            status, ret_obj = self._myParent.get_workflow().get_ipts_info(self._iptsDir)
        except AttributeError as e:
            gutil.pop_dialog_error(self, 'Unable to get IPTS information due to %s.' % str(e))
            self.ui.label_loadingStatus.setText('Failed to access %s.' % self._iptsDir)
            return

        # Error in retrieving
        if status is False:
            error_message = ret_obj
            gutil.pop_dialog_error('Unable to get IPTS information due to %s.' % error_message)
            self.ui.label_loadingStatus.setText('Failed to access %s.' % self._iptsDir)
            return

        # Get list
        run_tup_list = ret_obj
        assert(isinstance(run_tup_list, list))

        # Sort by run
        run_tup_list.sort(key=lambda x: x[0])
        first_run = run_tup_list[0][0]
        last_run = run_tup_list[-1][0]
        self.ui.lineEdit_begin.setText(str(first_run))
        self.ui.lineEdit_end.setText(str(last_run))

        # Sort by date
        run_tup_list.sort(key=lambda x: x[1])
        date_begin = gutil.convert_to_qdate_epoch(run_tup_list[0][1])
        self.ui.dateEdit_begin.setDate(date_begin)

        date_end = gutil.convert_to_qdate_epoch(run_tup_list[-1][1])
        self.ui.dateEdit_end.setDate(date_end)

        self.ui.label_loadingStatus.setText('IPTS directory %s: total %d runs' % (
            self._iptsDir, len(run_tup_list)))

        # Enable widgets to complete the setup
        self.ui.dateEdit_begin.setEnabled(True)
        self.ui.dateEdit_end.setEnabled(True)
        self.ui.lineEdit_begin.setEnabled(True)
        self.ui.lineEdit_end.setEnabled(True)
        self.ui.pushButton_OK_2.setEnabled(True)

        return

    def do_set_ipts_dir(self):
        """
        Create the IPTS directory from an IPTS number
        :return:
        """
        # Get IPTS number
        ipts_number = gutil.parse_integer(self.ui.lineEdit_iptsNumber)
        if ipts_number is None:
            gutil.pop_dialog_error(self, 'IPTS number must be given!')
            return
        self._iptsNumber = ipts_number

        # Get and check IPTS directory
        # Check
        if self._dataDir is None:
            gutil.pop_dialog_error('Data directory is not set up.')
            return

        ipts_dir = os.path.join(self._dataDir, 'IPTS-%d/data/' % ipts_number)
        if os.path.exists(ipts_dir) is False:
            gutil.pop_dialog_error(self, 'IPTS number %d cannot be found under %s. ' % (
                ipts_number, ipts_dir))
            self.ui.lineEdit_iptsNumber.setStyleSheet('color:red')
            return
        else:
            self.ui.lineEdit_iptsNumber.setStyleSheet('color:green')

        self._iptsDir = ipts_dir
        self._iptsDirFromNumber = ipts_dir

        # Enable widgets for next step
        self.ui.pushButton_iptsInfo.setEnabled(True)
        # self.ui.dateEdit_begin.setEnabled(True)
        # self.ui.dateEdit_end.setEnabled(True)

        return

    def do_save_quit(self):
        """
        Quit with accepting user's setup
        :return:
        """
        # Check whether it is fine to leave with 'OK'
        if self._iptsDir is None:
            gutil.pop_dialog_error('IPTS or data directory has not been set up.'
                                   'Use Cancel instead of OK.')
            return

        begin_date = self.ui.dateEdit_begin.date()
        assert(isinstance(begin_date, QtCore.QDate))
        self._beginDate = '%02d/%02d/%02d' % (begin_date.month(), begin_date.day(), begin_date.year())

        end_date = self.ui.dateEdit_end.date()
        assert(isinstance(end_date, QtCore.QDate))
        self._endDate = '%02d/%02d/%02d' % (end_date.month(), end_date.day(), end_date.year())

        begin_run = gutil.parse_integer(self.ui.lineEdit_begin)
        if begin_run is not None:
            self._beginRunNumber = begin_run

        end_run = gutil.parse_integer(self.ui.lineEdit_end)
        if end_run is not None:
            self._endRunNumber = end_run

        # Quit
        self.quit = True
        self.close()

        return

    def do_reject_quit(self):
        """ Quit and abort the operation
        """
        self.quit = True
        self.close()

        return

    def evt_skip_scan_data(self):
        """
        Purpose: enable/disable the requirement to scan directory before add data!s
        :return:
        """
        # TODO/NOW/1st: Implement
        blablabla

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

    def set_data_root_dir(self, root_dir):
        """
        Set root data dir
        :param root_dir:
        :return:
        """
        self._dataDir = root_dir


""" Test Main """
if __name__=="__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = AddRunsByIPTSDialog(None)
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)
