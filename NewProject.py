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
    def __init__(self, parent):
        """ Init
        """
        QWidget.__init__(self)

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        print "Initalized"
        
        self.myParent = parent
        
        # Set event handler
        QtCore.QObject.connect(self.ui.pushButton, QtCore.SIGNAL('clicked()'),
            self.quitCreateNew)

        #QtCore.QObject.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'), self.quit)
        
        
    def quitCreateNew(self):
        """ Quit for creating new project
        """
        projectanme = str(elf.ui.lineEdit.text())
        if len(projectname) == 0:
            projectname = "new project"
        
        #self.myParent.newprojectname = projectname
        
        self.close()
        
        return

    def setMessage(self, errmsg):
        """ Set message
        """
        #self.ui.label_errmsg.setWordWrap(True)
        #self.ui.label_errmsg.setText(errmsg)

        return


    def quit(self):
        """ Quit
        """
        #self.close()

        return