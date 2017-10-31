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

# #import version information
# from _version import __version__
# 
# #import constants from config.py
# import config
# 
#import GUI components generated from Qt Designer .ui file
from ui_VanDatabaseCriterialSetup import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class MyVanadiumDatabaseCriterialDialog(QtGui.QMainWindow):
    
    #initialize app
    def __init__(self, parent, configdict):
        #setup main window
        QtGui.QMainWindow.__init__(self,parent)
        self.ui = Ui_MainWindow() #defined in ui_AppTemplate.py
        self.ui.setupUi(self)

        # Parnet
        self._myParent = parent
        self._myConfig = configdict
    
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

        #
        self.connect(self.ui.pushButton_saveQuit, QtCore.SIGNAL('clicked()'),
                self.doSaveQuit)

        # 
        self.connect(self.ui.tableWidgetTable1, QtCore.SIGNAL('cellChanged()'),
                self.doCheckChangedCellValue)

        # 
        self.connect(self.ui.pushButton_cancel, QtCore.SIGNAL('clicked()'), 
                self.doCancelQuit)

        
        #define column headings
        # tmpHdr=['First Name','Last Name','Favorite Ice Cream','Favorite Color','Status']
        tmpHdr=['Log Name','Status', 'Type', 'Example']
        NHdrs=len(tmpHdr)
        HzHeaders=['']*NHdrs
        HzHeaders[0] = tmpHdr[0]
        HzHeaders[1] = tmpHdr[1]
        HzHeaders[2] = tmpHdr[2]
        HzHeaders[3] = tmpHdr[3]

        self.ui.tableWidgetTable1.setHorizontalHeaderLabels(HzHeaders)
        self.ui.tableWidgetTable1.setColumnCount(4)
            
        # class variables
        self._numRows = 0
        
        self._myLogUseDict = {} # key: string for log sample value: boolean

        return


    def clear(self):
        """ Clear the selection
        """
        self._myLogUseDict.clear()

        return


    def setAllChoices(self, vandbfilelogs, logexamples):
        """ Set the logs to match for the vanadium
        dabase file to the GUI
        """
        # check
        if isinstance(vandbfilelogs, list) is False:
            raise NotImplementedError("Input for setAllChoices() must be a list of strings")
        if len(logexamples) != len(vandbfilelogs):
            raise NotImplementedError("Input for setAllChoices() should have two lists with same sizes.")

        # set value and dictionary
        for irow in xrange(len(vandbfilelogs)):
            logname = vandbfilelogs[irow]
            example = logexamples[irow]
            irow = self._appendRow( [logname, False, "float", example] )
            self._myLogUseDict[logname] = (irow, "float", False)

        # Load configuration
        self._loadDefaultConfig()

        return

    def _appendRow(self, rowitemlist):
        """ Append a row to the table
        """
        # check
        if isinstance(rowitemlist, list) is False:
            raise NotImplementedError("Input rowlist is not a list")

        logname = rowitemlist[0]
        useit = rowitemlist[1]
        datatype = rowitemlist[2]
        example = rowitemlist[3]

        # append a row and set value
        row = self._numRows
        self._numRows += 1

        # insert a new row if it is over the limit
        if self._numRows > self.ui.tableWidgetTable1.rowCount():
            self.ui.tableWidgetTable1.insertRow(row)

        # log name
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8(logname)) 
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row, 0, item)         

        # used
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Blue")) 
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row, 1, item)      
        addCheckboxToWSTCell(self.ui.tableWidgetTable1, row, 1, useit)

        # type
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Blue"))
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row, 2, item)      
        addComboboxToWSTCell(self.ui.tableWidgetTable1, row, 2, useit)

        # example
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8(example)) 
        item.setFlags(item.flags()) 
        self.ui.tableWidgetTable1.setItem(row, 3, item)         

        print "Row %d: Log name = %s" % (row, logname)

        return row

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

    # Event Hanling
    def doCheckChangedCellValue(self):
        """ Respond as a cell value changed
        """
        # FIXME No use!!!
        print "There is some value changed."

        return


    def doSaveQuit(self):
        """ Save the choice and quit
        """
        # save_to_buffer and close
        returnlist = []
        numrows = self.ui.tableWidgetTable1.rowCount()
        print "Number of rows = ", numrows
        for irow in xrange(numrows):
            if self.ui.tableWidgetTable1.cellWidget(irow, 1).checkState() == 2:
                logname = str(self.ui.tableWidgetTable1.item(irow, 0).text())
                datatype = str(self.ui.tableWidgetTable1.cellWidget(irow, 2).currentText()).lower()
                returnlist.append((logname, datatype))
                print "Criteria selected: %s of type %s." % (logname, datatype)

        self.close()

        # call parent
        self._myParent.setVanMatchCriteria(returnlist)

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

    def doCancelQuit(self):
        """ Cancel and quit 
        """
        self.close()

        return

    def _loadDefaultConfig(self):
        """ Load default configuration, i.e., sample logs that are used for matching
        """
        defaultloglist = self._myConfig['vanadium.SampleLogToMatch']
        defaultlognamelist = []
        for tp in defaultloglist:
            if isinstance(tp, tuple) is False:
                raise NotImplementedError("vanadium.SampleLogToMatch must be a list of 2-tuple.")
            defaultlognamelist.append(tp[0])

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


def addCheckboxToWSTCell(table,row,col,state):
    #function to add a new select checkbox to a cell in a table row
    #won't add a new checkbox if one already exists
    if state == '':
        state=False
    #check if cellWidget exitst
    if table.cellWidget(row,col) != None:
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


def addComboboxToWSTCell(table,row,col,state):
    #function to add a new select checkbox to a cell in a table row
    #won't add a new checkbox if one already exists
    if state == '':
        state=False
    #check if cellWidget exitst
    if table.cellWidget(row,col) != None:
        print "Not None!"
        table.cellWidget(row,col).setChecked(state)
    else:
        #case to add checkbox

        checkbox = QtGui.QComboBox()
        checkbox.addItems(["Float", "Integer", "String"])
        
        #adding a widget which will be inserted into the table cell
        #then centering the checkbox within this widget which in turn,
        #centers it within the table column :-)
        QW=QtGui.QWidget()
        cbLayout=QtGui.QHBoxLayout(QW)
        cbLayout.addWidget(checkbox)
        cbLayout.setAlignment(QtCore.Qt.AlignCenter)
        cbLayout.setContentsMargins(0,0,0,0)
        table.setCellWidget(row,col, checkbox) #if just adding the checkbox directly



#Main program
if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = TableMain()
    myapp.show()

    exit_code=app.exec_()
    #print "exit code: ",exit_code
    sys.exit(exit_code)
