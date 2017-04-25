import os
from os import listdir
from os.path import isfile, join
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

    def load_binned_data(self, data_file_name, data_file_type):
        """
        load binned data
        :param data_file_name:
        :param data_file_type:
        :return: data key
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
        if data_file_type == 'gsas':
            # load as GSAS
            # get the output workspace name
            data_ws_name = os.path.basename(file_name) + '_gsas'

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
        :return:
        """
        # check inputs
        assert isinstance(chopped_data_dir, str), 'Direcotry {0} must be given as a string but not a {1}.' \
                                                  ''.format(chopped_data_dir, str(chopped_data_dir))
        if not os.path.exists(chopped_data_dir):
            raise RuntimeError('Directory {0} for chopped data does not exist.'.format(chopped_data_dir))

        assert isinstance(file_format, str), 'Reduced data file format {0} must be a string.'.format(file_format)

        # list the files in a directory
        file_list = [f for f in listdir(chopped_data_dir) if isfile(join(chopped_data_dir, f))]

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
                reduced_file_list.append(file_name)
        # END-IF

        # sort file
        reduced_file_list.sort()

        # load file
        data_key_dict = dict()
        for file_name in reduced_file_list:
            data_key = self.load_binned_data(data_file_name=file_name, data_file_type=file_format)
            data_key_dict[data_key] = file_name
        # END-FOR

        return data_key_dict
