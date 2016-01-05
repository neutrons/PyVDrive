########
# Read/Write peak file in GSAS format for single peak fitting
#
# $ bank, name, number of peak, position, width					
# 1	bcc110	2	2.101	2.07	0.03
# 1	Fcc111	2	2.173	2.028	0.03
# 1	Fcc200	1	1.879	0.035	
# 1	bcc200	1	1.486	0.03	
# 1	Fcc220	1	1.326	0.03	
# 1	bcc211	1	1.214	0.03	
# 1	Fcc311	1	1.134	0.03	
# 1	Fcc222	2	0.9374	1.017	0.03
# $1 	Bcc220	2	1.017	1.039	0.03
# $1 	bcc310FCC400	1	0.9039	0.03	
# $1 	bcc222	2	0.829	0.8038	0.02
# $1 	fcc331	2	0.8038	0.83	0.02
# $1 	bcc321	1	0.768	0.02	
# $ bank, name, number of peak, position, width					
# 2	bcc110	2	2.101	2.07	0.03
# 2	Fcc111	2	2.173	2.028	0.03
# 2	Fcc200	1	1.879	0.035	
# 2	bcc200	1	1.486	0.03	
# 2	Fcc220	1	1.326	0.03	
# 2	bcc211	1	1.214	0.03	
# 2	Fcc311	1	1.134	0.03	
# 2	Fcc222	2	0.9374	1.017	0.03
# $2 	Bcc220	2	1.017	1.039	0.03
# $2 	bcc310FCC400	1	0.9039	0.03	
# $2 	bcc222	2	0.829	0.8038	0.02
# $2 	fcc331	2	0.8038	0.83	0.02
# $2 	bcc321	1	0.768	0.02	
########


class GSASPeakFileManager(object):
    def __init__(self):
        """ Initialization
        :return:
        """
        # key: a tuple as bank number and peak name
        self._peakDict = dict()
        # List of bank numbers
        self._bankNumberList = list()

        return

    def add_peak(self, bank, name, position, width, overlapped_peaks_pos):
        """ Add a peak
        Purpose: add a peak to the object
        Requirement: the bank and name pair is unique, width is positive, position is positive
        Guarantees: a peak is
        :param bank:
        :param name:
        :param position:
        :param width:
        :param overlapped_peaks_pos: list of positions of the overlapped peaks
        :return:
        """
        # Check requirements
        assert isinstance(bank, int), 'Bank number must be an integer but not %s.' % str(type(bank))
        assert isinstance(name, str), 'Peak name must be a string but not %s.' % str(type(name))
        assert (bank, name) not in self._peakDict, 'Bank %d peak %s has already been added.' % (bank, name)
        assert isinstance(position, float), 'Peak position must be a float but not %s.' % str(type(position))
        assert position > 0., 'Peak position must be greater than 0, but given %f.' % position
        assert isinstance(width,float), 'Peak width must be a string but not %s.' % str(type(width))
        assert width > 0., 'Peak width must be greater than 0 but not %f.' % width
        assert overlapped_peaks_pos is None or isinstance(overlapped_peaks_pos, list), 'Over lapped peak list ' \
                                                                                       'must either None or a list.'
        if isinstance(overlapped_peaks_pos, list):
            for peak_pos in overlapped_peaks_pos:
                assert isinstance(peak_pos, float)
                assert peak_pos > 0.

        self._peakDict[(bank, name)] = [position, width, overlapped_peaks_pos]

        # Update bank number
        if bank not in self._bankNumberList:
            self._bankNumberList.append(bank)
            self._bankNumberList.sort()

        return

    def delete_peak(self, bank, name):
        """ Delete a peak from peaks list
        :param bank:
        :param name:
        :return:
        """
        assert isinstance(bank, int), 'Bank number must be an integer but not %s.' % str(type(bank))
        assert isinstance(name, str), 'Peak name must be a string but not %s.' % str(type(name))
        assert (bank, name) in self._peakDict, 'Bank %d peak %s is not found.' % (bank, name)

        del self._peakDict[(bank, name)]

        return

    def export_peaks(self, peak_file):
        """ Export all peaks to a GSAS standard peak file
        Purpose: export all the peaks to a GSAS-recognizable text file for single peak fitting
        Requirements: file name is a valid path with write permission
        Guarantees: a peak file is generated
        :param peak_file:
        :return:
        """
        # Check requirements
        assert isinstance(peak_file, str), 'Peak file path must be a string but not %s.' % str(type(peak_file))
        assert len(self._peakDict) > 0, 'There must be at least one peak added.'

        # Start
        wbuf = ''

        # Re-organize the list of peaks
        peak_pos_name_dict = dict()
        for bank in self._bankNumberList:
            peak_pos_name_dict[bank] = list()

        # For each bank, create a list sortable by peak positions
        for bank, name in self._peakDict.keys():
            peak_pos = self._peakDict[(bank, name)][0]
            peak_pos_name_dict[bank].append((peak_pos, name))

        # For each bank, sort the peaks by position
        for bank in peak_pos_name_dict.keys():
            peak_pos_name_dict[bank].sort(reversed=True)

        # Write
        for bank in self._bankNumberList:
            wbuf += '$ bank, name, number of peak, position, width\n'
            for i_pos in xrange(len(peak_pos_name_dict[bank])):
                peak_name = peak_pos_name_dict[bank][i_pos][1]
                wbuf += '%d\t%s\t%'


        pass

    def import_peaks(self, peak_file):
        """
        TODO/NOW: doc and implement
        :param peak_file:
        :return:
        """
        pass


    def get_number_peaks(self):
        """
        TODO/NOW: doc and implement
        :param peak_file:
        :return:
        """
        pass