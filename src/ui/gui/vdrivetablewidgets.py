#from PyQt4 import QtGui
import ndav_widgets.NTableWidget as NT

Data_Slicer_Table_Setup = [('Start', 'float'),
                           ('Stop', 'float'),
                           ('', 'checkbox')]


class DataSlicerSegmentTable(NT.NTableWidget):
    """
    """
    def __init__(self, parent):
        """
        """
        NT.NTableWidget.__init__(self, parent)

        return

    def append_start_time(self, time_stamp):
        """

        :param time_stamp:
        :return:
        """
        row_value_list = [time_stamp, '', False]
        self.append_row(row_value_list)

        return

    def get_selected_time_segments(self, flag):
        """
        Select time segments
        :param flag: If flag is true, then return the selected rows; otherwise, the
                     not-selected rows
        :return: 2-tuple as a list of time segments and a list of row numbers for them
        """
        # Get column index
        i_col_status = Data_Slicer_Table_Setup.index(('', 'checkbox'))
        i_col_start = Data_Slicer_Table_Setup.index(('Start', 'float'))
        i_col_stop = Data_Slicer_Table_Setup.index(('Stop', 'float'))

        # Collect time segment
        time_segment_list = list()
        row_number_list = list()
        num_rows = self.rowCount()
        for i_row in xrange(num_rows):
            if self.get_cell_value(i_row, i_col_status) == flag:
                start_time = self.get_cell_value(i_row, i_col_start)
                stop_time = self.get_cell_value(i_row, i_col_stop)
                # FIXME : The last row's stop is not calculated by method fill_stop_time()
                time_segment_list.append((start_time, stop_time))
                row_number_list.append(i_row)
        # END-FOR

        return time_segment_list, row_number_list

    def fill_stop_time(self):
        """ Fill the stop time by next line's start time
        :return: None
        """
        num_rows = self.rowCount()
        col_index_start = Data_Slicer_Table_Setup.index(('Start', 'float'))
        col_index_stop = Data_Slicer_Table_Setup.index(('Stop', 'float'))
        for ir in xrange(num_rows-1):
            stop_time = self.get_cell_value(ir+1, col_index_start)
            self.set_value_cell(ir, col_index_stop, stop_time)

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
        :return: a list of 2-tuple as start time and stop time relative to run start
        """
        split_tup_list = list()

        num_rows = self.rowCount()
        for ir in xrange(num_rows):
            selected = self.get_cell_value(ir, 2)
            if selected is True:
                start_time = self.get_cell_value(ir, 0)
                stop_time = self.get_cell_value(ir, 1)
                split_tup_list.append((start_time, stop_time))
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

        i_start_time = Data_Slicer_Table_Setup.index(('Start', 'float'))
        i_stop_time = Data_Slicer_Table_Setup.index(('Stop', 'float'))
        # FIXME/NOW - get i_select properly
        i_select = 2

        # Replace original row
        print '[DB-HUGE] Update cell @ %d, %d with value %f.' % (row_number, i_start_time, time_segments[0][0])
        self.update_cell_value(row_number, i_start_time, time_segments[0][0])
        print '[DB-HUGE] Update cell @ %d, %d with value %f.' % (row_number, i_stop_time, time_segments[0][1])
        self.update_cell_value(row_number, i_stop_time, time_segments[0][1])

        # Insert the rest
        for index in xrange(1, len(time_segments)):
            print '[DB-HUGE] Insert a row @ %d. Total number of rows = %d' % (row_number+1, self.rowCount())
            self.insertRow(row_number+1)
        for index in xrange(1, len(time_segments)):
            print '[DB-HUGE] Set cell value for row %d: ' % (row_number+index) , time_segments[index][0], time_segments[index][1]
            self.set_value_cell(row_number+index, i_start_time, time_segments[index][0])
            self.set_value_cell(row_number+index, i_stop_time, time_segments[index][1])
            self.set_value_cell(row_number+index, i_select, False)

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

        col_index = Data_Slicer_Table_Setup.index(('', 'checkbox'))
        self.update_cell_value(row_index, col_index, flag)

        return

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(Data_Slicer_Table_Setup)

        # Set up column width
        self.setColumnWidth(0, 90)
        self.setColumnWidth(1, 90)
        self.setColumnWidth(2, 25)

        return

    def sort_by_start_time(self):
        """ Sort table by start time and ignore the other columns
        """
        # Get the values of the first column to a new list
        num_rows = self.rowCount()
        start_time_list = list()
        i_start_col = Data_Slicer_Table_Setup.index(('Start', 'float'))
        for i_row in xrange(num_rows):
            start_time = self.get_cell_value(i_row, i_start_col)
            start_time_list.append(start_time)
        # END-FOR(i_row)

        # Sort list
        start_time_list.sort()

        # Update the sorted list to table
        for i_row in xrange(num_rows):
            self.update_cell_value(i_row, i_start_col, start_time_list[i_row])

        return


class PeakParameterTable(NT.NTableWidget):
    """
    A customized table to hold diffraction peaks with the parameters
    """
    PeakTableSetup = [('Bank', 'int'),
                      ('Name', 'string'),
                      ('Centre', 'float'),
                      ('Width', 'float'),
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
        NT.NTableWidget.__init__(self, parent)

        self._buffer = dict()

        return

    def add_peak(self, bank, name, centre, width):
        """ Append a peak to the table
        Purpose:
            Append a new peak to the table
        Requirements:
            Peak centre must be in d-spacing.  And it is within the peak range
        Guarantees:
            A row is append
        :param centre:
        :param bank: bank number
        :param width: peak width
        :return:
        """
        # Check requirements
        assert isinstance(centre, float)
        assert isinstance(bank, int)
        assert isinstance(width, float)
        assert isinstance(name, str)
        assert width > 0

        # Get new index
        # new_index = self.rowCount()
        self.append_row([bank, name, centre, width, False])

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

    def get_peak(self, peak_index):
        """ Get the peak's information from the table
        Purpose:
            Get the peak's information including centre, and range
        Requirements:
            Specified peak index must be in range
        Guarantees:
            Return a dictionary containing peak centre in d-dpacing and its range
        :param peak_index:
        :return:
        """
        # Check requirements
        assert isinstance(peak_index, int)
        assert 0 <= peak_index < self.rowCount(), 'Index of peak %d is out of boundary' % peak_index

        # Get information
        peak_dict = {'Centre': self.get_cell_value(peak_index, 1),
                     'xmin': self.get_cell_value(peak_index, 2),
                     'xmax': self.get_cell_value(peak_index, 3)}

        return peak_dict

    def get_selected_peaks_position(self):
        """ Purpose: get selected peaks' positions
        Requirements: At least 1 peak must be selected
        Guarantees:
        :return:
        """
        # TODO/NOW/1st: Doc/Assertion

        # Go over
        row_number_list = self.get_selected_rows()
        assert len(row_number_list) > 0, 'bla bla bla'

        pos_col_index = 2
        peak_pos_list = list()
        for i_row in row_number_list:
            peak_pos = self.get_cell_value(i_row, pos_col_index)
            peak_pos_list.append(peak_pos)

        return peak_pos_list

    def save(self, bank_id):
        """ Save table
        :return:
        """
        self._buffer[bank_id] = list()

        num_rows = self.rowCount()
        for i_row in xrange(num_rows):
            row_i = self.get_row_value(i_row)
            self._buffer[bank_id].append(row_i)
            # print 'row %d' % i_row, row_i, type(row_i)

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


class TimeSegmentsTable(NT.NTableWidget):
    """
    Table for show time segments for data splitting
    """
    def __init__(self, parent):
        """
        """
        NT.NTableWidget.__init__(self, parent)

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


class VdriveRunTableWidget(NT.NTableWidget):
    """
    """
    def __init__(self, parent):
        """
        """
        NT.NTableWidget.__init__(self, parent)

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
        """

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

