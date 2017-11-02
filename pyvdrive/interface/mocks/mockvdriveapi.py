
class MockVDriveAPI(object):
    """

    """
    def __init__(self):
        """

        :return:
        """
        self._currWS = None

        return

    def calculate_peaks_position(self, phase, min_d, max_d):
        """
        Purpose: calculate the bragg peaks' position from

        Requirements:

        Guarantees:
          1. return a list of reflections
          2. each reflection is a tuple. first is a float for peak position. second is a list of list for HKLs

        :param phase: [name, type, a, b, c]
        :param min_d:
        :param max_d:
        :return: list of 2-tuples.  Each tuple is a float as d-spacing and a list of HKL's
        """
        import PyVDrive.lib.mantid_helper as mantid_helper

        # Check requirements
        assert isinstance(phase, list), 'Input Phase must be a list but not %s.' % (str(type(phase)))
        assert len(phase) == 5, 'Input phase  of type list must have 5 elements'

        # Get information
        phase_type = phase[1]
        lattice_a = phase[2]
        lattice_b = phase[3]
        lattice_c = phase[4]

        # Convert phase type to
        phase_type = phase_type.split()[0]
        if phase_type == 'BCC':
            phase_type = mantid_helper.UnitCell.BCC
        elif phase_type == 'FCC':
            phase_type = mantid_helper.UnitCell.FCC
        elif phase_type == 'HCP':
            phase_type = mantid_helper.UnitCell.HCP
        elif phase_type == 'Body-Center':
            phase_type = mantid_helper.UnitCell.BC
        elif phase_type == 'Face-Center':
            phase_type = mantid_helper.UnitCell.FC
        else:
            raise RuntimeError('Unit cell type %s is not supported.' % phase_type)

        # Get reflections
        # silicon = mantid_helper.UnitCell(mantid_helper.UnitCell.FC, 5.43)  #, 5.43, 5.43)
        unit_cell = mantid_helper.UnitCell(phase_type, lattice_a, lattice_b, lattice_c)
        reflections = mantid_helper.calculate_reflections(unit_cell, 1.0, 5.0)

        # Sort by d-space... NOT FINISHED YET
        num_ref = len(reflections)
        ref_dict = dict()
        for i_ref in xrange(num_ref):
            ref_tup = reflections[i_ref]
            assert isinstance(ref_tup, tuple)
            assert len(ref_tup) == 2
            pos_d = ref_tup[1]
            assert isinstance(pos_d, float)
            assert pos_d > 0
            # HKL should be an instance of mantid.kernel._kernel.V3D
            hkl_v3d = ref_tup[0]
            hkl = [hkl_v3d.X(), hkl_v3d.Y(), hkl_v3d.Z()]

            # pos_d has not such key, then add it
            if pos_d not in ref_dict:
                ref_dict[pos_d] = list()
            ref_dict[pos_d].append(hkl)
        # END-FOR

        # Merge all the peaks with peak position within tolerance
        TOL = 0.0001
        # sort the list again with peak positions...
        peak_pos_list = ref_dict.keys()
        peak_pos_list.sort()
        print '[DB] List of peak positions: ', peak_pos_list
        curr_list = None
        curr_pos = -1
        for peak_pos in peak_pos_list:
            if peak_pos - curr_pos < TOL:
                # combine the element (list)
                assert isinstance(curr_list, list)
                curr_list.extend(ref_dict[peak_pos])
                del ref_dict[peak_pos]
            else:
                curr_list = ref_dict[peak_pos]
                curr_pos = peak_pos
        # END-FOR

        # Convert from dictionary to list as 2-tuples

        print '[DB-BAT] List of final reflections:', type(ref_dict)
        d_list = ref_dict.keys()
        d_list.sort(reverse=True)
        reflection_list = list()
        for peak_pos in d_list:
            reflection_list.append((peak_pos, ref_dict[peak_pos]))
            print '[DB-BAT] d = %f\treflections: %s' % (peak_pos, str(ref_dict[peak_pos]))

        return reflection_list

    def does_exist_data(self, data_key):
        """
        TODO/NOW/1s: should be implemented in the workflow controller!
        :return:
        """
        return True

    def get_diffraction_pattern_info(self, data_key):
        """ Get information from a diffraction pattern, i.e., a loaded workspace
        Purpose: get run number from "data key" and number of banks
        Requirements: data_key is an existing key as a string and it is the path to the data file
                      where the run number can be extracted
        Requirements: find out the run number and bank number
        :return:
        """
        import os
        print 'Data key is %s of type %s' % (str(data_key), str(type(data_key)))

        # Check requirements
        assert isinstance(data_key, str), 'Data key must be a string.'

        # Key (temporary) is the file name
        run_number = int(os.path.basename(data_key).split('.')[0])
        #
        num_banks = self._currWS.getNumberHistograms()

        return run_number, num_banks

    def get_diffraction_pattern(self, data_key, bank, include_err=False):
        """
        Purpose: get diffraction pattern of a bank
        Requirements:
            1. date key exists
            2. bank is a valid integer
        Guarantees: returned a 2 or 3 vector
        :param data_key:
        :param bank:
        :param include_err:
        :return:
        """
        # Check requirements
        assert self.does_exist_data(data_key)
        assert isinstance(bank, int)
        assert bank > 0
        assert isinstance(include_err, bool)

        # Get data
        # FIXME/TODO/NOW - 1st: Make it True and implement for real workflow controller
        if False:
            ws_index = self.convert_bank_to_ws(bank)

            if self._currDataKey == data_key:
                vec_x = self._currWS.readX(ws_index)
                vec_y = self._currWS.readY(ws_index)
                if include_err:
                    vec_e = []
                    return vec_x, vec_y, vec_e
            else:
                raise RuntimeError('Current workspace is not the right data set!')
        else:
            ws_index = bank-1
            vec_x = self._currWS.readX(ws_index)
            vec_y = self._currWS.readY(ws_index)

        return vec_x, vec_y

    def get_reduced_runs(self):
        """

        :return:
        """
        return []

    def import_gsas_peak_file(self, peak_file_name):
        """

        :param peak_file_name:
        :return: XXXX XXXX
        """
        # TODO/NOW/1st: Check requirements and finish the algorithm
        import PyVDrive.lib.io_peak_file as pio

        # Check requirements
        assert isinstance(peak_file_name, str)

        # Import peak file and get peaks
        peak_manager = pio.GSASPeakFileManager()
        peak_manager.import_peaks(peak_file_name)
        peak_list = peak_manager.get_peaks()

        for peak in peak_list:
            print type(peak), peak

        return peak_list

    def load_diffraction_file(self, file_name, file_type):
        """

        :param file_type:
        :return:
        """
        import sys
        sys.path.append('/Users/wzz/MantidBuild/debug/bin')
        import mantid.simpleapi

        if file_type.lower() == 'gsas':
            # load
            temp_ws = mantid.simpleapi.LoadGSS(Filename=file_name, OutputWorkspace='Temp')
            # set instrument geometry
            if temp_ws.getNumberHistograms() == 2:
                mantid.simpleapi.EditInstrumentGeometry(Workspace='Temp',
                                                        PrimaryFlightPath=43.753999999999998,
                                                        SpectrumIDs='1,2',
                                                        L2='2.00944,2.00944',
                                                        Polar='90,270')
            else:
                raise RuntimeError('It is not implemented for cases more than 2 spectra.')
            # convert unit
            mantid.simpleapi.ConvertUnits(InputWorkspace='Temp', OutputWorkspace='Temp',
                                          Target='dSpacing')

            self._currWS = mantid.simpleapi.ConvertToPointData(InputWorkspace='Temp', OutputWorkspace='Temp')
        else:
            raise NotImplementedError('File type %s is not supported.' % file_type)

        return file_name
