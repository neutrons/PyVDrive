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
        
        # add action support for menu
        self.connect(self.ui.actionReduction_Project, QtCore.SIGNAL('triggered()'), 
            self.newReductionProject)
        
        
        self.connect(self.ui.actionNewReduction, QtCore.SIGNAL('triggered()'), self.showReductionWndow)
    
        #add action exit for File --> Exit menu option
        #self.connect(self.ui.actionExit, QtCore.SIGNAL('triggered()'), self.confirmExit)
        #add signal/slot connection for pushbutton exit request
        #self.connect(self.ui.pushButtonExit, QtCore.SIGNAL('clicked()'), self.confirmExit)
        
    def confirmExit(self):
        reply = QtGui.QMessageBox.question(self, 'Message',
        "Are you sure to quit?", QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        
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
        # FIXME - this multithreading also fails
        # p = Process(target=self.showProjectNameWindow, args=('good',))
        # p.start()
        # p.join()
        
        
        self.projnamewindow = npj.MyProjectNameWindow(self)
        self.projnamewindow.show()
        
        # wait: this is not good!  
        # FIXME - the window does not launch after show().  It might be launched after this method is returned? 
        # TODO  - solution? multiple thread? 
        icount = 0
        while self.newprojectname is None:
            time.sleep(1)
            icount += 1
            if icount > 3:
                break
        
        print "New project name = ", self.newprojectname
        
        return
        
        
            
    def showMenuMessage1(self):
        """ 
        """
        print "Hello!  Reduction is selected!"
        
        
    def showReductionWndow(self):
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
