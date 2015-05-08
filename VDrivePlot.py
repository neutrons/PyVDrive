#!/usr/bin/python

#import utility modules
import sys
import os

#import PyQt modules
from PyQt4 import QtGui, QtCore, Qt

#include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

""" import GUI components generated from Qt Designer .ui file """
from ui.ui_MainWindow import *

""" import PyVDrive library """
import Ui_VDrive as vdrive

import ui.Window_ReductionSetup as rdwn
import ui.Dialog_NewProject as npj
import ui.Dialog_AppLog as dlglog
import ui.Dialog_SelectRuns as dlgsr

import config
import PyVDrive.vdrive.FacilityUtil as futil

class VDrivePlot(QtGui.QMainWindow):
    """ Main GUI class for VDrive 
    """ 
    # Define signals to child windows as None(s) 
    myLogSignal = QtCore.pyqtSignal(str)
    mySideBarSignal = QtCore.pyqtSignal(str)
    
    #initialize app
    def __init__(self, parent=None):
        """ Init
        """
        #setup main window
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("VDrivePlot Main")
        self.ui = Ui_MainWindow() #defined in ui_AppTemplate.py
        self.ui.setupUi(self)

        #-----------------------------------------------------------------------
        # Defining status variables
        #-----------------------------------------------------------------------
        # new project
        self._myWorkflow = vdrive.VDriveAPI()

        # statis variables
        self._tableCurrentProject = None
        
        # controls to the sub windows
        self._openSubWindows = []
        
        #-----------------------------------------------------------------------
        # add action support for menu
        #-----------------------------------------------------------------------
        # submenu 'File'
        self.connect(self.ui.actionFile_New, QtCore.SIGNAL('triggered()'), 
                self.doNewProject)

        self.connect(self.ui.action_OpenProject, QtCore.SIGNAL('triggered()'),
                self.doLoadProject)

        self.connect(self.ui.action_SaveProject, QtCore.SIGNAL('triggered()'),
                self.doSaveProject)

        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'), 
                self.confirmExit)

        # submenu 'Reduction'
        self.connect(self.ui.actionReduction_NewSetup, QtCore.SIGNAL('triggered()'),
                self.doSetupReduction)

        # submenue 'View'
        self.connect(self.ui.actionLog_Window, QtCore.SIGNAL('triggered()'),
                self.doShowAppLog)

        # sub-menu 'Quick Start'
        self.connect(self.ui.actionStart_New_Project, QtCore.SIGNAL('triggered()'),
                self.doNewProject)

        # Project tree widget
        self.connect(self.ui.treeWidget_Project, QtCore.SIGNAL('itemSelectionChanged()'),
            self.doChangeTreeMenu)

        # This is the right way to use right mouse operation for pop-up sub menu 
        addAction = QtGui.QAction('Add', self)
        addAction.triggered.connect(self.doAddFile)
        self.ui.treeWidget_Project.addAction(addAction)
        setupReductionAction = QtGui.QAction('Setup', self)
        setupReductionAction.triggered.connect(self.doSetupReduction)
        self.ui.treeWidget_Project.addAction(setupReductionAction)
        self.ui.treeWidget_Project.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self._treeCurrentLevel = 1

        # App counter
        self.ui.appCntr = 1
    
        #add action exit for File --> Exit menu option
        #self.connect(self.ui.actionExit, QtCore.SIGNAL('triggered()'), self.confirmExit)
        #add signal/slot connection for pushbutton exit request
        #self.connect(self.ui.pushButtonExit, QtCore.SIGNAL('clicked()'), self.confirmExit)


        # Child windows
        self._myLogDialog = None
        self._reductionWindow = None

        # Close signal
        self._closeFromAction = False

        # Set up defaults
        self._setupDefaults()
        # from the import set some other 
        # self._myWorkflow.setDataPath()

        return


    def _setupDefaults(self):
        """ Set up defaults 
        """
        # # import config module
        # try:
        #     import config
        #     setEmpties = False
        # except ImportError:
        #     setEmpties = True

        # # set defaults
        # if setEmpties is False:
        #     # TODO - THIS PART IS STILL EXPANDING

        #     # data path
        #     for dp in config.defaultDataPath:
        #         if os.path.exists(dp) is True:
        #             self.config["default.BaseDataPath"] = dp
        #             break

        #     # vanadium dabase file
        #     defaultVanDBFiles = config.defaultVanadiumDataBaseFile
        #     for vfile in defaultVanDBFiles:
        #         if os.path.exists(vfile) is True:
        #             self.config["default.VanadiumDataBaseFile"] = vfile
        #             break
        #     # ENDFOR (vfile)

        # # ENDIF

        # print self.config

        return

        
    def closeEvent(self, event=None):
        """
        """
        # close all child windows without prompting for saving and etc. 
        for iws in xrange(len(self._openSubWindows)):
            self._openSubWindows[iws].close()
       
        event.accept()

        return

    def confirmExit(self):
        """ Exit with confirmation
        """
        reply = QtGui.QMessageBox.question(self, 'Message', "Are you sure to quit?", 
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
       
        # FIXME - This cause the modal issue on Mac OSX!
        if reply == QtGui.QMessageBox.Yes:
            #close application 
            self._closeFromAction = True
            self.close()
        else: 
            #do nothing and return
            pass     

        return

    #---------------------------------------------------------------------------
    # Widget event handling methods
    #---------------------------------------------------------------------------
    def doAddFile(self):
        """ Add file
        """
        newdatafiledialog = Dialog_NewRuns()


        print "Add a new file to current project"
        curitem = self.ui.treeWidget_Project.currentItem()
        # 
        print "Add file to ", curitem, " with parent = ", curitem.parent(), " data = ", \
                curitem.data(0,0), " data = ", curitem.text(0), curitem.text(1)
        
        #Add file to  <PyQt4.QtGui.QTreeWidgetItem object at 0x7fe454028f28>

        return

    def doChangeTreeMenu(self):
        """ Change the tree menu if it is on different level
        """
        # identify whether the tree level will be changed or not
        currTreeItem = self.ui.treeWidget_Project.currentItem()
        col0 = str(currTreeItem.text(0)).strip()
        col1 = str(currTreeItem.text(1)).strip()
        print "Item is changed: ", str(col0), str(col1)

        if len(col0) == 0 and len(col1) > 0:
            currLevel = 2
        elif len(col1) == 0 and len(col0) > 0:
            currLevel = 1
        else:
            raise NotImplementedError("This is an unsupported and weird case.")

        # return if there is no change in level
        if currLevel == self._treeCurrentLevel:
            return

        # reset 
        self._treeCurrentLevel = currLevel
        self._clearTreeActions()

        if self._treeCurrentLevel == 1:
            self._setTreeLevel1Actions()
        else:
            self._setTreeLevel2Actions()

        return
        
    def doDeleteRunFromProjTree(self):
        """ Delete a run from a project from the project tree
        """
        # Delete runs from a project
        projectname, run = self._getCurrentProjectFromTree()

        self._myWorflow.deleteRunFromProject(projectname, run)

        return

            
    def doLoadProject(self):
        """ Load a project with prompt
        """
        self._addLogInformation("User plans to load a project from a file.")

        # Launch a a window for file name: this is a blocking session
        continueselect = True
        curdir = os.curdir
        while continueselect is True:
            filter="All files (*.*);;Pickle (*.p);;NXSPE (*.nxspe)" 
            fileList = QtGui.QFileDialog.getOpenFileNames(self, 'Open File(s)', curdir,filter)
            print [str(file) for file in fileList]
            if len(fileList) == 1:
                continueselect = False

        # Load
        self._addLogInformation("Loading project file %s." % (fileList[0]))
        status, rvalue = self._myWorkflow.loadProject(fileList[0])
        if status is True:
            projtype, projname = rvalue
        else:
            self._myWorkflow.addLogError("Loading project error due to %s" % (rvalue))
            return

        # added to project tree
        project_item = QtGui.QTreeWidgetItem(self.ui.treeWidget_Project, [projname, ""])
        self.ui.treeWidget_Project.expandItem(project_item) 

        # initialize the table widget
        self._initReductionProjectTable(projname)

        return

    def doNewProject(self):
        """ New reduction project
        """
        import time
        from multiprocessing import Process
        
        print "A new reduction project is to be created and added to project tree"
        
        self.newprojectname = None  
        self.newprojectname = None
        
        # Launch dialog for project name
        self.projnamewindow = npj.MyProjectNameWindow(self)
        self.projnamewindow.show()

        if self.newprojectname == "%6--0$22":
            print "User aborts the operation to create a new reduction project"
        else:
            print "New project name is ", self.newprojectname
        
        return

    def doSaveProject(self):
        """ Load a project with prompt
        """
        self._addLogInformation("User plans to save a project to a file.")

        # Find out which project to save
        # FIXME - a method???
        curitem = self.ui.treeWidget_Project.currentItem()
        projectname = str(curitem.text(0))

        # Get file name to save
        curdir = os.curdir
        filter="Pickle (*.p);;NXSPE (*.nxspe)" 
        sfile = str(QtGui.QFileDialog.getSaveFileName(self, 'Save File', curdir,filter))

        # Save
        self._addLogInformation("About to saving project %s to %s. " % (projectname, sfile))
        status, errmsg = self._myWorkflow.saveProject('r', projectname, sfile)

        self._addLogInformation("Save project = %s; Error: %s." % (str(status), errmsg))

        return
         
    def doSetupReduction(self, automode=False, project="", ipts=None, runstart=None, runend=None):
        """ Lauch reduction setup window with optional preset

        Arguments: 
         - automode :: Boolean default as false
         - project  :: string as project name
         - ipts     :: IPTS number
         - runstart :: integer as staring run number
         - runend   :: integer as ending run number
        """
        # Create and set up reduction window
        if self._reductionWindow is None: 
            self._reductionWindow = rdwn.MyReductionWindow(self, self._myWorkflow._myConfig) 
            self._reductionWindow.resize(1200, 800)

            projnames = sorted(self._myWorkflow.getProjectNames())

            self._reductionWindow.setProjectNames(projnames) 
            self._registerSubWindow(self._reductionWindow)

        # Find out which project to save
        # FIXME - a method???
        curitem = self.ui.treeWidget_Project.currentItem()
        if curitem is not None: 
            currprojname = str(curitem.text(0)) 
            status, errmsg = self._reductionWindow.setCurrentProject(currprojname) 
            self._addLogInformation(errmsg)
        else:
            print "[Log Warning] No project in tree widget is set."

        # Auto mode
        if automode is True:
            self._reductionWindow.setupAutoFileAddMode(project, ipts, runstart, runend)
        
        # show
        self._reductionWindow.show()

        return

    def doShowAppLog(self):
        """ Show App Log
        """
        # 2 status
        self._logDebug("Action log window is checked = ", self.ui.actionLog_Window.isChecked())
        # NOTE: this method is called after the action.  so if it is not checked before.  after it is clicked,
        #       the state is changed to isChecked() = True
        if self.ui.actionLog_Window.isChecked() is True:
            # show window 
            if self._myLogDialog is None:
                # create log and lauch
                self._myLogDialog = dlglog.MyAppLogDialog(self)
                self.myLogSignal.connect(self._myLogDialog.setText)
            self._myLogDialog.show()
            self._registerSubWindow(self._myLogDialog)

        else:
            # close
            if self._myLogDialog is not None:
                self._myLogDialog.close()
            else:
                raise NotImplementedError("State machine error for AppLogDialog")

        return


    #---------------------------------------------------------------------------
    # Event handling methods
    #---------------------------------------------------------------------------
    @QtCore.pyqtSlot(str, list)
    def evtAddRuns(self, projname, datacallist):
        """
        Arguments: 
         - projname :: string as project name
         - datacallist :: data/van run list
        """
        runsadded = []

        for datafile, calrun in datacallist:
            # add to list 
            runsadded.append(datafile)

            # set to project
            self._myWorkflow.setCalibration(projname, datafile, calrun)
        # ENDFOR
        
        self._treeAddRuns(projname, runsadded)
        self._tableAddRuns(projname, datacallist)

        return

    # add slot for NewProject signal to connect to
    @QtCore.pyqtSlot(int) 
    def evtCreateReductionProject(self, val):
        """ New reduction project as a call from a secondary window
        """
        # Information output
        prepend = "NewProject_" + str(val) + ": "
        print "[INFO] Got signal from 'NewProject' as %s.  New project name = %s of type %s." % (prepend,
                self.newprojectname, self.newprojecttype)

        # Initlalize a new project and register
        self._myWorkflow.newProject(projname = self.newprojectname, projtype = self.newprojecttype)

        # Added to project tree
        newprojectwidget = QtGui.QTreeWidgetItem(self.ui.treeWidget_Project, [self.newprojectname, ""])
        self.ui.treeWidget_Project.expandItem(newprojectwidget) 

        # Add runs if the given project name is a valid IPTS number by NEW WINDOW
        # NOTE: Feature to add files automatically will launch another window.  Thus it is better to 
        #       put it in GUI rather than workflow control class
        if self.newprojectname.lower().startswith('ipts') is True: 
            ipts = None
            deltaD = int(val)
            if self.newprojectname[4].isdigit() is True:
                try: 
                    ipts = int(self.newprojectname[4:])
                except ValueError:
                    self._logError("Unable to convert %s to IPTS number." % (self.newprojectname[4:]))
            else:
                try: 
                    ipts = int(self.newprojectname[5:])
                except ValueError:
                    self._logError("Unable to convert %s to IPTS number." % (self.newprojectname[5:]))
            
            if ipts is not None:
                status, errmsg = self._myWorkflow.searchFilesIPTS(self.newprojectname, ipts, deltaD)
                if status is True:
                    self.showIPTSFileWindow(self.newprojectname, ipts)
            # ENDIF
        else:
            # Show reduction window
            self.doSetupReduction()
        # ENDIF

        return
    
    @QtCore.pyqtSlot(list)
    def evtSetupShowReductionWindow(self, val):
        """ Event handling to set up and show reduction window
        Requiring: (1) project name; (2) range of runs
        """
        # Parse signal
        projname = val[0]
        ipts = val[1] 
        numrunset = len(val)-2
        print "[DB] %d sets of runs are selected." % (numrunset)

        gui_runstart = 1000000000000
        gui_runend = 0
        for i in xrange(numrunset):
            # parse signal
            runstart = val[i+2][0]
            runend = val[i+2][1]
            # add runs/files to project
            self._myWorkflow.addAutoFoundRuns(projname, ipts, runstart)
            # update gui run range
            if runstart < gui_runstart:
                gui_runstart = runstart
            if runend > gui_runend:
                gui_runend = runend

            print "[DB] Auto IPTS Search: Run from %d to %d." % (runstart, runend)
        # ENDFOR

        # Launch reduction window
        self.doSetupReduction(automode=True, project=projname, ipts=ipts, 
                runstart=gui_runstart, runend=gui_runend)

        # Add files to project tree
        execstatus, errmsg, datafilepairlist = self._myWorkflow.getDataFiles(projname)
        runslist = []
        for dpair in datafilepairlist:
            print dpair
            runslist.append(dpair[0])

        if execstatus is True: 
            self._treeAddRuns(projname, runslist, usebasefilename=True)
            self._tableAddRuns(projname, runslist)
        else:
            self._logError(errmsg) 
        
        return


    #---------------------------------------------------------------------------
    # Methods to get information from Main GUI 
    # Implemented for child-windows/dialogs
    #---------------------------------------------------------------------------
    def getLogText(self):
        """ 
        """
        # TODO - ASAP
        self._myLogList = []

        return "IMPLEMENT ASAP"


    def getReductionList(self, selectedlist=None):
        """ Get the data to reduce from reduction table

        Return :: list of 2-tuple (data file name, reduce?)
        """
        reductionlist = []

        numrows = self.ui.tableWidget_generalInfo.rowCount()
        for irow in xrange(numrows):
            # get the checkbox widget to see whether it is to get reduced
            reducewidget = self.ui.tableWidget_generalInfo.cellWidget(irow, 2)
            # date file
            datafname = str(self.ui.tableWidget_generalInfo.item(irow, 0).text())

            # override
            doreduce = False
            if selectedlist is not None: 
                ipts, runnumber = futil.getIptsRunFromFileName(datafname)
                print "check run %d in file %s within list %s." % (runnumber, datafname, str(selectedlist))
                if runnumber in selectedlist:
                    doreduce = True
                    reducewidget.setChecked(True)
                # ENDIF
            # ENDIF

            if doreduce is False: 
                doreduce = reducewidget.isChecked()

            # read cell 0 and 1
            # NOTE : van run is not needed here.  It is just for information for user
            # vanrun = str(self.ui.tableWidget_generalInfo.item(irow, 1).text())
            # if vanrun.isdigit() is True:
            #     vanrun = int(vanrun)
            # else:
            #     vanrun = None

            # add to output list
            reductionlist.append( (datafname, doreduce) )
            # EDNDIF
        # ENFOR
                
        return reductionlist


    def getReductionProjectNames(self):
        """ Get the names of all reduction projects
        """
        return self._myWorkflow.getReductionProjectNames()


    def getWorkflowObj(self):
        """ Get my controller workflow object
        It is mostly used by its children
        """
        return self._myWorkflow

    
    #---------------------------------------------------------------------------
    # Others..
    #---------------------------------------------------------------------------
    def projectOperation(self):
        """
        """
        print "Project is pressed"

        # This is how to created a popup menu
        self.menu = QtGui.QMenu(self)
        addAction = QtGui.QAction('Add File', self)
        addAction.triggered.connect(self.doAddFile)
        self.menu.addAction(addAction)

        renameAction = QtGui.QAction('Rename', self)
        renameAction.triggered.connect(self.renameSlot)
        self.menu.addAction(renameAction)
        self.menu.popup(QtGui.QCursor.pos())

        curitem = self.ui.treeWidget_Project.currentItem()
        print curitem

        return


    def renameSlot(self):
        print "Renaming slot called"



    def showIPTSFileWindow(self, projname, ipts):
        """ Show the child window for files/runs belonged to an IPTS

        Arguments: 
         - ipts :: int for IPTS
        """
        # Start a new window and register it
        self._iptsRunWindow = dlgsr.SelectRunsDialog(self)
        self._registerSubWindow(self._iptsRunWindow)

        # Append rows: each row is a period of experiments
        self._iptsRunWindow.setRunInfo(projname, ipts)

        runinfolist = self._myWorkflow.getIptsRunInfo(ipts)
        for rinfo in runinfolist:
            print "[DB] IPTS-Run Info: ", rinfo
            self._iptsRunWindow.appendRow(rinfo[0], rinfo[1], rinfo[2], rinfo[3], True)

        # Show window
        self._iptsRunWindow.show()


        return


    def showProjectNameWindow(self, signal):
        """
        """           
        self._projnamewindow = npj.MyProjectNameWindow(None)
        self._projnamewindow.show() 
        self._registerSubWindow(self._projnamewindow)
    
        return


    #------------------------------------------
    # Reduction related event handlers
    #------------------------------------------
    def setRuns(self, projname, ipts, runs, autofindcal):
        """ Add runs to a project

        Return :: a list of 2-tuple (string as file name, list of van run/None)
        """
        status, errmsg, datafilesets = \
                self._myWorkflow.addExperimentRuns(projname = projname, 
                                                   operation ='reduction', 
                                                   ipts = ipts, 
                                                   runnumberlist = runs, 
                                                   autofindcal = autofindcal)
        # addExperimentRuns(self, projname, operation, ipts, runnumberlist, autofindcal):

        if status is False:
            self._addLogError(errmsg)
            return
        
        # self._tmpIPTS = ipts
        # self._tmpRuns = runs

        return datafilesets


    #---------------------------------------------------------------------------
    # Private methods 
    #---------------------------------------------------------------------------
    def _addLogInformation(self, logstr):
        """ Add log at information level
        """
        self._myWorkflow.addLogInformation(logstr)

        # Emit signal to parent
        if self.myLogSignal is not None: 
            sigVal = logstr
            self.myLogSignal.emit(sigVal)

        print "---> Should send out a signal to update log window: %s." % (logstr)

        return


    def _addLogError(self, logstr):
        """ Add log at information level
        """
        self._myWorkflow.addLogInformation(logstr)

        # Emit signal to parent
        if self.myLogSignal is not None: 
            sigVal = logstr
            self.myLogSignal.emit(sigVal)

        print "---> Should send out a signal to update log window: %s." % (logstr)

        return


    def _clearTreeActions(self):
        """ Clear all the actions of the tree widget
        """
        actions = self.ui.treeWidget_Project.actions()
        for action in actions:
            print action.whatsThis(), " | ", action.text()
            self.ui.treeWidget_Project.removeAction(action)
        # ENDFOR (action)
        
        return
        
    def _exitApp(self):
        """ Close all the child windows before 
        """
        # FIXME - Who called me???
        raise NotImplementedError("Who calls me?")

        return
        

    def _initReductionProjectTable(self, projname):
        """ Initialize reduction project table: 
        Widget: (1) self.ui.tableWidget_generalInfo
        """
        # load project
        status, errmsg, datapairlist = self._myWorkflow.getDataFiles(projname)
        if status is False:
            self._addLogInformation(errmsg)
            return
        
        # get some information
        numrows = len(datapairlist)

        # clear
        self.ui.tableWidget_generalInfo.setRowCount(0)
        self.ui.tableWidget_generalInfo.setColumnCount(0)

        # init
        self.ui.tableWidget_generalInfo.setHorizontalHeaderLabels(['File', 'Van Run', 'Reduce'])
        tmpHdr=['Log Name','Status', 'Type']
        NHdrs=len(tmpHdr)
        HzHeaders=['']*NHdrs
        HzHeaders[0] = tmpHdr[0]
        HzHeaders[1] = tmpHdr[1]
        HzHeaders[2] = tmpHdr[2]

        self.ui.tableWidget_generalInfo.setHorizontalHeaderLabels(HzHeaders)
        self.ui.tableWidget_generalInfo.setColumnCount(3)

        self.ui.tableWidget_generalInfo.setColumnCount(3)
        self.ui.tableWidget_generalInfo.setRowCount(numrows)
       
        # set values
        if numrows == 0:
            self._addLogInformation("There is no data file that has been added to project %s yet." % (projname))
            return
        else:
            self._addLogInformation("There are %d data files that have been added to project %s." % (numrows, projname))

        # set to table
        self._tableAddRuns(projname, datapairlist)

        return

    def _registerSubWindow(self, windowobj):
        """ Register a child window for VDrivePlot
        """
        # Check whether this window has been registered
        if self._openSubWindows.count(windowobj) > 0:
            self._logError("Child window has been appended to child windows list already.")
            raise RuntimeError("Programming error for registering one window twice.")

        self._openSubWindows.append(windowobj)

        return


    def _setTreeLevel1Actions(self):         
        """ Set project level actions for project tree
        """
        # This is the right way to use right mouse operation for pop-up sub menu 
        addAction = QtGui.QAction('Add', self)
        addAction.triggered.connect(self.doAddFile)
        self.ui.treeWidget_Project.addAction(addAction)
        setupReductionAction = QtGui.QAction('Setup', self)
        setupReductionAction.triggered.connect(self.doSetupReduction)
        self.ui.treeWidget_Project.addAction(setupReductionAction)
        #self.ui.treeWidget_Project.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        
        return

    def _setTreeLevel2Actions(self):         
        """ Set run level actions for project tree
        """
        # This is the right way to use right mouse operation for pop-up sub menu 
        delAction = QtGui.QAction('Delete (Run)', self)
        delAction.triggered.connect(self.doDeleteRunFromProjTree)
        self.ui.treeWidget_Project.addAction(delAction)

        return

    def _setTreeLevel1Actions_duplicate(self):         
        """
        """
        # This is the right way to use right mouse operation for pop-up sub menu 
        addAction = QtGui.QAction('Add', self)
        addAction.triggered.connect(self.doAddFile)
        self.ui.treeWidget_Project.addAction(addAction)
        setupReductionAction = QtGui.QAction('Setup', self)
        setupReductionAction.triggered.connect(self.doSetupReduction)
        self.ui.treeWidget_Project.addAction(setupReductionAction)
        #self.ui.treeWidget_Project.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        
        return

    def _tableAddRuns(self, projname, datapairlist, selectAll=None):
        """ Add new runs to table: self.ui.tableWidget_generalInfo.

        Argument:
         - projname ::
         - datapairlist :: list of pair of (data file and run)
        """
        # Create the table if it does not exist
        if self._tableCurrentProject is None:
            # Initialize
            self._tableCurrentProject = projname
        
            # Clear
            self.ui.tableWidget_generalInfo.setRowCount(0)
            self.ui.tableWidget_generalInfo.setColumnCount(10)

            # Setup the table
            self.ui.tableWidget_generalInfo.setColumnCount(3)
            headerlist = ['Run/Data File', 'Vanadium Run', 'Reduce']
            self.ui.tableWidget_generalInfo.setHorizontalHeaderLabels(headerlist)
            # FIXME - Only work for reductionp project
        # ENDIF

        # check project name
        if projname != self._tableCurrentProject:
            raise NotImplementedError("[DB1248] Need to implement the algorithm \
                    to switch between projects.")

        # Set lines
        numrows = self.ui.tableWidget_generalInfo.rowCount()
        numrows += len(datapairlist)
        self.ui.tableWidget_generalInfo.setRowCount(numrows)

        # Set rows
        iline = 0
        for datapair in datapairlist:
            # data 
        
            # accept 2 situation
            if isinstance(datapair, str):
                run = datapair
                vanrun = None
            elif isinstance(datapair, list) or isinstance(datapair, tuple):
                run = datapair[0]
                vanrun = datapair[1]

            item = QtGui.QTableWidgetItem()
            item.setText(run)
            self.ui.tableWidget_generalInfo.setItem(iline, 0, item)

            # van run to calibrate
            item = QtGui.QTableWidgetItem()

            if vanrun is None:
                item.setText("") 
            else:
                item.setText(str(vanrun))
            self.ui.tableWidget_generalInfo.setItem(iline, 1, item)

            # set reduce check box
            if selectAll is None:
                # Auto decide to select all or not
                if vanrun is None:
                    state = False
                else:
                    state = True
            else:
                state = bool(selectAll)
            addCheckboxToWSTCell(self.ui.tableWidget_generalInfo, iline, 2, state)

            iline += 1
        # ENDFOR(datapair)

        # Resize column width
        self.ui.tableWidget_generalInfo.resizeColumnsToContents()

        return

    def _treeAddRuns(self, projname, runsadded, usebasefilename=True):
        """ Add runs/file names to reduce to the tree widget
        """
        # NOTE: The procedure to add items to tree is 
        #       1. create a new QTreeWidgetItem with parent set up (a<--b)
        #       2. call the QTreeWidget (the root) to expandItem   (a-->b)

        curitem = self.ui.treeWidget_Project.currentItem()
        print "[DB] Project-Tree: current item = ", str(curitem)

        # Set the current item if never set up
        if curitem is None:
            treewidgetlist = self.ui.treeWidget_Project.findItems(projname, QtCore.Qt.MatchRegExp, column=0)
            if len(treewidgetlist) == 0:
                item00 = self.ui.treeWidget_Project.itemAt(0, 0)
                text00 = item00.text()
                print "[DB] No matched item found in project-tree '%s'." % (str(text00))
            elif len(treewidgetlist) > 1:
                print "[DB] How come more than 1 matched?"

            curitem = treewidgetlist[0]
        # ENDIF

        if len(runsadded) == 0:
            self._addLogInformation("No run is found and added to project %s." % (projname))
            print "No run is found and added to project %s." % (projname)

        #for run in sorted(runsadded):
        for run in sorted(runsadded):
            if usebasefilename is True:
                run = os.path.basename(run)

            newrunw = QtGui.QTreeWidgetItem(curitem, ["", run])
            self.ui.treeWidget_Project.expandItem(newrunw)

        return



#-------------------------------------------------------------------------
# External methods
#-------------------------------------------------------------------------
def addCheckboxToWSTCell(table, row, col, state):
    #function to add a new select checkbox to a cell in a table row
    #won't add a new checkbox if one already exists
    if state == '':
        state=False
    #check if cellWidget exitst
    if table.cellWidget(row,col) != None:
        table.cellWidget(row,col).setChecked(state)
    else:
        #case to add checkbox

        checkbox = QtGui.QCheckBox()
        checkbox.setText('Select')
        checkbox.setChecked(state)
        
        #adding a widget which will be inserted into the table cell
        #then centering the checkbox within this widget which in turn,
        #centers it within the table column :-)
        QW=QtGui.QWidget()
        cbLayout=QtGui.QHBoxLayout(QW)
        cbLayout.addWidget(checkbox)
        cbLayout.setAlignment(QtCore.Qt.AlignCenter)
        cbLayout.setContentsMargins(0,0,0,0)
        table.setCellWidget(row,col, checkbox) #if just adding the checkbox directly

    return
    
if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = VDrivePlot()
    myapp.show()

    exit_code=app.exec_()
    #print "exit code: ",exit_code
    sys.exit(exit_code)
