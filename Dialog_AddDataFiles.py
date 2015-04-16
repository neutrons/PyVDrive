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
from ui.ui_AddDataToReduce import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


#------------------------------------------------------------------------------
# Essential External Methods
#------------------------------------------------------------------------------

def addCheckboxToWSTCell(table, row, col, state):
    """ function to add a new select checkbox to a cell in a table row
    won't add a new checkbox if one already exists
    """
    # Convert state to boolean
    if state is None:
        state = False
    elif isinstance(state, str) is True:
        if state.lower() == 'true':
            state = True
        elif state.lower() == 'false':
            state = False
        else:
            state = bool(int(state))
    elif isinstance(state, int) is True:
        state = bool(state)
    elif isinstance(state, bool) is True:
        pass
    else:
        raise NotImplementedError("Input state %s of type %s is not accepted." % (str(state),
            str(type(state))))
    # ENDIF

    #check if cellWidget exitst
    if table.cellWidget(row,col) != None:
        # existing: just set the value
        table.cellWidget(row,col).setChecked(state)
    else:
        #case to add checkbox
        checkbox = QtGui.QCheckBox()
        checkbox.setText('')
        checkbox.setChecked(state)
        
        #adding a widget which will be inserted into the table cell
        #then centering the checkbox within this widget which in turn,
        #centers it within the table column :-)
        QW=QtGui.QWidget()
        cbLayout=QtGui.QHBoxLayout(QW)
        cbLayout.addWidget(checkbox)
        cbLayout.setAlignment(QtCore.Qt.AlignCenter)
        cbLayout.setContentsMargins(0,0,0,0)
        table.setCellWidget(row,col, checkbox) #if just adding the checkbox directly

    return


def addComboboxToWSTCell(table, row, col, itemlist, curindex):
    """ function to add a new select checkbox to a cell in a table row
    won't add a new checkbox if one already exists

    Arguments:
     - row
     - col
     - itemlist :: list of string for combo box
     - curindex :: current index for the item get selected
    """
    # Check and set up input
    if curindex is None:
        curindex = 0

    # Check if cellWidget exitst
    if table.cellWidget(row,col) != None:
        # Existing: set to current index
        table.cellWidget(row,col).setCurrentIndex(curindex)
    else:
        # Case to add QComboBox
        # check input
        if isinstance(itemlist, list) is False:
            raise NotImplementedError("Input *itemlist* must be list!")
        qlist = []
        for item in itemlist:
            qlist.append(str(item))
        combobox = QtGui.QComboBox()
        combobox.addItems(qlist)
        
        #adding a widget which will be inserted into the table cell
        #then centering the checkbox within this widget which in turn,
        #centers it within the table column :-)
        QW=QtGui.QWidget()
        cbLayout=QtGui.QHBoxLayout(QW)
        cbLayout.addWidget(combobox)
        cbLayout.setAlignment(QtCore.Qt.AlignCenter)
        cbLayout.setContentsMargins(0,0,0,0)
        table.setCellWidget(row,col, combobox) #if just adding the checkbox directly
        combobox.setCurrentIndex(curindex)
    # ENDIFELSE

    return


