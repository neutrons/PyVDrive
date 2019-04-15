import ndav_widgets.NTableWidget as NdavTable
from pyvdrive.lib import datatypeutility


class DataSlicerSegmentTable(NdavTable.NTableWidget):
    """
    """
    TableSetupList = [('Start', 'float'),
                      ('Stop', 'float'),
                      ('Target', 'str'),
                      ('', 'checkbox')]

    def __init__(self, parent):
        """
        """
        NdavTable.NTableWidget.__init__(self, parent)

        # Initialize some variables
        self._colIndexStart = -1
        self._colIndexStop = -1
        self._colIndexTargetWS = -1
        self._colIndexSelect = -1

        return

    def append_time_slicer(self, start_time, stop_time=None, target=None):
        """
        append a time slicer to the table
        :param start_time:
        :param stop_time:
        :param target:
        :return:
        """
        # check input
        assert isinstance(start_time, float), 'Starting time {0} must be a float but not a {1}.' \
                                              ''.format(start_time, type(start_time))
        if stop_time is None:
            stop_time = ''

        if target is None:
            target = str(self.rowCount())

        # add a new row
        row_value_list = [start_time, stop_time, target, False]
        self.append_row(row_value_list)

        return

    def fill_stop_time(self):
        """ Fill the stop time by next line's start time
        :return: None
        """
        num_rows = self.rowCount()

        # fill the stop time by next row's start time
        for ir in xrange(num_rows-1):
            stop_time = self.get_cell_value(ir + 1, self._colIndexStart)
            self.set_value_cell(ir, self._colIndexStop, stop_time)

        return

    def get_start_times(self):
        """ Return the sorted starting times
        :return:
        """
        num_rows = self.rowCount()
        start_time_list = list()

        for ir in xrange(num_rows):
            start_time = self.get_cell_value(ir, 0)
            start_time_list.append(start_time)

        start_time_list.sort()
        print '[DB] Start Times: ', start_time_list

        return start_time_list

    def get_splitter(self, row_number):
        """
        get a splitter (start time, stop time and target) of a specified row
        :param row_number:
        :return:
        """
        # check input
        assert isinstance(row_number, int), 'Row number {0} must be an integer but not a {1}.' \
                                            ''.format(row_number, type(row_number))

        # check validity
        if row_number < 0 or row_number >= self.rowCount():
            raise RuntimeError('Row number {0} is out of range [0, {1})'.format(row_number, self.rowCount()))

        # get result
        start_time = self.get_cell_value(row_number, 0)
        stop_time = self.get_cell_value(row_number, 1)
        target = self.get_cell_value(row_number, 2)

        return start_time, stop_time, target

    def get_splitter_list(self):
        """
        Get all splitters that are selected
        Note: splitters are relative time to run_start in unit of second
        :return: a list of 3-tuple as start time, stop time relative to run start
        """
        split_tup_list = list()

        num_rows = self.rowCount()
        for ir in xrange(num_rows):
            selected = self.get_cell_value(ir, self._colIndexSelect)
            if not selected:
                continue

            # get start and stop time
            start_time = self.get_cell_value(ir, self._colIndexStart)
            stop_time = self.get_cell_value(ir, self._colIndexStop, allow_blank=True)
            ws_index = self.get_cell_value(ir, self._colIndexTargetWS)

            if stop_time is None and ir != num_rows-1:
                raise RuntimeError('Stop time cannot be empty beside last row.')

            split_tup_list.append((start_time, stop_time, ws_index))
        # END-FOR

        return split_tup_list

    def replace_splitter(self, row_number, time_segments):
        """
        Replace a splitter (i.e., a row) by a few of new rows
        :param row_number: the number of the row to be replace
        :param time_segments: items for the new rows.
        :return: 2-tuple as (bool, str)
        """
        # Check
        assert isinstance(row_number, int), 'Input row number {0} must be an integer but not a {1}.' \
                                            ''.format(row_number, type(row_number))
        assert isinstance(time_segments, list), 'Input time segment {0} must be a list but not a {1}.' \
                                                ''.format(time_segments, type(time_segments))

        num_rows = self.rowCount()
        if row_number < 0 or row_number >= num_rows:
            return False, 'Input row number %d is out of range [0, %d).' % (row_number, num_rows)

        # Replace original row
        print '[DB-HUGE] Update cell @ %d, %d with value %f.' % (row_number, self._colIndexStart, time_segments[0][0])
        self.update_cell_value(row_number, self._colIndexStart, time_segments[0][0])
        print '[DB-HUGE] Update cell @ %d, %d with value %f.' % (row_number, self._colIndexStop, time_segments[0][1])
        self.update_cell_value(row_number, self._colIndexStop, time_segments[0][1])

        # Insert the rest by inserting rows and set values
        for index in xrange(1, len(time_segments)):
            start_time = -0.1
            stop_time = -0.1
            target = ''
            self.insert_row(row_number + 1, [start_time, stop_time, target, False])
        # END-FOR

        # set value to all the rows belonged to that
        for index in xrange(1, len(time_segments)):
            self.update_cell_value(row_number + index, self._colIndexStart, time_segments[index][0])
            self.update_cell_value(row_number + index, self._colIndexStop, time_segments[index][1])
            if len(time_segments[index]) >= 3:
                target = time_segments[index][2]
                self.update_cell_value(row_number + index, self._colIndexTargetWS, target)
            self.update_cell_value(row_number + index, self._colIndexSelect, True)

        return True, ''

    def select_row(self, row_index, flag):
        """
        Set a row to be selected
        :param row_index:
        :param flag: boolean to select or deselect the
        :return: None
        """
        assert (row_index >= 0) and (row_index < self.rowCount())
        assert isinstance(flag, bool)

        self.update_cell_value(row_index, self._colIndexSelect, flag)

        return

    # TODO - TODAY 190 - Test!
    def set_time_slicers(self, time_slicer_list):
        """
        clear the current table and set new time slicers (in a list) to this table
        :param time_slicer_list: list of times (in float)
        :return:
        """
        # check inputs
        datatypeutility.check_list('Event splitters', time_slicer_list)
        if len(time_slicer_list) == 0:
            raise RuntimeError('An empty slicer list is input to set_time_slicers')
        else:
            # sort
            time_slicer_list.sort()

        # clear the current table
        self.remove_all_rows()

        # check it is type 1 (list of times) or type 2 (list of splitters)
        if isinstance(time_slicer_list[0], tuple) or isinstance(time_slicer_list[0], list):
            # type 2: splitters
            for slicer_index, time_slicer_tup in enumerate(time_slicer_list):
                if len(time_slicer_tup) <= 1:
                    raise RuntimeError('{}-th slicer has too less items'
                                       ''.format(slicer_index, time_slicer_tup))
                elif len(time_slicer_tup) == 2 or time_slicer_tup[2] is None:
                    # use automatic slicer order index as target workspace
                    self.append_row([time_slicer_tup[0], time_slicer_tup[1], slicer_index+1, True])
                else:
                    # use user specified as target workspace
                    self.append_row([time_slicer_tup[0], time_slicer_list[1], time_slicer_list[2],
                                     True])
                # END-IF-ELSE
            # END-FOR
        else:
            # type 1: list of time stamps: set time
            for i_time in range(len(time_slicer_list)-1):
                start_time = time_slicer_list[i_time]
                stop_time = time_slicer_list[i_time + 1]
                self.append_row([start_time, stop_time, i_time, True])
        # END-FOR

        return

    def rename_chop_target(self, row_number_list, target):
        """
        rename the target (workspace/index) of the chopped data of selected rows
        :param row_number_list:
        :param target:
        :return:
        """
        for i_row in row_number_list:
            self.update_cell_value(i_row, self._colIndexTargetWS, target)

        return

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(self.TableSetupList)

        # Set up column width
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 200)
        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 100)

        # Set up the column index for start, stop and select
        self._colIndexStart = self.TableSetupList.index(('Start', 'float'))
        self._colIndexStop = self.TableSetupList.index(('Stop', 'float'))
        self._colIndexTargetWS = self.TableSetupList.index(('Target', 'str'))
        self._colIndexSelect = self.TableSetupList.index(('', 'checkbox'))

        return

    def sort_by_start_time(self):
        """ Sort table by start time and ignore the other columns
        """
        # Get the values of the first column to a new list
        num_rows = self.rowCount()
        start_time_list = list()
        for i_row in xrange(num_rows):
            start_time = self.get_cell_value(i_row, self._colIndexStart)
            start_time_list.append(start_time)
        # END-FOR(i_row)

        # Sort list
        start_time_list.sort()

        # Update the sorted list to table
        for i_row in xrange(num_rows):
            self.update_cell_value(i_row, self._colIndexStart, start_time_list[i_row])

        return


