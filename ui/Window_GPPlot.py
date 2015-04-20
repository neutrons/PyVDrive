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

import matplotlib
import matplotlib.pyplot


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
        
import ui_GPPlot

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
        self.ui = ui_GPPlot.Ui_MainWindow()
        self.ui.setupUi(self)

        # Event handling
        # push buttons 
        self.connect(self.ui.pushButton_prevView, QtCore.SIGNAL('clicked()'), 
                self.doPlotRunPrev)
        self.connect(self.ui.pushButton_nextView, QtCore.SIGNAL('clicked()'),
                self.doPlotRunNext)
        self.connect(self.ui.pushButton_plot, QtCore.SIGNAL('clicked()'),
                self.doPlotRunSelected)

        self.connect(self.ui.pushButton_normByCurrent, QtCore.SIGNAL('clicked()'),
                self.doNormByCurrent)
        self.connect(self.ui.pushButton_nomByVanadium, QtCore.SIGNAL('clicked()'),
                self.doNormByVanadium)
        self.connect(self.ui.pushButton_stripVPeaks, QtCore.SIGNAL('clicked()'),
                self.doStripVanPeaks)

        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                self.doQuit)

        # on-graph operation
        self.ui.graphicsView.mpl_connect('button_press_event', self.on_mouseDownEvent)

        # Input validator
        # FIXME / TODO - Add validators... 

        # Class status variable
        self._runList = []
        self._currRun = None
        self._currRunIndex = 0

        # Initialze graph
        self._initFigureCanvas()

        return

    #---------------------------------------------------------------------------
    # Widget event handling methods
    #---------------------------------------------------------------------------
    def doNormByCurrent(self):
        """ Normalize by current/proton charge
        """
        # TODO - ASAP

        return

    def doNormByVanadium(self):
        """ Normalize by vanadium spectrum
        """
        # TODO - ASAP

        return

    def doPlotRunSelected(self):
        """ Plot the current run
        """
        # TODO - ASAP ASAP ASAP
        print "Plot user specified run"
      
        # attempt to read line edit input
        try: 
            run = self.ui.lineEdit_run.text()
            if run in self._runList:
                usecombobox = False
            else:
                usecombobox = True
        except ValueError as e:
            usecombobox = True

        # attempt to read from combo box
        if usecombobox is True:
            try: 
                run = self.ui.comboBox_runs.currentText()
                if run not in self._runList: 
                    print  "Run %s from combo box is not a valid run." % (run)
                    return (False, "No line edit input... ")
            except ValueError as e:
                print "No valid ... "
                return (False, "No valid ... ")

        print "Run %s is selected." % (run)
        # get current run and plot
        vecx, vecy, notelist = self._myParent.getData(runnumber=run)

        self._plot(vecx, vecy, plotindex=0)

        return
        

    def doPlotRunPrev(self):
        """ Plot the previous run
        """
        # TODO - ASAP ASAP ASAP
        print "Plot previous run"


    def doPlotRunRun(self):
        """ Plot the next run
        """
        # TODO - ASAP ASAP ASAP
        print "Plot next run"

    
    def doStripVanPeaks(self):
        """ Strip vanadium peaks
        """
        # TODO - ASAP ASAP

        return


    #---------------------------------------------------------------------------
    # Set up
    #---------------------------------------------------------------------------
    def resetRuns(self):
        """ Reset runs in comboBox_runs 
        """
        # clear
        del self._runList[:]

        # clear combo box
        self.ui.comboBox_runs.clear()

        return

    def setCurrentRun(self, run):
        """ Set current run to a specified value
        If this run does not exist in _runList, it is not accepted
        """
        if run in self._runList:
            qindex = self._runList.index(run)
            self.ui.comboBox_runs.setCurrentIndex(qindex)
        else:
            print "Run %s does not exist!" % (run)

        return


    def setRuns(self, runslist):
        """ Add runs shown in runs list to comboBox_runs
        """ 
        # Add run to _runList
        for run in runslist:
            if run not in self._runList: 
                self._runList.append(run)
        # ENDFOR

        # Sort by value
        self._runList = sorted(self._runList)

        # Set the sorted lsit to combo box
        self.ui.comboBox_runs.clear() 
        self.ui.comboBox_runs.addItems(self._runList)

        return


    #--------------------------------------------------------------------
    # Event handling methods: WxPython canvas operation
    #--------------------------------------------------------------------
    def on_mouseDownEvent(self, event):
        """ Respond to pick up a value with mouse down event
        """
        x = event.xdata
        y = event.ydata

        if x is not None and y is not None:
            msg = "You've clicked on a bar with coords:\n %f, %f" % (x, y)
            QMessageBox.information(self, "Click!", msg)

        return

    #---------------------------------------------------------------------------
    # Private methods
    #---------------------------------------------------------------------------
    def _initFigureCanvas(self):
        """ Initialize graph
        """
        # TODO - ASAP

        if False: 
            # 
            # TODO - Refactor this part
            vecx, vecy, xlim, ylim = self.computeMock()
            self.ui.mainplot = self.ui.graphicsView.getPlot()

            self.mainline = self.ui.mainplot.plot(vecx, vecy, 'r-')
            self.plotlinelist = [self.mainline]

            leftx = [xlim[0], xlim[0]]
            lefty = [ylim[0], ylim[1]]
            self.leftslideline = self.ui.mainplot.plot(leftx, lefty, 'b--')
            rightx = [xlim[1], xlim[1]]
            righty = [ylim[0], ylim[1]]
            self.rightslideline = self.ui.mainplot.plot(rightx, righty, 'g--')
            upperx = [xlim[0], xlim[1]]
            uppery = [ylim[1], ylim[1]]
            self.upperslideline = self.ui.mainplot.plot(upperx, uppery, 'b--')
            lowerx = [xlim[0], xlim[1]]
            lowery = [ylim[0], ylim[0]]
            self.lowerslideline = self.ui.mainplot.plot(lowerx, lowery, 'g--')
        
        return


    def _plot(self, vecx, vecy, plotindex):
        """ Plot data with vec_x and vec_y
        """
        # Get limits of x
        xmin = min(vecx)
        xmax = max(vecx)
        ymin = min(vecy)
        ymax = max(vecy)

        # Reset graph's data range
        self.ui.mainplot.set_xlim(xmin, xmax)
        self.ui.mainplot.set_ylim(ymin, ymax)

        # Reset x- and y-axi label
        self.ui.mainplot.set_xlabel('Time (seconds)', fontsize=13)
        self.ui.mainplot.set_ylabel('Counts', fontsize=13)

        # Set up main line
        matplotlib.pyplot.setp(self.plotlinelist[plotindex], xdata=vecx, ydata=vecy)

        # Show the change
        self.ui.graphicsView.draw()

        return

