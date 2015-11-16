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

    def fill_stop_time(self):
        """ Fill the stop time by next start time
        :return:
        """
        num_rows = self.rowCount()
        for ir in xrange(num_rows-1):
            stop_time = self.get_cell_value(ir+1, 0)
            self.set_value_cell(ir, 1, stop_time)

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
        :return:
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
        # TODO/FIXME/NOW: Follow

        # Check input type

        #
        for segment in segments_list:
            assert len(segment) == 3

            self._currRowNumber += 1
            self.append_row(segment)
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
        print '[DB] Appending %d runs' % len(run_list)
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