class ExperimentRecordTable(NdavTable.NTableWidget):
    """Experimental record information table
    """
    TableSetup = [('Run', 'int'),
                  ('AutoRecord', 'str'),
                  ('Align', 'str'),
                  ('Data', 'str')]

    def __init__(self, parent):
        """ initialization
        :param parent:
        """
        super(ExperimentRecordTable, self).__init__(parent)

        return

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(ExperimentRecordTable.TableSetup)

        return


class MTSFormatTable(NdavTable.NTableWidget):
    """ An extended class for users to set up the format of the MTS log file
    """
    MTSTableSetup = [('Row', 'int'),
                     ('Content', 'str'),
                     ('Block Start', 'checkbox'),
                     ('Header', 'checkbox'),
                     ('Unit', 'checkbox'),
                     ('Data', 'checkbox'),
                     ('Comment', 'checkbox')]

    def __init__(self, parent):
        """ Initialization
        :param parent:
        :return:
        """
        NdavTable.NTableWidget.__init__(self, parent)

        # set up class variables
        self._colIndexRow = -1
        self._colIndexContent = -1
        self._colBlockStart = -1
        self._colIndexComment = -1
        self._colIndexHeader = -1
        self._colIndexUnit = -1
        self._colIndexData = -1

        return

    def append_line(self, row_number, mts_line):
        """
        Append a line in MTS log file
        :param row_number:
        :param mts_line:
        :return:
        """
        status, ret_msg = self.append_row([row_number, mts_line, False, False, False, False, False])
        assert status, ret_msg

        return

    def get_content(self, row_index):
        """
        Get the line content of a row presented
        :param row_index:
        :return:
        """
        return self.get_cell_value(row_index, self._colIndexContent)

    def get_log_line_number(self, row_index):
        """
        Get the line number of the presented content in the log file
        :param row_index:
        :return:
        """
        return self.get_cell_value(row_index, self._colIndexRow)

    def is_block_start(self, row_index):
        """
        Is the start line of a block?
        :param row_index:
        :return:
        """
        return self.get_cell_value(row_index, self._colBlockStart)

    def is_header(self, row_index):
        """
        Is it a header line?
        :param row_index:
        :return:
        """
        return self.get_cell_value(row_index, self._colIndexHeader)

    def is_unit(self, row_index):
        """
        Is it a unit line?
        :param row_index:
        :return:
        """
        return self.get_cell_value(row_index, self._colIndexUnit)

    def is_data(self, row_index):
        """
        Is it a data line?
        :param row_index:
        :return:
        """
        return self.get_cell_value(row_index, self._colIndexData)

    def retrieve_format_dict(self):
        """
        Parse and retrieve log file format set up
        What is in the returned dictionary?
         - key: 'blockstart', 'header', 'unit', 'comment', 'data'
         - value: 2-tuple (row number, row content) or list of 2-tuple
        :return: tuple (boolean, dictionary with set up information)
        """
        num_rows = self.rowCount()
        comment_rows = list()
        block_start_rows = list()
        header_rows = list()
        unit_rows = list()
        data_rows = list()

        for i_row in range(num_rows):
            # for each row, read all checked box
            num_true_counts = 0
            # get row number
            print '[DB...BAT] Parsing row %d', i_row
            row_number = self.get_cell_value(i_row, self._colIndexRow)
            # is comments
            # use if but not if-else in order to prevent user selects more than 1 checkbox
            if self.get_cell_value(i_row, self._colBlockStart):
                block_start_rows.append(row_number)
                num_true_counts += 1
            if self.get_cell_value(i_row, self._colIndexComment):
                comment_rows.append(row_number)
                num_true_counts += 1
            if self.get_cell_value(i_row, self._colIndexHeader):
                header_rows.append(row_number)
                num_true_counts += 1
            if self.get_cell_value(i_row, self._colIndexUnit):
                unit_rows.append(row_number)
                num_true_counts += 1
            if self.get_cell_value(i_row, self._colIndexData):
                data_rows.append(row_number)
                num_true_counts += 1

            # check that there is 1 and only 1 shall be checked
            if num_true_counts == 0:
                return False, 'Row %d: No checkbox is checked' % row_number
            elif num_true_counts > 1:
                return False, 'Row %d: Too many checkboxes are checked' % row_number
        # END-FOR (i_row)

        # check something are very important
        assert len(block_start_rows) == 1, 'There must be 1 and only 1 line for block start. ' \
                                           'Now %d.' % len(block_start_rows)
        assert len(header_rows) == 1, 'There must be 1 and only 1 line for header. ' \
                                      'Now %d.' % len(header_rows)
        assert len(unit_rows) == 1, 'There must be 1 and only 1 line for line for unit. ' \
                                    'Now %d.' % len(unit_rows)

        # for dictionary
        format_dict = {'comment': comment_rows,
                       'blockstart': block_start_rows[0],
                       'header': header_rows[0],
                       'unit': unit_rows[0],
                       'data': data_rows}

        return True, format_dict

    def set_block_start(self, row_index, status):
        """
        Set this row as block starter
        :param row_index:
        :param status:
        :return:
        """
        # check
        assert isinstance(status, bool)

        # uncheck all type
        self._uncheck_all(row_index)

        # set value
        self.update_cell_value(row_index, self._colBlockStart, status)

        return

    def set_header_line(self, row_index, status):
        """
        Set this row as header
        :param row_index:
        :param status:
        :return:
        """
        # check
        assert isinstance(status, bool)

        # uncheck all type
        self._uncheck_all(row_index)

        # set value
        self.update_cell_value(row_index, self._colIndexHeader, status)

        return

    def set_unit_line(self, row_index, status):
        """
        Sett this row as unit line
        :param row_index:
        :param status:
        :return:
        """
        # check
        assert isinstance(status, bool)

        # uncheck all type
        self._uncheck_all(row_index)

        # set value
        self.update_cell_value(row_index, self._colIndexUnit, status)

        return

    def set_data_line(self, row_index, status):
        """
        Set this row as data line
        :param row_index:
        :param status:
        :return:
        """
        # check
        assert isinstance(status, bool)

        # uncheck all type
        self._uncheck_all(row_index)

        # set value
        self.update_cell_value(row_index, self._colIndexData, status)

        return

    def _uncheck_all(self, row_index):
        """
        Uncheck all type boxes
        :return:
        """
        assert isinstance(row_index, int), 'Row number/index must be an integer'
        assert 0 <= row_index < self.rowCount(), 'Row number/index is out of range.'

        self.update_cell_value(row_index, self._colBlockStart, False)
        self.update_cell_value(row_index, self._colIndexComment, False)
        self.update_cell_value(row_index, self._colIndexHeader, False)
        self.update_cell_value(row_index, self._colIndexData, False)
        self.update_cell_value(row_index, self._colIndexUnit, False)

        return

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(MTSFormatTable.MTSTableSetup)

        # set up column indexes
        self._colIndexRow = self.MTSTableSetup.index(('Row', 'int'))
        self._colIndexContent = self.MTSTableSetup.index(('Content', 'str'))
        self._colIndexComment = self.MTSTableSetup.index(('Comment', 'checkbox'))
        self._colBlockStart = self.MTSTableSetup.index(('Block Start', 'checkbox'))
        self._colIndexHeader = self.MTSTableSetup.index(('Header', 'checkbox'))
        self._colIndexUnit = self.MTSTableSetup.index(('Unit', 'checkbox'))
        self._colIndexData = self.MTSTableSetup.index(('Data', 'checkbox'))

        # set up column width
        self.setColumnWidth(0, 100)
        self.setColumnWidth(1, 800)

        return


