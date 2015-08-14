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

#import config
#import PyVDrive.vdrive.FacilityUtil as futil

import ui.Dialog_AddRuns as dlgrun


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

        # controls to the sub windows
        self._openSubWindows = []

        # Initialize widgets
        # self._init_widgets()

        # Define event handling
        self.connect(self.ui.pushButton_selectIPTS, QtCore.SIGNAL('clicked()'),
                     self.do_add_runs_by_ipts)
        self.connect(self.ui.pushButton_loadCalFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_calibration)
        self.connect(self.ui.pushButton_readSampleLogFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_sample_log_file)

        # Group widgets
        self._groupedSnapViewList = []
        self._setup_snap_view_groups(self._numSnapViews)


        return

    def _init_widgets(self):
        """ Initialize widgets including
        (1) project runs view
        :return: None
        """
        # IPTS and run tree view
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'IPTS')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Run')
        self.ui.treeView_iptsRun.setModel(model)
        self.ui.treeView_iptsRun.setColumnWidth(0, 90)
        self.ui.treeView_iptsRun.setColumnWidth(1, 60)
        self.ui.treeView_iptsRun.setDragEnabled(True)

        tree = QtGui.QTreeView()

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
        r = child_window.exec_()

        # Return due to 'cancel'
        if child_window.get_ipts_dir() is None:
            return

        # Add ITPS
        ipts_dir = child_window.get_ipts_dir()
        begin_date, end_date, begin_run, end_run = child_window.get_date_run_range()
        print "[NEXT] Add IPTS directly %s to Tree" % (ipts_dir)

        status, ret_obj = self._myWorkflow.get_ipts_info(ipts_dir)
        if status is True:
            run_tup_list = ret_obj
        else:
            # FIXME - Pop error
            guiutil.pop_dialog_error(self, 'blabalba')
            return

        status, ret_obj = self._myWorkflow.filter_runs_by_date(run_tup_list, begin_date, end_date)
        if status is True:
            run_tup_list = ret_obj
        else:
            # FIXME - pop error
            guiutil.pop_dialog_error(self, 'blabal')
            return

        status, error_message = self._myWorkflow.add_runs(ipts_dir, '121234')
        if status is False:
            guiutil.pop_dialog_error(self, error_message)
            return

        # Set to tree
        self._myWorkflow.get_runs(ipts)
        # guiutil.add_runs_to_tree(self.ui.treeView_iptsRun, ipts, runs)
        # FIXME - Implement these 2 methods
        self.ui.treeView_iptsRun.add_ipts_runs(ipts_number, run_number_list)
        self.ui.treeView_runFiles.set_home_dir(home_dir, curr_dir)

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
        """

        :return:
        """
        # Dialog to get the file name
        # FIXME - homedir should be set up from configuration and previous user input
        home_dir = '/SNS/VULCAN/'
        file_filter="NXS (*.nxs);;All files (*.*)"
        # FIXME - Speed up for testing
        if False:
            log_file_name = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Sample Log File',
                                                              home_dir, file_filter))
        else:
            log_file_name = '/SNS/VULCAN/IPTS-14114/0/71087/NeXus/VULCAN_71087_event.nxs'
        print "About to load sample log from file %s."%(log_file_name)

        # Load file
        status, errmsg, retvalue = self._myWorkflow.loadNexus(filename=log_file_name, logonly=True)
        if status is False:
            self._logError(errmsg)
            return
        else:
            tag = retvalue

        # Plot first 6 sample logs
        status, errmsg, retvalue = self._myWorkflow.getSampleLogNames(tag)
        if status is False:
            self._logError(errmsg)
        else:
            log_name_list = sorted(retvalue)

        # Set up all 6 widgets groups
        for i in xrange(self._numSnapViews):
            # create a log_widget from base snap view widgets and set up
            snap_widget = self._groupedSnapViewList[i]
            log_widget = spview.SampleLogView(snap_widget)
            log_widget.setLogNames(log_name_list)

        # Plot the first 6...
        for i in xrange(self._numSnapViews):
            pass


        '''
        for i in xrange(6):
            status, errmsg, retvalue = self._myWorkflow.getSampleLogVectorByIndex(tag, logindex=i)
            if status is False:
                self._logError(errmsg)
                continue
            else:
                vecx, vecy, logname = retvalue

            self._snapGraphicsView[i].plotSampleLog(vecx, vecy, lognamelist, logname)
        # ENDFOR
        '''
        raise NotImplementedError('Debut Stop Here! 342')

    def get_workflow(self):
        """

        :return:
        """
        # TODO -Doc
        return self._myWorkflow

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = VDrivePlotBeta()
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)
