#!/usr/bin/python

#import utility modules
import sys

#import PyQt modules
from PyQt4 import QtGui, QtCore, Qt

#include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

#import GUI components generated from Qt Designer .ui file
import GuiUtility as gutil
from ui_selectRuns import *


class SelectRunsDialog(QtGui.QMainWindow):
    """ GUI (sub) application to select runs

    One window works for 1 project/IPTS
    """
    mySetupSignal = QtCore.pyqtSignal(list)
    myCancelSignal = QtCore.pyqtSignal(int)

    # Class
    def __init__(self, parent):
        """ setup main window
        """
        # Base class initialization and set up GUI
        QtGui.QMainWindow.__init__(self,parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Parnet & config
        self._myParent = parent

        # Sub-app specific event handling 
        self.connect(self.ui.pushButton_saveQuit, QtCore.SIGNAL('clicked()'),
                self.doSaveQuit)
        self.connect(self.ui.pushButton_cancelQuit, QtCore.SIGNAL('clicked()'), 
                self.doCancelQuit)

        # Set up table
        headerlist = ['Start Date', 'End Date', 'Start Run', 'End Run', 'Select']

        self.ui.tableWidget.setColumnCount(5)
        self.ui.tableWidget.setHorizontalHeaderLabels(headerlist)

        # Table controlling variable
        self._numRows = self.ui.tableWidget.rowCount()
        self._currRowIndex = -1

        # Project related parameters
        self._myProjectName = "N/A"
        self._myIPTS = -1

        # Signals emit from this GUI
        self.mySetupSignal.connect(self._myParent.evtSetupShowReductionWindow)

        return

     
    #--------------------------------------------------------------------------
    # Methods to handling GUI events
    #--------------------------------------------------------------------------
    def doCancelQuit(self):
        """ Cancel and quit 
        """
        # Emit signal
        self.myCancelSignal.emit()

        # Quit
        self.close()

        return


    def doSaveQuit(self):
        """ Save the choice and quit: this is very specific to the caller!
        """
        # Get the list to return
        signallist = [self._myProjectName, self._myIPTS] 

        numrows = self.ui.tableWidget.rowCount()
        for irow in xrange(numrows): 
            selected = self.ui.tableWidget.cellWidget(irow, 4).isChecked()
            if selected is True:
                startrun = int(self.ui.tableWidget.item(irow, 2).text())
                endrun   = int(self.ui.tableWidget.item(irow, 3).text())
                print "Selected runs: from %d to %d." % (startrun, endrun)
                signallist.append( (startrun, endrun) )
            # ENDIF
        # ENDFOR

        # Emit signal for parent
        self.mySetupSignal.emit(signallist)

        # Close window
        self.close()

        return
        
    #--------------------------------------------------------------------------
    # Methods to access, set up and update table
    #--------------------------------------------------------------------------
    def appendRow(self, startdate, enddate, startrun, endrun, select):
        """ Append a row to the project table
        """
        # Validate input
        try:
            startrun = int(startrun)
            endrun = int(endrun)
            if isinstance(select, bool) is False:
                raise ValueError("Select should be a boolean")
        except ValueError as e:
            raise e
        
        # Format to strings
        startrun = str(int(startrun))
        endrun = str(endrun)
        startdate = str(startdate)
        enddate = str(enddate)

        # Append a row and set value
        if self._currRowIndex == self._numRows-1:
            # current row is the last row: insert a row
            self.ui.tableWidget.insertRow(self._numRows)
            self._numRows += 1

        # Update current row
        self._currRowIndex += 1

        # start date
        irow = self._currRowIndex

        print "[DB] Table Current Index = ", irow, " to set items", \
                " number of rows = ", self.ui.tableWidget.rowCount()

        #  The 4 lines of script can be put to a method
        gutil.setTextToQTableCell(self.ui.tableWidget, irow, 0, startdate)
        #cellitem=QtGui.QTableWidgetItem()
        #cellitem.setFlags(cellitem.flags() & ~QtCore.Qt.ItemIsEditable)
        #cellitem.setText(_fromUtf8(startdate)) 
        #self.ui.tableWidget.setItem(irow, 0, cellitem)


        # FIXME After testing, replace all the scripts to function call
        cellitem=QtGui.QTableWidgetItem()
        cellitem.setFlags(cellitem.flags() & ~QtCore.Qt.ItemIsEditable)
        cellitem.setText(_fromUtf8(enddate)) 
        self.ui.tableWidget.setItem(irow, 1, cellitem)

        cellitem=QtGui.QTableWidgetItem()
        cellitem.setFlags(cellitem.flags() & ~QtCore.Qt.ItemIsEditable)
        cellitem.setText(_fromUtf8(startrun)) 
        self.ui.tableWidget.setItem(irow, 2, cellitem)

        cellitem=QtGui.QTableWidgetItem()
        cellitem.setFlags(cellitem.flags() & ~QtCore.Qt.ItemIsEditable)
        cellitem.setText(_fromUtf8(endrun)) 
        self.ui.tableWidget.setItem(irow, 3, cellitem)

        # Add widget for the selection
        gutil.addCheckboxToWSTCell(self.ui.tableWidget, irow, 4, select)
        
        # Resize of the width of each new cell
        self.ui.tableWidget.resizeColumnsToContents()

        return


    def setRunInfo(self, projectname, ipts):
        """ Set ITPS project information to this window
        and set the title line

        Arguments: 
         - projectname
         - ipts
        """
        self._myProjectName = projectname
        self._myIPTS = int(ipts)

        title = "Project %s :  Add runs of IPTS-%d" % (self._myProjectName,
                self._myIPTS)
        self.ui.label_title.setText(title)

        return


if __name__=="__main__":
    """ Test Main """
    # Start application
    app = QtGui.QApplication(sys.argv)
    myapp = SelectRunsDialog(None)
    myapp.show()

    startdate = "2015-03-21 13:32:22"
    enddate = "2015-03-21 23:22:11"
    startrun = 12322
    endrun = 12433
    select = True
    myapp.appendRow(startdate, enddate, startrun, endrun, select)

    exit_code=app.exec_()
    sys.exit(exit_code)