class MyAddDataFilesDialog(QtGui.QMainWindow):
    """ GUI (sub) application to add data files to reduce
    Purpose:
    1. User can see view all data files to be reduced;
    2. User can select the vanadium run for matching
    """
    # Define signal
    myAddRunsSignal = QtCore.pyqtSignal(str, list)


    # Class
    def __init__(self, parent, configdict=None, tableheaderdict=None):
        """ setup main window
        """
        # Base class initialization and set up GUI
        QtGui.QMainWindow.__init__(self,parent)
        self.ui = Ui_MainWindow() 
        self.ui.setupUi(self)

        # Parnet & config
        self._myParent = parent
        self._myConfig = configdict
        if self._myParent is not None: 
            self._myProjectName = self._myParent._myProjectName
        else:
            self._myProjectName = ""

        # Sub-app specific event handling 
        # save and quit
        self.connect(self.ui.pushButton_saveQuit, QtCore.SIGNAL('clicked()'),
                self.doSaveQuit)

        # cancel
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'), 
                self.doCancelQuit)

        # cell value changed
        self.connect(self.ui.tableWidgetTable1, QtCore.SIGNAL('cellChanged()'),
                self.doCheckChangedCellValue)

        # Set up table
        if tableheaderdict is not None and isinstance(tableheaderdict, dict) is True:
            self.setupTable(tableheaderdict)

        # Signal
        if self._myParent is not None: 
            self.myAddRunsSignal.connect(self._myParent.evtAddRuns)
            self.myAddRunsSignal.connect(self._myParent.getParent().evtAddRuns)


        """ Other features ...  
        #add action exit for File --> Exit menu option
        self.connect(self.ui.actionExit, QtCore.SIGNAL('triggered()'), self.confirmExit)
        #add action exit for 'About' information
        self.connect(self.ui.actionAbout, QtCore.SIGNAL('triggered()'), self.About)
        #add signal/slot connection for pushbutton remove rows
        self.connect(self.ui.pushButtonSelectAll, QtCore.SIGNAL('clicked()'), self.selAll)        
        #add signal/slot connection for pushbutton remove rows
        self.connect(self.ui.pushButtonDeSelectAll, QtCore.SIGNAL('clicked()'), self.deSelAll)
        #add signal/slot connection for pushbutton remove rows
        self.connect(self.ui.pushButtonRemoveEmptyRows, QtCore.SIGNAL('clicked()'), \
                self.removeEmptyRows)
        #add signal/slot connection for pushbutton delete selected rows
        self.connect(self.ui.pushButtonDeleteSelectedRows, QtCore.SIGNAL('clicked()'), \
                self.deleteRows)
        #add signal/slot connection for pushbutton add rows
        # self.connect(self.ui.pushButtonAddRows, QtCore.SIGNAL('clicked()'), self.addRow)
        #add signal/slot connection for pushbutton move selected rows up
        self.connect(self.ui.pushButtonMoveRowsUp, QtCore.SIGNAL('clicked()'), self.moveRowsUp)
        #add signal/slot connection for pushbutton move selected rows down
        self.connect(self.ui.pushButtonMoveRowsDown, QtCore.SIGNAL('clicked()'), self.moveRowsDown)
        """
        return

    #--------------------------------------------------------------------------
    # Methods to access, set up and update table
    #--------------------------------------------------------------------------
    def appendRows(self, rowlist):
        """ Append rows to table (public method)
        """
        # check
        if isinstance(rowlist, list) is False:
            raise NotImplementedError("Input for appendRows() must be a list of strings")

        # set value and dictionary
        for irow in xrange(len(rowlist)):
            temprow = rowlist[irow]
            if isinstance(temprow, list) is False or len(temprow) != self._numCols:
                print "Row %d is either not a list or a list with different sizes than table. Skipped!" % (irow)
                continue
            else: 
                irow = self._appendRow(temprow)
            # ENDIFELSE
        # ENDFOR

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
    def doCheckChangedCellValue(self):
        """ Respond as a cell value changed
        """
        # FIXME No use!!!
        print "There is some value changed."

        return

    def doCancelQuit(self):
        """ Cancel and quit 
        """
        # Emit signal
        self.myAddRunsSignal.emit(self._myProjectName, [])

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



    def selectLogs(self, lognamelist):
        """ Select the log names
        """
        for logname in lognamelist:
            if self._myLogUseDict[logname][1] is False:
                self._setItemValue(self._myLogUseDict[logname][0], 1, True)
        # ENDFOR

        return

    def deselectLots(self, lognamelist):
        """ Deselect the log names
        """
        for logname in lognamelist:
            if self._myLogUseDict[logname][1] is True:
                self._setItemValue(self._myLogUseDict[logname][0], 1, False)
        # ENDFOR

        return

    def _setItemValue(self, irow, icol, value):
        """ Set value to an item in the table
        """
        if isinstance(value, bool): 
            self.ui.tableWidgetTable1.cellWidget(irow, icol).setChecked(value)
        else:
            raise NotImplementedError("Not supported yet [1000]")

        return


    def _loadDefaultConfig(self):
        """ Load default configuration, i.e., sample logs that are used for matching
        """
        defaultlognamelist = self._myConfig['vanadium.SampleLogToMatch']
        
        # loop over the form rows
        numrows = self.ui.tableWidgetTable1.rowCount()
        for irow in xrange(numrows):
            curlogname = str(self.ui.tableWidgetTable1.item(irow, 0).text())
            if curlogname in defaultlognamelist:
                self.ui.tableWidgetTable1.cellWidget(irow, 1).setChecked(True)
            # ENDIF
        # ENDFOR
        
        return

    # ENDOFCLASS

        
    #Button callbacks
    def selAll(self):
        #placeholder call necessary to extract info not passed via the signal call defined above
        SelectAll(self,self.ui.tableWidgetTable1,config.select)
        
    def deSelAll(self):
        #placeholder call necessary to extract info not passed via the signal call defined above
        DeSelectAll(self,self.ui.tableWidgetTable1,config.select)

    
    def removeEmptyRows(self):
        #delete the empty rows from the table
        table=self.ui.tableWidgetTable1
        Nrows=table.rowCount()
        
        for i in range(Nrows):
            row=Nrows-i-1 #easier to start from the end of the table
            #check if row is empty
            if table.item(row,config.firstName) == None:
                #case to remove empty row
                table.removeRow(row)

        
    def deleteRows(self):
        #delete selected rows from the table
        table=self.ui.tableWidgetTable1
        Nrows=table.rowCount()      
        col=config.select  
        for i in range(Nrows):
            row=Nrows-i-1
            #check if a row is selected
            cell=table.cellWidget(row,col)
            if cell != None:
                if cell.checkState():
                    table.removeRow(row)
        
    def addRow(self):
        #add a new row at the end of the table
        table=self.ui.tableWidgetTable1
        row=table.rowCount()      
        col=config.select  
        table.insertRow(row)
        ftext, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', 'Enter First Name:')
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8(ftext)) 
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.firstName,item)   
        ltext, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', 'Enter Last Name:')
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8(ltext)) 
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.lastName,item)  
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8(" ")) 
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.favIceCream,item)         
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8(" ")) 
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)  
        self.ui.tableWidgetTable1.setItem(row,config.favColor,item)       
        addCheckboxToWSTCell(self.ui.tableWidgetTable1,row,config.select,False)

        if ftext == "" and ltext == "":
            #case where no name was given
            self.ui.tableWidgetTable1.removeRow(row)
        
    def moveRowsUp(self):
        #wrapper function to move rows up in the table
        table=self.ui.tableWidgetTable1
        moveRows(table,config.up)
        
    def moveRowsDown(self):
        #wrapper function to move rows down in the table
        table=self.ui.tableWidgetTable1
        moveRows(table,config.down)
        
        
    #Menubar pulldown items
    def About(self):
        dialog=QtGui.QMessageBox(self)
        dialog.setText("Example Table_1 Application "+__version__)

        dialog.exec_()        
        
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
    
    def resizeEvent(self,resizeEvent):
        #support user dynamically resizing the table
        table=self.ui.tableWidgetTable1
        sz=table.size()
        w=sz.width()

        #now use widget width to determine process table column width
        Ncol=float(table.columnCount())
        colWidth=float(w)/(Ncol+0.33)
        table.setColumnWidth(0,colWidth) #Log name
        table.setColumnWidth(1,colWidth) #Select?
        table.setColumnWidth(2,colWidth) #Data type
        table.setColumnWidth(2,colWidth) #Example

    
