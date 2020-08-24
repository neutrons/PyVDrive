import time
import datetime
import numpy
import platform
try:
    import qtconsole.inprocess  # noqa: F401
    from PyQt5 import QtCore
    from PyQt5.QtWidgets import QLineEdit, QMessageBox, QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout, QFileDialog
    from PyQt5.QtWidgets import QComboBox
    from PyQt5.QtGui import QStandardItemModel, QStandardItem
except ImportError:
    from PyQt4 import QtCore
    from PyQt4.QtGui import QStandardItemModel, QStandardItem, QLineEdit, QMessageBox, QFileDialog  # noqa: F401
    from PyQt4.QtGui import QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout, QComboBox
# include this try/except block to remap QString needed when using IPython
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s  # noqa: E731

from pyvdrive.core import datatypeutility


def add_runs_to_tree(treewidget, ipts, runlist):
    """ Add runs to a tree:

    THIS IS NOT USED ANYMORE!

    :param treewidget:
    :param ipts:
    :param runlist:
    :return:
    """
    # TODO - record the example below
    #     model = QStandardItemModel()
    #     model.setColumnCount(2)
    #     model.setHeaderData(0, QtCore.Qt.Horizontal, 'IPTS')

    # treewidget = QTreeView(treewidget)
    model = treewidget.model()

    numrows = model.rowCount()
    itemmain = QStandardItem(QtCore.QString(str(ipts)))
    itemmain.setCheckable(False)
    model.setItem(numrows, 0, itemmain)
    for i in range(len(runlist)):
        runnumber = runlist[i]
        item = QStandardItem(QtCore.QString(str(runnumber)))
        model.setItem(numrows+i+1, 1, item)
        # itemmain.setChild(i, item) : this will add value under column 0

    return


def browse_file(parent, caption, default_dir, file_filter, file_list=False, save_file=False):
    """ browse a file or files
    :param parent:
    :param caption:
    :param default_dir:
    :param file_filter:
    :param file_list:
    :param save_file:
    :return: if file_list is False: return string (file name); otherwise, return a list;
             if user cancels the operation, then return None
    """
    # check inputs
    assert isinstance(parent, object), 'Parent {} must be of some object.'.format(parent)
    datatypeutility.check_string_variable('File browsing title/caption', caption)
    datatypeutility.check_file_name(default_dir, check_exist=False, is_dir=True)
    datatypeutility.check_bool_variable('Flag for browse a list of files to load', file_list)
    datatypeutility.check_bool_variable('Flag to select loading or saving file', save_file)
    if file_filter is None:
        file_filter = 'All Files (*.*)'
    else:
        datatypeutility.check_string_variable('File filter', file_filter)

    if save_file:
        # browse file name to save to
        if platform.system() == 'Darwin':
            # TODO - 20180721 - Find out the behavior on Mac!
            file_filter = ''
        save_set = QFileDialog.getSaveFileName(parent, caption=caption, directory=default_dir,
                                               filter=file_filter)
        if isinstance(save_set, tuple):
            # returned include both file name and filter
            file_name = str(save_set[0])
        else:
            file_name = str(save_set)

    elif file_list:
        # browse file names to load
        open_set = QFileDialog.getOpenFileNames(parent, caption, default_dir, file_filter)

        if isinstance(open_set, tuple):
            # PyQt5
            file_name_list = open_set[0]
        else:
            file_name_list = open_set

        if len(file_name_list) == 0:
            # use cancel
            return None
        else:
            return file_name_list

    else:
        # browse single file name
        open_set = QFileDialog.getOpenFileName(parent, caption, default_dir, file_filter)

        if isinstance(open_set, tuple):
            # PyQt5
            file_name = open_set[0]
        else:
            file_name = open_set

    # END-IF-ELSE

    # check result for single file whether user cancels operation
    if len(file_name) == 0:
        return None

    return file_name


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


# TODO - TODAY - TEST - NEW Method
def get_load_file_by_dialog(parent, title, default_dir, file_filter):
    """ Get the file name to load via QFileDialog
    :param parent:
    :param title:
    :param default_dir:
    :param file_filter:
    :return:
    """
    datatypeutility.check_string_variable('Title (to load file)', title)
    datatypeutility.check_string_variable('Default directory to load file', default_dir)
    datatypeutility.check_file_name(default_dir, True, False, True, 'Default directory to load file')
    datatypeutility.check_string_variable('File filter', file_filter)

    # append "All files:
    if file_filter.count('*.*') == 0:
        file_filter += ';;All files (*.*)'

    # get file name
    returns = QFileDialog.getOpenFileName(parent, title, default_dir, file_filter)
    if isinstance(returns, tuple):
        file_name = str(returns[0])
    else:
        file_name = str(returns).strip()
    file_name = file_name.strip()

    print('[DB...BAT] Splitter file: {}'.format(file_name))

    return file_name


def get_save_file_by_dialog(parent, title, default_dir, file_filter):
    """ Get file name to save via QFileDialog
    :param parent:
    :param title:
    :param default_dir:
    :param file_filter:
    :return:
    """
    out_file_name = QFileDialog.getSaveFileName(parent, title, default_dir, file_filter)

    # PyQt5 returns a tuple
    if isinstance(out_file_name, tuple):
        out_file_name = out_file_name[0]

    # convert to string
    out_file_name = str(out_file_name).strip()

    return out_file_name


