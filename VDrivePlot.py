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

import Window_ReductionSetup as rdwn
import Dialog_NewProject as npj
import Dialog_AppLog as dlglog

class VDrivePlot(QtGui.QMainWindow):
    """ Main GUI class for VDrive 
    """ 
    # Define signals to child windows as None(s) 
    myLogSignal = QtCore.pyqtSignal(str)
    
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

        # controls to the sub windows
        self._openSubWindows = []
        
        #-----------------------------------------------------------------------
        # add action support for menu
        #-----------------------------------------------------------------------
        # submenu 'File'
        self.connect(self.ui.actionFile_New_Reduction, QtCore.SIGNAL('triggered()'), 
                self.doNewReductionProject)

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


        # Project tree widget
        #        self.connect(self.ui.treeWidget_Project, QtCore.SIGNAL('mousePressEvent()'),
        #                self.projectOperation)
        #        self.connect(self.ui.treeWidget_Project, QtCore.SIGNAL('itemPressed()'),
        #                self.projectOperation)
        #        self.connect(self.ui.treeWidget_Project, QtCore.SIGNAL('itemClicked()'),
        #                self.projectOperation)
        #
        #        self.connect(self.ui.treeWidget_Project, QtCore.SIGNAL('itemSelectionChanged()'),
        #                self.projectOperation)
        #
        # This is the right way to use right mouse operation for pop-up sub menu 
        addAction = QtGui.QAction('Add', self)
        addAction.triggered.connect(self.addFile)
        self.ui.treeWidget_Project.addAction(addAction)
        setupReductionAction = QtGui.QAction('Setup', self)
        setupReductionAction.triggered.connect(self.doSetupReduction)
        self.ui.treeWidget_Project.addAction(setupReductionAction)
        self.ui.treeWidget_Project.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # App counter
        self.ui.appCntr = 1
    
        #add action exit for File --> Exit menu option
        #self.connect(self.ui.actionExit, QtCore.SIGNAL('triggered()'), self.confirmExit)
        #add signal/slot connection for pushbutton exit request
        #self.connect(self.ui.pushButtonExit, QtCore.SIGNAL('clicked()'), self.confirmExit)


        # Child windows
        self._myLogDialog = None
        self._reductionWindow = None


        return

        
    def confirmExit(self):
        reply = QtGui.QMessageBox.question(self, 'Message', "Are you sure to quit?", 
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        
        for iws in xrange(len(self._openSubWindows)):
            self._openSubWindows[iws].close()

        if reply == QtGui.QMessageBox.Yes:
        #close application
            self.close()
        else:
        #do nothing and return
            pass     


    #------------ New projects -----------------------------------------------------
            
    def doNewReductionProject(self):
        """ New reduction project
        """
        import time
        from multiprocessing import Process
        
        print "A new reduction project is to be created and added to project tree"
        
        self.newprojectname = None  
        
        # Launch dialog for project name
        self.projnamewindow = npj.MyProjectNameWindow(self)
        self.projnamewindow.show()

        # Wait for user to input
        # waitforuser = True
        # while waitforuser is True:
        #     if self.newprojectname is None:
        #         time.sleep(1)
        #     else:
        #         waitforuser = False

        if self.newprojectname == "%6--0$22":
            print "User aborts the operation to create a new reduction project"
        else:
            print "New project name is ", self.newprojectname
        
        return

    # add slot for NewProject signal to connect to
    @QtCore.pyqtSlot(int)
    def newReductionProject_Step2(self, val):
        """ New reduction project as a call from a secondary window
        """
        prepend = "NewProject" + str(val) + ": "
        print "Got signal from 'NewProject' as %s.  New project name = %s." % (prepend,
                self.newprojectname)


        # initlalize a new project and register
        self._myWorkflow.newProject(projname = self.newprojectname, projtype = "reduction")

        # added to project tree
        project1 = QtGui.QTreeWidgetItem(self.ui.treeWidget_Project, [self.newprojectname, ""])
        self.ui.treeWidget_Project.expandItem(project1) 

        return

    #------------ END New projects -------------------------------------------------

    #------------ Load & Save projects ----------------------------------------------------
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
         

    #------------ END Load projects ------------------------------------------------


    def getReductionProjectNames(self):
        """ Get the names of all reduction projects
        """
        return self._myWorkflow.getReductionProjectNames()

    def projectOperation(self):
        """
        """
        print "Project is pressed"

        # This is how to created a popup menu
        self.menu = QtGui.QMenu(self)
        addAction = QtGui.QAction('Add File', self)
        addAction.triggered.connect(self.addFile)
        self.menu.addAction(addAction)

        renameAction = QtGui.QAction('Rename', self)
        renameAction.triggered.connect(self.renameSlot)
        self.menu.addAction(renameAction)
        self.menu.popup(QtGui.QCursor.pos())

        curitem = self.ui.treeWidget_Project.currentItem()
        print curitem

        return


    def addFile(self):
        """ Add file
        """
        print "Add a new file to current project"
        curitem = self.ui.treeWidget_Project.currentItem()
        # 
        print "Add file to ", curitem, " with parent = ", curitem.parent(), " data = ", curitem.data(0,0), " data = ", curitem.text(0), curitem.text(1)
        
        #Add file to  <PyQt4.QtGui.QTreeWidgetItem object at 0x7fe454028f28>

        return


    def renameSlot(self):
        print "Renaming slot called"
        

    def doSetupReduction(self):
        """ Lauch reduction setup window
        """
        print "Hello! Reduction is selected in menu bar."
    
        # create and setup
        if self._reductionWindow is None: 
            self._reductionWindow = rdwn.MyReductionWindow(self) 

            projnames = sorted(self._myWorkflow.getProjectNames())

            self._reductionWindow.setProjectNames(projnames) 
            self._openSubWindows.append(self._reductionWindow)

        # Find out which project to save
        # FIXME - a method???
        curitem = self.ui.treeWidget_Project.currentItem()
        if curitem is not None: 
            currprojname = str(curitem.text(0)) 
            status, errmsg = self._reductionWindow.setCurrentProject(currprojname) 
            self._addLogInformation(errmsg)
        
        # show
        self._reductionWindow.show()

        return

    def doShowAppLog(self):
        """ Show App Log
        """
        # 2 status
        print "[DB] action log window is checked = ", self.ui.actionLog_Window.isChecked()
        # NOTE: this method is called after the action.  so if it is not checked before.  after it is clicked,
        #       the state is changed to isChecked() = True
        if self.ui.actionLog_Window.isChecked() is True:
            # show window 
            if self._myLogDialog is None:
                # create log and lauch
                self._myLogDialog = dlglog.MyAppLogDialog(self)
                self.myLogSignal.connect(self._myLogDialog.setText)
            self._myLogDialog.show()

        else:
            # close
            if self._myLogDialog is not None:
                self._myLogDialog.close()
            else:
                raise NotImplementedError("State machine error for AppLogDialog")

        return

        
    def showProjectNameWindow(self, signal):
        """
        """           
        print "Good....", signal
        projnamewindow = npj.MyProjectNameWindow(None)
        projnamewindow.show()
    
        return


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


    def getLogText(self):
        """ 
        """
        self._myLogList = []


    #------------------------------------------
    # Reduction related event handlers
    #------------------------------------------
    def setRuns(self, ipts, runs):
        """
        """
        self._tmpIPTS = ipts
        self._tmpRuns = runs

        return

    @QtCore.pyqtSlot(str)
    def evtAddRuns(self, val):
        """
        Arguments: 
        - val :: string as project name
        """
        # project name
        projname = str(val)

        # runs
        # FIXME - need to add the option to match runs automatically 
        status, result = self._myWorkflow.addExperimentRuns(projname, 'reduction', self._tmpIPTS, self._tmpRuns, False)
        msg = result[0]
        runsadded = result[1]
        self._treeAddRuns(projname, runsadded)

        return

    
if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = VDrivePlot()
    myapp.show()

    exit_code=app.exec_()
    #print "exit code: ",exit_code
    sys.exit(exit_code)
