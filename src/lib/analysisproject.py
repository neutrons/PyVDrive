__author__ = 'wzz'

import os
import mantid_helper

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

    def get_data(self, data_key=None, data_file_name=None, bank_id=1):
        """ Get data
        :param data_key:
        :return:
        """
        """ Get data X, Y and E
        """
        # get file name
        fullpathdatafname = self._getFullpathFileName(basedatafilename)
        if fullpathdatafname is None:
            return (False, "Data file name %s does not exist in project. " % (basedatafilename))

        if os.path.exists(fullpathdatafname):
            return (False, "Data file name %s cannot be found. " % (fullpathdatafname))

        # retrieve
        ws = mantid.LoadGSS(Filename=fullpathdatafname)

        # FIXME - Consider single-spectrum GSS file only!

        return (True, [ws.readX(0), ws.readY(0), ws.readE(0)])

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
        out_ws_name = mantid_helper.workspace_name(data_file_name)

        if data_type.upper() == 'GSAS':
            mantid_helper.load_gsas_file(data_file_name, out_ws_name)
        else:
            raise NotImplementedError('Data type %s is not supported yet!' % data_type)

        # Add to dictionary
        base_name = os.path.basename(data_file_name)
        self._dataKeyPathMap[base_name] = data_file_name
        self._dataWorkspaceDict[base_name] = out_ws_name

        return base_name