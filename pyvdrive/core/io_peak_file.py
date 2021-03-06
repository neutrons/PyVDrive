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
        # This is a dictionary of dictionary
        # level-1 key: bank ID, level-2 key: group ID, value: (peak name, peak center, peak width)
        self._peakDict = dict()
        # List of bank numbers
        self._bankNumberList = list()

        return

    def add_peak(self, bank, name, position, width, group_id):
        """ Add a peak
        Purpose: add a peak to the object
        Requirement: the bank and name pair is unique, width is positive, position is positive
        Guarantees: a peak is
        :param bank:
        :param name:
        :param position:
        :param width:
        :param group_id: list of positions of the overlapped peaks OR None for no overlapped
        :return:
        """
        # Check requirements
        assert isinstance(bank, int), 'Bank number must be an integer but not %s.' % str(type(bank))
        assert isinstance(position, float), 'Peak position %s must be a float but not %s.' % (
            str(position), type(position))
        assert position > 0., 'Peak position must be greater than 0, but given %f.' % position
        assert isinstance(
            width, float), 'Peak width must be a string but not %s.' % str(type(width))
        assert width > 0., 'Peak width must be greater than 0 but not %f.' % width
        assert isinstance(group_id, int), 'Group ID (%s) must be an integer but not %s.' \
                                          '' % (str(group_id), str(type(group_id)))

        # Locate the level-1 and level-2 keys: bank and group ID
        if bank not in self._peakDict:
            self._peakDict[bank] = dict()
        if group_id not in self._peakDict[bank]:
            self._peakDict[bank][group_id] = list()

        # peak name
        assert isinstance(name, str) or name is None, 'Peak name must be a string or None but not %s.' \
                                                      '' % str(type(name))
        if name == '' or name is None:
            # automatic peak name
            peak_index = len(self._peakDict[bank][group_id]) + 1
            name = 'Peak-B%dG%d-%d' % (bank, group_id, peak_index)

        self._peakDict[bank][group_id].append((name, position, width))

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
        assert isinstance(peak_file, str), 'Peak file path must be a string but not %s.' % str(
            type(peak_file))
        assert len(self._peakDict) > 0, 'There must be at least one peak added.'

        # For each bank, create a list sortable by group positions
        # by assuming that there is no peak of another group inside any group
        group_pos_dict = dict()
        for bank in self._peakDict.keys():
            group_pos_list = list()
            for group_id in self._peakDict[bank].keys():
                group_pos = -1
                for peak_info_tup in self._peakDict[bank][group_id]:
                    peak_pos = peak_info_tup[1]
                    group_pos = peak_pos
                    break
                # END-FOR (peak)

                # append to group_position list for sorting
                group_pos_list.append((group_pos, group_id))
            # END-FOR (group)

            # sort group list in reverse order and add to dictionary for this bank
            group_pos_list.sort(reverse=True)
            group_pos_dict[bank] = group_pos_list
        # END-FOR (bank)

        # Init writing
        w_buf = ''

        # Write
        for bank in self._bankNumberList:
            # NOTE: the following codes are good, and will be kept!
            w_buf += '$ bank, name, number of peak, position, width\n'

            # loop over each group from high-D to low-D
            for g_tup in group_pos_dict[bank]:
                # get group ID
                group_id = g_tup[1]

                # sort peaks in reverse order
                peak_info_list = self._peakDict[bank][group_id]
                peak_info_list.sort(reverse=True)

                # get a list peak of peak positions
                overlapped_peaks = list()
                for peak_tup in peak_info_list:
                    overlapped_peaks.append(peak_tup[1])
                num_peaks = len(overlapped_peaks)

                # write peak to file
                for peak_tup in peak_info_list:
                    # get all necessary value
                    peak_name = peak_tup[0]
                    peak_pos = peak_tup[1]
                    peak_width = peak_tup[2]

                    # write bank name and peak name
                    w_buf += '%d\t%s\t%d\t' % (bank, peak_name, num_peaks)

                    # write this peak
                    peak_pos_str = format_significant_4(peak_pos)
                    w_buf += '%s\t' % peak_pos_str

                    # write other peaks
                    if num_peaks > 1:
                        other_peaks = overlapped_peaks[:]
                        other_peaks.pop(overlapped_peaks.index(peak_pos))
                        for p_pos in other_peaks:
                            temp_pos_str = format_significant_4(p_pos)
                            w_buf += '%s\t' % temp_pos_str
                    # END-IF

                    # write peak width
                    # TODO - NIGHT - peak width shall be close to 0.03
                    peak_width = 0.03
                    w_buf += '%.3f\n' % peak_width
                # END-FOR (peak-tup)
            # END-FOR (group)
        # END-FOR (bank)

        try:
            out_file = open(peak_file, 'w')
            out_file.write(w_buf)
            out_file.close()
        except IOError as err:
            raise IOError('Unable to write to file %s due to %s.' % (peak_file, str(err)))

        return

    def get_number_peaks(self):
        """ Get the number of peaks in this class
        :param peak_file:
        :return:
        """
        return len(self._peakDict)

    def get_peaks(self):
        """ Return all peaks
        Purpose: get all peaks to client
        Requirements: None
        Guarantees: peaks are exported as a list of list.  Each sub list is for one peak as
            [bank, name, centre, width, overlapped positions]
        Get all peaks by transforming ... self._peakDict = dict()
        :return:
        """
        peak_list = list()
        for key_tup in self._peakDict.keys():
            bank = key_tup[0]
            name = key_tup[1]
            peak_info = [bank, name]
            peak_info.extend(self._peakDict[key_tup])
            peak_list.append(peak_info)

        return peak_list

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
                    for i_peak in range(num_peaks-1):
                        over_peak_pos = float(terms[4+i_peak])
                        overlapped_peak_list.append(over_peak_pos)
                # END-IF
                peak_width = float(terms[3+num_peaks])

                # add peak
                self.add_peak(bank_number, peak_name, peak_pos, peak_width, overlapped_peak_list)
            except IndexError:
                raise IndexError('Number of items in line "%s" is not right!' % line)
            except TypeError as err:
                raise TypeError('Line {} is not in a supported format but of type {}. FYI: {}.'
                                ''.format(line, type(line), err))

        return


def format_significant_4(float_number):
    """
    Format a float number with 4 significant digit if it is between 0.01 and 10.
    :param float_number:
    :return:
    """
    assert isinstance(float_number, float)

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
    print(format_significant_4(0.012345))
    print(format_significant_4(0.12345))
    print(format_significant_4(1.2345))

    peak_manager = GSASPeakFileManager()
    peak_manager.import_peaks('/home/wzz/Projects/PyVDrive/tests/peak_processing/peak.txt')

    peak_manager.export_peaks('/home/wzz/Projects/PyVDrive/tests/peak_processing/dumb_peak.txt')
