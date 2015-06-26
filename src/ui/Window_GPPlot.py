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
        self.connect(self.ui.pushButton_allFillPlot, QtCore.SIGNAL('clicked()'),
                self.doPlotAllRuns)

        self.connect(self.ui.pushButton_normByCurrent, QtCore.SIGNAL('clicked()'),
                self.doNormByCurrent)
        self.connect(self.ui.pushButton_normByVanadium, QtCore.SIGNAL('clicked()'),
                self.doNormByVanadium)

        self.connect(self.ui.pushButton_showVanadiumPeaks, QtCore.SIGNAL('clicked()'),
                self.doShowVanadiumPeaks)
        self.connect(self.ui.pushButton_stripVPeaks, QtCore.SIGNAL('clicked()'),
                self.doStripVanPeaks)
        self.connect(self.ui.pushButton_smoothVanadium, QtCore.SIGNAL('clicked()'),
                self.doSmoothVanadium)

        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'),
                self.doQuit)

        # combo boxes
        self.connect(self.ui.comboBox_spectraList, QtCore.SIGNAL('currentIndexChanged(int)'),
                self.doPlotSelectedSpectra)

        # on-graph operation
        # FIXME : Disabled for future developing
        #self.ui.graphicsView_mainPlot.canvas.mpl_connect('button_press_event', self.on_mouseDownEvent)

        # Input validator
        # FIXME / TODO - Add validators... 

        # GUI event handling flag
        self._respondToComboBoxSpectraListChange = False

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
        execstatus, errmsg = self.getWorkflow().normalizeByCurrent(self._currProjectName, self._currRun)
        if execstatus is False:
            self.getLog().logError(errmsg)

        return

    def doNormByVanadium(self):
        """ Normalize by vanadium spectrum
        """
        execstatus, errmsg = self.getWorkflow().normalizeByVanadium(self._currProjectName, self._currRun)
        if execstatus is False:
            self.getLog().logError(errmsg)

        return


    def doPlotAllRuns(self):
        """ Plot all runs in a fill plot style
        """
        print '------------------------  PLOTTING (2D) ------------------------------'
        # Get list of all reduced data
        runlist = self._myParent.getWorkflowObj().getReducedRuns(self._myProjectName)
        print "[DB] Number of reduced runs = %d" % (len(runlist))

        # Convert the workspaces to 2D vector
        vecylist = []
        yticklabels = []
        xmin = None
        xmax = None

        # FIXME - Should have a selection!
        ikey = 0

        for runno in runlist:
            # put y values to list for constructing 2D array
            # TODO : Remove vecx, vecy = self._myControl.getVectorToPlot(expno, scanno)
            reduceddatadict = self._myParent.getWorkflowObj().getReducedData(self._myProjectName, runno)
            specid = sorted(reduceddatadict.keys())[ikey]
            vecx, vecy = reduceddatadict[specid]

            print "[DB] VecY Size = %d." % (len(vecy))
            vecylist.append(vecy)
            # yticklabels.append('Exp %d Scan %d' % (expno, scanno))
            #print "[DB] Scan ", scanno, ": X range: ", vecx[0], vecx[-1], " Size X = ", len(vecx)

            # set up range of x
            if xmin is None:
                xmin = vecx[0]
                xmax = vecx[-1]
            # ENDIF
        # ENDFOR

        dim2array = numpy.array(vecylist)
        print "[DB] Type of 2D array: %s." % (str(type(dim2array)))
        self._plot2D(dim2array, xmin=xmin, xmax=xmax, ymin=0, ymax=len(vecylist), clearimage=True)

        ## Plot
        #holdprev=False
        #self.ui.graphicsView_mergeRun.clearAllLines()
        #self.ui.graphicsView_mergeRun.addPlot2D(dim2array, xmin=xmin, xmax=xmax, ymin=0, \
        #    ymax=len(vecylist), holdprev=holdprev, yticklabels=yticklabels)

        print '------------------------  ENDING   (2D) ------------------------------'

        return


    def doPlotRunSelected(self):
        """ Plot the current run
        """
        # Attempt 1 to read line edit input
        try: 
            run = str(self.ui.lineEdit_run.text())
            if run in self._runList:
                usecombobox = False
            else:
                usecombobox = True
        except ValueError as e:
            usecombobox = True

        # Attempt 2 to read from combo box
        if usecombobox is True:
            try: 
                run = str(self.ui.comboBox_runs.currentText())
                if run not in self._runList: 
                    print  "Run %s from combo box is not a valid run." % (run)
                    return (False, "No line edit input... ")
            except ValueError as e:
                print "No valid ... "
                return (False, "No valid ... ")

        print "Run %s is selected." % (run)
        # get current run and plot
        reduceddatalist = self._myParent.getWorkflowObj().getReducedData(self._myProjectName, run)

        # set up the spectrum combobox
        self._respondToComboBoxSpectraListChange = False
        self.ui.comboBox_spectraList.clear()
        self.ui.comboBox_spectraList.addItem('%s: All'%(run))

        # Plot spectra
        print "Number of spectra: %d" % (len(reduceddatalist.keys()))
        self._clearPlot()
        for spectrum in sorted(reduceddatalist.keys()): 
            vecx, vecy = reduceddatalist[spectrum]
            label = "%s-%d"%(run, spectrum)
            self._plot(vecx, vecy, label=label, overplot=True)

            # add to comobox
            self.ui.comboBox_spectraList.addItem("%s: %d" % (run, spectrum))
        # ENDFOR

        # Update class variable
        self._currRun = run
        self._currSpectrum = 'All'

        self._respondToComboBoxSpectraListChange = True

        return
        

    def doPlotRunPrev(self):
        """ Plot the previous run
        """
        # Get previous run
        if self._currRunIndex == 0:
            self.getLog().logError("There is no previous run.  Run %s is the first." % (self._currRun))
        else:
            self._currRunIndex -= 1
            self._currRun = self._runList[self._currRunIndex]
       
        # FIXME - Refactor!
        print "Run %s is selected." % (run)
        # get current run and plot
        reduceddatalist = self._myParent.getWorkflowObj().getReducedData(self._myProjectName, run)

        print "Check point 1"

        # set up the spectrum combobox
        self._respondToComboBoxSpectraListChange = False
        self.ui.comboBox_spectraList.clear()
        self.ui.comboBox_spectraList.addItem('%s: All'%(run))

        # Plot spectra
        print "Number of spectra: %d" % (len(reduceddatalist.keys()))
        self._clearPlot()
        for spectrum in sorted(reduceddatalist.keys()): 
            vecx, vecy = reduceddatalist[spectrum]
            label = "%s-%d"%(run, spectrum)
            self._plot(vecx, vecy, label=label, overplot=True)

            # add to comobox
            self.ui.comboBox_spectraList.addItem("%s: %d" % (run, spectrum))
        # ENDFOR

        # Update class variable
        self._currRun = run
        self._currSpectrum = 'All'

        self._respondToComboBoxSpectraListChange = True

        print '------------------------  ENDING ------------------------------'

        return

    def doPlotRunNext(self):
        """ Plot the next run
        """
        if self._currRunIndex == len(self._runList)-1:
            self.getLog().logError("There is no next run.  Run %d is the last run in the list." % (
                self._currRunIndex))
        else:
            # TODO - ASAP ASAP ASAP
            raise NotImplementedError("ASAP")

        return


    def doPlotSelectedSpectra(self):
        """
        """
        # Return if it is not set to reponding mode
        if self._respondToComboBoxSpectraListChange is False:
            return

        # Parse option
        plotspectraoption = str(self.ui.comboBox_spectraList.currentText())
        terms = plotspectraoption.split(':')
        runstr = terms[0].strip()
        spectrumstr = terms[1].strip()
        if spectrumstr == 'All':
            print "Plot all spectrum"
        else:
            iws = int(spectrumstr)
            self._currSpectrum = iws
            print "Plot spectrum %d" % (iws)

        # Get current run and plot
        reduceddatalist = self._myParent.getWorkflowObj().getReducedData(self._myProjectName, runstr)

        # Plot spectra
        firsttouch = True
        for spectrum in sorted(reduceddatalist.keys()): 

            if spectrumstr == 'All' or iws == spectrum:
                vecx, vecy = reduceddatalist[spectrum]
                label = "%s-%d"%(runstr, spectrum)

                if firsttouch is True:
                    overplot = False
                else:
                    overplot = True

                self._plot(vecx, vecy, label=label, overplot=overplot)

                firsttouch = False
            # ENDIF (spectrum)
        # ENDFOR

        return


    def doShowVanadiumPeaks(self):
        """ Convert reduced data to d-spacing, re-plot and plot vanadium peaks
        """
        if self._currSpectrum == 'All':
            print "Unable to show vanadium peaks with all spectra on canvas.  Pick up 1"

        reduceddatalist = self._myParent.getWorkflowObj().getReducedData(self._myProjectName, self._currRun, unit='dSpacing') 
        
        vecx, vecy = reduceddatalist[self._currSpectrum] 
        label = "%s-%d"%(self._currRun, self._currSpectrum)
        self._plot(vecx, vecy, label=label, overplot=False)

        # Get vanadium peak and plot
        vanpeakposlist = self._myParent.getWorkflowObj().getVanadiumPeakPosList(min(vecx), max(vecy))
        self._plotPeakIndicators(vanpeakposlist)

        return


    def doQuit(self):
        """ Quit
        """
        self.close()

        return


    def doSmoothVanadium(self):
        """ Smooth vanadium data
        """
        status, errmsg = self._myParent.getWorkflowObj().smoothVanadiumData(self._myProjectName, 
                self._currRun)
        if status is False:
            raise NotImplementedError("Failed to strip vanadium peaks due to %s." % (errmsg))

        # get pre-smooth data
        vandatadict = self._myParent.getWorkflowObj().getProcessedVanadium(self._myProjectName, self._currRun)
        vanvecx, vanvecy = vandatadict[self._currSpectrum]

        # get smoothed but temporary data
        smoothdatadict = self._myParent.getWorkflowObj().getTempSmoothedVanadium(self._myProjectName, self._currRun)
        smoothvecx, smoothvecy = smoothdatadict[self._currSpectrum]

        # plot
        self._clearPlot()
        self._plot(vanvecx, vanvecy, label='vanadium', color='black', marker='.', overplot=True)
        self._plot(smoothvecx, smoothvecy, label='smoothed', color='red', marker='None', overplot=True)

        return

    
    def doStripVanPeaks(self):
        """ Strip vanadium peaks
        """
        status, errmsg = self._myParent.getWorkflowObj().stripVanadiumPeaks(self._myProjectName, 
                self._currRun)

        if status is False:
            raise NotImplementedError("Failed to strip vanadium peaks due to %s." % (errmsg))

        reduceddatadict = self._myParent.getWorkflowObj().getReducedData(self._myProjectName, self._currRun)
        vandatadict = self._myParent.getWorkflowObj().getProcessedVanadium(self._myProjectName, self._currRun)
        print "[DB] Type of reduced data  dict: ", str(type(reduceddatadict)), " keys: ", str(reduceddatadict.keys())
        print "[DB] Type of vanadium data dict: ", str(type(vandatadict))    , " keys: ", str(vandatadict.keys())
        print "[DB] Current spectrum = %d" % (self._currSpectrum)

        origvecx, origvecy = reduceddatadict[self._currSpectrum]
        vanvecx, vanvecy = vandatadict[self._currSpectrum]

        print "[DB] doStripVanPeaks: OrigX.size = %d, OrigY.size=%d"%(len(origvecx), len(origvecy)), origvecx, origvecy
        print "[DB] doStripVanPeaks: VanDX.size = %d, VanDY.size=%d"%(len(vanvecx), len(vanvecy)), vanvecx, vanvecy

        diffvecx = vanvecx
        diffvecy = origvecy - vanvecy
        maxdiffy = max(diffvecy)
        diffvecy = diffvecy - 1.5*maxdiffy

        self._clearPlot()
        self._plot(origvecx, origvecy, label='original', color='black', marker='.', overplot=False) 
        self._plot(vanvecx, vanvecy, label='van peak stripped', color='red', marker='.', overplot=True)
        self._plot(diffvecx, diffvecy, label='diff', color='green', marker='+', overplot=True)

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
            self.ui.label_currentRun.setText(str(run))
        else:
            print "Run %s does not exist!" % (run)

        return


    def setProject(self, vdprojectname):
        """ Set VDProject's name  for future reference
        """
        self._myProjectName = vdprojectname
        self.ui.labe_currentProject.setText(vdprojectname)

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
    def _clearPlot(self):
        """ 
        """ 
        self.ui.graphicsView_mainPlot.clearAllLines()

        return


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


    def _plot(self, vecx, vecy, label, overplot, color='black', marker='.', xlabel=None):
        """ Plot data with vec_x and vec_y
        """
        # Remove all previous lines on canvas if overplot is not selected
        if overplot is False:
            self.ui.graphicsView_mainPlot.clearAllLines()

        # Plot
        self.ui.graphicsView_mainPlot.addPlot(vecx, vecy, color=color, marker=marker, label=label, xlabel=xlabel)

        # Re-set XY limit
        if overplot is False:
            xmin = min(vecx)
            xmax = max(vecx)
            dx = xmax-xmin

            ymin = min(vecy)
            ymax = max(vecy)
            dy = ymax-ymin

            self.ui.graphicsView_mainPlot.setXYLimits(xmin-0.01*dx, xmax+0.01*dx, ymin-0.01*dy, ymax+0.01*dy)
        # ENDIF

        return


    def _plot2D(self, array2d, xmin, xmax, ymin, ymax, clearimage=True):
        """ Plot 2D
        self._plot2D(dim2array, xmin=xmin, xmax=xmax, ymin=0, ymax=len(vecylist), clearimage=True)
        """
        # Clear image
        if clearimage is True:
            self.ui.graphicsView_mainPlot.clearCanvas()

        # Add 2D plot 
        self.ui.graphicsView_mainPlot.addPlot2D(array2d, xmin, xmax, ymin, ymax, holdprev=False, yticklabels=None)



    def _plotPeakIndicators(self, peakposlist):
        """ Plot indicators for peaks
        """ 
        rangex = self.ui.graphicsView_mainPlot.getXLimit()
        rangey = self.ui.graphicsView_mainPlot.getYLimit()

        for pos in peakposlist:
            if pos >= rangex[0] and pos <= rangex[1]:
                vecx = numpy.array([pos, pos])
                vecy = numpy.array([rangey[0], rangey[1]])
                self.ui.graphicsView_mainPlot.addPlot(vecx, vecy, color='red', linestyle='--') 
        # ENDFOR
        
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
