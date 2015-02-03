#!/usr/bin/python

#import utility modules
import sys

#import PyQt modules
from PyQt4 import QtGui, QtCore, Qt

#include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

#import GUI components generated from Qt Designer .ui file
from ui.ui_MainWindow import *

#import PyVDrive library
import PyVDrive as vdrive

import ReductionWindow as rdwn
import NewProject as npj

class AppTemplateMain(QtGui.QMainWindow):
    
    #initialize app
    def __init__(self, parent=None):
        #setup main window
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle("App Template Main")
        self.ui = Ui_MainWindow() #defined in ui_AppTemplate.py
        self.ui.setupUi(self)
        
        #-----------------------------------------------------------------------
        # add action support for menu
        #-----------------------------------------------------------------------
        # submenu 'File'
        self.connect(self.ui.actionFile_New_Reduction, QtCore.SIGNAL('triggered()'), 
                self.newReductionProject)

        # submenu 'Reduction'
        self.connect(self.ui.actionReduction_NewSetup, QtCore.SIGNAL('triggered()'),
                self.setupReduction)


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
        setupReductionAction.triggered.connect(self.setupReduction)
        self.ui.treeWidget_Project.addAction(setupReductionAction)
        self.ui.treeWidget_Project.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # App counter
        self.ui.appCntr = 1
    
        #add action exit for File --> Exit menu option
        #self.connect(self.ui.actionExit, QtCore.SIGNAL('triggered()'), self.confirmExit)
        #add signal/slot connection for pushbutton exit request
        #self.connect(self.ui.pushButtonExit, QtCore.SIGNAL('clicked()'), self.confirmExit)
        
    def confirmExit(self):
        reply = QtGui.QMessageBox.question(self, 'Message', "Are you sure to quit?", 
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        
        if reply == QtGui.QMessageBox.Yes:
        #close application
            self.close()
        else:
        #do nothing and return
            pass     
            
    def newReductionProject(self):
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
        """
        """
        import PyVDrive as pvdrive

        prepend = "NewProject" + str(val) + ": "
        print "Got signal from 'NewProject' as %s.  New project name = %s." % (prepend,
                self.newprojectname)

        # new project
        myworkflow = pvdrive.PyVDrive()

        # initlalize a new project
        myworkflow.newProject(projname = self.newprojectname, projtype = "reduction")
      
        project1 = QtGui.QTreeWidgetItem(self.ui.treeWidget_Project, [self.newprojectname, ""])
        self.ui.treeWidget_Project.expandItem(project1) 

        return

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
        
            
    def showMenuMessage1(self):
        """ 
        """
        print "Hello!  Reduction is selected!"
       

    def setupReduction(self):
        """
        """
        print "Hello! Reduction is selected in menu bar."
    
        # lauch window
        self._reductionWindow = rdwn.MyReductionWindow()
        self._reductionWindow.show()

        return
        
        
    def showProjectNameWindow(self, signal):
        """
        """           
        print "Good....", signal
        projnamewindow = npj.MyProjectNameWindow(None)
        projnamewindow.show()
    
        return
    
if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = AppTemplateMain()
    myapp.show()

    exit_code=app.exec_()
    #print "exit code: ",exit_code
    sys.exit(exit_code)
