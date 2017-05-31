import os
from os import listdir
from os.path import isfile, join
import math
import mantid_helper


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
                                                                       'is not supported.'.format(data_key,
                                                                                                  type(data_key))

        has = data_key in self._workspaceDict

        if not has:
            print '[DB....BAT] Loaded data keys are {0}.'.format(self._workspaceDict.keys())

        return has

    def load_binned_data(self, data_file_name, data_file_type, prefix, max_int):
        """
        load binned data
        :param data_file_name:
        :param data_file_type:
        :param prefix: prefix of the GSAS workspace name. It can be None, an integer, or a string
        :param max_int: maximum integer for sequence such as 999 for 001, 002, ... 999
        :return: string as data key (aka. workspace name)
        """
        # check inputs
        assert isinstance(data_file_type, str) or data_file_type is None, \
            'Data file type {0} must be a string or None but not a {1}.' \
            ''.format(data_file_type, type(data_file_type))
        assert isinstance(data_file_name, str), 'Data file name {0} must be a string but not a {1}.' \
                                                ''.format(data_file_name, type(data_file_name))

        # find out the type of the data file
        file_name, file_extension = os.path.splitext(data_file_name)

        if data_file_type is None:
            if file_extension.lower() in ['.gda', '.gsa', '.gss']:
                data_file_type = 'gsas'
            else:
                raise RuntimeError('Data file type {0} is not recognized.'.format(data_file_type))
        else:
            data_file_type = data_file_type.lower()
        # END-IF-ELSE

        # Load data
        base_ws_name = os.path.basename(file_name)
        if data_file_type == 'gsas':
            # load as GSAS
            # get the output workspace name
            if prefix is None or prefix == '':
                # no prefix is specified
                data_ws_name = '{0}_gsas'.format(base_ws_name)
            elif base_ws_name.isdigit():
                # base workspace name is an integer and prefix is given.
                num_zeros = int(math.log(max_int) / math.log(10)) + 1
                data_ws_name = '{0}_{1:0{2}}'.format(prefix, int(base_ws_name), num_zeros)
            else:
                # prefix_basename
                data_ws_name = '{0}_{1}'.format(prefix, os.path.basename(file_name))
            # END-IF

            # load data
            data_key = mantid_helper.load_gsas_file(data_file_name, data_ws_name,
                                                    standard_bin_workspace=self._myParent.vdrive_bin_template)
        else:
            raise RuntimeError('Unable to support %s file.' % data_file_type)

        # add to data management dictionary
        self._workspaceDict[data_key] = data_ws_name

        return data_key

    def load_chopped_binned_data(self, chopped_data_dir, file_format='gsas'):
        """
        load chopped and binned data (in GSAS format) for a diretory
        :param chopped_data_dir:
        :param file_format:
        :return: 2-tuple.  dictionary
        """
        # check inputs
        assert isinstance(chopped_data_dir, str), 'Direcotry {0} must be given as a string but not a {1}.' \
                                                  ''.format(chopped_data_dir, str(chopped_data_dir))
        if not os.path.exists(chopped_data_dir):
            raise RuntimeError('Directory {0} for chopped data does not exist.'.format(chopped_data_dir))

        assert isinstance(file_format, str), 'Reduced data file format {0} must be a string.'.format(file_format)

        # list the files in a directory
        file_list = [f for f in listdir(chopped_data_dir) if isfile(join(chopped_data_dir, f))]

        # search run_???_chop_info.txt
        chop_info_file = None
        for file_name in file_list:
            if file_name.startswith('run_') and file_name.endswith('_chop_info.txt'):
                chop_info_file = file_name
                break
        # END-FOR
        print '[DB...BAT] Chop Information File: {0}'.format(chop_info_file)

        if chop_info_file is None:
            # chopping information file is not given, then search reduced diffraction files from hard disk
            reduced_tuple_list = self.search_reduced_files(file_format, file_list, chopped_data_dir)
            run_number = None
        else:
            # parsing the chopping information file for reduced file and raw event files
            reduced_tuple_list = self.parse_chop_info_file(os.path.join(chopped_data_dir, chop_info_file))
            run_number = chop_info_file.split('_')[1]

        # load file
        data_key_dict = dict()
        for file_name, nexus_file_name, ws_name in reduced_tuple_list:
            # load GSAS file
            data_ws_name = self.load_binned_data(data_file_name=file_name, data_file_type=file_format,
                                                 prefix=run_number, max_int=len(reduced_tuple_list))

            if nexus_file_name is not None:
                # load raw NeXus file for sample logs
                mantid_helper.load_nexus(data_file_name=nexus_file_name, output_ws_name=ws_name,
                                         meta_data_only=True)
            # END-IF

            # form output
            data_key_dict[data_ws_name] = (ws_name, file_name)
        # END-FOR

        return data_key_dict, run_number

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

        reduced_file_list = list()
        for file_name in file_list:
            # get the file's extension
            file_extension = file_name.lower().split('.')[-1]
            file_extension = '.' + file_extension
            # check and add if the file is of the right type
            if file_extension in allowed_posfix:
                file_name = os.path.join(chopped_data_dir, file_name)
                reduced_file_list.append((file_name, None, None))
        # END-IF

        # sort file
        reduced_file_list.sort()

        return reduced_file_list
