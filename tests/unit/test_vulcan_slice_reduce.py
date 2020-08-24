# Test pyvdrive.lib.vulcan_slice_reduce.SliceFocusVulcan
import pytest
import os
import pyvdrive.lib.vulcan_slice_reduce as vulcan_slice_reduce


def test_load_modules():
    """Test to load all modules
    """
    print('Hello world!')


def test_vanadium():
    """
    test main
    :return:
    """
    # Test data definition
    detector_efficiency_file = 'tests/data/vulcan_eff_156473.hdf5'
    if not os.path.exists(detector_efficiency_file):
        pytest.skip(f'Test file {detector_efficiency_file} cannot be found.')

    reducer = vulcan_slice_reduce.SliceFocusVulcan(number_banks=7, focus_instrument_dict=dict(),
                                                   num_threads=1)
    reducer.load_detector_eff_file(file_name=detector_efficiency_file)
    event_file_name = '/SNS/VULCAN/IPTS-19576/nexus/VULCAN_{0}.nxs.h5'.format(156473)
    ref_id = reducer.load_data(event_file_name=event_file_name)
    reducer.align_detectors(ref_id)
    reducer.diffraction_focus(ref_id, binning='-0.0004', apply_det_efficiency=True)
    reducer.save_nexus(ref_id, output_file_name='vulcan_det_eff_27banks.nxs')

    reducer = vulcan_slice_reduce.SliceFocusVulcan(number_banks=27)
    event_file_name = '/SNS/VULCAN/IPTS-19576/nexus/VULCAN_{0}.nxs.h5'.format(156473)
    ref_id = reducer.load_data(event_file_name=event_file_name)
    reducer.align_detectors(ref_id)
    reducer.diffraction_focus(ref_id, binning='-0.0004', apply_det_efficiency=False)
    reducer.save_nexus(ref_id, output_file_name='vulcan_raw_27banks.nxs')


if __name__ == '__main__':
    pytest.main(__file__)