class PeakParameterTable(NdavTable.NTableWidget):
    """
    A customized table to hold diffraction peaks with the parameters
    """
    PeakTableSetup = [('Select', 'checkbox'),
                      ('Bank', 'int'),
                      ('Name', 'str'),
                      ('Centre', 'float'),
                      ('Range', 'float'),   # range of the single peak or overlapped peaks
                      ('HKLs', 'str'),
                      ('Group', 'int')]

    def __init__(self, parent):
        """ Initialization
        Purpose:
            Initialize the table objet
        Requirements:
            None
        Guarantees:
            An object is made
        :param parent:
        :return:
        """
        NdavTable.NTableWidget.__init__(self, parent)

        self._buffer = dict()
        # group ID for overlapped peaks
        self._currGroupID = 0

        # columns
        self._bankColIndex = None
        self._nameColIndex = None
        self._posColIndex = None
        self._widthColIndex = None
        self._hklColIndex = None
        self._groupColIndex = None

        return

    def add_peak(self, bank, name, centre, width, group_id):
        """ Append a peak to the table
        Purpose:
            Append a new peak to the table
        Requirements:
            Peak centre must be in d-spacing.  And it is within the peak range
        Guarantees:
            A row is append
        :param centre:
        :param bank: bank number
        :param name: peak name.  If empty, then an automatic name will be given according to its row number
        :param width: peak width
        :param group_id:
        :return:
        """
        # Check requirements
        assert isinstance(centre, float), 'Peak center %s must be a float but not %s.' % (str(centre),
                                                                                          str(type(centre)))
        assert isinstance(bank, int)
        assert isinstance(width, float)
        assert isinstance(name, str)
        assert isinstance(group_id, int), 'Group ID must be an integer.'
        assert width > 0

        # set default peak name
        if len(name.strip()) == 0:
            peak_index = self.rowCount() + 1
            name = 'Peak%0d-B%d' % (peak_index, bank)

        # add peak
        status, message = self.append_row([True, bank, name, centre, width, name, group_id],
                                          num_decimal=3)
        if status is False:
            raise RuntimeError('Unable to add a new row for a peak due to %s.' % message)

        return

    def add_peak_to_buffer(self, bank, name, centre, width, overlapped_peak_pos_list):
        """ Append a peak to the buffer
        Purpose:
            Append a new peak to the table
        Requirements:
            Peak centre must be in d-spacing.  And it is within the peak range
        Guarantees:
            A row is append in the buffer
        :param bank: bank number
        :param name: peak name
        :param centre:
        :param width: peak width
        :param overlapped_peak_pos_list: list of overlapped peaks' positions
        :return:
        """
        # Check requirements
        assert isinstance(centre, float)
        assert isinstance(bank, int)
        assert isinstance(width, float)
        assert isinstance(name, str)
        assert width > 0
        assert isinstance(overlapped_peak_pos_list, list)
        # FIXME/NOW/1st: overlapped_peak_pos_list is not used!

        # Add buffer
        if bank not in self._buffer:
            self._buffer[bank] = list()

        self._buffer[bank].append([bank, name, centre, width, '', -1])

        return

    def clear_selected_peaks(self):
        """

        :return:
        """
        # TODO FIXME - NIGHT - This is not correct with the name and purpose
        self.remove_all_rows()

        return

    def delete_peak(self, peak_index):
        """ Delete i-th peak from the table
        Purpose:
            Delete a peak from the table
        Requirements:
            Given peak's index must be in the range
        Guarantees:
            The specified peak will be deleted from the table
        :param peak_index:
        :return:
        """
        # Check requirements
        assert isinstance(peak_index, int)
        assert 0 <= peak_index < self.rowCount(), 'Index of peak %d is out of boundary' % peak_index

        # Remove peak
        self.remove_row(peak_index)

        # remove the peak from buffered
        self._buffer.pop(peak_index)

        return

    def get_buffered_peaks(self, excluded_banks):
        """
        Return the buffered peaks
        :param excluded_banks: bank ID that will be excluded
        :return: a dictionary of a list of peaks (in 5-element list): bank, name, center, width, group
        """
        # Check
        assert isinstance(excluded_banks, list)

        # Get bank IDs
        bank_id_list = sorted(self._buffer.keys())
        bank_peak_dict = dict()
        for bank_id in bank_id_list:
            # skip the bank IDs to be excluded
            if bank_id in excluded_banks:
                continue

            # transform the peaks
            peak_row_list = self._buffer[bank_id]

            peak_list = list()
            for peak_row in peak_row_list:
                # check request
                assert isinstance(peak_row, list), 'Each peak row should be a list but NOT of %s.' % str(type(peak_row))
                bank = peak_row[0]
                peak_name = peak_row[1]
                peak_centre = peak_row[2]
                peak_width = peak_row[3]
                peak_group = peak_row[5]

                peak_i = [bank, peak_name, peak_centre, peak_width, peak_group]
                print '[DB...BAT] Buffered peak: ', peak_i
                peak_list.append(peak_i)

                print 'Appending peak %d: %s' % (len(peak_list)-1, str(peak_i))
            # END-FOR

            # add to dictionary
            bank_peak_dict[bank_id] = peak_list
        # END-FOR (bank)

        return bank_peak_dict

    def get_next_group_id(self):
        """
        Get the next group ID and involve the current one to the next one
        :return:
        """
        self._currGroupID += 1

        return self._currGroupID

    def get_peak(self, peak_index):
        """ Get one peak's information from the table according to its row number
        Purpose:
            Get the peak's information including centre, and range
        Requirements:
            Specified peak index must be in range
        Guarantees:
            Return a dictionary containing peak centre in d-dpacing and its range
        :param peak_index:
        :return: a list as bank, name, peak position, width, group ID (int)
        """
        # Check requirements
        assert isinstance(peak_index, int)
        assert 0 <= peak_index < self.rowCount(), 'Index of peak %d is out of boundary' % peak_index

        # Get information
        bank = self.get_cell_value(peak_index, self._bankColIndex)
        name = self.get_cell_value(peak_index, self._nameColIndex)
        position = self.get_cell_value(peak_index, self._posColIndex)
        width = self.get_cell_value(peak_index, self._widthColIndex)

        # Get overlapped peaks' positions
        group = self.get_cell_value(peak_index, self._groupColIndex)

        return [bank, name, position, width, group]

    def get_selected_peaks(self):
        """ Purpose: get selected peaks' positions
        Requirements: At least 1 peak must be selected
        Guarantees:
        :return: a list of peak positions of the peaks that are selected.
        """
        # Go over
        row_number_list = self.get_selected_rows()
        assert len(row_number_list) > 0, 'At least one peak must be selected.'

        # FIXME - Made this more flexible for column index
        pos_col_index = self._posColIndex
        width_col_index = self._widthColIndex

        peak_pos_list = list()
        for i_row in row_number_list:
            peak_pos = self.get_cell_value(i_row, pos_col_index)
            peak_width = self.get_cell_value(i_row, width_col_index)
            peak_pos_list.append((peak_pos, peak_width))

        return peak_pos_list

    def save_to_buffer(self, bank_id):
        """ Save table to buffer
        :param bank_id:
        :return:
        """
        self._buffer[bank_id] = list()

        num_rows = self.rowCount()
        for i_row in xrange(num_rows):
            row_i = self.get_row_value(i_row)
            self._buffer[bank_id].append(row_i)
            print 'row %d' % i_row, row_i, type(row_i)

        return

    def set_group_id(self, row_index, group_id):
        """ Set group ID to a grow
        Purpose: set a value to column 'Group'
        Requirements: group ID must be a non-negative integer
        :param row_index: index of a row
        :param group_id
        :return:
        """
        # Check requirements
        assert isinstance(group_id, int)
        assert group_id >= 0

        # Get the column index and set the value
        column_index = PeakParameterTable.PeakTableSetup.index(('Group', 'int'))
        self.set_value_cell(row_index, column_index, group_id)

        return

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(PeakParameterTable.PeakTableSetup)

        # Set up column width
        self.setColumnWidth(0, 60)

        # set up column index
        self._bankColIndex = self.get_column_index('Bank')
        self._nameColIndex = self.get_column_index('Name')
        self._posColIndex = self.get_column_index('Centre')
        self._widthColIndex = self.get_column_index('Range')
        self._hklColIndex = self.get_column_index('HKLs')
        self._groupColIndex = self.get_column_index('Group')

        return


