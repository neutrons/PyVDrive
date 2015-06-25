################################################################################
# Test of GUI for Striping Vanadium Peaks
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
    myapp.show()
    
    # Test section
    
    # step 1: create new reduction project
    myapp.doNewProject()
    myapp.projnamewindow.ui.lineEdit.setText('TestStripVPeaksProj')
    myapp.projnamewindow.quitCreateNew()
    time.sleep(0.1)
    
    # step 2: launch a new redcution window
    myapp.doSetupReduction()
    myapp._reductionWindow.setCurrentProject('TestStripVPeaksProj')
    myapp._reductionWindow.ui.tab_calibSetup.setCurrentIndex(0)
    
    # 2.0 Set up a V-run IPTS-12180, Run-64928 
    #     Options: 	 IPTS-11285, Run-64315
    myapp._reductionWindow.ui.lineEdit_ipts.setText('12180')
    myapp._reductionWindow.ui.lineEdit_runstart.setText('64928')
    myapp._reductionWindow.ui.lineEdit_runend.setText('')
    
    # 2.1 Set up vanadium  (Option is off)
    # myapp._reductionWindow.doBrowseVanDBFile()
    # myapp._reductionWindow._vanDBCriteriaWindow.doSaveQuit()
    
    # 2.2 Add runs: turn off the auto vanadium run setup flag
    myapp._reductionWindow.ui.checkBox_autoVanRun.setChecked(False)
    r = myapp._reductionWindow.doAddRuns()
    if r is False:
        raise NotImplementedError("Test failed!")
    myapp._reductionWindow._myCalibMatchWindow.doSaveQuit()

    # 2.3 Configure reduction parameters
    myapp._reductionWindow.ui.lineEdit_binSize.setText('-0.001')

    # 2.4 Reduce
    myapp._reductionWindow.doReduceData()

    # 3. Prepare processing

    exit_code=app.exec_()

    #print "exit code: ",exit_code
    sys.exit(exit_code)
