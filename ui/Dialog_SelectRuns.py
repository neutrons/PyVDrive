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
from ui_selectRuns import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

import GuiUtility as guiutil

class SelectRunsDialog(QtGui.QMainWindow):
    """ GUI (sub) application to select runs
    """
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

        return

    # FIXME - Clean the code!

    #--------------------------------------------------------------------------
    # Methods to access, set up and update table
    #--------------------------------------------------------------------------
    def appendRow(self, startdate, enddate, startrun, endrun, select):
        """ Append a row to table
        """
        # TODO - Doc
        # TODO - Check input
        startdate = str(startdate)
        enddate = str(enddate)
        startrun = str(startrun)
        endrun = str(endrun)

        # Append a row and set value
        # FIXME - Need a class variable to judge whether a new row is required or not
        self.ui.tableWidget.insertRow(0)
        # TODO self._numRows += 1
        # FIXME irow should be set properly
        irow = 0

        # start date
        cellitem=QtGui.QTableWidgetItem()
        cellitem.setFlags(cellitem.flags() & ~QtCore.Qt.ItemIsEditable)
        cellitem.setText(_fromUtf8(startdate)) 
        #sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        #cellitem.setSizePolicy(sizePolicy)
        self.ui.tableWidget.setItem(irow, 0, cellitem)

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

        # TODO - Add widget for the selection

        # Resize!
        self.ui.tableWidget.resizeColumnsToContents()
        #tableResult->setVisible(false);
        #tableResult->resizeColumnsToContents();
        #tableResult->setVisible(true);
        return


    def setupTable(self, tableheaderdict):
        """ Set up Table dynamically
        """
        # check input
        if isinstance(tableheaderdict, dict) is False:
            raise NotImplementedError("setupTable takes dictoary as input.")

        # set up header
        headerlist = tableheaderdict['Headers']
        if isinstance(headerlist, list) is False:
            raise NotImplementedError("Element 'Headers' is not list.")
        self._numCols = len(headerlist)
        self.ui.tableWidgetTable1.setColumnCount(self._numCols)
        self.ui.tableWidgetTable1.setHorizontalHeaderLabels(headerlist)

        self._colType = tableheaderdict['CellType']
        if isinstance(self._colType, list) is False or len(self._colType) != self._numCols:
            raise NotImplementedError("Element 'CellType' is not list or has different \
                    size than 'Headers'")

        # row
        self._numRows = 0

        return

    def _appendRow(self, rowitemlist):
        """ Append a row to the table (private method)
        Assuming that the input rowitemlist is checked with type and size in the caller

        Arguments: 
         - rowitemlist :: 2-tuple:  (1) string as data file name, 
                                    (2) list of vanadium run/None
        """
        # Append a row and set value
        self.ui.tableWidgetTable1.insertRow(self._numRows)
        irow = self._numRows
        self._numRows += 1

        # Set up the items of the new row
        useit = True
        for itemindex in xrange(len(rowitemlist)):
            # get value
            itemvalue = rowitemlist[itemindex]

            # get a widget for item
            cellitem=QtGui.QTableWidgetItem()
            cellitem.setFlags(cellitem.flags() & ~QtCore.Qt.ItemIsEditable)

            if self._colType[itemindex] == 'text': 
                # regualr text/label 
                cellitem.setText(_fromUtf8(itemvalue)) 
                self.ui.tableWidgetTable1.setItem(irow, itemindex, cellitem)

            elif self._colType[itemindex] == 'checkbox':
                # a check box
                cellitem.setText(_fromUtf8(''))
                self.ui.tableWidgetTable1.setItem(irow, itemindex, cellitem)
                state = itemvalue
                addCheckboxToWSTCell(self.ui.tableWidgetTable1, irow, itemindex, state)

            elif self._colType[itemindex] == 'combobox':
                # a combo box
                # correct input
                if itemvalue is None:
                    itemvalue = []
                elif isinstance(itemvalue, str) is False:
                    itemvalue = [str(itemvalue)]

                cellitem.setText(_fromUtf8(''))
                self.ui.tableWidgetTable1.setItem(irow, itemindex, cellitem) 
                addComboboxToWSTCell(self.ui.tableWidgetTable1, irow, itemindex, itemvalue, 0)

            else:
                raise NotImplementedError('Cell type %s is not supported!' % (self._colType[itemindex]))

            # ENDIFELSE
        # ENDFOR

        return 
     
    #--------------------------------------------------------------------------
    # Methods to handling GUI events
    #--------------------------------------------------------------------------
    def doCancelQuit(self):
        """ Cancel and quit 
        """
        # Emit signal
        # TODO - Set up signal
        # self.myAddRunsSignal.emit(self._myProjectName, [])

        # Quit
        self.close()

        return


    def doSaveQuit(self):
        """ Save the choice and quit: this is very specific to the caller!
        """
        # Get the list to return
        returnlist = []
        numrows = self.ui.tableWidgetTable1.rowCount()
        for irow in xrange(numrows):
            try:
                term0 = str(self.ui.tableWidgetTable1.item(irow, 0).text())
                term1 = str(self.ui.tableWidgetTable1.cellWidget(irow, 1).currentText())
                returnlist.append([term0, term1])
                print "%s\t%s" % (term0, term1)
            except AttributeError:
                break
        # ENDIF

        # Emit signal
        self.myAddRunsSignal.emit(self._myProjectName, returnlist)

        # Close
        self.close()

        return

    def doSelectQuit(self):
        """ Select and quit
        """
        # Do it 
        for logname in self._myLogUseDict:
            if self._myLogUseDict[logname] is True: 
                self._myParent._criteriaList.append(logname)

        # send out a signal
        # FIXME - Useless unless you can make doCheckChangedCellValue() work!
        raise  NotImplementedError("continue from here... [834]") 

        # close myself
        self.close()

        return

    #--------------------------------------------------------------------------
    # Others... 
    #--------------------------------------------------------------------------
    def clear(self):
        """ Clear the selection
        """
        self._myLogUseDict.clear()

        return

    def confirmExit(self):
        reply = QtGui.QMessageBox.question(self, 'Message',
        "Are you sure to quit?", QtGui.QMessageBox.Yes | 
        QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        
        if reply == QtGui.QMessageBox.Yes:
        #close application
            self.close()
        else:
        #do nothing and return
            pass     
    


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
