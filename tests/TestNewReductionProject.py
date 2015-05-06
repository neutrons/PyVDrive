################################################################################
# Test of GUI for Data Reduction of Auto-searching Files With IPTS
################################################################################
import time

#import PyQt modules
from PyQt4 import QtGui, QtCore, Qt

#include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s
    
import sys
sys.path.append("/Users/wzz/Library/Python/2.7/lib/python/site-packages")
    
import PyVDrive
import PyVDrive.VDrivePlot
from PyVDrive import *
    
if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = PyVDrive.VDrivePlot.VDrivePlot()
    
    # Test section
    
    # step 1: create new reduction project
    try:
        myapp.doNewProject()
        myapp.projnamewindow.ui.lineEdit.setText('IPTS_10311')
        #myapp.projnamewindow.quitCreateNew()
        #time.sleep(0.1)

        # add more... ...

    except Exception as e:
        print e
    else:
        myapp.show()
        exit_code=app.exec_()
        sys.exit(exit_code)


    ## step 2: launch a new redcution window
    #myapp.doSetupReduction()
    #myapp._reductionWindow.setCurrentProject('MockNewReductionProj')
    #
    ## 2.0 Set up IPTS, start run and end run
    #myapp._reductionWindow.ui.lineEdit_ipts.setText('10311')
    #myapp._reductionWindow.ui.lineEdit_runstart.setText('57075')
    #myapp._reductionWindow.ui.lineEdit_runend.setText('57100')
    #
    ## 2.1 Set up vanadium 
    #myapp._reductionWindow.doBrowseVanDBFile()
    #myapp._reductionWindow._vanDBCriteriaWindow.doSaveQuit()
    #
    ## 2.2 Add runs
    #myapp._reductionWindow.doAddRuns()

    ## 2.3 Configure reduction parameters
    #myapp._reductionWindow.ui.lineEdit_binSize.setText('-0.001')
    

    #print "exit code: ",exit_code

