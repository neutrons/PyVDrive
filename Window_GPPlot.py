########################################################################
#
# General-purposed plotting window
#
########################################################################
import sys
import os
import numpy

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import ui.ui_GPPlot

class Window_GPPlot(QMainWindow):
    """ Class for general-puposed plot window
    """
    # class
    def __init__(self, parent=None):
        """ Init
        """
        # call base
        QMainWindow.__init__(self)

        # parent
        self._myParent = parent

        # set up UI
        self.ui = ui.ui_GPPlot.Ui_MainWindow()
        self.ui.setupUi(self)

        # Event handling
        self.connect(self.ui.pushButton_prevView, QtCore.SIGNAL('clicked()'), 
                self.doPlotPrevRun)

        self.connect(self.ui.pushButton_nextView, QtCore.SIGNAL('clicked()'),
                self.doPlotNextRun)

        self.connect(self.ui.pushButton_plot, QtCore.SIGNAL('clicked()'),
                self.doPlotRun)

        # Validator
        # FIXME - Add validators... 

        # Class status variable
        self._runList = []
        self._currRun = None
        self._currRunIndex = 0

        return

    #--------------------------------------------------------------------
    # Event handling methods
    #--------------------------------------------------------------------
    def doPlotRun(self):
        """ Plot the current run
        """
        print "Plot current run"
      
        # attempt to read line edit input
        try: 
            run = int(self.ui.lineEdit_run)
            if run in self._runList:
                usecombobox = False
        except ValueError as e:
            usecombobox = True

        # attempt to read from combo box
        if usecombobox is True:
            try: 
                run = int(self.ui.comboBox_runs.currentText())
                if run not in self._runList: 
                    return (False, "No line edit input... ")
            except ValueError as e:
                return (False, "No valid ... ")

        # get current run and plot
        ... ...

        

    def doPlotPrevRun(self):
        """ Plot the previous run
        """
        print "Plot previous run"


    def doPlotNextRun(self):
        """ Plot the next run
        """
        print "Plot next run"







def testmain(argv):
    """ Main method for testing purpose
    """
    app = QtGui.QApplication(argv)
    myapp = Window_GPPlot()
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)


    return

if __name__ == "__main__":
    testmain(sys.argv)
