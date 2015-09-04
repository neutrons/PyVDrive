#!/usr/bin/python
__author__ = 'wzz'

# import utility modules
import sys
import os

# import PyQt modules
from PyQt4 import QtGui, QtCore, Qt

# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

""" import GUI components generated from Qt Designer .ui file """
import ui.VdriveMain as mainUi
import ui.GuiUtility as guiutil
import ui.snapgraphicsview as spview

""" import PyVDrive library """
import VDriveAPI as vdrive

import ui.Dialog_AddRuns as dlgrun
import ui.Window_LogPicker as LogPicker
import ui.DialogLogSnapView as dlgSnap


class VDrivePlotBeta(QtGui.QMainWindow):
    """ Main GUI class for VDrive of the beta version
    """
    # Define signals to child windows as None(s)
    myLogSignal = QtCore.pyqtSignal(str)
    mySideBarSignal = QtCore.pyqtSignal(str)

    # initialize app
    def __init__(self, parent=None):
        """ Init
        """
        # Setup main window
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle('VDrivePlot (Beta)')
        self.ui = mainUi.Ui_MainWindow()
        self.ui.setupUi(self)

        # Define status variables
        # new work flow
        self._myWorkflow = vdrive.VDriveAPI()
        self._calibCriteriaFile = ''
        self._numSnapViews = 6

        # Initialize widgets
        self._init_widgets()

        # Define event handling
        self.connect(self.ui.pushButton_selectIPTS, QtCore.SIGNAL('clicked()'),
                     self.do_add_runs_by_ipts)
        self.connect(self.ui.pushButton_loadCalFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_calibration)
        self.connect(self.ui.pushButton_readSampleLogFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_sample_log_file)

        # Column 2
        self.connect(self.ui.checkBox_chopRun, QtCore.SIGNAL('stateChanged(int)'),
                     self.evt_chop_run_state_change)
        self.connect(self.ui.pushButton_manualPicker, QtCore.SIGNAL('clicked()'),
                     self.pop_manual_picker)
        self.connect(self.ui.pushButton_pickSlicer, QtCore.SIGNAL('clicked()'),
                     self.do_pick_slicer)

        # Column 3
        self._snapViewCheckBoxList = [self.ui.checkBox_plotInFloat1,
                                      self.ui.checkBox_plotInFloat2,
                                      self.ui.checkBox_plotInFloat3,
                                      self.ui.checkBox_plotInFloat4,
                                      self.ui.checkBox_plotInFloat5,
                                      self.ui.checkBox_plotInFloat6]
        for check_box in self._snapViewCheckBoxList:
            self.connect(check_box, QtCore.SIGNAL('stateChanged(int)'),
                         self.pop_snap_view)

        self._combo_box_list = [self.ui.comboBox_g11, self.ui.comboBox_g21,
                          self.ui.comboBox_g31, self.ui.comboBox_g41,
                          self.ui.comboBox_g51, self.ui.comboBox_g61]
        for combo_box in self._combo_box_list:
            self.connect(combo_box, QtCore.SIGNAL('indexChanged(int)'),
                         self.do_change_log_snap_view)

        #self.connect(self.ui.checkBox_plotInFloat1, QtCore.SIGNAL('stateChanged(int)'),
        #             self.pop_snap_view)

        # Event handling for menu
        self.connect(self.ui.actionSave_Project, QtCore.SIGNAL('triggered()'),
                     self.menu_save_session)
        self.connect(self.ui.actionSave_Project_As, QtCore.SIGNAL('triggered()'),
                     self.menu_save_session_as)
        self.connect(self.ui.actionOpen_Project, QtCore.SIGNAL('triggered()'),
                     self.menu_load_session)

        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'),
                     self.evt_quit)

        # Group widgets
        self._groupedSnapViewList = list()
        self._setup_snap_view_groups(self._numSnapViews)

        # Sub windows
        # controls to the sub windows
        self._openSubWindows = []
        self._manualPikerWindow = None
        self._snapViewWindow = None

        # Some class variable for recording status
        self._savedSessionFileName = None

        return

    def _init_widgets(self):
        """ Initialize widgets including
        (1) project runs view
        :return: None
        """
        '''
        # IPTS and run tree view
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'IPTS')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Run')
        self.ui.treeView_iptsRun.setModel(model)
        self.ui.treeView_iptsRun.setColumnWidth(0, 90)
        self.ui.treeView_iptsRun.setColumnWidth(1, 60)
        self.ui.treeView_iptsRun.setDragEnabled(True)
        '''

        # Chopping
        self.ui.checkBox_chopRun.setCheckState(QtCore.Qt.Unchecked)
        self.ui.tabWidget_reduceData.setCurrentIndex(1)
        self.ui.tabWidget_reduceData.setTabEnabled(0, False)

        # Plotting log
        self.ui.checkBox_logSkipSec.setCheckState(QtCore.Qt.Checked)
        self.ui.lineEdit_numSecLogSkip.setText('1')

        return

    def _setup_snap_view_groups(self, num_groups):
        """ Set up 6 snap view and control widgets groups
        Class variable _groupSnapViewList will record all of them accordingly
        :param num_groups: number of groups to initialize
        :return: None
        """
        for i in xrange(1, num_groups+1):
            try:
                # get on hold of three widgets with systematic naming
                graph_view = getattr(self.ui, 'graphicsView_snapView%d'%(i))
                combo1 = getattr(self.ui, 'comboBox_g%d1'%(i))
                combo2 = getattr(self.ui, 'comboBox_g%d2'%(i))
            except AttributeError as e:
                raise RuntimeError('GUI changed but python code is not changed accordingly: %s'%(str(e)))
            else:
                # set up group
                graph_group = spview.SnapGraphicsView(graph_view, combo1, combo2)
                self._groupedSnapViewList.append(graph_group)
        # END_FOR(i)

        return

    def do_add_runs_by_ipts(self):
        """ import runs by IPTS number
        :return: None
        """
        # Launch window
        child_window = dlgrun.AddRunsByIPTSDialog(self)
        child_window.set_data_root_dir(self._myWorkflow.get_data_root_directory())
        r = child_window.exec_()

        # Return due to 'cancel'
        ipts_dir = child_window.get_ipts_dir()
        if ipts_dir is None:
            return

        # Add IPTS
        ipts_number = child_window.get_ipts_number()
        if ipts_number is None:
            status, ret_obj = self._myWorkflow.get_ipts_number_from_dir(ipts_dir)
            if status is False:
                message = 'Unable to get IPTS number due to %s. Using user directory.' % ret_obj
                guiutil.pop_dialog_error(self, message)
                ipts_number = 0
            else:
                ipts_number = ret_obj
        begin_date, end_date, begin_run, end_run = child_window.get_date_run_range()

        status, ret_obj = self._myWorkflow.get_ipts_info(ipts_dir)
        if status is True:
            run_tup_list = ret_obj
        else:
            # Pop error
            error_message = ret_obj
            guiutil.pop_dialog_error(self, error_message)
            return

        status, ret_obj = vdrive.filter_runs_by_date(run_tup_list, begin_date, end_date,
                                                     include_end_date=True)
        if status is True:
            run_tup_list = ret_obj
        else:
            #  pop error
            error_message = ret_obj
            guiutil.pop_dialog_error(self, error_message)
            return

        # Filter runs by run
        status, ret_obj = vdrive.filter_runs_by_run(run_tup_list, begin_run, end_run)
        if status is False:
            guiutil.pop_dialog_error(ret_obj)
            return
        else:
            run_tup_list = ret_obj

        status, error_message = self._myWorkflow.add_runs(run_tup_list, ipts_number)
        if status is False:
            guiutil.pop_dialog_error(self, error_message)
            return

        # Set to tree
        if ipts_number == 0:
            ipts_number = os.path.basename(ipts_dir)
        self.ui.treeView_iptsRun.add_ipts_runs(ipts_number, run_tup_list)

        # Set to file tree directory
        if ipts_number > 0:
            home_dir = '/SNS/VULCAN'
        else:
            home_dir = os.path.expanduser('~')
        curr_dir = ipts_dir
        self.ui.treeView_runFiles.set_root_path(home_dir)
        self.ui.treeView_runFiles.set_current_path(curr_dir)

        return

    def do_change_log_snap_view(self):
        """
        Event handling if user chooses to plot another log in snap view
        :return:
        """
        for i in xrange(len(self._combo_box_list)):
            curr_value = str(self._combo_box_list[i].currentText())
            if curr_value != self._cacheSnapViewLogNames[i]:
                do_plot_again()
                break
        return

    def do_load_calibration(self):
        """
        :return:
        """
        # Get calibration file
        if os.path.exists(self._calibCriteriaFile) is False:
            self._calibCriteriaFile = str(
                QtGui.QFileDialog.getOpenFileName(self, 'Get Vanadium Criteria', '/SNS/VULCAN/')
            )
            if self._calibCriteriaFile is None or len(self._calibCriteriaFile) == 0:
                return

        # Launch second dialog to select the criteria from table
        import ui.Dialog_SetupVanCalibrationRules as vanSetup
        setupdialog = vanSetup.SetupVanCalibRuleDialog(self)
        setupdialog.exec_()

        return

    def do_load_sample_log_file(self):
        """ Load nexus file for plotting sample log.
        The file should be selected from runs in the tree
        :return:
        """
        # Get the default file path
        data_path = self._myWorkflow.get_data_root_directory()

        status, ret_obj = self.ui.treeView_iptsRun.get_current_run()
        if status is True:
            run_number = ret_obj
            status, ret_obj = self._myWorkflow.get_run_info(run_number)
            if status is True:
                if data_path.startswith('/SNS/'):
                    # get to IPTS-???/0/.. directory
                    ipts_number = ret_obj[1]
                    data_path = os.path.join(data_path, 'IPTS-%d/0/%d/NeXus' % (ipts_number, run_number))
                else:
                    data_path = os.path.dirname(ret_obj[0])
            else:
                print 'Unable to get run from tree view: %s' % ret_obj
        else:
            print 'Unable to get run from tree view: %s' % ret_obj

        # Dialog to get the file name
        file_filter = "NXS (*.nxs);;All files (*.*)"
        log_file_name = str(QtGui.QFileDialog.getOpenFileName(self, 'Open NeXus File',
                                                              data_path, file_filter))

        """
        # Load file
        status, errmsg = self._myWorkflow.init_slicing_helper(nxs_file_name=log_file_name)
        if status is False:
            guiutil.pop_dialog_error(errmsg)

        # Get log names
        status, ret_value = self._myWorkflow.get_sample_log_names()
        if status is False:
            errmsg = ret_value
            guiutil.pop_dialog_error(errmsg)
            return
        else:
            log_name_list = sorted(ret_value)
            print '[DB] List of log names: %s' % str(log_name_list)
        """
        log_name_list = self.load_sample_run(log_file_name)

        # Plot first 6 sample logs
        do_skip = self.ui.checkBox_logSkipSec.checkState() == QtCore.Qt.Checked
        if do_skip is True:
            num_sec_skipped = guiutil.parse_integer(self.ui.lineEdit_numSecLogSkip)
        else:
            num_sec_skipped = None

        # Set up and plot all 6 widgets groups
        for i in xrange(min(self._numSnapViews, len(log_name_list))):
            # create a log_widget from base snap view widgets and set up
            snap_widget = self._groupedSnapViewList[i]
            log_widget = spview.SampleLogView(snap_widget)

            log_widget.set_log_names(log_name_list)
            log_widget.set_current_log_name(i)

            # get log value
            log_name = log_name_list[i]
            """
            status, ret_obj = self._myWorkflow.get_sample_log_values(log_name)
            if status is False:
                guiutil.pop_dialog_error(ret_obj)
                continue
            vec_times, vec_log_value = ret_obj
            """
            vec_times, vec_log_value = self.get_sample_log_value(log_name)

            # plot log value
            log_widget.plot_data(vec_times, vec_log_value, do_skip, num_sec_skipped)

        # END-FOR

        return

    def do_pick_slicer(self):
        """ Pick up (time) slicing information and show it by indicating lines in snap view
        :return:
        """
        # TODO - Get slicing information

        # TODO - Create splitters by Mantid

        # TODO - Apply splitters to all snap view

        return

    def do_save_slicer(self):
        """ Save the slicer (splitters) for future splitting
        :return:
        """

    def evt_chop_run_state_change(self):
        """
        Event handling for checkbox 'chop data' is checked or unchecked
        :return:
        """
        new_status = self.ui.checkBox_chopRun.checkState()
        if new_status == QtCore.Qt.Unchecked:
            self.ui.tabWidget_reduceData.setCurrentIndex(1)
            self.ui.tabWidget_reduceData.setTabEnabled(0, False)
        else:
            self.ui.tabWidget_reduceData.setCurrentIndex(0)
            self.ui.tabWidget_reduceData.setTabEnabled(0, True)

        return

    def evt_quit(self):
        """
        Quit application without saving
        :return:
        """
        # FIXME - Save the session automatically before leaving
        self.close()

    def get_sample_log_value(self, log_name):
        """
        Get sample log vaue
        :param log_name:
        :return: 2-tuple as (numpy.1darray, numpy.1darray)
        """
        status, ret_obj = self._myWorkflow.get_sample_log_values(log_name)
        if status is False:
            raise RuntimeError(ret_obj)

        vec_times, vec_log_value = ret_obj

        return vec_times, vec_log_value

    def get_ipts_runs(self):
        """
        Get added IPTS and run to caller
        :return:
        """
        return self._myWorkflow.get_project_runs()

    def get_workflow(self):
        """
        Get workflow instance
        :return:
        """
        return self._myWorkflow

    def load_sample_run(self, run):
        """
        Load sample run
        :param run: string or integer as nxs file name or run number
        :return: list of string for log names
        """
        # Check
        assert isinstance(run, str) or isinstance(run, int)

        # Get NeXus file name
        if isinstance(run, int):
            # in case of run number is given
            status, run_tuple = self._myWorkflow.get_run_info(run)
            if status is False:
                raise RuntimeError(run_tuple)
            nxs_file_name = run_tuple[0]
        else:
            nxs_file_name = run

        # Load file
        status, errmsg = self._myWorkflow.init_slicing_helper(nxs_file_name=nxs_file_name)
        if status is False:
            raise RuntimeError(errmsg)

        # Get log names
        status, ret_value = self._myWorkflow.get_sample_log_names()
        if status is False:
            errmsg = ret_value
            raise RuntimeError(errmsg)

        log_name_list = sorted(ret_value)

        return log_name_list

    def menu_save_session(self):
        """
        Save session called from menu
        :return:
        """
        if self._savedSessionFileName is None:
            self._savedSessionFileName = str(
                QtGui.QFileDialog.getSaveFileName(self, 'Save Session', self._myWorkflow.get_working_dir(),
                                                  'XML files (*.xml);; All files (*.*)'))

        self._myWorkflow.save_session(self._savedSessionFileName)

        return

    def menu_save_session_as(self):
        """
        Save session as
        :return:
        """
        saved_session_file_name = str(
                QtGui.QFileDialog.getSaveFileName(self, 'Save Session', self._myWorkflow.get_working_dir(),
                                                  'XML files (*.xml); All files (*.*)'))

        self._myWorkflow.save_session(saved_session_file_name)

        return

    def menu_load_session(self):
        """
        Load session from file
        :return:
        """
        # Get file name
        input_file_name = str(
            QtGui.QFileDialog.getOpenFileName(self, 'Load Session', self._myWorkflow.get_working_dir(),
                                              'XML files (*.xml);; All files (*.*)')
        )

        # Load
        status, input_file_name = self._myWorkflow.load_session(input_file_name)
        if status is False:
            guiutil.pop_dialog_error('Unable to load session from %s' % input_file_name)

        # Set input file to default session back up file
        self._savedSessionFileName = input_file_name

        # Set up tree
        # FIXME - Consider to refactor these to a method with do_add_runs_by_ipts
        ipts_dict = self._myWorkflow.get_project_runs()
        for ipts_number in sorted(ipts_dict.keys()):
            self.ui.treeView_iptsRun.add_ipts_runs(ipts_number, ipts_dict[ipts_number])
            # FIXME - Need to figure out how to deal with this
            home_dir = '/SNS/VULCAN'
            curr_dir = os.path.join(home_dir, 'IPTS-%d' % ipts_number)
            self.ui.treeView_runFiles.set_root_path(home_dir)
            self.ui.treeView_runFiles.set_current_path(curr_dir)

        return

    def pop_manual_picker(self):
        """
        Pop out manual picker window
        :return:
        """
        # Start
        if isinstance(self._manualPikerWindow, LogPicker.WindowLogPicker):
            self._manualPikerWindow.show()
        else:
            self._manualPikerWindow = LogPicker.WindowLogPicker(self)

        # Set up tree view for runs
        self._manualPikerWindow.setup()

        # Show
        self._manualPikerWindow.show()

        return

    def pop_snap_view(self):
        """ Pop out snap view dialog (window)
        :return:
        """
        # TODO - Find the change of these 6 check box.  If any new box is checked, then un-check the
        #        previously checked box
        #        If no box is checked, close the window and return
        #        If there are 2 checked box, find out which one is the previously checked
        # FIXME/TODO - NOW

        # Check whether there is any open window
        if self._snapViewWindow is None:
            self._snapViewWindow = dlgSnap.DialogLogSnapView()
        elif self._snapViewWindow.is_open() is False:
            self._snapViewWindow.show()
        else:
            if self._snapViewWindow.is_saved() is False:
                # If window is open but not saved, pop error message
                guiutil.pop_dialog_error('Current window is not saved.')
                return

        # TODO - If window is None or not open, then show() it

        # TODO - Set up / re-set up log value to the sub window



        # FIXME - It is a mock now!
        self._snapViewWindow.setup(self._myWorkflow, run_number, sample_log_name, num_sec_skip)

        self._snapViewWindow.show()

        return


if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = VDrivePlotBeta()
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)
