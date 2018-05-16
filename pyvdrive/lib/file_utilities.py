# Zoo of utility methods for IO via file
# All the PyVDrive specific files will be parsed or written by methods in this module
import os
import h5py
import datatypeutility
from mantid.simpleapi import SaveNexusProcessed, LoadNexusProcessed


def import_detector_efficiency(h5_name):
    """
    import detector efficiency file
    :param h5_name:
    :return:
    """
    assert isinstance(h5_name, str)
    assert os.path.exists(h5_name)

    # open file
    det_file = h5py.File(h5_name, 'r')

    pid_vec = det_file['entry']['detector_efficiency']['pid'].value
    det_eff_factor_vec = det_file['entry']['detector_efficiency']['inverted efficiency'].value

    # close file
    det_file.close()

    return pid_vec, det_eff_factor_vec


def load_processed_nexus(nexus_file_name, output_ws_name):
    """
    load a Mantid processed Nexus file
    :param nexus_file_name:
    :param output_ws_name:
    :return:
    """
    datatypeutility.check_file_name(nexus_file_name, check_exist=True, check_writable=False,
                                    note='Mantid processed NeXus file')
    datatypeutility.check_string_variable('Output workspace name', output_ws_name)
    # LoadNexusProcessed(Filename='/home/wzz/Projects/PyVDrive/tests/data/vulcan_vanadium.nxs',
    #                    OutputWorkspace='7bankvanadium')

    LoadNexusProcessed(Filename=nexus_file_name, OutputWorkspace=output_ws_name)

    return


def save_workspace(ws_name, file_name, file_type='nxs', title=''):
    """
    save a workspace to Mantid processed Nexus file
    :param ws_name:
    :param file_name:
    :param file_type:
    :param title:
    :return:
    """
    datatypeutility.check_string_variable('Workspace name', ws_name)
    datatypeutility.check_file_name(file_name=file_name, check_writable=True,
                                    check_exist=False,
                                    note='Output processed NeXus file')
    datatypeutility.check_string_variable('Workspace title', title)

    if (file_type is None and file_name.lower().ends('.nxs')) or file_type == 'nxs':
        SaveNexusProcessed(InputWorkspace=ws_name,
                           Filename=file_name,
                           Title=title)
    else:
        raise RuntimeError('File type {0} or output file postfix {1} is not supported for saving.'
                           ''.format(file_type, file_name.lower()))

    return
