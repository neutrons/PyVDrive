__author__ = 'wzz'

import gui.ndav_widgets.NTableWidget as NT


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

    def setup(self):
        """
        Init setup
        :return:
        """
        self.init_setup(PeakParameterTable.PeakTableSetup)

        # Set up column width
        self.setColumnWidth(0, 20)

        return