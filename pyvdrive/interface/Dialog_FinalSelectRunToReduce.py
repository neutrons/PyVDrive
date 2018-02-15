#!/usr/bin/python
# TODO TODO FIXME FIXME - Evaluate to remove!

import sys
try:
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtWidgets import QMainWindow
except ImportError:
    from PyQt4 import QtGui, QtCore
    from PyQt4.QtGui import QMainWindow

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

import gui.GuiUtility as gutil
import gui.ui_FinalSelectRunToReduce_ui as gui


class FinalSelectRunToReduceDialog(QMainWindow):
    """ GUI (sub) for select run to reduce as final decision before reduction
    """
    # Define signal
    mySelectSignal = QtCore.pyqtSignal(str, list) # list of int
    myCancelSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        """ Set up main window
        """
        # Init & set up GUI
        QMainWindow.__init__(self, parent)
        self.ui = gui.Ui_MainWindow()
        self.ui.setupUi(self)

        # Set up class variable
        self._myParent = parent
        self._myProjectName = ""
        self._myIPTS = None

        self._currRowIndex = -1
        self._numRows = 0

        # Widget handlers
        self.ui.pushButton_selectAll.clicked.connect(self.doSelectAll)

        self.ui.pushButton_clear.clicked.connect(self.doClearAllSelection)

        self.ui.pushButton_exitToReduce.clicked.connect(self.doQuitContinueReduce)

        # self.connect(self.ui.pushButton_selectAll, QtCore.SIGNAL('clicked()'),
        #         self.doSelectAll)
        #
        # self.connect(self.ui.pushButton_clear, QtCore.SIGNAL('clicked()'),
        #         self.doClearAllSelection)
        #
        # self.connect(self.ui.pushButton_exitToReduce, QtCore.SIGNAL('clicked()'),
        #         self.doQuitContinueReduce)

        # Signal handlers
        if self._myParent is not None:
            self.mySelectSignal.connect(self._myParent.evtReduceData)

        return


    #--------------------------------------------------------------------------
    # Methods to handle GUI events
    #--------------------------------------------------------------------------
    def doClearAllSelection(self):
        """ Clear all selected runs for not reduction
        """
        numrows = self.ui.tableWidget.rowCount()
        for irow in xrange(numrows):
            self.ui.tableWidget.cellWidget(irow, 3).setChecked(False)

        return


    def doSelectAll(self):
        """ Select all runs to reduce
        """
        numrows = self.ui.tableWidget.rowCount()
        for irow in xrange(numrows):
            self.ui.tableWidget.cellWidget(irow, 3).setChecked(True)

        return


    def doQuitContinueReduce(self):
        """ Quit dialog window and continue to reduce data
        """
        # Collect runs to reduce
        retlist = []
        numrows = self.ui.tableWidget.rowCount()
        for irow in xrange(numrows):
            if self.ui.tableWidget.cellWidget(irow, 3).isChecked() is True:
                retlist.append(int(str(self.ui.tableWidget.item(irow, 0).text())))

        print "[DB] Runs to reduce: ", retlist

        self.mySelectSignal.emit(self._myProjectName, retlist)

        # Close window
        self.close()

        return



    #--------------------------------------------------------------------------
    # Methods to access, set up and update table
    #--------------------------------------------------------------------------
    def appendRow(self, ipts, run, vanrun, select):
        """ Append a row to the project table

        Arguments:
        - ipts :: ITPS number
        - run  :: run number
        - vanrun :: run number for vanadium run
        - select :: whether this run is selected to reduce
        """
        # Validate input
        try:
            ipts = int(ipts)
            run = int(run)
            if vanrun is None:
                vanrun = ""
            else:
                vanrun = int(vanrun)
            if isinstance(select, bool) is False:
                raise ValueError("Select should be a boolean")
        except ValueError as e:
            raise e

        # Format to strings
        ipts = str(ipts)
        run = str(run)
        vanrun = str(vanrun)

        # Append a row and set value
        if self._currRowIndex == self._numRows-1:
            # current row is the last row: insert a row
            self.ui.tableWidget.insertRow(self._numRows)
            self._numRows += 1

        # Update current row
        self._currRowIndex += 1
        irow = self._currRowIndex

        gutil.setTextToQTableCell(self.ui.tableWidget, irow, 0, run)
        gutil.setTextToQTableCell(self.ui.tableWidget, irow, 1, ipts)
        gutil.setTextToQTableCell(self.ui.tableWidget, irow, 2, vanrun)
        gutil.addCheckboxToWSTCell(self.ui.tableWidget, irow, 3, select)

        # Resize column width
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
        self.setWindowTitle(title)

        return