class TimeSegmentsTable(NdavTable.NTableWidget):
    """
    Table for show time segments for data splitting
    """
    TimeSegment_TableSetup = [('Start', 'float'),
                              ('Stop', 'float'),
                              ('Destination', 'int')]

    def __init__(self, parent):
        """
        """
        NdavTable.NTableWidget.__init__(self, parent)

        self._currRowNumber = 0

    def set_segments(self, segments_list):
        """

        :param segments_list:
        :return:
        """
        for segment in segments_list:
            seg_list = [segment.start, segment.stop, str(segment.target)]
            self.append_row(seg_list)
            self._currRowNumber += 1
        # END-FOR

        return

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(TimeSegmentsTable.TimeSegment_TableSetup)

        return


Run_Selection_Table_Setup = [('Run Number', 'int'),
                             ('', 'checkbox')]


class VdriveRunTableWidget(NdavTable.NTableWidget):
    """
    """
    def __init__(self, parent):
        """
        """
        NdavTable.NTableWidget.__init__(self, parent)

    def append_runs(self, run_list):
        """
        Append a number of (experiment) runs to table
        :param run_list:
        :return:
        """
        for run in run_list:
            self.append_row([run, False])

        return

    def get_selected_runs(self):
        """ Get list of selected runs
        :return:
        """
        row_num_list = self.get_selected_rows()
        col_index_run = Run_Selection_Table_Setup.index(('Run Number', 'int'))

        run_number_list = list()
        for i_row in sorted(row_num_list):
            run_number = self.get_cell_value(i_row, col_index_run)
            run_number_list.append(run_number)

        return run_number_list

    def get_rows_by_run(self, run_list):
        """ Get row number/index for specified run numbers
        :param run_list: list of run numbers
        :return:
        """
        assert isinstance(run_list, list)

        row_number_list = list()
        num_rows = self.rowCount()
        for run_number in run_list:
            match_row_number = -1
            for i_row in xrange(num_rows):
                temp_row_number = self.get_cell_value(i_row, 0)
                if run_number == temp_row_number:
                    match_row_number = i_row
                    break
            row_number_list.append(match_row_number)
        # END-FOR

        return row_number_list

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(Run_Selection_Table_Setup)

        # Set up column width
        self.setColumnWidth(0, 90)
        self.setColumnWidth(1, 25)

        return
