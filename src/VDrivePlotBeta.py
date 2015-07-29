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
        # new project
        self._myWorkflow = vdrive.VDriveAPI()
        self._calibCriteriaFile = ''

        # controls to the sub windows
        self._openSubWindows = []

        # Initialize widgets
        self._initWidgets()

        # Define event handling
        self.connect(self.ui.pushButton_selectIPTS, QtCore.SIGNAL('clicked()'),
                     self.do_add_runs_by_ipts)
        self.connect(self.ui.pushButton_loadCalFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_calibration)
        self.connect(self.ui.pushButton_readSampleLogFile, QtCore.SIGNAL('clicked()'),
                     self.do_load_sample_log_file)

        # Group widgets
        self._groupedSnapViewList = []

        # TODO - Use  getattr(a, 'x') for all 6
        graph_group0 = spview.SnapGraphicsView(self.ui.graphicsView_snapView0,
                                              self.ui.comboBox_g11, self.ui.comboBox_g12)
        self._groupedSnapViewList.append(graph_group0)


        return

    def _initWidgets(self):
        """

        :return:
        """
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


    def do_add_runs_by_ipts(self):
        """ import runs by IPTS number
        :return: None
        """
        # Launch window
        childwindow = dlgrun.AddRunsByIPTSDialog(self)
        r = childwindow.exec_()

        # Return due to 'cancel'
        if childwindow.get_ipts_dir() is None:
            return

        # Add ITPS
        iptsdir = childwindow.get_ipts_dir()
        print "[NEXT] Add IPTS directly %s to Tree" % (iptsdir)

        ipts, runs = self._myWorkflow.add_runs(iptsdir)

        guiutil.add_runs_to_tree(self.ui.treeView_iptsRun, ipts, runs)

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
            lognamelist = retvalue

        snapwidget =  self._groupedSnapViewList[0]
        logwidget = spview.SampleLogView(snapwidget)
        logwidget.setLogNames(lognamelist)

        # Plot the first 6...

        # FIXME - This is prototype


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

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = VDrivePlotBeta()
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)
