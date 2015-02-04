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
    def __init__(self):
        """ Init
        """
        QWidget.__init__(self)


        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #QtCore.QObject.connect(self.ui.pushButton_quit, QtCore.SIGNAL('clicked()'), self.quit)

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