def moveRows(table,dir):
    #Workhorse function to do the moving of the rows up or down
    Nrows=table.rowCount()     
    col=config.select  
    cnt=0
    lst=[]
    for row in range(Nrows):
        cell=table.cellWidget(row,col)
        if cell != None:
            if cell.checkState():
                lst.append(row)
                cnt+=1
       
    if dir==config.up:
        #move rows up
        offset1=1 
        #new row to be inserted
        offset2=-1 #current row getting info from
        chk=0
        sortdir=QtCore.Qt.DescendingOrder
    else:
        #move rows down
        lst.reverse()
        offset1=2
        offset2=0
        chk=Nrows-1
        sortdir=QtCore.Qt.AscendingOrder
                
    if len(lst) > 0:
        #make sure we have rows selected to move up
        if lst[0]==chk:
            #check if first row is already at the top
            dialog=QtGui.QMessageBox()
            dialog.setText("Unable to move rows - returning")
            dialog.exec_()  
            return
            
        else:
            #case to move rows up or down
            if config.colSort:
                #determine which column has been selected for sorting
                Ncols=table.columnCount()
                column_sorted=table.horizontalHeader().sortIndicatorSection()
                order = table.horizontalHeader().sortIndicatorOrder()
                table.sortItems(Ncols,order=sortdir)
            #try:
            #using try here to handle cases when cells don't have items to edit as code will crash othewise
            for row in lst:
                #copy items from row+offset2 to new row row+offset1
                #the following try/except clauses handle cases where there's nothing in the row/col cell
                table.insertRow(row+offset1) #new row
                item=QtGui.QTableWidgetItem() #create placeholder item
                try:
                    item.setText(_fromUtf8(table.item(row+offset2,config.firstName).text())) #put text in this item
                except:
                    item.setText(_fromUtf8(' '))
                table.setItem(row+offset1,config.firstName,item) #now place item in the table
                #repeat above pattern for each column in the new row
                item=QtGui.QTableWidgetItem()
                try:
                    item.setText(_fromUtf8(table.item(row+offset2,config.lastName).text())) 
                except:
                    item.setText(_fromUtf8(' '))
                table.setItem(row+offset1,config.lastName,item)
                item=QtGui.QTableWidgetItem()
                try:
                    item.setText(_fromUtf8(table.item(row+offset2,config.favIceCream).text())) 
                except:
                    item.setText(_fromUtf8(' '))                
                table.setItem(row+offset1,config.favIceCream,item)
                item=QtGui.QTableWidgetItem()
                try:
                    item.setText(_fromUtf8(table.item(row+offset2,config.favColor).text())) 
                except:
                    item.setText(_fromUtf8(' '))
                table.setItem(row+offset1,config.favColor,item)
                #column with the status checkbox requires a cell rather than an item to contain the checkbox
                #check select state of the existing row
                try:
                    #if cell exists, check and set select status
                    chk=table.cellWidget(row+offset2,config.select).checkState()
                    if chk == QtCore.Qt.Checked:
                        state=True
                    else:
                        state=False
                    #now create a Select checkbox in the new row with the same state as the row to copy from
                    addCheckboxToWSTCell(table,row+offset1,config.select,state)
                except:
                    #if no cell exists, just ignore
                    pass
                
                
                #now that copying is done, remove the old row
                table.removeRow(row+offset2)

    else:
        print "No rows to move"
        return      
      
