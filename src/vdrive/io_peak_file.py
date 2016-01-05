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
            print 'Add bank %d' % bank

        # For each bank, create a list sortable by peak positions
        for bank, name in self._peakDict.keys():
            peak_pos = self._peakDict[(bank, name)][0]
            print 'Bank = ', bank, 'of type', type(bank)
            peak_pos_name_dict[bank].append((peak_pos, name))

        # For each bank, sort the peaks by position
        for bank in peak_pos_name_dict.keys():
            peak_pos_name_dict[bank].sort(reverse=True)

        # Write
        for bank in self._bankNumberList:
            wbuf += '$ bank, name, number of peak, position, width\n'
            for i_pos in xrange(len(peak_pos_name_dict[bank])):
                # get all necessary value
                peak_pos = peak_pos_name_dict[bank][i_pos][0]
                peak_name = peak_pos_name_dict[bank][i_pos][1]
                width = self._peakDict[(bank, peak_name)][1]
                overlapped_list = self._peakDict[(bank, peak_name)][2]
                num_peaks = 1
                if isinstance(overlapped_list, list):
                    num_peaks += len(overlapped_list)

                # write bank name and peak name
                wbuf += '%d\t%s\t%d\t' % (bank, peak_name, num_peaks)
                # write peak name
                peak_pos_str = format_significant_4(peak_pos)
                wbuf += '%s\t' % peak_pos_str

                # write peak width and possible overlapped peaks' positions
                if isinstance(overlapped_list, list):
                    for temp_pos in overlapped_list:
                        temp_pos_str = format_significant_4(temp_pos)
                        wbuf += '%s\t' % temp_pos_str

                wbuf += '%.3f\n' % width
            # END-FOR
        # END-FOR

        try:
            out_file = open(peak_file, 'w')
            out_file.write(wbuf)
            out_file.close()
        except IOError, err:
            raise IOError('Unable to write to file %s due to %s.' % (peak_file, str(err)))

        return

    def import_peaks(self, peak_file):
        """ Import peaks from a GSAS single peak file
        Purpose: Read a standard GSAS peak file and
        Requirement: given peak file can be readable
        Guarantees: all peaks are loaded
        :param peak_file:
        :return:
        """
        # Check requirements
        assert isinstance(peak_file, str)

        # Get the file
        in_file = open(peak_file, 'r')
        raw_lines = in_file.readlines()
        in_file.close()

        for raw_line in raw_lines:
            line = raw_line.strip()

            # skip empty line and comment line
            if len(line) == 0:
                continue
            elif line.startswith('$'):
                continue

            terms = line.split()
            try:
                bank_number = int(terms[0])
                assert bank_number >= 0
                peak_name = terms[1]
                num_peaks = int(terms[2])
                assert num_peaks >= 1
                peak_pos = float(terms[3])
                if num_peaks == 1:
                    overlapped_peak_list = None
                else:
                    overlapped_peak_list = list()
                    for i_peak in xrange(num_peaks-1):
                        over_peak_pos = float(terms[4+i_peak])
                        overlapped_peak_list.append(over_peak_pos)
                # END-IF
                peak_width = float(terms[3+num_peaks])

                # add peak
                self.add_peak(bank_number, peak_name, peak_pos, peak_width, overlapped_peak_list)
            except IndexError:
                raise IndexError('Number of items in line "%s" is not right!' % line)
            except TypeError as err:
                raise TypeError('Line "%s" is not in a supported format.' % line)

        return

    def get_number_peaks(self):
        """ Get the number of peaks in this class
        :param peak_file:
        :return:
        """
        return len(self._peakDict)


def format_significant_4(float_number):
    """
    Format a float number with 4 significant digit if it is between 0.01 and 10.
    :param float_number:
    :return:
    """
    assert isinstance(float_number, float)

    formatted = ''
    if 0.01 <= float_number < 0.1:
        formatted = '%.5f' % float_number
    elif 0.1 <= float_number < 1.0:
        formatted = '%.4f' % float_number
    elif 1.0 <= float_number < 10.:
        formatted = '%.3f' % float_number
    else:
        raise AssertionError('Float number %f is not within range.' % float_number)

    return formatted


if __name__ == '__main__':
    print format_significant_4(0.012345)
    print format_significant_4(0.12345)
    print format_significant_4(1.2345)

    peak_manager = GSASPeakFileManager()
    peak_manager.import_peaks('/home/wzz/Projects/PyVDrive/tests/peak_processing/peak.txt')

    peak_manager.export_peaks('/home/wzz/Projects/PyVDrive/tests/peak_processing/dumb_peak.txt')
