import os
from os import listdir
from os.path import isfile, join
import math
import mantid_helper
import datatypeutility


class LoadedDataManager(object):
    """
    A data manager for loaded binned data and the corresponding workspaces
    """
    def __init__(self, parent):
        """
        initialization
        :param parent:
        """
        self._myParent = parent  # usually parent is None or ProjectManager

        # workspace management dictionary
        self._workspaceDict = dict()  # key: data key, value: workspace name

        # more detailed information: key = run number (GSAS) / data key
        self._singleGSASDict = dict()
        self._chopped_gsas_dict = dict()  # [run number] = dictionary ([seq order] = ws_name, gsas file, log file)

        return

    def get_bank_list(self, data_key):
        """
        get the list of banks of the workspace which data key corresponds to
        :exception: key error (no catch inside method)
        :param data_key:
        :return:
        """
        # Check requirements
        assert isinstance(data_key, str) or isinstance(data_key, int),\
            'Data key {0} must be a string or integer but not {1}.'.format(data_key, type(data_key))

        if data_key not in self._workspaceDict:
            raise RuntimeError('Data key {0} does not exist. Existing data key for workspaces are {1}.'
                               ''.format(data_key, str(self._workspaceDict.keys())))
        workspace_name = self._workspaceDict[data_key]

        # get the list of banks starting from bank 1
        bank_list = mantid_helper.get_data_banks(workspace_name, start_bank_id=1)

        return bank_list

    def get_data_set(self, data_key, target_unit):
        """ Get whole data set as a dictionary.  Each entry is of a bank
        Requirements: data key or data file name is specified
        Guarantees:
        :param data_key: data key generated in Vdrive project
        :param target_unit: unit of returned data
        :return:
        """
        # make input unit more flexible
        if target_unit.lower() == 'd-spacing':
            target_unit = 'dSpacing'
        elif target_unit.lower() == 'tof':
            target_unit = 'TOF'

        # Check requirements
        assert isinstance(target_unit, str) and target_unit in ['TOF', 'dSpacing'],\
            'Target unit {0} is not supported.'.format(target_unit)

        # get the workspace name
        data_ws_name = self._workspaceDict[data_key]

        # get data
        data_set_dict, unit = mantid_helper.get_data_from_workspace(data_ws_name, target_unit=target_unit,
                                                                    point_data=True, start_bank_id=1)

        return data_set_dict

    def get_chopped_sequences(self, run_number):
        """
        get the GSAS workspaces of a chopped run as a sequence
        :param run_number:
        :return:
        """
        if run_number not in self._chopped_gsas_dict.keys():
            raise RuntimeError('Chopped run number {} has not been loaded.  Loaded chopped runs are {}'
                               ''.format(run_number, self._chopped_gsas_dict.keys()))

        return sorted(self._chopped_gsas_dict[run_number].keys())

    def get_chopped_sequence_info(self, run_number, chop_sequence):
        """
        get the information of one chopped workspace (gsas and etc) from a series of GSAS file from a chopped run
        :param run_number:
        :param chop_sequence:
        :return: 3-tuple (workspace name, GSAS file, h5 log file)  It is one element from the dictionary
        """
        datatypeutility.check_int_variable('Run number (to chop from)', run_number, (1, 99999999))
        datatypeutility.check_int_variable('Chopped (out) sequence', chop_sequence, (0, None))

        if run_number not in self._chopped_gsas_dict:
            raise RuntimeError('Run {} is not in "Chopped GSAS Dict".  Existing runs are {}'
                               ''.format(run_number, self._chopped_gsas_dict.keys()))
        if chop_sequence not in self._chopped_gsas_dict[run_number]:
            raise RuntimeError('Chopped (out) sequence {} is not in loaded chapped run {}.  Existing sequences are {}.'
                               'Chopped runs are {}'
                               ''.format(chop_sequence, run_number, self._chopped_gsas_dict[run_number].keys(),
                                         self._chopped_gsas_dict.keys()))

        return self._chopped_gsas_dict[run_number][chop_sequence]

    def get_loaded_chopped_runs(self):
        """
        get the run numbers or data keys of the loaded chopped data
        :return:
        """
        loaded_chopped_runs = self._chopped_gsas_dict.keys()
        loaded_chopped_runs.sort()

        return loaded_chopped_runs

    def get_loaded_runs(self):
        """
        get the run numbers or data keys of the loaded data
        :return: a list of 2-tuples: data file name, workspace name
        """
        loaded_ws_list = self._singleGSASDict.keys()
        if len(loaded_ws_list) > 0:
            run_ws_list = list()
            for ws_name in loaded_ws_list:
                gda_name = self._singleGSASDict[ws_name]
                gda_name = os.path.basename(gda_name)
                run_ws_list.append((gda_name, ws_name))
            # END-FOR
            run_ws_list.sort()
        else:
            run_ws_list = list()

        return run_ws_list

    def get_workspace_name(self, data_key):
        """
        get workspace's name
        :param data_key:
        :return:
        """
        return self._workspaceDict[data_key]

    def has_data(self, data_key):
        """
        check whether the data key corresponds to any workspace loaded from external data
        :param data_key:
        :return:
        """
        assert isinstance(data_key, str) or isinstance(data_key, int), 'Data key {0} of type {1} ' \
                                                                       'is not supported.' \
                                                                       ''.format(data_key, type(data_key))

        if data_key not in self._workspaceDict:
            return False

        print '[DB....BAT] Loaded data keys are {0}.'.format(self._workspaceDict.keys())

        return True

    @staticmethod
    def construct_workspace_name(file_name, file_type, prefix, max_int):
        """ Construct a standard workspace for loaded binned data (gsas/processed nexus)
        :param file_name:
        :param file_type:
        :param prefix:
        :param max_int:
        :return:
        """
        # check inputs
        datatypeutility.check_string_variable('File name', file_name)
        datatypeutility.check_string_variable('File type', file_type)
        datatypeutility.check_string_variable('Workspace prefix', prefix)
        datatypeutility.check_int_variable('Maximum integer for file sequence number', max_int, (10, None))

        base_ws_name = os.path.basename(file_name).split('.')[0]
        hash_part = hash(os.path.basename(file_name))

        # add zeros for better sorting
        if base_ws_name.isdigit():
            # add number of zeros in front
            num_zeros = int(math.log(max_int) / math.log(10)) + 1
            if num_zeros < 1:
                num_zeros = 1
            base_ws_name = '{0:0{1}}'.format(int(base_ws_name), num_zeros)

        if prefix != '':
            data_ws_name = '{}_{}'.format(prefix, base_ws_name)
        else:
            data_ws_name = base_ws_name

        if file_type == '':
            raise RuntimeError('File type cannot be empty string')
        else:
            data_ws_name = '{}_{}{}'.format(data_ws_name, file_type[0], hash_part)

        return data_ws_name

    def load_binned_data(self, data_file_name, data_file_type, max_int, prefix='', data_key=None,
                         target_unit=None):
        """ Load binned data
        :param data_file_name:
        :param data_file_type:
        :param prefix: prefix of the GSAS workspace name. It can be None, an integer, or a string
        :param max_int: maximum integer for sequence such as 999 for 001, 002, ... 999
        :param data_key: data key or None (to use workspace name as data key)
        :param target_unit: target unit or None
        :return: string as data key (aka. workspace name)
        """
        # check inputs
        datatypeutility.check_file_name(data_file_name, True, False, False, 'Binned/reduced data file to load')
        if data_file_type is not None:
            datatypeutility.check_string_variable('Data file type', data_file_type, ['gsas', 'processed nexus'])
        if data_key is not None:
            datatypeutility.check_string_variable('Data key', data_key)
        datatypeutility.check_string_variable('Workspace prefix', prefix)

        # find out the type of the data file
        file_name, file_extension = os.path.splitext(data_file_name)

        if data_file_type is None:
            if file_extension.lower() in ['.gda', '.gsa', '.gss']:
                data_file_type = 'gsas'
            elif file_extension.lower() == '.nxs':
                data_file_type = 'processed nexus'
            else:
                raise RuntimeError('Data file type {0} is not recognized.'.format(data_file_type))
        else:
            data_file_type = data_file_type.lower()
        # END-IF-ELSE

        # Load data
        data_ws_name = self.construct_workspace_name(data_file_name, data_file_type, prefix, max_int)

        if data_file_type == 'gsas':
            # load as GSAS
            mantid_helper.load_gsas_file(data_file_name, data_ws_name, standard_bin_workspace=None)
        elif data_file_type == 'processed nexus':
            # load processed nexus
            mantid_helper.load_nexus(data_file_name=file_name, output_ws_name=data_ws_name, meta_data_only=False)
        else:
            raise RuntimeError('Unable to support %s file.' % data_file_type)

        # convert unit
        if target_unit:
            mantid_helper.mtd_convert_units(data_ws_name, target_unit)

        if data_key is None:
            data_key = data_ws_name

        # register by adding to data management dictionary
        self._workspaceDict[data_key] = data_ws_name
        # TODO - TONIGHT 0 - Add an option to the method such that single run data will go to singleGSASDict
        # TODO - ... ...   - chopped run will NOT to be recorded .. self._loadedGSSDict[] = ...maybe
        self._singleGSASDict[data_key] = data_file_name

        return data_key

    @staticmethod
    def search_chop_info_file(file_list):
        # search run_???_chop_info.txt
        chop_info_file = None
        for file_name in file_list:
            if file_name.startswith('run_') and file_name.endswith('_chop_info.txt'):
                chop_info_file = file_name
                break
        # END-FOR

        return chop_info_file

    # TODO - TONIGHT 0 - Clean up!
    def load_chopped_binned_data(self, run_number, chopped_data_dir, chop_sequences=None, file_format='gsas'):
        """
        load chopped and binned data (in GSAS format) for a directory.
        Chopping information file will be searched first
        About returned workspaces dictionary:
            key = sequence, value = (workspace name, data file name)
        :param chopped_data_dir:
        :param chop_sequences: chop sequence (order) indexes
        :param file_format:
        :param run_number: prefix to the loaded workspace from GSAS. It is just for decoration
        :return: 2-tuple of dictionary and integer (run number)
            dictionary: [chop seq index] = (workspace name, gsas file name, log HDF file name)    i.e., 3-tuple
        """
        # check inputs
        datatypeutility.check_int_variable('Run number', run_number, (1, 9999999))

        assert isinstance(chopped_data_dir, str), 'Directory {0} must be given as a string but not a {1}.' \
                                                  ''.format(chopped_data_dir, str(chopped_data_dir))
        assert isinstance(file_format, str), 'Reduced data file format {0} must be a string.'.format(file_format)
        if file_format != 'gsas':
            raise NotImplementedError('File format {} (other than GSAS) is not supported yet'.format(file_format))

        if not os.path.exists(chopped_data_dir):
            raise RuntimeError('Directory {0} for chopped data does not exist.'.format(chopped_data_dir))

        # list the files in a directory
        file_list = [f for f in listdir(chopped_data_dir) if isfile(join(chopped_data_dir, f))]
        chop_info_file = self.search_chop_info_file(file_list)

        if chop_info_file:
            # parsing the chopping information file for reduced file and raw event files
            print '[INFO] Load Chop Information File: {0}'.format(chop_info_file)
            reduced_tuple_dict = self.parse_chop_info_file(os.path.join(chopped_data_dir, chop_info_file))
        else:
            # look into each file
            # # chopping information file is not given, then search reduced diffraction files from hard disk
            print '[WARNING] Unable to Find Chop Information File in {0}. No Sample Log Loaded.' \
                  ''.format(chopped_data_dir)
            reduced_tuple_dict = self.search_reduced_files(file_format, file_list, chopped_data_dir)

        # END-IF-ELSE
        chopped_sequence_keys = sorted(reduced_tuple_dict.keys())

        # data key list:
        if chop_sequences is None:
            # default for all data
            chop_sequences = range(1, len(chopped_sequence_keys) + 1)
        elif isinstance(chop_sequences, int):
            # convert single sequence to a list
            chop_sequences = [chop_sequences]
        else:
            datatypeutility.check_list('Chopped sequences to load', chop_sequences)
            print ('[DB...BAT] User specified sequence: {}'.format(chop_sequences))
        # END-IF-ELSE

        loaded_gsas_dict = dict()   # [sequence] = workspace_name, file_name, None
        if run_number is None and run_number is None:
            raise RuntimeError('Run number must be given (or  ')
        for seq_index in chop_sequences:
            # load GSAS file
            if seq_index not in reduced_tuple_dict:
                print ('[DB...BAT] {}-th chopped data does not exist.'.format(seq_index))
                continue
            file_name = reduced_tuple_dict[seq_index][0]
            print ('[DB...BAT] Seq-index = {}, GSAS file name = {}'.format(seq_index, file_name))
            data_ws_name = self.load_binned_data(data_file_name=file_name, data_file_type=file_format,
                                                 prefix='G{}'.format(run_number),
                                                 max_int=len(chopped_sequence_keys) + 1)
            loaded_gsas_dict[seq_index] = data_ws_name, file_name, None
            # FIXME TODO - TONIGHT 1 - None shall be replaced by x.hdf5
        # END-FOR

        # register for chopped data dictionary: if run exists, then merge 2 dictionary!
        if run_number in self._chopped_gsas_dict:
            # run already exists, merge 2 dictionary
            self._chopped_gsas_dict[run_number].update(loaded_gsas_dict)
        else:
            self._chopped_gsas_dict[run_number] = loaded_gsas_dict

        return loaded_gsas_dict

    @staticmethod
    def parse_chop_info_file(info_file_name):
        """

        :param info_file_name:
        :return:
        """
        # get the file
        info_file = open(info_file_name, 'r')
        raw_lines = info_file.readlines()
        info_file.close()

        # parse it
        tuple_list = list()
        for raw_line in raw_lines:
            line = raw_line.strip()
            terms = line.split()
            if len(terms) == 3:
                tuple_list.append((terms[0], terms[1], terms[2]))
        # END-FOR

        # print '[DB...BAT] Get chop result tuples: {0}.'.format(tuple_list)

        return tuple_list

    @staticmethod
    def search_reduced_files(file_format, file_list, chopped_data_dir):
        """
        search reduced diffraction files in the given directory
        :return:
        """
        # check input
        assert isinstance(file_format, str), 'File format {0} must be an integer.'.format(file_format)
        assert isinstance(file_list, list), 'Files {0} must be given by list.'.format(file_list)
        assert isinstance(chopped_data_dir, str), 'Directory {0} must be a string.'.format(chopped_data_dir)

        allowed_posfix = list()
        if file_format == 'gsas':
            allowed_posfix.extend(['.gda', '.gss', '.gsa'])

        reduced_file_dict = dict()   # distinct file name or integer number
        for file_name in file_list:
            # get the file's extension
            file_extension = file_name.lower().split('.')[-1]
            file_extension = '.' + file_extension
            # check and add if the file is of the right type
            if file_extension not in allowed_posfix:
                continue

            data_key = file_name.split('.')[0]
            if data_key.isdigit():
                data_key = int(data_key)   # sequence number

            file_name = os.path.join(chopped_data_dir, file_name)
            reduced_file_dict[data_key] = file_name, None, None
        # END-IF

        return reduced_file_dict
