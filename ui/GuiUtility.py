from PyQt4 import QtGui, QtCore

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
            raise NotImplementedError("Input 'itemlist' must be list! Current input is of type '%s'", 
                    str(type(itemlist)))
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