def parse_integer(line_edit, allow_blank=True):
    """
    Parse a line edit to an integer value
    :exception: ValueError
    :param line_edit:
    :param allow_blank: if true, then return None if there is no string written in the LineEdit
    :return: integer or None
    """
    # Check input
    if isinstance(line_edit, QLineEdit):
        str_value = line_edit.text()
    elif isinstance(line_edit, QComboBox):
        str_value = line_edit.currentText()
    else:
        raise AssertionError('Widget {} is not supported'.format(line_edit))

    # process
    str_value = str(str_value).strip()
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
    :param remove_duplicate: flat to remove duplicates
    :param increase:
    :return:
    """
    # check inputs
    assert isinstance(line_edit, QLineEdit), 'Input {0} of type {1} must be a QLineEdit instance' \
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


def parse_float(line_edit, allow_blank=True, default=None):
    """
    Parse a line edit as a float number
    :param line_edit:
    :param allow_blank: if true, then return None if there is no string written in the LineEdit
    :param default: default value.  If None, then set as blank still
    :return: float or None (or blank)
    """
    # Check input
    assert(isinstance(line_edit, QLineEdit)), 'Input shall be a QLineEdit instance but not a {}'.format(type(line_edit))

    str_value = str(line_edit.text()).strip()

    input_invalid = False
    float_value = None
    error_msg = 'Logic error'

    if len(str_value) == 0:
        input_invalid = True
        error_msg = 'Blank editor'
    else:
        try:
            float_value = float(str_value)
        except ValueError as e:
            input_invalid = True
            error_msg = '{} cannot be converted to float: {}'.format(str_value, e)
    # END-IF

    # if input is not valid
    if input_invalid and allow_blank:
        if default is not None:
            datatypeutility.check_float_variable('Default value of QLineEdit', default, (None, None))
            line_edit.setText('{}'.format(default))
            float_value = default
        else:
            float_value = None
    elif input_invalid:
        # raise Error!
        raise RuntimeError(error_msg)

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
    assert isinstance(message, str), 'Input message "{0}" must be a string but not a {1}' \
                                     ''.format(message, type(message))

    QMessageBox.information(parent, 'Information', message)

    return


def set_combobox_current_item(combo_box, item_name, match_beginning):
    """
    set the current (index/item) of a combo box by name
    :param combo_box:
    :param item_name:
    :param match_beginning: if True, only need to match beginning but not all
    :return:
    """
    # check
    assert isinstance(combo_box, QComboBox), 'Input widget {} must be a QComboBox instance but not a ' \
                                             '{}'.format(combo_box, type(combo_box))
    datatypeutility.check_string_variable('Combo box item name', item_name)

    # get the list of items' names
    item_name_list = [str(combo_box.itemText(i)).strip() for i in range(combo_box.count())]  # string and no space

    if match_beginning:
        # match beginning
        item_index = None
        for index_i, item_name_i in enumerate(item_name_list):
            if item_name_i.startswith(item_name):
                item_index = index_i
                break
        if item_index is None:
            raise RuntimeError('Combo box does not have item {}.  Available names are {}'
                               ''.format(item_name, item_name_list))
    else:
        # match all
        if item_name not in item_name_list:
            raise RuntimeError('Combo box does not have item {}.  Available names are {}'
                               ''.format(item_name, item_name_list))
        item_index = item_name_list.index(item_name)
    # END-IF-ELSE

    # set current index
    combo_box.setCurrentIndex(item_index)

    return


def set_combobox_items(combo_box, items):
    """ set the items to a combo Box (QComboBox) and by default set the current index to 0
    :param combo_box:
    :param items:
    :return:
    """
    # check
    assert isinstance(combo_box, QComboBox), 'Input widget {} must be a QComboBox instance but not a ' \
                                             '{}'.format(combo_box, type(combo_box))
    assert isinstance(items, list), 'Input items {} added to QComboBox must be in list but not in {}' \
                                    ''.format(items, type(items))
    if len(items) == 0:
        raise RuntimeError('Item list is empty!')

    # clear and then add items
    combo_box.clear()
    for item in items:
        combo_box.addItem(item)

    # set to first item
    combo_box.setCurrentIndex(0)

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
    for i in range(1, size):
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
        raise NotImplementedError("Input state %s of type %s is not accepted." % (str(state), str(type(state))))
    # ENDIF

    # check if cellWidget exitst
    if table.cellWidget(row, col) is not None:
        # existing: just set the value
        table.cellWidget(row, col).setChecked(state)
    else:
        # case to add checkbox
        checkbox = QCheckBox()
        checkbox.setText('')
        checkbox.setChecked(state)

        # adding a widget which will be inserted into the table cell
        # then centering the checkbox within this widget which in turn,
        # centers it within the table column :-)
        qw = QWidget()
        box_layout = QHBoxLayout(qw)
        box_layout.addWidget(checkbox)
        box_layout.setAlignment(QtCore.Qt.AlignCenter)
        box_layout.setContentsMargins(0, 0, 0, 0)
        table.setCellWidget(row, col, checkbox)  # if just adding the checkbox directly

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
    if table.cellWidget(row, col) is not None:
        # Existing: set to current index
        table.cellWidget(row, col).setCurrentIndex(curindex)
    else:
        # Case to add QComboBox
        # check input
        if not isinstance(itemlist, list):
            raise NotImplementedError("Input 'itemlist' must be list! Current input is of type '{}'"
                                      "".format(type(itemlist)))
        qlist = list()
        for item in itemlist:
            qlist.append(str(item))
        combobox = QComboBox()
        combobox.addItems(qlist)

        # adding a widget which will be inserted into the table cell
        # then centering the checkbox within this widget which in turn,
        # centers it within the table column :-)
        qw = QWidget()
        box_layout = QHBoxLayout(qw)
        box_layout.addWidget(combobox)
        box_layout.setAlignment(QtCore.Qt.AlignCenter)
        box_layout.setContentsMargins(0, 0, 0, 0)
        table.setCellWidget(row, col, combobox)  # if just adding the checkbox directly
        combobox.setCurrentIndex(curindex)
    # ENDIFELSE

    return
