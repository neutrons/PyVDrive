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






