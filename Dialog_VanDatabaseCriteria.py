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

#import version information
from _version import __version__

#import constants from config.py
import config

#import GUI components generated from Qt Designer .ui file
from ui_table_1 import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class TableMain(QtGui.QMainWindow):
    
    #initialize app
    def __init__(self,parent=None):
        #setup main window
        QtGui.QMainWindow.__init__(self,parent)
        self.ui = Ui_MainWindow() #defined in ui_AppTemplate.py
        self.ui.setupUi(self)
    
        #add action exit for File --> Exit menu option
        self.connect(self.ui.actionExit, QtCore.SIGNAL('triggered()'), self.confirmExit)
        #add action exit for 'About' information
        self.connect(self.ui.actionAbout, QtCore.SIGNAL('triggered()'), self.About)
        #add signal/slot connection for pushbutton remove rows
        self.connect(self.ui.pushButtonSelectAll, QtCore.SIGNAL('clicked()'), self.selAll)        
        #add signal/slot connection for pushbutton remove rows
        self.connect(self.ui.pushButtonDeSelectAll, QtCore.SIGNAL('clicked()'), self.deSelAll)
        #add signal/slot connection for pushbutton remove rows
        self.connect(self.ui.pushButtonRemoveEmptyRows, QtCore.SIGNAL('clicked()'), self.removeEmptyRows)
        #add signal/slot connection for pushbutton delete selected rows
        self.connect(self.ui.pushButtonDeleteSelectedRows, QtCore.SIGNAL('clicked()'), self.deleteRows)
        #add signal/slot connection for pushbutton add rows
        self.connect(self.ui.pushButtonAddRows, QtCore.SIGNAL('clicked()'), self.addRow)
        #add signal/slot connection for pushbutton move selected rows up
        self.connect(self.ui.pushButtonMoveRowsUp, QtCore.SIGNAL('clicked()'), self.moveRowsUp)
        #add signal/slot connection for pushbutton move selected rows down
        self.connect(self.ui.pushButtonMoveRowsDown, QtCore.SIGNAL('clicked()'), self.moveRowsDown)
        
        #define column headings
        tmpHdr=['First Name','Last Name','Favorite Ice Cream','Favorite Color','Status']
        NHdrs=len(tmpHdr)
        HzHeaders=['']*NHdrs
        HzHeaders[config.firstName]=tmpHdr[0]
        HzHeaders[config.lastName]=tmpHdr[1]
        HzHeaders[config.favIceCream]=tmpHdr[2]
        HzHeaders[config.favColor]=tmpHdr[3]
        HzHeaders[config.select]=tmpHdr[4]        
            
            
        self.ui.tableWidgetTable1.setHorizontalHeaderLabels(HzHeaders)
        
        
        #for demo purposes, place some stuff in the table
        #add Jean
        row=0
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Jean")) 
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.firstName,item)         
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Bilheux")) 
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.lastName,item)  
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Chocolate")) 
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.favIceCream,item)         
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Blue")) 
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.favColor,item)      
        addCheckboxToWSTCell(self.ui.tableWidgetTable1,row,config.select,True)
        
        #now add Wenduo
        row=1
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Wenduo")) 
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.firstName,item)         
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Zhou")) 
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.lastName,item)  
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Vanila")) 
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.favIceCream,item)         
        item=QtGui.QTableWidgetItem()
        item.setText(_fromUtf8("Red")) 
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.ui.tableWidgetTable1.setItem(row,config.favColor,item)    
        addCheckboxToWSTCell(self.ui.tableWidgetTable1,row,config.select,False)
        
        #enable sorting for the table
        if config.colSort:
            self.ui.tableWidgetTable1.setSortingEnabled(True)
        else:
            self.ui.tableWidgetTable1.setSortingEnabled(False)
        
        
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
        table.setColumnWidth(config.firstName,colWidth) #PID
        table.setColumnWidth(config.lastName,colWidth) #User
        table.setColumnWidth(config.favIceCream,colWidth) #CPU%
        table.setColumnWidth(config.favColor,colWidth) #MEM%
        table.setColumnWidth(config.select,colWidth) #Name

    
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
        checkbox.setText('Select')
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



#Main program
if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = TableMain()
    myapp.show()

    exit_code=app.exec_()
    #print "exit code: ",exit_code
    sys.exit(exit_code)
