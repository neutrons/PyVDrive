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
        
from ui.ui_ReductionSetup import *
from vdrive.

class MyReductionWindow(QWidget):
    """ Pop up dialog window
    """
    # define signals
    myAddRunsSignal = pyqtSignal(str)

    # class
    def __init__(self, parent):
        """ Init
        """
        # call base
        QWidget.__init__(self)

        # parent
        self._myParent = parent

        # set up UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)

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

        # setup tabs
        QtCore.QObject.connect(self.ui.pushButton_browseBaseDataPath,
                QtCore.SIGNAL('clicked()'), self.doBrowseBaseDataPath)

        # quit
        QtCore.QObject.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'), self.quit)

        # Customerized event 
        self.myAddRunsSignal.connect(self._myParent.evtAddRuns)

        # FIXME - Remove this section after debugging 
        #---------------- Debug Setup ---------------------------------
        self.ui.lineEdit_ipts.setText('10311')
        self.ui.lineEdit_runstart.setText('57075')
        self.ui.lineEdit_runend.setText('57100')
        self.ui.lineEdit_baseDataPath.setText('/SNS/VULCAN/')
        #--------------------------------------------------------------

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
        """ add IPTS-run numbers to 
        """
        # get data from GUI
        ipts = str(self.ui.lineEdit_ipts.text())
        runstart = str(self.ui.lineEdit_runstart.text())
        runend = str(self.ui.lineEdit_runend.text())

        logmsg = "Get IPTS %s Run %s to %s." % (ipts, runstart, runend)
        print "Log: %s" % (logmsg)

        # parse
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
            
        # add runs to project: self._myProjectName
        self._myParent.setRuns(ipts, runnumberlist)
        self.myAddRunsSignal.emit(self._myProjectName) 

        return

    def doBrowseBaseDataPath(self):
        """ Prompt a dialog box for selecting the home directory
        """
        # TODO - doc on method
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
        fileList = QtGui.QFileDialog.getOpenFileNames(self, 'Open File', home, filter)
        vandbfile = str(fileList[0])
        self.ui.lineEdit_vanDBFile.setText(vandbfile)

        # launch the window to ask user to set up match criteria
        vandbfilelogs = vulcan_util.getLogsList(vandbfile)

        self._vanDBCriteriaWindow = Dialog_VanDBCriteriaList(self)
        self._vanDBCriteriaWindow.setAllChoices(vandbfilelogs)
        self._vanDBCriteriaWindow.setDefaults(config.defaultVanDBCriteria)
        self._vanDBCriteriaWindow.show()

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

def getHomeDir():
    """ Get home directory
    """ 
    if sys.platform == 'win32': 
        home = os.path.expanduser("~") 
    else: 
        home=os.getenv("HOME") 
        
    return home
