import time
import datetime
import numpy
try:
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QLineEdit, QMessageBox, QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout
    from PyQt5.QtGui import QStandardItemModel, QStandardItem
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QStandardItemModel, QStandardItem, QLineEdit, QMessageBox, QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout

#include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


def add_runs_to_tree(treewidget, ipts, runlist):
    """ Add runs to a tree:

    THIS IS NOT USED ANYMORE!

    :param treewidget:
    :param ipts:
    :param runlist:
    :return:
    """
    if False:
        model = QStandardItemModel()
        model.setColumnCount(2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'IPTS')

    #treewidget = QTreeView(treewidget)
    model = treewidget.model()

    numrows = model.rowCount()
    itemmain = QStandardItem(QtCore.QString(str(ipts)))
    itemmain.setCheckable(False)
    model.setItem(numrows, 0, itemmain)
    for i in xrange(len(runlist)):
        runnumber = runlist[i]
        item = QStandardItem(QtCore.QString(str(runnumber)))
        model.setItem(numrows+i+1, 1, item)
        # itemmain.setChild(i, item) : this will add value under column 0

    return


def convert_time_vector_to_relative(vec_times):
    """ Convert vector of epoch times (absolute) to relative time
    :param vec_times: 1-D numpy array of epoch time (absolute time)
    :return: 1-E numpy array of relative time such that vec_time[0] = 0.
    """
    assert isinstance(vec_times, numpy.ndarray)

    time0 = vec_times[0]
    vec_rel_time = vec_times[:] - time0

    return vec_rel_time


def convert_to_qdate(date_time):
    """
    Convert date time to QtCore.QDate
    :param date_time:
    :return:
    """
    if isinstance(date_time, float):
        # assume it is an epoch time
        q_date = convert_to_qdate_epoch(date_time)

    elif isinstance(date_time, datetime.datetime):
        # input time is datetime.datetime
        q_date = convert_to_qdate_datetime(date_time)

    else:
        raise RuntimeError('Date time of %s type is not supported to convert to QDate.'
                           '' % date_time.__class__.__name__)

    return q_date


def convert_to_qdate_datetime(date_time):
    """
    Convert python's datetime.datetime to PyQt's QDate for display.
    :param date_time:
    :return:
    """
    # check
    assert isinstance(date_time, datetime.datetime), 'Input date and time must be a datetime.datetime but not %s.' \
                                                     '' % type(date_time)

    # convert: get year, month and day from date_time structure
    year = date_time.year
    month = date_time.month
    day = date_time.day

    # create a QDate object
    m_date = QtCore.QDate(year, month, day)

    return m_date


def convert_to_qdate_epoch(epoch_time):
    """
    Convert epoch time to PyQt4.QtCore.QDate
    :param epoch_time:
    :return:
    """
    assert isinstance(epoch_time, float), 'Method convert_to_qdate_epoch() takes epoch_time %s ' \
                                          'in format of float but not %s.' % (str(epoch_time),
                                                                              type(epoch_time))

    # Use time.struct_time
    m_time = time.gmtime(epoch_time)
    year = m_time.tm_year
    month = m_time.tm_mon
    day = m_time.tm_mday

    m_date = QtCore.QDate(year, month, day)

    return m_date


def parse_integer(line_edit, allow_blank=True):
    """
    Parse a line edit to an integer value
    :exception: ValueError
    :param line_edit:
    :param allow_blank: if true, then return None if there is no string written in the LineEdit
    :return: integer or None
    """
    # Check input
    assert(isinstance(line_edit, QLineEdit))

    str_value = str(line_edit.text()).strip()
    if len(str_value) == 0:
        if allow_blank:
            return None
        else:
            raise RuntimeError('Blank editor')

    try:
        int_value = int(str_value)
    except ValueError as e:
        raise e

    return int_value


def parse_integer_list(line_edit, size=None, check_order=False, remove_duplicate=False, increase=False):
    """
    parse a QLineEdit whose text can be converted to a list of positive integers;
    the optional operation can be used to check size, and order
    Example: 110898,110912,110997,110872,110802, 110829, 110932-110936,110830-110834
    :param line_edit:
    :param size:
    :param check_order: flag to check whether the input is ordered
    :param increase:
    :return:
    """
    # check inputs
    assert isinstance(line_edit, QLineEdit), 'Input {0} of type {1} must be a QLineEdit instance.' \
                                                   ''.format(line_edit, type(line_edit))

    # get the text and split
    line_text = str(line_edit.text())
    line_text = line_text.replace(',', ' ')
    terms = line_text.split()

    # convert terms to list of integers
    # parse to integers
    integer_list = list()
    for idx, term in enumerate(terms):
        term = term.strip()
        if term.count('-') >= 1 and term.startswith('-') is False:
            # contain a '-' but not start with '-'
            sub_terms = term.split('-')
            if len(sub_terms) != 2:
                raise RuntimeError('Only positive integers are supported here. {0} is not a supported form.'
                                   ''.format(term))
            try:
                start_value = int(sub_terms[0])
                end_value = int(sub_terms[1])
            except ValueError:
                raise RuntimeError('Unable to convert {0} and {1} to integers.'.format(sub_terms[0], sub_terms[1]))
            if start_value > end_value:
                raise RuntimeError('Range {0} - {1} is not in ascending order.'.format(start_value, end_value))
            series = range(start_value, end_value)
            integer_list.extend(series)
        else:
            try:
                integer_list.append(int(term))
            except ValueError:
                raise RuntimeError('{0}-th term {1} is not an integer.'.format(idx, term))
        # END-IF-ELSE
    # END-FOR

    # check size
    if size is not None and len(integer_list) != size:
        raise RuntimeError('Number of integers must be 2 but not {0}. FYI: {1}'
                           ''.format(len(terms), terms))

    # check order
    if check_order:
        for index in range(1, len(integer_list)):
            if increase and integer_list[index] < integer_list[index-1]:
                raise RuntimeError('Input integer list {0} is not in ascending order'.format(integer_list))
            elif not increase and integer_list[index] > integer_list[index-1]:
                raise RuntimeError('Input integer list {0} is not in in descending order.'.format(integer_list))
        # END-FOR
    # END-IF

    # convert to list
    if remove_duplicate:
        int_set = set(integer_list)
        integer_list = list(int_set)
        integer_list.sort(reverse=not increase)

    return integer_list


