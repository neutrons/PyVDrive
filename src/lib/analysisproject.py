import os
import mantid_helper

__author__ = 'wzz'


class AnalysisProject(object):
    """ VDrive Analysis Project.  This is a simplified project manager than VDriveProject.
    AnalysisProject is designed to start from reduced powder diffraction data and is focused on data analysis

    Here are some conventions that are used in this class
    1. data key: the base data file name including postfix;
    """
    def __init__(self, project_name=None):
        """ Initialization
        :param project_name:
        """
        # Check
        assert isinstance(project_name, str) or project_name is None

        # Set class variable
        self._name = project_name

        # workspace holder
        self._dataWorkspaceDict = dict()
        # map between data key and full path
        self._dataKeyPathMap = dict()

        return

    @property
    def name(self):
        """ Return project name
        :return: if return None, it means that the project name has not been set up yet.
        """
        return self._name

    @name.setter
    def name(self, project_name):
        """ Set project name
        Requirements: project name is a string
        :param project_name:
        :return:
        """
        assert isinstance(project_name, str)
        self._name = project_name

        return

    def get_information(self, data_key=None, data_file_name=None):
        """
        Requirements: data key must exist
        :param data_key:
        :param data_file_name:
        :return:
        """
        # Check requirement
        assert data_key is not None or data_file_name is not None, 'Data key and data file name must be given 1.'
        assert (data_key is None and data_file_name is None) is False, 'Data key and data file name cannot have 2.'

        if data_file_name is not None:
            data_key = os.path.basename(data_file_name)

        if data_key not in self._dataWorkspaceDict:
            return False, 'data key %s does not exist.' % data_key

        # Get data
        data_set = self._dataWorkspaceDict[data_key]

        return len(data_key)

    def get_data(self, data_key=None, data_file_name=None):
        """ Get whole data set as a dictionary.  Each entry is of a bank
        Requirements: data key or data file name is specified
        Guarantees:
        :param data_key:
        :param data_file_name:
        :return:
        """
        # Check requirements
        assert data_key is None and data_file_name is None, 'Neither of ... specified... blabla'
        assert data_key is not None and data_file_name is not None, 'Both of ... blabla'

        # check and convert to data key
        if data_file_name is not None:
            assert isinstance(data_file_name, str), 'blabla'
            # TODO: make this to a method ???
            data_key = os.path.basename(data_file_name)
        else:
            assert isinstance(data_key, str), 'blabla'

        # check existence
        if data_key not in self._dataWorkspaceDict:
            raise KeyError('data key %s does not exist.' % data_key)

        # FIXME - data set dictionary can be retrieved from workspace long long time ago to save time
        data_set_dict = mantid_helper.get_data_from_workspace(self._dataWorkspaceDict[data_key], True)

        return True, data_set_dict

    def get_data_information(self, data_key):
        """ Get bank information of a loaded data file (workspace)
        Requirements: data_key is a valid string as an existing key to the MatrixWorkspace
        Guarantees: return
        :param data_key:
        :return:
        """
        # Check requirements
        assert isinstance(data_key, str), 'Data key must be a string but not %s.' % str(type(data_key))
        assert data_key in self._dataWorkspaceDict, 'Data key %s does not exist.' % data_key

        # FIXME - data set dictionary can be retrieved from workspace long long time ago to save time
        data_set_dict = mantid_helper.get_data_from_workspace(self._dataWorkspaceDict[data_key], True)

        return data_set_dict.keys()

    def load_data(self, data_file_name, data_type='GSAS'):
        """
        Load GSAS data
        Requirements: data file name is a valid full data path to a diffraction data (GSAS or Fullprof)
        :param data_file_name:
        :param data_type:
        :return: string as data key
        """
        # Check
        assert isinstance(data_file_name, str)
        assert os.path.exists(data_file_name), 'Data file %s does not exist.' % data_file_name

        # Get output workspace name
        out_ws_name = mantid_helper.get_standard_ws_name(data_file_name, False)

        if data_type.upper() == 'GSAS':
            mantid_helper.load_gsas_file(data_file_name, out_ws_name)
        else:
            raise NotImplementedError('Data type %s is not supported yet!' % data_type)

        # Add to dictionary
        base_name = os.path.basename(data_file_name)
        self._dataKeyPathMap[base_name] = data_file_name
        self._dataWorkspaceDict[base_name] = out_ws_name

        return base_name