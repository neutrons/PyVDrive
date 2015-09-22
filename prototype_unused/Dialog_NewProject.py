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
        
from ui_ProjectNameDialog import *

class MyProjectNameWindow(QWidget):
    """ Pop up dialog window for creating a new project
    """
    # establish signal for communication - must be before constructor
    mySignal = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        """ Init
        """
        QWidget.__init__(self)

        # Parent
        self._myParent = parent
        
        # Set up widigets
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
       
        # Set event handler
        QtCore.QObject.connect(self.ui.pushButton_newProject, QtCore.SIGNAL('clicked()'), 
                self.doCreateProjectQuit)

        QtCore.QObject.connect(self.ui.pushButton_2, QtCore.SIGNAL('clicked()'), 
                self.quitAbort)

        QtCore.QObject.connect(self.ui.lineEdit, QtCore.SIGNAL('returnPressed()'),
                self.doCreateProjectQuit)

        # Customerized event 
        self.mySignal.connect(self._myParent.evtCreateReductionProject)

        return
        
        
    def doCreateProjectQuit(self):
        """ Quit for creating new project
        """
        # project name
        projectname = str(self.ui.lineEdit.text())
        if len(projectname) == 0:
            projectname = "new project"
       
        # project type
        projecttype = str(self.ui.comboBox_projectTypes.currentText()).split()[0].lower()
        
        self._myParent.newprojectname = projectname
        self._myParent.newprojecttype = projecttype

        # possible IPTS delta-days
        deltaDay_str = str(self.ui.comboBox_deltaDays.currentText()) 
        if deltaDay_str.startswith('Per Day') is True:
            deltaD = 1
        elif deltaDay_str.startswith('Per Week') is True:
            deltaD = 7
        elif deltaDay_str.startswith('Per Month') is True:
            deltaD = 30
        else:
            raise NotImplementedError("Delta Days %d is not recognized."%(deltaDay_str))

        # Emit signal to parent to create reduction project
        sigVal = deltaD
        self.mySignal.emit(sigVal)
        
        self.close()
        
        return


    def quitAbort(self):
        """ Quit and abort the operation
        """
        self._myParent.newprojectname = "%6--0$22"

        self.close()

        return
