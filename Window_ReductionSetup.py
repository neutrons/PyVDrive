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

class MyReductionWindow(QWidget):
    """ Pop up dialog window
    """
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
                QtCore.SIGNAL('clicked()'), self.selectProject)

        # add runs/file for reduction
        QtCore.QObject.connect(self.ui.pushButton_addRuns,
                QtCore.SIGNAL('clicked()'), self.addRuns)


        # quit
        QtCore.QObject.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'), self.quit)

        #---------------------------------
        # Setup GUI event handlers
        #---------------------------------
        self.ui.comboBox_projectNames.addItems(self._myParent.getReductionProjectNames())


    def setMessage(self, errmsg):
        """ Set message
        """
        #self.ui.label_errmsg.setWordWrap(True)
        #self.ui.label_errmsg.setText(errmsg)

        return


    def selectProject(self):
        """ select projects by name
        """
        projname = self.ui.comboBox_projectNames.currentText()
        print "Project %s is selected. " % (str(projname))

        return


    def addRuns(self):
        """ add IPTS-run numbers to 
        """
        # get data from GUI
        ipts = str(self.ui.lineEdit_ipts.text())
        runstart = str(self.ui.lineEdit_runstart.text())
        runend = str(self.ui.lineEdit_runstart.text())

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
            runnumberlist.append(range(int(runstart), int(runend)+1))

        logmsg = "Adding ITPS-%d runs: %s. " % (ipts, str(runnumberlist))
            



    def quit(self):
        """ Quit
        """
        self.close()

        return
