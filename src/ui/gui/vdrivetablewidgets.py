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



Run_Selection_Table_Setup = [('Run Number', 'float'),
                             ('', 'checkbox')]

class VdriveRunTableWidget(NT.NTableWidget):
    """
    """
    def __init__(self, parent):
        """
        """
        NT.NTableWidget.__init__(self, parent)

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