def parse_float(line_edit, allow_blank=True):
    """
    Parse a line edit as a float number
    :param line_edit:
    :param allow_blank: if true, then return None if there is no string written in the LineEdit
    :return: float or None
    """
    # Check input
    assert(isinstance(line_edit, QLineEdit))

    str_value = str(line_edit.text()).strip()
    if len(str_value) == 0:
        if allow_blank:
            return None
        else:
            raise RuntimeError('Blank editor')

    try:
        float_value = float(str_value)
    except ValueError as e:
        raise e

    return float_value


def pop_dialog_error(parent, message):
    """ Pop up a one-button dialog for error message
    :param parent:
    :param message:
    :return:
    """
    assert isinstance(message, str), 'Input message "{0}" must be a string but not a {1}' \
                                     ''.format(message, type(message))
    QMessageBox.warning(parent, 'Error', message)

    return


def pop_dialog_information(parent, message):
    """
    Pop up a one-button dialog for regular information
    :param parent:
    :param message:
    :return:
    """
    QMessageBox.information(parent, 'Information!', message)

    return


def skip_time(vec_times, vec_value, num_sec_skip, time_unit):
    """
    For a time series' times and value, pick up time and value pair by
    skipping some time period.
    :param vec_times:
    :param vec_value:
    :param num_sec_skip:
    :param time_unit:
    :return:
    """
    # Check input
    assert len(vec_times) == len(vec_value)
    assert isinstance(num_sec_skip, float) or isinstance(num_sec_skip, int)

    # Unit
    if time_unit == 'second':
        factor = 1.
    elif time_unit == 'nanosecond':
        factor = 1.E9
    else:
        raise RuntimeError('Time unit %s is not supported.' % time_unit)

    # Pick value
    out_vec_times = [vec_times[0]]
    out_vec_value = [vec_value[0]]
    prev_time = vec_times[0]

    size = len(vec_value)
    for i in xrange(1, size):
        if prev_time + num_sec_skip * factor - 1.E-6 <= vec_times[i]:
            # on next time spot within tolerance
            out_vec_times.append(vec_times[i])
            out_vec_value.append(vec_value[i])
            prev_time = vec_times[i]
    # END-FOR

    return numpy.array(out_vec_times), numpy.array(out_vec_value)


def sort_sample_logs(log_name_list, reverse=False, ignore_1_value=True):
    """ Sort the sample logs by size if the log name contains the size of the log
    with the option to ignore the single-value log
    :param log_name_list:
    :param reverse:
    :param ignore_1_value:
    :return: sorted log_name_list
    """
    # get a new list for sorting
    sort_list = list()
    for log_name in log_name_list:
        # split log size information
        log_size = int(log_name.split('(')[1].split(')')[0])
        # ignore single-value log
        if ignore_1_value and log_size <= 1:
            continue
        sort_list.append((log_size, log_name))
    # END-FOR

    # sort
    sort_list.sort(reverse=reverse)

    # create output
    return_list = [log_name for log_size, log_name in sort_list]

    return return_list


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
    cellitem = QTableWidgetItem()
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
        checkbox = QCheckBox()
        checkbox.setText('')
        checkbox.setChecked(state)
        
        #adding a widget which will be inserted into the table cell
        #then centering the checkbox within this widget which in turn,
        #centers it within the table column :-)
        QW=QWidget()
        cbLayout=QHBoxLayout(QW)
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
        combobox = QComboBox()
        combobox.addItems(qlist)
        
        #adding a widget which will be inserted into the table cell
        #then centering the checkbox within this widget which in turn,
        #centers it within the table column :-)
        QW=QWidget()
        cbLayout=QHBoxLayout(QW)
        cbLayout.addWidget(combobox)
        cbLayout.setAlignment(QtCore.Qt.AlignCenter)
        cbLayout.setContentsMargins(0,0,0,0)
        table.setCellWidget(row,col, combobox) #if just adding the checkbox directly
        combobox.setCurrentIndex(curindex)
    # ENDIFELSE

    return

