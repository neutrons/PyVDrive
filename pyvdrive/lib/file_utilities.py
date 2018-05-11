# Zoo of utility methods for IO via file
# All the PyVDrive specific files will be parsed or written by methods in this module
import os
import h5py
import vdrivehelper
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

def load_processed_nexus():
    # TODO
    LoadNexusProcessed(Filename='/home/wzz/Projects/PyVDrive/tests/data/vulcan_vanadium.nxs',
                       OutputWorkspace='7bankvanadium')

    return

def save_workspace(ws_name, file_name, file_type='nxs', title=''):
    if (file_type is None and file_name.lower().ends('.nxs')) or file_type == 'nxs':
        SaveNexusProcessed(InputWorkspace=ws_name,
                           Filename=file_name,
                           Title=title)

