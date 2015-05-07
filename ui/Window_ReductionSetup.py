import sys
import os
import math
import numpy

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
from ui_ReductionSetup import *
import Dialog_VanDatabaseCriteria # MyVanadiumDatabaseCriterialDialog
import Dialog_AddDataFiles

import PyVDrive
import PyVDrive.vdrive.vulcan_util
import Window_GPPlot

# TODO - Clean codes

class MyReductionWindow(QWidget):
    """ Pop up dialog window
    """
    # define signals
    myAddRunsSignal = pyqtSignal(str)

    # class
    def __init__(self, parent, config):
        """ Init
        """
        # call base
        QWidget.__init__(self)

        # parent & config
        self._myParent = parent
        self._myConfig = config


        # set up UI & initial values
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.checkBox_autoVanRun.setChecked(True)

        self._myDataPlotWindow  = None

        #---------------------------------
        # Set up validation
        #---------------------------------
        # ipts, run start, run end should be integers

        #---------------------------------
        # Setup GUI event handlers
        #---------------------------------
        # project selection 
        QtCore.QObject.connect(self.ui.pushButton_selectproject, 
                QtCore.SIGNAL('clicked()'), self.doSelectProject)

        # add runs/file for reduction
        QtCore.QObject.connect(self.ui.pushButton_addRuns,
                QtCore.SIGNAL('clicked()'), self.doAddRuns)

        # calibration setup
        QtCore.QObject.connect(self.ui.pushButton_vanDBFile, 
                QtCore.SIGNAL('clicked()'), self.doBrowseVanDBFile)

        QtCore.QObject.connect(self.ui.pushButton_vanDBCriteriaSetup,
                QtCore.SIGNAL('clicked()'), self.doShowVanCriteriaWindow)

        # setup tabs
        QtCore.QObject.connect(self.ui.pushButton_browseBaseDataPath,
                QtCore.SIGNAL('clicked()'), self.doBrowseBaseDataPath)

        # reduction
        QtCore.QObject.connect(self.ui.pushButton_reduceData, 
                QtCore.SIGNAL('clicked()'), self.doReduceData)

        # quit
        QtCore.QObject.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'), self.quit)

        # Customerized event 
        self.myAddRunsSignal.connect(self._myParent.evtAddRuns)

        # TODO - Set the defaults
        self._myProjectName = None

        self.ui.lineEdit_baseDataPath.setText(
                self._myParent._myWorkflow._myConfig["default.BaseDataPath"])
        self.ui.lineEdit_vanDBFile.setText(
                self._myParent._myWorkflow._myConfig["default.VanadiumDataBaseFile"])
        self.ui.lineEdit_timeFocusTable.setText(
                self._myParent._myWorkflow._myConfig['default.timeFocusFile'])


        print "Default of Base Data Path:", str(self.ui.lineEdit_baseDataPath.text())
        print "Default of Vanadium Data File Path:", str(self.ui.lineEdit_vanDBFile.text())

        return

    def setMessage(self, errmsg):
        """ Set message
        """
        #self.ui.label_errmsg.setWordWrap(True)
        #self.ui.label_errmsg.setText(errmsg)

        return


    def setProjectNames(self, projnames):
        """ Set project names
        """
        # self.ui.comboBox_projectNames.addItems(self._myParent.getReductionProjectNames())
        self.ui.comboBox_projectNames.addItems(projnames)

        return

    def setCurrentProject(self, projname):
        """ Set current project name
        """
        index = self.ui.comboBox_projectNames.findText(projname)
        if index < 0:
            return (False, "Project %s does not exist in project list." % (projname))

        self.ui.comboBox_projectNames.setCurrentIndex(index)
        self._myProjectName = projname

        return (True, "Set project %s with index %d as current project."%(projname, index))


    def doSelectProject(self):
        """ select projects by name
        """
        self._myProjectName = str(self.ui.comboBox_projectNames.currentText())
        print "Project %s is selected. " % (str( self._myProjectName))

        # FIXME - Need to wipe out previous setup and fill in the new ones

        return


    def doAddRuns(self):
        """ add IPTS-run numbers to current reduction project
        """
        # Get IPTS and runs from GUI
        ipts = str(self.ui.lineEdit_ipts.text())
        runstart = str(self.ui.lineEdit_runstart.text())
        runend = str(self.ui.lineEdit_runend.text())

        logmsg = "Get IPTS %s Run %s to %s." % (ipts, runstart, runend)
        print "Log: %s" % (logmsg)

        # Parse and build list of run numbers
        if len(ipts) == 0:
            logmsg = "Error: IPTS must be given for adding runs." 
            print logmsg
        else:
            ipts = int(ipts)

        runnumberlist = []
        if len(runstart) == 0 and len(runend) == 0:
            logmsg = "Error: No run number is given!"
            print logmsg
            return
        elif len(runstart) == 0:
            runnumberlist.append(int(runend))
        elif len(runend) == 0:
            runnumberlist.append(int(runstart))
        else:
            runnumberlist.extend(range(int(runstart), int(runend)+1))

        logmsg = "Adding ITPS-%d runs: %s. " % (ipts, str(runnumberlist))
          
        # 2-Steps to add runs to a project instance
        # a) Add all runs to project and let project to decide which runs to be taken 
        autofindcal = self.ui.checkBox_autoVanRun.isChecked()
        runfilecallist = self._myParent.setRuns(self._myProjectName, ipts, runnumberlist, autofindcal)
        if runfilecallist is None:
            print "Run file calibration list is None!"
            return False

        # b) Launch the dialog window for user to determine the vanadium runs
        filecallist = [] 
        for dfname, vanruns in runfilecallist:
            dfname = os.path.basename(dfname)
            filecallist.append( [dfname, vanruns] )
       
        tableinfodict = {
                'Headers':  ['Run/Data File', 'Vanadium  Run'],
                'CellType': ['text', 'combobox']}
        self._myCalibMatchWindow = Dialog_AddDataFiles.MyAddDataFilesDialog(self, \
                self._myConfig, tableinfodict)
        self._myCalibMatchWindow.appendRows(filecallist) 
        self._myCalibMatchWindow.show()

        # ... Disable some buttons to avoid miss operation
        # FIXME - Should be a method such _blockReduction()
        self.ui.pushButton_addRuns.setEnabled(False)

        # b) Launch a dialog for user to determine the vanadium/calibration runs

        # self.myAddRunsSignal.emit(self._myProjectName) 

        return

    def doBrowseBaseDataPath(self):
        """ Prompt a dialog box for selecting the home directory
        """
        # Prompty a dialog bos for selecting base data path
        if len(str(self.ui.lineEdit_baseDataPath.text())) > 0:
            home = str(self.ui.lineEdit_baseDataPath.text())
        else: 
            home = getHomeDir()

        basedatadir = str(QtGui.QFileDialog.getExistingDirectory(self,'Get Directory',home))
        self.ui.lineEdit_baseDataPath.setText(basedatadir)

        # TODO - use a dictionary of class to hold all information of the reduction setup
        self._myParent._myWorkflow.setDataPath(projname = self._myProjectName, 
                basedatapath = vconfig.defaultDataPath)
        
        return

    def doBrowseVanDBFile(self):
        """ Prompt a dialog box for selecting vanadium database file
        """ 
        # get vanadium database file via dialog
        vandbfile = None
        defaultfilename = str(self.ui.lineEdit_vanDBFile.text())
        if len(defaultfilename) > 0: 
            if os.path.isfile(defaultfilename) is True:
                vandbfile = defaultfilename
            else: 
                homedir = os.path.dirname(defaultfilename) 
                if os.path.exists(homedir) is False: 
                    homedir = os.getcwd()
            # ENDIF
        else:
            homedir = os.getcwd()
        # ENDIFELSE(defaultfilename is empty)

        # get vanadium db file via dialog
        if vandbfile is None:
            vandbfilter = "Text files (*.txt);;All files (*.*)"
            fileList = QtGui.QFileDialog.getOpenFileNames(self, 'Open File', homedir, vandbfilter)
            if len(fileList) == 0:
                self._myParent._addLogInformation("No vanadium dabase file is selected");
                return
            vandbfile = str(fileList[0])
            # set value back to line edit
            self.ui.lineEdit_vanDBFile.setText(vandbfile)
        # ENDIF

        # launch the window to ask user to set up match criteria
        vandbfilelogs, vanlogexamples = PyVDrive.vdrive.vulcan_util.getLogsList(vandbfile)
        #print vandbfilelogs

        self._vanDBCriteriaWindow = \
            Dialog_VanDatabaseCriteria.MyVanadiumDatabaseCriterialDialog(self,
                    self._myConfig)
        self._vanDBCriteriaWindow.setAllChoices(vandbfilelogs, vanlogexamples)
        # self._vanDBCriteriaWindow.setDefaults(config.defaultVanDBCriteria)
        self._vanDBCriteriaWindow.show()

        return

    def doShowVanCriteriaWindow(self):
        """ Show vanadium database matchup criteria window
        """
        if self._vanDBCriteriaWindow is not None: 
            self._vanDBCriteriaWindow.show()
        else:
            vandbfile = str(self.ui.lineEdit_vanDBFile.text())

            if os.path.exists(vandbfile) and os.path.isFile(vandbfile):
                # launch the window to ask user to set up match criteria
                vandbfilelogs, vanlogexamples = PyVDrive.vdrive.vulcan_util.getLogsList(vandbfile)
                print vandbfilelogs

                self._vanDBCriteriaWindow = \
                        Dialog_VanDatabaseCriteria.MyVanadiumDatabaseCriterialDialog(self)
                self._vanDBCriteriaWindow.setAllChoices(vandbfilelogs, vanlogexamples)
                self._vanDBCriteriaWindow.show()

            else:
                # van database file is not setup.  
                self._myParent._addLogInformation("Vanadium criteria window cannot be openeda \
                        because vanadium files has not been setup.")

        return

    def doReduceData(self):
        """ Do reduction
        collect the information in this window and call reduction in the main window
        """
        # TODO - Launch the reduction form window!

        # Get project name
        if self._myProjectName is None:
            raise NotImplementedError("It is logically wrong for _myProjectName not setup at doReduceData()")
        else:
            projname = self._myProjectName

        # Collect runs to reduce: go through main window's table
        reductionlist = self._myParent.getReductionList()
        setstatus, msg = self._myParent.getWorkflowObj().setReductionFlags(projname, reductionlist)
        if setstatus is False:
            print msg

        # FIXME - Set parameters...
        ## Collect reduction parameters
        #paramdict = {
        #        "Instrument": "VULCAN",
        #        "Extension": "_event.nxs",
        #        "PreserveEvents": True,
        #        "Binning" : -0.001,
        #        "OutputDirectory" : outputdir, 
        #        "NormalizeByCurrent":  False,
        #        "FilterBadPulses": False,
        #        "CompressTOFTolerance": False,
        #        "FrequencyLogNames": "skf1.speed",
        #        "WaveLengthLogNames": "skf12.lambda"
        #        }
        #self._myParent.getWorkflowObj().setReductionParameters(projname, paramdict)

        # disable all controls during reduction
        self._setEnabledReductionWidgets(False)
        self.ui.pushButton_reduceData.setEnabled(False)

        # Reduce data
        self._myParent.getWorkflowObj().reduceData(projname)
        # # FIXME It is a mock for GUI
        # for i in xrange(100):
        #     self.ui.progressBar.setValue(i+1)

        # enable all controls after reduction
        self._setEnabledReductionWidgets(True)
        self.ui.pushButton_reduceData.setEnabled(True)

        # If reduction is successful, launch post data processing window
        if self._myParent.getWorkflowObj().isReductionSuccessful(projname)[0] is True: 
            self._showDataPlotWindow(projname)
        else:
            print "Error: %s" % (self._myParent.getWorkflowObj().isReductionSuccessful(projname)[1])

        return

    #--------------------------------------------------------------------------
    # Methods to get access to private variable
    #--------------------------------------------------------------------------
    def getParent(self):
        """
        """
        return self._myParent


    #--------------------------------------------------------------------------
    # Singal handling methods
    #--------------------------------------------------------------------------
    @QtCore.pyqtSlot(str, list)
    def evtAddRuns(self, pname, vlist):
        """
        """
        print "Get signal for %s: List size = %d" % (pname,  len(vlist))

        # re-enable some widgets
        self.ui.pushButton_addRuns.setEnabled(True) 

        return


    @QtCore.pyqtSlot(str)
    def _handleBrowseVanDBFile(self):
        """ Second step to handle vanadium database match up
        """
        # check
        if len(self._criteriaList) == 0:
            raise NotImplementedError("No criterial is setup")

        # FIXME - where should this file go? 
        self._myParnet._myWorkflow.setVanadiumCalibrationMatchCriterion(self._myProjectName,
                self._criterialList)
        #self._myParent.setVanadiumDatabaseFile(vandbfile)


        return

    def quit(self):
        """ Quit
        """
        self.close()

        return


    def setupAutoFileAddMode(self, projectname, ipts, runstart, runend):
        """  Set the reduction set up window to auto-IPTS run searching mode
        i.e., project and IPTS are set up.
        """
        # TODO : self.ui.comboBox_projectNames should set to projectname

        # Set up the current project
        self._myProjectName = projectname
        # Set up IPTS
        self.ui.lineEdit_ipts.setText(str(ipts))

        #self.ui.label_SectionAddFiles.setText('Auto File Addition Mode')
        #self.ui.lineEdit_runstart.setText(str(runstart))
        #self.ui.lineEdit_runstart.setEnabled(False)


        return


    def setVanMatchCriteria(self, criterialist):
        """ 
        """
        self._vanDBCriteriaList = criterialist

        self._myParent._myWorkflow.setVanadiumCalibrationMatchCriterion(
                self._myProjectName, self._vanDBCriteriaList)

        return


    # Enable and disable controls
    def _setEnabledReductionWidgets(self, value):
        """ Enable/disable widgets during reduction
        """
        self.ui.lineEdit_timeFocusTable.setDisabled(value)
        self.ui.lineEdit_vanDBFile.setDisabled(value)
        self.ui.lineEdit_binSize.setDisabled(value)

        self.ui.pushButton_timeFocusTableFile.setEnabled(not value)
        self.ui.pushButton_vanDBFile.setEnabled(not value)
        self.ui.pushButton_vanDBCriteriaSetup.setEnabled(not value)
        self.ui.pushButton_gsasPRM.setEnabled(not value)

        return


    def _showDataPlotWindow(self, projname):
        """ Show data plot window
        """
        # Create data plot and processing widget 
        if self._myDataPlotWindow is None:
            self._myDataPlotWindow = Window_GPPlot.Window_GPPlot(self._myParent)
        # Set current project
        self._myDataPlotWindow.setProject(projname)

        # Set up run
        status, errmsg, datafilepairlist = self._myParent.getWorkflowObj().getDataFiles(projname)
        print datafilepairlist
        runlist = []
        for filepair in datafilepairlist:
            runlist.append(filepair[0])
        if len(runlist) is False:
            raise NotImplementedError('Empty run list.')
        runlist = sorted(runlist)
        self._myDataPlotWindow.setRuns(runlist)

        # Set current run
        self._myDataPlotWindow.setCurrentRun(runlist[0])

        # Show 
        self._myDataPlotWindow.show()

        return


def getHomeDir():
    """ Get home directory
    """ 
    if sys.platform == 'win32': 
        home = os.path.expanduser("~") 
    else: 
        home=os.getenv("HOME") 
        
    return home
