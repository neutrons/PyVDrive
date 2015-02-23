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
        
from ui.ui_ProjectNameDialog import *

class MyProjectNameWindow(QWidget):
    """ Pop up dialog window
    """
   
    # establish signal for communication - must be before constructor
    mySignal = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        """ Init
        """
        QWidget.__init__(self)

        # Parent
        self.myParent = parent
        
        # Set up widigets
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
       
        # Set event handler
        QtCore.QObject.connect(self.ui.pushButton, QtCore.SIGNAL('clicked()'),
            self.quitCreateNew)

        QtCore.QObject.connect(self.ui.pushButton_2, QtCore.SIGNAL('clicked()'), self.quitAbort)

        QtCore.QObject.connect(self.ui.lineEdit, QtCore.SIGNAL('returnPressed()'),
                self.quitCreateNew)

        # Customerized event 
        self.mySignal.connect(self.myParent.newReductionProject_Step2)

        return
        
        
    def quitCreateNew(self):
        """ Quit for creating new project
        """
        # project name
        projectname = str(self.ui.lineEdit.text())
        if len(projectname) == 0:
            projectname = "new project"
       
        # project type
        projecttype = str(self.ui.comboBox_projectTypes.currentText()).split()[0].lower()
        
        self.myParent.newprojectname = projectname
        self.myParent.newprojecttype = projecttype

        # Emit signal to parent
        sigVal = 1
        self.mySignal.emit(sigVal)
        
        self.close()
        
        return


    def quitAbort(self):
        """ Quit and abort the operation
        """
        self.myParent.newprojectname = "%6--0$22"

        self.close()

        return
