# Zoo of utility methods for IO via file
# All the PyVDrive specific files will be parsed or written by methods in this module
import os
import h5py
import vdrivehelper


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
    det_eff_factor_vec = det_file['entry']['detector_efficiency']['inversed efficiency'].value

    # close file
    det_file.close()

    return pid_vec, det_eff_factor_vec
