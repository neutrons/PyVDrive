import ndav_widgets.NTableWidget as NdavTable


class DataSlicerSegmentTable(NdavTable.NTableWidget):
    """
    """
    TableSetupList = [('Start', 'float'),
                      ('Stop', 'float'),
                      ('Target', 'int'),
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

    def append_start_time(self, time_stamp):
        """

        :param time_stamp:
        :return:
        """
        num_rows = self.rowCount()
        row_value_list = [time_stamp, '', num_rows, False]
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

    def replace_line(self, row_number, time_segments):
        """
        Replace a row by a few of new rows
        :param row_number: the number of the row to be replace
        :param time_segments: items for the new rows.
        :return: 2-tuple as (bool, str)
        """
        # Check
        assert isinstance(row_number, int)
        assert isinstance(time_segments, list)

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
            self.insertRow(row_number+1)
        for index in xrange(1, len(time_segments)):
            self.set_value_cell(row_number + index, self._colIndexStart, time_segments[index][0])
            self.set_value_cell(row_number + index, self._colIndexStop, time_segments[index][1])
            self.set_value_cell(row_number + index, self._colIndexSelect, False)

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

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(self.TableSetupList)

        # Set up column width
        self.setColumnWidth(0, 90)
        self.setColumnWidth(1, 90)
        self.setColumnWidth(2, 25)

        # Set up the column index for start, stop and select
        self._colIndexStart = self.TableSetupList.index(('Start', 'float'))
        self._colIndexStop = self.TableSetupList.index(('Stop', 'float'))
        self._colIndexTargetWS = self.TableSetupList.index(('Target', 'int'))
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


class MTSFormatTable(NdavTable.NTableWidget):
    """ An extended class for users to set up the format of the MTS log file
    """
    MTSTableSetup = [('Row', 'int'),
                     ('Content', 'string'),
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
        self.append_row([row_number, mts_line, False, False, False, False])

    def retrieve_format_dict(self):
        """
        Parse and retrieve log file format set up
        :return: tuple (boolean, dictionary with set up information)
        """
        num_rows = self.rowCount()
        comment_rows = list()
        header_rows = list()
        unit_rows = list()
        data_rows = list()

        for i_row in range(num_rows):
            # for each row, read all checked box
            num_true_counts = 0
            # get row number
            row_number = self.get_cell_value(i_row, self._colIndexRow)
            # is comment?
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

        # for dictionary
        format_dict = {'comment': comment_rows,
                       'header': header_rows[0],
                       'unit': unit_rows[0],
                       'data': data_rows}

        return True, format_dict

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(MTSFormatTable.MTSTableSetup)

        # set up column indexes
        self._colIndexRow = self.MTSTableSetup.index(('Row', 'int'))
        self._colIndexComment = self.MTSTableSetup.index(('Comment', 'checkbox'))
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
    PeakTableSetup = [('Bank', 'int'),
                      ('Name', 'string'),
                      ('Centre', 'float'),
                      ('Range', 'float'),   # range of the single peak or overlapped peaks
                      ('HKLs', 'string'),
                      ('Group', 'int'),
                      ('Select', 'checkbox')]

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
        :param name: peak name
        :param width: peak width
        :param overlapped_peak_pos_list:
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

        # Get new index
        status, message = self.append_row([bank, name, centre, width, name, group_id, False])
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

    def delete_peak(self, peak_index):
        """ Delete a peak from the table
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

        # Update the peak index of each peak behind
        for i_row in xrange(peak_index, self.rowCount()):
            this_index = self.get_cell_value(i_row, 0)
            self.update_cell_value(i_row, 0, this_index-1)
        # END-FOR(i_row)

        return

    def get_buffered_peaks(self, excluded_banks):
        """
        Return the buffered peaks
        :param excluded_banks: bank ID that will be excluded
        :return: a dictionary of a list of peaks (in 5-element list): bank, name, center, width, group
        """
        # TODO/NOW - check and doc

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
        bank = self.get_cell_value(peak_index, 0)
        name = self.get_cell_value(peak_index, 1)
        position = self.get_cell_value(peak_index, 2)
        width = self.get_cell_value(peak_index, 3)

        # Get overlapped peaks' positions
        group = self.get_cell_value(peak_index, 5)

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
        pos_col_index = 2
        width_col_index = 3

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

        return


TimeSegment_TableSetup = [('Start', 'float'),
                          ('Stop', 'float'),
                          ('Destination', 'int')]


class TimeSegmentsTable(NdavTable.NTableWidget):
    """
    Table for show time segments for data splitting
    """
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
        self.init_setup(TimeSegment_TableSetup)

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
