import time
from PyQt4 import QtGui, QtCore

#include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


def add_runs_to_tree(treewidget, ipts, runlist):
    """
    :param treewidget:
    :param ipts:
    :param runlist:
    :return:
    """
    if False:
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'IPTS')

    #treewidget = QtGui.QTreeView(treewidget)
    model = treewidget.model()

    numrows = model.rowCount()
    itemmain = QtGui.QStandardItem(QtCore.QString(str(ipts)))
    itemmain.setCheckable(False)
    model.setItem(numrows, 0, itemmain)
    for i in xrange(len(runlist)):
        runnumber = runlist[i]
        item = QtGui.QStandardItem(QtCore.QString(str(runnumber)))
        model.setItem(numrows+i+1, 1, item)
        # itemmain.setChild(i, item) : this will add value under column 0

    return


def convert_to_qdate_epoch(epoch_time):
    """

    :param epoch_time:
    :return:
    """
    assert(isinstance(epoch_time, float))

    # Use time.struct_time
    m_time = time.gmtime(epoch_time)
    year = m_time.tm_year
    month =  m_time.tm_mon
    day = m_time.tm_mday

    m_date = QtCore.QDate(year, month, day)

    return m_date


def parse_integer(line_edit):
    """
    Parse a line edit to an integer value
    :param line_edit:
    :return: integer or None
    """
    # Check input
    assert(isinstance(line_edit, QtGui.QLineEdit))

    str_value = str(line_edit.text()).strip()
    if len(str_value) == 0:
        return None

    try:
        int_value = int(str_value)
    except ValueError as e:
        raise e

    return int_value


def parse_float(line_edit):
    """
    Parse a line edit as a float number
    :param line_edit:
    :return: float or None
    """
    # Check input
    assert(isinstance(line_edit, QtGui.QLineEdit))

    str_value = str(line_edit.text()).strip()
    if len(str_value) == 0:
        return None

    try:
        float_value = float(str_value)
    except ValueError as e:
        raise e

    return float_value


def pop_dialog_error(parent, message):
    """ Pop up a one-button dialog for error message
    :param message:
    :return:
    """
    QtGui.QMessageBox.information(parent, 'Error!', message)

    return


def setTextToQTableCell(table, irow, icol, text):
    """ Set up a regular text cell in a QTableWidget

    Arguments: 
     - table    :: QTableWidget
     - irow     :: integer as row number
     - icol     :: integer as column number
     - text     :: string as the text to be set to the cell
    """
    # Validate
    irow = int(irow)
    icol = int(icol)

    # Set up
    cellitem = QtGui.QTableWidgetItem()
    cellitem.setFlags(cellitem.flags() & ~QtCore.Qt.ItemIsEditable)
    cellitem.setText(_fromUtf8(str(text)))
    table.setItem(irow, icol, cellitem)

    return

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