class MockParent:
    """ Mocking parent for universal purpose
    """
    def __init__(self):
        """ Init
        """
        # self._arrayX, self._arrayY, self._noteList = self._parseData()

        return


    def _parseData(self):
        datafile = open('./tests/mockdata.dat', 'r')
        rawlines = datafile.readlines()
        datafile.close()

        xlist = []
        ylist = []
        tlist = []

        for rline in rawlines:
            line = rline.strip()
            if len(line) == 0:
                continue

            terms = line.split()
            x = float(terms[0])
            y = float(terms[1])
            t = terms[0]

            xlist.append(x)
            ylist.append(y)
            tlist.append(t)

        x_array = numpy.array(xlist)
        y_array = numpy.array(ylist)

        return x_array, y_array, tlist

    #--------------------------------------------------------------------
    # For testing purpose
    #--------------------------------------------------------------------
    def computeMock(self):
        """ Compute vecx and vecy as mocking
        """
        import random, math

        x0 = 0.
        xf = 1.
        dx = 0.1

        vecx = []
        vecy = []

        x = x0
        while x < xf:
            y = 0.0
            vecx.append(x)
            vecy.append(y)
            x += dx

        xlim = [x0, xf]
        ylim = [-1., 1]

        return (vecx, vecy, xlim, ylim)



    def getData(self, runnumber):
        """ Form two numpy array for plotting
        """
        return (self._arrayX, self._arrayY, self._noteList)

def testmain(argv):
    """ Main method for testing purpose
    """
    parent = MockParent()

    app = QtGui.QApplication(argv)

    # my plot window app
    myapp = Window_GPPlot(parent)
    # myapp.setRuns(['002271'])
    myapp.show()

    exit_code=app.exec_()
    sys.exit(exit_code)


    return

if __name__ == "__main__":
    testmain(sys.argv)