def SelectAll(self,table,selCol):
    #toggle checkboxes off for rows that have these checkboxes 
    Nrows=table.rowCount()
    for i in range(Nrows):
        if table.cellWidget(i,selCol) != None:
            addCheckboxToWSTCell(table,i,selCol,True)

            
    
def DeSelectAll(self,table,selCol):
    #toggle checkboxes off for rows that have these checkboxes 
    Nrows=table.rowCount()
    for i in range(Nrows):
        if table.cellWidget(i,selCol) != None:
            addCheckboxToWSTCell(table,i,selCol,False)



#Main program
if __name__=="__main__":
    """ Test Main """
    # Test case
    tmpHdr  = ['Log Name', 'Match', 'Status', 'Example']
    tmpType = ['text', 'combobox', 'checkbox', 'text']

    row0 = ['AAA', ['1', '2', '3'], 'True',  'blabla..aaa']
    row1 = ['BBB', ['9', '8', '7', '6'], 'False', 'blabla..bbb']

    # Start application
    app = QtGui.QApplication(sys.argv)
    myapp = MyAddDataFilesDialog(None, None, {'Headers': tmpHdr, 'CellType': tmpType})
    myapp.appendRows([row0, row1])
    myapp.show()

    exit_code=app.exec_()
    #print "exit code: ",exit_code
    sys.exit(exit_code)
